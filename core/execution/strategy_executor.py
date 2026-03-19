#!/usr/bin/env python3
"""
🦞 策略执行器

功能:
    - 策略信号→开单
    - 杠杆和金额严格控制
    - 互斥检查
    - 跟车止损
    - 策略关闭→平仓 + 取消止损

完整生命周期:
    1. 启动策略 → 互斥检查 → 开单 → 注册 → 监控止损 → 跟车
    2. 策略信号 → 执行开单/平仓
    3. 关闭策略 → 平仓 → 取消止损 → 注销
"""

import time
from decimal import Decimal
from typing import Dict, Optional, Callable
from datetime import datetime

from modules.utils.logger import setup_logger
from modules.utils.result import Result, ok, fail
from modules.interfaces.execution import IExecutionEngine

from .position_calculator import PositionCalculator, get_calculator
from .trailing_stop import TrailingStop, get_trailing_stop
from .stop_loss_manager import StopLossManager
from ..risk.mutual_exclusion import MutualExclusion, get_exclusion

logger = setup_logger("strategy_executor", log_file="logs/strategy_executor.log")


class StrategyExecutor:
    """策略执行器"""
    
    def __init__(self, connector: IExecutionEngine):
        """
        初始化执行器
        
        Args:
            connector: 币安连接器
        """
        self.connector = connector
        
        # 初始化子模块
        self.calculator = get_calculator(connector)
        self.exclusion = get_exclusion()
        self.stop_loss_manager = StopLossManager(connector)
        self.trailing_stop = get_trailing_stop(self.stop_loss_manager, connector)
        
        # 策略状态
        self.active_strategies = {}  # {symbol: strategy_info}
    
    def start_strategy(
        self,
        symbol: str,
        strategy_name: str,
        leverage: int,
        amount_usd: float,
        stop_loss_pct: float,
        trailing_stop_pct: float = 0.02,
        signal_callback: Optional[Callable] = None
    ) -> Result:
        """
        启动策略
        
        完整流程:
        1. 互斥检查
        2. 获取当前价格
        3. 设置杠杆
        4. 计算仓位
        5. 开单
        6. 创建止损单
        7. 注册策略
        8. 启动跟车止损
        
        Args:
            symbol: 币种
            strategy_name: 策略名称
            leverage: 杠杆倍数
            amount_usd: 投资金额
            stop_loss_pct: 止损百分比
            trailing_stop_pct: 跟车止损百分比
            signal_callback: 信号回调函数
            
        Returns:
            Result: 执行结果
        """
        logger.info(f"🚀 启动策略：{symbol} - {strategy_name}")
        
        try:
            # 1. 互斥检查
            logger.info("【1】互斥检查...")
            if not self.exclusion.check_symbol_exclusive(symbol):
                return fail(f"{symbol} 已有策略运行，拒绝启动")
            logger.info("✅ 互斥检查通过")
            
            # 2. 获取当前价格
            logger.info("【2】获取当前价格...")
            price_data = self.connector.get_mark_price(symbol)
            current_price = Decimal(str(price_data['markPrice']))
            logger.info(f"✅ 当前价格：${current_price}")
            
            # 3. 设置杠杆
            logger.info("【3】设置杠杆...")
            leverage_result = self.connector.set_leverage(symbol, leverage)
            if not leverage_result.get('success'):
                return fail(f"设置杠杆失败：{leverage_result}")
            logger.info(f"✅ 杠杆已设置：{leverage}x")
            
            # 4. 计算仓位
            logger.info("【4】计算仓位...")
            quantity = self.calculator.calculate_position_size(
                Decimal(str(amount_usd)),
                leverage,
                current_price,
                symbol
            )
            position_value = Decimal(str(amount_usd)) * leverage
            logger.info(f"✅ 仓位计算：{quantity} {symbol.replace('USDT', '')} (${position_value})")
            
            # 5. 开单
            logger.info("【5】开单...")
            order_result = self.connector.open_position(
                symbol=symbol,
                side='BUY',
                quantity=quantity,
                order_type='MARKET'
            )
            if not order_result.get('success'):
                return fail(f"开单失败：{order_result}")
            
            entry_price = Decimal(str(order_result['avgPrice']))
            logger.info(f"✅ 开单成功：{quantity} @ {entry_price}")
            
            # 6. 创建止损单
            logger.info("【6】创建止损单...")
            stop_price = entry_price * (1 - Decimal(str(stop_loss_pct)))
            stop_result = self.stop_loss_manager.create_stop_loss(
                symbol=symbol,
                stop_price=stop_price,
                quantity=quantity
            )
            if not stop_result.get('success'):
                logger.warning(f"⚠️ 止损单创建失败：{stop_result}")
            else:
                logger.info(f"✅ 止损单已创建：{stop_price}")
            
            # 7. 注册策略
            logger.info("【7】注册策略...")
            strategy_info = {
                'symbol': symbol,
                'strategy': strategy_name,
                'leverage': leverage,
                'amount_usd': amount_usd,
                'entry_price': float(entry_price),
                'quantity': float(quantity),
                'stop_loss_pct': stop_loss_pct,
                'start_time': datetime.now().isoformat(),
                'status': 'running'
            }
            self.active_strategies[symbol] = strategy_info
            logger.info(f"✅ 策略已注册")
            
            # 8. 启动跟车止损
            logger.info("【8】启动跟车止损...")
            self.trailing_stop.start_trailing(
                symbol=symbol,
                entry_price=entry_price,
                initial_stop_price=stop_price,
                trailing_pct=Decimal(str(trailing_stop_pct))
            )
            logger.info(f"✅ 跟车止损已启动 ({trailing_stop_pct*100}%)")
            
            logger.info(f"🎉 {symbol} 策略启动完成！")
            return ok(strategy_info)
            
        except Exception as e:
            logger.error(f"❌ 启动策略失败：{e}", exc_info=True)
            return fail(f"启动策略失败：{str(e)}")
    
    def stop_strategy(self, symbol: str, close_position: bool = True) -> Result:
        """
        停止策略
        
        流程:
        1. 停止跟车止损
        2. 取消止损单
        3. 平仓（可选）
        4. 注销策略
        
        Args:
            symbol: 币种
            close_position: 是否平仓
            
        Returns:
            Result: 执行结果
        """
        logger.info(f"⏹️ 停止策略：{symbol}")
        
        try:
            # 1. 停止跟车止损
            logger.info("【1】停止跟车止损...")
            self.trailing_stop.stop_trailing(symbol)
            logger.info("✅ 跟车止损已停止")
            
            # 2. 取消止损单
            logger.info("【2】取消止损单...")
            self.stop_loss_manager.cancel_stop_loss(symbol)
            logger.info("✅ 止损单已取消")
            
            # 3. 平仓
            if close_position:
                logger.info("【3】平仓...")
                position = self.connector.get_position(symbol)
                if position and float(position['positionAmt']) != 0:
                    quantity = abs(Decimal(position['positionAmt']))
                    close_result = self.connector.close_position(symbol, quantity)
                    if close_result.get('success'):
                        logger.info(f"✅ 平仓成功：{quantity} @ {close_result['avgPrice']}")
                    else:
                        logger.warning(f"⚠️ 平仓失败：{close_result}")
                else:
                    logger.info("ℹ️ 无持仓")
            
            # 4. 注销策略
            logger.info("【4】注销策略...")
            if symbol in self.active_strategies:
                del self.active_strategies[symbol]
            self.exclusion.unregister_strategy(symbol)
            logger.info("✅ 策略已注销")
            
            logger.info(f"🎉 {symbol} 策略停止完成！")
            return ok({'symbol': symbol, 'status': 'stopped'})
            
        except Exception as e:
            logger.error(f"❌ 停止策略失败：{e}", exc_info=True)
            return fail(f"停止策略失败：{str(e)}")
    
    def execute_signal(
        self,
        symbol: str,
        signal_type: str,
        signal_data: Dict
    ) -> Result:
        """
        执行策略信号
        
        Args:
            symbol: 币种
            signal_type: 信号类型 (BUY/SELL/CLOSE)
            signal_data: 信号数据
            
        Returns:
            Result: 执行结果
        """
        logger.info(f"📡 执行信号：{symbol} - {signal_type}")
        
        try:
            if signal_type == 'BUY':
                return self._execute_buy(symbol, signal_data)
            elif signal_type == 'SELL':
                return self._execute_sell(symbol, signal_data)
            elif signal_type == 'CLOSE':
                return self._execute_close(symbol, signal_data)
            else:
                return fail(f"未知信号类型：{signal_type}")
                
        except Exception as e:
            logger.error(f"❌ 执行信号失败：{e}", exc_info=True)
            return fail(f"执行信号失败：{str(e)}")
    
    def _execute_buy(self, symbol: str, signal_data: Dict) -> Result:
        """执行买入信号"""
        # 获取策略配置
        if symbol not in self.active_strategies:
            return fail(f"{symbol} 策略未启动")
        
        strategy = self.active_strategies[symbol]
        leverage = strategy['leverage']
        amount = strategy['amount_usd']
        
        # 获取价格
        price_data = self.connector.get_mark_price(symbol)
        price = Decimal(str(price_data['markPrice']))
        
        # 计算仓位
        quantity = self.calculator.calculate_position_size(
            Decimal(str(amount)),
            leverage,
            price,
            symbol
        )
        
        # 开单
        result = self.connector.open_position(symbol, 'BUY', quantity, 'MARKET')
        return ok(result) if result.get('success') else fail(result)
    
    def _execute_sell(self, symbol: str, signal_data: Dict) -> Result:
        """执行卖出信号"""
        # 获取持仓
        position = self.connector.get_position(symbol)
        if not position or float(position['positionAmt']) == 0:
            return fail(f"{symbol} 无持仓")
        
        quantity = abs(Decimal(position['positionAmt']))
        result = self.connector.close_position(symbol, quantity)
        return ok(result) if result.get('success') else fail(result)
    
    def _execute_close(self, symbol: str, signal_data: Dict) -> Result:
        """执行平仓信号"""
        return self.stop_strategy(symbol, close_position=True)
    
    def get_strategy_status(self, symbol: str) -> Optional[Dict]:
        """获取策略状态"""
        return self.active_strategies.get(symbol)
    
    def get_all_strategies(self) -> Dict:
        """获取所有策略"""
        return self.active_strategies.copy()


# 全局单例
_executor = None

def get_executor(connector) -> StrategyExecutor:
    """获取执行器单例"""
    global _executor
    if _executor is None:
        _executor = StrategyExecutor(connector)
    return _executor


if __name__ == "__main__":
    # 测试
    print("=== 策略执行器测试 ===\n")
    print("此模块需要币安连接器才能运行")
    print("请参考文档进行集成测试")
