#!/usr/bin/env python3
"""
测试 API 配置管理模块
"""

import pytest
import os
import json
from pathlib import Path

from modules.config.api_config import (
    APIConfig,
    get_api_config,
    reset_api_config,
    get_binance_api_key,
    get_binance_secret_key,
    is_binance_testnet
)


class TestAPIConfig:
    """测试 API 配置管理器"""
    
    @pytest.fixture
    def config_file(self, tmp_path):
        """创建临时配置文件"""
        config_file = tmp_path / "test_api_keys.json"
        
        config_data = {
            "binance": {
                "testnet": {
                    "api_key": "test_api_key",
                    "secret_key": "test_secret_key"
                },
                "mainnet": {
                    "api_key": "main_api_key",
                    "secret_key": "main_secret_key"
                }
            },
            "default_testnet": True
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        return str(config_file)
    
    @pytest.fixture
    def config(self, config_file):
        """创建配置管理器实例"""
        reset_api_config()
        return APIConfig(config_file=config_file)
    
    def test_init(self, config):
        """测试初始化"""
        assert config is not None
        assert config.config_file is not None
    
    def test_load_from_file(self, config):
        """测试从文件加载配置"""
        assert 'binance' in config.config
        assert 'testnet' in config.config['binance']
        assert 'mainnet' in config.config['binance']
    
    def test_get_binance_config_testnet(self, config):
        """测试获取测试网配置"""
        binance_config = config.get_binance_config('testnet')
        
        assert 'api_key' in binance_config
        assert 'secret_key' in binance_config
        assert binance_config['api_key'] == 'test_api_key'
        assert binance_config['secret_key'] == 'test_secret_key'
    
    def test_get_binance_config_mainnet(self, config):
        """测试获取实盘配置"""
        binance_config = config.get_binance_config('mainnet')
        
        assert 'api_key' in binance_config
        assert 'secret_key' in binance_config
        assert binance_config['api_key'] == 'main_api_key'
        assert binance_config['secret_key'] == 'main_secret_key'
    
    def test_get_api_key(self, config):
        """测试获取 API Key"""
        api_key = config.get_api_key('testnet')
        assert api_key == 'test_api_key'
    
    def test_get_secret_key(self, config):
        """测试获取 Secret Key"""
        secret_key = config.get_secret_key('testnet')
        assert secret_key == 'test_secret_key'
    
    def test_is_testnet(self, config):
        """测试是否测试网"""
        assert config.is_testnet() is True
    
    def test_validate_config(self, config):
        """测试配置验证"""
        result = config.validate_config()
        
        assert result.is_success
        assert '配置验证通过' in result.message
    
    def test_get_config_info(self, config):
        """测试获取配置信息"""
        info = config.get_config_info()
        
        assert 'config_file' in info
        assert 'config_file_exists' in info
        assert info['config_file_exists'] is True
        assert info['has_testnet_config'] is True
    
    def test_create_config_template(self, config, tmp_path):
        """测试创建配置模板"""
        output_file = tmp_path / "api_keys_template.json"
        
        # 直接调用方法，不通过 config 实例
        from modules.config.api_config import APIConfig
        template_config = APIConfig()
        template = template_config.create_config_template(str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            template_data = json.load(f)
        
        assert 'binance' in template_data
        assert 'testnet' in template_data['binance']
        assert 'mainnet' in template_data['binance']


class TestAPIConfigEnv:
    """测试环境变量配置"""
    
    def test_load_from_env(self, monkeypatch, tmp_path):
        """测试从环境变量加载配置"""
        # 设置环境变量
        monkeypatch.setenv('BINANCE_API_KEY', 'env_api_key')
        monkeypatch.setenv('BINANCE_SECRET_KEY', 'env_secret_key')
        monkeypatch.setenv('BINANCE_TESTNET', 'true')
        
        config_file = tmp_path / "nonexistent.json"
        config = APIConfig(config_file=str(config_file))
        
        # 验证从环境变量加载
        assert config.config['api_key'] == 'env_api_key'
        assert config.config['secret_key'] == 'env_secret_key'
    
    def test_env_priority(self, monkeypatch, config_file, tmp_path):
        """测试环境变量优先级高于配置文件"""
        # 设置环境变量
        monkeypatch.setenv('BINANCE_API_KEY', 'env_api_key')
        monkeypatch.setenv('BINANCE_SECRET_KEY', 'env_secret_key')
        
        config = APIConfig(config_file=config_file)
        
        # 环境变量优先
        assert config.get_api_key() == 'env_api_key'


class TestGlobalAPIConfig:
    """测试全局配置实例"""
    
    def test_get_api_config_singleton(self):
        """测试单例模式"""
        reset_api_config()
        
        config1 = get_api_config()
        config2 = get_api_config()
        
        assert config1 is config2
    
    def test_get_binance_api_key(self, monkeypatch):
        """测试便捷函数"""
        monkeypatch.setenv('BINANCE_API_KEY', 'test_key')
        monkeypatch.setenv('BINANCE_SECRET_KEY', 'test_secret')
        
        reset_api_config()
        
        api_key = get_binance_api_key()
        assert api_key == 'test_key'
    
    def test_is_binance_testnet(self, monkeypatch):
        """测试测试网判断"""
        monkeypatch.setenv('BINANCE_TESTNET', 'true')
        
        reset_api_config()
        
        assert is_binance_testnet() is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
