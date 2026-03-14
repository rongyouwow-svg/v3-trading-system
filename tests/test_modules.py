#!/usr/bin/env python3
"""
🧪 模块测试脚本

测试已完成的模块功能
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_exception_handler():
    """测试异常处理引擎"""
    print("\n=== 测试异常处理引擎 ===")
    
    try:
        from modules.exception import handler
        
        # 测试异常类
        exc = handler.NetworkException("测试网络错误")
        assert exc.retryable == True
        print("✅ NetworkException 测试通过")
        
        exc = handler.InsufficientBalanceException("余额不足")
        assert exc.retryable == False
        print("✅ InsufficientBalanceException 测试通过")
        
        # 测试装饰器
        @handler.retry_on_exception(max_retries=2, delay=0.1)
        def test_func():
            raise handler.NetworkException("测试重试")
        
        try:
            test_func()
        except handler.NetworkException:
            print("✅ retry_on_exception 测试通过")
        
        print("✅ 异常处理引擎测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 异常处理引擎测试失败：{e}\n")
        return False


def test_state_sync():
    """测试状态同步层"""
    print("\n=== 测试状态同步层 ===")
    
    try:
        from modules.state_sync import StateSync
        
        # 创建同步器
        sync = StateSync(data_dir="data/test")
        print("✅ StateSync 初始化成功")
        
        # 测试状态更新
        sync.update_state("test_key", {"value": "test"}, sync=True)
        print("✅ 状态更新测试通过")
        
        # 测试状态获取
        value = sync.get_state("test_key")
        assert value == {"value": "test"}
        print("✅ 状态获取测试通过")
        
        # 测试快照
        snapshot_file = sync.create_snapshot("test_snapshot")
        assert snapshot_file != ""
        print("✅ 快照创建测试通过")
        
        # 清理测试数据
        import shutil
        if os.path.exists("data/test"):
            shutil.rmtree("data/test")
        
        print("✅ 状态同步层测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 状态同步层测试失败：{e}\n")
        return False


def test_binance_api():
    """测试币安 API 集成"""
    print("\n=== 测试币安 API 集成 ===")
    
    try:
        import requests
        
        # 测试账户信息
        response = requests.get('http://localhost:3000/api/binance/account-info', timeout=5)
        data = response.json()
        
        assert data.get('success') == True
        assert 'account' in data
        print(f"✅ 账户信息：{data['account']['balance']} USDT")
        
        # 测试持仓查询
        response = requests.get('http://localhost:3000/api/binance/positions', timeout=5)
        data = response.json()
        
        assert data.get('success') == True
        print(f"✅ 持仓查询：{len(data.get('positions', []))} 个持仓")
        
        # 测试交易记录
        response = requests.get('http://localhost:3000/api/binance/trades?limit=5', timeout=5)
        data = response.json()
        
        assert data.get('success') == True
        print(f"✅ 交易记录：{len(data.get('trades', []))} 条记录")
        
        print("✅ 币安 API 集成测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 币安 API 集成测试失败：{e}\n")
        return False


def test_strategy_engine():
    """测试策略引擎"""
    print("\n=== 测试策略引擎 ===")
    
    try:
        from core.strategy import StrategyEngine
        
        engine = StrategyEngine()
        
        # 测试启动策略
        result = engine.start_strategy('breakout', 'ETHUSDT', {'leverage': 5, 'amount': 100})
        assert result['success'] == True
        print(f"✅ 策略启动：{result}")
        
        # 测试获取策略状态
        status = engine.get_strategy_status('ETHUSDT')
        assert status is not None
        print(f"✅ 策略状态：{status['status']}")
        
        # 测试停止策略
        result = engine.stop_strategy('ETHUSDT')
        assert result['success'] == True
        print(f"✅ 策略停止：{result}")
        
        print("✅ 策略引擎测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 策略引擎测试失败：{e}\n")
        return False


def test_execution_engine():
    """测试执行引擎"""
    print("\n=== 测试执行引擎 ===")
    
    try:
        from core.execution import ExecutionEngine
        
        engine = ExecutionEngine()
        
        # 测试创建订单
        result = engine.create_order('ETHUSDT', 'BUY', 'MARKET', 0.1)
        assert result['success'] == True
        print(f"✅ 订单创建：{result}")
        
        # 测试创建止损单
        result = engine.create_stop_loss('ETHUSDT', 2000.0, 0.1)
        assert result['success'] == True
        print(f"✅ 止损单创建：{result}")
        
        # 测试取消订单
        order_id = list(engine.orders.keys())[0]
        result = engine.cancel_order('ETHUSDT', order_id)
        assert result['success'] == True
        print(f"✅ 订单取消：{result}")
        
        print("✅ 执行引擎测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 执行引擎测试失败：{e}\n")
        return False


def test_risk_engine():
    """测试风控引擎"""
    print("\n=== 测试风控引擎 ===")
    
    try:
        from core.risk import RiskEngine
        
        engine = RiskEngine()
        
        # 测试仓位限制检查
        result = engine.check_position_limit('ETHUSDT', 500)
        assert result['success'] == True
        print(f"✅ 仓位检查：{result}")
        
        # 测试回撤检查
        result = engine.check_drawdown(900, 1000)
        assert result['success'] == True
        print(f"✅ 回撤检查：{result}")
        
        # 测试创建告警
        engine.create_alert('test', '测试告警', 'warning')
        alerts = engine.get_alerts()
        assert len(alerts) > 0
        print(f"✅ 告警创建：{len(alerts)} 个告警")
        
        print("✅ 风控引擎测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 风控引擎测试失败：{e}\n")
        return False


def test_market_data_engine():
    """测试行情数据引擎"""
    print("\n=== 测试行情数据引擎 ===")
    
    try:
        from core.market_data import MarketDataEngine
        
        engine = MarketDataEngine()
        
        # 测试更新 Ticker
        engine.update_ticker('ETHUSDT', {'price': 2000.0, 'volume': 1000})
        ticker = engine.get_ticker('ETHUSDT')
        assert ticker is not None
        print(f"✅ Ticker 更新：{ticker['price']}")
        
        # 测试获取最新价格
        price = engine.get_latest_price('ETHUSDT')
        assert price == 2000.0
        print(f"✅ 最新价格：{price}")
        
        print("✅ 行情数据引擎测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 行情数据引擎测试失败：{e}\n")
        return False


def test_capital_engine():
    """测试资金管理引擎"""
    print("\n=== 测试资金管理引擎 ===")
    
    try:
        from core.capital import CapitalEngine
        
        engine = CapitalEngine()
        
        # 测试仓位计算
        position_size = engine.calculate_position_size(100, 2000, 5)
        assert position_size > 0
        print(f"✅ 仓位计算：{position_size}")
        
        # 测试 PnL 计算
        pnl = engine.calculate_pnl(2000, 2100, 0.25, 'LONG')
        assert pnl > 0
        print(f"✅ PnL 计算：{pnl}")
        
        # 测试 PnL 百分比
        pnl_pct = engine.calculate_pnl_pct(2000, 2100, 'LONG')
        assert pnl_pct > 0
        print(f"✅ PnL 百分比：{pnl_pct:.2f}%")
        
        print("✅ 资金管理引擎测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 资金管理引擎测试失败：{e}\n")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*50)
    print("🧪 模块测试")
    print("="*50)
    
    results = []
    
    # 测试各模块
    results.append(("异常处理引擎", test_exception_handler()))
    results.append(("状态同步层", test_state_sync()))
    results.append(("币安 API 集成", test_binance_api()))
    results.append(("策略引擎", test_strategy_engine()))
    results.append(("执行引擎", test_execution_engine()))
    results.append(("风控引擎", test_risk_engine()))
    results.append(("行情数据引擎", test_market_data_engine()))
    results.append(("资金管理引擎", test_capital_engine()))
    
    # 汇总结果
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    
    print(f"\n总计：{passed}/{total} 通过 ({passed/total*100:.0f}%)\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
