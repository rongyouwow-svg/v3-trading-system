#!/usr/bin/env python3
"""
🦞 UNI RSI 反转策略

策略逻辑:
- RSI < 30 超卖 → 做多
- RSI > 70 超买 → 平仓
- 简单有效

参数:
- RSI 周期：14
- RSI 超卖：30
- RSI 超买：70
- 止损：5%
- 跟车：2%
"""

import time
from decimal import Decimal
from typing import Dict

from base_strategy import BaseStrategy
from modules.utils.logger import setup_logger

logger = setup_logger("uni_rsi_reversal", log_file="logs/uni_rsi_reversal.log")


class UNIRSIReversalStrategy(BaseStrategy):
    """UNI RSI 反转策略"""
    
    def __init__(
        self,
        symbol: str = "UNIUSDT",
        leverage: int = 5,
        amount: float = 200,
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
        super().__init__(
            symbol=symbol,
            leverage=leverage,
            amount=amount,
            stop_loss_pct=stop_loss_pct,
            trailing_stop_pct=trailing_stop_pct
        )
        
        # 策略参数
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        logger.info(f"✅ UNI RSI 反转策略初始化完成")
        logger.info(f"   杠杆：{leverage}x")
        logger.info(f"   金额：{amount} USDT")
        logger.info(f"   RSI 参数：{self.rsi_period} ({self.rsi_oversold}/{self.rsi_overbought})")
    
    def calculate_rsi(self, prices: list) -> float:
        """计算 RSI"""
        if len(prices) < self.rsi_period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(float(change))
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(float(change)))
        
        avg_gain = sum(gains[-self.rsi_period:]) / self.rsi_period
        avg_loss = sum(losses[-self.rsi_period:]) / self.rsi_period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def check_entry_condition(self, rsi: float) -> bool:
        """检查入场条件"""
        condition = rsi < self.rsi_oversold
        
        if condition:
            logger.info(f"📊 入场信号：RSI={rsi:.2f} < {self.rsi_oversold}")
        
        return condition
    
    def check_exit_condition(self, rsi: float) -> bool:
        """检查出场条件"""
        condition = rsi > self.rsi_overbought
        
        if condition:
            logger.info(f"📉 出场信号：RSI={rsi:.2f} > {self.rsi_overbought}")
        
        return condition
    
    def run(self):
        """运行策略"""
        logger.info(f"🚀 UNI RSI 反转策略启动")
        
        try:
            # 启动策略执行器
            result = self.executor.start_strategy(
                symbol=self.symbol,
                strategy_name="uni_rsi_reversal",
                leverage=self.leverage,
                amount_usd=self.amount,
                stop_loss_pct=self.stop_loss_pct,
                trailing_stop_pct=self.trailing_stop_pct
            )
            
            if not result.get('success'):
                logger.error(f"❌ 启动失败：{result}")
                return
            
            logger.info(f"✅ 策略启动成功")
            
            # 主循环（1 小时 K 线）
            while self.is_running:
                try:
                    # 获取 1 小时 K 线
                    klines = self.connector.get_klines(self.symbol, '1h', limit=50)
                    prices = [Decimal(k['close']) for k in klines]
                    
                    if len(prices) < 20:
                        time.sleep(60)
                        continue
                    
                    # 计算 RSI
                    rsi = self.calculate_rsi(prices)
                    current_price = prices[-1]
                    
                    # 检查信号
                    if not self.position:
                        # 无持仓，检查入场
                        if self.check_entry_condition(rsi):
                            logger.info("📈 开多信号")
                            self.executor.execute_signal(
                                self.symbol,
                                'BUY',
                                {'price': float(current_price)}
                            )
                    else:
                        # 有持仓，检查出场
                        if self.check_exit_condition(rsi):
                            logger.info("📉 平仓信号")
                            self.executor.execute_signal(
                                self.symbol,
                                'CLOSE',
                                {'price': float(current_price)}
                            )
                    
                    time.sleep(60)  # 1 分钟检查一次
                    
                except Exception as e:
                    logger.error(f"循环异常：{e}", exc_info=True)
                    time.sleep(60)
            
            # 停止策略
            logger.info("⏹️ 策略停止中...")
            self.executor.stop_strategy(self.symbol)
            
        except Exception as e:
            logger.error(f"❌ 策略运行异常：{e}", exc_info=True)
        finally:
            logger.info("⏹️ UNI RSI 反转策略已停止")


if __name__ == "__main__":
    # 测试运行
    strategy = UNIRSIReversalStrategy(
        symbol="UNIUSDT",
        leverage=5,
        amount=200,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.02
    )
    
    logger.info("按 Ctrl+C 停止策略")
    strategy.run()
