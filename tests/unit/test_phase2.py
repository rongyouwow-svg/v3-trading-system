#!/usr/bin/env python3
"""
测试 Phase 2 核心模块
"""

import pytest
from decimal import Decimal
from core.sync.state_sync import StateSync, reset_state_sync
from core.capital.capital_manager import CapitalManager, reset_capital_manager
from core.exception.exception_handler import ExceptionManager, reset_exception_manager
from modules.utils.exceptions import NetworkException, InsufficientBalanceException
from modules.utils.result import Result
from unittest.mock import Mock


class TestStateSync:
    """测试状态同步器"""
    
    @pytest.fixture
    def connector(self):
        """创建模拟连接器"""
        connector = Mock()
        connector.get_account_balance.return_value = Result.ok(data={
            'balances': [{'asset': 'USDT', 'free': '10000', 'total': '10000'}]
        })
        connector.get_positions.return_value = Result.ok(data={'positions': []})
        return connector
    
    @pytest.fixture
    def sync(self, connector, tmp_path):
        """创建状态同步器实例"""
        reset_state_sync()
        sync = StateSync(connector)
        sync.persistence_file = str(tmp_path / "test_state_sync.json")
        return sync
    
    def test_state_sync_init(self, sync):
        """测试初始化"""
        assert sync is not None
        assert sync.running is False
    
    def test_start_stop(self, sync):
        """测试启动停止"""
        sync.start()
        assert sync.running is True
        
        sync.stop()
        assert sync.running is False
    
    def test_get_state(self, sync):
        """测试获取状态"""
        state = sync.get_state()
        assert isinstance(state, dict)
    
    def test_get_sync_statistics(self, sync):
        """测试获取同步统计"""
        stats = sync.get_sync_statistics()
        
        assert 'sync_count' in stats
        assert 'version' in stats
        assert 'is_running' in stats


class TestCapitalManager:
    """测试资金管理引擎"""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """创建资金管理引擎实例"""
        reset_capital_manager()
        manager = CapitalManager()
        manager.persistence_file = str(tmp_path / "test_capital.json")
        return manager
    
    def test_capital_manager_init(self, manager):
        """测试初始化"""
        assert manager is not None
        assert manager.total_capital == Decimal('0')
    
    def test_calculate_position_size_fixed(self, manager):
        """测试固定比例仓位计算"""
        position_size = manager.calculate_position_size(
            Decimal('100'),
            Decimal('2000'),
            5
        )
        
        assert position_size == Decimal('0.25')
    
    def test_calculate_position_size_kelly(self, manager):
        """测试凯利公式仓位计算"""
        position_size = manager.calculate_position_size(
            Decimal('100'),
            Decimal('2000'),
            1,
            mode=CapitalManager.POSITION_MODE_KELLY,
            win_rate=0.6,
            profit_loss_ratio=2.0
        )
        
        # 凯利公式：f* = (0.6 * 2 - 0.4) / 2 = 0.4
        assert position_size > Decimal('0')
    
    def test_calculate_pnl_long(self, manager):
        """测试多头盈亏计算"""
        pnl = manager.calculate_pnl(
            Decimal('2000'),
            Decimal('2100'),
            Decimal('0.1'),
            'LONG'
        )
        
        assert pnl == Decimal('10')
    
    def test_calculate_pnl_short(self, manager):
        """测试空头盈亏计算"""
        pnl = manager.calculate_pnl(
            Decimal('2100'),
            Decimal('2000'),
            Decimal('0.1'),
            'SHORT'
        )
        
        assert pnl == Decimal('10')
    
    def test_add_commission(self, manager):
        """测试添加手续费"""
        manager.add_commission(Decimal('0.1'), 'USDT')
        
        assert manager.total_commission == Decimal('0.1')
    
    def test_add_trade(self, manager):
        """测试添加交易记录"""
        manager.add_trade(Decimal('10'), True)
        
        assert manager.trade_count == 1
        assert manager.win_count == 1
        assert manager.realized_pnl == Decimal('10')
    
    def test_check_risk_limits(self, manager):
        """测试风险限制检查"""
        manager.total_capital = Decimal('10000')
        manager.available_capital = Decimal('10000')
        
        result = manager.check_risk_limits(
            Decimal('0.1'),
            Decimal('2000'),
            'ETHUSDT'
        )
        
        assert result.is_success
    
    def test_get_statistics(self, manager):
        """测试获取统计信息"""
        stats = manager.get_statistics()
        
        assert 'total_capital' in stats
        assert 'win_rate' in stats


class TestExceptionManager:
    """测试异常处理引擎"""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """创建异常处理引擎实例"""
        reset_exception_manager()
        manager = ExceptionManager()
        manager.persistence_file = str(tmp_path / "test_exception.json")
        return manager
    
    def test_exception_manager_init(self, manager):
        """测试初始化"""
        assert manager is not None
        assert manager.exception_count == 0
    
    def test_handle_network_exception(self, manager):
        """测试处理网络异常"""
        exception = NetworkException("网络错误")
        result = manager.handle_exception(exception)
        
        assert result.is_success
        assert result.data.get('retry') is True
    
    def test_handle_insufficient_balance(self, manager):
        """测试处理余额不足"""
        exception = InsufficientBalanceException("余额不足")
        result = manager.handle_exception(exception)
        
        assert result.is_error
        assert result.error_code == "INSUFFICIENT_BALANCE"
    
    def test_handle_generic_exception(self, manager):
        """测试处理通用异常"""
        exception = ValueError("未知错误")
        result = manager.handle_exception(exception)
        
        assert result.is_error
        assert result.error_code == "INTERNAL_ERROR"
    
    def test_get_statistics(self, manager):
        """测试获取统计信息"""
        # 触发一些异常
        manager.handle_exception(NetworkException("测试"))
        
        stats = manager.get_statistics()
        
        assert 'exception_count' in stats
        assert stats['exception_count'] >= 1


class TestPhase2Integration:
    """测试 Phase 2 集成"""
    
    def test_capital_and_exception_integration(self, tmp_path, monkeypatch):
        """测试资金管理和异常处理集成"""
        reset_capital_manager()
        reset_exception_manager()
        
        capital_file = tmp_path / "test_capital.json"
        exception_file = tmp_path / "test_exception.json"
        
        capital_manager = CapitalManager()
        capital_manager.persistence_file = str(capital_file)
        
        exception_manager = ExceptionManager()
        exception_manager.persistence_file = str(exception_file)
        
        # 测试风险检查
        capital_manager.total_capital = Decimal('10000')
        capital_manager.available_capital = Decimal('10000')
        
        result = capital_manager.check_risk_limits(
            Decimal('0.1'),
            Decimal('2000'),
            'ETHUSDT'
        )
        
        assert result.is_success
        
        # 测试异常处理
        exception = NetworkException("测试")
        result = exception_manager.handle_exception(exception)
        
        assert result.is_success
