#!/bin/bash
# 🦞 V3 系统完整监控 v1.0
# 监控层级：L1 基础设施 + L2 业务逻辑 + L3 数据一致性 + L4 风险控制

LOG_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/v3_complete_monitor_$(date +%Y%m%d).log"
STATE_DIR="/root/.openclaw/workspace/quant/v3-architecture/monitor_state"
ALERT_CHAT="1233887750"
BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"

mkdir -p "$STATE_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local level="$1"
    local message="$2"
    python3 -c "
import requests
try:
    requests.post(
        'https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/sendMessage',
        json={'chat_id': '1233887750', 'text': '''$level

$message''', 'parse_mode': 'Markdown'},
        timeout=10
    )
except Exception as e:
    print(f'发送失败：{e}')
" 2>/dev/null
}

# ==================== L1: 基础设施层 ====================

check_infrastructure() {
    log "【L1】基础设施检查..."
    local has_issue=false
    
    # 1. 检查 Dashboard API
    local dashboard_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health 2>/dev/null)
    if [[ "$dashboard_health" == "200" ]]; then
        log "  ✅ Dashboard API: 正常 ($dashboard_health)"
    else
        log "  ❌ Dashboard API: 异常 ($dashboard_health)"
        send_alert "🔴 **P0 - Dashboard 异常**" "Dashboard API 无响应 (HTTP $dashboard_health)"
        has_issue=true
    fi
    
    # 2. 检查策略进程
    local strategy_count=$(ps aux | grep -E "rsi_.*strategy.py" | grep -v grep | wc -l)
    if [[ $strategy_count -ge 3 ]]; then
        log "  ✅ 策略进程：$strategy_count 个运行中"
    else
        log "  ❌ 策略进程：只有 $strategy_count 个运行中"
        send_alert "🔴 **P0 - 策略进程异常**" "只有 $strategy_count 个策略进程运行"
        has_issue=true
    fi
    
    # 3. 检查币安连接
    local binance_check=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/binance/positions 2>/dev/null)
    if [[ "$binance_check" == "200" ]]; then
        log "  ✅ 币安连接：正常"
    else
        log "  ⚠️ 币安连接：异常 ($binance_check)"
    fi
    
    if [[ "$has_issue" == "false" ]]; then
        log "  ✅ L1 检查通过"
    fi
    log ""
}

# ==================== L2: 业务逻辑层 ====================

check_business_logic() {
    log "【L2】业务逻辑检查..."
    
    python3 << 'PYEOF'
import requests
import json
import os
from datetime import datetime

STATE_DIR = '/root/.openclaw/workspace/quant/v3-architecture/monitor_state'
ALERT_SENT = False

def send_alert(level, message):
    global ALERT_SENT
    if not ALERT_SENT:
        try:
            requests.post(
                'https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/sendMessage',
                json={'chat_id': '1233887750', 'text': f'{level}\n\n{message}', 'parse_mode': 'Markdown'},
                timeout=10
            )
            ALERT_SENT = True
        except:
            pass

try:
    # 加载上次状态
    last_state_file = f'{STATE_DIR}/last_check.json'
    if os.path.exists(last_state_file):
        with open(last_state_file, 'r') as f:
            last_state = json.load(f)
    else:
        last_state = {'strategies': {}}
    
    # 获取策略状态
    strategy_response = requests.get('http://localhost:3000/api/strategy/active', timeout=5)
    strategy_data = strategy_response.json()
    
    strategies = strategy_data.get('active_strategies', [])
    has_issue = False
    
    for strategy in strategies:
        symbol = strategy['symbol']
        status = strategy['status']
        signals_sent = strategy.get('signals_sent', 0)
        signals_executed = strategy.get('signals_executed', 0)
        
        print(f"  {symbol}: {status}, 信号={signals_sent}/{signals_executed}")
        
        # 检查 1: 策略运行
        if status != 'running':
            print(f"    ❌ 策略未运行")
            send_alert("🔴 **P0 - 策略异常**", f"{symbol} 策略未运行 (status={status})")
            has_issue = True
        
        # 检查 2: 信号产生（对比上次）
        if symbol in last_state.get('strategies', {}):
            last_sent = last_state['strategies'][symbol].get('signals_sent', 0)
            if signals_sent > last_sent:
                print(f"    ✅ 产生 {signals_sent - last_sent} 个新信号")
            elif signals_sent == 0 and last_sent == 0:
                print(f"    ℹ️ 无信号需求（正常）")
        
        # 检查 3: 信号执行
        if signals_executed < signals_sent:
            print(f"    ❌ 有信号未执行")
            send_alert("🟠 **P1 - 信号未执行**", f"{symbol} 发送={signals_sent}, 执行={signals_executed}")
            has_issue = True
    
    if not has_issue:
        print("  ✅ L2 检查通过")
    
    # 保存状态
    current_state = {
        'strategies': {s['symbol']: s for s in strategies},
        'check_time': datetime.now().isoformat()
    }
    
    with open(last_state_file, 'w') as f:
        json.dump(current_state, f, indent=2, default=str)
    
except Exception as e:
    print(f"  ❌ L2 检查失败：{e}")
PYEOF
    
    log ""
}

# ==================== L3: 数据一致性层 ====================

check_data_consistency() {
    log "【L3】数据一致性检查..."
    
    python3 << 'PYEOF'
import requests

try:
    # 获取持仓
    positions_response = requests.get('http://localhost:3000/api/binance/positions', timeout=5)
    positions_data = positions_response.json()
    positions = positions_data.get('positions', [])
    
    # 获取止损单
    stoploss_response = requests.get('http://localhost:3000/api/binance/stop-loss', timeout=5)
    stoploss_data = stoploss_response.json()
    stop_losses = stoploss_data.get('orders', [])
    
    print(f"  持仓：{len(positions)} 个")
    print(f"  止损单：{len(stop_losses)} 个")
    
    has_issue = False
    
    # 检查每个持仓是否有止损单
    for pos in positions:
        symbol = pos['symbol']
        has_stop = any(sl.get('symbol') == symbol for sl in stop_losses)
        
        if not has_stop:
            print(f"  ❌ {symbol}: 有持仓无止损")
            # 发送告警
            import requests as req
            req.post(
                'https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/sendMessage',
                json={'chat_id': '1233887750', 'text': f'🔴 **P0 - 无止损单**\n\n{symbol} 有持仓但未设置止损单', 'parse_mode': 'Markdown'},
                timeout=10
            )
            has_issue = True
        else:
            print(f"  ✅ {symbol}: 止损单已设置")
    
    if not has_issue:
        print("  ✅ L3 检查通过")
    
except Exception as e:
    print(f"  ❌ L3 检查失败：{e}")
PYEOF
    
    log ""
}

# ==================== L4: 风险控制层 ====================

check_risk_control() {
    log "【L4】风险控制检查..."
    
    python3 << 'PYEOF'
import requests

try:
    # 获取持仓
    positions_response = requests.get('http://localhost:3000/api/binance/positions', timeout=5)
    positions_data = positions_response.json()
    positions = positions_data.get('positions', [])
    
    # 策略配置（预期值）
    STRATEGY_CONFIG = {
        'ETHUSDT': {'leverage': 3, 'amount': 300},
        'LINKUSDT': {'leverage': 3, 'amount': 100},
        'AVAXUSDT': {'leverage': 8, 'amount': 200}
    }
    
    has_issue = False
    
    for pos in positions:
        symbol = pos['symbol']
        leverage = pos['leverage']
        pnl = pos.get('unrealized_pnl', 0)
        
        print(f"  {symbol}: 杠杆={leverage}, 盈亏={pnl:.2f} USDT")
        
        # 检查 1: 杠杆一致性
        if symbol in STRATEGY_CONFIG:
            expected_leverage = STRATEGY_CONFIG[symbol]['leverage']
            if leverage != expected_leverage:
                print(f"    ⚠️ 杠杆不一致：实际={leverage}, 配置={expected_leverage}")
                # 发送 P2 告警
                import requests as req
                req.post(
                    'https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/sendMessage',
                    json={'chat_id': '1233887750', 'text': f'🟠 **P2 - 杠杆不一致**\n\n{symbol}\n实际={leverage}, 配置={expected_leverage}', 'parse_mode': 'Markdown'},
                    timeout=10
                )
        
        # 检查 2: 亏损阈值
        if pnl < -50:
            print(f"    ❌ 亏损超阈值：{pnl:.2f} USDT")
            import requests as req
            req.post(
                'https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/sendMessage',
                json={'chat_id': '1233887750', 'text': f'🟠 **P2 - 亏损超阈值**\n\n{symbol}: {pnl:.2f} USDT', 'parse_mode': 'Markdown'},
                timeout=10
            )
            has_issue = True
    
    if not has_issue:
        print("  ✅ L4 检查通过")
    
except Exception as e:
    print(f"  ❌ L4 检查失败：{e}")
PYEOF
    
    log ""
}

# ==================== 主循环 ====================

log "========================================"
log "🦞 V3 系统完整监控 v1.0"
log "========================================"
log ""

check_infrastructure
check_business_logic
check_data_consistency
check_risk_control

log "========================================"
log "📊 本轮检查完成"
log "========================================"
log ""
log "⏰ 下次检查：10 分钟后"
