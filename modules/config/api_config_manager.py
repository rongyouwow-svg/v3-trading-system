#!/usr/bin/env python3
"""
🦞 多 API 配置管理器 v3.0

功能:
    - 支持多套 API 配置（测试网 + 实盘）
    - 策略可指定使用哪套 API
    - API 配置 CRUD 操作
    - API 实例管理

用法:
    from modules.config.api_config_manager import APIConfigManager
    
    manager = APIConfigManager()
    
    # 获取所有 API 配置
    configs = manager.get_all_configs()
    
    # 获取默认 API
    default = manager.get_default_config()
    
    # 创建 API 实例
    connector = manager.create_connector("testnet_1")
"""

import json
import os
from typing import Dict, List, Optional
from decimal import Decimal

from modules.utils.logger import setup_logger
from modules.utils.result import Result

logger = setup_logger("api_config_manager", log_file="logs/api_config_manager.log")


class APIConfigManager:
    """API 配置管理器"""
    
    CONFIG_FILE = "config/api_configs.json"
    
    def __init__(self, config_file: str = None):
        """
        初始化 API 配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or self.CONFIG_FILE
        self.config = self._load_config()
        self.connectors: Dict[str, any] = {}  # 缓存的连接器实例
        
        logger.info(f"✅ API 配置管理器初始化完成")
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"❌ 加载配置文件失败：{e}")
        
        # 返回默认配置
        return {
            "api_configs": [],
            "default_api_id": None,
            "strategy": {
                "default_leverage": 5,
                "default_amount": 100,
                "stop_loss_pct": 5
            }
        }
    
    def _save_config(self):
        """保存配置文件"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.debug(f"📝 配置文件已保存")
        except Exception as e:
            logger.error(f"❌ 保存配置文件失败：{e}")
    
    def get_all_configs(self) -> List[Dict]:
        """获取所有 API 配置"""
        return self.config.get("api_configs", [])
    
    def get_config(self, api_id: str) -> Optional[Dict]:
        """获取指定 API 配置"""
        configs = self.get_all_configs()
        for cfg in configs:
            if cfg.get("id") == api_id:
                return cfg
        return None
    
    def get_default_config(self) -> Optional[Dict]:
        """获取默认 API 配置"""
        default_id = self.config.get("default_api_id")
        if default_id:
            return self.get_config(default_id)
        
        # 如果没有默认，返回第一个启用的
        configs = self.get_all_configs()
        for cfg in configs:
            if cfg.get("enabled", False):
                return cfg
        return None
    
    def add_config(self, api_config: Dict) -> Result:
        """
        添加 API 配置
        
        Args:
            api_config: API 配置字典
        
        Returns:
            Result: 操作结果
        """
        # 验证必填字段
        required_fields = ["id", "name", "api_key", "secret_key"]
        for field in required_fields:
            if field not in api_config:
                return Result.fail(
                    error_code="MISSING_FIELD",
                    message=f"缺少必填字段：{field}"
                )
        
        # 检查 ID 是否重复
        if self.get_config(api_config["id"]):
            return Result.fail(
                error_code="DUPLICATE_ID",
                message=f"API ID 已存在：{api_config['id']}"
            )
        
        # 添加到配置
        self.config["api_configs"].append(api_config)
        self._save_config()
        
        logger.info(f"✅ 添加 API 配置：{api_config['name']}")
        return Result.ok(message=f"API 配置已添加：{api_config['name']}")
    
    def update_config(self, api_id: str, updates: Dict) -> Result:
        """
        更新 API 配置
        
        Args:
            api_id: API ID
            updates: 更新字段
        
        Returns:
            Result: 操作结果
        """
        configs = self.config.get("api_configs", [])
        for i, cfg in enumerate(configs):
            if cfg.get("id") == api_id:
                configs[i].update(updates)
                self.config["api_configs"] = configs
                self._save_config()
                
                # 清除缓存的连接器
                if api_id in self.connectors:
                    del self.connectors[api_id]
                
                logger.info(f"✅ 更新 API 配置：{api_id}")
                return Result.ok(message=f"API 配置已更新：{api_id}")
        
        return Result.fail(
            error_code="NOT_FOUND",
            message=f"API 配置不存在：{api_id}"
        )
    
    def delete_config(self, api_id: str) -> Result:
        """
        删除 API 配置
        
        Args:
            api_id: API ID
        
        Returns:
            Result: 操作结果
        """
        configs = self.config.get("api_configs", [])
        configs = [cfg for cfg in configs if cfg.get("id") != api_id]
        self.config["api_configs"] = configs
        
        # 如果删除的是默认 API，清除默认设置
        if self.config.get("default_api_id") == api_id:
            self.config["default_api_id"] = None
        
        self._save_config()
        
        # 清除缓存的连接器
        if api_id in self.connectors:
            del self.connectors[api_id]
        
        logger.info(f"✅ 删除 API 配置：{api_id}")
        return Result.ok(message=f"API 配置已删除：{api_id}")
    
    def set_default(self, api_id: str) -> Result:
        """
        设置默认 API
        
        Args:
            api_id: API ID
        
        Returns:
            Result: 操作结果
        """
        if not self.get_config(api_id):
            return Result.fail(
                error_code="NOT_FOUND",
                message=f"API 配置不存在：{api_id}"
            )
        
        self.config["default_api_id"] = api_id
        self._save_config()
        
        logger.info(f"✅ 设置默认 API：{api_id}")
        return Result.ok(message=f"默认 API 已设置：{api_id}")
    
    def enable_config(self, api_id: str) -> Result:
        """启用 API 配置"""
        return self.update_config(api_id, {"enabled": True})
    
    def disable_config(self, api_id: str) -> Result:
        """禁用 API 配置"""
        return self.update_config(api_id, {"enabled": False})
    
    def get_enabled_configs(self) -> List[Dict]:
        """获取所有启用的 API 配置"""
        configs = self.get_all_configs()
        return [cfg for cfg in configs if cfg.get("enabled", False)]
    
    def create_connector(self, api_id: str):
        """
        创建 API 连接器实例
        
        Args:
            api_id: API ID
        
        Returns:
            连接器实例
        """
        # 检查缓存
        if api_id in self.connectors:
            return self.connectors[api_id]
        
        # 获取配置
        config = self.get_config(api_id)
        if not config:
            raise ValueError(f"API 配置不存在：{api_id}")
        
        # 创建连接器
        from connectors.binance.usdt_futures import BinanceUSDTFuturesConnector
        
        connector = BinanceUSDTFuturesConnector(
            api_key=config["api_key"],
            secret_key=config["secret_key"],
            testnet=config.get("testnet", False)
        )
        
        # 缓存连接器
        self.connectors[api_id] = connector
        
        logger.info(f"✅ 创建 API 连接器：{api_id}")
        return connector
    
    def get_strategy_config(self) -> Dict:
        """获取策略配置"""
        return self.config.get("strategy", {})
    
    def update_strategy_config(self, updates: Dict) -> Result:
        """更新策略配置"""
        if "strategy" not in self.config:
            self.config["strategy"] = {}
        
        self.config["strategy"].update(updates)
        self._save_config()
        
        logger.info(f"✅ 更新策略配置")
        return Result.ok(message="策略配置已更新")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        configs = self.get_all_configs()
        enabled = [cfg for cfg in configs if cfg.get("enabled", False)]
        testnet = [cfg for cfg in configs if cfg.get("testnet", False)]
        mainnet = [cfg for cfg in configs if not cfg.get("testnet", False)]
        
        return {
            "total_configs": len(configs),
            "enabled_configs": len(enabled),
            "testnet_configs": len(testnet),
            "mainnet_configs": len(mainnet),
            "default_api_id": self.config.get("default_api_id")
        }


# 全局实例
_api_config_manager: Optional[APIConfigManager] = None


def get_api_config_manager() -> APIConfigManager:
    """获取全局 API 配置管理器实例"""
    global _api_config_manager
    if _api_config_manager is None:
        _api_config_manager = APIConfigManager()
    return _api_config_manager


def reset_api_config_manager():
    """重置 API 配置管理器（测试用）"""
    global _api_config_manager
    _api_config_manager = None
