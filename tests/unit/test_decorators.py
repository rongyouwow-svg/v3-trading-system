#!/usr/bin/env python3
"""
测试装饰器
"""

import pytest
import time
from modules.utils.decorators import (
    handle_exceptions,
    retry_on_exception,
    log_execution,
    cache_result,
)
from modules.utils.result import Result
from modules.utils.exceptions import NetworkException


class TestHandleExceptions:
    """测试异常处理装饰器"""

    def test_success_case(self):
        """测试成功情况"""

        @handle_exceptions()
        def success_func():
            return Result.ok(data={"key": "value"})

        result = success_func()
        assert result.is_success
        assert result.data["key"] == "value"

    def test_exception_case(self):
        """测试异常情况"""

        @handle_exceptions()
        def error_func():
            raise ValueError("测试错误")

        result = error_func()
        assert result.is_error
        assert result.error_code == "INTERNAL_ERROR"

    def test_default_return(self):
        """测试默认返回值"""

        @handle_exceptions(default_return=Result.fail("DEFAULT", "默认返回"))
        def error_func_with_default():
            raise ValueError("测试错误")

        result = error_func_with_default()
        assert result.is_error
        assert result.error_code == "DEFAULT"


class TestRetryOnException:
    """测试重试装饰器"""

    def test_success_no_retry(self):
        """测试成功不需要重试"""
        call_count = 0

        @retry_on_exception(max_retries=3)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_network_exception(self):
        """测试网络异常重试"""
        call_count = 0

        @retry_on_exception(max_retries=3, delay=0.1)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkException("网络错误")
            return "success"

        result = fail_then_succeed()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted(self):
        """测试重试用尽"""
        call_count = 0

        @retry_on_exception(max_retries=2, delay=0.1)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise NetworkException("总是失败")

        with pytest.raises(NetworkException):
            always_fail()

        assert call_count == 2


class TestCacheResult:
    """测试缓存装饰器"""

    def test_cache_hit(self):
        """测试缓存命中"""
        call_count = 0

        @cache_result(ttl_seconds=60)
        def get_value(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # 第一次调用
        result1 = get_value(5)
        assert result1 == 10
        assert call_count == 1

        # 第二次调用（缓存命中）
        result2 = get_value(5)
        assert result2 == 10
        assert call_count == 1  # 不应该增加

    def test_cache_miss_different_args(self):
        """测试不同参数缓存未命中"""
        call_count = 0

        @cache_result(ttl_seconds=60)
        def get_value(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = get_value(5)
        result2 = get_value(10)

        assert result1 == 10
        assert result2 == 20
        assert call_count == 2  # 两次调用


class TestLogExecution:
    """测试日志装饰器"""

    def test_log_execution(self):
        """测试执行日志"""

        @log_execution()
        def test_func():
            time.sleep(0.1)
            return "done"

        result = test_func()
        assert result == "done"
