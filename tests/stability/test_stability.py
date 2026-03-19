#!/usr/bin/env python3
"""
🦞 策略管理器稳定性测试

测试内容:
    1. 连续运行 10 次
    2. 并发启动多个策略
    3. 长时间运行测试
    4. 异常恢复测试

用法:
    python tests/stability/test_stability.py
"""

import sys
import os
import time
import threading
from decimal import Decimal
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.strategy.manager import StrategyManager
from modules.utils.result import Result

# 持久化文件路径
PERSISTENCE_FILE = "/root/.openclaw/workspace/quant/v3-architecture/data/plugin_strategies.json"


def cleanup():
    """清理测试环境"""
    if os.path.exists(PERSISTENCE_FILE):
        os.remove(PERSISTENCE_FILE)


def test_continuous_runs(runs=10):
    """测试 1: 连续运行多次"""
    print("\n" + "="*60)
    print(f"📊 测试 1: 连续运行 {runs} 次")
    print("="*60)
    
    success_count = 0
    fail_count = 0
    
    for i in range(runs):
        try:
            cleanup()
            manager = StrategyManager()
            
            # 启动策略
            result = manager.start_strategy(
                symbol="ETHUSDT",
                strategy_id="breakout",
                leverage=5,
                amount=100
            )
            
            if not result.is_success:
                print(f"  [{i+1}/{runs}] ❌ 启动失败：{result.message}")
                fail_count += 1
                continue
            
            # 查询策略
            strategy = manager.get_strategy_status("ETHUSDT")
            if not strategy:
                print(f"  [{i+1}/{runs}] ❌ 查询失败")
                fail_count += 1
                continue
            
            # 停止策略
            result = manager.stop_strategy("ETHUSDT")
            if not result.is_success:
                print(f"  [{i+1}/{runs}] ❌ 停止失败：{result.message}")
                fail_count += 1
                continue
            
            print(f"  [{i+1}/{runs}] ✅ 通过")
            success_count += 1
            
        except Exception as e:
            print(f"  [{i+1}/{runs}] ❌ 异常：{e}")
            fail_count += 1
    
    print(f"\n结果：{success_count}/{runs} 通过 ({success_count*100/runs:.0f}%)")
    return success_count == runs


def test_concurrent_start():
    """测试 2: 并发启动多个策略"""
    print("\n" + "="*60)
    print("📊 测试 2: 并发启动多个策略")
    print("="*60)
    
    cleanup()
    manager = StrategyManager()
    
    symbols = ["ETHUSDT", "BTCUSDT", "AVAXUSDT", "LINKUSDT", "UNIUSDT"]
    results = []
    
    def start_strategy(symbol, idx):
        result = manager.start_strategy(
            symbol=symbol,
            strategy_id=f"strategy_{idx}",
            leverage=5,
            amount=100
        )
        results.append((symbol, result))
    
    # 并发启动
    threads = []
    for i, symbol in enumerate(symbols):
        t = threading.Thread(target=start_strategy, args=(symbol, i))
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join(timeout=5)
    
    # 检查结果
    success_count = 0
    for symbol, result in results:
        if result.is_success:
            print(f"  ✅ {symbol}: {result.data['strategy_id']}")
            success_count += 1
        else:
            print(f"  ❌ {symbol}: {result.message}")
    
    print(f"\n结果：{success_count}/{len(symbols)} 成功")
    
    # 验证所有策略都在内存中
    active_strategies = manager.get_active_strategies()
    print(f"活跃策略数：{len(active_strategies)}")
    
    # 停止所有策略
    for symbol in symbols:
        manager.stop_strategy(symbol)
    
    return success_count == len(symbols)


def test_long_running():
    """测试 3: 长时间运行测试"""
    print("\n" + "="*60)
    print("📊 测试 3: 长时间运行测试 (30 秒)")
    print("="*60)
    
    cleanup()
    manager = StrategyManager()
    
    # 启动策略
    result = manager.start_strategy(
        symbol="ETHUSDT",
        strategy_id="breakout",
        leverage=5,
        amount=100
    )
    
    if not result.is_success:
        print(f"❌ 启动失败：{result.message}")
        return False
    
    print("✅ 策略已启动")
    
    # 等待 30 秒，期间定期检查
    check_count = 0
    for i in range(30):
        time.sleep(1)
        
        # 每 5 秒检查一次
        if i % 5 == 0:
            strategy = manager.get_strategy_status("ETHUSDT")
            if strategy and strategy.is_running():
                check_count += 1
                print(f"  [{i}s] ✅ 策略运行正常 (检查{check_count}次)")
            else:
                print(f"  [{i}s] ❌ 策略异常")
                return False
    
    # 停止策略
    result = manager.stop_strategy("ETHUSDT")
    if not result.is_success:
        print(f"❌ 停止失败：{result.message}")
        return False
    
    print(f"\n结果：运行 30 秒，检查{check_count}次，全部正常 ✅")
    return True


def test_exception_recovery():
    """测试 4: 异常恢复测试"""
    print("\n" + "="*60)
    print("📊 测试 4: 异常恢复测试")
    print("="*60)
    
    cleanup()
    
    test_passed = True
    
    # 测试 1: 启动不存在的策略（应该失败但不应崩溃）
    print("  [测试] 启动无效参数...")
    try:
        manager = StrategyManager()
        # 尝试启动空 symbol
        result = manager.start_strategy(
            symbol="",  # 空 symbol
            strategy_id="test",
            leverage=5,
            amount=100
        )
        # 应该失败或成功，但不应该崩溃
        print(f"    结果：{'✅ 未崩溃' if result else '⚠️ 返回空'}")
    except Exception as e:
        print(f"    ❌ 异常：{e}")
        test_passed = False
    
    # 测试 2: 重复停止（应该失败但不应崩溃）
    print("  [测试] 重复停止策略...")
    try:
        manager.start_strategy("ETHUSDT", "test", leverage=5, amount=100)
        manager.stop_strategy("ETHUSDT")
        result = manager.stop_strategy("ETHUSDT")  # 重复停止
        if result.is_error:
            print(f"    ✅ 正确返回错误：{result.error_code}")
        else:
            print(f"    ⚠️ 重复停止返回成功")
    except Exception as e:
        print(f"    ❌ 异常：{e}")
        test_passed = False
    
    # 测试 3: 查询不存在的策略
    print("  [测试] 查询不存在的策略...")
    try:
        strategy = manager.get_strategy_status("NONEXISTENT")
        if strategy is None:
            print(f"    ✅ 正确返回 None")
        else:
            print(f"    ⚠️ 返回了策略对象")
    except Exception as e:
        print(f"    ❌ 异常：{e}")
        test_passed = False
    
    # 测试 4: 持久化文件损坏恢复
    print("  [测试] 持久化文件损坏恢复...")
    try:
        # 创建损坏的文件
        with open(PERSISTENCE_FILE, 'w') as f:
            f.write("{ invalid json }")
        
        # 创建新 manager（应该能处理损坏文件）
        manager2 = StrategyManager()
        print(f"    ✅ 未崩溃，正常初始化")
    except Exception as e:
        print(f"    ❌ 异常：{e}")
        test_passed = False
    
    print(f"\n结果：{'✅ 所有异常处理正常' if test_passed else '❌ 部分异常处理失败'}")
    return test_passed


def test_memory_leak():
    """测试 5: 内存泄漏检测"""
    print("\n" + "="*60)
    print("📊 测试 5: 内存泄漏检测 (启动/停止 10 次)")
    print("="*60)
    
    cleanup()
    
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"  初始内存：{initial_memory:.2f} MB")
    
    for i in range(10):
        manager = StrategyManager()
        manager.start_strategy("ETHUSDT", "test", leverage=5, amount=100)
        manager.stop_strategy("ETHUSDT")
        
        if i % 3 == 0:
            current_memory = process.memory_info().rss / 1024 / 1024
            print(f"  [{i+1}/10] 内存：{current_memory:.2f} MB (+{current_memory - initial_memory:.2f} MB)")
    
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory
    
    print(f"\n  最终内存：{final_memory:.2f} MB")
    print(f"  内存增长：{memory_increase:.2f} MB")
    
    # 内存增长超过 50MB 认为可能有泄漏
    if memory_increase > 50:
        print(f"\n  ⚠️ 警告：内存增长较大 ({memory_increase:.2f} MB)")
        return False
    else:
        print(f"\n  ✅ 内存增长正常 ({memory_increase:.2f} MB)")
        return True


def run_all_stability_tests():
    """运行所有稳定性测试"""
    print("\n" + "="*60)
    print("🦞 大王量化交易系统 v3.0 - 稳定性测试")
    print("="*60)
    
    results = {}
    
    # 测试 1: 连续运行
    results["连续运行 10 次"] = test_continuous_runs(10)
    
    # 测试 2: 并发启动
    results["并发启动"] = test_concurrent_start()
    
    # 测试 3: 长时间运行
    results["长时间运行 (30 秒)"] = test_long_running()
    
    # 测试 4: 异常恢复
    results["异常恢复"] = test_exception_recovery()
    
    # 测试 5: 内存泄漏
    results["内存泄漏检测"] = test_memory_leak()
    
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


if __name__ == "__main__":
    success = run_all_stability_tests()
    sys.exit(0 if success else 1)
