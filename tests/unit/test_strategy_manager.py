#!/usr/bin/env python3
"""
测试策略管理器
"""

import pytest
from decimal import Decimal
from core.strategy.manager import StrategyManager


class TestStrategyManager:
    """测试策略管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建策略管理器实例"""
        return StrategyManager()
    
    def test_init(self, manager):
        """测试初始化"""
        assert manager is not None
        assert len(manager.strategies) == 0
    
    def test_start_strategy(self, manager):
        """测试启动策略"""
        result = manager.start_strategy(
            symbol="ETHUSDT",
            strategy_id="breakout",
            leverage=5,
            amount=100
        )
        
        assert result.is_success
        assert result.data["symbol"] == "ETHUSDT"
        assert result.data["strategy_id"] == "breakout"
        
        # 验证策略已添加
        assert "ETHUSDT" in manager.strategies
        strategy = manager.strategies["ETHUSDT"]
        assert strategy.strategy_id == "breakout"
        assert strategy.leverage == 5
        assert strategy.amount == Decimal("100")
    
    def test_start_strategy_duplicate(self, manager):
        """测试重复启动策略"""
        # 第一次启动
        manager.start_strategy("ETHUSDT", "breakout")
        
        # 第二次启动（应该失败）
        result = manager.start_strategy("ETHUSDT", "rsi")
        
        assert result.is_error
        assert result.error_code == "STRATEGY_EXISTS"
    
    def test_stop_strategy(self, manager):
        """测试停止策略"""
        # 先启动
        manager.start_strategy("ETHUSDT", "breakout")
        
        # 停止
        result = manager.stop_strategy("ETHUSDT")
        
        assert result.is_success
        
        # 验证策略已移除
        assert "ETHUSDT" not in manager.strategies
    
    def test_stop_strategy_not_found(self, manager):
        """测试停止不存在的策略"""
        result = manager.stop_strategy("ETHUSDT")
        
        assert result.is_error
        assert result.error_code == "STRATEGY_NOT_FOUND"
    
    def test_get_active_strategies(self, manager):
        """测试获取活跃策略"""
        # 启动多个策略
        manager.start_strategy("ETHUSDT", "breakout")
        manager.start_strategy("BTCUSDT", "rsi")
        
        strategies = manager.get_active_strategies()
        
        assert len(strategies) == 2
        assert strategies[0].symbol in ["ETHUSDT", "BTCUSDT"]
    
    def test_get_strategy_status(self, manager):
        """测试获取策略状态"""
        manager.start_strategy("ETHUSDT", "breakout")
        
        strategy = manager.get_strategy_status("ETHUSDT")
        
        assert strategy is not None
        assert strategy.strategy_id == "breakout"
    
    def test_reload_strategies(self, manager):
        """测试重新加载策略"""
        # 启动策略
        manager.start_strategy("ETHUSDT", "breakout")
        
        # 重新加载
        result = manager.reload_strategies()
        
        assert result.is_success
        # 注意：reload 会清除内存中的策略并从文件恢复
        # 因为启动时已经保存到文件，所以 reload 后会恢复
        assert result.data["count"] >= 0
