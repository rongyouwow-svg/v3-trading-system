#!/usr/bin/env python3
"""
🦞 策略管理器完整测试脚本

测试内容:
    1. 策略启动
    2. 策略持久化
    3. 热插拔恢复（重启）
    4. 策略停止
    5. 并发测试

用法:
    python tests/integration/test_strategy_integration.py
"""

import sys
import os
import time
from decimal import Decimal
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.strategy.manager import StrategyManager, get_strategy_manager
from modules.models.strategy import Strategy
from modules.utils.result import Result

# 持久化文件路径
PERSISTENCE_FILE = "/home/admin/.openclaw/workspace/quant/v3-architecture/data/plugin_strategies.json"


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
    if os.path.exists(PERSISTENCE_FILE):
        os.remove(PERSISTENCE_FILE)
        print(f"✅ 已清理持久化文件：{PERSISTENCE_FILE}")


def test_basic_functionality():
    """测试 1: 基本功能"""
    print_section("测试 1: 基本功能")
    
    cleanup()
    manager = StrategyManager()
    
    print_step(1, "启动策略 ETHUSDT - breakout")
    result = manager.start_strategy(
        symbol="ETHUSDT",
        strategy_id="breakout",
        leverage=5,
        amount=100,
        side="LONG"
    )
    
    print(f"  结果：{'✅ 成功' if result.is_success else '❌ 失败'}")
    print(f"  消息：{result.message}")
    print(f"  数据：{result.data}")
    
    assert result.is_success, "启动策略失败"
    assert "ETHUSDT" in manager.strategies, "策略未添加到内存"
    
    print_step(2, "启动策略 BTCUSDT - rsi")
    result = manager.start_strategy(
        symbol="BTCUSDT",
        strategy_id="rsi",
        leverage=3,
        amount=200,
        side="SHORT"
    )
    
    print(f"  结果：{'✅ 成功' if result.is_success else '❌ 失败'}")
    assert result.is_success, "启动策略失败"
    assert "BTCUSDT" in manager.strategies, "策略未添加到内存"
    
    print_step(3, "获取活跃策略列表")
    strategies = manager.get_active_strategies()
    print(f"  活跃策略数：{len(strategies)}")
    for s in strategies:
        print(f"    - {s.symbol}: {s.strategy_id} (杠杆:{s.leverage}, 保证金:{s.amount})")
    
    assert len(strategies) == 2, f"期望 2 个策略，实际{len(strategies)}个"
    
    print_step(4, "获取单个策略状态")
    strategy = manager.get_strategy_status("ETHUSDT")
    print(f"  ETHUSDT 状态：{strategy.strategy_id if strategy else 'None'}")
    assert strategy is not None, "策略状态为 None"
    assert strategy.strategy_id == "breakout", "策略 ID 不匹配"
    
    print("\n✅ 测试 1: 基本功能 - 通过")
    return manager


def test_persistence():
    """测试 2: 持久化机制"""
    print_section("测试 2: 持久化机制")
    
    print_step(1, "检查持久化文件")
    assert os.path.exists(PERSISTENCE_FILE), "持久化文件不存在"
    print(f"  文件路径：{PERSISTENCE_FILE}")
    
    import json
    with open(PERSISTENCE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"  策略数量：{len(data)}")
    for symbol, strategy_data in data.items():
        print(f"    - {symbol}: {strategy_data['strategy_id']} (状态:{strategy_data['status']})")
    
    assert len(data) == 2, f"期望 2 个策略，实际{len(data)}个"
    assert "ETHUSDT" in data, "ETHUSDT 策略未持久化"
    assert "BTCUSDT" in data, "BTCUSDT 策略未持久化"
    
    print("\n✅ 测试 2: 持久化机制 - 通过")


def test_hot_plug_recovery():
    """测试 3: 热插拔恢复（重启）"""
    print_section("测试 3: 热插拔恢复（重启）")
    
    print_step(1, "模拟重启：创建新的策略管理器实例")
    manager2 = StrategyManager()
    
    print_step(2, "检查策略是否自动恢复")
    strategies = manager2.get_active_strategies()
    print(f"  恢复的策略数：{len(strategies)}")
    
    for s in strategies:
        print(f"    - {s.symbol}: {s.strategy_id} (杠杆:{s.leverage}, 保证金:{s.amount})")
        print(f"      热插拔标记：{s.is_hot_plug}")
        print(f"      启动时间：{s.start_time}")
    
    assert len(strategies) == 2, f"期望恢复 2 个策略，实际{len(strategies)}个"
    
    eth_strategy = manager2.get_strategy_status("ETHUSDT")
    assert eth_strategy is not None, "ETHUSDT 策略未恢复"
    assert eth_strategy.strategy_id == "breakout", "ETHUSDT 策略 ID 不匹配"
    assert eth_strategy.is_hot_plug is True, "热插拔标记错误"
    
    btc_strategy = manager2.get_strategy_status("BTCUSDT")
    assert btc_strategy is not None, "BTCUSDT 策略未恢复"
    assert btc_strategy.strategy_id == "rsi", "BTCUSDT 策略 ID 不匹配"
    
    print("\n✅ 测试 3: 热插拔恢复 - 通过")
    return manager2


def test_stop_strategy():
    """测试 4: 策略停止"""
    print_section("测试 4: 策略停止")
    manager = StrategyManager()
    
    print_step(1, "停止 ETHUSDT 策略")
    result = manager.stop_strategy("ETHUSDT")
    
    print(f"  结果：{'✅ 成功' if result.is_success else '❌ 失败'}")
    print(f"  消息：{result.message}")
    
    assert result.is_success, "停止策略失败"
    assert "ETHUSDT" not in manager.strategies, "ETHUSDT 策略未从内存移除"
    
    print_step(2, "检查持久化文件更新")
    import json
    with open(PERSISTENCE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"  剩余策略数：{len(data)}")
    assert "ETHUSDT" not in data, "ETHUSDT 策略未从持久化文件移除"
    assert "BTCUSDT" in data, "BTCUSDT 策略不应被移除"
    
    print_step(3, "停止不存在的策略")
    result = manager.stop_strategy("ETHUSDT")
    print(f"  结果：{'❌ 失败 (预期)' if result.is_error else '✅ 成功 (异常)'}")
    print(f"  错误码：{result.error_code}")
    
    assert result.is_error, "停止不存在的策略应该失败"
    assert result.error_code == "STRATEGY_NOT_FOUND", "错误码不匹配"
    
    print("\n✅ 测试 4: 策略停止 - 通过")


def test_duplicate_start():
    """测试 5: 重复启动保护"""
    print_section("测试 5: 重复启动保护")
    manager = StrategyManager()
    
    # 先启动一个策略
    manager.start_strategy(
        symbol="TESTUSDT",
        strategy_id="test_strategy",
        leverage=5,
        amount=100
    )
    
    print_step(1, "尝试重复启动 TESTUSDT")
    result = manager.start_strategy(
        symbol="TESTUSDT",
        strategy_id="another_strategy",
        leverage=10,
        amount=500
    )
    
    print(f"  结果：{'❌ 失败 (预期)' if result.is_error else '✅ 成功 (异常)'}")
    print(f"  错误码：{result.error_code}")
    print(f"  消息：{result.message}")
    
    assert result.is_error, "重复启动应该失败"
    assert result.error_code == "STRATEGY_EXISTS", "错误码不匹配"
    
    # 验证原策略未被覆盖
    strategy = manager.get_strategy_status("TESTUSDT")
    assert strategy.strategy_id == "test_strategy", "原策略被错误覆盖"
    assert strategy.leverage == 5, "原策略参数被错误修改"
    
    print("\n✅ 测试 5: 重复启动保护 - 通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🦞 大王量化交易系统 v3.0 - 策略管理器完整测试")
    print("="*60)
    
    try:
        # 测试 1: 基本功能
        manager1 = test_basic_functionality()
        time.sleep(1)
        
        # 测试 2: 持久化机制
        test_persistence()
        
        # 测试 3: 热插拔恢复
        manager2 = test_hot_plug_recovery()
        time.sleep(1)
        
        # 测试 4: 策略停止
        test_stop_strategy()
        time.sleep(1)
        
        # 测试 5: 重复启动保护
        test_duplicate_start()
        
        print_section("🎉 所有测试通过！")
        print("\n✅ 测试总结:")
        print("  1. 基本功能 - 通过")
        print("  2. 持久化机制 - 通过")
        print("  3. 热插拔恢复 - 通过")
        print("  4. 策略停止 - 通过")
        print("  5. 重复启动保护 - 通过")
        
        print("\n📊 测试覆盖率:")
        print("  - 策略启动 ✅")
        print("  - 策略停止 ✅")
        print("  - 策略查询 ✅")
        print("  - 持久化保存 ✅")
        print("  - 持久化加载 ✅")
        print("  - 热插拔恢复 ✅")
        print("  - 错误处理 ✅")
        
        # 清理
        cleanup()
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败：{e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
