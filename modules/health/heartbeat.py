#!/usr/bin/env python3
"""
💓 心跳检测模块

功能:
    - 策略引擎定期更新心跳
    - 网关检查心跳状态
    - 检测策略是否失效
    - 健康状态监控

用法:
    from modules.health.heartbeat import HeartbeatMonitor
    
    monitor = HeartbeatMonitor()
    monitor.update_heartbeat("ETHUSDT")
    status = monitor.check_health("ETHUSDT")
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum

from modules.utils.logger import setup_logger

logger = setup_logger("heartbeat_monitor", log_file="logs/heartbeat.log")


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "HEALTHY"  # 健康
    UNHEALTHY = "UNHEALTHY"  # 不健康
    UNKNOWN = "UNKNOWN"  # 未知
    STOPPED = "STOPPED"  # 已停止


class HeartbeatMonitor:
    """
    心跳检测器
    
    核心功能:
        - 记录策略心跳时间
        - 检查策略健康状态
        - 检测超时策略
        - 提供健康报告
    """
    
    # 心跳超时阈值（秒）
    HEARTBEAT_TIMEOUT = 300  # 5 分钟
    
    def __init__(self):
        """初始化心跳检测器"""
        # 心跳记录 {symbol: last_heartbeat_time}
        self.heartbeats: Dict[str, datetime] = {}
        
        # 策略状态 {symbol: HealthStatus}
        self.statuses: Dict[str, HealthStatus] = {}
        
        # 心跳计数器 {symbol: count}
        self.counters: Dict[str, int] = {}
        
        logger.info("心跳检测器初始化完成")
    
    def update_heartbeat(self, symbol: str):
        """
        更新策略心跳
        
        Args:
            symbol (str): 交易对
        
        Example:
            >>> monitor.update_heartbeat("ETHUSDT")
        """
        now = datetime.now()
        self.heartbeats[symbol] = now
        self.statuses[symbol] = HealthStatus.HEALTHY
        self.counters[symbol] = self.counters.get(symbol, 0) + 1
        
        logger.debug(f"💓 {symbol} 心跳更新 (次数:{self.counters[symbol]})")
    
    def check_health(self, symbol: str) -> HealthStatus:
        """
        检查策略健康状态
        
        Args:
            symbol (str): 交易对
        
        Returns:
            HealthStatus: 健康状态
        
        Example:
            >>> status = monitor.check_health("ETHUSDT")
            >>> if status == HealthStatus.UNHEALTHY:
            ...     print("策略可能已失效！")
        """
        if symbol not in self.heartbeats:
            self.statuses[symbol] = HealthStatus.UNKNOWN
            return HealthStatus.UNKNOWN
        
        last_beat = self.heartbeats[symbol]
        now = datetime.now()
        diff = (now - last_beat).total_seconds()
        
        if diff > self.HEARTBEAT_TIMEOUT:
            self.statuses[symbol] = HealthStatus.UNHEALTHY
            logger.warning(f"⚠️ {symbol} 心跳超时 ({diff:.0f}秒 > {self.HEARTBEAT_TIMEOUT}秒)")
        else:
            self.statuses[symbol] = HealthStatus.HEALTHY
        
        return self.statuses[symbol]
    
    def check_all_health(self) -> Dict[str, HealthStatus]:
        """
        检查所有策略健康状态
        
        Returns:
            Dict[str, HealthStatus]: 所有策略的健康状态
        """
        results = {}
        for symbol in self.heartbeats.keys():
            results[symbol] = self.check_health(symbol)
        return results
    
    def get_healthy_strategies(self) -> List[str]:
        """
        获取健康的策略列表
        
        Returns:
            List[str]: 健康的策略符号列表
        """
        healthy = []
        for symbol, status in self.check_all_health().items():
            if status == HealthStatus.HEALTHY:
                healthy.append(symbol)
        return healthy
    
    def get_unhealthy_strategies(self) -> List[str]:
        """
        获取不健康的策略列表
        
        Returns:
            List[str]: 不健康的策略符号列表
        """
        unhealthy = []
        for symbol, status in self.check_all_health().items():
            if status == HealthStatus.UNHEALTHY:
                unhealthy.append(symbol)
        return unhealthy
    
    def get_last_heartbeat(self, symbol: str) -> Optional[datetime]:
        """
        获取策略最后心跳时间
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Optional[datetime]: 最后心跳时间，不存在返回 None
        """
        return self.heartbeats.get(symbol)
    
    def get_heartbeat_age(self, symbol: str) -> Optional[float]:
        """
        获取策略心跳年龄（距现在多少秒）
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Optional[float]: 心跳年龄（秒），不存在返回 None
        """
        last_beat = self.get_last_heartbeat(symbol)
        if not last_beat:
            return None
        
        return (datetime.now() - last_beat).total_seconds()
    
    def get_health_report(self) -> Dict:
        """
        生成健康报告
        
        Returns:
            Dict: 健康报告
        """
        all_status = self.check_all_health()
        
        healthy_count = sum(1 for s in all_status.values() if s == HealthStatus.HEALTHY)
        unhealthy_count = sum(1 for s in all_status.values() if s == HealthStatus.UNHEALTHY)
        unknown_count = sum(1 for s in all_status.values() if s == HealthStatus.UNKNOWN)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_strategies": len(all_status),
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "unknown_count": unknown_count,
            "health_rate": healthy_count / len(all_status) * 100 if all_status else 0,
            "strategies": {}
        }
        
        for symbol, status in all_status.items():
            age = self.get_heartbeat_age(symbol)
            report["strategies"][symbol] = {
                "status": status.value,
                "last_heartbeat": self.get_last_heartbeat(symbol).isoformat() if self.get_last_heartbeat(symbol) else None,
                "age_seconds": age,
                "heartbeat_count": self.counters.get(symbol, 0)
            }
        
        return report
    
    def set_status(self, symbol: str, status: HealthStatus):
        """
        手动设置策略状态
        
        Args:
            symbol (str): 交易对
            status (HealthStatus): 健康状态
        """
        self.statuses[symbol] = status
        logger.info(f"📊 {symbol} 状态设置为 {status.value}")
    
    def remove_strategy(self, symbol: str):
        """
        移除策略
        
        Args:
            symbol (str): 交易对
        """
        if symbol in self.heartbeats:
            del self.heartbeats[symbol]
        if symbol in self.statuses:
            del self.statuses[symbol]
        if symbol in self.counters:
            del self.counters[symbol]
        
        logger.info(f"🗑️ 已移除策略 {symbol}")
    
    def clear(self):
        """清空所有心跳记录"""
        self.heartbeats.clear()
        self.statuses.clear()
        self.counters.clear()
        logger.info("🧹 已清空所有心跳记录")


# 全局实例
_monitor: Optional[HeartbeatMonitor] = None


def get_heartbeat_monitor() -> HeartbeatMonitor:
    """获取全局心跳检测器实例"""
    global _monitor
    if _monitor is None:
        _monitor = HeartbeatMonitor()
    return _monitor


def reset_heartbeat_monitor():
    """重置心跳检测器（测试用）"""
    global _monitor
    _monitor = None
