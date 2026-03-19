#!/usr/bin/env python3
"""
🦞 策略互斥检查模块

功能:
    - 同一币种同时只能运行 1 个策略
    - 启动前检查是否有策略已在运行
    - 防止重复开仓
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

REGISTRY_FILE = Path("/root/.openclaw/workspace/quant/v3-architecture/logs/strategy_registry.json")


class MutualExclusion:
    """策略互斥检查器"""
    
    def __init__(self):
        self.registry_file = REGISTRY_FILE
        self.registry = self.load()
    
    def load(self) -> Dict:
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
    
    def check_symbol_exclusive(self, symbol: str) -> bool:
        """
        检查币种是否已有策略运行
        
        Args:
            symbol: 币种名称 (如 ETHUSDT)
            
        Returns:
            bool: True=可以启动，False=已有策略运行
        """
        running = self.get_running_strategies()
        
        # 检查该币种是否已有策略
        if symbol in running:
            strategy_info = running[symbol]
            print(f"❌ {symbol} 已有策略运行:")
            print(f"   策略：{strategy_info.get('config', {}).get('strategy', 'unknown')}")
            print(f"   PID: {strategy_info.get('pid', 'N/A')}")
            print(f"   启动时间：{strategy_info.get('start_time', 'N/A')}")
            return False
        
        return True
    
    def get_running_strategies(self) -> Dict:
        """获取所有运行中的策略"""
        return {
            symbol: info for symbol, info in self.registry.items()
            if info.get('status') == 'running'
        }
    
    def register_strategy(self, symbol: str, pid: int, config: dict):
        """注册策略"""
        self.registry[symbol] = {
            'status': 'running',
            'pid': pid,
            'config': config,
            'start_time': datetime.now().isoformat(),
            'last_heartbeat': datetime.now().isoformat()
        }
        self.save()
        print(f"✅ {symbol} 策略已注册 (PID: {pid})")
    
    def unregister_strategy(self, symbol: str):
        """注销策略"""
        if symbol in self.registry:
            del self.registry[symbol]
            self.save()
            print(f"✅ {symbol} 策略已注销")
    
    def update_heartbeat(self, symbol: str):
        """更新心跳"""
        if symbol in self.registry:
            self.registry[symbol]['last_heartbeat'] = datetime.now().isoformat()
            self.save()
    
    def check_alive(self, timeout_seconds: int = 120) -> list:
        """检查存活状态，返回死亡策略列表"""
        now = datetime.now()
        dead_symbols = []
        
        for symbol, info in self.registry.items():
            if info.get('status') != 'running':
                continue
            
            last_heartbeat = datetime.fromisoformat(info['last_heartbeat'])
            if (now - last_heartbeat).total_seconds() > timeout_seconds:
                dead_symbols.append(symbol)
        
        return dead_symbols


# 全局单例
_exclusion = None

def get_exclusion() -> MutualExclusion:
    """获取互斥检查器单例"""
    global _exclusion
    if _exclusion is None:
        _exclusion = MutualExclusion()
    return _exclusion


def check_mutual_exclusion(symbol: str) -> bool:
    """
    检查策略互斥
    
    Args:
        symbol: 币种名称
        
    Returns:
        bool: True=可以启动，False=已有策略运行
    """
    return get_exclusion().check_symbol_exclusive(symbol)


if __name__ == "__main__":
    # 测试
    exclusion = MutualExclusion()
    
    print("=== 测试策略互斥检查 ===\n")
    
    # 测试 ETHUSDT
    symbol = "ETHUSDT"
    can_start = exclusion.check_symbol_exclusive(symbol)
    print(f"{symbol}: {'✅ 可以启动' if can_start else '❌ 已有策略运行'}\n")
    
    # 显示所有运行中的策略
    running = exclusion.get_running_strategies()
    print(f"运行中的策略：{len(running)} 个")
    for sym, info in running.items():
        print(f"  - {sym}: {info.get('config', {}).get('strategy', 'unknown')}")
