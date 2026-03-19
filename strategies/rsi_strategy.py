#!/usr/bin/env python3
"""
🦞 RSI 超买超卖策略
RSI < 30 超卖做多，RSI > 70 超买做空
"""

from strategies.base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    """RSI 策略 - 超卖做多，超买做空"""
    
    def __init__(self, gateway, symbol: str, leverage: int, amount: float):
        super().__init__(gateway, symbol, leverage, amount)
        self.name = "RSIStrategy"
        self.description = "RSI 超买超卖策略 - RSI<30 做多，RSI>70 做空"
        self.rsi_period = 14
        self.rsi_oversold = 30  # 超卖线
        self.rsi_overbought = 70  # 超买线
        self.prices = []
        self.current_side = None
    
    def on_start(self):
        self.log(f"🚀 RSI 策略启动：{self.symbol} (周期{self.rsi_period}, 超卖{self.rsi_oversold}, 超买{self.rsi_overbought})")
        return True
    
    def on_stop(self):
        self.log(f"🛑 RSI 策略停止：{self.symbol}")
        self.prices = []
        self.current_side = None
        return True
    
    def on_tick(self, price_data: dict):
        price = price_data['price']
        self.prices.append(price)
        
        # 保持价格历史
        if len(self.prices) > self.rsi_period * 2:
            self.prices.pop(0)
        
        # 需要足够数据计算 RSI
        if len(self.prices) < self.rsi_period + 1:
            return None
        
        # 计算 RSI
        rsi = self.calculate_rsi()
        if rsi is None:
            return None
        
        # 超卖 - 开多
        if rsi < self.rsi_oversold and self.current_side != 'LONG':
            self.log(f"✨ 超卖信号：RSI={rsi:.1f} < {self.rsi_oversold} - 开多")
            self.current_side = 'LONG'
            return {
                'type': 'OPEN',
                'side': 'LONG',
                'percentage': 1.0,
                'stop_loss_pct': 0.05
            }
        
        # 超买 - 平多
        if rsi > self.rsi_overbought and self.current_side == 'LONG':
            self.log(f"💔 超买信号：RSI={rsi:.1f} > {self.rsi_overbought} - 平多")
            self.current_side = None
            return {
                'type': 'CLOSE',
                'side': 'LONG',
                'percentage': 1.0
            }
        
        return None
    
    def calculate_rsi(self):
        """计算 RSI"""
        if len(self.prices) < self.rsi_period + 1:
            return None
        
        # 计算价格变化
        changes = [self.prices[i] - self.prices[i-1] for i in range(1, len(self.prices))]
        
        # 分离涨跌
        gains = [max(0, c) for c in changes[-self.rsi_period:]]
        losses = [max(0, -c) for c in changes[-self.rsi_period:]]
        
        # 计算平均涨跌幅
        avg_gain = sum(gains) / self.rsi_period
        avg_loss = sum(losses) / self.rsi_period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
