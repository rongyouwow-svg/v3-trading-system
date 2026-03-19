#!/usr/bin/env python3
"""
🦞 状态同步器 v3.0

职责:
    - 定期全量同步（每 5 分钟）
    - 事件驱动增量同步
    - 冲突检测与解决
    - 状态恢复

特性:
    - 双缓冲机制
    - 版本号控制
    - 以交易所为准
    - 自动修复

用法:
    from core.sync.state_sync import StateSync
    
    sync = StateSync(connector)
    sync.start()
"""

import json
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from threading import Thread, Lock

from modules.utils.logger import setup_logger
from modules.utils.decorators import handle_exceptions, log_execution
from modules.utils.result import Result

logger = setup_logger("state_sync", log_file="logs/state_sync.log")


class StateSync:
    """
    状态同步器
    
    核心功能:
        - 定期全量同步
        - 事件驱动增量同步
        - 冲突检测与解决
        - 状态恢复
    """
    
    # 同步配置
    FULL_SYNC_INTERVAL = 300  # 5 分钟（秒）
    INCREMENTAL_SYNC_INTERVAL = 30  # 30 秒
    
    def __init__(self, connector, db_manager=None):
        """
        初始化状态同步器
        
        Args:
            connector: 交易所连接器
            db_manager: 数据库管理器（可选）
        """
        self.connector = connector
        self.db_manager = db_manager
        
        # 运行标志
        self.running = False
        
        # 同步线程
        self.full_sync_thread = None
        self.incremental_sync_thread = None
        
        # 状态存储
        self.local_state: Dict[str, Any] = {}
        self.remote_state: Dict[str, Any] = {}
        
        # 版本号
        self.version: int = 0
        
        # 锁
        self.state_lock = Lock()
        
        # 同步统计
        self.sync_count = 0
        self.last_full_sync = None
        self.last_incremental_sync = None
        
        # 持久化文件
        self.persistence_file = "/root/.openclaw/workspace/quant/v3-architecture/data/state_sync.json"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
        
        # 加载本地状态
        self._load_state()
        
        logger.info("状态同步器初始化完成")
    
    def start(self):
        """启动状态同步"""
        if self.running:
            logger.warning("⚠️ 状态同步器已在运行中")
            return
        
        self.running = True
        
        # 启动全量同步线程
        self.full_sync_thread = Thread(target=self._full_sync_loop, daemon=True)
        self.full_sync_thread.start()
        
        # 启动增量同步线程
        self.incremental_sync_thread = Thread(target=self._incremental_sync_loop, daemon=True)
        self.incremental_sync_thread.start()
        
        logger.info("✅ 状态同步器已启动")
    
    def stop(self):
        """停止状态同步"""
        if not self.running:
            return
        
        self.running = False
        
        # 保存状态
        self._save_state()
        
        logger.info("🛑 状态同步器已停止")
    
    def _full_sync_loop(self):
        """
        全量同步循环
        
        说明:
            - 每 5 分钟执行一次
            - 从交易所获取完整状态
            - 检测并解决冲突
            - 更新本地状态
        """
        logger.info("🔄 全量同步线程已启动")
        
        while self.running:
            try:
                # 执行全量同步
                self._do_full_sync()
                
                # 等待下一次同步
                for _ in range(self.FULL_SYNC_INTERVAL):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ 全量同步异常：{e}")
                time.sleep(10)
        
        logger.info("🛑 全量同步线程已停止")
    
    def _incremental_sync_loop(self):
        """
        增量同步循环
        
        说明:
            - 每 30 秒执行一次
            - 只同步变化的部分
            - 快速检测冲突
        """
        logger.info("🔄 增量同步线程已启动")
        
        while self.running:
            try:
                # 执行增量同步
                self._do_incremental_sync()
                
                # 等待下一次同步
                for _ in range(self.INCREMENTAL_SYNC_INTERVAL):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ 增量同步异常：{e}")
                time.sleep(5)
        
        logger.info("🛑 增量同步线程已停止")
    
    @handle_exceptions()
    @log_execution()
    def _do_full_sync(self):
        """执行全量同步"""
        logger.info("📊 开始全量同步...")
        
        # 1. 获取交易所状态
        remote_state = self._fetch_remote_state()
        
        if not remote_state:
            logger.warning("⚠️ 获取远程状态失败")
            return
        
        # 2. 检测冲突
        conflicts = self._detect_conflicts(remote_state)
        
        if conflicts:
            logger.warning(f"⚠️ 检测到 {len(conflicts)} 个冲突")
            # 3. 解决冲突（以交易所为准）
            self._resolve_conflicts(conflicts, remote_state)
        
        # 4. 更新本地状态
        with self.state_lock:
            self.local_state = remote_state.copy()
            self.version += 1
        
        # 5. 持久化
        self._save_state()
        
        # 6. 更新统计
        self.sync_count += 1
        self.last_full_sync = datetime.now()
        
        logger.info(f"✅ 全量同步完成（版本：{self.version}）")
    
    @handle_exceptions()
    @log_execution()
    def _do_incremental_sync(self):
        """执行增量同步"""
        logger.debug("📊 开始增量同步...")
        
        # 1. 获取关键状态
        remote_state = self._fetch_key_state()
        
        if not remote_state:
            logger.debug("⚠️ 获取远程状态失败")
            return
        
        # 2. 检测变化
        changes = self._detect_changes(remote_state)
        
        if changes:
            logger.info(f"📝 检测到 {len(changes)} 个变化")
            
            # 3. 应用变化
            with self.state_lock:
                for key, value in changes.items():
                    self.local_state[key] = value
                self.version += 1
        
        # 4. 更新统计
        self.last_incremental_sync = datetime.now()
        
        logger.debug(f"✅ 增量同步完成（变化：{len(changes) if changes else 0}）")
    
    def _fetch_remote_state(self) -> Optional[Dict]:
        """
        获取远程状态
        
        Returns:
            Optional[Dict]: 远程状态
        """
        try:
            # 1. 获取账户余额
            balance_result = self.connector.get_account_balance()
            
            # 2. 获取持仓
            positions_result = self.connector.get_positions()
            
            # 3. 获取订单
            # orders_result = self.connector.get_open_orders()
            
            # 4. 获取止损单
            # stop_orders_result = self.connector.get_stop_orders()
            
            state = {
                'balance': balance_result.data if balance_result.is_success else {},
                'positions': positions_result.data.get('positions', []) if positions_result.is_success else [],
                # 'orders': orders_result.data.get('orders', []) if orders_result.is_success else [],
                # 'stop_orders': stop_orders_result.data.get('stop_orders', []) if stop_orders_result.is_success else [],
                'sync_time': datetime.now().isoformat(),
                'source': 'exchange'
            }
            
            return state
            
        except Exception as e:
            logger.error(f"❌ 获取远程状态失败：{e}")
            return None
    
    def _fetch_key_state(self) -> Optional[Dict]:
        """
        获取关键状态（用于增量同步）
        
        Returns:
            Optional[Dict]: 关键状态
        """
        try:
            # 只获取关键数据（余额、持仓）
            balance_result = self.connector.get_account_balance()
            positions_result = self.connector.get_positions()
            
            state = {
                'balance': balance_result.data if balance_result.is_success else {},
                'positions': positions_result.data.get('positions', []) if positions_result.is_success else [],
                'sync_time': datetime.now().isoformat()
            }
            
            return state
            
        except Exception as e:
            logger.error(f"❌ 获取关键状态失败：{e}")
            return None
    
    def _detect_conflicts(self, remote_state: Dict) -> List[Dict]:
        """
        检测冲突
        
        Args:
            remote_state (Dict): 远程状态
        
        Returns:
            List[Dict]: 冲突列表
        """
        conflicts = []
        
        with self.state_lock:
            # 检测持仓冲突
            local_positions = {p['symbol']: p for p in self.local_state.get('positions', [])}
            remote_positions = {p['symbol']: p for p in remote_state.get('positions', [])}
            
            for symbol, remote_pos in remote_positions.items():
                local_pos = local_positions.get(symbol)
                
                if local_pos:
                    # 比较关键字段
                    if abs(float(local_pos.get('size', 0)) - float(remote_pos.get('size', 0))) > 0.001:
                        conflicts.append({
                            'type': 'position',
                            'symbol': symbol,
                            'local': local_pos,
                            'remote': remote_pos
                        })
        
        return conflicts
    
    def _resolve_conflicts(self, conflicts: List[Dict], remote_state: Dict):
        """
        解决冲突
        
        Args:
            conflicts (List[Dict]): 冲突列表
            remote_state (Dict): 远程状态
        """
        logger.info(f"🔧 开始解决 {len(conflicts)} 个冲突...")
        
        for conflict in conflicts:
            if conflict['type'] == 'position':
                # 以交易所为准
                logger.info(f"  💡 持仓冲突：{conflict['symbol']} - 以交易所为准")
        
        # 直接采用远程状态
        logger.info("✅ 冲突解决完成")
    
    def _detect_changes(self, remote_state: Dict) -> Dict:
        """
        检测变化
        
        Args:
            remote_state (Dict): 远程状态
        
        Returns:
            Dict: 变化数据
        """
        changes = {}
        
        with self.state_lock:
            # 检测余额变化
            local_balance = self.local_state.get('balance', {})
            remote_balance = remote_state.get('balance', {})
            
            if local_balance != remote_balance:
                changes['balance'] = remote_balance
            
            # 检测持仓变化
            local_positions = {p['symbol']: p for p in self.local_state.get('positions', [])}
            remote_positions = {p['symbol']: p for p in remote_state.get('positions', [])}
            
            if set(local_positions.keys()) != set(remote_positions.keys()):
                changes['positions'] = remote_state.get('positions', [])
            else:
                # 检查持仓数据是否变化
                for symbol in local_positions:
                    if local_positions[symbol] != remote_positions.get(symbol):
                        changes['positions'] = remote_state.get('positions', [])
                        break
        
        return changes
    
    def _load_state(self):
        """从持久化文件加载状态"""
        if not os.path.exists(self.persistence_file):
            logger.debug("持久化文件不存在，使用空状态")
            return
        
        try:
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.local_state = data.get('local_state', {})
            self.version = data.get('version', 0)
            
            logger.info(f"📊 加载状态成功（版本：{self.version}）")
            
        except Exception as e:
            logger.error(f"⚠️ 加载状态失败：{e}")
    
    def _save_state(self):
        """保存状态到持久化文件"""
        try:
            data = {
                'local_state': self.local_state,
                'version': self.version,
                'sync_count': self.sync_count,
                'last_full_sync': self.last_full_sync.isoformat() if self.last_full_sync else None,
                'last_incremental_sync': self.last_incremental_sync.isoformat() if self.last_incremental_sync else None
            }
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"📝 已保存状态（版本：{self.version}）")
            
        except Exception as e:
            logger.error(f"❌ 保存状态失败：{e}")
    
    def get_state(self, key: Optional[str] = None) -> Any:
        """
        获取状态
        
        Args:
            key (str, optional): 状态键
        
        Returns:
            Any: 状态数据
        """
        with self.state_lock:
            if key:
                return self.local_state.get(key)
            return self.local_state.copy()
    
    def get_sync_statistics(self) -> Dict:
        """
        获取同步统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'sync_count': self.sync_count,
            'version': self.version,
            'last_full_sync': self.last_full_sync.isoformat() if self.last_full_sync else None,
            'last_incremental_sync': self.last_incremental_sync.isoformat() if self.last_incremental_sync else None,
            'is_running': self.running
        }


# 全局实例
_state_sync: Optional[StateSync] = None


def get_state_sync(connector=None, db_manager=None) -> StateSync:
    """获取全局状态同步器实例"""
    global _state_sync
    if _state_sync is None:
        if connector is None:
            raise ValueError("首次调用需要提供 connector 参数")
        _state_sync = StateSync(connector, db_manager)
    return _state_sync


def reset_state_sync():
    """重置状态同步器（测试用）"""
    global _state_sync
    _state_sync = None
