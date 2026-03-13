#!/usr/bin/env python3
"""
Phase 2 集成测试（简化版）

测试内容:
    1. Phase 2 模块是否正确初始化
    2. Phase 2 模块是否可以被调用
"""

import pytest
from decimal import Decimal

from core.strategy.manager import StrategyManager
from core.capital.capital_manager import CapitalManager
from core.exception.exception_handler import ExceptionManager
from core.sync.state_sync import StateSync


class TestPhase2Integration:
    """Phase 2 集成测试"""
    
    def test_capital_manager_initialized(self):
        """测试资金管理引擎初始化"""
        # 不使用 connector，直接测试初始化
        manager = StrategyManager(connector=None)
        
        # 没有 connector 时，Phase 2 模块应该为 None
        assert manager.capital_manager is None
    
    def test_capital_manager_standalone(self):
        """测试资金管理引擎独立使用"""
        capital_manager = CapitalManager()
        
        # 测试仓位计算
        position_size = capital_manager.calculate_position_size(
            amount=Decimal("100"),
            price=Decimal("2000"),
            leverage=5
        )
        
        assert position_size == Decimal("0.25")
    
    def test_exception_manager_standalone(self):
        """测试异常处理引擎独立使用"""
        exception_manager = ExceptionManager()
        
        # 验证初始化成功
        assert exception_manager is not None
        
        # 测试统计信息
        stats = exception_manager.get_statistics()
        assert 'exception_count' in stats
    
    def test_state_sync_standalone(self):
        """测试状态同步引擎独立使用"""
        # 使用 Mock connector
        from unittest.mock import Mock
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
        
        # 验证初始化成功
        assert state_sync is not None
        
        # 测试统计信息
        stats = state_sync.get_sync_statistics()
        assert 'sync_count' in stats
    
    def test_all_phase2_modules_exist(self):
        """测试所有 Phase 2 模块都存在"""
        # 验证模块可以导入
        from core.sync import state_sync
        from core.capital import capital_manager
        from core.exception import exception_handler
        
        # 验证类存在
        assert hasattr(state_sync, 'StateSync')
        assert hasattr(capital_manager, 'CapitalManager')
        assert hasattr(exception_handler, 'ExceptionManager')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
