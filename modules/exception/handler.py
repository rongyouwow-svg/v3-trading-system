#!/usr/bin/env python3
"""
⚠️ 异常处理引擎

职责:
    - 异常分类
    - 重试机制
    - 恢复策略
"""

import logging
import time
from functools import wraps
from typing import Callable, Optional, Dict, Any

logger = logging.getLogger(__name__)


class TradingException(Exception):
    """交易异常基类"""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.retryable = retryable


class NetworkException(TradingException):
    """网络异常（可重试）"""
    def __init__(self, message: str = "网络错误"):
        super().__init__(message, "NETWORK_ERROR", retryable=True)


class OrderException(TradingException):
    """订单异常"""
    def __init__(self, message: str, error_code: str = "ORDER_ERROR"):
        super().__init__(message, error_code, retryable=False)


class InsufficientBalanceException(TradingException):
    """余额不足"""
    def __init__(self, message: str = "余额不足"):
        super().__init__(message, "INSUFFICIENT_BALANCE", retryable=False)


class RateLimitException(TradingException):
    """限流异常"""
    def __init__(self, message: str = "请求频率超限"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", retryable=True)


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避倍数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except TradingException as e:
                    if not e.retryable:
                        logger.error(f"❌ {func.__name__}: {e.error_code} - {e.message}")
                        raise
                    
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"⚠️ {func.__name__}: 重试 {attempt + 1}/{max_retries} ({wait_time:.1f}s 后)")
                        time.sleep(wait_time)
                    else:
                        last_exception = e
                        break
                except Exception as e:
                    logger.error(f"❌ {func.__name__}: 未知错误 - {str(e)}")
                    last_exception = TradingException(str(e), "UNKNOWN_ERROR", retryable=False)
                    break
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def handle_exceptions(default_return: Optional[Any] = None):
    """
    异常处理装饰器
    
    Args:
        default_return: 异常时的默认返回值
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except TradingException as e:
                logger.error(f"❌ {func.__name__}: {e.error_code} - {e.message}")
                if default_return is not None:
                    return default_return
                return {'success': False, 'error': e.message, 'error_code': e.error_code}
            except Exception as e:
                logger.error(f"❌ {func.__name__}: 未知错误 - {str(e)}")
                if default_return is not None:
                    return default_return
                return {'success': False, 'error': str(e), 'error_code': 'UNKNOWN_ERROR'}
        
        return wrapper
    return decorator
