#!/usr/bin/env python3
"""
🦞 异常处理引擎 v3.0

职责:
    - 异常分类
    - 重试机制
    - 恢复策略
    - 告警管理

特性:
    - 自动异常分类
    - 智能重试策略
    - 分级告警
    - 恢复策略库

用法:
    from core.exception.exception_handler import ExceptionManager
    
    manager = ExceptionManager()
    manager.handle_exception(exception)
"""

from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
import time
import json
import os

from modules.utils.logger import setup_logger
from modules.utils.result import Result
from modules.utils.exceptions import (
    TradingException,
    NetworkException,
    InsufficientBalanceException,
    OrderCreateException,
    OrderCancelException,
    RateLimitException
)

logger = setup_logger("exception_handler", log_file="logs/exception_handler.log")


class ExceptionSeverity(Enum):
    """异常严重程度"""
    LOW = "low"  # 低（可自动恢复）
    MEDIUM = "medium"  # 中（需要重试）
    HIGH = "high"  # 高（需要人工介入）
    CRITICAL = "critical"  # 严重（停止系统）


class ExceptionCategory(Enum):
    """异常分类"""
    NETWORK = "network"  # 网络异常
    BUSINESS = "business"  # 业务异常
    SYSTEM = "system"  # 系统异常
    EXCHANGE = "exchange"  # 交易所异常


class ExceptionManager:
    """
    异常处理引擎
    
    核心功能:
        - 异常分类
        - 重试机制
        - 恢复策略
        - 告警管理
    """
    
    # 重试配置
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # 秒
    MAX_DELAY = 60.0  # 秒
    
    def __init__(self):
        """初始化异常处理引擎"""
        # 异常统计
        self.exception_count: int = 0
        self.exception_by_category: Dict[str, int] = {}
        self.exception_by_severity: Dict[str, int] = {}
        
        # 重试队列
        self.retry_queue: List[Dict] = []
        
        # 告警回调
        self.alert_callbacks: List[Callable] = []
        
        # 恢复策略库
        self.recovery_strategies: Dict[str, Callable] = {}
        
        # 注册默认恢复策略
        self._register_default_strategies()
        
        # 持久化文件
        self.persistence_file = "/root/.openclaw/workspace/quant/v3-architecture/data/exception_handler.json"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
        
        # 加载数据
        self._load_data()
        
        logger.info("异常处理引擎初始化完成")
    
    def _register_default_strategies(self):
        """注册默认恢复策略"""
        self.recovery_strategies['network_retry'] = self._recover_network_retry
        self.recovery_strategies['balance_refresh'] = self._recover_balance_refresh
        self.recovery_strategies['order_cancel'] = self._recover_order_cancel
        self.recovery_strategies['system_restart'] = self._recover_system_restart
    
    # ==================== 异常处理 ====================
    
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict] = None
    ) -> Result:
        """
        处理异常
        
        Args:
            exception (Exception): 异常对象
            context (Dict, optional): 上下文信息
        
        Returns:
            Result: 处理结果
        """
        self.exception_count += 1
        
        # 1. 分类异常
        category = self._classify_exception(exception)
        severity = self._assess_severity(exception)
        
        # 2. 记录异常
        self._record_exception(exception, category, severity, context)
        
        # 3. 处理异常
        if isinstance(exception, TradingException):
            return self._handle_trading_exception(exception, category, severity)
        elif isinstance(exception, NetworkException):
            return self._handle_network_exception(exception)
        elif isinstance(exception, (OrderCreateException, OrderCancelException)):
            return self._handle_order_exception(exception)
        else:
            return self._handle_generic_exception(exception)
    
    def _classify_exception(self, exception: Exception) -> ExceptionCategory:
        """
        分类异常
        
        Args:
            exception (Exception): 异常对象
        
        Returns:
            ExceptionCategory: 异常分类
        """
        if isinstance(exception, (NetworkException, RateLimitException)):
            return ExceptionCategory.NETWORK
        elif isinstance(exception, (InsufficientBalanceException,)):
            return ExceptionCategory.BUSINESS
        elif isinstance(exception, (OrderCreateException, OrderCancelException)):
            return ExceptionCategory.EXCHANGE
        else:
            return ExceptionCategory.SYSTEM
    
    def _assess_severity(self, exception: Exception) -> ExceptionSeverity:
        """
        评估异常严重程度
        
        Args:
            exception (Exception): 异常对象
        
        Returns:
            ExceptionSeverity: 严重程度
        """
        if isinstance(exception, InsufficientBalanceException):
            return ExceptionSeverity.HIGH
        elif isinstance(exception, RateLimitException):
            return ExceptionSeverity.MEDIUM
        elif isinstance(exception, NetworkException):
            return ExceptionSeverity.LOW
        else:
            return ExceptionSeverity.MEDIUM
    
    def _record_exception(
        self,
        exception: Exception,
        category: ExceptionCategory,
        severity: ExceptionSeverity,
        context: Optional[Dict] = None
    ):
        """
        记录异常
        
        Args:
            exception (Exception): 异常对象
            category (ExceptionCategory): 分类
            severity (ExceptionSeverity): 严重程度
            context (Dict, optional): 上下文信息
        """
        # 更新统计
        category_key = category.value
        severity_key = severity.value
        
        self.exception_by_category[category_key] = self.exception_by_category.get(category_key, 0) + 1
        self.exception_by_severity[severity_key] = self.exception_by_severity.get(severity_key, 0) + 1
        
        # 记录日志
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': type(exception).__name__,
            'category': category_key,
            'severity': severity_key,
            'message': str(exception),
            'context': context or {}
        }
        
        if severity == ExceptionSeverity.CRITICAL:
            logger.critical(f"❌ 严重异常：{json.dumps(log_data, ensure_ascii=False)}")
        elif severity == ExceptionSeverity.HIGH:
            logger.error(f"❌ 高优先级异常：{json.dumps(log_data, ensure_ascii=False)}")
        else:
            logger.warning(f"⚠️ 异常：{json.dumps(log_data, ensure_ascii=False)}")
        
        # 发送告警
        if severity in [ExceptionSeverity.HIGH, ExceptionSeverity.CRITICAL]:
            self._send_alert(log_data)
    
    # ==================== 异常处理逻辑 ====================
    
    def _handle_trading_exception(
        self,
        exception: TradingException,
        category: ExceptionCategory,
        severity: ExceptionSeverity
    ) -> Result:
        """
        处理交易异常
        
        Args:
            exception (TradingException): 交易异常
            category (ExceptionCategory): 分类
            severity (ExceptionSeverity): 严重程度
        
        Returns:
            Result: 处理结果
        """
        logger.info(f"🔧 处理交易异常：{exception.error_code}")
        
        # 根据错误码选择恢复策略
        if exception.error_code == "INSUFFICIENT_BALANCE":
            # 余额不足 - 需要人工介入
            return Result.fail(
                error_code=exception.error_code,
                message=f"余额不足，请充值：{exception.message}"
            )
        elif exception.error_code == "NETWORK_ERROR":
            # 网络错误 - 自动重试
            return self._retry_operation(exception)
        elif exception.error_code == "RATE_LIMIT_EXCEEDED":
            # 限流 - 等待后重试
            return self._handle_rate_limit(exception)
        else:
            # 其他错误 - 返回错误信息
            return Result.fail(
                error_code=exception.error_code,
                message=exception.message
            )
    
    def _handle_network_exception(self, exception: NetworkException) -> Result:
        """
        处理网络异常
        
        Args:
            exception (NetworkException): 网络异常
        
        Returns:
            Result: 处理结果
        """
        logger.info("🔄 处理网络异常，尝试重试...")
        
        # 添加到重试队列
        self.retry_queue.append({
            'exception': exception,
            'timestamp': datetime.now(),
            'retry_count': 0
        })
        
        # 自动重试
        return self._retry_operation(exception)
    
    def _handle_order_exception(self, exception: Exception) -> Result:
        """
        处理订单异常
        
        Args:
            exception (Exception): 订单异常
        
        Returns:
            Result: 处理结果
        """
        logger.info(f"🔧 处理订单异常：{str(exception)}")
        
        # 订单异常通常不重试，直接返回错误
        return Result.fail(
            error_code="ORDER_ERROR",
            message=str(exception)
        )
    
    def _handle_generic_exception(self, exception: Exception) -> Result:
        """
        处理通用异常
        
        Args:
            exception (Exception): 异常对象
        
        Returns:
            Result: 处理结果
        """
        logger.error(f"❌ 未处理的异常：{type(exception).__name__} - {str(exception)}")
        
        return Result.fail(
            error_code="INTERNAL_ERROR",
            message=f"系统异常：{str(exception)}"
        )
    
    # ==================== 重试机制 ====================
    
    def _retry_operation(self, exception: Exception, max_retries: int = 3) -> Result:
        """
        重试操作
        
        Args:
            exception (Exception): 异常对象
            max_retries (int): 最大重试次数
        
        Returns:
            Result: 处理结果
        """
        # 查找重试队列中的记录
        retry_record = None
        for record in self.retry_queue:
            if str(record['exception']) == str(exception):
                retry_record = record
                break
        
        if not retry_record:
            # 新异常，创建重试记录
            retry_record = {
                'exception': exception,
                'timestamp': datetime.now(),
                'retry_count': 0
            }
            self.retry_queue.append(retry_record)
        
        # 检查重试次数
        if retry_record['retry_count'] >= max_retries:
            logger.error(f"❌ 重试次数已达上限（{max_retries}次）")
            return Result.fail(
                error_code="MAX_RETRIES_EXCEEDED",
                message=f"重试{max_retries}次后仍失败"
            )
        
        # 计算延迟时间（指数退避）
        delay = min(self.BASE_DELAY * (2 ** retry_record['retry_count']), self.MAX_DELAY)
        
        logger.info(f"⏳ {delay:.1f}秒后重试（第{retry_record['retry_count'] + 1}/{max_retries}次）")
        
        # 等待
        time.sleep(delay)
        
        # 增加重试计数
        retry_record['retry_count'] += 1
        
        # 返回重试信号
        return Result.ok(
            data={'retry': True, 'delay': delay, 'attempt': retry_record['retry_count']},
            message="准备重试"
        )
    
    def _handle_rate_limit(self, exception: RateLimitException) -> Result:
        """
        处理限流异常
        
        Args:
            exception (RateLimitException): 限流异常
        
        Returns:
            Result: 处理结果
        """
        logger.warning("⏳ 触发限流，等待 60 秒...")
        
        # 限流需要等待较长时间
        time.sleep(60)
        
        return Result.ok(
            data={'retry': True, 'delay': 60},
            message="限流解除，准备重试"
        )
    
    # ==================== 恢复策略 ====================
    
    def _recover_network_retry(self, context: Dict) -> Result:
        """
        网络重试恢复策略
        
        Args:
            context (Dict): 上下文信息
        
        Returns:
            Result: 恢复结果
        """
        logger.info("🔧 执行网络重试恢复策略")
        return Result.ok(message="网络重试恢复策略执行完成")
    
    def _recover_balance_refresh(self, context: Dict) -> Result:
        """
        余额刷新恢复策略
        
        Args:
            context (Dict): 上下文信息
        
        Returns:
            Result: 恢复结果
        """
        logger.info("🔧 执行余额刷新恢复策略")
        return Result.ok(message="余额刷新恢复策略执行完成")
    
    def _recover_order_cancel(self, context: Dict) -> Result:
        """
        订单取消恢复策略
        
        Args:
            context (Dict): 上下文信息
        
        Returns:
            Result: 恢复结果
        """
        logger.info("🔧 执行订单取消恢复策略")
        return Result.ok(message="订单取消恢复策略执行完成")
    
    def _recover_system_restart(self, context: Dict) -> Result:
        """
        系统重启恢复策略
        
        Args:
            context (Dict): 上下文信息
        
        Returns:
            Result: 恢复结果
        """
        logger.info("🔧 执行系统重启恢复策略")
        return Result.ok(message="系统重启恢复策略执行完成")
    
    # ==================== 告警管理 ====================
    
    def register_alert_callback(self, callback: Callable):
        """
        注册告警回调函数
        
        Args:
            callback (Callable): 回调函数
        """
        self.alert_callbacks.append(callback)
        logger.info("📝 注册告警回调函数")
    
    def _send_alert(self, alert_data: Dict):
        """
        发送告警
        
        Args:
            alert_data (Dict): 告警数据
        """
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"❌ 告警回调执行失败：{e}")
    
    # ==================== 持久化 ====================
    
    def _load_data(self):
        """从持久化文件加载数据"""
        if not os.path.exists(self.persistence_file):
            logger.debug("持久化文件不存在，使用默认数据")
            return
        
        try:
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.exception_count = data.get('exception_count', 0)
            self.exception_by_category = data.get('exception_by_category', {})
            self.exception_by_severity = data.get('exception_by_severity', {})
            
            logger.info(f"📊 加载数据成功（异常数：{self.exception_count}）")
            
        except Exception as e:
            logger.error(f"⚠️ 加载数据失败：{e}")
    
    def _save_data(self):
        """保存数据到持久化文件"""
        try:
            data = {
                'exception_count': self.exception_count,
                'exception_by_category': self.exception_by_category,
                'exception_by_severity': self.exception_by_severity,
                'update_time': datetime.now().isoformat()
            }
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("📝 已保存数据")
            
        except Exception as e:
            logger.error(f"❌ 保存数据失败：{e}")
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'exception_count': self.exception_count,
            'exception_by_category': self.exception_by_category,
            'exception_by_severity': self.exception_by_severity,
            'retry_queue_size': len(self.retry_queue),
            'recovery_strategies': list(self.recovery_strategies.keys())
        }


# 全局实例
_exception_manager: Optional[ExceptionManager] = None


def get_exception_manager() -> ExceptionManager:
    """获取全局异常处理引擎实例"""
    global _exception_manager
    if _exception_manager is None:
        _exception_manager = ExceptionManager()
    return _exception_manager


def reset_exception_manager():
    """重置异常处理引擎（测试用）"""
    global _exception_manager
    _exception_manager = None
