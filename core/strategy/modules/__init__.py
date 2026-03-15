"""
📊 策略模块包 v3.1

包含:
    - RSI 策略基类
    - 1 分钟 RSI 策略（ETH/LINK）
    - RSI 分批建仓策略（AVAX）
"""

# 延迟导入，避免循环依赖
def __getattr__(name):
    if name == 'RSIStrategy':
        from core.strategy.modules.rsi_strategy import RSIStrategy
        return RSIStrategy
    elif name == 'RSI1MinStrategy':
        from core.strategy.modules.rsi_1min_strategy import Strategy
        return Strategy
    elif name == 'RSIScaleInStrategy':
        from core.strategy.modules.rsi_scale_in_strategy import Strategy
        return Strategy
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ['RSIStrategy', 'RSI1MinStrategy', 'RSIScaleInStrategy']
