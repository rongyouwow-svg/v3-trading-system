# 🦞 龙虾王策略库集成系统指南

## 概述

策略库集成系统整合了 **70 个经典交易策略**，来自三大来源：

| 来源 | 数量 | 说明 |
|------|------|------|
| **TradingView** | 50 | 社区热门技术指标策略 |
| **GitHub** | 10 | 开源量化策略模式 |
| **学术论文** | 10 | 经典金融研究策略 |

## 文件结构

```
quant/
├── strategy_library.py      # 策略库核心代码
├── strategy_catalog.json    # 策略目录 (JSON)
└── STRATEGY_LIBRARY_GUIDE.md # 本文档
```

---

## 策略分类体系

### 按来源分类

```python
from strategy_library import StrategySource

StrategySource.TRADINGVIEW   # TradingView 社区策略
StrategySource.GITHUB        # GitHub 开源策略
StrategySource.ACADEMIC      # 学术论文策略
StrategySource.CUSTOM        # 自定义策略
```

### 按策略类型分类

```python
from strategy_library import StrategyType

StrategyType.TREND_FOLLOWING   # 趋势跟踪 (11 个)
StrategyType.MEAN_REVERSION    # 均值回归 (12 个)
StrategyType.MOMENTUM          # 动量策略 (11 个)
StrategyType.BREAKOUT          # 突破策略 (7 个)
StrategyType.REVERSAL          # 反转策略 (5 个)
StrategyType.ARBITRAGE         # 套利策略 (5 个)
StrategyType.MARKET_MAKING     # 做市策略 (2 个)
StrategyType.STATISTICAL       # 统计套利 (2 个)
StrategyType.MACHINE_LEARNING  # 机器学习 (4 个)
StrategyType.SENTIMENT         # 情绪分析 (1 个)
StrategyType.MULTI_FACTOR      # 多因子策略 (10 个)
```

### 按时间周期分类

```python
from strategy_library import Timeframe

Timeframe.SCALPING    # 剥头皮 (1m-5m) - 8 个
Timeframe.INTRADAY    # 日内 (15m-1h) - 18 个
Timeframe.SWING       # 波段 (4h-1d) - 28 个
Timeframe.POSITION    # 持仓 (1w+) - 16 个
```

### 按风险等级分类

```python
from strategy_library import RiskLevel

RiskLevel.LOW      # 低风险 - 15 个
RiskLevel.MEDIUM   # 中风险 - 35 个
RiskLevel.HIGH     # 高风险 - 17 个
RiskLevel.EXTREME  # 极高风险 - 3 个
```

### 按市场状态分类

```python
from strategy_library import MarketRegime

MarketRegime.BULL       # 牛市
MarketRegime.BEAR       # 熊市
MarketRegime.SIDEWAYS   # 震荡
MarketRegime.VOLATILE   # 高波动
MarketRegime.ALL        # 通用
```

---

## 快速开始

### 1. 初始化策略库

```python
from strategy_library import StrategyLibrary

# 初始化
library = StrategyLibrary()

# 获取统计信息
stats = library.get_statistics()
print(f"总策略数：{stats['total_strategies']}")
```

### 2. 获取策略

```python
# 获取单个策略
strategy = library.get_strategy('tv_001')
print(strategy.name)        # 双均线交叉
print(strategy.description) # 经典双均线策略...
print(strategy.entry_rules) # 入场规则列表
```

### 3. 筛选策略

```python
# 按类型筛选
trend_strategies = library.filter_strategies(
    strategy_type=StrategyType.TREND_FOLLOWING
)

# 按风险等级筛选
low_risk = library.filter_strategies(
    risk_level=RiskLevel.LOW
)

# 按时间周期筛选
swing_strategies = library.filter_strategies(
    timeframe=Timeframe.SWING
)

# 按市场状态筛选
bull_strategies = library.filter_strategies(
    market_regime=MarketRegime.BULL
)

# 组合筛选
safe_swing = library.filter_strategies(
    risk_level=RiskLevel.LOW,
    timeframe=Timeframe.SWING
)

# 按标签筛选
momentum_strategies = library.filter_strategies(
    tags=['momentum']
)
```

### 4. 搜索策略

```python
# 关键词搜索
results = library.search('bollinger')
for s in results:
    print(f"{s.id}: {s.name}")

# 搜索结果：
# tv_006: 布林带均值回归
```

### 5. 导出目录

```python
# 导出到 JSON
catalog = library.export_catalog()
# 保存到 strategy_catalog.json
```

---

## 策略执行

### 使用内置执行器

```python
from strategy_library import DualMAStrategy, StrategyLibrary
import pandas as pd

# 加载数据
df = pd.read_csv('data/ETHUSDT_30m.csv', index_col='timestamp', parse_dates=True)

# 创建策略执行器
strategy = DualMAStrategy()

# 运行回测
results = strategy.backtest(df, initial_capital=10000)

print(f"总收益：{results['total_return']:.2%}")
print(f"夏普比率：{results['sharpe_ratio']:.2f}")
print(f"最大回撤：{results['max_drawdown']:.2%}")
print(f"交易次数：{results['num_trades']}")
```

### 自定义策略执行器

```python
from strategy_library import StrategyExecutor, Signal, StrategyMetadata
import pandas as pd

class MyCustomStrategy(StrategyExecutor):
    """自定义策略"""
    
    def __init__(self):
        strategy = StrategyMetadata(
            id="custom_001",
            name="我的自定义策略",
            # ... 其他元数据
        )
        super().__init__(strategy)
    
    def generate_signal(self, df: pd.DataFrame, current_idx: int):
        """生成交易信号"""
        # 实现你的策略逻辑
        if df['rsi_14'].iloc[current_idx] < 30:
            return Signal(
                timestamp=df.index[current_idx],
                symbol='ETHUSDT',
                strategy_id=self.strategy.id,
                signal_type='LONG',
                price=df['close'].iloc[current_idx],
                strength=0.8
            )
        return None

# 使用
my_strategy = MyCustomStrategy()
results = my_strategy.backtest(df)
```

---

## 技术指标库

策略库内置了完整的技术指标计算器：

```python
from strategy_library import TechnicalIndicators

indicators = TechnicalIndicators()

# 移动平均
sma = indicators.sma(df, period=20)
ema = indicators.ema(df, period=20)

# 动量指标
rsi = indicators.rsi(df, period=14)
macd, signal, hist = indicators.macd(df)

# 波动率指标
upper, middle, lower = indicators.bollinger_bands(df)
atr = indicators.atr(df, period=14)

# 其他指标
k, d = indicators.stochastic(df)
adx = indicators.adx(df)
cci = indicators.cci(df)
wr = indicators.williams_r(df)
obv = indicators.obv(df)
vwap = indicators.vwap(df)
upper, middle, lower = indicators.keltner_channel(df)
ichimoku = indicators.ichimoku(df)
```

---

## TradingView 50 策略清单

### 趋势跟踪 (1-5)
1. tv_001 - 双均线交叉
2. tv_002 - 三重均线过滤
3. tv_003 - EMA 趋势跟踪
4. tv_004 - ADX 趋势强度
5. tv_005 - 超级趋势

### 均值回归 (6-10)
6. tv_006 - 布林带均值回归
7. tv_007 - RSI 超买超卖
8. tv_008 - 随机指标反转
9. tv_009 - CCI 通道交易
10. tv_010 - 威廉指标反转

### 动量策略 (11-15)
11. tv_011 - 价格动量突破
12. tv_012 - 相对强度策略
13. tv_013 - 成交量动量
14. tv_014 - MACD 动量
15. tv_015 - RSI 动量背离

### 突破策略 (16-20)
16. tv_016 - 唐奇安通道突破
17. tv_017 - 箱体突破
18. tv_018 - 三角形整理突破
19. tv_019 - 旗形突破
20. tv_020 - 头肩顶底突破

### 反转策略 (21-23)
21. tv_021 - 黄昏/黎明之星
22. tv_022 - 吞没形态
23. tv_023 - 锤子/上吊线

### 多因子策略 (24-25)
24. tv_024 - 多因子评分系统
25. tv_025 - 技术面 + 情绪面

### 波动率策略 (26-28)
26. tv_026 - 波动率突破
27. tv_027 - 波动率均值回归
28. tv_028 - 肯特纳通道

### 成交量策略 (29-31)
29. tv_029 - OBV 能量潮
30. tv_030 - VWAP 回归
31. tv_031 - 成交量分布

### 一目均衡表 (32-33)
32. tv_032 - 一目均衡表完整系统
33. tv_033 - 云突破

### 经典系统 (34-40)
34. tv_034 - 海龟交易法则
35. tv_035 - 三重屏交易系统
36. tv_036 - 枢轴点策略
37. tv_037 - 斐波那契回撤
38. tv_038 - 谐波形态
39. tv_039 - 艾略特波浪
40. tv_040 - 市场轮廓

### 高级策略 (41-50)
41. tv_041 - 机器学习分类器
42. tv_042 - 神经网络预测
43. tv_043 - 统计套利
44. tv_044 - 期现套利
45. tv_045 - 资金费率套利
46. tv_046 - 网格交易
47. tv_047 - 马丁格尔策略
48. tv_048 - 反马丁格尔
49. tv_049 - 时间序列动量
50. tv_050 - 波动率目标策略

---

## GitHub 策略模式清单

1. gh_001 - 双均线动量 (Quantopian)
2. gh_002 - 多因子 Alpha (Quantopian)
3. gh_003 - 统计套利配对
4. gh_004 - 机器学习选股
5. gh_005 - LSTM 价格预测
6. gh_006 - 加密货币动量
7. gh_007 - 资金费率套利
8. gh_008 - 链上数据策略
9. gh_009 - 做市策略 (Hummingbot)
10. gh_010 - TWAP 执行

---

## 学术论文策略清单

1. ap_001 - 时间序列动量 (Moskowitz et al., JFE 2012)
2. ap_002 - 横截面动量 (Jegadeesh & Titman, JF 1993)
3. ap_003 - 价值策略 (Fama & French, JF 1993)
4. ap_004 - 低波动异常 (Ang et al., JF 2006)
5. ap_005 - 质量因子 (Novy-Marx, RFS 2014)
6. ap_006 - 季节性效应 (Jegadeesh, JFE 1990)
7. ap_007 - 波动率风险溢价 (Carr & Wu, 2009)
8. ap_008 - Carry 策略 (Koijen et al., JFE 2017)
9. ap_009 - 贝塔动量 (Barroso & Santa-Clara, RFS 2015)
10. ap_010 - 风险平价 (Qian, 2005/2006)

---

## 使用场景

### 场景 1: 选择适合当前市场的策略

```python
from strategy_library import StrategyLibrary, MarketRegime

library = StrategyLibrary()

# 假设当前是牛市
bull_strategies = library.filter_strategies(
    market_regime=MarketRegime.BULL,
    risk_level=RiskLevel.MEDIUM
)

print(f"适合牛市的中等风险策略：{len(bull_strategies)} 个")
for s in bull_strategies[:5]:
    print(f"  - {s.name} ({s.type.value})")
```

### 场景 2: 构建策略组合

```python
# 分散配置不同策略类型
library = StrategyLibrary()

portfolio = {
    'trend': library.filter_strategies(strategy_type=StrategyType.TREND_FOLLOWING)[:2],
    'mean_rev': library.filter_strategies(strategy_type=StrategyType.MEAN_REVERSION)[:2],
    'momentum': library.filter_strategies(strategy_type=StrategyType.MOMENTUM)[:2],
}

print("策略组合:")
for category, strategies in portfolio.items():
    print(f"  {category}: {[s.name for s in strategies]}")
```

### 场景 3: 策略研究

```python
# 研究所有低风险策略
library = StrategyLibrary()

low_risk = library.filter_strategies(risk_level=RiskLevel.LOW)

for strategy in low_risk:
    print(f"\n{strategy.name} ({strategy.id})")
    print(f"  类型：{strategy.type.value}")
    print(f"  周期：{strategy.timeframe.value}")
    print(f"  入场：{strategy.entry_rules[0]}")
    print(f"  出场：{strategy.exit_rules[0]}")
    print(f"  风控：{strategy.risk_management[0]}")
```

---

## 扩展策略库

### 添加新策略

```python
from strategy_library import (
    StrategyMetadata, StrategySource, StrategyType,
    Timeframe, RiskLevel, MarketRegime
)

new_strategy = StrategyMetadata(
    id="custom_001",
    name="我的新策略",
    source=StrategySource.CUSTOM,
    type=StrategyType.TREND_FOLLOWING,
    timeframe=Timeframe.SWING,
    risk_level=RiskLevel.MEDIUM,
    market_regime=[MarketRegime.BULL],
    description="策略描述",
    author="你的名字",
    created_date="2026-03-04",
    version="1.0",
    tags=["custom", "trend"],
    parameters={"param1": 10, "param2": 20},
    entry_rules=["入场规则 1", "入场规则 2"],
    exit_rules=["出场规则 1", "出场规则 2"],
    risk_management=["风控规则 1", "风控规则 2"]
)
```

---

## 最佳实践

### 1. 策略选择原则

- **匹配市场状态**: 牛市用趋势策略，震荡市用均值回归
- **风险匹配**: 根据风险承受能力选择风险等级
- **时间周期匹配**: 根据交易频率选择合适周期
- **分散配置**: 不要只用单一策略类型

### 2. 回测验证

```python
# 回测前检查数据质量
assert len(df) > 1000, "数据不足"
assert 'close' in df.columns, "缺少收盘价"
assert 'volume' in df.columns, "缺少成交量"

# 多策略对比
strategies_to_test = ['tv_001', 'tv_006', 'tv_011']
results = {}

for strat_id in strategies_to_test:
    strategy = library.get_strategy(strat_id)
    executor = create_executor(strategy)  # 需要实现
    results[strat_id] = executor.backtest(df)

# 比较结果
compare_results(results)
```

### 3. 风险管理

- 单个策略仓位不超过总资金的 20%
- 设置最大回撤限制 (建议 15-20%)
- 定期评估策略有效性
- 策略失效时及时停止

---

## API 参考

### StrategyLibrary

| 方法 | 说明 |
|------|------|
| `get_strategy(id)` | 获取单个策略 |
| `filter_strategies(...)` | 筛选策略 |
| `search(query)` | 搜索策略 |
| `get_statistics()` | 获取统计信息 |
| `export_catalog()` | 导出 JSON 目录 |

### StrategyMetadata

| 属性 | 说明 |
|------|------|
| `id` | 策略 ID |
| `name` | 策略名称 |
| `source` | 策略来源 |
| `type` | 策略类型 |
| `timeframe` | 时间周期 |
| `risk_level` | 风险等级 |
| `market_regime` | 适用市场状态 |
| `description` | 描述 |
| `parameters` | 参数配置 |
| `entry_rules` | 入场规则 |
| `exit_rules` | 出场规则 |
| `risk_management` | 风控规则 |

### TechnicalIndicators

| 方法 | 说明 |
|------|------|
| `sma(df, period)` | 简单移动平均 |
| `ema(df, period)` | 指数移动平均 |
| `rsi(df, period)` | RSI 指标 |
| `macd(df)` | MACD 指标 |
| `bollinger_bands(df)` | 布林带 |
| `atr(df, period)` | ATR |
| `stochastic(df)` | 随机指标 |
| `adx(df)` | ADX |
| `cci(df)` | CCI |
| `williams_r(df)` | 威廉指标 |
| `obv(df)` | OBV |
| `vwap(df)` | VWAP |
| `keltner_channel(df)` | 肯特纳通道 |
| `ichimoku(df)` | 一目均衡表 |

---

## 更新日志

### v1.0.0 (2026-03-04)
- ✅ 集成 TradingView 50 策略
- ✅ 集成 GitHub 10 策略模式
- ✅ 集成学术论文 10 策略
- ✅ 策略分类管理系统
- ✅ 技术指标计算库
- ✅ 策略执行器框架
- ✅ JSON 目录导出

---

## 常见问题

**Q: 如何选择合适的策略？**
A: 根据市场状态、风险承受能力和交易频率筛选。牛市选趋势策略，震荡市选均值回归。

**Q: 策略回测结果可靠吗？**
A: 回测仅供参考，实际交易需考虑滑点、手续费、流动性等因素。

**Q: 可以修改策略参数吗？**
A: 可以，每个策略的 `parameters` 字段可根据实际情况调整。

**Q: 如何添加自己的策略？**
A: 创建 `StrategyMetadata` 对象并继承 `StrategyExecutor` 实现信号生成逻辑。

---

## 参考资料

- TradingView: https://www.tradingview.com/
- Quantopian: https://github.com/quantopian
- 学术论文：各策略 references 字段列出

---

🦞 **龙虾王量化团队** | 2026
