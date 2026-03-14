#!/usr/bin/env python3
"""
🔄 状态同步层

职责:
    - 状态快照
    - 冲突解决
    - 状态恢复
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

import logging
logger = logging.getLogger(__name__)


class StateSync:
    """状态同步器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.state_file = os.path.join(data_dir, "state_sync.json")
        self.states: Dict[str, Any] = {}
        
        # 确保目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载状态
        self._load_state()
    
    def _load_state(self):
        """从文件加载状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.states = json.load(f)
                logger.info(f"✅ 状态已加载：{len(self.states)} 个")
            except Exception as e:
                logger.error(f"❌ 加载状态失败：{e}")
                self.states = {}
    
    def _save_state(self):
        """保存状态到文件"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.states, f, indent=2, ensure_ascii=False)
            logger.debug(f"📝 状态已保存：{len(self.states)} 个")
        except Exception as e:
            logger.error(f"❌ 保存状态失败：{e}")
    
    def update_state(self, key: str, value: Any, sync: bool = True):
        """
        更新状态
        
        Args:
            key: 状态键
            value: 状态值
            sync: 是否立即同步到文件
        """
        self.states[key] = {
            'value': value,
            'updated_at': datetime.now().isoformat(),
            'version': self.states.get(key, {}).get('version', 0) + 1
        }
        
        if sync:
            self._save_state()
    
    def get_state(self, key: str) -> Optional[Any]:
        """获取状态"""
        if key in self.states:
            return self.states[key]['value']
        return None
    
    def get_all_states(self) -> Dict[str, Any]:
        """获取所有状态"""
        return {k: v['value'] for k, v in self.states.items()}
    
    def delete_state(self, key: str, sync: bool = True):
        """删除状态"""
        if key in self.states:
            del self.states[key]
            if sync:
                self._save_state()
    
    def resolve_conflict(self, key: str, local_value: Any, remote_value: Any) -> Any:
        """
        解决状态冲突
        
        策略：以远程（交易所）数据为准
        
        Args:
            key: 状态键
            local_value: 本地值
            remote_value: 远程值
        
        Returns:
            最终值
        """
        logger.warning(f"⚠️ 状态冲突：{key}")
        logger.warning(f"  本地：{local_value}")
        logger.warning(f"  远程：{remote_value}")
        
        # 以远程数据为准
        return remote_value
    
    def create_snapshot(self, snapshot_name: str = "snapshot") -> str:
        """
        创建状态快照
        
        Args:
            snapshot_name: 快照名称
        
        Returns:
            快照文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_file = os.path.join(self.data_dir, f"{snapshot_name}_{timestamp}.json")
        
        try:
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(self.states, f, indent=2, ensure_ascii=False)
            logger.info(f"📸 快照已创建：{snapshot_file}")
            return snapshot_file
        except Exception as e:
            logger.error(f"❌ 创建快照失败：{e}")
            return ""
    
    def restore_snapshot(self, snapshot_file: str) -> bool:
        """
        恢复快照
        
        Args:
            snapshot_file: 快照文件路径
        
        Returns:
            是否成功
        """
        if not os.path.exists(snapshot_file):
            logger.error(f"❌ 快照文件不存在：{snapshot_file}")
            return False
        
        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                self.states = json.load(f)
            self._save_state()
            logger.info(f"✅ 快照已恢复：{snapshot_file}")
            return True
        except Exception as e:
            logger.error(f"❌ 恢复快照失败：{e}")
            return False
