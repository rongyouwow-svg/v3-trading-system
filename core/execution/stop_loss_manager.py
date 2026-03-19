#!/usr/bin/env python3
"""
🦞 止损单管理器 v3.0

职责:
    - 止损单创建（防重机制）
    - 止损单取消
    - 止损单状态监控
    - 动态精度获取

特性:
    - 防重复创建（creating 标志 + 数据库）
    - 动态精度获取（从交易所）
    - 重试机制
    - 超时清理

用法:
    from core.execution.stop_loss_manager import StopLossManager
    
    manager = StopLossManager(connector)
    result = manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'))
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import time
import json
import os

from modules.interfaces.execution import IExecutionEngine
from modules.utils.result import Result, ok, fail
from modules.utils.exceptions import (
    OrderCreateException,
    NetworkException
)
from modules.utils.logger import setup_logger
from modules.utils.decorators import handle_exceptions, log_execution, retry_on_exception
from modules.utils.precision import PrecisionUtils

logger = setup_logger("stop_loss_manager", log_file="logs/stop_loss_manager.log")


class StopLossManager:
    """
    止损单管理器
    
    核心功能:
        - 止损单创建（带防重机制）
        - 止损单取消
        - 止损单状态监控
        - 动态精度获取
    """
    
    # 持久化文件路径
    PERSISTENCE_FILE = "/root/.openclaw/workspace/quant/v3-architecture/data/stop_orders.json"
    
    def __init__(self, connector):
        """
        初始化止损单管理器
        
        Args:
            connector: 交易所连接器
        """
        self.connector = connector
        
        # 止损单存储 {algo_id: stop_order_data}
        self.stop_orders: Dict[str, Dict] = {}
        
        # 创建中标志（防重）{symbol: bool}
        self.creating: Dict[str, bool] = {}
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.PERSISTENCE_FILE), exist_ok=True)
        
        # 加载已有止损单
        self._load_stop_orders()
        
        logger.info("止损单管理器初始化完成")
    
    def _load_stop_orders(self):
        """从持久化文件加载止损单"""
        if not os.path.exists(self.PERSISTENCE_FILE):
            logger.debug("持久化文件不存在，跳过加载")
            return
        
        try:
            with open(self.PERSISTENCE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for algo_id, order_data in data.items():
                self.stop_orders[algo_id] = order_data
            
            logger.info(f"📊 加载了 {len(self.stop_orders)} 个止损单")
            
        except Exception as e:
            logger.error(f"⚠️ 加载止损单失败：{e}")
    
    def _save_stop_orders(self):
        """保存止损单到持久化文件"""
        try:
            with open(self.PERSISTENCE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.stop_orders, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"📝 已保存 {len(self.stop_orders)} 个止损单")
            
        except Exception as e:
            logger.error(f"❌ 保存止损单失败：{e}")
    
    @handle_exceptions()
    @log_execution()
    @retry_on_exception(max_retries=3, delay=1.0)
    def create_stop_loss(self, symbol: str, trigger_price: Decimal, quantity: Decimal, 
                        side: str = "SELL", stop_price: Optional[Decimal] = None) -> Result:
        """
        创建止损单
        
        Args:
            symbol (str): 交易对
            trigger_price (Decimal): 触发价格
            quantity (Decimal): 数量
            side (str): 方向（BUY/SELL）
            stop_price (Decimal, optional): 止损价格（限价止损单）
        
        Returns:
            Result: 操作结果
        
        Example:
            >>> result = manager.create_stop_loss('ETHUSDT', Decimal('2000'), Decimal('0.1'))
        """
        # 检查是否正在创建（防重机制）
        if self.creating.get(symbol, False):
            logger.warning(f"⚠️ {symbol} 止损单正在创建中，跳过")
            return fail(
                error_code="STOP_LOSS_CREATING",
                message=f"{symbol} 止损单正在创建中，请稍后再试"
            )
        
        try:
            # 设置创建中标志
            self.creating[symbol] = True
            
            # 1. 检查是否已有止损单
            existing = self._get_stop_order_by_symbol(symbol)
            if existing and existing.get('status') == 'WAIT_TO_TRIGGER':
                logger.warning(f"⚠️ {symbol} 已有活跃止损单")
                return fail(
                    error_code="STOP_LOSS_EXISTS",
                    message=f"{symbol} 已有活跃止损单"
                )
            
            # 2. 参数验证
            is_valid, error_msg = PrecisionUtils.validate_price(symbol, trigger_price)
            if not is_valid:
                return fail(error_code="INVALID_PRICE", message=error_msg)
            
            is_valid, error_msg = PrecisionUtils.validate_quantity(symbol, quantity)
            if not is_valid:
                return fail(error_code="INVALID_QUANTITY", message=error_msg)
            
            # 3. 标准化精度
            trigger_price = PrecisionUtils.normalize_price(symbol, trigger_price)
            quantity = PrecisionUtils.normalize_quantity(symbol, quantity)
            
            if stop_price:
                stop_price = PrecisionUtils.normalize_price(symbol, stop_price)
            
            logger.info(f"📝 创建止损单：{symbol} {side} 触发价={trigger_price} 数量={quantity}")
            
            # 4. 调用交易所创建止损单
            result = self.connector.create_stop_loss_order(symbol, side, quantity, trigger_price)
            
            if not result.is_success:
                logger.error(f"❌ 止损单创建失败：{result.message}")
                return result
            
            # 5. 存储止损单信息
            algo_id = result.data.get('algo_id') or result.data.get('order_id')
            stop_order = {
                'algo_id': algo_id,
                'symbol': symbol,
                'side': side,
                'trigger_price': str(trigger_price),
                'quantity': str(quantity),
                'stop_price': str(stop_price) if stop_price else None,
                'status': 'WAIT_TO_TRIGGER',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.stop_orders[algo_id] = stop_order
            self._save_stop_orders()
            
            logger.info(f"✅ 止损单创建成功：{algo_id}")
            
            return ok(
                data={
                    'algo_id': algo_id,
                    'symbol': symbol,
                    'trigger_price': str(trigger_price),
                    'quantity': str(quantity),
                    'status': 'WAIT_TO_TRIGGER'
                },
                message="止损单创建成功"
            )
            
        finally:
            # 清除创建中标志
            self.creating[symbol] = False
    
    @handle_exceptions()
    @log_execution()
    @retry_on_exception(max_retries=3, delay=1.0)
    def cancel_stop_loss(self, symbol: str, algo_id: str) -> Result:
        """
        取消止损单
        
        Args:
            symbol (str): 交易对
            algo_id (str): 止损单 ID
        
        Returns:
            Result: 操作结果
        """
        logger.info(f"🚫 取消止损单：{symbol} {algo_id}")
        
        # 1. 检查本地止损单
        if algo_id not in self.stop_orders:
            logger.warning(f"⚠️ 止损单 {algo_id} 不存在")
            return fail(
                error_code="STOP_LOSS_NOT_FOUND",
                message=f"止损单 {algo_id} 不存在"
            )
        
        stop_order = self.stop_orders[algo_id]
        if stop_order.get('status') in ['TRIGGERED', 'CANCELED']:
            logger.warning(f"⚠️ 止损单 {algo_id} 状态为 {stop_order['status']}，无法取消")
            return fail(
                error_code="STOP_LOSS_NOT_CANCELABLE",
                message=f"止损单状态为 {stop_order['status']}，无法取消"
            )
        
        # 2. 调用交易所取消
        result = self.connector.cancel_stop_loss_order(symbol, algo_id)
        
        if not result.is_success:
            logger.error(f"❌ 止损单取消失败：{result.message}")
            return result
        
        # 3. 更新本地状态
        stop_order['status'] = 'CANCELED'
        stop_order['updated_at'] = datetime.now().isoformat()
        self._save_stop_orders()
        
        logger.info(f"✅ 止损单取消成功：{algo_id}")
        
        return ok(
            data={'algo_id': algo_id, 'symbol': symbol, 'status': 'CANCELED'},
            message="止损单取消成功"
        )
    
    def get_stop_order(self, algo_id: str) -> Optional[Dict]:
        """
        获取止损单信息
        
        Args:
            algo_id (str): 止损单 ID
        
        Returns:
            Optional[Dict]: 止损单信息，不存在返回 None
        """
        return self.stop_orders.get(algo_id)
    
    def get_stop_orders_by_symbol(self, symbol: str) -> List[Dict]:
        """
        获取指定交易对的止损单
        
        Args:
            symbol (str): 交易对
        
        Returns:
            List[Dict]: 止损单列表
        """
        return [order for order in self.stop_orders.values() if order['symbol'] == symbol]
    
    def get_active_stop_orders(self) -> List[Dict]:
        """
        获取所有活跃止损单
        
        Returns:
            List[Dict]: 活跃止损单列表
        """
        return [
            order for order in self.stop_orders.values()
            if order.get('status') == 'WAIT_TO_TRIGGER'
        ]
    
    def _get_stop_order_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        获取指定交易对的第一个活跃止损单
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Optional[Dict]: 止损单信息
        """
        orders = self.get_stop_orders_by_symbol(symbol)
        active = [o for o in orders if o.get('status') == 'WAIT_TO_TRIGGER']
        return active[0] if active else None
    
    def update_stop_order_status(self, algo_id: str, status: str):
        """
        更新止损单状态
        
        Args:
            algo_id (str): 止损单 ID
            status (str): 新状态
        """
        if algo_id not in self.stop_orders:
            logger.warning(f"⚠️ 止损单 {algo_id} 不存在，无法更新状态")
            return
        
        self.stop_orders[algo_id]['status'] = status
        self.stop_orders[algo_id]['updated_at'] = datetime.now().isoformat()
        
        if status == 'TRIGGERED':
            self.stop_orders[algo_id]['triggered_at'] = datetime.now().isoformat()
        
        self._save_stop_orders()
        
        logger.debug(f"📊 止损单 {algo_id} 状态更新为 {status}")
    
    def cancel_all_stop_losses(self, symbol: str) -> Result:
        """
        取消指定交易对的所有止损单
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Result: 操作结果
        """
        orders = self.get_stop_orders_by_symbol(symbol)
        active = [o for o in orders if o.get('status') == 'WAIT_TO_TRIGGER']
        
        success_count = 0
        fail_count = 0
        
        for order in active:
            result = self.cancel_stop_loss(symbol, order['algo_id'])
            if result.is_success:
                success_count += 1
            else:
                fail_count += 1
        
        logger.info(f"🧹 取消 {symbol} 止损单：成功{success_count}个，失败{fail_count}个")
        
        return ok(
            data={'symbol': symbol, 'success_count': success_count, 'fail_count': fail_count},
            message=f"取消 {symbol} 止损单：成功{success_count}个，失败{fail_count}个"
        )
    
    def get_stop_loss_statistics(self) -> Dict:
        """
        获取止损单统计信息
        
        Returns:
            Dict: 统计信息
        """
        total = len(self.stop_orders)
        by_status = {}
        by_symbol = {}
        
        for order in self.stop_orders.values():
            # 按状态统计
            status = order.get('status', 'UNKNOWN')
            by_status[status] = by_status.get(status, 0) + 1
            
            # 按币种统计
            symbol = order.get('symbol', 'UNKNOWN')
            by_symbol[symbol] = by_symbol.get(symbol, 0) + 1
        
        return {
            'total_stop_orders': total,
            'by_status': by_status,
            'by_symbol': by_symbol,
            'active_stop_orders': len(self.get_active_stop_orders())
        }


# 全局实例
_stop_loss_manager: Optional[StopLossManager] = None


def get_stop_loss_manager(connector=None) -> StopLossManager:
    """获取全局止损单管理器实例"""
    global _stop_loss_manager
    if _stop_loss_manager is None:
        if connector is None:
            raise ValueError("首次调用需要提供 connector 参数")
        _stop_loss_manager = StopLossManager(connector)
    return _stop_loss_manager


def reset_stop_loss_manager():
    """重置止损单管理器（测试用）"""
    global _stop_loss_manager
    _stop_loss_manager = None
