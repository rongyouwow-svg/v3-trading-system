#!/usr/bin/env python3
"""
策略引擎接口定义

所有策略引擎实现必须实现此接口。
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from modules.models.strategy import Strategy
from modules.utils.result import Result


class IStrategyEngine(ABC):
    """
    策略引擎接口 - 必须实现

    实现此接口的类必须实现所有抽象方法。
    """

    @abstractmethod
    def start_strategy(self, symbol: str, strategy_id: str, **kwargs) -> Result:
        """
        启动策略

        Args:
            symbol (str): 交易对
            strategy_id (str): 策略 ID
            **kwargs: 策略参数（leverage, amount 等）

        Returns:
            Result: 操作结果
        """
        pass

    @abstractmethod
    def stop_strategy(self, symbol: str) -> Result:
        """
        停止策略

        Args:
            symbol (str): 交易对

        Returns:
            Result: 操作结果
        """
        pass

    @abstractmethod
    def get_active_strategies(self) -> List[Strategy]:
        """
        获取活跃策略列表

        Returns:
            List[Strategy]: 策略列表
        """
        pass

    @abstractmethod
    def get_strategy_status(self, symbol: str) -> Optional[Strategy]:
        """
        获取策略状态

        Args:
            symbol (str): 交易对

        Returns:
            Optional[Strategy]: 策略状态，不存在返回 None
        """
        pass

    @abstractmethod
    def reload_strategies(self) -> Result:
        """
        重新加载策略（热插拔）

        Returns:
            Result: 操作结果
        """
        pass
