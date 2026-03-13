#!/usr/bin/env python3
"""
装饰器模块

提供常用的装饰器：异常处理、重试、日志等。

用法:
    from modules.utils.decorators import handle_exceptions, retry_on_exception

    @handle_exceptions()
    def create_order(...):
        pass

    @retry_on_exception(max_retries=3)
    def place_order(...):
        pass
"""

from functools import wraps
from typing import Any, Callable, Optional
import traceback
import logging
import time

from modules.utils.result import Result
from modules.utils.exceptions import NetworkException, TradingException

# 获取日志对象
logger = logging.getLogger(__name__)


def handle_exceptions(default_return: Optional[Any] = None):
    """
    异常处理装饰器 - 所有对外函数必须使用

    功能:
        - 自动捕获所有异常
        - 记录详细日志
        - 返回统一格式的错误结果

    用法:
        @handle_exceptions()
        def create_order(...):
            pass

        @handle_exceptions(default_return=Result.fail("DEFAULT", "默认返回"))
        def get_price(...):
            pass

    Args:
        default_return: 异常时的默认返回值（可选）

    Returns:
        Callable: 装饰器
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except TradingException as e:
                # 业务异常
                logger.error(
                    f"{func.__name__} 业务异常：{e.error_code} - {e.message}", exc_info=True
                )
                return Result.fail(error_code=e.error_code, message=e.message)
            except Exception as e:
                # 系统异常
                error_msg = f"{func.__name__} 异常：{str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)

                if default_return is not None:
                    return default_return
                return Result.fail(
                    error_code="INTERNAL_ERROR", message=f"{func.__name__} 执行失败：{str(e)}"
                )

        return wrapper

    return decorator


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器 - 用于网络请求等可重试操作

    功能:
        - 自动重试 NetworkException
        - 指数退避策略
        - 记录重试日志

    用法:
        @retry_on_exception(max_retries=3, delay=1.0)
        def place_order(...):
            pass

        @retry_on_exception(max_retries=5, delay=0.5, backoff=3.0)
        def get_ticker(...):
            pass

    Args:
        max_retries: 最大重试次数
        delay: 初始等待时间（秒）
        backoff: 退避倍数（每次重试等待时间 = delay * backoff^attempt）

    Returns:
        Callable: 装饰器
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except NetworkException as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff**attempt)
                        logger.warning(
                            f"{func.__name__} 重试 {attempt + 1}/{max_retries}: "
                            f"{e.message} (等待 {wait_time:.1f}秒)"
                        )
                        time.sleep(wait_time)
                        continue
                    break
                except TradingException:
                    # 业务异常不重试
                    raise
                except Exception as e:
                    # 其他异常不重试
                    logger.error(f"{func.__name__} 异常：{str(e)}")
                    raise

            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def log_execution(log_level: int = logging.INFO):
    """
    执行日志装饰器 - 记录函数执行信息

    功能:
        - 记录函数调用
        - 记录执行时间
        - 记录返回结果

    用法:
        @log_execution()
        def create_order(...):
            pass

        @log_execution(log_level=logging.DEBUG)
        def get_price(...):
            pass

    Args:
        log_level: 日志级别

    Returns:
        Callable: 装饰器
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            logger.log(log_level, f"开始执行：{func.__name__}")

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.log(log_level, f"执行完成：{func.__name__} (耗时 {elapsed:.3f}秒)")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"执行失败：{func.__name__} (耗时 {elapsed:.3f}秒): {str(e)}")
                raise

        return wrapper

    return decorator


def validate_params(validator_func: Callable):
    """
    参数验证装饰器 - 在执行前验证参数

    用法:
        def validate_order_params(symbol, quantity):
            if not symbol:
                raise ValueError("symbol 不能为空")
            if quantity <= 0:
                raise ValueError("数量必须大于 0")

        @validate_params(validate_order_params)
        def create_order(symbol, quantity):
            pass

    Args:
        validator_func: 验证函数

    Returns:
        Callable: 装饰器
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 调用验证函数
            try:
                validator_func(*args, **kwargs)
            except ValueError as e:
                return Result.fail(error_code="INVALID_PARAMS", message=str(e))

            return func(*args, **kwargs)

        return wrapper

    return decorator


def cache_result(ttl_seconds: int = 60):
    """
    缓存装饰器 - 缓存函数返回结果

    功能:
        - 缓存返回结果
        - 自动过期

    用法:
        @cache_result(ttl_seconds=60)
        def get_price(symbol):
            pass

    Args:
        ttl_seconds: 缓存时间（秒）

    Returns:
        Callable: 装饰器
    """

    def decorator(func: Callable):
        cache = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            key = str(args) + str(kwargs)

            # 检查缓存
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    return result
                del cache[key]

            # 执行函数
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result

        return wrapper

    return decorator
