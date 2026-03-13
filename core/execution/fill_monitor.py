#!/usr/bin/env python3
"""
🦞 成交监听器 v3.0

职责:
    - WebSocket 监听成交推送
    - 成交记录持久化
    - 状态更新通知
    - 触发止损单创建

特性:
    - 异步 WebSocket 连接
    - 自动重连机制
    - 成交数据解析
    - 事件驱动通知

用法:
    from core.execution.fill_monitor import FillMonitor
    
    monitor = FillMonitor(connector, order_manager, stop_loss_manager)
    monitor.start()
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
from modules.utils.result import Result

logger = setup_logger("fill_monitor", log_file="logs/fill_monitor.log")


class FillMonitor:
    """
    成交监听器
    
    核心功能:
        - WebSocket 监听成交推送
        - 成交记录持久化
        - 状态更新通知
        - 触发止损单创建
    """
    
    def __init__(self, connector, order_manager, stop_loss_manager):
        """
        初始化成交监听器
        
        Args:
            connector: 交易所连接器
            order_manager: 订单管理器
            stop_loss_manager: 止损单管理器
        """
        self.connector = connector
        self.order_manager = order_manager
        self.stop_loss_manager = stop_loss_manager
        
        # 运行标志
        self.running = False
        
        # WebSocket 连接
        self.ws = None
        self.ws_thread = None
        
        # 成交回调函数列表
        self.callbacks: List[Callable] = []
        
        # 成交统计
        self.fills_count = 0
        self.last_fill_time = None
        
        logger.info("成交监听器初始化完成")
    
    def start(self):
        """启动成交监听"""
        if self.running:
            logger.warning("⚠️ 成交监听器已在运行中")
            return
        
        self.running = True
        
        # 启动 WebSocket 监听线程
        self.ws_thread = Thread(target=self._websocket_listener, daemon=True)
        self.ws_thread.start()
        
        logger.info("✅ 成交监听器已启动")
    
    def stop(self):
        """停止成交监听"""
        if not self.running:
            return
        
        self.running = False
        
        # 关闭 WebSocket 连接
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        
        logger.info("🛑 成交监听器已停止")
    
    def _websocket_listener(self):
        """
        WebSocket 监听线程
        
        说明:
            - 连接币安 WebSocket
            - 监听成交推送
            - 解析成交数据
            - 触发回调
        """
        logger.info("🔌 WebSocket 监听线程已启动")
        
        while self.running:
            try:
                # TODO: 实现真实的 WebSocket 连接
                # 这里使用模拟数据演示流程
                
                # 模拟接收成交推送
                fill_data = self._mock_receive_fill()
                
                if fill_data:
                    self._process_fill(fill_data)
                
                # 等待下一次推送
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ WebSocket 监听异常：{e}")
                time.sleep(5)
        
        logger.info("🛑 WebSocket 监听线程已停止")
    
    def _mock_receive_fill(self) -> Optional[Dict]:
        """
        模拟接收成交推送（测试用）
        
        Returns:
            Optional[Dict]: 成交数据
        """
        # 实际实现应该从 WebSocket 接收数据
        return None
    
    def _process_fill(self, fill_data: Dict):
        """
        处理成交数据
        
        Args:
            fill_data (Dict): 成交数据
        """
        try:
            # 1. 解析成交数据
            symbol = fill_data.get('symbol')
            order_id = fill_data.get('order_id')
            fill_id = fill_data.get('fill_id')
            side = fill_data.get('side')
            quantity = Decimal(fill_data.get('quantity', '0'))
            price = Decimal(fill_data.get('price', '0'))
            commission = Decimal(fill_data.get('commission', '0'))
            commission_asset = fill_data.get('commission_asset', 'USDT')
            is_maker = fill_data.get('is_maker', False)
            trade_time = datetime.fromisoformat(fill_data.get('time')) if fill_data.get('time') else datetime.now()
            
            logger.info(f"📊 成交：{symbol} {side} {quantity} @ {price}")
            
            # 2. 更新订单状态
            if order_id:
                self.order_manager.update_order_status(
                    order_id,
                    fill_status='FILLED',
                    filled_quantity=quantity,
                    avg_price=price
                )
            
            # 3. 持久化成交记录
            self._save_fill_record({
                'fill_id': fill_id,
                'order_id': order_id,
                'symbol': symbol,
                'side': side,
                'quantity': str(quantity),
                'price': str(price),
                'commission': str(commission),
                'commission_asset': commission_asset,
                'is_maker': is_maker,
                'trade_time': trade_time.isoformat()
            })
            
            # 4. 更新统计
            self.fills_count += 1
            self.last_fill_time = datetime.now()
            
            # 5. 触发回调
            self._trigger_callbacks({
                'fill_id': fill_id,
                'order_id': order_id,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'commission': commission,
                'trade_time': trade_time
            })
            
            # 6. 检查是否需要创建止损单
            self._check_create_stop_loss(symbol, side, quantity, price)
            
        except Exception as e:
            logger.error(f"❌ 处理成交数据异常：{e}")
    
    def _save_fill_record(self, fill_data: Dict):
        """
        保存成交记录
        
        Args:
            fill_data (Dict): 成交数据
        """
        # TODO: 实现持久化到数据库
        logger.debug(f"📝 保存成交记录：{fill_data['fill_id']}")
    
    def _trigger_callbacks(self, fill_data: Dict):
        """
        触发回调函数
        
        Args:
            fill_data (Dict): 成交数据
        """
        for callback in self.callbacks:
            try:
                callback(fill_data)
            except Exception as e:
                logger.error(f"❌ 回调函数执行异常：{e}")
    
    def _check_create_stop_loss(self, symbol: str, side: str, quantity: Decimal, price: Decimal):
        """
        检查是否需要创建止损单
        
        Args:
            symbol (str): 交易对
            side (str): 方向
            quantity (Decimal): 数量
            price (Decimal): 价格
        """
        # TODO: 根据策略配置决定是否创建止损单
        # 示例：多头持仓，创建止损单
        if side == 'BUY':
            stop_price = price * Decimal('0.95')  # 5% 止损
            logger.info(f"💡 建议创建止损单：{symbol} SELL 触发价={stop_price}")
            # self.stop_loss_manager.create_stop_loss(symbol, stop_price, quantity, 'SELL')
    
    def register_callback(self, callback: Callable):
        """
        注册成交回调函数
        
        Args:
            callback (Callable): 回调函数，接收 fill_data 参数
        """
        self.callbacks.append(callback)
        logger.info(f"📝 注册成交回调函数")
    
    def unregister_callback(self, callback: Callable):
        """
        注销成交回调函数
        
        Args:
            callback (Callable): 回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.info(f"🗑️ 注销成交回调函数")
    
    def get_statistics(self) -> Dict:
        """
        获取成交统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'fills_count': self.fills_count,
            'last_fill_time': self.last_fill_time.isoformat() if self.last_fill_time else None,
            'is_running': self.running
        }
    
    @handle_exceptions()
    def on_fill(self, fill_data: Dict):
        """
        成交事件处理（默认回调）
        
        Args:
            fill_data (Dict): 成交数据
        """
        logger.info(
            f"💰 成交事件：{fill_data['symbol']} {fill_data['side']} "
            f"{fill_data['quantity']} @ {fill_data['price']}"
        )


# 全局实例
_fill_monitor: Optional[FillMonitor] = None


def get_fill_monitor(connector=None, order_manager=None, stop_loss_manager=None) -> FillMonitor:
    """获取全局成交监听器实例"""
    global _fill_monitor
    if _fill_monitor is None:
        if not all([connector, order_manager, stop_loss_manager]):
            raise ValueError("首次调用需要提供 connector, order_manager, stop_loss_manager 参数")
        _fill_monitor = FillMonitor(connector, order_manager, stop_loss_manager)
    return _fill_monitor


def reset_fill_monitor():
    """重置成交监听器（测试用）"""
    global _fill_monitor
    if _fill_monitor:
        _fill_monitor.stop()
    _fill_monitor = None
