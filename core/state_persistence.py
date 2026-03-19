#!/usr/bin/env python3
"""
🦞 状态持久化模块

功能:
- 定期保存策略状态
- 启动时恢复状态
- 防止进程崩溃状态丢失
"""

import json
import os
from datetime import datetime
from pathlib import Path

STATE_DIR = Path('/root/.openclaw/workspace/quant/v3-architecture/state')

class StatePersistence:
    """状态持久化管理器"""
    
    def __init__(self):
        self.state_dir = STATE_DIR
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def save_state(self, symbol: str, state: dict):
        """保存策略状态"""
        state['timestamp'] = datetime.now().isoformat()
        state_file = self.state_dir / f'{symbol}_state.json'
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"✅ {symbol} 状态已保存")
            return True
        except Exception as e:
            print(f"❌ 保存状态失败：{e}")
            return False
    
    def load_state(self, symbol: str) -> dict:
        """加载策略状态"""
        state_file = self.state_dir / f'{symbol}_state.json'
        
        try:
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                print(f"✅ {symbol} 状态已加载")
                return state
            else:
                print(f"⚠️ {symbol} 无历史状态")
                return {}
        except Exception as e:
            print(f"❌ 加载状态失败：{e}")
            return {}
    
    def save_all_states(self, states: dict):
        """保存所有策略状态"""
        for symbol, state in states.items():
            self.save_state(symbol, state)
    
    def load_all_states(self) -> dict:
        """加载所有策略状态"""
        states = {}
        for state_file in self.state_dir.glob('*_state.json'):
            symbol = state_file.stem.replace('_state', '')
            states[symbol] = self.load_state(symbol)
        return states
    
    def cleanup_old_states(self, days: int = 7):
        """清理旧状态文件"""
        import time
        cutoff = time.time() - (days * 86400)
        
        for state_file in self.state_dir.glob('*_state.json'):
            if state_file.stat().st_mtime < cutoff:
                state_file.unlink()
                print(f"🗑️ 已清理旧状态：{state_file.name}")

# 全局实例
state_manager = StatePersistence()
