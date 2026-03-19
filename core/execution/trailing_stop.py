#!/usr/bin/env python3
"""
🦞 跟车止损模块

功能:
    - 价格上移时自动上移止损
    - 价格下跌时保持止损不变
    - 防止盈利变亏损
"""

import threading
import time
from decimal import Decimal
from typing import Optional, Callable
from datetime import datetime

from modules.utils.logger import setup_logger

logger = setup_logger("trailing_stop", log_file="logs/trailing_stop.log")


class TrailingStop:
    """跟车止损管理器"""
    
    def __init__(self, stop_loss_manager, connector):
        """
        初始化
        
        Args:
            stop_loss_manager: 止损单管理器
            connector: 币安连接器
        """
        self.stop_loss_manager = stop_loss_manager
        self.connector = connector
        
        # 跟车配置
        self.trailing_pct = Decimal('0.02')  # 2% 跟车比例
        self.update_interval = 30  # 30 秒检查一次
        
        # 运行状态
        self._running = {}  # {symbol: thread}
        self._stop_prices = {}  # {symbol: current_stop_price}
        self._entry_prices = {}  # {symbol: entry_price}
    
    def start_trailing(
        self,
        symbol: str,
        entry_price: Decimal,
        initial_stop_price: Decimal,
        trailing_pct: Optional[Decimal] = None
    ):
        """
        启动跟车止损
        
        Args:
            symbol: 币种
            entry_price: 开仓价格
            initial_stop_price: 初始止损价
            trailing_pct: 跟车比例（可选）
        """
        if trailing_pct:
            self.trailing_pct = trailing_pct
        
        # 保存初始状态
        self._entry_prices[symbol] = entry_price
        self._stop_prices[symbol] = initial_stop_price
        
        # 启动监控线程
        if symbol in self._running and self._running[symbol].is_alive():
            logger.warning(f"{symbol} 跟车止损已在运行")
            return
        
        thread = threading.Thread(
            target=self._trailing_loop,
            args=(symbol,),
            daemon=True
        )
        thread.start()
        self._running[symbol] = thread
        
        logger.info(f"✅ {symbol} 跟车止损已启动")
        logger.info(f"   开仓价：{entry_price}")
        logger.info(f"   初始止损：{initial_stop_price}")
        logger.info(f"   跟车比例：{self.trailing_pct*100}%")
    
    def stop_trailing(self, symbol: str):
        """停止跟车止损"""
        if symbol in self._running:
            self._running[symbol] = False
            logger.info(f"⏹️ {symbol} 跟车止损已停止")
    
    def stop_all(self):
        """停止所有跟车止损"""
        for symbol in list(self._running.keys()):
            self.stop_trailing(symbol)
    
    def _trailing_loop(self, symbol: str):
        """跟车监控循环"""
        logger.info(f"🔄 {symbol} 跟车监控启动")
        
        while self._running.get(symbol, True):
            try:
                # 获取当前价格
                current_price = self._get_current_price(symbol)
                if not current_price:
                    time.sleep(self.update_interval)
                    continue
                
                # 计算新的止损价
                new_stop_price = self._calculate_new_stop(symbol, current_price)
                
                # 如果需要上移止损
                if new_stop_price > self._stop_prices[symbol]:
                    self._update_stop_loss(symbol, new_stop_price)
                    logger.info(
                        f"📈 {symbol} 止损上移：{self._stop_prices[symbol]} → {new_stop_price}"
                    )
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"{symbol} 跟车止损异常：{e}")
                time.sleep(self.update_interval)
        
        logger.info(f"⏹️ {symbol} 跟车监控停止")
    
    def _get_current_price(self, symbol: str) -> Optional[Decimal]:
        """获取当前价格"""
        try:
            price_data = self.connector.get_mark_price(symbol)
            return Decimal(str(price_data['markPrice']))
        except Exception as e:
            logger.error(f"获取 {symbol} 价格失败：{e}")
            return None
    
    def _calculate_new_stop(
        self,
        symbol: str,
        current_price: Decimal
    ) -> Decimal:
        """
        计算新的止损价
        
        逻辑:
        - 多头：止损价 = 当前价 × (1 - trailing_pct)
        - 只上移，不下移
        """
        # 计算理论止损价
        theoretical_stop = current_price * (1 - self.trailing_pct)
        
        # 只上移，不下移
        current_stop = self._stop_prices[symbol]
        new_stop = max(theoretical_stop, current_stop)
        
        return new_stop
    
    def _update_stop_loss(self, symbol: str, new_stop_price: Decimal):
        """更新止损单"""
        try:
            # 取消旧止损单
            self.stop_loss_manager.cancel_stop_loss(symbol)
            
            # 获取持仓数量
            position = self.connector.get_position(symbol)
            if not position or float(position['positionAmt']) == 0:
                logger.warning(f"{symbol} 无持仓，停止跟车")
                self.stop_trailing(symbol)
                return
            
            quantity = abs(Decimal(position['positionAmt']))
            
            # 创建新止损单
            result = self.stop_loss_manager.create_stop_loss(
                symbol=symbol,
                stop_price=new_stop_price,
                quantity=quantity
            )
            
            if result.get('success'):
                self._stop_prices[symbol] = new_stop_price
                logger.info(f"✅ {symbol} 止损单已更新：{new_stop_price}")
            else:
                logger.error(f"❌ {symbol} 止损单更新失败：{result}")
                
        except Exception as e:
            logger.error(f"{symbol} 更新止损单异常：{e}")


# 全局单例
_trailing_stop = None

def get_trailing_stop(stop_loss_manager, connector) -> TrailingStop:
    """获取跟车止损单例"""
    global _trailing_stop
    if _trailing_stop is None:
        _trailing_stop = TrailingStop(stop_loss_manager, connector)
    return _trailing_stop


if __name__ == "__main__":
    # 测试
    print("=== 测试跟车止损逻辑 ===\n")
    
    # 模拟数据
    entry_price = Decimal('2300')
    initial_stop = Decimal('2250')
    trailing_pct = Decimal('0.02')
    
    print(f"开仓价：{entry_price}")
    print(f"初始止损：{initial_stop}")
    print(f"跟车比例：{trailing_pct*100}%\n")
    
    # 模拟价格上涨
    prices = [2300, 2350, 2400, 2380, 2450, 2420]
    
    current_stop = initial_stop
    for price in prices:
        theoretical_stop = Decimal(str(price)) * (1 - trailing_pct)
        new_stop = max(theoretical_stop, current_stop)
        
        moved = "📈 上移" if new_stop > current_stop else "➡️ 保持"
        print(f"价格 ${price}: 止损 {moved} 到 {new_stop:.2f}")
        
        current_stop = new_stop
