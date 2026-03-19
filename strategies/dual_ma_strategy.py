#!/usr/bin/env python3
"""
🦞 双均线策略
经典策略：快线上穿慢线（金叉）做多，快线下穿慢线（死叉）做空
"""

from strategies.base_strategy import BaseStrategy

class DualMAStrategy(BaseStrategy):
    """双均线策略 - EMA 金叉做多，死叉做空"""
    
    def __init__(self, gateway, symbol: str, leverage: int, amount: float):
        super().__init__(gateway, symbol, leverage, amount)
        self.name = "DualMA"
        self.description = "双均线策略 - EMA12/26 金叉做多，死叉做空"
        self.fast_period = 12  # 快线周期
        self.slow_period = 26  # 慢线周期
        self.fast_ema = []
        self.slow_ema = []
        self.current_side = None
    
    def on_start(self):
        self.log(f"🚀 双均线策略启动：{self.symbol} (快{self.fast_period}/慢{self.slow_period})")
        return True
    
    def on_stop(self):
        self.log(f"🛑 双均线策略停止：{self.symbol}")
        self.fast_ema = []
        self.slow_ema = []
        self.current_side = None
        return True
    
    def on_tick(self, price_data: dict):
        price = price_data['price']
        
        # 更新 EMA
        self.update_ema(price, self.fast_ema, self.fast_period)
        self.update_ema(price, self.slow_ema, self.slow_period)
        
        # 需要足够的数据
        if len(self.fast_ema) < self.slow_period:
            return None
        
        # 获取当前和上一个 EMA 值
        fast_curr = self.fast_ema[-1]
        slow_curr = self.slow_ema[-1]
        fast_prev = self.fast_ema[-2]
        slow_prev = self.slow_ema[-2]
        
        # 金叉：快线上穿慢线 - 开多
        if fast_prev <= slow_prev and fast_curr > slow_curr and self.current_side != 'LONG':
            self.log(f"✨ 金叉信号：快线{fast_curr:.2f} > 慢线{slow_curr:.2f} - 开多")
            self.current_side = 'LONG'
            return {
                'type': 'OPEN',
                'side': 'LONG',
                'percentage': 1.0,
                'stop_loss_pct': 0.05
            }
        
        # 死叉：快线下穿慢线 - 平多
        if fast_prev >= slow_prev and fast_curr < slow_curr and self.current_side == 'LONG':
            self.log(f"💔 死叉信号：快线{fast_curr:.2f} < 慢线{slow_curr:.2f} - 平多")
            self.current_side = None
            return {
                'type': 'CLOSE',
                'side': 'LONG',
                'percentage': 1.0
            }
        
        return None
    
    def update_ema(self, price, ema_list, period):
        """更新 EMA 列表"""
        multiplier = 2 / (period + 1)
        if len(ema_list) == 0:
            ema_list.append(price)
        else:
            ema = price * multiplier + ema_list[-1] * (1 - multiplier)
            ema_list.append(ema)
            # 保持列表长度
            if len(ema_list) > period * 2:
                ema_list.pop(0)
