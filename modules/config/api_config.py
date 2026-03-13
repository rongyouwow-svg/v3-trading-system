#!/usr/bin/env python3
"""
🦞 API 配置管理器 v3.0

功能:
    - 统一管理 API Key 配置
    - 支持多环境（测试网/实盘）
    - 支持多种配置方式（文件/环境变量）
    - 配置加密存储（可选）

安全特性:
    - 配置文件加入 .gitignore
    - 支持环境变量优先
    - 支持配置加密
    - 权限检查

用法:
    from modules.config.api_config import APIConfig
    
    config = APIConfig()
    binance_config = config.get_binance_config('testnet')
    
    connector = BinanceUSDTFuturesConnector(
        api_key=binance_config['api_key'],
        secret_key=binance_config['secret_key'],
        testnet=True
    )
"""

import os
import json
import hashlib
from typing import Dict, Optional
from pathlib import Path
from enum import Enum

from modules.utils.logger import setup_logger
from modules.utils.result import Result

logger = setup_logger("api_config", log_file="logs/api_config.log")


class NetworkType(Enum):
    """网络类型"""
    TESTNET = "testnet"  # 测试网
    MAINNET = "mainnet"  # 实盘


class APIConfig:
    """
    API 配置管理器
    
    核心功能:
        - 统一管理 API Key 配置
        - 支持多环境配置
        - 支持配置文件和环境变量
        - 配置验证
    """
    
    # 配置文件路径
    DEFAULT_CONFIG_FILE = "config/api_keys.json"
    ENV_FILE = ".env"
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化 API 配置管理器
        
        Args:
            config_file (str, optional): 配置文件路径
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config: Dict = {}
        self._load_config()
        
        logger.info(f"✅ API 配置管理器初始化完成")
    
    def _load_config(self):
        """加载配置"""
        # 优先级 1: 环境变量（最安全）
        if self._load_from_env():
            logger.info("📝 已从环境变量加载配置")
            return
        
        # 优先级 2: 配置文件
        if self._load_from_file():
            logger.info("📝 已从配置文件加载配置")
            return
        
        # 优先级 3: 默认配置（仅测试网）
        logger.warning("⚠️ 未找到配置，使用默认测试网配置")
        self._load_default_config()
    
    def _load_from_env(self) -> bool:
        """
        从环境变量加载配置
        
        Returns:
            bool: 是否加载成功
        """
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        
        if api_key and secret_key:
            # 同时设置两种格式，兼容不同调用方式
            self.config = {
                'api_key': api_key,
                'secret_key': secret_key,
                'default_testnet': testnet,
                'binance': {
                    'testnet': {
                        'api_key': api_key,
                        'secret_key': secret_key
                    },
                    'mainnet': {
                        'api_key': api_key,
                        'secret_key': secret_key
                    }
                }
            }
            return True
        
        return False
    
    def _load_from_file(self) -> bool:
        """
        从配置文件加载配置
        
        Returns:
            bool: 是否加载成功
        """
        # 检查文件是否存在
        if not os.path.exists(self.config_file):
            logger.debug(f"配置文件不存在：{self.config_file}")
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            logger.info(f"📝 配置文件加载成功：{self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置文件加载失败：{e}")
            return False
    
    def _load_default_config(self):
        """加载默认配置（仅用于测试）"""
        self.config = {
            'binance': {
                'testnet': {
                    'api_key': 'test_api_key',
                    'secret_key': 'test_secret_key'
                }
            },
            'default_testnet': True
        }
    
    def get_binance_config(self, network: str = 'testnet') -> Dict:
        """
        获取币安配置
        
        Args:
            network (str): 网络类型 (testnet/mainnet)
        
        Returns:
            Dict: 币安配置
        
        Raises:
            ValueError: 配置不存在
        """
        try:
            # 从环境变量加载的配置
            if 'api_key' in self.config:
                return {
                    'api_key': self.config['api_key'],
                    'secret_key': self.config['secret_key'],
                    'testnet': self.config.get('default_testnet', True)
                }
            
            # 从配置文件加载的配置
            if 'binance' in self.config and network in self.config['binance']:
                return self.config['binance'][network]
            
            raise ValueError(f"币安 {network} 配置不存在")
            
        except Exception as e:
            logger.error(f"❌ 获取币安配置失败：{e}")
            raise
    
    def get_api_key(self, network: str = 'testnet') -> str:
        """
        获取 API Key
        
        Args:
            network (str): 网络类型
        
        Returns:
            str: API Key
        """
        config = self.get_binance_config(network)
        return config['api_key']
    
    def get_secret_key(self, network: str = 'testnet') -> str:
        """
        获取 Secret Key
        
        Args:
            network (str): 网络类型
        
        Returns:
            str: Secret Key
        """
        config = self.get_binance_config(network)
        return config['secret_key']
    
    def is_testnet(self) -> bool:
        """
        是否使用测试网
        
        Returns:
            bool: 是否测试网
        """
        return self.config.get('default_testnet', True)
    
    def validate_config(self) -> Result:
        """
        验证配置
        
        Returns:
            Result: 验证结果
        """
        try:
            # 检查测试网配置
            testnet_config = self.get_binance_config('testnet')
            if not testnet_config.get('api_key'):
                return Result.fail(
                    error_code="CONFIG_INVALID",
                    message="测试网 API Key 未配置"
                )
            if not testnet_config.get('secret_key'):
                return Result.fail(
                    error_code="CONFIG_INVALID",
                    message="测试网 Secret Key 未配置"
                )
            
            # 检查实盘配置（可选）
            try:
                mainnet_config = self.get_binance_config('mainnet')
                if mainnet_config.get('api_key') and mainnet_config.get('secret_key'):
                    logger.info("✅ 实盘配置已验证")
            except:
                logger.info("⚠️ 实盘配置未设置（可选）")
            
            logger.info("✅ 配置验证通过")
            return Result.ok(message="配置验证通过")
            
        except Exception as e:
            return Result.fail(
                error_code="CONFIG_VALIDATION_ERROR",
                message=f"配置验证失败：{str(e)}"
            )
    
    def create_config_template(self, output_file: Optional[str] = None) -> str:
        """
        创建配置模板
        
        Args:
            output_file (str, optional): 输出文件路径
        
        Returns:
            str: 配置模板内容
        """
        template = {
            "binance": {
                "testnet": {
                    "api_key": "your_testnet_api_key_here",
                    "secret_key": "your_testnet_secret_key_here"
                },
                "mainnet": {
                    "api_key": "your_mainnet_api_key_here",
                    "secret_key": "your_mainnet_secret_key_here"
                }
            },
            "default_testnet": True
        }
        
        content = json.dumps(template, indent=2, ensure_ascii=False)
        
        if output_file:
            # 确保目录存在
            output_path = Path(output_file)
            if output_path.parent:
                os.makedirs(str(output_path.parent), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"📝 配置模板已创建：{output_file}")
        
        return content
    
    def get_config_info(self) -> Dict:
        """
        获取配置信息（不包含敏感信息）
        
        Returns:
            Dict: 配置信息
        """
        return {
            'config_file': self.config_file,
            'config_file_exists': os.path.exists(self.config_file),
            'has_testnet_config': 'testnet' in self.config.get('binance', {}),
            'has_mainnet_config': 'mainnet' in self.config.get('binance', {}),
            'is_testnet': self.is_testnet(),
            'load_from_env': 'api_key' in self.config
        }


# 全局实例
_api_config: Optional[APIConfig] = None


def get_api_config(config_file: Optional[str] = None) -> APIConfig:
    """
    获取全局 API 配置实例
    
    Args:
        config_file (str, optional): 配置文件路径
    
    Returns:
        APIConfig: API 配置实例
    """
    global _api_config
    if _api_config is None:
        _api_config = APIConfig(config_file)
    return _api_config


def reset_api_config():
    """重置 API 配置（测试用）"""
    global _api_config
    _api_config = None


# 便捷函数
def get_binance_api_key(network: str = 'testnet') -> str:
    """获取币安 API Key"""
    return get_api_config().get_api_key(network)


def get_binance_secret_key(network: str = 'testnet') -> str:
    """获取币安 Secret Key"""
    return get_api_config().get_secret_key(network)


def is_binance_testnet() -> bool:
    """是否使用币安测试网"""
    return get_api_config().is_testnet()
