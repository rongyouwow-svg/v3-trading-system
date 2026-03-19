from strategies.base_strategy import BaseStrategy

class DemoStrategy(BaseStrategy):
    """演示策略 - 热插拔测试"""
    
    def __init__(self, gateway, symbol, leverage, amount):
        super().__init__(gateway, symbol, leverage, amount)
        self.name = "DemoStrategy"
        self.description = "演示策略 - 热插拔测试"
    
    def on_start(self):
        self.log(f"🚀 演示策略启动：{self.symbol}")
        return True
    
    def on_stop(self):
        self.log(f"🛑 演示策略停止：{self.symbol}")
        return True
    
    def on_tick(self, price_data):
        return None
