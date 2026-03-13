#!/usr/bin/env python3
"""
测试异常类
"""

import pytest
from modules.utils.exceptions import (
    TradingException,
    InsufficientBalanceException,
    NetworkException,
    OrderCreateException,
    OrderCancelException,
    RateLimitException,
)


class TestExceptions:
    """测试异常类"""

    def test_trading_exception_basic(self):
        """测试基础异常"""
        exc = TradingException("测试错误", "TEST_ERROR")

        assert exc.message == "测试错误"
        assert exc.error_code == "TEST_ERROR"
        assert exc.retryable is False
        assert str(exc) == "TEST_ERROR: 测试错误"

    def test_trading_exception_retryable(self):
        """测试可重试异常"""
        exc = TradingException("网络错误", "NETWORK_ERROR", retryable=True)

        assert exc.retryable is True

    def test_insufficient_balance_exception(self):
        """测试余额不足异常"""
        exc = InsufficientBalanceException("USDT 余额不足")

        assert exc.error_code == "INSUFFICIENT_BALANCE"
        assert exc.retryable is False
        assert "USDT 余额不足" in str(exc)

    def test_network_exception(self):
        """测试网络异常"""
        exc = NetworkException("连接超时")

        assert exc.error_code == "NETWORK_ERROR"
        assert exc.retryable is True

    def test_order_create_exception(self):
        """测试订单创建异常"""
        exc = OrderCreateException("价格精度错误")

        assert exc.error_code == "ORDER_CREATE_FAILED"
        assert exc.retryable is False

    def test_order_cancel_exception(self):
        """测试订单取消异常"""
        exc = OrderCancelException("订单已成交")

        assert exc.error_code == "ORDER_CANCEL_FAILED"
        assert exc.retryable is False

    def test_rate_limit_exception(self):
        """测试限流异常"""
        exc = RateLimitException("API 请求超限")

        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.retryable is True


class TestExceptionHandling:
    """测试异常处理"""

    def test_raise_and_catch(self):
        """测试抛出和捕获异常"""
        with pytest.raises(InsufficientBalanceException) as exc_info:
            raise InsufficientBalanceException("测试余额不足")

        assert exc_info.value.error_code == "INSUFFICIENT_BALANCE"

    def test_retryable_exception_check(self):
        """测试可重试异常判断"""
        exc1 = NetworkException("超时")
        exc2 = OrderCreateException("参数错误")

        assert exc1.retryable is True
        assert exc2.retryable is False
