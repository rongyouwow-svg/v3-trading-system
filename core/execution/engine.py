#!/usr/bin/env python3
"""
💼 执行引擎 v3.1

职责:
    - 订单管理（统一订单接口）
    - 止损单管理（开仓后立即创建）
    - 持仓同步（从交易所获取真实持仓）
    - 策略信号执行

特性:
    - 开仓后立即创建止损单
    - 5% 硬止损兜底（策略无止损配置时）
    - 止损单查重（避免重复创建）
    - 分批建仓止损单自动更新
    - 持仓自动同步

用法:
    from core.execution.engine import ExecutionEngine
    
    engine = ExecutionEngine(connector)
    engine.execute_open_signal(signal)
    engine.execute_close_signal(signal)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    执行引擎
    
    核心功能:
        - 订单管理
        - 止损单管理（开仓后立即创建）
        - 持仓同步
        - 策略信号执行
    """
    
    def __init__(self, connector: Any):
        """
        初始化执行引擎
        
        Args:
            connector: 币安连接器
        """
        self.connector = connector
        
        # 管理器初始化
        from core.execution.order_manager import OrderManager
        from core.execution.stop_loss_manager import StopLossManager
        from core.execution.position_manager import PositionManager
        
        self.order_manager = OrderManager(connector)
        self.stop_loss_manager = StopLossManager(connector)
        self.position_manager = PositionManager(connector)
        
        # 策略注册表（由 StrategyManager 管理）
        self.strategies: Dict[str, Any] = {}
        
        logger.info("✅ 执行引擎初始化完成")
        logger.info("  - 订单管理器：已初始化")
        logger.info("  - 止损管理器：已初始化")
        logger.info("  - 持仓管理器：已初始化")
    
    def execute_open_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行开仓信号
        
        Args:
            signal: 开仓信号
                {
                    'symbol': 'ETHUSDT',
                    'quantity': 0.15,
                    'stop_loss_pct': 0.002,  # None 表示使用 5% 兜底
                    ...
                }
        
        Returns:
            执行结果
        """
        symbol = signal.get('symbol')
        quantity = signal.get('quantity')
        stop_loss_pct = signal.get('stop_loss_pct')  # None 表示使用 5% 兜底
        
        logger.info(f"🚀 执行开仓信号：{symbol} x {quantity}")
        
        # 1. 开仓
        order_result = self.order_manager.place_order(
            symbol=symbol,
            side='BUY',
            quantity=quantity,
            order_type='MARKET'
        )
        
        if not order_result.get('success'):
            logger.error(f"❌ 开仓失败：{order_result.get('error')}")
            return order_result
        
        logger.info(f"✅ 开仓成功：{order_result}")
        
        # 2. 开仓成功 → 立即获取持仓
        position = self.position_manager.sync_position(symbol)
        
        if not position:
            logger.error(f"❌ 获取持仓失败：{symbol}")
            return {'success': False, 'error': '获取持仓失败'}
        
        logger.info(f"📊 获取持仓成功：{position}")
        
        # 3. 立即创建止损单（带 5% 兜底逻辑）
        actual_stop_loss_pct = stop_loss_pct if stop_loss_pct is not None else 0.05  # 5% 兜底
        
        stop_loss_result = self.stop_loss_manager.create_stop_loss(
            symbol=symbol,
            quantity=position['size'],
            entry_price=position['entry_price'],
            stop_loss_pct=actual_stop_loss_pct
        )
        
        if stop_loss_result.get('success'):
            logger.info(f"✅ 止损单创建成功：{actual_stop_loss_pct*100}% ({'策略止损' if stop_loss_pct else '5% 兜底'})")
        else:
            logger.error(f"❌ 止损单创建失败：{stop_loss_result.get('error')}")
        
        # 4. 返回结果
        return {
            'success': True,
            'order': order_result,
            'position': position,
            'stop_loss': stop_loss_result,
            'message': f'开仓成功，止损单已创建 ({actual_stop_loss_pct*100}%)'
        }
    
    def execute_close_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行平仓信号
        
        Args:
            signal: 平仓信号
                {
                    'symbol': 'ETHUSDT',
                    'quantity': 0.15,  # 可选，不传则全平
                    ...
                }
        
        Returns:
            执行结果
        """
        symbol = signal.get('symbol')
        quantity = signal.get('quantity')
        
        logger.info(f"📉 执行平仓信号：{symbol} x {quantity or 'ALL'}")
        
        # 1. 获取持仓
        position = self.position_manager.sync_position(symbol)
        
        if not position or position['size'] == 0:
            logger.warning(f"⚠️ 无持仓，跳过平仓：{symbol}")
            return {'success': False, 'error': '无持仓'}
        
        # 2. 平仓（全平或部分平仓）
        close_quantity = quantity if quantity else position['size']
        
        order_result = self.order_manager.place_order(
            symbol=symbol,
            side='SELL',
            quantity=close_quantity,
            order_type='MARKET',
            reduce_only=True
        )
        
        if not order_result.get('success'):
            logger.error(f"❌ 平仓失败：{order_result.get('error')}")
            return order_result
        
        logger.info(f"✅ 平仓成功：{order_result}")
        
        # 3. 平仓成功 → 取消止损单
        cancel_result = self.stop_loss_manager.cancel_stop_loss_by_symbol(symbol)
        
        if cancel_result.get('success'):
            logger.info(f"✅ 止损单已取消：{symbol}")
        else:
            logger.warning(f"⚠️ 止损单取消失败：{cancel_result.get('error')}")
        
        # 4. 返回结果
        return {
            'success': True,
            'order': order_result,
            'cancel_stop_loss': cancel_result,
            'message': '平仓成功，止损单已取消'
        }
    
    def execute_update_position_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行持仓更新信号（分批建仓场景）
        
        Args:
            signal: 更新信号
                {
                    'symbol': 'AVAXUSDT',
                    'action': 'increase',  # increase/decrease
                    'quantity': 0.1,
                    'stop_loss_pct': 0.005,
                    ...
                }
        
        Returns:
            执行结果
        """
        symbol = signal.get('symbol')
        action = signal.get('action', 'increase')
        quantity = signal.get('quantity')
        stop_loss_pct = signal.get('stop_loss_pct', 0.05)
        
        logger.info(f"🔄 执行持仓更新信号：{symbol} {action} x {quantity}")
        
        # 1. 执行开仓/平仓
        if action == 'increase':
            result = self.execute_open_signal({
                'symbol': symbol,
                'quantity': quantity,
                'stop_loss_pct': stop_loss_pct
            })
        else:  # decrease
            result = self.execute_close_signal({
                'symbol': symbol,
                'quantity': quantity
            })
        
        # 2. 分批建仓时，止损单会自动更新（StopLossManager 内部逻辑）
        
        return result
    
    def check_position_limit(self, symbol: str, amount: float, leverage: int) -> bool:
        """
        检查仓位限制（105% 上限）
        
        Args:
            symbol: 交易对
            amount: 计划开仓金额（USDT）
            leverage: 杠杆
        
        Returns:
            是否超过限制
        """
        # 获取当前持仓
        position = self.position_manager.sync_position(symbol)
        
        if not position:
            return True  # 无持仓，未超限
        
        # 计算当前仓位价值
        current_value = position['size'] * position['entry_price']
        
        # 计算允许最大仓位（105% 上限）
        max_value = amount * leverage * 1.05
        
        # 检查是否超限
        if current_value >= max_value:
            logger.warning(f"⚠️ 达到仓位上限：当前 {current_value:.2f} USDT, 上限 {max_value:.2f} USDT")
            return False
        
        logger.info(f"✅ 仓位检查通过：当前 {current_value:.2f} USDT, 上限 {max_value:.2f} USDT")
        return True
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        获取所有持仓
        
        Returns:
            持仓列表
        """
        return self.position_manager.get_all_positions()
    
    def get_all_stop_losses(self) -> List[Dict[str, Any]]:
        """
        获取所有止损单
        
        Returns:
            止损单列表
        """
        return self.stop_loss_manager.get_all_stop_losses()
    
    def register_strategy(self, name: str, strategy: Any):
        """
        注册策略（由 StrategyManager 调用）
        
        Args:
            name: 策略名称
            strategy: 策略实例
        """
        self.strategies[name] = strategy
        logger.info(f"✅ 策略 {name} 已注册")
    
    def unregister_strategy(self, name: str):
        """
        注销策略（由 StrategyManager 调用）
        
        Args:
            name: 策略名称
        """
        if name in self.strategies:
            del self.strategies[name]
            logger.info(f"✅ 策略 {name} 已注销")
    
    def shutdown(self):
        """
        关闭执行引擎
        """
        logger.info("🛑 关闭执行引擎")
        
        # 关闭管理器
        if hasattr(self.order_manager, 'shutdown'):
            self.order_manager.shutdown()
        
        if hasattr(self.stop_loss_manager, 'shutdown'):
            self.stop_loss_manager.shutdown()
        
        if hasattr(self.position_manager, 'shutdown'):
            self.position_manager.shutdown()
        
        logger.info("✅ 执行引擎已关闭")
