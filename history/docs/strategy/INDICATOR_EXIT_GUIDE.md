# 🦞 指标条件止盈止损使用指南

## 功能概述

新增指标条件止盈止损功能，支持：

1. **多种指标条件类型**
   - RSI 超买/超卖（RSI>70 止盈，RSI<30 止损）
   - MACD 死叉/金叉（MACD 死叉止盈，MACD 金叉止损）
   - 布林带触及上下轨
   - EMA 死叉/金叉

2. **多条件 OR 逻辑**
   - 支持多个止盈条件，任一满足即止盈
   - 支持多个止损条件，任一满足即止损
   - 可与固定止盈止损并行使用

3. **灵活配置**
   - 支持 Python 代码配置
   - 支持 Web 界面配置
   - 支持 JSON 配置导入

---

## 快速开始

### 示例 1: RSI>70 止盈 + 固定止损

```python
from backtest_framework_v2 import *
from indicator_based_exit import *

# 1. 创建指标条件退出配置
exit_config = ExitConfig(
    take_profit_conditions=[
        ExitCondition.rsi_take_profit(70),      # RSI>70 止盈
    ],
    stop_loss_conditions=[
        ExitCondition.fixed_stop_loss(0.05),    # 固定 5% 止损
    ]
)

# 2. 创建指标条件止盈配置
take_profit = TakeProfitConfig.indicator_based(exit_config)

# 3. 创建回测引擎
engine = BacktestEngine(
    initial_capital=10000,
    stop_loss=StopLossConfig.fixed(0.05),
    take_profit=take_profit,
    position_size=0.1
)

# 4. 配置入场指标
indicator_configs = [
    IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=30),
    IndicatorConfig.macd_cross(bullish=True),
]
signal_gen = SignalGenerator(indicator_configs)

# 5. 运行回测
df = pd.read_csv('data/BTCUSDT_30m.csv', index_col=0, parse_dates=True)
result = engine.run_backtest(df, signal_gen, symbol='BTCUSDT')

# 6. 查看退出原因
for trade in result.trades:
    print(f"交易{trade.trade_id}: 退出原因 = {trade.exit_reason}")
    # 可能输出：TP_RSI_ABOVE, TP_FIXED, SL_FIXED, 等
```

---

### 示例 2: 多条件止盈（OR 逻辑）

```python
# 三个止盈条件，任一满足即止盈
exit_config = ExitConfig(
    take_profit_conditions=[
        ExitCondition.rsi_take_profit(70),           # 条件 1: RSI>70
        ExitCondition.macd_dead_cross(),             # 条件 2: MACD 死叉
        ExitCondition.fixed_take_profit(0.15),       # 条件 3: 固定 15% 止盈
    ],
    stop_loss_conditions=[
        ExitCondition.fixed_stop_loss(0.05),         # 固定 5% 止损
        ExitCondition.rsi_stop_loss(30),             # RSI<30 止损
    ]
)

take_profit = TakeProfitConfig.indicator_based(exit_config)
```

**触发逻辑：**
- 如果 RSI>70 → 止盈 ✅
- 或者 MACD 死叉 → 止盈 ✅
- 或者 价格达到 15% 利润 → 止盈 ✅
- 三个条件独立判断，任一满足即退出

---

### 示例 3: 激进策略配置

```python
# 使用预设的激进策略配置
exit_config = ExitConfig.default_aggressive()

# 等价于：
exit_config = ExitConfig(
    take_profit_conditions=[
        ExitCondition.rsi_take_profit(70),
        ExitCondition.macd_dead_cross(),
        ExitCondition.fixed_take_profit(0.15)
    ],
    stop_loss_conditions=[
        ExitCondition.rsi_stop_loss(30),
        ExitCondition.fixed_stop_loss(0.05)
    ]
)
```

---

### 示例 4: 保守策略配置

```python
# 使用预设的保守策略配置
exit_config = ExitConfig.default_conservative()

# 等价于：
exit_config = ExitConfig(
    take_profit_conditions=[
        ExitCondition.rsi_take_profit(80),           # RSI>80 才止盈（更宽松）
        ExitCondition.bb_upper(),                    # 触及布林带上轨
        ExitCondition.fixed_take_profit(0.10)        # 固定 10% 止盈
    ],
    stop_loss_conditions=[
        ExitCondition.fixed_stop_loss(0.03)          # 严格 3% 止损
    ]
)
```

---

## 支持的指标条件类型

### 止盈条件

| 类型 | 方法 | 说明 | 参数 |
|------|------|------|------|
| RSI 超买 | `ExitCondition.rsi_take_profit(threshold)` | RSI 大于阈值时止盈 | threshold: 默认 70 |
| MACD 死叉 | `ExitCondition.macd_dead_cross()` | MACD 下穿信号线时止盈 | 无 |
| 布林带上轨 | `ExitCondition.bb_upper()` | 价格触及布林带上轨时止盈 | 无 |
| EMA 死叉 | `ExitCondition.ema_dead_cross(fast, slow)` | 快 EMA 下穿慢 EMA 时止盈 | fast:12, slow:26 |
| 固定止盈 | `ExitCondition.fixed_take_profit(percent)` | 达到固定利润率止盈 | percent: 0.15 |

### 止损条件

| 类型 | 方法 | 说明 | 参数 |
|------|------|------|------|
| RSI 超卖 | `ExitCondition.rsi_stop_loss(threshold)` | RSI 小于阈值时止损 | threshold: 默认 30 |
| MACD 金叉 | `ExitCondition.macd_gold_cross()` | MACD 上穿信号线时止损 | 无 |
| 布林带下轨 | `ExitCondition.bb_lower()` | 价格触及布林带下轨时止损 | 无 |
| EMA 金叉 | `ExitCondition.ema_gold_cross(fast, slow)` | 快 EMA 上穿慢 EMA 时止损 | fast:12, slow:26 |
| 固定止损 | `ExitCondition.fixed_stop_loss(percent)` | 达到固定损失率止损 | percent: 0.05 |

---

## Web 界面配置

### 步骤

1. 访问回测框架页面：`http://localhost:8000/backtest_framework.html`

2. 在"止盈止损"部分，选择 **止盈模式 = 指标条件止盈 (新)**

3. 配置止盈条件（最多 3 个）：
   - 条件 1：RSI > 70
   - 条件 2：MACD 死叉
   - 条件 3：固定止盈 15%

4. 配置止损条件（最多 2 个）：
   - 条件 1：固定止损 5%
   - 条件 2：RSI < 30

5. 点击"运行回测"

### Web 配置示例（JSON）

```json
{
  "takeProfitMode": "indicator",
  "indicatorExitConfig": {
    "take_profit": [
      { "type": "rsi_above", "threshold": 0.7 },
      { "type": "macd_dead_cross" },
      { "type": "fixed_tp", "threshold": 0.15 }
    ],
    "stop_loss": [
      { "type": "fixed_sl", "threshold": 0.05 },
      { "type": "rsi_below", "threshold": 0.3 }
    ]
  }
}
```

---

## 退出原因说明

回测结果中的 `exit_reason` 字段会显示具体的退出触发原因：

### 止盈原因

| 退出原因 | 说明 |
|---------|------|
| `TP_RSI_ABOVE` | RSI 超过阈值止盈 |
| `TP_MACD_DEAD_CROSS` | MACD 死叉止盈 |
| `TP_BB_UPPER` | 触及布林带上轨止盈 |
| `TP_EMA_DEAD_CROSS` | EMA 死叉止盈 |
| `TP_FIXED` | 固定止盈 |
| `TP_TRAILING` | 移动止盈 |
| `TP_RR` | 盈亏比倍数止盈 |

### 止损原因

| 退出原因 | 说明 |
|---------|------|
| `SL_RSI_BELOW` | RSI 低于阈值止损 |
| `SL_MACD_GOLD_CROSS` | MACD 金叉止损 |
| `SL_BB_LOWER` | 触及布林带下轨止损 |
| `SL_EMA_GOLD_CROSS` | EMA 金叉止损 |
| `SL_FIXED` | 固定止损 |
| `SL_TRAILING` | 移动止损 |
| `SL_TIME` | 时间止损 |

---

## 实战建议

### 1. 趋势跟踪策略

```python
# 趋势跟踪：让利润奔跑，严格止损
exit_config = ExitConfig(
    take_profit_conditions=[
        ExitCondition.macd_dead_cross(),             # MACD 死叉才止盈（让趋势充分发展）
        ExitCondition.trailing_take_profit(0.03),    # 3% 移动止盈
    ],
    stop_loss_conditions=[
        ExitCondition.fixed_stop_loss(0.05),         # 5% 固定止损
    ]
)
```

### 2. 震荡策略

```python
# 震荡市：快速止盈，快速止损
exit_config = ExitConfig(
    take_profit_conditions=[
        ExitCondition.rsi_take_profit(70),           # RSI 超买即止盈
        ExitCondition.bb_upper(),                    # 触及布林带上轨即止盈
        ExitCondition.fixed_take_profit(0.08),       # 8% 固定止盈
    ],
    stop_loss_conditions=[
        ExitCondition.fixed_stop_loss(0.03),         # 3% 严格止损
        ExitCondition.rsi_stop_loss(30),             # RSI 超卖即止损
    ]
)
```

### 3. 突破策略

```python
# 突破策略：宽止损，大止盈
exit_config = ExitConfig(
    take_profit_conditions=[
        ExitCondition.fixed_take_profit(0.25),       # 25% 大止盈
        ExitCondition.rsi_take_profit(80),           # RSI 极度超买才止盈
    ],
    stop_loss_conditions=[
        ExitCondition.fixed_stop_loss(0.08),         # 8% 宽止损
    ]
)
```

---

## API 参考

### ExitConfig

```python
class ExitConfig:
    def __init__(self, 
                 take_profit_conditions: List[ExitCondition] = None,
                 stop_loss_conditions: List[ExitCondition] = None):
        pass
    
    def add_take_profit(self, condition: ExitCondition) -> ExitConfig
    def add_stop_loss(self, condition: ExitCondition) -> ExitConfig
    
    @classmethod
    def default_aggressive(cls) -> ExitConfig
    @classmethod
    def default_conservative(cls) -> ExitConfig
```

### ExitCondition

```python
class ExitCondition:
    def __init__(self, 
                 condition_type: ExitConditionType,
                 threshold: float = 0.0,
                 params: Dict = None):
        pass
    
    @classmethod
    def rsi_take_profit(cls, threshold: float = 70) -> ExitCondition
    @classmethod
    def rsi_stop_loss(cls, threshold: float = 30) -> ExitCondition
    @classmethod
    def macd_dead_cross(cls) -> ExitCondition
    @classmethod
    def macd_gold_cross(cls) -> ExitCondition
    @classmethod
    def bb_upper(cls) -> ExitCondition
    @classmethod
    def bb_lower(cls) -> ExitCondition
    @classmethod
    def ema_dead_cross(cls, fast: int = 12, slow: int = 26) -> ExitCondition
    @classmethod
    def ema_gold_cross(cls, fast: int = 12, slow: int = 26) -> ExitCondition
    @classmethod
    def fixed_take_profit(cls, percent: float = 0.15) -> ExitCondition
    @classmethod
    def fixed_stop_loss(cls, percent: float = 0.05) -> ExitCondition
```

### IndicatorBasedExitChecker

```python
class IndicatorBasedExitChecker:
    def __init__(self, exit_config: ExitConfig):
        pass
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame
    def check_take_profit(self, df, idx, direction, entry_price, current_price) -> Tuple[bool, str]
    def check_stop_loss(self, df, idx, direction, entry_price, current_price) -> Tuple[bool, str]
    def get_active_conditions_summary(self) -> Dict
```

---

## 测试与验证

### 运行演示

```bash
cd ~/.openclaw/workspace/quant
python3 indicator_based_exit.py
python3 backtest_framework_v2.py
```

### 回测验证

```bash
# 使用指标条件止盈进行回测
python3 -c "
from backtest_framework_v2 import *
from indicator_based_exit import *
import pandas as pd

# 配置
exit_config = ExitConfig.default_aggressive()
take_profit = TakeProfitConfig.indicator_based(exit_config)

# 回测
engine = BacktestEngine(take_profit=take_profit)
df = pd.read_csv('data/BTCUSDT_30m.csv', index_col=0, parse_dates=True)

# 配置入场信号
signal_gen = SignalGenerator([
    IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=30),
    IndicatorConfig.macd_cross(bullish=True)
])

result = engine.run_backtest(df, signal_gen, 'BTCUSDT')
print(f'总收益：{result.total_return_pct:.2f}%')
print(f'胜率：{result.win_rate:.1f}%')

# 查看退出原因分布
from collections import Counter
exit_reasons = [t.exit_reason for t in result.trades]
print(f'退出原因分布：{Counter(exit_reasons)}')
"
```

---

## 常见问题

### Q1: 多个止盈条件如何工作？

**A:** 采用 OR 逻辑，任一条件满足即触发止盈。例如：
- 条件 1: RSI>70
- 条件 2: MACD 死叉
- 条件 3: 固定 15% 止盈

如果价格先达到 15% 利润，即使 RSI 还没到 70，也会止盈。

### Q2: 指标条件止盈和固定止盈能同时用吗？

**A:** 可以！指标条件止盈是一种独立的止盈模式，但也可以在 ExitConfig 中包含固定止盈条件作为多个 OR 条件之一。

### Q3: 如何查看具体是哪个指标触发的退出？

**A:** 查看交易记录的 `exit_reason` 字段，会显示如 `TP_RSI_ABOVE`、`TP_MACD_DEAD_CROSS` 等具体原因。

### Q4: 指标条件止损和止盈可以同时使用吗？

**A:** 可以！ExitConfig 同时支持配置止盈条件列表和止损条件列表，两者独立工作。

---

## 更新日志

### v1.0 (2026-03-03)
- ✅ 新增指标条件止盈止损模块
- ✅ 支持 RSI、MACD、布林带、EMA 交叉等指标
- ✅ 支持多条件 OR 逻辑
- ✅ 集成到 backtest_framework_v2.py
- ✅ 更新 Web 界面支持配置
- ✅ 添加预设策略配置（激进/保守）

---

🦞 Happy Trading!
