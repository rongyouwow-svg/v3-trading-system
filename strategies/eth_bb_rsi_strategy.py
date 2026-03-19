#!/usr/bin/env python3
"""
🦞 ETH BB+RSI 策略 (年化 2135%)

回测数据:
- 年化收益：2135.84%
- 总收益：239.92%
- 胜率：33.3%
- 最大回撤：43.3%
- 交易数：24
- 时间周期：1 小时

策略逻辑:
- 布林带 + RSI 组合
- RSI < 40 且价格 < 下轨 → 做多
- RSI > 60 且价格 > 上轨 → 平仓

参数:
- RSI 超卖：40
- RSI 超买：60
- 布林带：2.0 标准差
- 均线：20
"""

import time
from decimal import Decimal
from datetime import datetime
from typing import Dict, Optional

from base_strategy import BaseStrategy
from modules.utils.logger import setup_logger

logger = setup_logger("eth_bb_rsi", log_file="logs/eth_bb_rsi.log")


class ETHBBRSIStrategy(BaseStrategy):
    """ETH BB+RSI 策略"""
    
    def __init__(
        self,
        symbol: str = "ETHUSDT",
        leverage: int = 3,
        amount: float = 300,
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
        
        # 策略参数（回测最优）
        self.rsi_period = 14
        self.rsi_oversold = 40
        self.rsi_overbought = 60
        self.bb_period = 20
        self.bb_std = 2.0
        
        # 状态
        self.last_rsi = 0
        self.last_prices = []
        
        logger.info(f"✅ ETH BB+RSI 策略初始化完成")
        logger.info(f"   杠杆：{leverage}x")
        logger.info(f"   金额：{amount} USDT")
        logger.info(f"   RSI 参数：{self.rsi_period} ({self.rsi_oversold}/{self.rsi_overbought})")
        logger.info(f"   布林带：{self.bb_period}, {self.bb_std}σ")
    
    def calculate_indicators(self, prices: list) -> Dict:
        """
        计算指标
        
        Args:
            prices: 价格列表
            
        Returns:
            dict: 指标值
        """
        if len(prices) < self.bb_period:
            return {'rsi': 50, 'bb_upper': 0, 'bb_middle': 0, 'bb_lower': 0}
        
        # 计算 RSI
        rsi = self._calculate_rsi(prices, self.rsi_period)
        
        # 计算布林带
        bb = self._calculate_bollinger_bands(prices, self.bb_period, self.bb_std)
        
        return {
            'rsi': rsi,
            'bb_upper': bb['upper'],
            'bb_middle': bb['middle'],
            'bb_lower': bb['lower']
        }
    
    def check_entry_condition(self, indicators: Dict, current_price: Decimal) -> bool:
        """
        检查入场条件
        
        条件:
        - RSI < 40 (超卖)
        - 价格 < 布林带下轨
        
        Args:
            indicators: 指标值
            current_price: 当前价格
            
        Returns:
            bool: 是否入场
        """
        rsi = indicators['rsi']
        bb_lower = indicators['bb_lower']
        
        condition = (rsi < self.rsi_oversold) and (current_price < bb_lower)
        
        if condition:
            logger.info(f"📊 入场信号：RSI={rsi:.2f}, 价格={current_price} < BB 下轨={bb_lower:.2f}")
        
        return condition
    
    def check_exit_condition(self, indicators: Dict, current_price: Decimal) -> bool:
        """
        检查出场条件
        
        条件:
        - RSI > 60 (超买)
        - 价格 > 布林带上轨
        
        Args:
            indicators: 指标值
            current_price: 当前价格
            
        Returns:
            bool: 是否出场
        """
        rsi = indicators['rsi']
        bb_upper = indicators['bb_upper']
        
        condition = (rsi > self.rsi_overbought) and (current_price > bb_upper)
        
        if condition:
            logger.info(f"📊 出场信号：RSI={rsi:.2f}, 价格={current_price} > BB 上轨={bb_upper:.2f}")
        
        return condition
    
    def run(self):
        """运行策略"""
        logger.info(f"🚀 ETH BB+RSI 策略启动")
        
        try:
            # 启动策略执行器
            result = self.executor.start_strategy(
                symbol=self.symbol,
                strategy_name="eth_bb_rsi",
                leverage=self.leverage,
                amount_usd=self.amount,
                stop_loss_pct=self.stop_loss_pct,
                trailing_stop_pct=self.trailing_stop_pct
            )
            
            if not result.get('success'):
                logger.error(f"❌ 启动失败：{result}")
                return
            
            logger.info(f"✅ 策略启动成功")
            
            # 主循环
            while self.is_running:
                try:
                    # 获取 K 线数据
                    klines = self.connector.get_klines(self.symbol, '1h', limit=50)
                    prices = [Decimal(k['close']) for k in klines]
                    
                    if len(prices) < 20:
                        time.sleep(60)
                        continue
                    
                    # 计算指标
                    indicators = self.calculate_indicators(prices)
                    current_price = prices[-1]
                    
                    self.last_rsi = indicators['rsi']
                    
                    # 检查信号
                    if not self.position:
                        # 无持仓，检查入场
                        if self.check_entry_condition(indicators, current_price):
                            logger.info("📈 开多信号")
                            self.executor.execute_signal(
                                self.symbol,
                                'BUY',
                                {'price': float(current_price)}
                            )
                    else:
                        # 有持仓，检查出场
                        if self.check_exit_condition(indicators, current_price):
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
            logger.info("⏹️ ETH BB+RSI 策略已停止")
    
    def _calculate_rsi(self, prices: list, period: int) -> float:
        """计算 RSI"""
        if len(prices) < period + 1:
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
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_bollinger_bands(
        self,
        prices: list,
        period: int,
        std_dev: float
    ) -> Dict:
        """计算布林带"""
        if len(prices) < period:
            return {'upper': 0, 'middle': 0, 'lower': 0}
        
        recent = prices[-period:]
        middle = sum(recent) / period
        
        variance = sum((p - middle) ** 2 for p in recent) / period
        std = variance ** 0.5
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }


if __name__ == "__main__":
    # 测试运行
    strategy = ETHBBRSIStrategy(
        symbol="ETHUSDT",
        leverage=3,
        amount=300,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.02
    )
    
    logger.info("按 Ctrl+C 停止策略")
    strategy.run()
