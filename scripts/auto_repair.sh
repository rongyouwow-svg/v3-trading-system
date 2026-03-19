#!/bin/bash
# 🦞 V3 系统全自动修复脚本
# 每 10 分钟检查一次，自动修复

LOG_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/auto_repair_$(date +%Y%m%d).log"
SUPERVISORCTL="/root/.pyenv/versions/3.10.13/bin/supervisorctl"
SUPERVISOR_CONF="/root/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf"
PYTHON="/root/.pyenv/versions/3.10.13/bin/python3"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local message="$1"
    python3 << EOF
import requests
try:
    requests.post(
        "https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/sendMessage",
        json={
            'chat_id': '1233887750',
            'text': '''$message''',
            'parse_mode': 'Markdown'
        },
        timeout=10
    )
except Exception as e:
    print(f"发送告警失败：{e}")
EOF
}

check_and_fix_service() {
    local service=$1
    local status=$($SUPERVISORCTL -c $SUPERVISOR_CONF status $service 2>&1)
    
    if [[ $status == *"RUNNING"* ]]; then
        log "✅ $service: 正常运行"
        return 0
    elif [[ $status == *"FATAL"* ]] || [[ $status == *"BACKOFF"* ]] || [[ $status == *"STOPPED"* ]]; then
        log "❌ $service: $status - 尝试修复..."
        
        # 清理残留
        pkill -9 -f "$service" 2>/dev/null
        
        # 重启
        $SUPERVISORCTL -c $SUPERVISOR_CONF start $service 2>&1 | tee -a "$LOG_FILE"
        sleep 5
        
        # 验证
        local new_status=$($SUPERVISORCTL -c $SUPERVISOR_CONF status $service 2>&1)
        if [[ $new_status == *"RUNNING"* ]]; then
            log "✅ $service: 修复成功"
            send_alert "✅ **服务已修复**

服务：$service
状态：$new_status
时间：$(date '+%Y-%m-%d %H:%M:%S')"
            return 0
        else
            log "🚨 $service: 修复失败 - $new_status"
            send_alert "🚨 **服务修复失败**

服务：$service
状态：$new_status
时间：$(date '+%Y-%m-%d %H:%M:%S')

需要手动干预！"
            return 1
        fi
    else
        log "⚠️ $service: 未知状态 - $status"
        return 1
    fi
}

check_dashboard() {
    log "📊 检查 Dashboard..."
    
    local response=$(curl -s http://localhost:3000/api/health 2>/dev/null)
    
    if [[ $response == *'"status":"ok"'* ]] || [[ $response == *'"status": "ok"'* ]]; then
        log "✅ Dashboard: API 正常"
        return 0
    else
        log "❌ Dashboard: API 异常 - 尝试重启..."
        
        # 清理进程
        pkill -9 -f "uvicorn.*3000" 2>/dev/null
        rm -f /root/.openclaw/workspace/quant/v3-architecture/logs/*.sock 2>/dev/null
        sleep 2
        
        # 重启
        cd /root/.openclaw/workspace/quant/v3-architecture
        nohup $PYTHON -m uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000 --timeout-keep-alive 30 > logs/dashboard_out.log 2>&1 &
        sleep 5
        
        # 验证
        local new_response=$(curl -s http://localhost:3000/api/health 2>/dev/null)
        if [[ $new_response == *'"status":"ok"'* ]] || [[ $new_response == *'"status": "ok"'* ]]; then
            log "✅ Dashboard: 重启成功"
            send_alert "✅ **Dashboard 已修复**

Dashboard API 恢复正常
时间：$(date '+%Y-%m-%d %H:%M:%S')"
            return 0
        else
            log "🚨 Dashboard: 重启失败"
            send_alert "🚨 **Dashboard 修复失败**

需要手动干预！
时间：$(date '+%Y-%m-%d %H:%M:%S')"
            return 1
        fi
    fi
}

check_strategies() {
    log "📈 检查策略执行..."
    
    local response=$(curl -s http://localhost:3000/api/strategy/active 2>/dev/null)
    
    if [[ $response == *'"success": true'* ]] || [[ $response == *'"success":true'* ]]; then
        local count=$(echo $response | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('active_strategies',[])))" 2>/dev/null)
        log "✅ 策略执行：$count 个策略运行中"
        return 0
    else
        log "❌ 策略执行：API 异常"
        return 1
    fi
}

check_positions() {
    log "💰 检查持仓..."
    
    local response=$(curl -s http://localhost:3000/api/binance/positions 2>/dev/null)
    
    if [[ $response == *'"success": true'* ]] || [[ $response == *'"success":true'* ]]; then
        local count=$(echo $response | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('positions',[])))" 2>/dev/null)
        log "✅ 持仓检查：$count 个持仓"
        return 0
    else
        log "❌ 持仓检查：API 异常"
        return 1
    fi
}

# ==================== 主循环 ====================

log "========================================"
log "🦞 V3 系统全自动修复启动"
log "========================================"

# 检查所有服务
log ""
log "【1】检查 Supervisor 服务..."
check_and_fix_service "quant-strategy-eth"
check_and_fix_service "quant-strategy-link"
check_and_fix_service "quant-strategy-avax"
check_and_fix_service "quant-deep-monitor"
check_and_fix_service "quant-enhanced-monitor"
check_and_fix_service "service-monitor"

# 检查 Dashboard
log ""
log "【2】检查 Dashboard..."
check_dashboard

# 检查策略执行
log ""
log "【3】检查策略执行..."
check_strategies

# 检查持仓
log ""
log "【4】检查持仓..."
check_positions

# 生成报告
log ""
log "========================================"
log "📊 本轮检查完成"
log "========================================"

# 发送汇总报告
send_alert "📊 **V3 系统检查报告**

时间：$(date '+%Y-%m-%d %H:%M:%S')

✅ 所有服务已检查
✅ 自动修复已完成

详情查看日志：
logs/auto_repair_$(date +%Y%m%d).log"

log ""
log "⏰ 下次检查：10 分钟后"
log "========================================"
