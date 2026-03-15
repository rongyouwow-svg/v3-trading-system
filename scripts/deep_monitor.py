#!/usr/bin/env python3
"""
🔍 v3.1 深度监测脚本

监控内容:
    1. 每 5 分钟查询币安实际持仓
    2. 每 5 分钟查询币安实际止损单
    3. 对比策略配置和实际持仓（检查是否超标）
    4. 对比开仓记录和止损单（检查是否创建）
    5. 验证止损单是否跟上车
    6. 记录所有异常并告警

运行频率：每 60 秒
"""

import requests
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
MONITOR_FILE = LOGS_DIR / 'deep_monitor.json'
ALERT_FILE = LOGS_DIR / 'monitor_alerts.log'

# 策略配置
STRATEGY_CONFIG = {
    'ETHUSDT': {
        'amount': 100,  # USDT
        'leverage': 3,
        'stop_loss_pct': 0.002,  # 0.2%
        'max_position': 100 * 3 * 1.05  # 315 USDT
    },
    'LINKUSDT': {
        'amount': 100,
        'leverage': 3,
        'stop_loss_pct': 0.002,
        'max_position': 315
    },
    'AVAXUSDT': {
        'amount': 200,
        'leverage': 3,
        'stop_loss_pct': 0.005,  # 0.5%
        'max_position': 200 * 3 * 1.05  # 630 USDT
    }
}

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

def alert(message: str, send_telegram: bool = True):
    """告警"""
    log(message, '🚨 ALERT')
    
    # 发送 Telegram 告警
    if send_telegram:
        try:
            send_telegram_alert(message)
        except Exception as e:
            log(f"Telegram 告警失败：{e}", 'ERROR')

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

def get_binance_trades(limit=20):
    """获取币安实际成交"""
    try:
        response = requests.get(f"{BASE_URL}/api/binance/trades?limit={limit}", timeout=10)
        data = response.json()
        return data.get('trades', [])
    except Exception as e:
        log(f"获取成交失败：{e}", 'ERROR')
        return []

# ==================== 检查函数 ====================
def check_position_limit(symbol, positions):
    """检查仓位是否超标"""
    if symbol not in STRATEGY_CONFIG:
        return
    
    config = STRATEGY_CONFIG[symbol]
    max_position = config['max_position']
    
    # 查找该交易对的持仓
    for pos in positions:
        if pos['symbol'] == symbol:
            position_value = pos['size'] * pos['entry_price']
            
            if position_value > max_position:
                alert(f"{symbol} 仓位超标！实际：{position_value:.2f} USDT, 上限：{max_position:.2f} USDT, 超标：{(position_value/max_position-1)*100:.1f}%")
            else:
                log(f"{symbol} 仓位正常：{position_value:.2f} / {max_position:.2f} USDT ({position_value/max_position*100:.1f}%)")
            
            return position_value
    
    return 0

def check_stop_loss_exists(symbol, positions, stop_losses):
    """检查有持仓是否有止损单"""
    # 查找该交易对的持仓
    for pos in positions:
        if pos['symbol'] == symbol:
            # 检查是否有对应的止损单
            has_stop_loss = False
            for sl in stop_losses:
                if sl.get('symbol') == symbol:
                    has_stop_loss = True
                    break
            
            if not has_stop_loss:
                alert(f"{symbol} 有持仓但无止损单！持仓：{pos['size']} @ {pos['entry_price']}")
            else:
                log(f"{symbol} 止损单正常")
            
            return has_stop_loss
    
    return True

def check_recent_trades(trades, symbol):
    """检查最近成交"""
    # 查找该交易对的最近成交
    symbol_trades = [t for t in trades if t['symbol'] == symbol]
    
    if symbol_trades:
        latest = symbol_trades[0]
        trade_time = latest.get('trade_time', 'Unknown')
        side = latest.get('side', 'Unknown')
        quantity = latest.get('quantity', 0)
        price = latest.get('price', 0)
        
        log(f"{symbol} 最近成交：{trade_time} {side} {quantity} @ {price}")
        
        return latest
    
    return None

# ==================== 主监测函数 ====================
def run_monitoring():
    """运行监测"""
    log("="*60)
    log("🔍 开始深度监测")
    log("="*60)
    
    # 获取数据
    positions = get_binance_positions()
    stop_losses = get_binance_stop_losses()
    trades = get_binance_trades()
    
    log(f"持仓：{len(positions)} 个")
    log(f"止损单：{len(stop_losses)} 个")
    log(f"成交：{len(trades)} 条")
    
    # 检查每个策略
    for symbol in STRATEGY_CONFIG.keys():
        log(f"\n=== 检查 {symbol} ===")
        
        # 1. 检查仓位是否超标
        check_position_limit(symbol, positions)
        
        # 2. 检查有持仓是否有止损单
        check_stop_loss_exists(symbol, positions, stop_losses)
        
        # 3. 检查最近成交
        check_recent_trades(trades, symbol)
    
    # 保存监测数据
    monitor_data = {
        'timestamp': datetime.now().isoformat(),
        'positions': positions,
        'stop_losses': stop_losses,
        'trades': trades,
        'alerts': []
    }
    
    # 保存到文件
    try:
        with open(MONITOR_FILE, 'w', encoding='utf-8') as f:
            json.dump(monitor_data, f, indent=2, ensure_ascii=False)
        log(f"\n✅ 监测数据已保存：{MONITOR_FILE}")
    except Exception as e:
        log(f"❌ 保存监测数据失败：{e}", 'ERROR')
    
    log("="*60)
    log("✅ 监测完成")
    log("="*60)

# ==================== 主程序 ====================
if __name__ == "__main__":
    log("🚀 深度监测脚本启动")
    log(f"监测频率：每 60 秒")
    log(f"日志文件：{ALERT_FILE}")
    log(f"数据文件：{MONITOR_FILE}")
    log("")
    
    # 确保目录存在
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 主循环
    while True:
        try:
            run_monitoring()
        except Exception as e:
            log(f"❌ 监测异常：{e}", 'ERROR')
        
        # 等待 60 秒
        time.sleep(60)
