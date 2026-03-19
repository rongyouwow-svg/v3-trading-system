#!/usr/bin/env python3
"""
🦞 策略引擎 + 执行引擎集成测试

测试内容:
    1. 策略启动 → 订单创建 → 止损单创建
    2. 完整交易流程
    3. 心跳检测集成
    4. 状态持久化验证

用法:
    python tests/integration/test_strategy_execution_integration.py
"""

import sys
import os
import time
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.strategy.manager import StrategyManager
from core.execution.order_manager import OrderManager
from core.execution.stop_loss_manager import StopLossManager
from modules.models.order import Order, OrderType, OrderSide, OrderStatus
from modules.utils.result import Result
from modules.health.heartbeat import get_heartbeat_monitor, reset_heartbeat_monitor


def print_section(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"📊 {title}")
    print("="*60)


def print_step(step, description):
    """打印步骤"""
    print(f"\n[{step}] {description}")


def cleanup():
    """清理测试环境"""
    # 清理持久化文件
    files = [
        "/root/.openclaw/workspace/quant/v3-architecture/data/plugin_strategies.json",
        "/root/.openclaw/workspace/quant/v3-architecture/data/stop_orders.json"
    ]
    for f in files:
        if os.path.exists(f):
            os.remove(f)
            print(f"✅ 已清理：{f}")


def create_mock_connector():
    """创建模拟连接器"""
    connector = Mock()
    
    # 模拟下单
    connector.place_order.return_value = Result.ok(data={
        'order_id': 'TEST123',
        'status': 'FILLED',
        'filled_quantity': '0.1',
        'avg_price': '2050.5'
    })
    
    # 模拟取消订单
    connector.cancel_order.return_value = Result.ok(data={
        'order_id': 'TEST123',
        'status': 'CANCELED'
    })
    
    # 模拟创建止损单
    connector.create_stop_loss_order.return_value = Result.ok(data={
        'algo_id': 'SL_TEST123',
        'status': 'WAIT_TO_TRIGGER'
    })
    
    # 模拟取消止损单
    connector.cancel_stop_loss_order.return_value = Result.ok(data={
        'algo_id': 'SL_TEST123',
        'status': 'CANCELED'
    })
    
    return connector


def test_strategy_execution_integration():
    """测试 1: 策略引擎 + 执行引擎集成"""
    print_section("测试 1: 策略引擎 + 执行引擎集成")
    
    cleanup()
    reset_heartbeat_monitor()
    
    # 创建组件
    connector = create_mock_connector()
    strategy_manager = StrategyManager(connector=connector)
    order_manager = OrderManager(connector)
    stop_loss_manager = StopLossManager(connector)
    
    print_step(1, "启动策略")
    result = strategy_manager.start_strategy(
        symbol="ETHUSDT",
        strategy_id="breakout",
        leverage=5,
        amount=100,
        side="LONG"
    )
    
    assert result.is_success, f"策略启动失败：{result.message}"
    print(f"  ✅ 策略启动成功：{result.data['strategy_id']}")
    
    print_step(2, "创建订单（模拟策略信号）")
    order = Order(
        symbol="ETHUSDT",
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        quantity=Decimal('0.1')
    )
    
    result = order_manager.create_order(order)
    assert result.is_success, f"订单创建失败：{result.message}"
    print(f"  ✅ 订单创建成功：{result.data['order_id']}")
    
    print_step(3, "创建止损单（订单成交后）")
    result = stop_loss_manager.create_stop_loss(
        symbol="ETHUSDT",
        trigger_price=Decimal('2000'),
        quantity=Decimal('0.1'),
        side="SELL"
    )
    assert result.is_success, f"止损单创建失败：{result.message}"
    print(f"  ✅ 止损单创建成功：{result.data['algo_id']}")
    
    print_step(4, "验证心跳检测")
    time.sleep(0.1)
    
    health = strategy_manager.get_strategy_health("ETHUSDT")
    assert health["is_healthy"], f"策略健康状态异常：{health['health_status']}"
    print(f"  ✅ 策略健康状态：{health['health_status']}")
    
    print_step(5, "停止策略（自动取消止损单）")
    result = stop_loss_manager.cancel_stop_loss("ETHUSDT", result.data['algo_id'])
    assert result.is_success, f"止损单取消失败：{result.message}"
    print(f"  ✅ 止损单取消成功")
    
    result = strategy_manager.stop_strategy("ETHUSDT")
    assert result.is_success, f"策略停止失败：{result.message}"
    print(f"  ✅ 策略停止成功")
    
    print("\n✅ 测试 1: 策略引擎 + 执行引擎集成 - 通过")
    return True


def test_full_trading_flow():
    """测试 2: 完整交易流程"""
    print_section("测试 2: 完整交易流程")
    
    cleanup()
    reset_heartbeat_monitor()
    
    connector = create_mock_connector()
    strategy_manager = StrategyManager(connector=connector)
    order_manager = OrderManager(connector)
    stop_loss_manager = StopLossManager(connector)
    
    print_step(1, "启动策略 ETHUSDT")
    result = strategy_manager.start_strategy("ETHUSDT", "breakout", leverage=5, amount=100)
    assert result.is_success
    
    print_step(2, "策略生成买入信号 → 创建订单")
    order = Order("ETHUSDT", OrderSide.BUY, OrderType.MARKET, Decimal('0.1'))
    result = order_manager.create_order(order)
    assert result.is_success
    order_id = result.data['order_id']
    
    print_step(3, "订单成交 → 创建止损单")
    result = stop_loss_manager.create_stop_loss(
        "ETHUSDT", Decimal('2000'), Decimal('0.1'), "SELL"
    )
    assert result.is_success
    algo_id = result.data['algo_id']
    
    print_step(4, "查询订单状态")
    order_status = order_manager.get_order_status(order_id)
    assert order_status is not None
    print(f"  订单状态：{order_status.status.value}")
    
    print_step(5, "查询止损单状态")
    stop_order = stop_loss_manager.get_stop_order(algo_id)
    assert stop_order is not None
    print(f"  止损单状态：{stop_order['status']}")
    
    print_step(6, "查询策略健康状态")
    health = strategy_manager.get_strategy_health("ETHUSDT")
    assert health["is_healthy"]
    print(f"  策略健康：{health['health_status']}")
    
    print_step(7, "获取健康报告")
    report = strategy_manager.get_all_health_status()
    assert report["total_strategies"] > 0
    assert report["healthy_count"] > 0
    print(f"  健康报告：总计{report['total_strategies']}个，健康{report['healthy_count']}个")
    
    print_step(8, "停止策略 → 取消止损单")
    result = stop_loss_manager.cancel_stop_loss("ETHUSDT", algo_id)
    assert result.is_success
    
    result = strategy_manager.stop_strategy("ETHUSDT")
    assert result.is_success
    
    print("\n✅ 测试 2: 完整交易流程 - 通过")
    return True


def test_concurrent_strategies():
    """测试 3: 多策略并发"""
    print_section("测试 3: 多策略并发")
    
    cleanup()
    reset_heartbeat_monitor()
    
    connector = create_mock_connector()
    strategy_manager = StrategyManager(connector=connector)
    order_manager = OrderManager(connector)
    stop_loss_manager = StopLossManager(connector)
    
    symbols = ["ETHUSDT", "BTCUSDT", "AVAXUSDT"]
    
    print_step(1, "启动多个策略")
    for symbol in symbols:
        result = strategy_manager.start_strategy(symbol, "breakout", leverage=5, amount=100)
        assert result.is_success, f"{symbol} 策略启动失败"
        print(f"  ✅ {symbol} 策略已启动")
    
    print_step(2, "为每个策略创建订单")
    for symbol in symbols:
        order = Order(symbol, OrderSide.BUY, OrderType.MARKET, Decimal('0.1'))
        result = order_manager.create_order(order)
        assert result.is_success, f"{symbol} 订单创建失败"
        print(f"  ✅ {symbol} 订单已创建")
    
    print_step(3, "为每个策略创建止损单")
    for symbol in symbols:
        result = stop_loss_manager.create_stop_loss(
            symbol, Decimal('2000'), Decimal('0.1'), "SELL"
        )
        assert result.is_success, f"{symbol} 止损单创建失败"
        print(f"  ✅ {symbol} 止损单已创建")
    
    print_step(4, "验证所有策略健康状态")
    report = strategy_manager.get_all_health_status()
    assert report["total_strategies"] == 3
    assert report["healthy_count"] == 3
    print(f"  ✅ 所有策略健康：{report['healthy_count']}/{report['total_strategies']}")
    
    print_step(5, "停止所有策略")
    for symbol in symbols:
        # 取消止损单
        stop_orders = stop_loss_manager.get_stop_orders_by_symbol(symbol)
        for stop_order in stop_orders:
            stop_loss_manager.cancel_stop_loss(symbol, stop_order['algo_id'])
        
        # 停止策略
        result = strategy_manager.stop_strategy(symbol)
        assert result.is_success, f"{symbol} 策略停止失败"
        print(f"  ✅ {symbol} 策略已停止")
    
    print("\n✅ 测试 3: 多策略并发 - 通过")
    return True


def test_persistence_recovery():
    """测试 4: 持久化恢复"""
    print_section("测试 4: 持久化恢复")
    
    cleanup()
    reset_heartbeat_monitor()
    
    connector = create_mock_connector()
    
    print_step(1, "创建策略管理器并启动策略")
    strategy_manager1 = StrategyManager(connector=connector)
    result = strategy_manager1.start_strategy("ETHUSDT", "breakout", leverage=5, amount=100)
    assert result.is_success
    
    print_step(2, "创建订单和止损单")
    order_manager = OrderManager(connector)
    stop_loss_manager = StopLossManager(connector)
    
    order = Order("ETHUSDT", OrderSide.BUY, OrderType.MARKET, Decimal('0.1'))
    result = order_manager.create_order(order)
    assert result.is_success
    
    result = stop_loss_manager.create_stop_loss(
        "ETHUSDT", Decimal('2000'), Decimal('0.1'), "SELL"
    )
    assert result.is_success
    algo_id = result.data['algo_id']
    
    print_step(3, "模拟重启：创建新的策略管理器")
    strategy_manager2 = StrategyManager(connector=connector)
    
    # 验证策略已恢复
    strategies = strategy_manager2.get_active_strategies()
    assert len(strategies) > 0, "策略未恢复"
    print(f"  ✅ 策略已恢复：{len(strategies)}个")
    
    print_step(4, "验证止损单已恢复")
    stop_loss_manager2 = StopLossManager(connector)
    stop_orders = stop_loss_manager2.get_active_stop_orders()
    assert len(stop_orders) > 0, "止损单未恢复"
    print(f"  ✅ 止损单已恢复：{len(stop_orders)}个")
    
    print_step(5, "清理：停止策略并取消止损单")
    for stop_order in stop_orders:
        stop_loss_manager2.cancel_stop_loss("ETHUSDT", stop_order['algo_id'])
    
    result = strategy_manager2.stop_strategy("ETHUSDT")
    assert result.is_success
    
    print("\n✅ 测试 4: 持久化恢复 - 通过")
    return True


def run_all_integration_tests():
    """运行所有集成测试"""
    print("\n" + "="*60)
    print("🦞 大王量化交易系统 v3.0 - 集成测试")
    print("="*60)
    
    results = {}
    
    try:
        # 测试 1: 策略引擎 + 执行引擎集成
        results["策略引擎 + 执行引擎集成"] = test_strategy_execution_integration()
        time.sleep(0.5)
        
        # 测试 2: 完整交易流程
        results["完整交易流程"] = test_full_trading_flow()
        time.sleep(0.5)
        
        # 测试 3: 多策略并发
        results["多策略并发"] = test_concurrent_strategies()
        time.sleep(0.5)
        
        # 测试 4: 持久化恢复
        results["持久化恢复"] = test_persistence_recovery()
        
        # 总结
        print("\n" + "="*60)
        print("📊 测试总结")
        print("="*60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {status} - {test_name}")
        
        print(f"\n总计：{passed}/{total} 通过 ({passed*100/total:.0f}%)")
        
        # 清理
        cleanup()
        
        return passed == total
        
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)
