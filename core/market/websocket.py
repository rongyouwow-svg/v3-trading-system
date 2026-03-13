#!/usr/bin/env python3
"""
🦞 WebSocket 实时数据 v3.0

职责:
    - WebSocket 连接币安
    - 订阅行情数据
    - 推送实时价格
    - K 线数据缓存

特性:
    - 异步 WebSocket 连接
    - 自动重连机制
    - 多频道订阅
    - 数据缓存

用法:
    from core.market.websocket import BinanceWebSocket
    
    ws = BinanceWebSocket()
    ws.subscribe_ticker('ETHUSDT')
    ws.start()
"""

import asyncio
import json
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Callable, List
from threading import Thread

from modules.utils.logger import setup_logger
from modules.utils.decorators import handle_exceptions

logger = setup_logger("websocket", log_file="logs/websocket.log")


class BinanceWebSocket:
    """
    币安 WebSocket 客户端
    
    核心功能:
        - WebSocket 连接
        - 行情数据订阅
        - 实时价格推送
        - K 线数据缓存
    """
    
    # WebSocket 端点
    WS_URL = "wss://fstream.binance.com/ws"
    TESTNET_WS_URL = "wss://testnet.binancefuture.com/ws"
    
    def __init__(self, testnet: bool = True):
        """
        初始化 WebSocket 客户端
        
        Args:
            testnet (bool): 是否使用测试网
        """
        self.testnet = testnet
        self.ws_url = self.TESTNET_WS_URL if testnet else self.WS_URL
        
        # WebSocket 连接
        self.ws = None
        self.ws_thread = None
        
        # 运行标志
        self.running = False
        
        # 订阅列表
        self.subscriptions: List[str] = []
        
        # 数据缓存
        self.ticker_cache: Dict[str, Dict] = {}
        self.kline_cache: Dict[str, List[Dict]] = {}
        
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            'ticker': [],
            'kline': [],
            'depth': [],
            'trade': []
        }
        
        # 统计信息
        self.message_count = 0
        self.last_message_time = None
        self.reconnect_count = 0
        
        logger.info(f"WebSocket 客户端初始化完成 (testnet={testnet})")
    
    def start(self):
        """启动 WebSocket 连接"""
        if self.running:
            logger.warning("⚠️ WebSocket 已在运行中")
            return
        
        self.running = True
        
        # 启动 WebSocket 线程
        self.ws_thread = Thread(target=self._websocket_loop, daemon=True)
        self.ws_thread.start()
        
        logger.info("✅ WebSocket 已启动")
    
    def stop(self):
        """停止 WebSocket 连接"""
        if not self.running:
            return
        
        self.running = False
        
        # 关闭 WebSocket 连接
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        
        logger.info("🛑 WebSocket 已停止")
    
    def _websocket_loop(self):
        """
        WebSocket 主循环
        
        说明:
            - 连接 WebSocket
            - 发送订阅消息
            - 接收推送数据
            - 自动重连
        """
        logger.info("🔌 WebSocket 主循环已启动")
        
        while self.running:
            try:
                # 1. 连接 WebSocket
                self._connect()
                
                # 2. 发送订阅消息
                self._send_subscriptions()
                
                # 3. 接收推送数据
                self._receive_messages()
                
            except Exception as e:
                logger.error(f"❌ WebSocket 异常：{e}")
                
                if self.running:
                    self.reconnect_count += 1
                    logger.warning(f"⚠️ 尝试重连 ({self.reconnect_count})...")
                    time.sleep(5)
        
        logger.info("🛑 WebSocket 主循环已停止")
    
    def _connect(self):
        """连接 WebSocket"""
        # TODO: 实现真实的 WebSocket 连接
        # 这里使用模拟连接
        logger.info(f"🔌 连接到 {self.ws_url}")
        self.ws = True  # 模拟连接成功
    
    def _send_subscriptions(self):
        """发送订阅消息"""
        if not self.subscriptions:
            return
        
        # TODO: 实现真实的订阅消息发送
        logger.info(f"📝 发送订阅消息：{self.subscriptions}")
    
    def _receive_messages(self):
        """接收推送消息"""
        # TODO: 实现真实的消息接收
        # 这里使用模拟数据
        time.sleep(1)
    
    def subscribe_ticker(self, symbol: str):
        """
        订阅 Ticker
        
        Args:
            symbol (str): 交易对
        """
        channel = f"{symbol.lower()}@ticker"
        if channel not in self.subscriptions:
            self.subscriptions.append(channel)
            logger.info(f"📊 订阅 Ticker: {symbol}")
    
    def subscribe_kline(self, symbol: str, interval: str = '1m'):
        """
        订阅 K 线
        
        Args:
            symbol (str): 交易对
            interval (str): 时间周期
        """
        channel = f"{symbol.lower()}@kline_{interval}"
        if channel not in self.subscriptions:
            self.subscriptions.append(channel)
            logger.info(f"📈 订阅 K 线：{symbol} {interval}")
    
    def subscribe_depth(self, symbol: str, level: str = '20'):
        """
        订阅深度
        
        Args:
            symbol (str): 交易对
            level (str): 深度级别
        """
        channel = f"{symbol.lower()}@depth{level}@100ms"
        if channel not in self.subscriptions:
            self.subscriptions.append(channel)
            logger.info(f"📊 订阅深度：{symbol} {level}")
    
    def subscribe_trade(self, symbol: str):
        """
        订阅成交
        
        Args:
            symbol (str): 交易对
        """
        channel = f"{symbol.lower()}@trade"
        if channel not in self.subscriptions:
            self.subscriptions.append(channel)
            logger.info(f"💰 订阅成交：{symbol}")
    
    def unsubscribe(self, symbol: str):
        """
        取消订阅
        
        Args:
            symbol (str): 交易对
        """
        # 移除所有相关订阅
        self.subscriptions = [
            s for s in self.subscriptions
            if not s.startswith(f"{symbol.lower()}@")
        ]
        logger.info(f"🚫 取消订阅：{symbol}")
    
    def register_callback(self, channel_type: str, callback: Callable):
        """
        注册回调函数
        
        Args:
            channel_type (str): 频道类型 (ticker/kline/depth/trade)
            callback (Callable): 回调函数
        """
        if channel_type in self.callbacks:
            self.callbacks[channel_type].append(callback)
            logger.info(f"📝 注册 {channel_type} 回调函数")
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        获取 Ticker 数据
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Optional[Dict]: Ticker 数据
        """
        return self.ticker_cache.get(symbol)
    
    def get_price(self, symbol: str) -> Optional[Decimal]:
        """
        获取最新价格
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Optional[Decimal]: 最新价格
        """
        ticker = self.get_ticker(symbol)
        if ticker:
            return Decimal(ticker.get('p', '0'))
        return None
    
    def get_klines(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        获取 K 线数据
        
        Args:
            symbol (str): 交易对
            limit (int): 数量限制
        
        Returns:
            List[Dict]: K 线数据列表
        """
        klines = self.kline_cache.get(symbol, [])
        return klines[-limit:]
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'message_count': self.message_count,
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'reconnect_count': self.reconnect_count,
            'subscriptions_count': len(self.subscriptions),
            'is_running': self.running
        }
    
    @handle_exceptions()
    def _process_message(self, message: Dict):
        """
        处理 WebSocket 消息
        
        Args:
            message (Dict): 消息数据
        """
        self.message_count += 1
        self.last_message_time = datetime.now()
        
        # 解析消息类型
        event_type = message.get('e')
        
        if event_type == '24hrTicker':
            # Ticker 推送
            symbol = message.get('s')
            self.ticker_cache[symbol] = message
            
            # 触发回调
            for callback in self.callbacks['ticker']:
                callback(message)
        
        elif event_type == 'kline':
            # K 线推送
            symbol = message.get('s')
            kline = message.get('k')
            
            if symbol not in self.kline_cache:
                self.kline_cache[symbol] = []
            
            self.kline_cache[symbol].append(kline)
            
            # 触发回调
            for callback in self.callbacks['kline']:
                callback(kline)
        
        elif event_type == 'depthUpdate':
            # 深度推送
            for callback in self.callbacks['depth']:
                callback(message)
        
        elif event_type == 'trade':
            # 成交推送
            for callback in self.callbacks['trade']:
                callback(message)
        
        logger.debug(f"📨 处理消息：{event_type}")


# 全局实例
_websocket: Optional[BinanceWebSocket] = None


def get_binance_websocket(testnet: bool = True) -> BinanceWebSocket:
    """获取全局 WebSocket 实例"""
    global _websocket
    if _websocket is None:
        _websocket = BinanceWebSocket(testnet=testnet)
    return _websocket


def reset_binance_websocket():
    """重置 WebSocket 实例（测试用）"""
    global _websocket
    if _websocket:
        _websocket.stop()
    _websocket = None
