#!/usr/bin/env python3
"""
pytest 测试配置文件

提供通用的测试夹具（fixtures）。
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock


@pytest.fixture
def sample_order():
    """示例订单"""
    from modules.models.order import Order, OrderType, OrderSide

    return Order(
        symbol="ETHUSDT", side=OrderSide.BUY, type=OrderType.MARKET, quantity=Decimal("0.1")
    )


@pytest.fixture
def sample_strategy():
    """示例策略"""
    from modules.models.strategy import Strategy

    return Strategy(
        symbol="ETHUSDT",
        strategy_id="breakout",
        strategy_name="突破策略",
        side="LONG",
        leverage=5,
        amount=Decimal("100"),
    )


@pytest.fixture
def mock_connector():
    """模拟连接器"""
    connector = Mock()
    connector.place_order.return_value = {"order_id": "123", "status": "FILLED"}
    connector.cancel_order.return_value = {"status": "CANCELED"}
    connector.get_order.return_value = {"order_id": "123", "status": "FILLED"}
    return connector


@pytest.fixture
def mock_result_success():
    """模拟成功结果"""
    from modules.utils.result import Result

    return Result.ok(data={"order_id": "123"}, message="操作成功")


@pytest.fixture
def mock_result_error():
    """模拟失败结果"""
    from modules.utils.result import Result

    return Result.fail(error_code="TEST_ERROR", message="测试错误")
