#!/usr/bin/env python3
"""
🧪 v3.1 重构集成测试

测试范围:
    1. 策略模块导入
    2. 策略管理器
    3. 执行引擎
    4. API 接口
    5. 前端功能

用法:
    python3 tests/test_integration_v3.py
"""

import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/home/admin/.openclaw/workspace/quant/v3-architecture')

print("="*70)
print("🧪 v3.1 重构集成测试")
print("="*70)
print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("")

# 测试计数器
tests_passed = 0
tests_failed = 0
tests_total = 0

def test_result(name, success, error_msg=None):
    global tests_passed, tests_failed, tests_total
    tests_total += 1
    if success:
        tests_passed += 1
        print(f"✅ {name}")
    else:
        tests_failed += 1
        print(f"❌ {name}: {error_msg}")

# ============================================================================
# 测试 1: 策略模块导入
# ============================================================================
print("="*70)
print("测试 1: 策略模块导入")
print("="*70)

try:
    from core.strategy.modules import RSIStrategy, RSI1MinStrategy, RSIScaleInStrategy
    test_result("RSIStrategy 导入", True)
    test_result("RSI1MinStrategy 导入", True)
    test_result("RSIScaleInStrategy 导入", True)
except Exception as e:
    test_result("策略模块导入", False, str(e))

# ============================================================================
# 测试 2: 策略管理器
# ============================================================================
print("")
print("="*70)
print("测试 2: 策略管理器")
print("="*70)

try:
    from core.strategy.strategy_manager import StrategyManager
    
    # 创建策略管理器
    manager = StrategyManager(max_workers=5)
    test_result("StrategyManager 创建", True)
    
    # 测试策略加载
    config = {
        'symbol': 'ETHUSDT',
        'type': 'rsi_strategy',
        'leverage': 3,
        'amount': 100,
        'stop_loss_pct': 0.002
    }
    success = manager.load_strategy('TEST_ETH', config)
    test_result("策略加载", success)
    
    # 测试策略启动
    success = manager.start_strategy('TEST_ETH')
    test_result("策略启动", success)
    
    # 测试策略状态
    status = manager.get_strategy_status('TEST_ETH')
    test_result("策略状态查询", status is not None)
    
    # 测试策略停止
    success = manager.stop_strategy('TEST_ETH')
    test_result("策略停止", success)
    
    # 测试策略卸载
    success = manager.unload_strategy('TEST_ETH')
    test_result("策略卸载", success)
    
    # 清理
    manager.shutdown()
    
except Exception as e:
    test_result("策略管理器测试", False, str(e))

# ============================================================================
# 测试 3: 执行引擎
# ============================================================================
print("")
print("="*70)
print("测试 3: 执行引擎")
print("="*70)

try:
    from core.execution.engine import ExecutionEngine
    
    # 创建 Mock 连接器
    class MockConnector:
        def get_positions(self, symbol=None):
            return []
    
    connector = MockConnector()
    engine = ExecutionEngine(connector)
    test_result("ExecutionEngine 创建", True)
    
    # 测试止损管理器初始化
    test_result("StopLossManager 初始化", engine.stop_loss_manager is not None)
    
    # 测试持仓管理器初始化
    test_result("PositionManager 初始化", engine.position_manager is not None)
    
    # 测试订单管理器初始化
    test_result("OrderManager 初始化", engine.order_manager is not None)
    
except Exception as e:
    test_result("执行引擎测试", False, str(e))

# ============================================================================
# 测试 4: RSI 计算
# ============================================================================
print("")
print("="*70)
print("测试 4: RSI 计算")
print("="*70)

try:
    from core.strategy.modules import RSIStrategy
    
    strategy = RSIStrategy(symbol='ETHUSDT')
    
    # 模拟 K 线数据（上涨趋势）
    klines = [{'close': 2000 + i*10} for i in range(20)]
    rsi = strategy.calculate_rsi(klines)
    
    test_result("RSI 计算", rsi > 50, f"RSI={rsi:.2f} (预期>50)")
    
except Exception as e:
    test_result("RSI 计算测试", False, str(e))

# ============================================================================
# 测试 5: 信号生成（2 根 K 线确认）
# ============================================================================
print("")
print("="*70)
print("测试 5: 信号生成（2 根 K 线确认）")
print("="*70)

try:
    from core.strategy.modules import RSIStrategy
    
    strategy = RSIStrategy(symbol='ETHUSDT', stop_loss_pct=0.002)
    strategy.start()
    
    market_data = {
        'klines': [{'close': 2000 + i*5} for i in range(20)],
        'current_price': 2100,
        'timestamp': '2026-03-14T17:16:00Z'
    }
    
    # 第 1 次调用（等待确认）
    signal1 = strategy.on_tick(market_data)
    test_result("第 1 次调用（等待）", signal1 is None)
    
    # 第 2 次调用（确认开仓）
    signal2 = strategy.on_tick(market_data)
    test_result("第 2 次调用（开仓）", signal2 is not None and signal2.get('action') == 'open')
    
    if signal2:
        test_result("止损配置传递", signal2.get('stop_loss_pct') == 0.002)
    
except Exception as e:
    test_result("信号生成测试", False, str(e))

# ============================================================================
# 测试 6: 分批建仓策略
# ============================================================================
print("")
print("="*70)
print("测试 6: 分批建仓策略")
print("="*70)

try:
    from core.strategy.modules import RSIScaleInStrategy
    
    strategy = RSIScaleInStrategy(symbol='AVAXUSDT', leverage=3, total_amount=200, stop_loss_pct=0.005)
    strategy.start()
    
    # 验证分批配置
    test_result("分批配置", len(strategy.scale_in_ratios) == 3)
    test_result("第 1 批比例", strategy.scale_in_ratios[0] == 0.30)
    test_result("第 2 批比例", strategy.scale_in_ratios[1] == 0.50)
    test_result("第 3 批比例", strategy.scale_in_ratios[2] == 0.20)
    
    # 验证止损配置
    test_result("止损配置", strategy.stop_loss_pct == 0.005)
    
except Exception as e:
    test_result("分批建仓测试", False, str(e))

# ============================================================================
# 测试 7: API 接口（需要 Web 服务运行）
# ============================================================================
print("")
print("="*70)
print("测试 7: API 接口")
print("="*70)

try:
    import requests
    
    # 测试策略列表 API
    response = requests.get('http://localhost:3000/api/strategy/list', timeout=5)
    test_result("GET /api/strategy/list", response.status_code == 200)
    
    # 测试止损单 API
    response = requests.get('http://localhost:3000/api/binance/stop-loss', timeout=5)
    test_result("GET /api/binance/stop-loss", response.status_code == 200)
    
    # 测试持仓 API
    response = requests.get('http://localhost:3000/api/binance/positions', timeout=5)
    test_result("GET /api/binance/positions", response.status_code == 200)
    
except Exception as e:
    test_result("API 接口测试", False, f"Web 服务可能未运行：{str(e)}")

# ============================================================================
# 测试总结
# ============================================================================
print("")
print("="*70)
print("📊 测试总结")
print("="*70)
print(f"总测试数：{tests_total}")
print(f"✅ 通过：{tests_passed}")
print(f"❌ 失败：{tests_failed}")
print(f"通过率：{tests_passed/tests_total*100:.1f}%")
print("")

if tests_failed == 0:
    print("🎉 所有测试通过！v3.1 重构验证成功！")
else:
    print(f"⚠️ {tests_failed} 个测试失败，请检查错误信息")

print("")
print("="*70)

# 返回退出码
sys.exit(0 if tests_failed == 0 else 1)
