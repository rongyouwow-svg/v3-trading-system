#!/usr/bin/env python3
"""
🦞 插件基类 v3.0

所有插件必须继承此基类。

用法:
    from plugins.base import BasePlugin
    
    class MyPlugin(BasePlugin):
        def execute(self, **kwargs):
            pass
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from modules.utils.result import Result
from modules.utils.logger import setup_logger

logger = setup_logger("plugin_base", log_file="logs/plugin.log")


class PluginStatus(Enum):
    """插件状态"""
    ACTIVE = "active"  # 活跃
    INACTIVE = "inactive"  # 未激活
    ERROR = "error"  # 错误
    LOADING = "loading"  # 加载中


class BasePlugin(ABC):
    """
    插件基类
    
    所有插件必须继承此基类并实现 execute 方法
    """
    
    # 插件元数据
    name: str = "BasePlugin"
    version: str = "1.0.0"
    description: str = "基础插件"
    author: str = "Unknown"
    
    def __init__(self):
        """初始化插件"""
        self.status = PluginStatus.LOADING
        self.created_at = datetime.now()
        self.last_executed = None
        self.execution_count = 0
        self.error_message: Optional[str] = None
        
        logger.info(f"🔌 插件初始化：{self.name} v{self.version}")
    
    @abstractmethod
    def execute(self, **kwargs) -> Result:
        """
        执行插件
        
        Args:
            **kwargs: 执行参数
        
        Returns:
            Result: 执行结果
        """
        pass
    
    def initialize(self) -> Result:
        """
        初始化插件
        
        Returns:
            Result: 初始化结果
        """
        try:
            self._initialize()
            self.status = PluginStatus.ACTIVE
            logger.info(f"✅ 插件初始化成功：{self.name}")
            return Result.ok(message=f"插件 {self.name} 初始化成功")
        except Exception as e:
            self.status = PluginStatus.ERROR
            self.error_message = str(e)
            logger.error(f"❌ 插件初始化失败：{self.name} - {e}")
            return Result.fail(error_code="PLUGIN_INIT_FAILED", message=str(e))
    
    def _initialize(self):
        """
        子类实现的初始化逻辑
        
        可选实现
        """
        pass
    
    def shutdown(self) -> Result:
        """
        关闭插件
        
        Returns:
            Result: 关闭结果
        """
        try:
            self._shutdown()
            self.status = PluginStatus.INACTIVE
            logger.info(f"🛑 插件已关闭：{self.name}")
            return Result.ok(message=f"插件 {self.name} 已关闭")
        except Exception as e:
            logger.error(f"❌ 插件关闭失败：{self.name} - {e}")
            return Result.fail(error_code="PLUGIN_SHUTDOWN_FAILED", message=str(e))
    
    def _shutdown(self):
        """
        子类实现的关闭逻辑
        
        可选实现
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取插件信息
        
        Returns:
            Dict[str, Any]: 插件信息
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'execution_count': self.execution_count,
            'error_message': self.error_message
        }
    
    def _before_execute(self):
        """执行前钩子"""
        pass
    
    def _after_execute(self, result: Result):
        """执行后钩子"""
        self.last_executed = datetime.now()
        self.execution_count += 1
    
    def execute_with_log(self, **kwargs) -> Result:
        """
        带日志的执行
        
        Args:
            **kwargs: 执行参数
        
        Returns:
            Result: 执行结果
        """
        logger.info(f"▶️ 执行插件：{self.name}")
        
        self._before_execute()
        
        try:
            result = self.execute(**kwargs)
            self._after_execute(result)
            
            if result.is_success:
                logger.info(f"✅ 插件执行成功：{self.name}")
            else:
                logger.warning(f"⚠️ 插件执行失败：{self.name} - {result.message}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 插件执行异常：{self.name} - {e}")
            self.error_message = str(e)
            return Result.fail(error_code="PLUGIN_EXECUTION_ERROR", message=str(e))
