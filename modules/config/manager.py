#!/usr/bin/env python3
"""
配置管理模块

使用 pydantic-settings 管理配置，支持 YAML 和环境变量。

用法:
    from modules.config.manager import load_config

    config = load_config('config/default.yaml')
    print(config.binance.api_key)
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict
import yaml
import os


class SystemConfig(BaseSettings):
    """系统配置"""

    name: str = "大王量化交易系统"
    version: str = "v3.0.0"
    environment: str = "development"  # development/production


class BinanceConfig(BaseSettings):
    """币安配置"""

    api_key: str = ""
    secret_key: str = ""
    testnet: bool = True
    rate_limit_orders_per_second: int = 10
    rate_limit_orders_per_day: int = 100000

    class Config:
        env_prefix = "BINANCE_"


class DatabaseConfig(BaseSettings):
    """数据库配置"""

    type: str = "sqlite"
    path: str = "data/lobster_v3.db"

    # Redis 配置（可选）
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0


class LoggingConfig(BaseSettings):
    """日志配置"""

    level: str = "INFO"  # DEBUG/INFO/WARNING/ERROR
    format: str = "json"  # json/text
    output_file: str = "logs/trading.log"
    console_output: bool = True


class StrategyConfig(BaseSettings):
    """策略配置"""

    default_leverage: int = 5
    default_amount: float = 100.0
    max_positions: int = 10
    max_total_exposure: float = 10000.0


class RiskConfig(BaseSettings):
    """风控配置"""

    max_total_exposure: float = 10000.0
    max_single_position: float = 1000.0
    max_daily_loss: float = 500.0
    stop_loss_percentage: float = 0.05  # 5%


class Config(BaseSettings):
    """总配置"""

    system: SystemConfig = Field(default_factory=SystemConfig)
    binance: BinanceConfig = Field(default_factory=BinanceConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_path: str = "config/default.yaml") -> Config:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        Config: 配置对象

    Example:
        >>> config = load_config('config/default.yaml')
        >>> print(config.binance.testnet)
        True
    """
    if not os.path.exists(config_path):
        # 配置文件不存在，返回默认配置
        return Config()

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # 合并环境变量
    return Config(**data)


def save_config(config: Config, config_path: str = "config/default.yaml"):
    """
    保存配置到文件

    Args:
        config: 配置对象
        config_path: 配置文件路径
    """
    # 确保目录存在
    config_dir = os.path.dirname(config_path)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)

    data = {
        "system": config.system.dict(),
        "binance": config.binance.dict(),
        "database": config.database.dict(),
        "logging": config.logging.dict(),
        "strategy": config.strategy.dict(),
        "risk": config.risk.dict(),
    }

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
