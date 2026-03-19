# 策略文件说明

本目录包含量化交易策略实现。

## ⚠️ 注意

**核心策略文件未上传到 GitHub**

为了保护策略逻辑和知识产权，核心策略文件（`.py`）未包含在此代码库中。

## 可用策略

当前系统支持以下策略类型：

1. **突破策略 (Breakout)** - 基于价格突破的趋势跟踪策略
2. **RSI 反转策略** - 基于 RSI 指标的均值回归策略
3. **MACD 趋势策略** - 基于 MACD 金叉死叉的趋势跟踪策略
4. **网格交易策略** - 自动高抛低吸的网格交易策略

## 如何添加策略

1. 在 `strategies/` 目录创建新的策略文件
2. 继承 `BaseStrategy` 基类
3. 实现 `generate_signal()` 方法
4. 在策略管理器中注册

## 策略模板

```python
from modules.strategy.base import BaseStrategy
from modules.utils.result import Result

class MyStrategy(BaseStrategy):
    """自定义策略"""
    
    def __init__(self, symbol: str, **kwargs):
        super().__init__(symbol, **kwargs)
        self.name = "MyStrategy"
    
    def generate_signal(self) -> Result:
        """生成交易信号"""
        # 实现你的策略逻辑
        pass
```

## 联系

如需获取完整策略文件，请联系项目作者。
