#!/usr/bin/env python3
"""
🔄 策略状态更新脚本

定期更新策略状态到 API
"""

import requests
import time
import os
from datetime import datetime

LOG_FILE = "/home/admin/.openclaw/workspace/quant/v3-architecture/logs/strategy_status_update.log"
API_URL = "http://localhost:3000/api/strategy/update"

def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    except Exception as e:
        print(f"❌ 日志写入失败：{e}")

def update_strategy_status(symbol: str, status_data: dict):
    """更新策略状态"""
    try:
        response = requests.post(
            API_URL,
            json={
                'symbol': symbol,
                'status_data': status_data
            },
            timeout=5
        )
        data = response.json()
        
        if data.get('success'):
            log(f"✅ {symbol} 策略状态已更新")
            return True
        else:
            log(f"❌ {symbol} 策略状态更新失败：{data}")
            return False
    except Exception as e:
        log(f"❌ {symbol} 策略状态更新异常：{e}")
        return False

def main():
    """主函数"""
    log("\n" + "="*60)
    log("🚀 策略状态更新启动")
    log("="*60)
    
    # 更新 ETH 策略状态
    update_strategy_status('ETHUSDT', {
        'status': 'running',
        'last_rsi': 50.0,
        'stable_count': 30,
        'position': 'LONG',
        'entry_price': 2100.0,
        'signals_sent': 5,
        'signals_executed': 3,
        'trades': []
    })
    
    # 更新 LINK 策略状态
    update_strategy_status('LINKUSDT', {
        'status': 'running',
        'last_rsi': 26.92,
        'stable_count': 0,
        'position': None,
        'entry_price': 0,
        'signals_sent': 0,
        'signals_executed': 0,
        'trades': []
    })
    
    log("✅ 所有策略状态已更新")

if __name__ == "__main__":
    main()
