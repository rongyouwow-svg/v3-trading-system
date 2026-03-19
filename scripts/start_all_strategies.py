#!/usr/bin/env python3
"""
🚀 v3.1 实盘测试启动脚本

启动 3 个策略:
    1. ETH RSI (100 USDT, 0.2% 止损)
    2. LINK RSI (100 USDT, 0.2% 止损)
    3. AVAX RSI 分批 (200 USDT, 0.5% 止损)

用法:
    python3 scripts/start_all_strategies.py
"""

import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace/quant/v3-architecture')

from core.strategy.strategy_manager import StrategyManager
from core.execution.engine import ExecutionEngine
import time
import json
from datetime import datetime

print("="*70)
print("🚀 v3.1 实盘测试 - 启动 3 个策略")
print("="*70)
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("")

# 创建 Mock 连接器（实际应使用真实币安连接器）
class MockBinanceConnector:
    def get_positions(self, symbol=None):
        return []
    
    def create_order(self, **kwargs):
        print(f"  📝 [模拟] 创建订单：{kwargs}")
        return {'success': True, 'order_id': 'mock_order_' + str(time.time())}

connector = MockBinanceConnector()

# 创建执行引擎
print("📊 创建执行引擎...")
engine = ExecutionEngine(connector)
print("✅ 执行引擎创建完成")
print("")

# 创建策略管理器
print("📊 创建策略管理器...")
manager = StrategyManager(max_workers=10)
print("✅ 策略管理器创建完成")
print("")

# 配置 3 个策略
strategies_config = [
    {
        'name': 'ETH_RSI',
        'symbol': 'ETHUSDT',
        'type': 'rsi_strategy',
        'leverage': 3,
        'amount': 100,
        'stop_loss_pct': 0.002  # 0.2% 策略止损
    },
    {
        'name': 'LINK_RSI',
        'symbol': 'LINKUSDT',
        'type': 'rsi_strategy',
        'leverage': 3,
        'amount': 100,
        'stop_loss_pct': 0.002  # 0.2% 策略止损
    },
    {
        'name': 'AVAX_RSI_SCALE',
        'symbol': 'AVAXUSDT',
        'type': 'rsi_scale_in_strategy',
        'leverage': 3,
        'amount': 200,
        'stop_loss_pct': 0.005  # 0.5% 策略止损
    }
]

# 加载并启动策略
print("="*70)
print("📊 加载并启动策略")
print("="*70)

for config in strategies_config:
    print(f"\n📈 策略：{config['name']}")
    print(f"  - 交易对：{config['symbol']}")
    print(f"  - 杠杆：{config['leverage']}x")
    print(f"  - 保证金：{config['amount']} USDT")
    print(f"  - 止损：{config['stop_loss_pct']*100}%")
    
    # 加载策略
    success = manager.load_strategy(config['name'], config)
    if not success:
        print(f"  ❌ 加载失败")
        continue
    
    # 启动策略
    success = manager.start_strategy(config['name'])
    if success:
        print(f"  ✅ 启动成功")
        
        # 注册到执行引擎
        engine.register_strategy(config['name'], manager.strategies[config['name']])
    else:
        print(f"  ❌ 启动失败")

print("")
print("="*70)
print("📊 策略状态")
print("="*70)

for status in manager.get_all_status():
    stop_loss_info = f"{status['stop_loss_pct']*100}%" if status['stop_loss_pct'] else "5% (兜底)"
    print(f"✅ {status['name']}: {status['status']} (止损：{stop_loss_info})")

print("")
print("="*70)
print("🎯 监测记录已启动")
print("="*70)
print(f"监测文件：/root/.openclaw/workspace/quant/v3-architecture/logs/live_test_monitor.json")
print("")
print("💡 提示：运行 python3 scripts/monitor_live_test.py 查看实时监测")
print("")

# 保存策略配置
monitor_data = {
    'start_time': datetime.now().isoformat(),
    'strategies': strategies_config,
    'status': 'running'
}

os.makedirs('/root/.openclaw/workspace/quant/v3-architecture/logs', exist_ok=True)
with open('/root/.openclaw/workspace/quant/v3-architecture/logs/live_test_config.json', 'w', encoding='utf-8') as f:
    json.dump(monitor_data, f, indent=2, ensure_ascii=False)

print("✅ 策略配置已保存")
# 启动策略（后台循环运行）
print("")
print("="*70)
print("🚀 启动策略进程（后台循环运行）")
print("="*70)

import subprocess
import os

# 策略进程列表
processes = []

# 启动 ETH 策略
print("\n📈 启动 ETH_RSI...")
proc = subprocess.Popen(
    ['python3', 'strategies/rsi_1min_strategy.py'],
    cwd='/root/.openclaw/workspace/quant/v3-architecture',
    env={**os.environ, 'PYTHONPATH': '/root/.openclaw/workspace/quant/v3-architecture'}
)
processes.append(('ETH_RSI', proc))
print(f"  ✅ ETH_RSI 已启动 (PID: {proc.pid})")

# 启动 LINK 策略
print("\n📈 启动 LINK_RSI...")
proc = subprocess.Popen(
    ['python3', 'strategies/link_rsi_detailed_strategy.py'],
    cwd='/root/.openclaw/workspace/quant/v3-architecture',
    env={**os.environ, 'PYTHONPATH': '/root/.openclaw/workspace/quant/v3-architecture'}
)
processes.append(('LINK_RSI', proc))
print(f"  ✅ LINK_RSI 已启动 (PID: {proc.pid})")

# 启动 AVAX 策略
print("\n📈 启动 AVAX_RSI_SCALE...")
proc = subprocess.Popen(
    ['python3', 'strategies/rsi_scale_in_strategy.py'],
    cwd='/root/.openclaw/workspace/quant/v3-architecture',
    env={**os.environ, 'PYTHONPATH': '/root/.openclaw/workspace/quant/v3-architecture'}
)
processes.append(('AVAX_RSI_SCALE', proc))
print(f"  ✅ AVAX_RSI_SCALE 已启动 (PID: {proc.pid})")

print("")
print("="*70)
print(f"🎉 3 个策略已全部启动（后台循环运行）！")
print("="*70)
print("")
print("💡 提示:")
print("  - 策略正在后台循环运行，每根 K 线自动检查信号")
print("  - 运行 python3 scripts/monitor_live_test.py 查看实时监测")
print("  - 查看日志：tail -f logs/strategies_restart.log")
print("")

# 保存进程 PID
pid_data = {
    'start_time': datetime.now().isoformat(),
    'processes': [
        {'name': name, 'pid': proc.pid}
        for name, proc in processes
    ]
}

with open('/root/.openclaw/workspace/quant/v3-architecture/logs/strategy_processes.json', 'w', encoding='utf-8') as f:
    json.dump(pid_data, f, indent=2, ensure_ascii=False)

print("✅ 策略进程信息已保存")
print("")
