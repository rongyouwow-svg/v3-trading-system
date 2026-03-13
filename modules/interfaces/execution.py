#!/usr/bin/env python3
"""
执行引擎接口定义

所有执行引擎实现必须实现此接口。
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal

from modules.models.order import Order
from modules.utils.result import Result


class IExecutionEngine(ABC):
    """
    执行引擎接口 - 必须实现
    """

    @abstractmethod
    def create_order(self, order: Order) -> Result:
        """
        创建订单

        Args:
            order (Order): 订单对象

        Returns:
            Result: 操作结果
        """
        pass

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> Result:
        """
        取消订单

        Args:
            symbol (str): 交易对
            order_id (str): 订单 ID

        Returns:
            Result: 操作结果
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """
        获取订单状态

        Args:
            order_id (str): 订单 ID

        Returns:
            Optional[Order]: 订单状态
        """
        pass

    @abstractmethod
    def create_stop_loss(self, symbol: str, trigger_price: Decimal, quantity: Decimal) -> Result:
        """
        创建止损单

        Args:
            symbol (str): 交易对
            trigger_price (Decimal): 触发价格
            quantity (Decimal): 数量

        Returns:
            Result: 操作结果
        """
        pass

    @abstractmethod
    def cancel_stop_loss(self, symbol: str, algo_id: str) -> Result:
        """
        取消止损单

        Args:
            symbol (str): 交易对
            algo_id (str): 止损单 ID

        Returns:
            Result: 操作结果
        """
        pass

    @abstractmethod
    def get_stop_orders(self, symbol: str) -> List[dict]:
        """
        获取止损单列表

        Args:
            symbol (str): 交易对

        Returns:
            List[dict]: 止损单列表
        """
        pass
