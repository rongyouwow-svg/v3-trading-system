#!/usr/bin/env python3
"""
异常处理模块

定义所有业务异常类，支持自动重试标记。

用法:
    from modules.utils.exceptions import InsufficientBalanceException, OrderCreateException

    try:
        # 业务逻辑
        if balance < amount:
            raise InsufficientBalanceException("余额不足")
    except TradingException as e:
        print(f"业务异常：{e.error_code} - {e.message}")
"""




class TradingException(Exception):
    """
    交易异常基类

    Attributes:
        message: 错误消息
        error_code: 错误码
        retryable: 是否可重试
    """

    def __init__(self, message: str, error_code: str, retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.retryable = retryable

    def __str__(self) -> str:
        return f"{self.error_code}: {self.message}"


class ExchangeException(TradingException):
    """
    交易所异常

    场景:
        - API 返回错误
        - 交易所维护
        - 交易对不存在
    """

    pass


class InsufficientBalanceException(TradingException):
    """
    余额不足

    场景:
        - 开仓时保证金不足
        - 加仓时余额不足
        - 手续费不足

    处理:
        - 不可重试
        - 需要用户充值或减少仓位
    """

    def __init__(self, message: str = "余额不足"):
        super().__init__(message, "INSUFFICIENT_BALANCE", retryable=False)


class NetworkException(TradingException):
    """
    网络异常（可重试）

    场景:
        - 网络超时
        - 连接断开
        - DNS 解析失败

    处理:
        - 可重试
        - 使用指数退避策略
    """

    def __init__(self, message: str = "网络错误"):
        super().__init__(message, "NETWORK_ERROR", retryable=True)


class OrderException(TradingException):
    """订单异常基类"""

    pass


class OrderCreateException(OrderException):
    """
    订单创建失败

    场景:
        - 参数错误
        - 价格精度错误
        - 数量精度错误
        - 超出限制

    处理:
        - 不可重试
        - 需要修正参数
    """

    def __init__(self, message: str):
        super().__init__(message, "ORDER_CREATE_FAILED", retryable=False)


class OrderCancelException(OrderException):
    """
    订单取消失败

    场景:
        - 订单已成交
        - 订单不存在
        - 订单已取消

    处理:
        - 不可重试
        - 检查订单状态
    """

    def __init__(self, message: str):
        super().__init__(message, "ORDER_CANCEL_FAILED", retryable=False)


class OrderNotFoundException(OrderException):
    """订单不存在"""

    def __init__(self, order_id: str):
        super().__init__(f"订单不存在：{order_id}", "ORDER_NOT_FOUND", retryable=False)


class StrategyException(TradingException):
    """策略异常基类"""

    pass


class StrategyNotFoundException(StrategyException):
    """策略不存在"""

    def __init__(self, strategy_id: str):
        super().__init__(f"策略不存在：{strategy_id}", "STRATEGY_NOT_FOUND", retryable=False)


class StrategyExistsException(StrategyException):
    """策略已存在"""

    def __init__(self, symbol: str):
        super().__init__(f"{symbol} 已有活跃策略", "STRATEGY_EXISTS", retryable=False)


class DataException(TradingException):
    """数据异常"""

    pass


class DataNotFoundException(DataException):
    """数据不存在"""

    def __init__(self, data_type: str, key: str):
        super().__init__(f"{data_type} 不存在：{key}", "DATA_NOT_FOUND", retryable=False)


class ValidationException(TradingException):
    """验证异常"""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", retryable=False)


class ConfigException(TradingException):
    """配置异常"""

    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR", retryable=False)


class DatabaseException(TradingException):
    """数据库异常"""

    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR", retryable=True)


class RateLimitException(TradingException):
    """
    限流异常

    场景:
        - API 请求超限
        - 订单频率超限

    处理:
        - 可重试
        - 等待后重试
    """

    def __init__(self, message: str = "请求频率超限"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", retryable=True)
