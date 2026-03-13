#!/usr/bin/env python3
"""
🦞 订单管理器 v3.0

职责:
    - 订单创建
    - 订单取消
    - 订单状态跟踪
    - 订单生命周期管理

特性:
    - 订单状态机（PENDING→OPEN→FILLED/CANCELED）
    - 精度自动处理
    - 重试机制
    - 订单持久化

用法:
    from core.execution.order_manager import OrderManager
    
    manager = OrderManager(connector)
    result = manager.create_order(order)
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import time

from modules.models.order import Order, OrderType, OrderSide, OrderStatus
from modules.utils.result import Result, ok, fail
from modules.utils.exceptions import (
    OrderCreateException,
    OrderCancelException,
    NetworkException,
    InsufficientBalanceException
)
from modules.utils.logger import setup_logger
from modules.utils.decorators import handle_exceptions, log_execution, retry_on_exception
from modules.utils.precision import PrecisionUtils

logger = setup_logger("order_manager", log_file="logs/order_manager.log")


class OrderManager:
    """
    订单管理器
    
    核心功能:
        - 订单创建（带精度处理）
        - 订单取消
        - 订单状态跟踪
        - 订单生命周期管理
    """
    
    def __init__(self, connector):
        """
        初始化订单管理器
        
        Args:
            connector: 交易所连接器
        """
        self.connector = connector
        
        # 订单存储 {order_id: Order}
        self.orders: Dict[str, Order] = {}
        
        # 订单创建中标志（防重）{symbol: bool}
        self.creating: Dict[str, bool] = {}
        
        logger.info("订单管理器初始化完成")
    
    @handle_exceptions()
    @log_execution()
    @retry_on_exception(max_retries=3, delay=1.0)
    def create_order(self, order: Order) -> Result:
        """
        创建订单
        
        Args:
            order (Order): 订单对象
        
        Returns:
            Result: 操作结果
        
        Example:
            >>> order = Order('ETHUSDT', OrderSide.BUY, OrderType.MARKET, Decimal('0.1'))
            >>> result = manager.create_order(order)
        """
        symbol = order.symbol
        
        # 检查是否正在创建（防重机制）
        if self.creating.get(symbol, False):
            logger.warning(f"⚠️ {symbol} 订单正在创建中，跳过")
            return fail(
                error_code="ORDER_CREATING",
                message=f"{symbol} 订单正在创建中，请稍后再试"
            )
        
        try:
            # 设置创建中标志
            self.creating[symbol] = True
            
            # 1. 参数验证
            is_valid, error_msg = PrecisionUtils.validate_quantity(symbol, order.quantity)
            if not is_valid:
                return fail(error_code="INVALID_QUANTITY", message=error_msg)
            
            if order.price and order.type == OrderType.LIMIT:
                is_valid, error_msg = PrecisionUtils.validate_price(symbol, order.price)
                if not is_valid:
                    return fail(error_code="INVALID_PRICE", message=error_msg)
            
            # 2. 标准化精度
            order.quantity = PrecisionUtils.normalize_quantity(symbol, order.quantity)
            if order.price:
                order.price = PrecisionUtils.normalize_price(symbol, order.price)
            
            logger.info(f"📝 创建订单：{symbol} {order.side.value} {order.quantity} @ {order.price or 'MARKET'}")
            
            # 3. 提交到交易所
            result = self.connector.place_order(order)
            
            if not result.is_success:
                logger.error(f"❌ 订单创建失败：{result.message}")
                return result
            
            # 4. 更新订单信息
            order_data = result.data
            order.order_id = order_data.get('order_id')
            order.status = OrderStatus(order_data.get('status', 'OPEN'))
            order.filled_quantity = Decimal(order_data.get('filled_quantity', '0'))
            order.avg_price = Decimal(order_data.get('avg_price', '0')) if order_data.get('avg_price') else None
            
            # 5. 存储订单
            if order.order_id:
                self.orders[order.order_id] = order
            
            logger.info(f"✅ 订单创建成功：{order.order_id}")
            
            return ok(
                data={
                    'order_id': order.order_id,
                    'symbol': order.symbol,
                    'status': order.status.value,
                    'quantity': str(order.quantity),
                    'filled_quantity': str(order.filled_quantity)
                },
                message="订单创建成功"
            )
            
        finally:
            # 清除创建中标志
            self.creating[symbol] = False
    
    @handle_exceptions()
    @log_execution()
    @retry_on_exception(max_retries=3, delay=1.0)
    def cancel_order(self, symbol: str, order_id: str) -> Result:
        """
        取消订单
        
        Args:
            symbol (str): 交易对
            order_id (str): 订单 ID
        
        Returns:
            Result: 操作结果
        """
        logger.info(f"🚫 取消订单：{symbol} {order_id}")
        
        # 1. 检查本地订单
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELED]:
                logger.warning(f"⚠️ 订单 {order_id} 状态为 {order.status.value}，无法取消")
                return fail(
                    error_code="ORDER_NOT_CANCELABLE",
                    message=f"订单状态为 {order.status.value}，无法取消"
                )
        
        # 2. 调用交易所取消
        result = self.connector.cancel_order(symbol, order_id)
        
        if not result.is_success:
            logger.error(f"❌ 订单取消失败：{result.message}")
            return result
        
        # 3. 更新本地订单状态
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELED
        
        logger.info(f"✅ 订单取消成功：{order_id}")
        
        return ok(
            data={'order_id': order_id, 'symbol': symbol, 'status': 'CANCELED'},
            message="订单取消成功"
        )
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """
        获取订单状态
        
        Args:
            order_id (str): 订单 ID
        
        Returns:
            Optional[Order]: 订单对象，不存在返回 None
        """
        return self.orders.get(order_id)
    
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """
        获取指定交易对的所有订单
        
        Args:
            symbol (str): 交易对
        
        Returns:
            List[Order]: 订单列表
        """
        return [order for order in self.orders.values() if order.symbol == symbol]
    
    def get_active_orders(self) -> List[Order]:
        """
        获取所有活跃订单（未成交且未取消）
        
        Returns:
            List[Order]: 活跃订单列表
        """
        return [
            order for order in self.orders.values()
            if order.status in [OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]
        ]
    
    def update_order_status(self, order_id: str, new_status: OrderStatus, 
                           filled_quantity: Optional[Decimal] = None,
                           avg_price: Optional[Decimal] = None):
        """
        更新订单状态
        
        Args:
            order_id (str): 订单 ID
            new_status (OrderStatus): 新状态
            filled_quantity (Decimal, optional): 已成交数量
            avg_price (Decimal, optional): 成交均价
        """
        if order_id not in self.orders:
            logger.warning(f"⚠️ 订单 {order_id} 不存在，无法更新状态")
            return
        
        order = self.orders[order_id]
        order.update_status(new_status)
        
        if filled_quantity is not None:
            order.filled_quantity = filled_quantity
        
        if avg_price is not None:
            order.avg_price = avg_price
        
        logger.debug(f"📊 订单 {order_id} 状态更新为 {new_status.value}")
    
    def clear_old_orders(self, max_age_hours: int = 24):
        """
        清理旧订单
        
        Args:
            max_age_hours (int): 最大保留时间（小时）
        """
        now = datetime.now()
        to_remove = []
        
        for order_id, order in self.orders.items():
            age = (now - order.updated_at).total_seconds() / 3600
            if age > max_age_hours and order.status in [OrderStatus.FILLED, OrderStatus.CANCELED]:
                to_remove.append(order_id)
        
        for order_id in to_remove:
            del self.orders[order_id]
        
        logger.info(f"🧹 清理了 {len(to_remove)} 个旧订单")
    
    def get_order_statistics(self) -> Dict:
        """
        获取订单统计信息
        
        Returns:
            Dict: 统计信息
        """
        total = len(self.orders)
        by_status = {}
        by_symbol = {}
        
        for order in self.orders.values():
            # 按状态统计
            status = order.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            # 按币种统计
            symbol = order.symbol
            by_symbol[symbol] = by_symbol.get(symbol, 0) + 1
        
        return {
            'total_orders': total,
            'by_status': by_status,
            'by_symbol': by_symbol,
            'active_orders': len(self.get_active_orders())
        }


# 全局实例
_order_manager: Optional[OrderManager] = None


def get_order_manager(connector=None) -> OrderManager:
    """获取全局订单管理器实例"""
    global _order_manager
    if _order_manager is None:
        if connector is None:
            raise ValueError("首次调用需要提供 connector 参数")
        _order_manager = OrderManager(connector)
    return _order_manager


def reset_order_manager():
    """重置订单管理器（测试用）"""
    global _order_manager
    _order_manager = None
