#!/usr/bin/env python3
"""
日志模块

提供统一的 JSON 格式日志配置。

用法:
    from modules.utils.logger import setup_logger

    logger = setup_logger('strategy_engine', log_file='logs/strategy.log')
    logger.info("策略已启动", extra={'extra_data': {'symbol': 'ETHUSDT'}})
"""

import logging
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any


class JSONFormatter(logging.Formatter):
    """
    JSON 格式日志 - 所有模块必须使用

    日志格式:
        {
            "timestamp": "2026-03-13T14:00:00",
            "level": "INFO",
            "module": "strategy_engine",
            "function": "start_strategy",
            "line": 123,
            "message": "策略已启动",
            "data": {"symbol": "ETHUSDT"}
        }
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外数据
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False, indent=2)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True,
    log_format: str = "json",
) -> logging.Logger:
    """
    设置日志

    Args:
        name: 日志名称（通常是模块名）
        level: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
        log_file: 日志文件路径（可选）
        console_output: 是否输出到控制台
        log_format: 日志格式（json/text）

    Returns:
        logging.Logger: 配置好的日志对象

    Example:
        >>> logger = setup_logger('strategy_engine', log_file='logs/strategy.log')
        >>> logger.info("策略已启动", extra={'extra_data': {'symbol': 'ETHUSDT'}})
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除已有处理器
    logger.handlers.clear()

    # 选择格式化器
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 文件处理器
    if log_file:
        # 确保目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 防止日志传播到父日志
    logger.propagate = False

    return logger


# 快捷函数
def get_logger(name: str) -> logging.Logger:
    """
    获取日志对象（使用默认配置）

    Args:
        name: 日志名称

    Returns:
        logging.Logger: 日志对象
    """
    return setup_logger(name, console_output=True)


# 预定义的日志级别
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
