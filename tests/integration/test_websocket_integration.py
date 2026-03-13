#!/usr/bin/env python3
"""
测试 WebSocket 真实连接
"""

import pytest
import time
from unittest.mock import Mock, patch
from core.market.websocket import BinanceWebSocket, reset_binance_websocket
from modules.utils.result import Result


class TestBinanceWebSocketReal:
    """测试 WebSocket 真实连接"""
    
    @pytest.fixture
    def ws(self):
        """创建 WebSocket 实例"""
        reset_binance_websocket()
        return BinanceWebSocket(testnet=True)
    
    def test_websocket_connection(self, ws):
        """测试 WebSocket 连接"""
        ws.start()
        
        # 等待连接
        time.sleep(0.5)
        
        assert ws.running is True
        
        ws.stop()
        assert ws.running is False
    
    def test_subscribe_multiple_channels(self, ws):
        """测试订阅多个频道"""
        ws.subscribe_ticker('ETHUSDT')
        ws.subscribe_kline('ETHUSDT', '1m')
        ws.subscribe_depth('ETHUSDT', '20')
        ws.subscribe_trade('ETHUSDT')
        
        assert len(ws.subscriptions) == 4
        assert 'ethusdt@ticker' in ws.subscriptions
        assert 'ethusdt@kline_1m' in ws.subscriptions
        assert 'ethusdt@depth20@100ms' in ws.subscriptions
        assert 'ethusdt@trade' in ws.subscriptions
    
    def test_unsubscribe_all(self, ws):
        """测试取消所有订阅"""
        ws.subscribe_ticker('ETHUSDT')
        ws.subscribe_ticker('BTCUSDT')
        ws.subscribe_kline('AVAXUSDT', '5m')
        
        ws.unsubscribe('ETHUSDT')
        ws.unsubscribe('BTCUSDT')
        ws.unsubscribe('AVAXUSDT')
        
        assert len(ws.subscriptions) == 0
    
    def test_callback_execution(self, ws):
        """测试回调函数执行"""
        callback_data = []
        
        def ticker_callback(data):
            callback_data.append(data)
        
        ws.register_callback('ticker', ticker_callback)
        
        # 模拟消息
        mock_message = {
            'e': '24hrTicker',
            's': 'ETHUSDT',
            'p': '2050.5'
        }
        
        ws._process_message(mock_message)
        
        assert len(callback_data) == 1
        assert callback_data[0]['s'] == 'ETHUSDT'
    
    def test_ticker_cache(self, ws):
        """测试 Ticker 缓存"""
        # 模拟接收 Ticker 推送
        mock_message = {
            'e': '24hrTicker',
            's': 'ETHUSDT',
            'p': '2050.5',
            'P': '2.5'
        }
        
        ws._process_message(mock_message)
        
        ticker = ws.get_ticker('ETHUSDT')
        
        assert ticker is not None
        assert ticker['p'] == '2050.5'
    
    def test_price_query(self, ws):
        """测试价格查询"""
        from decimal import Decimal
        
        # 模拟接收 Ticker 推送
        mock_message = {
            'e': '24hrTicker',
            's': 'ETHUSDT',
            'p': '2050.50'
        }
        
        ws._process_message(mock_message)
        
        price = ws.get_price('ETHUSDT')
        
        assert price is not None
        assert price == Decimal('2050.50')
    
    def test_kline_cache(self, ws):
        """测试 K 线缓存"""
        # 模拟接收 K 线推送
        mock_message = {
            'e': 'kline',
            's': 'ETHUSDT',
            'k': {
                't': 1234567890,
                'o': '2050.0',
                'h': '2060.0',
                'l': '2040.0',
                'c': '2055.0',
                'v': '100.0',
                'i': '1m'
            }
        }
        
        ws._process_message(mock_message)
        
        klines = ws.get_klines('ETHUSDT')
        
        assert len(klines) > 0
        assert klines[0]['c'] == '2055.0'
    
    def test_statistics(self, ws):
        """测试统计信息"""
        ws.start()
        
        # 模拟接收消息
        for i in range(10):
            mock_message = {
                'e': '24hrTicker',
                's': f'SYMBOL{i}',
                'p': '2050.5'
            }
            ws._process_message(mock_message)
        
        stats = ws.get_statistics()
        
        assert stats['message_count'] == 10
        assert stats['is_running'] is True
        
        ws.stop()
    
    def test_reconnect_mechanism(self, ws):
        """测试重连机制"""
        # 模拟连接失败
        with patch.object(ws, '_connect', side_effect=Exception("Connection failed")):
            ws.start()
            
            # 等待重连
            time.sleep(1)
            
            # 验证重连计数
            assert ws.reconnect_count > 0
            
            ws.stop()
    
    def test_multiple_symbols(self, ws):
        """测试多交易对"""
        symbols = ['ETHUSDT', 'BTCUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT']
        
        for symbol in symbols:
            ws.subscribe_ticker(symbol)
        
        # 模拟接收多个交易对的推送
        for symbol in symbols:
            mock_message = {
                'e': '24hrTicker',
                's': symbol,
                'p': '2050.5'
            }
            ws._process_message(mock_message)
        
        # 验证所有交易对都有缓存
        for symbol in symbols:
            ticker = ws.get_ticker(symbol)
            assert ticker is not None


class TestBinanceWebSocketIntegration:
    """测试 WebSocket 集成"""
    
    def test_websocket_with_strategy(self, tmp_path, monkeypatch):
        """测试 WebSocket 与策略集成"""
        from core.strategy.manager import StrategyManager
        from core.market.websocket import reset_binance_websocket
        
        reset_binance_websocket()
        
        connector = Mock()
        ws = BinanceWebSocket(testnet=True)
        
        # 订阅行情
        ws.subscribe_ticker('ETHUSDT')
        ws.start()
        
        # 启动策略
        monkeypatch.setattr(StrategyManager, "PERSISTENCE_FILE", str(tmp_path / "test.json"))
        strategy_manager = StrategyManager(connector=connector)
        result = strategy_manager.start_strategy('ETHUSDT', 'breakout', leverage=5, amount=100)
        
        assert result.is_success
        
        # 模拟接收行情推送
        mock_message = {
            'e': '24hrTicker',
            's': 'ETHUSDT',
            'p': '2050.5'
        }
        ws._process_message(mock_message)
        
        # 验证价格缓存
        price = ws.get_price('ETHUSDT')
        assert price is not None
        
        # 停止
        ws.stop()
        strategy_manager.stop_strategy('ETHUSDT')
    
    def test_websocket_with_order_manager(self, tmp_path, monkeypatch):
        """测试 WebSocket 与订单管理器集成"""
        from core.execution.order_manager import OrderManager
        from core.market.websocket import reset_binance_websocket
        
        reset_binance_websocket()
        
        connector = Mock()
        connector.place_order.return_value = Result.ok(data={
            'order_id': 'TEST123',
            'status': 'FILLED',
            'filled_quantity': '0.1',
            'avg_price': '2050.5'
        })
        
        ws = BinanceWebSocket(testnet=True)
        order_manager = OrderManager(connector)
        
        # 订阅成交
        ws.subscribe_trade('ETHUSDT')
        ws.start()
        
        # 创建订单
        from modules.models.order import Order, OrderType, OrderSide
        from decimal import Decimal
        
        order = Order('ETHUSDT', OrderSide.BUY, OrderType.MARKET, Decimal('0.1'))
        result = order_manager.create_order(order)
        
        assert result.is_success
        
        # 模拟成交推送
        mock_message = {
            'e': 'trade',
            's': 'ETHUSDT',
            't': 123456,
            'p': '2050.5',
            'q': '0.1',
            'b': 123456789,
            'a': 987654321,
            'T': 1234567890,
            'm': True
        }
        ws._process_message(mock_message)
        
        ws.stop()
