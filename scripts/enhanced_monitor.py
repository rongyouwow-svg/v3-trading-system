#!/usr/bin/env python3
"""
🔍 v3.1 增强监控脚本

监控内容 (每 60 秒):
    1. 仓位超标检查 - 超过上限立即告警
    2. 止损单缺失检查 - 有持仓无止损单立即告警
    3. 信号执行率监控 - 执行率低于 10% 告警
    4. RSI 极端值监控 - RSI>85 或<15 告警
    5. 进程存活检查 - 策略进程/Web 服务宕机告警
    6. 账户余额监控 - 余额低于阈值告警
    7. 策略存活检查 - 策略进程自动重启

运行频率：每 60 秒
告警方式：Telegram + 日志
"""

import requests
import subprocess
import time
import json
import sys
from datetime import datetime
from pathlib import Path

# 导入 Telegram 告警
sys.path.insert(0, '/home/admin/.openclaw/workspace/quant/v3-architecture/scripts')
from telegram_alert import send_telegram_alert

# ==================== 配置 ====================
BASE_URL = "http://localhost:3000"
LOGS_DIR = Path('/home/admin/.openclaw/workspace/quant/v3-architecture/logs')
MONITOR_FILE = LOGS_DIR / 'enhanced_monitor.json'
ALERT_FILE = LOGS_DIR / 'monitor_alerts.log'

# 策略配置（独立仓位控制）
STRATEGY_CONFIG = {
    'ETHUSDT': {
        'amount': 100,  # USDT
        'leverage': 3,
        'stop_loss_pct': 0.002,  # 0.2%
        'max_position': 100 * 3 * 1.05,  # 315 USDT
        'rsi_overbought': 85,  # RSI 超买阈值
        'rsi_oversold': 15  # RSI 超卖阈值
    },
    'LINKUSDT': {
        'amount': 100,
        'leverage': 3,
        'stop_loss_pct': 0.002,
        'max_position': 315,
        'rsi_overbought': 85,
        'rsi_oversold': 15
    },
    'AVAXUSDT': {
        'amount': 200,
        'leverage': 3,
        'stop_loss_pct': 0.005,  # 0.5%
        'max_position': 200 * 3 * 1.05,  # 630 USDT
        'rsi_overbought': 85,
        'rsi_oversold': 15
    }
}

# 账户余额告警阈值
MIN_BALANCE_WARNING = 1000  # USDT
MIN_BALANCE_CRITICAL = 500  # USDT

# 进程配置
SUPERVISOR_CONF = '/home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf'
EXPECTED_PROCESSES = [
    'uvicorn',  # Web 服务进程名
    'quant-strategy-eth',
    'quant-strategy-link',
    'quant-strategy-avax',
    'quant-deep-monitor'
]

# ==================== 工具函数 ====================
def log(message: str, level: str = 'INFO'):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    # 写入日志文件
    try:
        with open(ALERT_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    except Exception as e:
        print(f"❌ 日志写入失败：{e}")

def alert(message: str, send_telegram: bool = True, level: str = 'CRITICAL'):
    """告警"""
    log(message, f'🚨 ALERT [{level}]')
    
    # 发送 Telegram 告警（总是发送）
    if send_telegram:
        try:
            send_telegram_alert(f"[{level}] {message}")
            log(f"Telegram 告警已发送：{message}", 'INFO')
        except Exception as e:
            log(f"Telegram 告警失败：{e}", 'ERROR')
            # 记录到单独的错误文件
            with open(LOGS_DIR / 'telegram_errors.log', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {e}\n")

def get_binance_positions():
    """获取币安实际持仓"""
    try:
        response = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
        data = response.json()
        return data.get('positions', [])
    except Exception as e:
        log(f"获取持仓失败：{e}", 'ERROR')
        return []

def get_binance_stop_losses():
    """获取币安实际止损单"""
    try:
        response = requests.get(f"{BASE_URL}/api/binance/stop-loss", timeout=10)
        data = response.json()
        return data.get('orders', [])
    except Exception as e:
        log(f"获取止损单失败：{e}", 'ERROR')
        return []

def get_binance_trades(limit=50):
    """获取币安实际成交"""
    try:
        response = requests.get(f"{BASE_URL}/api/binance/trades?limit={limit}", timeout=10)
        data = response.json()
        return data.get('trades', [])
    except Exception as e:
        log(f"获取成交失败：{e}", 'ERROR')
        return []

def get_strategy_status():
    """获取策略状态（从文件）"""
    try:
        with open(LOGS_DIR / 'strategy_pids.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def get_account_balance():
    """获取账户余额"""
    try:
        response = requests.get(f"{BASE_URL}/api/binance/account-info", timeout=10)
        data = response.json()
        if data.get('success'):
            return data.get('account', {}).get('available', 0)
        return 0
    except Exception as e:
        log(f"获取余额失败：{e}", 'ERROR')
        return 0

def check_supervisor_processes():
    """检查 supervisor 管理的进程状态"""
    try:
        result = subprocess.run(
            ['supervisorctl', '-c', SUPERVISOR_CONF, 'status'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        status_lines = result.stdout.strip().split('\n')
        process_status = {}
        
        for line in status_lines:
            if ':' in line:
                parts = line.split()
                name = parts[0].rstrip(':')
                status = parts[1] if len(parts) > 1 else 'UNKNOWN'
                process_status[name] = status
        
        return process_status
    except Exception as e:
        log(f"检查进程失败：{e}", 'ERROR')
        return {}

# ==================== 监控函数 ====================
def check_position_limit(symbol, positions):
    """检查仓位是否超标（独立仓位控制）"""
    if symbol not in STRATEGY_CONFIG:
        return
    
    config = STRATEGY_CONFIG[symbol]
    max_position = config['max_position']
    
    # 查找该交易对的持仓
    for pos in positions:
        if pos['symbol'] == symbol:
            position_value = pos['size'] * pos['entry_price']
            
            if position_value > max_position:
                alert(f"{symbol} 仓位超标！实际：{position_value:.2f} USDT, 上限：{max_position:.2f} USDT, 超标：{(position_value/max_position-1)*100:.1f}%", level='CRITICAL')
                # TODO: 添加自动平仓逻辑
            else:
                log(f"{symbol} 仓位正常：{position_value:.2f} / {max_position:.2f} USDT ({position_value/max_position*100:.1f}%)")
            
            return position_value
    
    return 0

def check_stop_loss_exists(symbol, positions, stop_losses):
    """检查有持仓是否有止损单"""
    for pos in positions:
        if pos['symbol'] == symbol:
            has_stop_loss = False
            for sl in stop_losses:
                if sl.get('symbol') == symbol:
                    has_stop_loss = True
                    break
            
            if not has_stop_loss:
                alert(f"{symbol} 有持仓但无止损单！持仓：{pos['size']} @ {pos['entry_price']}", level='CRITICAL')
            else:
                log(f"{symbol} 止损单正常")
            
            return has_stop_loss
    
    return True

def check_signal_execution_rate(symbol, strategy_status):
    """检查信号执行率"""
    if symbol not in strategy_status:
        return
    
    data = strategy_status[symbol]
    signals_sent = data.get('signals_sent', 0)
    signals_executed = data.get('signals_executed', 0)
    
    if signals_sent > 10 and signals_executed == 0:
        alert(f"{symbol} 信号执行率过低：0% ({signals_sent} 信号，{signals_executed} 执行)", level='WARNING')
    elif signals_sent > 0:
        rate = signals_executed / signals_sent * 100
        if rate < 10:
            alert(f"{symbol} 信号执行率过低：{rate:.1f}% ({signals_sent} 信号，{signals_executed} 执行)", level='WARNING')

def check_rsi_extreme(symbol, strategy_status):
    """检查 RSI 极端值"""
    if symbol not in strategy_status:
        return
    
    config = STRATEGY_CONFIG[symbol]
    data = strategy_status[symbol]
    rsi = data.get('last_rsi', 0)
    
    if rsi > config['rsi_overbought']:
        alert(f"{symbol} RSI 严重超买：{rsi:.2f} (阈值：{config['rsi_overbought']})", level='WARNING')
    elif rsi < config['rsi_oversold']:
        alert(f"{symbol} RSI 严重超卖：{rsi:.2f} (阈值：{config['rsi_oversold']})", level='WARNING')

def check_process_status(process_status):
    """检查进程存活状态"""
    for process_name in EXPECTED_PROCESSES:
        if process_name not in process_status:
            alert(f"进程异常：{process_name} 未找到", level='CRITICAL')
        elif process_status[process_name] != 'RUNNING':
            alert(f"进程异常：{process_name} 状态={process_status[process_name]}", level='CRITICAL')
            # 尝试自动重启
            log(f"尝试重启进程：{process_name}")
            try:
                subprocess.run(
                    ['supervisorctl', '-c', SUPERVISOR_CONF, 'restart', process_name],
                    timeout=30
                )
                log(f"进程已重启：{process_name}")
            except Exception as e:
                alert(f"进程重启失败：{process_name} - {e}", level='CRITICAL')

def check_account_balance(balance):
    """检查账户余额"""
    if balance < MIN_BALANCE_CRITICAL:
        alert(f"账户余额严重不足：{balance:.2f} USDT (警告线：{MIN_BALANCE_CRITICAL} USDT)", level='CRITICAL')
    elif balance < MIN_BALANCE_WARNING:
        alert(f"账户余额不足：{balance:.2f} USDT (警告线：{MIN_BALANCE_WARNING} USDT)", level='WARNING')
    else:
        log(f"账户余额正常：{balance:.2f} USDT")

# ==================== 主监控函数 ====================
def run_monitoring():
    """运行监控"""
    log("="*60)
    log("🔍 开始增强监控")
    log("="*60)
    
    # 获取数据
    positions = get_binance_positions()
    stop_losses = get_binance_stop_losses()
    trades = get_binance_trades()
    strategy_status = get_strategy_status()
    process_status = check_supervisor_processes()
    balance = get_account_balance()
    
    log(f"持仓：{len(positions)} 个")
    log(f"止损单：{len(stop_losses)} 个")
    log(f"成交：{len(trades)} 条")
    log(f"策略状态：{len(strategy_status)} 个")
    log(f"进程状态：{len(process_status)} 个")
    log(f"账户余额：{balance:.2f} USDT")
    
    # 检查每个策略
    for symbol in STRATEGY_CONFIG.keys():
        log(f"\n=== 检查 {symbol} ===")
        
        # 1. 检查仓位是否超标
        check_position_limit(symbol, positions)
        
        # 2. 检查有持仓是否有止损单
        check_stop_loss_exists(symbol, positions, stop_losses)
        
        # 3. 检查信号执行率
        check_signal_execution_rate(symbol, strategy_status)
        
        # 4. 检查 RSI 极端值
        check_rsi_extreme(symbol, strategy_status)
    
    # 5. 检查进程存活
    log(f"\n=== 检查进程存活 ===")
    check_process_status(process_status)
    
    # 6. 检查账户余额
    log(f"\n=== 检查账户余额 ===")
    check_account_balance(balance)
    
    # 保存监控数据
    monitor_data = {
        'timestamp': datetime.now().isoformat(),
        'positions': positions,
        'stop_losses': stop_losses,
        'trades': trades,
        'strategy_status': strategy_status,
        'process_status': process_status,
        'balance': balance,
        'alerts': []
    }
    
    # 保存到文件
    try:
        with open(MONITOR_FILE, 'w', encoding='utf-8') as f:
            json.dump(monitor_data, f, indent=2, ensure_ascii=False)
        log(f"\n✅ 监控数据已保存：{MONITOR_FILE}")
    except Exception as e:
        log(f"❌ 保存监控数据失败：{e}", 'ERROR')
    
    log("="*60)
    log("✅ 监控完成")
    log("="*60)

# ==================== 主程序 ====================
if __name__ == "__main__":
    log("🚀 增强监控脚本启动")
    log(f"监控频率：每 60 秒")
    log(f"日志文件：{ALERT_FILE}")
    log(f"数据文件：{MONITOR_FILE}")
    log(f"Telegram 告警：已启用")
    log("")
    
    # 确保目录存在
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 主循环
    while True:
        try:
            run_monitoring()
        except Exception as e:
            log(f"❌ 监控异常：{e}", 'ERROR')
        
        # 等待 60 秒
        time.sleep(60)
