#!/usr/bin/env python3
"""
📝 策略注册中心

功能：
1. 策略启动时自动注册
2. 策略停止时自动注销
3. 提供当前运行策略列表
4. 监控系统基于此列表保护
"""

import requests
import os
from datetime import datetime

# 注册中心 API
REGISTRY_URL = "http://localhost:3000/api/strategy"

def register_strategy(symbol: str, pid: int = None, leverage: int = 1, amount: float = 0, script: str = ""):
    """注册策略到注册中心"""
    if pid is None:
        pid = os.getpid()
    
    try:
        resp = requests.post(
            f"{REGISTRY_URL}/register",
            json={
                'symbol': symbol,
                'pid': pid,
                'leverage': leverage,
                'amount': amount,
                'script': script,
                'start_time': datetime.now().isoformat()
            },
            timeout=5
        )
        result = resp.json()
        if result.get('success'):
            print(f"✅ 策略 {symbol} 已注册 (PID: {pid})")
            return True
        else:
            print(f"❌ 策略 {symbol} 注册失败：{result.get('error', 'Unknown')}")
            return False
    except Exception as e:
        print(f"❌ 注册异常：{e}")
        return False

def unregister_strategy(symbol: str):
    """从注册中心注销策略"""
    try:
        resp = requests.post(
            f"{REGISTRY_URL}/unregister",
            json={'symbol': symbol},
            timeout=5
        )
        result = resp.json()
        if result.get('success'):
            print(f"✅ 策略 {symbol} 已注销")
            return True
        else:
            print(f"❌ 策略 {symbol} 注销失败：{result.get('error', 'Unknown')}")
            return False
    except Exception as e:
        print(f"❌ 注销异常：{e}")
        return False

def get_active_strategies():
    """获取当前活跃的策略列表"""
    try:
        resp = requests.get(f"{REGISTRY_URL}/list", timeout=5)
        result = resp.json()
        return result.get('strategies', [])
    except Exception as e:
        print(f"❌ 获取策略列表失败：{e}")
        return []

def is_strategy_running(symbol: str):
    """检查策略是否在运行"""
    strategies = get_active_strategies()
    return any(s.get('symbol') == symbol for s in strategies)
