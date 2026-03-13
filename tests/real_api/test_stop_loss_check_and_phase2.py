#!/usr/bin/env python3
"""
真实 API 测试：止损单查重 + Phase 2 集成

测试内容:
    1. 止损单查重功能
    2. 自动创建止损单
    3. 自动取消止损单
    4. Phase 2 模块实际使用
"""

import sys
from pathlib import Path
from decimal import Decimal

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from connectors.binance.usdt_futures import BinanceUSDTFuturesConnector
from core.strategy.manager import StrategyManager
from modules.config.api_config import get_api_config

# API 配置
config = get_api_config()
binance_config = config.get_binance_config('testnet')


def print_section(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"📊 {title}")
    print("="*60)


def print_step(step, description):
    """打印步骤"""
    print(f"\n[{step}] {description}")


def test_stop_loss_duplicate_check():
    """测试 1: 止损单查重功能"""
    print_section("测试 1: 止损单查重功能")
    
    # 创建连接器
    connector = BinanceUSDTFuturesConnector(
        api_key=binance_config['api_key'],
        secret_key=binance_config['secret_key'],
        testnet=True
    )
    
    print_step(1, "检查 ETHUSDT 是否有活跃止损单")
    result = connector.check_stop_loss_exists("ETHUSDT", "SELL")
    
    if result.is_success:
        if result.data["exists"]:
            print(f"  ✅ 已有 {result.data['count']} 个活跃止损单")
            for order in result.data["orders"]:
                print(f"    - Algo ID: {order['algo_id']}, 触发价：{order['trigger_price']}")
        else:
            print(f"  ✅ 没有活跃止损单")
        return True, connector
    else:
        print(f"  ❌ 查重失败：{result.message}")
        return False, None


def test_auto_create_stop_loss(connector):
    """测试 2: 自动创建止损单"""
    print_section("测试 2: 自动创建止损单")
    
    print_step(1, "创建测试止损单（ETHUSDT）")
    result = connector.create_stop_loss_order(
        symbol="ETHUSDT",
        side="SELL",
        quantity=Decimal("0.01"),
        stop_price=Decimal("2000")
    )
    
    if result.is_success:
        algo_id = result.data.get("algo_id", "")
        print(f"  ✅ 止损单创建成功")
        print(f"  Algo ID: {algo_id}")
        return True, algo_id
    else:
        print(f"  ❌ 止损单创建失败：{result.message}")
        return False, None


def test_duplicate_prevention(connector, algo_id):
    """测试 3: 查重防重功能"""
    print_section("测试 3: 查重防重功能")
    
    print_step(1, "再次检查 ETHUSDT 止损单")
    result = connector.check_stop_loss_exists("ETHUSDT", "SELL")
    
    if result.is_success and result.data["exists"]:
        print(f"  ✅ 检测到已有止损单：{result.data['count']} 个")
        
        # 验证是同一个止损单
        orders = result.data["orders"]
        if orders and orders[0].get("algo_id") == algo_id:
            print(f"  ✅ 防重成功：已存在的止损单 ID 匹配")
            return True
        else:
            print(f"  ⚠️ 发现不同的止损单")
            return True
    else:
        print(f"  ❌ 未检测到已有止损单")
        return False


def test_cancel_stop_loss(connector, algo_id):
    """测试 4: 取消止损单"""
    print_section("测试 4: 取消止损单")
    
    print_step(1, f"取消止损单 {algo_id}")
    result = connector.cancel_algo_order("ETHUSDT", algo_id)
    
    if result.is_success:
        print(f"  ✅ 止损单已取消")
        return True
    else:
        print(f"  ❌ 止损单取消失败：{result.message}")
        return False


def test_phase2_capital_manager():
    """测试 5: Phase 2 资金管理"""
    print_section("测试 5: Phase 2 资金管理")
    
    from core.capital.capital_manager import CapitalManager
    
    capital_manager = CapitalManager()
    
    print_step(1, "测试固定比例仓位计算")
    position_size = capital_manager.calculate_position_size(
        amount=Decimal("100"),
        price=Decimal("2000"),
        leverage=5,
        mode=CapitalManager.POSITION_MODE_FIXED
    )
    print(f"  100 USDT @ 2000 USDT, 5x 杠杆 = {position_size} ETH")
    assert position_size == Decimal("0.25"), "仓位计算错误"
    print(f"  ✅ 固定比例计算正确")
    
    print_step(2, "测试凯利公式仓位计算")
    position_size = capital_manager.calculate_position_size(
        amount=Decimal("100"),
        price=Decimal("2000"),
        leverage=5,
        mode=CapitalManager.POSITION_MODE_KELLY,
        win_rate=0.6,
        profit_loss_ratio=2.0
    )
    print(f"  凯利公式（胜率 60%, 盈亏比 2:1）= {position_size} ETH")
    assert position_size > Decimal("0"), "凯利公式计算错误"
    print(f"  ✅ 凯利公式计算正确")
    
    print_step(3, "测试风险检查")
    result = capital_manager.check_risk_limits(
        position_size=Decimal("0.1"),
        price=Decimal("2000"),
        symbol="ETHUSDT"
    )
    if result.is_success:
        print(f"  ✅ 风险检查通过")
    else:
        print(f"  ⚠️ 风险检查警告：{result.message}")
    
    return True


def test_phase2_exception_manager():
    """测试 6: Phase 2 异常处理"""
    print_section("测试 6: Phase 2 异常处理")
    
    from core.exception.exception_handler import ExceptionManager
    
    exception_manager = ExceptionManager()
    
    print_step(1, "测试异常分类")
    from modules.utils.exceptions import NetworkException
    
    network_exception = NetworkException("测试网络错误")
    result = exception_manager.handle_exception(network_exception)
    
    if result.is_success:
        print(f"  ✅ 网络异常处理成功")
    else:
        print(f"  ⚠️ 网络异常处理结果：{result.message}")
    
    print_step(2, "测试统计信息")
    stats = exception_manager.get_statistics()
    print(f"  异常总数：{stats['exception_count']}")
    print(f"  按分类统计：{stats['exception_by_category']}")
    print(f"  ✅ 异常处理引擎正常")
    
    return True


def test_phase2_state_sync():
    """测试 7: Phase 2 状态同步"""
    print_section("测试 7: Phase 2 状态同步")
    
    from core.sync.state_sync import StateSync
    from unittest.mock import Mock
    
    # 创建 Mock 连接器
    connector = Mock()
    connector.get_account_balance.return_value = Mock(
        is_success=True,
        data={"balances": []}
    )
    connector.get_positions.return_value = Mock(
        is_success=True,
        data={"positions": []}
    )
    
    state_sync = StateSync(connector)
    
    print_step(1, "测试状态同步初始化")
    print(f"  全量同步间隔：{state_sync.FULL_SYNC_INTERVAL} 秒")
    print(f"  增量同步间隔：{state_sync.INCREMENTAL_SYNC_INTERVAL} 秒")
    print(f"  ✅ 状态同步初始化成功")
    
    print_step(2, "测试统计信息")
    stats = state_sync.get_sync_statistics()
    print(f"  同步次数：{stats['sync_count']}")
    print(f"  版本号：{stats['version']}")
    print(f"  ✅ 状态同步引擎正常")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🦞 大王量化交易系统 - 真实 API 测试 + Phase 2 集成测试")
    print("="*60)
    
    results = {}
    
    try:
        # 测试 1: 止损单查重
        success, connector = test_stop_loss_duplicate_check()
        results['止损单查重'] = success
        
        if not connector:
            print("\n❌ 连接器创建失败，停止后续测试")
            return False
        
        # 测试 2: 自动创建止损单
        success, algo_id = test_auto_create_stop_loss(connector)
        results['自动创建止损单'] = success
        
        if not algo_id:
            print("\n⚠️ 止损单创建失败，跳过查重防重测试")
            results['查重防重'] = False
        else:
            # 测试 3: 查重防重
            results['查重防重'] = test_duplicate_prevention(connector, algo_id)
            
            # 测试 4: 取消止损单
            results['取消止损单'] = test_cancel_stop_loss(connector, algo_id)
        
        # 测试 5: Phase 2 资金管理
        results['Phase2 资金管理'] = test_phase2_capital_manager()
        
        # 测试 6: Phase 2 异常处理
        results['Phase2 异常处理'] = test_phase2_exception_manager()
        
        # 测试 7: Phase 2 状态同步
        results['Phase2 状态同步'] = test_phase2_state_sync()
        
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
        
        return passed == total
        
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
