#!/usr/bin/env python3
"""
数据库模型定义

使用 SQLAlchemy ORM 定义数据表结构。
"""

from sqlalchemy import Column, Integer, String, Decimal, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class StrategyModel(Base):
    """策略表"""

    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    strategy_id = Column(String(50), nullable=False)
    strategy_name = Column(String(100))
    side = Column(String(10), nullable=False)  # LONG/SHORT
    leverage = Column(Integer, default=1)
    amount = Column(Decimal(20, 8), default=0)
    status = Column(String(20), default="running", index=True)  # running/stopped/paused
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    entry_price = Column(Decimal(20, 8))
    current_price = Column(Decimal(20, 8))
    position_size = Column(Decimal(20, 8))
    pnl = Column(Decimal(20, 8), default=0)
    pnl_pct = Column(Decimal(10, 8), default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "side": self.side,
            "leverage": self.leverage,
            "amount": str(self.amount) if self.amount else None,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "entry_price": str(self.entry_price) if self.entry_price else None,
            "current_price": str(self.current_price) if self.current_price else None,
            "position_size": str(self.position_size) if self.position_size else None,
            "pnl": str(self.pnl) if self.pnl else None,
            "pnl_pct": str(self.pnl_pct) if self.pnl_pct else None,
        }


class OrderModel(Base):
    """订单表"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY/SELL
    type = Column(String(20), nullable=False)  # MARKET/LIMIT/STOP_MARKET
    quantity = Column(Decimal(20, 8), nullable=False)
    price = Column(Decimal(20, 8))
    avg_price = Column(Decimal(20, 8))
    filled_quantity = Column(Decimal(20, 8), default=0)
    status = Column(String(20), default="PENDING", index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (Index("idx_symbol_status", "symbol", "status"),)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "side": self.side,
            "type": self.type,
            "quantity": str(self.quantity),
            "price": str(self.price) if self.price else None,
            "avg_price": str(self.avg_price) if self.avg_price else None,
            "filled_quantity": str(self.filled_quantity),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StopOrderModel(Base):
    """止损单表"""

    __tablename__ = "stop_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    algo_id = Column(String(50), unique=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    trigger_price = Column(Decimal(20, 8), nullable=False)
    quantity = Column(Decimal(20, 8), nullable=False)
    status = Column(String(20), default="WAIT_TO_TRIGGER")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    triggered_at = Column(DateTime)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "algo_id": self.algo_id,
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "side": self.side,
            "trigger_price": str(self.trigger_price),
            "quantity": str(self.quantity),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
        }


class TradeModel(Base):
    """成交表"""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(50), unique=True)
    order_id = Column(String(50), ForeignKey("orders.order_id"))
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    quantity = Column(Decimal(20, 8), nullable=False)
    price = Column(Decimal(20, 8), nullable=False)
    commission = Column(Decimal(20, 8), default=0)
    commission_asset = Column(String(20), default="USDT")
    realized_pnl = Column(Decimal(20, 8), default=0)
    trade_time = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (Index("idx_symbol_time", "symbol", "trade_time"),)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trade_id": self.trade_id,
            "order_id": self.order_id,
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": str(self.quantity),
            "price": str(self.price),
            "commission": str(self.commission),
            "commission_asset": self.commission_asset,
            "realized_pnl": str(self.realized_pnl),
            "trade_time": self.trade_time.isoformat() if self.trade_time else None,
        }


class StateSnapshotModel(Base):
    """状态快照表"""

    __tablename__ = "state_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_type = Column(String(20), nullable=False)  # strategy/order/position
    snapshot_data = Column(Text, nullable=False)  # JSON 数据
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "snapshot_type": self.snapshot_type,
            "snapshot_data": self.snapshot_data,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
