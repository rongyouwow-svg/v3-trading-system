#!/usr/bin/env python3
"""
统一返回结果模块

所有模块必须使用 Result 类返回结果，禁止直接返回字典。

用法:
    from modules.utils.result import Result, StatusCode

    # 成功
    return Result.ok(data={'order_id': '123'}, message="订单已创建")

    # 失败
    return Result.fail(error_code="ORDER_CREATE_FAILED", message=str(e))
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class StatusCode(Enum):
    """状态码"""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Result:
    """
    统一返回结果 - 所有模块必须使用

    Attributes:
        code: 状态码（SUCCESS/ERROR/WARNING）
        message: 消息描述
        data: 返回数据（可选）
        error_code: 错误码（失败时必填）
    """

    code: StatusCode
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None

    def to_dict(self) -> Dict:
        """
        转换为字典（用于 JSON 序列化）

        Returns:
            Dict: 字典格式的返回结果
        """
        result = {
            "code": self.code.value,
            "message": self.message,
            "timestamp": datetime.now().isoformat(),
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error_code is not None:
            result["error_code"] = self.error_code
        return result

    @classmethod
    def ok(cls, data: Dict = None, message: str = "操作成功") -> "Result":
        """
        创建成功结果

        Args:
            data: 返回数据
            message: 成功消息

        Returns:
            Result: 成功结果
        """
        return cls(code=StatusCode.SUCCESS, message=message, data=data)

    @classmethod
    def fail(cls, error_code: str, message: str, data: Dict = None) -> "Result":
        """
        创建失败结果

        Args:
            error_code: 错误码（如 ORDER_CREATE_FAILED）
            message: 错误消息
            data: 附加数据（可选）

        Returns:
            Result: 失败结果
        """
        return cls(code=StatusCode.ERROR, message=message, data=data, error_code=error_code)

    @classmethod
    def warning(cls, message: str, data: Dict = None) -> "Result":
        """
        创建警告结果

        Args:
            message: 警告消息
            data: 附加数据（可选）

        Returns:
            Result: 警告结果
        """
        return cls(code=StatusCode.WARNING, message=message, data=data)

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.code == StatusCode.SUCCESS

    @property
    def is_error(self) -> bool:
        """是否错误"""
        return self.code == StatusCode.ERROR

    @property
    def is_warning(self) -> bool:
        """是否警告"""
        return self.code == StatusCode.WARNING


# 快捷函数
def ok(data: Dict = None, message: str = "操作成功") -> Result:
    """快捷创建成功结果"""
    return Result.ok(data=data, message=message)


def fail(error_code: str, message: str, data: Dict = None) -> Result:
    """快捷创建失败结果"""
    return Result.fail(error_code=error_code, message=message, data=data)


def warning(message: str, data: Dict = None) -> Result:
    """快捷创建警告结果"""
    return Result.warning(message=message, data=data)
