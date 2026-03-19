#!/usr/bin/env python3
"""
📝 策略注册中心

功能：
1. 策略启动时注册
2. 策略停止时注销
3. 查询活跃策略列表
"""

import json
import os
from datetime import datetime

REGISTRY_FILE = "/root/.openclaw/workspace/quant/v3-architecture/logs/strategy_registry.json"

def load_registry():
    """加载注册表"""
    try:
        with open(REGISTRY_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'strategies': {}} if os.path.exists(REGISTRY_FILE) else {'strategies': {}}

def save_registry(data):
    """保存注册表"""
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def register_strategy(symbol, pid=None, leverage=1, amount=0, script=''):
    """注册策略"""
    import os
    if pid is None:
        pid = os.getpid()
    
    registry = load_registry()
    registry['strategies'][symbol] = {
        'symbol': symbol,
        'pid': pid,
        'leverage': leverage,
        'amount': amount,
        'script': script,
        'start_time': datetime.now().isoformat(),
        'status': 'running'
    }
    save_registry(registry)
    print(f"✅ 策略已注册：{symbol} (PID: {pid})")
    return True

def unregister_strategy(symbol):
    """注销策略"""
    registry = load_registry()
    if symbol in registry['strategies']:
        del registry['strategies'][symbol]
        save_registry(registry)
        print(f"✅ 策略已注销：{symbol}")
        return True
    return False

def get_active_strategies():
    """获取活跃策略列表"""
    registry = load_registry()
    return list(registry['strategies'].values())

def is_strategy_running(symbol):
    """检查策略是否运行"""
    registry = load_registry()
    return symbol in registry['strategies']

if __name__ == '__main__':
    # 测试
    print("策略注册中心测试")
    register_strategy('TEST', pid=12345)
    print(f"活跃策略：{get_active_strategies()}")
    unregister_strategy('TEST')
