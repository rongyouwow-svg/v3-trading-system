#!/usr/bin/env python3
"""
测试成交监听器和 WebSocket
"""

import pytest
import time
from unittest.mock import Mock
from core.execution.fill_monitor import FillMonitor, reset_fill_monitor
from core.market.websocket import BinanceWebSocket, reset_binance_websocket


class TestFillMonitor:
    """测试成交监听器"""
    
    @pytest.fixture
    def components(self):
        """创建组件"""
        connector = Mock()
        order_manager = Mock()
        stop_loss_manager = Mock()
        return connector, order_manager, stop_loss_manager
    
    @pytest.fixture
    def monitor(self, components):
        """创建成交监听器"""
        reset_fill_monitor()
        connector, order_manager, stop_loss_manager = components
        return FillMonitor(connector, order_manager, stop_loss_manager)
    
    def test_fill_monitor_init(self, monitor):
        """测试初始化"""
        assert monitor is not None
        assert monitor.running is False
        assert len(monitor.callbacks) == 0
    
    def test_start_stop(self, monitor):
        """测试启动停止"""
        monitor.start()
        assert monitor.running is True
        
        time.sleep(0.1)
        
        monitor.stop()
        assert monitor.running is False
    
    def test_register_callback(self, monitor):
        """测试注册回调"""
        def callback(fill_data):
            pass
        
        monitor.register_callback(callback)
        
        assert len(monitor.callbacks) == 1
        assert callback in monitor.callbacks
    
    def test_unregister_callback(self, monitor):
        """测试注销回调"""
        def callback(fill_data):
            pass
        
        monitor.register_callback(callback)
        monitor.unregister_callback(callback)
        
        assert len(monitor.callbacks) == 0
    
    def test_get_statistics(self, monitor):
        """测试获取统计信息"""
        stats = monitor.get_statistics()
        
        assert 'fills_count' in stats
        assert 'last_fill_time' in stats
        assert 'is_running' in stats


class TestBinanceWebSocket:
    """测试 WebSocket"""
    
    @pytest.fixture
    def ws(self):
        """创建 WebSocket 实例"""
        reset_binance_websocket()
        return BinanceWebSocket(testnet=True)
    
    def test_websocket_init(self, ws):
        """测试初始化"""
        assert ws is not None
        assert ws.running is False
        assert ws.testnet is True
        assert len(ws.subscriptions) == 0
    
    def test_start_stop(self, ws):
        """测试启动停止"""
        ws.start()
        assert ws.running is True
        
        time.sleep(0.1)
        
        ws.stop()
        assert ws.running is False
    
    def test_subscribe_ticker(self, ws):
        """测试订阅 Ticker"""
        ws.subscribe_ticker('ETHUSDT')
        
        assert 'ethusdt@ticker' in ws.subscriptions
    
    def test_subscribe_kline(self, ws):
        """测试订阅 K 线"""
        ws.subscribe_kline('ETHUSDT', '1m')
        
        assert 'ethusdt@kline_1m' in ws.subscriptions
    
    def test_subscribe_depth(self, ws):
        """测试订阅深度"""
        ws.subscribe_depth('ETHUSDT', '20')
        
        assert 'ethusdt@depth20@100ms' in ws.subscriptions
    
    def test_subscribe_trade(self, ws):
        """测试订阅成交"""
        ws.subscribe_trade('ETHUSDT')
        
        assert 'ethusdt@trade' in ws.subscriptions
    
    def test_unsubscribe(self, ws):
        """测试取消订阅"""
        ws.subscribe_ticker('ETHUSDT')
        ws.subscribe_kline('ETHUSDT', '1m')
        
        ws.unsubscribe('ETHUSDT')
        
        assert len(ws.subscriptions) == 0
    
    def test_register_callback(self, ws):
        """测试注册回调"""
        def callback(data):
            pass
        
        ws.register_callback('ticker', callback)
        
        assert len(ws.callbacks['ticker']) == 1
    
    def test_get_statistics(self, ws):
        """测试获取统计信息"""
        stats = ws.get_statistics()
        
        assert 'message_count' in stats
        assert 'reconnect_count' in stats
        assert 'subscriptions_count' in stats
        assert 'is_running' in stats


class TestIntegration:
    """测试集成"""
    
    def test_websocket_and_fill_monitor(self):
        """测试 WebSocket + 成交监听器集成"""
        reset_binance_websocket()
        reset_fill_monitor()
        
        from unittest.mock import Mock
        connector = Mock()
        order_manager = Mock()
        stop_loss_manager = Mock()
        
        # 创建组件
        ws = BinanceWebSocket(testnet=True)
        monitor = FillMonitor(connector, order_manager, stop_loss_manager)
        
        # 订阅行情
        ws.subscribe_ticker('ETHUSDT')
        ws.subscribe_kline('ETHUSDT', '1m')
        
        # 启动
        ws.start()
        monitor.start()
        
        # 等待
        time.sleep(0.5)
        
        # 验证
        assert ws.running is True
        assert monitor.running is True
        assert len(ws.subscriptions) == 2
        
        # 停止
        ws.stop()
        monitor.stop()
        
        assert ws.running is False
        assert monitor.running is False
