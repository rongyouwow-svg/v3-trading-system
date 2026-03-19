from strategies.base_strategy import BaseStrategy
class SimpleStrategy(BaseStrategy):
    """简单策略 - 热插拔验证"""
    def __init__(self, gateway, symbol, leverage, amount):
        super().__init__(gateway, symbol, leverage, amount)
    def on_start(self): return True
    def on_stop(self): return True
    def on_tick(self, price_data): return None
