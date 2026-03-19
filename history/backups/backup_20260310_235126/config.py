#!/usr/bin/env python3
"""
🦞 配置管理模块
"""

import json
import os
from typing import Dict, Optional

# 配置文件路径
API_KEYS_FILE = '/tmp/binance_api_keys.json'
SIM_STATE_FILE = '/tmp/sim_state_v6.json'
STRATEGIES_FILE = '/tmp/strategies_v6.json'

def load_api_keys() -> list:
    """加载币安 API Key 列表"""
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_api_keys(keys: list):
    """保存币安 API Key 列表"""
    with open(API_KEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(keys, f, indent=2, ensure_ascii=False)

def get_active_api_key(testnet: bool = False) -> Optional[Dict]:
    """获取当前激活的 API Key"""
    keys = load_api_keys()
    for key in keys:
        if key.get('active', False) and key.get('testnet', False) == testnet:
            return key
    # 如果没有找到，返回第一个匹配类型的
    for key in keys:
        if key.get('testnet', False) == testnet:
            return key
    return None

def load_sim_state() -> Dict:
    """加载模拟账户状态"""
    default = {
        'icap': 100.0,
        'cap': 100.0,
        'pos': {},
        'trades': [],
        'tid': 0
    }
    if os.path.exists(SIM_STATE_FILE):
        with open(SIM_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_sim_state(state: Dict):
    """保存模拟账户状态"""
    with open(SIM_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def load_strategies() -> list:
    """加载策略列表"""
    if os.path.exists(STRATEGIES_FILE):
        with open(STRATEGIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_strategies(strategies: list):
    """保存策略列表"""
    with open(STRATEGIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(strategies, f, indent=2, ensure_ascii=False)
