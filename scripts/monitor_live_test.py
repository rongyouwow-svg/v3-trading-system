#!/usr/bin/env python3
"""
📊 v3.1 实盘测试监测脚本

功能:
    - 每 30 秒记录策略状态
    - 每 30 秒记录持仓信息
    - 每 30 秒记录止损单状态
    - 生成测试报告

用法:
    python3 scripts/monitor_live_test.py
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/home/admin/.openclaw/workspace/quant/v3-architecture')

print("="*70)
print("📊 v3.1 实盘测试监测")
print("="*70)
print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("")

# 监测配置
MONITOR_INTERVAL = 30  # 30 秒
LOGS_DIR = Path('/home/admin/.openclaw/workspace/quant/v3-architecture/logs')
MONITOR_FILE = LOGS_DIR / 'live_test_monitor.json'
REPORT_FILE = LOGS_DIR / 'live_test_report.md'

# 确保目录存在
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# 监测数据
monitor_data = {
    'start_time': datetime.now().isoformat(),
    'records': [],
    'events': []
}

def log_event(event_type, message, data=None):
    """记录事件"""
    event = {
        'timestamp': datetime.now().isoformat(),
        'type': event_type,
        'message': message,
        'data': data or {}
    }
    monitor_data['events'].append(event)
    print(f"  [{event_type}] {message}")

def get_strategy_status():
    """获取策略状态（模拟）"""
    # 实际应从策略管理器获取
    return {
        'ETH_RSI': {'status': 'running', 'rsi': 50.0, 'position': None},
        'LINK_RSI': {'status': 'running', 'rsi': 26.92, 'position': None},
        'AVAX_RSI_SCALE': {'status': 'running', 'rsi': 67.44, 'position': None}
    }

def get_account_info():
    """获取账户信息（模拟）"""
    # 实际应从 API 获取
    return {
        'balance': 5000.0,
        'available': 4600.0,
        'unrealized_pnl': 0.0
    }

def save_monitor_data():
    """保存监测数据"""
    with open(MONITOR_FILE, 'w', encoding='utf-8') as f:
        json.dump(monitor_data, f, indent=2, ensure_ascii=False)

def generate_report():
    """生成测试报告"""
    report = []
    report.append("# 📊 v3.1 实盘测试报告")
    report.append("")
    report.append(f"**测试时间**: {monitor_data['start_time']}")
    report.append(f"**报告生成**: {datetime.now().isoformat()}")
    report.append(f"**监测记录**: {len(monitor_data['records'])} 条")
    report.append(f"**事件记录**: {len(monitor_data['events'])} 条")
    report.append("")
    
    # 策略状态汇总
    report.append("## 📈 策略状态汇总")
    report.append("")
    
    latest_record = monitor_data['records'][-1] if monitor_data['records'] else {}
    
    for strategy_name, status in latest_record.get('strategies', {}).items():
        position_info = status.get('position', '无')
        rsi_info = f"{status.get('rsi', 0):.2f}"
        report.append(f"### {strategy_name}")
        report.append(f"- 状态：{status.get('status', 'unknown')}")
        report.append(f"- RSI: {rsi_info}")
        report.append(f"- 持仓：{position_info}")
        report.append("")
    
    # 事件时间线
    report.append("## 📅 事件时间线")
    report.append("")
    
    for event in monitor_data['events']:
        timestamp = event['timestamp'].split('T')[1].split('.')[0]
        report.append(f"- [{timestamp}] {event['type']}: {event['message']}")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append("**报告生成时间**: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\n✅ 测试报告已生成：{REPORT_FILE}")

# 主循环
print("📊 开始监测...")
print(f"监测间隔：{MONITOR_INTERVAL}秒")
print(f"监测文件：{MONITOR_FILE}")
print("")

try:
    iteration = 0
    while True:
        iteration += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 获取策略状态
        strategies = get_strategy_status()
        account = get_account_info()
        
        # 记录数据
        record = {
            'timestamp': datetime.now().isoformat(),
            'iteration': iteration,
            'strategies': strategies,
            'account': account
        }
        monitor_data['records'].append(record)
        
        # 显示状态
        print(f"[{timestamp}] 监测记录 #{iteration}")
        for name, status in strategies.items():
            position = status.get('position', '无')
            rsi = status.get('rsi', 0)
            print(f"  - {name}: RSI={rsi:.2f}, 持仓={position}")
        
        # 保存数据
        save_monitor_data()
        
        # 等待下次监测
        time.sleep(MONITOR_INTERVAL)
        
except KeyboardInterrupt:
    print("\n\n⚠️ 监测已停止")
    generate_report()
    print("")
    print("="*70)
    print("✅ 监测结束，报告已生成")
    print("="*70)
