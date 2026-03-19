#!/usr/bin/env python3
"""
🦞 AVAX 突破策略 (年化 20.18%)

回测数据:
- 年化收益：20.18%
- 胜率：53.33%
- 夏普比率：4.66
- 交易次数：15
- 最大回撤：2.85%

策略逻辑:
- 突破 20 日高点 → 做多
- 跌破 10 日低点 → 平仓
- 成交量确认

参数:
- lookback: 20
- volume_mult: 1.5
- stop_loss: 0.06
- take_profit: 0.18
"""

import time
from decimal import Decimal
from typing import Dict

from base_strategy import BaseStrategy
from modules.utils.logger import setup_logger

logger = setup_logger("avax_breakout", log_file="logs/avax_breakout.log")


class AVAXBreakoutStrategy(BaseStrategy):
    """AVAX 突破策略"""
    
    def __init__(
        self,
        symbol: str = "AVAXUSDT",
        leverage: int = 8,
        amount: float = 250,
        stop_loss_pct: float = 0.06,
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
        self.lookback = 20
        self.volume_mult = 1.5
        self.take_profit_pct = 0.18
        
        logger.info(f"✅ AVAX 突破策略初始化完成")
        logger.info(f"   杠杆：{leverage}x")
        logger.info(f"   金额：{amount} USDT")
        logger.info(f"   突破周期：{self.lookback} 日")
        logger.info(f"   成交量倍数：{self.volume_mult}x")
    
    def calculate_indicators(self, klines: list) -> Dict:
        """
        计算指标
        
        Args:
            klines: K 线数据
            
        Returns:
            dict: 指标值
        """
        if len(klines) < self.lookback:
            return {
                'high_20d': 0,
                'low_10d': 0,
                'avg_volume': 0,
                'current_volume': 0
            }
        
        # 20 日高点
        highs = [Decimal(k['high']) for k in klines[-self.lookback:]]
        high_20d = max(highs)
        
        # 10 日低点
        lows = [Decimal(k['low']) for k in klines[-10:]]
        low_10d = min(lows)
        
        # 成交量
        volumes = [Decimal(k['volume']) for k in klines[-self.lookback:]]
        avg_volume = sum(volumes) / len(volumes)
        current_volume = volumes[-1]
        
        return {
            'high_20d': high_20d,
            'low_10d': low_10d,
            'avg_volume': avg_volume,
            'current_volume': current_volume
        }
    
    def check_entry_condition(self, indicators: Dict, current_price: Decimal) -> bool:
        """
        检查入场条件
        
        条件:
        - 价格突破 20 日高点
        - 成交量 > 1.5 倍均量
        
        Args:
            indicators: 指标值
            current_price: 当前价格
            
        Returns:
            bool: 是否入场
        """
        high_20d = indicators['high_20d']
        avg_volume = indicators['avg_volume']
        current_volume = indicators['current_volume']
        
        breakout = current_price > high_20d
        volume_confirmed = current_volume > (avg_volume * self.volume_mult)
        
        condition = breakout and volume_confirmed
        
        if condition:
            logger.info(
                f"📊 入场信号：价格={current_price} > 20 日高点={high_20d}, "
                f"成交量={current_volume:.2f} > {self.volume_mult}x 均量={avg_volume:.2f}"
            )
        
        return condition
    
    def check_exit_condition(self, indicators: Dict, current_price: Decimal) -> bool:
        """
        检查出场条件
        
        条件:
        - 跌破 10 日低点
        - 或达到止盈 (18%)
        
        Args:
            indicators: 指标值
            current_price: 当前价格
            
        Returns:
            bool: 是否出场
        """
        low_10d = indicators['low_10d']
        
        # 跌破低点
        breakdown = current_price < low_10d
        
        # 止盈检查
        take_profit = False
        if self.position:
            entry_price = Decimal(str(self.position['entryPrice']))
            profit_pct = (current_price - entry_price) / entry_price
            take_profit = profit_pct >= self.take_profit_pct
            
            if take_profit:
                logger.info(f"📊 止盈信号：盈利={profit_pct*100:.2f}% >= {self.take_profit_pct*100:.1f}%")
        
        condition = breakdown or take_profit
        
        if condition:
            reason = "跌破 10 日低点" if breakdown else "达到止盈"
            logger.info(f"📉 出场信号：{reason}")
        
        return condition
    
    def run(self):
        """运行策略"""
        logger.info(f"🚀 AVAX 突破策略启动")
        
        try:
            # 启动策略执行器
            result = self.executor.start_strategy(
                symbol=self.symbol,
                strategy_name="avax_breakout",
                leverage=self.leverage,
                amount_usd=self.amount,
                stop_loss_pct=self.stop_loss_pct,
                trailing_stop_pct=self.trailing_stop_pct
            )
            
            if not result.get('success'):
                logger.error(f"❌ 启动失败：{result}")
                return
            
            logger.info(f"✅ 策略启动成功")
            
            # 主循环（4 小时 K 线）
            while self.is_running:
                try:
                    # 获取 4 小时 K 线
                    klines = self.connector.get_klines(self.symbol, '4h', limit=50)
                    
                    if len(klines) < 20:
                        time.sleep(240)  # 等待 4 分钟
                        continue
                    
                    # 计算指标
                    indicators = self.calculate_indicators(klines)
                    current_price = Decimal(klines[-1]['close'])
                    
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
                    
                    time.sleep(240)  # 4 分钟检查一次
                    
                except Exception as e:
                    logger.error(f"循环异常：{e}", exc_info=True)
                    time.sleep(240)
            
            # 停止策略
            logger.info("⏹️ 策略停止中...")
            self.executor.stop_strategy(self.symbol)
            
        except Exception as e:
            logger.error(f"❌ 策略运行异常：{e}", exc_info=True)
        finally:
            logger.info("⏹️ AVAX 突破策略已停止")


if __name__ == "__main__":
    # 测试运行
    strategy = AVAXBreakoutStrategy(
        symbol="AVAXUSDT",
        leverage=8,
        amount=250,
        stop_loss_pct=0.06,
        trailing_stop_pct=0.02
    )
    
    logger.info("按 Ctrl+C 停止策略")
    strategy.run()
