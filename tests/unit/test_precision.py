#!/usr/bin/env python3
"""
测试精度处理工具
"""

from decimal import Decimal
from modules.utils.precision import PrecisionUtils


class TestPrecisionUtils:
    """测试精度处理工具"""

    def test_get_step_size(self):
        """测试获取数量精度"""
        assert PrecisionUtils.get_step_size("ETHUSDT") == Decimal("0.001")
        assert PrecisionUtils.get_step_size("BTCUSDT") == Decimal("0.001")
        assert PrecisionUtils.get_step_size("AVAXUSDT") == Decimal("0.1")
        assert PrecisionUtils.get_step_size("UNKNOWN") == Decimal("0.001")  # 默认值

    def test_get_tick_size(self):
        """测试获取价格精度"""
        assert PrecisionUtils.get_tick_size("ETHUSDT") == Decimal("0.01")
        assert PrecisionUtils.get_tick_size("BTCUSDT") == Decimal("0.1")
        assert PrecisionUtils.get_tick_size("AVAXUSDT") == Decimal("0.001")

    def test_normalize_quantity(self):
        """测试标准化数量"""
        quantity = Decimal("0.123456789")
        normalized = PrecisionUtils.normalize_quantity("ETHUSDT", quantity)
        assert normalized == Decimal("0.123")

        quantity2 = Decimal("10.987654")
        normalized2 = PrecisionUtils.normalize_quantity("AVAXUSDT", quantity2)
        assert normalized2 == Decimal("10.9")

    def test_normalize_price(self):
        """测试标准化价格"""
        price = Decimal("2050.567")
        normalized = PrecisionUtils.normalize_price("ETHUSDT", price)
        assert normalized == Decimal("2050.56")

        price2 = Decimal("70000.123")
        normalized2 = PrecisionUtils.normalize_price("BTCUSDT", price2)
        assert normalized2 == Decimal("70000.1")

    def test_validate_quantity_valid(self):
        """测试验证有效数量"""
        is_valid, msg = PrecisionUtils.validate_quantity("ETHUSDT", Decimal("0.1"))
        assert is_valid is True
        assert msg == ""

    def test_validate_quantity_invalid_negative(self):
        """测试验证无效数量（负数）"""
        is_valid, msg = PrecisionUtils.validate_quantity("ETHUSDT", Decimal("-0.1"))
        assert is_valid is False
        assert "必须大于 0" in msg

    def test_validate_quantity_invalid_precision(self):
        """测试验证无效数量（精度错误）"""
        is_valid, msg = PrecisionUtils.validate_quantity("ETHUSDT", Decimal("0.123456789"))
        assert is_valid is False
        assert "精度错误" in msg

    def test_validate_price_valid(self):
        """测试验证有效价格"""
        is_valid, msg = PrecisionUtils.validate_quantity("ETHUSDT", Decimal("2000.50"))
        assert is_valid is True

    def test_calculate_position_size(self):
        """测试计算仓位大小"""
        quantity = PrecisionUtils.calculate_position_size(
            Decimal("100"), Decimal("2000"), 5  # 保证金  # 价格  # 杠杆
        )
        assert quantity == Decimal("0.25")

    def test_calculate_pnl_long(self):
        """测试计算盈亏（做多）"""
        pnl = PrecisionUtils.calculate_pnl(
            Decimal("2000"),  # 入场价
            Decimal("2100"),  # 出场价
            Decimal("0.1"),  # 数量
            "LONG",  # 方向
        )
        assert pnl == Decimal("10.0")

    def test_calculate_pnl_short(self):
        """测试计算盈亏（做空）"""
        pnl = PrecisionUtils.calculate_pnl(
            Decimal("2100"),  # 入场价
            Decimal("2000"),  # 出场价
            Decimal("0.1"),  # 数量
            "SHORT",  # 方向
        )
        assert pnl == Decimal("10.0")

    def test_calculate_pnl_pct(self):
        """测试计算盈亏百分比"""
        pnl_pct = PrecisionUtils.calculate_pnl_pct(
            Decimal("2000"), Decimal("2100"), "LONG"  # 入场价  # 出场价
        )
        assert pnl_pct == Decimal("0.05")  # 5%
