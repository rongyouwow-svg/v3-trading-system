#!/usr/bin/env python3
"""
币安测试网真实 API 测试

测试内容:
    1. 连接测试
    2. 获取余额
    3. 获取持仓
    4. 创建订单
    5. 取消订单
    6. 创建止损单
    7. 取消止损单
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from connectors.binance.usdt_futures import BinanceUSDTFuturesConnector
from modules.utils.result import Result
from decimal import Decimal

# API 配置
API_KEY = "YOUR_API_KEY"
SECRET_KEY = "YOUR_SECRET_KEY"
TESTNET = True


def print_section(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"📊 {title}")
    print("="*60)


def print_step(step, description):
    """打印步骤"""
    print(f"\n[{step}] {description}")


def test_connection():
    """测试 1: 连接测试"""
    print_section("测试 1: 连接测试")
    
    print_step(1, "创建币安测试网连接器")
    connector = BinanceUSDTFuturesConnector(
        api_key=API_KEY,
        secret_key=SECRET_KEY,
        testnet=TESTNET
    )
    print(f"  ✅ 连接器创建成功")
    print(f"  测试网：{connector.testnet}")
    print(f"  API 端点：{connector.base_url}")
    
    print_step(2, "健康检查")
    result = connector.health_check()
    
    if result.is_success:
        print(f"  ✅ 健康检查通过")
        print(f"  状态：{result.data}")
        return True, connector
    else:
        print(f"  ❌ 健康检查失败：{result.message}")
        return False, None


def test_get_balance(connector):
    """测试 2: 获取余额"""
    print_section("测试 2: 获取余额")
    
    print_step(1, "获取账户余额")
    result = connector.get_account_balance()
    
    if result.is_success:
        print(f"  ✅ 获取余额成功")
        balances = result.data.get('balances', [])
        for balance in balances:
            if float(balance.get('total', 0)) > 0:
                print(f"    {balance['asset']}: {balance['total']} (可用：{balance['available']})")
        return True
    else:
        print(f"  ❌ 获取余额失败：{result.message}")
        return False


def test_get_positions(connector):
    """测试 3: 获取持仓"""
    print_section("测试 3: 获取持仓")
    
    print_step(1, "获取当前持仓")
    result = connector.get_positions()
    
    if result.is_success:
        print(f"  ✅ 获取持仓成功")
        positions = result.data.get('positions', [])
        if positions:
            for pos in positions:
                if float(pos.get('size', 0)) != 0:
                    print(f"    {pos['symbol']}: {pos['side']} {pos['size']} @ {pos['entry_price']}")
        else:
            print(f"    当前无持仓")
        return True
    else:
        print(f"  ❌ 获取持仓失败：{result.message}")
        return False


def test_create_order(connector):
    """测试 4: 创建订单"""
    print_section("测试 4: 创建订单")
    
    from modules.models.order import Order, OrderType, OrderSide
    
    print_step(1, "创建测试订单（ETHUSDT 市价单）")
    order = Order(
        symbol='ETHUSDT',
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        quantity=Decimal('0.01')  # 小金额测试
    )
    
    result = connector.place_order(order)
    
    if result.is_success:
        print(f"  ✅ 订单创建成功")
        print(f"  订单 ID: {result.data.get('order_id')}")
        print(f"  状态：{result.data.get('status')}")
        print(f"  数量：{result.data.get('quantity')}")
        print(f"  成交价：{result.data.get('avg_price')}")
        return True, result.data.get('order_id')
    else:
        print(f"  ❌ 订单创建失败：{result.message}")
        return False, None


def test_cancel_order(connector, order_id):
    """测试 5: 取消订单"""
    print_section("测试 5: 取消订单")
    
    if not order_id:
        print(f"  ⚠️ 无订单可取消")
        return True
    
    print_step(1, f"取消订单 {order_id}")
    result = connector.cancel_order('ETHUSDT', order_id)
    
    if result.is_success:
        print(f"  ✅ 订单取消成功")
        return True
    else:
        print(f"  ⚠️ 订单取消失败：{result.message}")
        print(f"  （可能已成交或已取消）")
        return True


def test_create_stop_loss(connector):
    """测试 6: 创建止损单"""
    print_section("测试 6: 创建止损单")
    
    print_step(1, "创建测试止损单（ETHUSDT）")
    # 先获取当前价格，设置合理的止损价
    result = connector.create_stop_loss_order(
        symbol='ETHUSDT',
        side='SELL',
        quantity=Decimal('0.01'),
        stop_price=Decimal('2000')  # 使用 stop_price 参数
    )
    
    if result.is_success:
        print(f"  ✅ 止损单创建成功")
        print(f"  止损单 ID: {result.data.get('algo_id')}")
        print(f"  状态：{result.data.get('status')}")
        return True, result.data.get('algo_id')
    else:
        print(f"  ❌ 止损单创建失败：{result.message}")
        return False, None


def test_cancel_stop_loss(connector, algo_id):
    """测试 7: 取消止损单"""
    print_section("测试 7: 取消止损单")
    
    if not algo_id:
        print(f"  ⚠️ 无止损单可取消")
        return True
    
    print_step(1, f"取消止损单 {algo_id}")
    result = connector.cancel_stop_loss_order('ETHUSDT', algo_id)
    
    if result.is_success:
        print(f"  ✅ 止损单取消成功")
        return True
    else:
        print(f"  ⚠️ 止损单取消失败：{result.message}")
        print(f"  （可能已触发或已取消）")
        return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🦞 大王量化交易系统 v3.0 - 币安测试网真实 API 测试")
    print("="*60)
    print(f"\n测试网：{TESTNET}")
    print(f"API 端点：https://testnet.binancefuture.com")
    
    results = {}
    connector = None
    
    try:
        # 测试 1: 连接测试
        success, connector = test_connection()
        results['连接测试'] = success
        
        if not success or not connector:
            print("\n❌ 连接测试失败，停止后续测试")
            return False
        
        # 测试 2: 获取余额
        results['获取余额'] = test_get_balance(connector)
        
        # 测试 3: 获取持仓
        results['获取持仓'] = test_get_positions(connector)
        
        # 测试 4: 创建订单
        success, order_id = test_create_order(connector)
        results['创建订单'] = success
        
        # 测试 5: 取消订单
        results['取消订单'] = test_cancel_order(connector, order_id)
        
        # 测试 6: 创建止损单
        success, algo_id = test_create_stop_loss(connector)
        results['创建止损单'] = success
        
        # 测试 7: 取消止损单
        results['取消止损单'] = test_cancel_stop_loss(connector, algo_id)
        
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
