#!/usr/bin/env python3
"""
精度处理模块

所有金额和数量必须使用 Decimal，禁止使用 float。

用法:
    from decimal import Decimal
    from modules.utils.precision import PrecisionUtils

    # 标准化数量
    quantity = Decimal('0.123456789')
    normalized = PrecisionUtils.normalize_quantity('ETHUSDT', quantity)

    # 验证数量
    is_valid, error_msg = PrecisionUtils.validate_quantity('ETHUSDT', quantity)
"""

from decimal import Decimal, ROUND_DOWN
from typing import Tuple, Dict


class PrecisionUtils:
    """
    精度处理工具 - 所有模块必须使用

    核心功能:
        - 获取精度信息（stepSize/tickSize）
        - 标准化数量/价格
        - 验证数量/价格合法性
    """

    # 数量精度映射（实际应从交易所动态获取）
    STEP_SIZE_MAP: Dict[str, Decimal] = {
        "ETHUSDT": Decimal("0.001"),
        "BTCUSDT": Decimal("0.001"),
        "AVAXUSDT": Decimal("0.1"),
        "LINKUSDT": Decimal("0.1"),
        "UNIUSDT": Decimal("0.1"),
    }

    # 价格精度映射
    TICK_SIZE_MAP: Dict[str, Decimal] = {
        "ETHUSDT": Decimal("0.01"),
        "BTCUSDT": Decimal("0.1"),
        "AVAXUSDT": Decimal("0.001"),
        "LINKUSDT": Decimal("0.001"),
        "UNIUSDT": Decimal("0.001"),
    }

    @classmethod
    def get_step_size(cls, symbol: str) -> Decimal:
        """
        获取数量精度

        Args:
            symbol: 交易对（如 ETHUSDT）

        Returns:
            Decimal: 数量精度（stepSize）
        """
        return cls.STEP_SIZE_MAP.get(symbol, Decimal("0.001"))

    @classmethod
    def get_tick_size(cls, symbol: str) -> Decimal:
        """
        获取价格精度

        Args:
            symbol: 交易对（如 ETHUSDT）

        Returns:
            Decimal: 价格精度（tickSize）
        """
        return cls.TICK_SIZE_MAP.get(symbol, Decimal("0.01"))

    @classmethod
    def normalize_quantity(cls, symbol: str, quantity: Decimal) -> Decimal:
        """
        标准化数量（向下取整到 stepSize）

        Args:
            symbol: 交易对
            quantity: 原始数量

        Returns:
            Decimal: 标准化后的数量

        Example:
            >>> PrecisionUtils.normalize_quantity('ETHUSDT', Decimal('0.123456789'))
            Decimal('0.123')
        """
        step_size = cls.get_step_size(symbol)
        return quantity.quantize(step_size, rounding=ROUND_DOWN)

    @classmethod
    def normalize_price(cls, symbol: str, price: Decimal) -> Decimal:
        """
        标准化价格（向下取整到 tickSize）

        Args:
            symbol: 交易对
            price: 原始价格

        Returns:
            Decimal: 标准化后的价格

        Example:
            >>> PrecisionUtils.normalize_price('ETHUSDT', Decimal('2050.567'))
            Decimal('2050.56')
        """
        tick_size = cls.get_tick_size(symbol)
        return price.quantize(tick_size, rounding=ROUND_DOWN)

    @classmethod
    def validate_quantity(cls, symbol: str, quantity: Decimal) -> Tuple[bool, str]:
        """
        验证数量是否合法

        Args:
            symbol: 交易对
            quantity: 数量

        Returns:
            Tuple[bool, str]: (是否合法，错误消息)

        Example:
            >>> is_valid, msg = PrecisionUtils.validate_quantity('ETHUSDT', Decimal('0.1'))
            >>> if not is_valid:
            ...     print(f"错误：{msg}")
        """
        step_size = cls.get_step_size(symbol)

        # 检查是否大于 0
        if quantity <= 0:
            return False, "数量必须大于 0"

        # 检查是否小于最小精度
        if quantity < step_size:
            return False, f"数量不能小于 {step_size}"

        # 检查是否符合精度
        normalized = cls.normalize_quantity(symbol, quantity)
        if normalized != quantity:
            return False, f"数量精度错误，应该是 {normalized}（当前：{quantity}）"

        return True, ""

    @classmethod
    def validate_price(cls, symbol: str, price: Decimal) -> Tuple[bool, str]:
        """
        验证价格是否合法

        Args:
            symbol: 交易对
            price: 价格

        Returns:
            Tuple[bool, str]: (是否合法，错误消息)
        """
        tick_size = cls.get_tick_size(symbol)

        # 检查是否大于 0
        if price <= 0:
            return False, "价格必须大于 0"

        # 检查是否符合精度
        normalized = cls.normalize_price(symbol, price)
        if normalized != price:
            return False, f"价格精度错误，应该是 {normalized}（当前：{price}）"

        return True, ""

    @classmethod
    def calculate_position_size(cls, amount: Decimal, price: Decimal, leverage: int = 1) -> Decimal:
        """
        计算仓位大小（数量）

        Args:
            amount: 保证金（USDT）
            price: 价格
            leverage: 杠杆

        Returns:
            Decimal: 仓位大小（币种数量）

        Example:
            >>> PrecisionUtils.calculate_position_size(Decimal('100'), Decimal('2000'), 5)
            Decimal('0.25')
        """
        if price <= 0:
            return Decimal("0")

        position_value = amount * leverage
        quantity = position_value / price
        return quantity

    @classmethod
    def calculate_pnl(
        cls, entry_price: Decimal, exit_price: Decimal, quantity: Decimal, side: str
    ) -> Decimal:
        """
        计算盈亏

        Args:
            entry_price: 入场价
            exit_price: 出场价
            quantity: 数量
            side: 方向（LONG/SHORT）

        Returns:
            Decimal: 盈亏（正数盈利，负数亏损）

        Example:
            >>> PrecisionUtils.calculate_pnl(Decimal('2000'), Decimal('2100'), Decimal('0.1'), 'LONG')
            Decimal('10.0')
        """
        if side.upper() == "LONG":
            return (exit_price - entry_price) * quantity
        else:  # SHORT
            return (entry_price - exit_price) * quantity

    @classmethod
    def calculate_pnl_pct(cls, entry_price: Decimal, exit_price: Decimal, side: str) -> Decimal:
        """
        计算盈亏百分比

        Args:
            entry_price: 入场价
            exit_price: 出场价
            side: 方向（LONG/SHORT）

        Returns:
            Decimal: 盈亏百分比（如 0.05 表示 5%）
        """
        if entry_price <= 0:
            return Decimal("0")

        if side.upper() == "LONG":
            return (exit_price - entry_price) / entry_price
        else:  # SHORT
            return (entry_price - exit_price) / entry_price
