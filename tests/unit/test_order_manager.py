#!/usr/bin/env python3
"""
测试订单管理器
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock
from core.execution.order_manager import OrderManager, reset_order_manager
from modules.models.order import Order, OrderType, OrderSide, OrderStatus
from modules.utils.result import Result


class TestOrderManager:
    """测试订单管理器"""
    
    @pytest.fixture
    def connector(self):
        """创建模拟连接器"""
        connector = Mock()
        connector.place_order.return_value = Result.ok(data={
            'order_id': '123',
            'status': 'OPEN',
            'filled_quantity': '0',
            'avg_price': None
        })
        connector.cancel_order.return_value = Result.ok(data={
            'order_id': '123',
            'status': 'CANCELED'
        })
        return connector
    
    @pytest.fixture
    def manager(self, connector):
        """创建订单管理器实例"""
        reset_order_manager()
        return OrderManager(connector)
    
    def test_create_order_success(self, manager):
        """测试成功创建订单"""
        order = Order(
            symbol='ETHUSDT',
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal('0.1')
        )
        
        result = manager.create_order(order)
        
        assert result.is_success
        assert result.data['order_id'] == '123'
        assert '123' in manager.orders
    
    def test_create_order_duplicate_prevention(self, manager):
        """测试重复创建保护"""
        order = Order(
            symbol='ETHUSDT',
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal('0.1')
        )
        
        # 第一次创建
        manager.create_order(order)
        
        # 手动设置创建中标志
        manager.creating['ETHUSDT'] = True
        
        # 第二次创建（应该失败）
        result = manager.create_order(order)
        
        assert result.is_error
        assert result.error_code == 'ORDER_CREATING'
    
    def test_cancel_order_success(self, manager):
        """测试成功取消订单"""
        # 先创建订单
        order = Order(
            symbol='ETHUSDT',
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal('0.1')
        )
        result = manager.create_order(order)
        order_id = result.data['order_id']
        
        # 取消订单
        result = manager.cancel_order('ETHUSDT', order_id)
        
        assert result.is_success
        assert manager.orders[order_id].status == OrderStatus.CANCELED
    
    def test_get_order_status(self, manager):
        """测试获取订单状态"""
        order = Order(
            symbol='ETHUSDT',
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal('0.1')
        )
        result = manager.create_order(order)
        order_id = result.data['order_id']
        
        retrieved = manager.get_order_status(order_id)
        
        assert retrieved is not None
        assert retrieved.order_id == order_id
    
    def test_get_orders_by_symbol(self, manager, connector):
        """测试获取指定交易对的订单"""
        # 设置连接器返回不同 order_id
        connector.place_order.side_effect = [
            Result.ok(data={'order_id': '1', 'status': 'OPEN', 'filled_quantity': '0'}),
            Result.ok(data={'order_id': '2', 'status': 'OPEN', 'filled_quantity': '0'}),
            Result.ok(data={'order_id': '3', 'status': 'OPEN', 'filled_quantity': '0'})
        ]
        
        # 创建多个订单
        manager.create_order(Order('ETHUSDT', OrderSide.BUY, OrderType.MARKET, Decimal('0.1')))
        manager.create_order(Order('ETHUSDT', OrderSide.SELL, OrderType.MARKET, Decimal('0.2')))
        manager.create_order(Order('BTCUSDT', OrderSide.BUY, OrderType.MARKET, Decimal('0.01')))
        
        orders = manager.get_orders_by_symbol('ETHUSDT')
        
        assert len(orders) == 2
    
    def test_get_active_orders(self, manager, connector):
        """测试获取活跃订单"""
        connector.place_order.return_value = Result.ok(data={'order_id': '1', 'status': 'OPEN', 'filled_quantity': '0'})
        
        # 创建订单
        order = Order('ETHUSDT', OrderSide.BUY, OrderType.MARKET, Decimal('0.1'))
        manager.create_order(order)
        
        active = manager.get_active_orders()
        
        assert len(active) > 0
    
    def test_update_order_status(self, manager):
        """测试更新订单状态"""
        order = Order('ETHUSDT', OrderSide.BUY, OrderType.MARKET, Decimal('0.1'))
        result = manager.create_order(order)
        order_id = result.data['order_id']
        
        manager.update_order_status(order_id, OrderStatus.CANCELED)
        
        assert manager.orders[order_id].status == OrderStatus.CANCELED
    
    def test_order_statistics(self, manager, connector):
        """测试订单统计"""
        # 设置连接器返回不同 order_id
        connector.place_order.side_effect = [
            Result.ok(data={'order_id': '1', 'status': 'OPEN', 'filled_quantity': '0'}),
            Result.ok(data={'order_id': '2', 'status': 'OPEN', 'filled_quantity': '0'})
        ]
        
        # 创建多个订单
        manager.create_order(Order('ETHUSDT', OrderSide.BUY, OrderType.MARKET, Decimal('0.1')))
        manager.create_order(Order('BTCUSDT', OrderSide.BUY, OrderType.MARKET, Decimal('0.01')))
        
        stats = manager.get_order_statistics()
        
        assert stats['total_orders'] == 2
        assert 'ETHUSDT' in stats['by_symbol']
        assert 'BTCUSDT' in stats['by_symbol']
