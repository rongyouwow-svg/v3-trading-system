#!/usr/bin/env python3
"""
🦞 插件管理器 v3.0

职责:
    - 插件加载
    - 插件卸载
    - 插件执行
    - 插件状态管理

用法:
    from plugins.manager import PluginManager
    
    manager = PluginManager()
    manager.load_plugin('telegram')
    manager.execute_plugin('telegram', message='Hello')
"""

import os
import importlib
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

from plugins.base import BasePlugin, PluginStatus
from modules.utils.result import Result
from modules.utils.logger import setup_logger

logger = setup_logger("plugin_manager", log_file="logs/plugin_manager.log")


class PluginManager:
    """
    插件管理器
    
    核心功能:
        - 插件加载
        - 插件卸载
        - 插件执行
        - 状态管理
    """
    
    def __init__(self, plugin_dir: str = None):
        """
        初始化插件管理器
        
        Args:
            plugin_dir (str, optional): 插件目录
        """
        self.plugin_dir = plugin_dir or os.path.dirname(__file__)
        
        # 已加载的插件 {plugin_name: plugin_instance}
        self.plugins: Dict[str, BasePlugin] = {}
        
        # 插件配置 {plugin_name: config}
        self.plugin_configs: Dict[str, Dict] = {}
        
        logger.info("🔌 插件管理器初始化完成")
    
    def load_plugin(self, plugin_name: str, config: Optional[Dict] = None) -> Result:
        """
        加载插件
        
        Args:
            plugin_name (str): 插件名称
            config (Dict, optional): 插件配置
        
        Returns:
            Result: 加载结果
        """
        logger.info(f"📥 加载插件：{plugin_name}")
        
        try:
            # 检查是否已加载
            if plugin_name in self.plugins:
                logger.warning(f"⚠️ 插件已加载：{plugin_name}")
                return Result.ok(message=f"插件 {plugin_name} 已加载")
            
            # 动态导入插件模块
            module_path = f"plugins.{plugin_name}.{plugin_name}_plugin"
            module = importlib.import_module(module_path)
            
            # 查找插件类
            plugin_class = self._find_plugin_class(module)
            
            if not plugin_class:
                return Result.fail(
                    error_code="PLUGIN_CLASS_NOT_FOUND",
                    message=f"未找到插件类：{plugin_name}"
                )
            
            # 创建插件实例
            plugin_instance = plugin_class()
            
            # 保存配置
            if config:
                self.plugin_configs[plugin_name] = config
            
            # 初始化插件
            init_result = plugin_instance.initialize()
            
            if not init_result.is_success:
                return init_result
            
            # 保存插件
            self.plugins[plugin_name] = plugin_instance
            
            logger.info(f"✅ 插件加载成功：{plugin_name}")
            
            return Result.ok(
                data={'name': plugin_name, 'version': plugin_instance.version},
                message=f"插件 {plugin_name} 加载成功"
            )
            
        except ImportError as e:
            logger.error(f"❌ 插件导入失败：{plugin_name} - {e}")
            return Result.fail(
                error_code="PLUGIN_IMPORT_ERROR",
                message=f"插件 {plugin_name} 导入失败：{str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ 插件加载失败：{plugin_name} - {e}")
            return Result.fail(
                error_code="PLUGIN_LOAD_ERROR",
                message=f"插件 {plugin_name} 加载失败：{str(e)}"
            )
    
    def _find_plugin_class(self, module) -> Optional[Type[BasePlugin]]:
        """
        查找插件类
        
        Args:
            module: 插件模块
        
        Returns:
            Optional[Type[BasePlugin]]: 插件类
        """
        # 遍历模块属性查找插件类
        for name in dir(module):
            obj = getattr(module, name)
            
            # 检查是否是 BasePlugin 的子类
            if (isinstance(obj, type) and 
                issubclass(obj, BasePlugin) and 
                obj is not BasePlugin):
                return obj
        
        return None
    
    def unload_plugin(self, plugin_name: str) -> Result:
        """
        卸载插件
        
        Args:
            plugin_name (str): 插件名称
        
        Returns:
            Result: 卸载结果
        """
        logger.info(f"📤 卸载插件：{plugin_name}")
        
        if plugin_name not in self.plugins:
            return Result.fail(
                error_code="PLUGIN_NOT_FOUND",
                message=f"插件 {plugin_name} 未加载"
            )
        
        try:
            plugin = self.plugins[plugin_name]
            
            # 关闭插件
            shutdown_result = plugin.shutdown()
            
            if not shutdown_result.is_success:
                return shutdown_result
            
            # 移除插件
            del self.plugins[plugin_name]
            
            # 移除配置
            if plugin_name in self.plugin_configs:
                del self.plugin_configs[plugin_name]
            
            logger.info(f"✅ 插件卸载成功：{plugin_name}")
            
            return Result.ok(message=f"插件 {plugin_name} 已卸载")
            
        except Exception as e:
            logger.error(f"❌ 插件卸载失败：{plugin_name} - {e}")
            return Result.fail(
                error_code="PLUGIN_UNLOAD_ERROR",
                message=f"插件 {plugin_name} 卸载失败：{str(e)}"
            )
    
    def execute_plugin(self, plugin_name: str, **kwargs) -> Result:
        """
        执行插件
        
        Args:
            plugin_name (str): 插件名称
            **kwargs: 执行参数
        
        Returns:
            Result: 执行结果
        """
        if plugin_name not in self.plugins:
            return Result.fail(
                error_code="PLUGIN_NOT_FOUND",
                message=f"插件 {plugin_name} 未加载"
            )
        
        plugin = self.plugins[plugin_name]
        
        if plugin.status != PluginStatus.ACTIVE:
            return Result.fail(
                error_code="PLUGIN_NOT_ACTIVE",
                message=f"插件 {plugin_name} 未激活"
            )
        
        # 执行插件
        return plugin.execute_with_log(**kwargs)
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict]:
        """
        获取插件信息
        
        Args:
            plugin_name (str): 插件名称
        
        Returns:
            Optional[Dict]: 插件信息
        """
        if plugin_name not in self.plugins:
            return None
        
        return self.plugins[plugin_name].get_info()
    
    def get_all_plugins(self) -> Dict[str, Dict]:
        """
        获取所有插件信息
        
        Returns:
            Dict[str, Dict]: 插件信息字典
        """
        return {
            name: plugin.get_info()
            for name, plugin in self.plugins.items()
        }
    
    def get_active_plugins(self) -> List[str]:
        """
        获取所有活跃插件
        
        Returns:
            List[str]: 活跃插件名称列表
        """
        return [
            name for name, plugin in self.plugins.items()
            if plugin.status == PluginStatus.ACTIVE
        ]
    
    def reload_plugin(self, plugin_name: str, config: Optional[Dict] = None) -> Result:
        """
        重新加载插件
        
        Args:
            plugin_name (str): 插件名称
            config (Dict, optional): 新配置
        
        Returns:
            Result: 重载结果
        """
        logger.info(f"🔄 重新加载插件：{plugin_name}")
        
        # 卸载
        unload_result = self.unload_plugin(plugin_name)
        
        if not unload_result.is_success:
            return unload_result
        
        # 重新加载
        return self.load_plugin(plugin_name, config)
    
    def get_statistics(self) -> Dict:
        """
        获取插件统计信息
        
        Returns:
            Dict: 统计信息
        """
        total = len(self.plugins)
        active = sum(1 for p in self.plugins.values() if p.status == PluginStatus.ACTIVE)
        error = sum(1 for p in self.plugins.values() if p.status == PluginStatus.ERROR)
        
        return {
            'total_plugins': total,
            'active_plugins': active,
            'error_plugins': error,
            'inactive_plugins': total - active - error,
            'plugin_names': list(self.plugins.keys())
        }


# 全局实例
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(plugin_dir: str = None) -> PluginManager:
    """获取全局插件管理器实例"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager(plugin_dir)
    return _plugin_manager


def reset_plugin_manager():
    """重置插件管理器（测试用）"""
    global _plugin_manager
    _plugin_manager = None
