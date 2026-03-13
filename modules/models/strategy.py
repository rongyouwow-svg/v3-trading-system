#!/usr/bin/env python3
"""
策略数据对象

所有模块必须使用 Strategy 类传递策略数据。

用法:
    from decimal import Decimal
    from modules.models.strategy import Strategy

    strategy = Strategy(
        symbol='ETHUSDT',
        strategy_id='breakout',
        strategy_name='突破策略',
        side='LONG',
        leverage=5,
        amount=Decimal('100')
    )
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict


@dataclass
class Strategy:
    """
    策略数据对象 - 所有模块必须使用

    Attributes:
        symbol: 交易对（如 ETHUSDT）
        strategy_id: 策略 ID（如 breakout）
        strategy_name: 策略名称（如 突破策略）
        side: 方向（LONG/SHORT）
        leverage: 杠杆倍数
        amount: 保证金（USDT）
        status: 状态（running/stopped/paused）
        start_time: 启动时间
        stop_time: 停止时间（可选）
        entry_price: 入场价
        current_price: 当前价
        position_size: 持仓数量
        pnl: 盈亏（USDT）
        pnl_pct: 盈亏百分比
        is_hot_plug: 是否热插拔策略
        params: 策略参数
    """

    symbol: str
    strategy_id: str
    strategy_name: str
    side: str  # LONG/SHORT
    leverage: int
    amount: Decimal
    status: str = "running"  # running/stopped/paused
    start_time: datetime = field(default_factory=datetime.now)
    stop_time: Optional[datetime] = None
    entry_price: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    position_size: Optional[Decimal] = None
    pnl: Decimal = Decimal("0")
    pnl_pct: Decimal = Decimal("0")
    is_hot_plug: bool = True
    params: Dict = field(default_factory=dict)

    def __post_init__(self):
        """初始化后验证"""
        # 验证杠杆范围
        if not (1 <= self.leverage <= 125):
            raise ValueError("杠杆必须在 1-125 之间")

        # 验证保证金
        if self.amount <= 0:
            raise ValueError("保证金必须大于 0")

        # 验证方向
        if self.side not in ["LONG", "SHORT"]:
            raise ValueError("方向必须是 LONG 或 SHORT")

        # 设置启动时间
        if self.start_time is None:
            self.start_time = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "side": self.side,
            "leverage": self.leverage,
            "amount": str(self.amount),
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "entry_price": str(self.entry_price) if self.entry_price else None,
            "current_price": str(self.current_price) if self.current_price else None,
            "position_size": str(self.position_size) if self.position_size else None,
            "pnl": str(self.pnl),
            "pnl_pct": str(self.pnl_pct),
            "is_hot_plug": self.is_hot_plug,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Strategy":
        """从字典创建"""
        return cls(
            symbol=data["symbol"],
            strategy_id=data["strategy_id"],
            strategy_name=data.get("strategy_name", data["strategy_id"]),
            side=data["side"],
            leverage=data.get("leverage", 1),
            amount=Decimal(data["amount"]),
            status=data.get("status", "running"),
            start_time=(
                datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None
            ),
            stop_time=datetime.fromisoformat(data["stop_time"]) if data.get("stop_time") else None,
            entry_price=Decimal(data["entry_price"]) if data.get("entry_price") else None,
            current_price=Decimal(data["current_price"]) if data.get("current_price") else None,
            position_size=Decimal(data["position_size"]) if data.get("position_size") else None,
            pnl=Decimal(data.get("pnl", "0")),
            pnl_pct=Decimal(data.get("pnl_pct", "0")),
            is_hot_plug=data.get("is_hot_plug", True),
            params=data.get("params", {}),
        )

    def is_running(self) -> bool:
        """是否运行中"""
        return self.status == "running"

    def is_stopped(self) -> bool:
        """是否已停止"""
        return self.status == "stopped"

    def is_paused(self) -> bool:
        """是否暂停"""
        return self.status == "paused"

    def stop(self):
        """停止策略"""
        self.status = "stopped"
        self.stop_time = datetime.now()

    def pause(self):
        """暂停策略"""
        self.status = "paused"

    def resume(self):
        """恢复策略"""
        self.status = "running"

    def update_pnl(self, current_price: Decimal):
        """
        更新盈亏

        Args:
            current_price: 当前价格
        """
        self.current_price = current_price

        if self.entry_price and self.position_size:
            if self.side == "LONG":
                self.pnl = (current_price - self.entry_price) * self.position_size
            else:  # SHORT
                self.pnl = (self.entry_price - current_price) * self.position_size

            if self.entry_price > 0:
                self.pnl_pct = (current_price - self.entry_price) / self.entry_price
                if self.side == "SHORT":
                    self.pnl_pct = -self.pnl_pct

    def get_uptime(self) -> float:
        """
        获取运行时长（秒）

        Returns:
            float: 运行时长（秒）
        """
        if self.stop_time:
            return (self.stop_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
