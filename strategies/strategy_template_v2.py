#!/usr/bin/env python3
"""
🦞 策略模板 V2（止损在策略内部）

核心特性:
    - 止损逻辑在策略内部
    - 策略自己管理止损单
    - 完整的生命周期管理
    - 支持跟车止损

止损流程:
    1. 开仓后立即创建止损单
    2. 价格上涨时上移止损（跟车）
    3. 价格下跌时保持止损不变
    4. 平仓时取消止损单

用法:
    继承此模板，实现具体的交易逻辑
    class MyStrategy(StrategyTemplateV2):
        def check_entry_condition(self): ...
        def check_exit_condition(self): ...
"""

import time
import requests
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional

from modules.utils.logger import setup_logger

logger = setup_logger("strategy_template_v2", log_file="logs/strategy_template_v2.log")


class StrategyTemplateV2:
    """策略模板 V2（带内置止损）"""
    
    def __init__(
        self,
        symbol: str,
        leverage: int,
        amount: float,
        stop_loss_pct: float = 0.05,
        trailing_stop_pct: float = 0.02
    ):
        """
        初始化策略
        
        Args:
            symbol: 币种
            leverage: 杠杆
            amount: 投资金额
            stop_loss_pct: 止损百分比
            trailing_stop_pct: 跟车止损百分比
        """
        # 策略配置
        self.symbol = symbol
        self.leverage = leverage
        self.amount = amount
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
        
        # 状态变量
        self.position = None  # 持仓信息
        self.entry_price = 0
        self.stop_loss_price = 0
        self.stop_loss_order_id = None
        self.is_running = False
        
        # 统计
        self.trades = []
        self.pnl = 0
        
        logger.info(f"✅ 策略初始化：{symbol}")
        logger.info(f"   杠杆：{leverage}x")
        logger.info(f"   金额：{amount} USDT")
        logger.info(f"   止损：{stop_loss_pct*100}%")
        logger.info(f"   跟车：{trailing_stop_pct*100}%")
    
    # ==================== 止损管理（策略内部） ====================
    
    def create_stop_loss(self, quantity: float):
        """
        创建止损单（策略内部）
        
        Args:
            quantity: 平仓数量
        """
        if not self.position:
            logger.warning("⚠️ 无持仓，无法创建止损单")
            return False
        
        # 计算止损价
        self.stop_loss_price = self.entry_price * (1 - self.stop_loss_pct)
        
        logger.info(f"📊 创建止损单...")
        logger.info(f"   数量：{quantity}")
        logger.info(f"   止损价：{self.stop_loss_price}")
        
        try:
            # 调用币安 API 创建止损单
            response = requests.post(
                "http://localhost:3000/api/binance/stop-loss",
                json={
                    'symbol': self.symbol,
                    'side': 'SELL',
                    'type': 'STOP_MARKET',
                    'stopPrice': float(self.stop_loss_price),
                    'quantity': quantity,
                    'reduceOnly': True
                },
                timeout=10
            )
            
            data = response.json()
            
            if data.get('success'):
                self.stop_loss_order_id = data.get('order', {}).get('orderId')
                logger.info(f"✅ 止损单已创建：{self.stop_loss_order_id}")
                return True
            else:
                logger.error(f"❌ 止损单创建失败：{data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 创建止损单异常：{e}")
            return False
    
    def update_stop_loss(self, current_price: Decimal):
        """
        更新止损价（跟车止损）
        
        逻辑:
        - 价格上涨时上移止损
        - 价格下跌时保持止损不变
        
        Args:
            current_price: 当前价格
        """
        if not self.position or not self.stop_loss_price:
            return
        
        # 计算新的止损价
        new_stop_price = current_price * (1 - self.trailing_stop_pct)
        
        # 只上移，不下移
        if new_stop_price > self.stop_loss_price:
            logger.info(f"📈 跟车止损：{self.stop_loss_price} → {new_stop_price}")
            
            # 取消旧止损单
            self.cancel_stop_loss()
            
            # 获取持仓数量
            quantity = abs(self.position.get('positionAmt', 0))
            
            # 创建新止损单
            self.stop_loss_price = new_stop_price
            self.create_stop_loss(quantity)
    
    def cancel_stop_loss(self):
        """取消止损单"""
        if not self.stop_loss_order_id:
            return
        
        logger.info(f"❌ 取消止损单：{self.stop_loss_order_id}")
        
        try:
            response = requests.delete(
                f"http://localhost:3000/api/binance/stop-loss/{self.stop_loss_order_id}",
                timeout=10
            )
            
            data = response.json()
            
            if data.get('success'):
                logger.info(f"✅ 止损单已取消")
                self.stop_loss_order_id = None
                self.stop_loss_price = 0
                return True
            else:
                logger.error(f"❌ 止损单取消失败：{data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 取消止损单异常：{e}")
            return False
    
    def check_stop_loss_triggered(self, current_price: Decimal) -> bool:
        """
        检查止损是否触发
        
        Args:
            current_price: 当前价格
            
        Returns:
            bool: 是否触发
        """
        if not self.stop_loss_price:
            return False
        
        if current_price <= self.stop_loss_price:
            logger.warning(f"🚨 止损触发！价格={current_price} <= 止损价={self.stop_loss_price}")
            return True
        
        return False
    
    # ==================== 策略生命周期 ====================
    
    def open_position(self, quantity: float, price: Decimal):
        """
        开仓（带止损）
        
        Args:
            quantity: 数量
            price: 开仓价格
        """
        logger.info(f"🚀 开仓...")
        logger.info(f"   数量：{quantity}")
        logger.info(f"   价格：{price}")
        
        try:
            # 开单
            response = requests.post(
                "http://localhost:3000/api/binance/order",
                json={
                    'symbol': self.symbol,
                    'side': 'BUY',
                    'type': 'MARKET',
                    'quantity': quantity
                },
                timeout=10
            )
            
            data = response.json()
            
            if data.get('success'):
                order = data.get('order', {})
                self.position = {
                    'symbol': self.symbol,
                    'side': 'LONG',
                    'size': quantity,
                    'entryPrice': float(price),
                    'leverage': self.leverage
                }
                self.entry_price = price
                
                logger.info(f"✅ 开仓成功")
                
                # 立即创建止损单
                time.sleep(1)  # 等待订单确认
                self.create_stop_loss(quantity)
                
                return True
            else:
                logger.error(f"❌ 开仓失败：{data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 开仓异常：{e}")
            return False
    
    def close_position(self, quantity: float, price: Decimal):
        """
        平仓（取消止损）
        
        Args:
            quantity: 数量
            price: 平仓价格
        """
        logger.info(f"📉 平仓...")
        logger.info(f"   数量：{quantity}")
        logger.info(f"   价格：{price}")
        
        # 先取消止损单
        self.cancel_stop_loss()
        
        try:
            # 平仓
            response = requests.post(
                "http://localhost:3000/api/binance/order",
                json={
                    'symbol': self.symbol,
                    'side': 'SELL',
                    'type': 'MARKET',
                    'quantity': quantity
                },
                timeout=10
            )
            
            data = response.json()
            
            if data.get('success'):
                # 计算盈亏
                pnl = (float(price) - self.entry_price) * quantity
                self.pnl += pnl
                
                logger.info(f"✅ 平仓成功")
                logger.info(f"   盈亏：{pnl:.2f} USDT")
                
                # 重置状态
                self.position = None
                self.entry_price = 0
                self.stop_loss_price = 0
                self.stop_loss_order_id = None
                
                return True
            else:
                logger.error(f"❌ 平仓失败：{data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 平仓异常：{e}")
            return False
    
    # ==================== 策略接口（子类实现） ====================
    
    def check_entry_condition(self, indicators: Dict, current_price: Decimal) -> bool:
        """
        检查入场条件（子类实现）
        
        Args:
            indicators: 指标值
            current_price: 当前价格
            
        Returns:
            bool: 是否入场
        """
        raise NotImplementedError("子类必须实现 check_entry_condition")
    
    def check_exit_condition(self, indicators: Dict, current_price: Decimal) -> bool:
        """
        检查出场条件（子类实现）
        
        Args:
            indicators: 指标值
            current_price: 当前价格
            
        Returns:
            bool: 是否出场
        """
        raise NotImplementedError("子类必须实现 check_exit_condition")
    
    def calculate_indicators(self, klines: List[Dict]) -> Dict:
        """
        计算指标（子类实现）
        
        Args:
            klines: K 线数据
            
        Returns:
            dict: 指标值
        """
        raise NotImplementedError("子类必须实现 calculate_indicators")
    
    # ==================== 策略主循环 ====================
    
    def run(self):
        """运行策略（模板方法）"""
        logger.info(f"🚀 策略启动：{self.symbol}")
        self.is_running = True
        
        try:
            while self.is_running:
                try:
                    # 获取 K 线
                    klines = self.get_klines(self.symbol, '1h', limit=50)
                    if len(klines) < 20:
                        time.sleep(60)
                        continue
                    
                    # 计算指标
                    indicators = self.calculate_indicators(klines)
                    current_price = Decimal(klines[-1]['close'])
                    
                    # 检查止损触发
                    if self.position:
                        if self.check_stop_loss_triggered(current_price):
                            logger.warning("🚨 止损触发，自动平仓！")
                            self.close_position(self.position['size'], current_price)
                            continue
                        
                        # 更新跟车止损
                        self.update_stop_loss(current_price)
                    
                    # 检查交易信号
                    if not self.position:
                        # 无持仓，检查入场
                        if self.check_entry_condition(indicators, current_price):
                            logger.info("📈 入场信号")
                            quantity = self.calculate_quantity(current_price)
                            self.open_position(quantity, current_price)
                    else:
                        # 有持仓，检查出场
                        if self.check_exit_condition(indicators, current_price):
                            logger.info("📉 出场信号")
                            self.close_position(self.position['size'], current_price)
                    
                    time.sleep(60)
                    
                except Exception as e:
                    logger.error(f"循环异常：{e}", exc_info=True)
                    time.sleep(60)
            
            # 策略停止，平仓并取消止损
            logger.info("⏹️ 策略停止中...")
            if self.position:
                self.close_position(self.position['size'], Decimal('0'))
            
        except Exception as e:
            logger.error(f"❌ 策略运行异常：{e}", exc_info=True)
        finally:
            self.is_running = False
            logger.info("⏹️ 策略已停止")
    
    def calculate_quantity(self, price: Decimal) -> float:
        """计算开仓数量"""
        position_value = Decimal(str(self.amount)) * self.leverage
        quantity = position_value / price
        return float(quantity)
    
    def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict]:
        """获取 K 线数据"""
        try:
            response = requests.get(
                f"http://localhost:3000/api/binance/klines",
                params={
                    'symbol': symbol,
                    'interval': interval,
                    'limit': limit
                },
                timeout=10
            )
            data = response.json()
            return data.get('klines', [])
        except Exception as e:
            logger.error(f"获取 K 线失败：{e}")
            return []


if __name__ == "__main__":
    logger.info("策略模板 V2 - 止损在策略内部")
    logger.info("继承此模板，实现具体的交易逻辑")
