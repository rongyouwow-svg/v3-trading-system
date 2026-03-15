#!/usr/bin/env python3
"""
🔍 止损单创建流程监控

监控内容:
    1. 开仓后是否正确获取入场价
    2. 止损单是否成功创建
    3. 重试次数统计
    4. 失败案例记录

运行时间：2026-03-15 01:30 - 08:00
"""

import requests
import time
import json
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path('/home/admin/.openclaw/workspace/quant/v3-architecture/logs')
MONITOR_FILE = LOGS_DIR / 'stop_loss_monitor.json'

def check_stop_loss_creation():
    """检查止损单创建流程"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 检查止损单创建流程")
    
    # 检查策略运行状态
    try:
        response = requests.get("http://localhost:3000/api/strategy/active", timeout=10)
        strategies = response.json().get('active_strategies', [])
        
        print(f"  当前运行策略：{len(strategies)} 个")
        
        for s in strategies:
            symbol = s['symbol']
            signals_sent = s.get('signals_sent', 0)
            signals_executed = s.get('signals_executed', 0)
            success_rate = (signals_executed / signals_sent * 100) if signals_sent > 0 else 0
            
            print(f"  - {symbol}: 信号{signals_sent}/{signals_executed}, 成功率{success_rate:.1f}%")
            
            # 信号成功率过低告警
            if signals_sent > 10 and success_rate < 10:
                print(f"    ⚠️ 警告：信号成功率过低，可能 RSI 波动过大")
    except Exception as e:
        print(f"  ❌ 获取策略状态失败：{e}")
    
    # 1. 获取当前持仓
    try:
        response = requests.get("http://localhost:3000/api/binance/positions", timeout=10)
        positions = response.json().get('positions', [])
        
        print(f"  当前持仓：{len(positions)} 个")
        
        for pos in positions:
            if float(pos['size']) > 0:
                symbol = pos['symbol']
                entry_price = float(pos['entry_price'])
                print(f"  - {symbol}: 入场价 {entry_price}")
        
    except Exception as e:
        print(f"  ❌ 获取持仓失败：{e}")
    
    # 2. 获取当前止损单
    try:
        response = requests.get("http://localhost:3000/api/binance/stop-loss", timeout=10)
        stop_losses = response.json().get('orders', [])
        
        print(f"  当前止损单：{len(stop_losses)} 个")
        
        for sl in stop_losses:
            symbol = sl['symbol']
            trigger_price = sl['trigger_price']
            quantity = sl['quantity']
            status = sl['status']
            print(f"  - {symbol}: 触发价 {trigger_price}, 数量 {quantity}, 状态 {status}")
        
    except Exception as e:
        print(f"  ❌ 获取止损单失败：{e}")
    
    # 3. 检查策略日志（查看重试次数）
    try:
        log_file = LOGS_DIR / 'supervisor_eth_out.log'
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-50:]
                
            retry_count = 0
            success_count = 0
            for line in lines:
                if '重试' in line:
                    retry_count += 1
                if '获取到入场价' in line:
                    success_count += 1
            
            print(f"  策略日志统计:")
            print(f"    重试次数：{retry_count}")
            print(f"    成功获取：{success_count}")
    except Exception as e:
        print(f"  ❌ 读取策略日志失败：{e}")
    
    # 4. 保存监控数据
    monitor_data = {
        'timestamp': datetime.now().isoformat(),
        'positions_count': len(positions) if 'positions' in dir() else 0,
        'stop_losses_count': len(stop_losses) if 'stop_losses' in dir() else 0,
        'retry_count': retry_count if 'retry_count' in dir() else 0,
        'success_count': success_count if 'success_count' in dir() else 0
    }
    
    try:
        with open(MONITOR_FILE, 'a', encoding='utf-8') as f:
            json.dump(monitor_data, f, ensure_ascii=False)
            f.write('\n')
        print(f"  ✅ 监控数据已保存")
    except Exception as e:
        print(f"  ❌ 保存监控数据失败：{e}")

if __name__ == "__main__":
    print("="*60)
    print("🔍 止损单创建流程监控启动")
    print(f"监控时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 08:00")
    print("="*60)
    
    # 立即检查一次
    check_stop_loss_creation()
    
    # 每 30 分钟检查一次
    while datetime.now().hour < 8:
        time.sleep(1800)  # 30 分钟
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 定期检查")
        check_stop_loss_creation()
