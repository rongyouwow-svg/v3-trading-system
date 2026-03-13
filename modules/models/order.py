#!/usr/bin/env python3
"""
订单数据对象

所有模块必须使用 Order 类传递订单数据，禁止使用字典。

用法:
    from decimal import Decimal
    from modules.models.order import Order, OrderType, OrderStatus

    order = Order(
        symbol='ETHUSDT',
        side='BUY',
        type=OrderType.MARKET,
        quantity=Decimal('0.1')
    )
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from enum import Enum


class OrderType(Enum):
    """订单类型"""

    MARKET = "MARKET"  # 市价单
    LIMIT = "LIMIT"  # 限价单
    STOP_MARKET = "STOP_MARKET"  # 止损市价单
    STOP_LIMIT = "STOP_LIMIT"  # 止损限价单


class OrderStatus(Enum):
    """订单状态"""

    PENDING = "PENDING"  # 待提交
    OPEN = "OPEN"  # 开放中
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # 部分成交
    FILLED = "FILLED"  # 已成交
    CANCELED = "CANCELED"  # 已取消
    REJECTED = "REJECTED"  # 已拒绝
    EXPIRED = "EXPIRED"  # 已过期


class OrderSide(Enum):
    """订单方向"""

    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Order:
    """
    订单数据对象 - 所有模块必须使用

    Attributes:
        symbol: 交易对（如 ETHUSDT）
        side: 买卖方向（BUY/SELL）
        type: 订单类型（MARKET/LIMIT 等）
        quantity: 数量（必须使用 Decimal）
        price: 价格（限价单必填）
        stop_price: 止损触发价（止损单必填）
        order_id: 订单 ID（交易所返回）
        status: 订单状态
        filled_quantity: 已成交数量
        avg_price: 成交均价
        created_at: 创建时间
        updated_at: 更新时间
        strategy_id: 关联策略 ID（可选）
        client_order_id: 客户端订单 ID（可选）
    """

    symbol: str
    side: OrderSide
    type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: Decimal = Decimal("0")
    avg_price: Optional[Decimal] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    strategy_id: Optional[str] = None
    client_order_id: Optional[str] = None

    def __post_init__(self):
        """初始化后验证"""
        # 验证数量必须为正
        if self.quantity <= 0:
            raise ValueError("订单数量必须为正数")

        # 限价单必须有价格
        if self.type == OrderType.LIMIT and self.price is None:
            raise ValueError("限价单必须指定价格")

        # 止损单必须有止损价
        if self.type in [OrderType.STOP_MARKET, OrderType.STOP_LIMIT] and self.stop_price is None:
            raise ValueError("止损单必须指定止损触发价")

        # 设置创建时间
        if self.created_at is None:
            self.created_at = datetime.now()

        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """
        转换为字典（用于 JSON 序列化）

        Returns:
            dict: 字典格式的订单数据
        """
        return {
            "symbol": self.symbol,
            "side": self.side.value,
            "type": self.type.value,
            "quantity": str(self.quantity),
            "price": str(self.price) if self.price else None,
            "stop_price": str(self.stop_price) if self.stop_price else None,
            "order_id": self.order_id,
            "status": self.status.value,
            "filled_quantity": str(self.filled_quantity),
            "avg_price": str(self.avg_price) if self.avg_price else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "strategy_id": self.strategy_id,
            "client_order_id": self.client_order_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        """
        从字典创建订单对象

        Args:
            data: 字典格式的订单数据

        Returns:
            Order: 订单对象
        """
        return cls(
            symbol=data["symbol"],
            side=OrderSide(data["side"]),
            type=OrderType(data["type"]),
            quantity=Decimal(data["quantity"]),
            price=Decimal(data["price"]) if data.get("price") else None,
            stop_price=Decimal(data["stop_price"]) if data.get("stop_price") else None,
            order_id=data.get("order_id"),
            status=OrderStatus(data.get("status", "PENDING")),
            filled_quantity=Decimal(data.get("filled_quantity", "0")),
            avg_price=Decimal(data["avg_price"]) if data.get("avg_price") else None,
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
            ),
            strategy_id=data.get("strategy_id"),
            client_order_id=data.get("client_order_id"),
        )

    def is_buy(self) -> bool:
        """是否买入"""
        return self.side == OrderSide.BUY

    def is_sell(self) -> bool:
        """是否卖出"""
        return self.side == OrderSide.SELL

    def is_market_order(self) -> bool:
        """是否市价单"""
        return self.type == OrderType.MARKET

    def is_limit_order(self) -> bool:
        """是否限价单"""
        return self.type == OrderType.LIMIT

    def is_stop_order(self) -> bool:
        """是否止损单"""
        return self.type in [OrderType.STOP_MARKET, OrderType.STOP_LIMIT]

    def is_filled(self) -> bool:
        """是否已成交"""
        return self.status == OrderStatus.FILLED

    def is_canceled(self) -> bool:
        """是否已取消"""
        return self.status == OrderStatus.CANCELED

    def is_active(self) -> bool:
        """是否活跃（未成交且未取消）"""
        return self.status in [OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]

    def get_remaining_quantity(self) -> Decimal:
        """获取剩余数量"""
        return self.quantity - self.filled_quantity

    def get_fill_rate(self) -> Decimal:
        """获取成交比例"""
        if self.quantity <= 0:
            return Decimal("0")
        return self.filled_quantity / self.quantity

    def update_status(self, new_status: OrderStatus):
        """
        更新订单状态

        Args:
            new_status: 新状态
        """
        self.status = new_status
        self.updated_at = datetime.now()

    def update_fill(self, filled_quantity: Decimal, avg_price: Decimal):
        """
        更新成交信息

        Args:
            filled_quantity: 已成交数量
            avg_price: 成交均价
        """
        self.filled_quantity = filled_quantity
        self.avg_price = avg_price

        # 更新状态
        if filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        elif filled_quantity > 0:
            self.status = OrderStatus.PARTIALLY_FILLED

        self.updated_at = datetime.now()


# 快捷创建函数
def market_order(symbol: str, side: str, quantity: Decimal, **kwargs) -> Order:
    """创建市价单"""
    return Order(
        symbol=symbol, side=OrderSide(side), type=OrderType.MARKET, quantity=quantity, **kwargs
    )


def limit_order(symbol: str, side: str, quantity: Decimal, price: Decimal, **kwargs) -> Order:
    """创建限价单"""
    return Order(
        symbol=symbol,
        side=OrderSide(side),
        type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        **kwargs,
    )


def stop_order(symbol: str, side: str, quantity: Decimal, stop_price: Decimal, **kwargs) -> Order:
    """创建止损单"""
    return Order(
        symbol=symbol,
        side=OrderSide(side),
        type=OrderType.STOP_MARKET,
        quantity=quantity,
        stop_price=stop_price,
        **kwargs,
    )
