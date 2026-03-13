#!/usr/bin/env python3
"""
测试止损单管理器
"""

import pytest
import os
import time
from decimal import Decimal
from unittest.mock import Mock
from core.execution.stop_loss_manager import StopLossManager, reset_stop_loss_manager
from modules.utils.result import Result


class TestStopLossManager:
    """测试止损单管理器"""
    
    @pytest.fixture
    def connector(self):
        """创建模拟连接器"""
        connector = Mock()
        connector.create_stop_loss_order.return_value = Result.ok(data={
            'algo_id': 'SL_TEST123',
            'status': 'WAIT_TO_TRIGGER'
        })
        connector.cancel_stop_loss_order.return_value = Result.ok(data={
            'algo_id': 'SL_TEST123',
            'status': 'CANCELED'
        })
        return connector
    
    @pytest.fixture
    def manager(self, connector, tmp_path, monkeypatch):
        """创建止损单管理器实例"""
        reset_stop_loss_manager()
        persistence_file = tmp_path / "test_stop_orders.json"
        monkeypatch.setattr(StopLossManager, "PERSISTENCE_FILE", str(persistence_file))
        return StopLossManager(connector)
    
    def test_create_stop_loss_success(self, manager):
        """测试成功创建止损单"""
        result = manager.create_stop_loss(
            symbol='ETHUSDT',
            trigger_price=Decimal('2000'),
            quantity=Decimal('0.1'),
            side='SELL'
        )
        
        assert result.is_success
        assert result.data['algo_id'] == 'SL_TEST123'
        assert 'SL_TEST123' in manager.stop_orders
    
    def test_create_stop_loss_duplicate_prevention(self, manager):
        """测试重复创建保护"""
        # 第一次创建
        manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        
        # 手动设置创建中标志
        manager.creating['ETHUSDT'] = True
        
        # 第二次创建（应该失败）
        result = manager.create_stop_loss(
            'ETHUSDT', Decimal('1900'), Decimal('0.1'), 'SELL'
        )
        
        assert result.is_error
        assert result.error_code == 'STOP_LOSS_CREATING'
    
    def test_create_stop_loss_already_exists(self, manager):
        """测试已存在止损单"""
        # 第一次创建
        manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        
        # 第二次创建（应该失败）
        result = manager.create_stop_loss(
            'ETHUSDT', Decimal('1900'), Decimal('0.1'), 'SELL'
        )
        
        assert result.is_error
        assert result.error_code == 'STOP_LOSS_EXISTS'
    
    def test_cancel_stop_loss_success(self, manager):
        """测试成功取消止损单"""
        # 先创建
        result = manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        algo_id = result.data['algo_id']
        
        # 取消
        result = manager.cancel_stop_loss('ETHUSDT', algo_id)
        
        assert result.is_success
        assert manager.stop_orders[algo_id]['status'] == 'CANCELED'
    
    def test_cancel_stop_loss_not_found(self, manager):
        """测试取消不存在的止损单"""
        result = manager.cancel_stop_loss('ETHUSDT', 'NONEXISTENT')
        
        assert result.is_error
        assert result.error_code == 'STOP_LOSS_NOT_FOUND'
    
    def test_get_stop_order(self, manager):
        """测试获取止损单信息"""
        result = manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        algo_id = result.data['algo_id']
        
        stop_order = manager.get_stop_order(algo_id)
        
        assert stop_order is not None
        assert stop_order['algo_id'] == algo_id
    
    def test_get_stop_orders_by_symbol(self, manager):
        """测试获取指定交易对的止损单"""
        # 创建一个止损单
        result = manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        algo_id = result.data['algo_id']
        
        orders = manager.get_stop_orders_by_symbol('ETHUSDT')
        
        # 至少有一个
        assert len(orders) >= 1
    
    def test_get_active_stop_orders(self, manager):
        """测试获取活跃止损单"""
        manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        # 取消第一个，创建第二个
        manager.cancel_stop_loss('ETHUSDT', 'SL_TEST123')
        manager.create_stop_loss('BTCUSDT', Decimal('60000'), Decimal('0.01'), 'SELL')
        
        active = manager.get_active_stop_orders()
        
        # 只有一个活跃的（BTCUSDT）
        assert len(active) == 1
    
    def test_update_stop_order_status(self, manager):
        """测试更新止损单状态"""
        result = manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        algo_id = result.data['algo_id']
        
        manager.update_stop_order_status(algo_id, 'TRIGGERED')
        
        assert manager.stop_orders[algo_id]['status'] == 'TRIGGERED'
    
    def test_cancel_all_stop_losses(self, manager):
        """测试取消所有止损单"""
        # 创建一个止损单
        manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        
        # 取消所有
        result = manager.cancel_all_stop_losses('ETHUSDT')
        
        assert result.is_success
        assert result.data['success_count'] >= 1
    
    def test_stop_loss_statistics(self, manager):
        """测试止损单统计"""
        manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        # 取消后再创建另一个
        manager.cancel_stop_loss('ETHUSDT', 'SL_TEST123')
        manager.create_stop_loss('BTCUSDT', Decimal('60000'), Decimal('0.01'), 'SELL')
        
        stats = manager.get_stop_loss_statistics()
        
        assert stats['total_stop_orders'] >= 1
        assert 'BTCUSDT' in stats['by_symbol']
    
    def test_persistence(self, manager, tmp_path, monkeypatch):
        """测试持久化"""
        # 创建止损单
        manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        
        # 创建新的管理器（模拟重启）
        persistence_file = tmp_path / "test_stop_orders.json"
        monkeypatch.setattr(StopLossManager, "PERSISTENCE_FILE", str(persistence_file))
        manager2 = StopLossManager(manager.connector)
        
        # 验证止损单已恢复
        assert len(manager2.stop_orders) > 0
        assert 'SL_TEST123' in manager2.stop_orders


class TestStopLossManagerIntegration:
    """测试止损单管理器集成"""
    
    def test_full_flow(self, tmp_path, monkeypatch):
        """测试完整流程"""
        from core.execution.stop_loss_manager import reset_stop_loss_manager
        
        reset_stop_loss_manager()
        
        connector = Mock()
        connector.create_stop_loss_order.return_value = Result.ok(data={
            'algo_id': 'SL_TEST',
            'status': 'WAIT_TO_TRIGGER'
        })
        connector.cancel_stop_loss_order.return_value = Result.ok(data={
            'algo_id': 'SL_TEST',
            'status': 'CANCELED'
        })
        
        persistence_file = tmp_path / "test_stop_orders.json"
        monkeypatch.setattr(StopLossManager, "PERSISTENCE_FILE", str(persistence_file))
        
        manager = StopLossManager(connector)
        
        # 创建
        result = manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'), 'SELL')
        assert result.is_success
        
        # 查询
        stop_order = manager.get_stop_order('SL_TEST')
        assert stop_order is not None
        
        # 取消
        result = manager.cancel_stop_loss('ETHUSDT', 'SL_TEST')
        assert result.is_success
        
        # 统计
        stats = manager.get_stop_loss_statistics()
        assert stats['total_stop_orders'] == 1
