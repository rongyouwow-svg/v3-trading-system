#!/usr/bin/env python3
"""
🦞 价格突破策略
简单易懂：价格突破 N 周期高点做多，跌破 N 周期低点做空
"""

from strategies.base_strategy import BaseStrategy

class PriceBreakoutStrategy(BaseStrategy):
    """价格突破策略 - 突破 N 周期高点做多，跌破低点做空"""
    
    def __init__(self, gateway, symbol: str, leverage: int, amount: float):
        super().__init__(gateway, symbol, leverage, amount)
        self.name = "PriceBreakout"
        self.description = "价格突破策略 - 突破 20 周期高点做多"
        self.lookback = 20  # 回溯周期
        self.prices = []  # 价格历史
        self.current_side = None  # 当前持仓方向
    
    def on_start(self):
        self.log(f"🚀 价格突破策略启动：{self.symbol} (回溯{self.lookback}周期)")
        return True
    
    def on_stop(self):
        self.log(f"🛑 价格突破策略停止：{self.symbol}")
        self.prices = []
        self.current_side = None
        return True
    
    def on_tick(self, price_data: dict):
        price = price_data['price']
        self.prices.append(price)
        
        # 保持价格历史长度
        if len(self.prices) > self.lookback * 2:
            self.prices.pop(0)
        
        # 需要足够的数据
        if len(self.prices) < self.lookback + 1:
            return None
        
        # 计算 N 周期高点和低点
        highest = max(self.prices[-self.lookback-1:-1])  # 前 N 个周期的最高点
        lowest = min(self.prices[-self.lookback-1:-1])   # 前 N 个周期的最低点
        current_price = self.prices[-1]  # 当前价格
        
        # 突破高点 - 开多
        if current_price > highest and self.current_side != 'LONG':
            self.log(f"✨ 突破信号：价格{current_price:.2f} > 高点{highest:.2f} - 开多")
            self.current_side = 'LONG'
            return {
                'type': 'OPEN',
                'side': 'LONG',
                'percentage': 1.0,
                'stop_loss_pct': 0.05
            }
        
        # 跌破低点 - 平多
        if current_price < lowest and self.current_side == 'LONG':
            self.log(f"💔 跌破信号：价格{current_price:.2f} < 低点{lowest:.2f} - 平多")
            self.current_side = None
            return {
                'type': 'CLOSE',
                'side': 'LONG',
                'percentage': 1.0
            }
        
        return None
