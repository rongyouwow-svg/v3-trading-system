#!/usr/bin/env python3
"""
🦞 策略注册中心

功能：
1. 策略启动时自动注册
2. 策略停止时自动注销
3. 监控进程动态读取注册表
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

REGISTRY_FILE = Path("/root/.openclaw/workspace/quant/v3-architecture/logs/strategy_registry.json")


class StrategyRegistry:
    """策略注册中心"""
    
    def __init__(self):
        self.registry_file = REGISTRY_FILE
        self.registry = self.load()
    
    def load(self):
        """加载注册表"""
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save(self):
        """保存注册表"""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
    
    def register(self, symbol: str, pid: int, config: dict):
        """注册策略"""
        self.registry[symbol] = {
            'status': 'running',
            'pid': pid,
            'config': config,
            'start_time': datetime.now().isoformat(),
            'last_heartbeat': datetime.now().isoformat()
        }
        self.save()
        print(f"✅ 策略 {symbol} 已注册 (PID: {pid})")
    
    def unregister(self, symbol: str):
        """注销策略"""
        if symbol in self.registry:
            del self.registry[symbol]
            self.save()
            print(f"✅ 策略 {symbol} 已注销")
    
    def update_heartbeat(self, symbol: str):
        """更新心跳"""
        if symbol in self.registry:
            self.registry[symbol]['last_heartbeat'] = datetime.now().isoformat()
            self.save()
    
    def get_all(self):
        """获取所有策略"""
        return self.registry
    
    def get_running(self):
        """获取运行中的策略"""
        return {k: v for k, v in self.registry.items() if v.get('status') == 'running'}
    
    def check_alive(self, timeout_seconds=120):
        """检查存活状态（超过 timeout 无心跳视为死亡）"""
        now = datetime.now()
        dead_symbols = []
        
        for symbol, info in self.registry.items():
            if info.get('status') != 'running':
                continue
            
            last_heartbeat = datetime.fromisoformat(info['last_heartbeat'])
            if (now - last_heartbeat).total_seconds() > timeout_seconds:
                dead_symbols.append(symbol)
                self.registry[symbol]['status'] = 'dead'
        
        if dead_symbols:
            self.save()
        
        return dead_symbols


# 便捷函数
def register_strategy(symbol: str, pid: int, **kwargs):
    """注册策略（便捷函数）"""
    registry = StrategyRegistry()
    config = {
        'symbol': symbol,
        'leverage': kwargs.get('leverage', 3),
        'amount': kwargs.get('amount', 100),
        'script': kwargs.get('script', 'unknown.py')
    }
    registry.register(symbol, pid, config)


def unregister_strategy(symbol: str):
    """注销策略（便捷函数）"""
    registry = StrategyRegistry()
    registry.unregister(symbol)


def get_active_strategies():
    """获取活跃策略列表"""
    registry = StrategyRegistry()
    return registry.get_running()


if __name__ == '__main__':
    # 测试
    registry = StrategyRegistry()
    print("当前注册策略:")
    for symbol, info in registry.get_all().items():
        print(f"  {symbol}: {info['status']} (PID: {info.get('pid', 'N/A')})")
