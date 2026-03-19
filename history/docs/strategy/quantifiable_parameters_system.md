# 🦞 龙虾王量化参数体系

> 完整的可量化参数系统文档 | 版本：v1.0 | 更新日期：2026-03-03

---

## 目录

1. [参数分类总览](#1-参数分类总览)
2. [指标参数](#2-指标参数)
3. [入场参数](#3-入场参数)
4. [出场参数](#4-出场参数)
5. [风控参数](#5-风控参数)
6. [仓位参数](#6-仓位参数)
7. [参数使用最佳实践](#7-参数使用最佳实践)
8. [参数组合方法论](#8-参数组合方法论)

---

## 1. 参数分类总览

### 1.1 五大参数类别

| 类别 | 数量 | 作用 | 调整频率 |
|------|------|------|----------|
| **指标参数** | ~30 个 | 计算技术指标，识别市场状态 | 低频（月度/季度） |
| **入场参数** | ~15 个 | 定义开仓条件，生成交易信号 | 中频（周度） |
| **出场参数** | ~12 个 | 定义平仓条件，锁定利润/止损 | 中频（周度） |
| **风控参数** | ~20 个 | 控制风险敞口，防止极端亏损 | 低频（月度） |
| **仓位参数** | ~15 个 | 决定仓位大小，优化资金效率 | 高频（每日/每笔） |

### 1.2 参数层级结构

```
量化参数体系
├── 战略层 (低频)
│   ├── 风控参数 (最大回撤、总敞口)
│   └── 仓位参数 (基础仓位、杠杆上限)
│
├── 战术层 (中频)
│   ├── 入场参数 (信号阈值、确认条件)
│   └── 出场参数 (止盈止损、移动跟踪)
│
└── 执行层 (高频)
    ├── 指标参数 (均线周期、RSI 阈值)
    └── 动态调整 (波动率调整、相关性限制)
```

---

## 2. 指标参数

### 2.1 趋势指标

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `EMA_FAST` | config.py | 20 | 快速 EMA 周期 | 12-26 |
| `EMA_SLOW` | config.py | 50 | 慢速 EMA 周期 | 30-100 |
| `EMA_LONG` | technical_analysis.py | 200 | 长期 EMA 周期 | 100-250 |
| `MA_PERIODS` | technical_analysis.py | [7, 14, 21, 50, 200] | 均线周期组 | - |
| `MACD_FAST` | technical_analysis.py | 12 | MACD 快线周期 | 10-15 |
| `MACD_SLOW` | technical_analysis.py | 26 | MACD 慢线周期 | 20-30 |
| `MACD_SIGNAL` | technical_analysis.py | 9 | MACD 信号线周期 | 7-12 |

### 2.2 动量指标

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `RSI_PERIOD` | technical_analysis.py | 14 | RSI 计算周期 | 10-20 |
| `RSI_OVERBOUGHT` | adaptive_strategy_engine.py | 70 | RSI 超买阈值 | 65-80 |
| `RSI_OVERSOLD` | adaptive_strategy_engine.py | 30 | RSI 超卖阈值 | 20-35 |
| `RSI_TREND_MIN` | aggressive_strategy.py | 50 | 做多 RSI 下限 | 45-55 |
| `RSI_TREND_MAX` | aggressive_strategy.py | 75 | 做多 RSI 上限 | 70-80 |
| `MOMENTUM_PERIOD` | technical_analysis.py | [10, 30] | 动量计算周期 | - |

### 2.3 波动率指标

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `BB_PERIOD` | technical_analysis.py | 20 | 布林带周期 | 15-25 |
| `BB_STD` | technical_analysis.py | 2.0 | 布林带标准差倍数 | 1.5-2.5 |
| `ATR_PERIOD` | technical_analysis.py | 14 | ATR 计算周期 | 10-20 |
| `VOLATILITY_HIGH` | config.py | 0.05 | 高波动阈值 (5%) | 0.03-0.08 |
| `VOLATILITY_LOW` | config.py | 0.02 | 低波动阈值 (2%) | 0.01-0.03 |

### 2.4 成交量指标

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `VOLUME_MA_PERIOD` | technical_analysis.py | 20 | 成交量均线周期 | 15-30 |
| `VOLUME_RATIO_HIGH` | aggressive_strategy.py | 2.0 | 放量阈值 (2 倍) | 1.5-3.0 |
| `VOLUME_RATIO_LOW` | whale_detector.py | 0.5 | 缩量阈值 (50%) | 0.3-0.7 |

### 2.5 市场状态识别参数

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `BULL_RETURN_50D` | adaptive_strategy_engine.py | 30% | 牛市 50 日涨幅阈值 | 25-40% |
| `BEAR_RETURN_50D` | adaptive_strategy_engine.py | -20% | 熊市 50 日跌幅阈值 | -15%~-30% |
| `CRASH_RETURN_7D` | adaptive_strategy_engine.py | -40% | 崩盘 7 日跌幅阈值 | -30%~-50% |
| `SIDEWAYS_RANGE` | technical_analysis.py | 10% | 震荡市价格波动范围 | 8-15% |

---

## 3. 入场参数

### 3.1 趋势跟踪入场

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `TREND_ENTRY_EMA_ALIGN` | strategy_optimizer.py | True | EMA 多头/空头排列要求 | - |
| `TREND_ENTRY_MACD_CONFIRM` | strategy_optimizer.py | True | MACD 方向确认要求 | - |
| `TREND_MIN_SCORE` | strategy_optimizer.py | 60 | 趋势策略最低评分 | 50-70 |

### 3.2 突破入场

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `BREAKOUT_LOOKBACK` | strategy_optimizer.py | 20 | 突破高低点周期 | 15-30 |
| `BREAKOUT_THRESHOLD` | aggressive_strategy_config.yaml | 0.5% | 突破阈值 | 0.3-1.0% |
| `BREAKOUT_VOLUME_CONFIRM` | aggressive_strategy_config.yaml | True | 需要放量确认 | - |
| `BREAKOUT_MIN_SCORE` | aggressive_strategy.py | 75 | 突破策略最低评分 | 65-85 |

### 3.3 均值回归入场

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `MEAN_REV_RSI_LOW` | strategy_optimizer.py | 30 | RSI 超卖入场 | 25-35 |
| `MEAN_REV_RSI_HIGH` | strategy_optimizer.py | 70 | RSI 超买入场 | 65-80 |
| `MEAN_REV_BB_TOUCH` | strategy_optimizer.py | True | 触及布林带边界 | - |

### 3.4 多周期共振入场

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `MTF_TIMEFRAMES` | config.py | ['1h', '4h', '1d'] | 多周期时间框架 | - |
| `MTF_ALIGNMENT_REQUIRED` | strategy_optimizer.py | True | 多周期方向一致要求 | - |

### 3.5 信号评分系统

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `SCORE_BREAKOUT` | aggressive_strategy_config.yaml | 25 | 突破评分权重 | 20-30 |
| `SCORE_VOLUME` | aggressive_strategy_config.yaml | 25 | 成交量评分权重 | 20-30 |
| `SCORE_RSI` | aggressive_strategy_config.yaml | 20 | RSI 评分权重 | 15-25 |
| `SCORE_EMA` | aggressive_strategy_config.yaml | 15 | EMA 评分权重 | 10-20 |
| `SCORE_MACD` | aggressive_strategy_config.yaml | 15 | MACD 评分权重 | 10-20 |
| `MIN_CONFIRMATION_COUNT` | aggressive_strategy_config.yaml | 4 | 最少确认条件数 | 3-5 |
| `MIN_ENTRY_SCORE` | aggressive_strategy_config.yaml | 75 | 最低入场评分 | 65-85 |

---

## 4. 出场参数

### 4.1 止损参数

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `STOP_LOSS_PCT` | config.py | 5% | 固定止损比例 | 3-8% |
| `STOP_LOSS_ATR_MULT` | aggressive_strategy_config.yaml | 1.5 | ATR 倍数止损 | 1.0-2.5 |
| `STOP_LOSS_MAX_PCT` | aggressive_strategy_config.yaml | 12% | 最大止损比例 | 10-15% |
| `STOP_LOSS_MIN_PCT` | aggressive_strategy_config.yaml | 5% | 最小止损比例 | 3-8% |
| `STOP_LOSS_TYPE` | risk_management.py | "atr_based" | 止损类型 (fixed/atr/volatility) | - |

### 4.2 止盈参数

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `TAKE_PROFIT_PCT` | config.py | 15% | 固定止盈比例 | 10-25% |
| `TAKE_PROFIT_RRR` | aggressive_strategy_config.yaml | 3.0 | 目标盈亏比 | 2.0-4.0 |
| `TAKE_PROFIT_PARTIAL_ENABLE` | aggressive_strategy_config.yaml | True | 启用分批止盈 | - |
| `TAKE_PROFIT_PARTIAL_1` | aggressive_strategy_config.yaml | 30%@2R | 第一档止盈 (2 倍风险时 30%) | - |
| `TAKE_PROFIT_PARTIAL_2` | aggressive_strategy_config.yaml | 30%@4R | 第二档止盈 (4 倍风险时 30%) | - |

### 4.3 移动止盈

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `TRAILING_STOP_ENABLE` | aggressive_strategy_config.yaml | True | 启用移动止盈 | - |
| `TRAILING_ACTIVATION_RRR` | aggressive_strategy_config.yaml | 2.0 | 启动移动止盈的盈亏比 | 1.5-3.0 |
| `TRAILING_TYPE` | aggressive_strategy_config.yaml | "percent" | 跟踪类型 (percent/atr/ema) | - |
| `TRAILING_PCT` | aggressive_strategy.py | 5% | 回撤止盈百分比 | 3-10% |
| `TRAILING_EMA_PERIOD` | adaptive_strategy_engine.py | 20 | EMA 跟踪周期 (如使用 EMA 跟踪) | 10-30 |

### 4.4 时间止损

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `TIME_STOP_ENABLE` | aggressive_strategy_config.yaml | True | 启用时间止损 | - |
| `TIME_STOP_MAX_DAYS` | aggressive_strategy_config.yaml | 10 | 最大持仓天数 | 5-15 |
| `TIME_STOP_EXIT_TYPE` | aggressive_strategy_config.yaml | "market" | 时间止损出场方式 | - |

### 4.5 信号反转出场

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `SIGNAL_REVERSE_EXIT` | strategy_optimizer.py | True | 信号反转时出场 | - |
| `TREND_REVERSAL_EMA_CROSS` | adaptive_strategy_perp.py | True | EMA 交叉确认趋势反转 | - |

---

## 5. 风控参数

### 5.1 资金管理风控

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `INITIAL_CAPITAL` | config.py | 10000 | 初始资金 (USDT) | - |
| `MAX_TOTAL_EXPOSURE` | aggressive_strategy_config.yaml | 120% | 最大总敞口 | 100-150% |
| `MAX_POSITIONS_SIMULTANEOUS` | aggressive_strategy_config.yaml | 3 | 最多同时持仓数 | 2-5 |

### 5.2 回撤风控

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `MAX_DRAWDOWN_THRESHOLD` | risk_management.py | 5% | 最大回撤告警阈值 | 3-8% |
| `DRAWDOWN_LEVEL_1` | aggressive_strategy_config.yaml | 15% | 一级回撤阈值 (减仓 50%) | 10-20% |
| `DRAWDOWN_LEVEL_2` | aggressive_strategy_config.yaml | 25% | 二级回撤阈值 (减仓 75%) | 20-35% |
| `DRAWDOWN_LEVEL_3` | aggressive_strategy_config.yaml | 40% | 三级回撤阈值 (停止交易) | 35-50% |
| `MAX_ACCEPTABLE_DRAWDOWN` | aggressive_strategy_config.yaml | 50% | 策略最大可接受回撤 | 40-60% |

### 5.3 单日风控

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `DAILY_MAX_LOSS_PCT` | aggressive_strategy_config.yaml | 5% | 单日最大亏损比例 | 3-8% |
| `DAILY_MAX_TRADES` | aggressive_strategy_config.yaml | 5 | 单日最多交易次数 | 3-8 |
| `DAILY_MAX_LOSS_AMOUNT` | risk_management.py | 动态计算 | 单日最大亏损金额 | - |

### 5.4 连续止损风控

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `CONSECUTIVE_PAUSE_AFTER` | aggressive_strategy_config.yaml | 3 | 连续亏损后暂停交易 | 2-5 |
| `CONSECUTIVE_PAUSE_HOURS` | aggressive_strategy_config.yaml | 24 | 暂停交易时长 (小时) | 12-48 |
| `CONSECUTIVE_REDUCE_AFTER` | aggressive_strategy_config.yaml | 2 | 连续亏损后减仓 | 2-4 |
| `CONSECUTIVE_REDUCE_PCT` | aggressive_strategy.py | 50% | 连续亏损减仓比例 | 30-70% |

### 5.5 波动率风控

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `VOLATILITY_ADJUST_ENABLE` | aggressive_strategy_config.yaml | True | 启用波动率调整 | - |
| `VOLATILITY_MEASURE_PERIOD` | aggressive_strategy_config.yaml | 20 | 波动率计算周期 | 15-30 |
| `VOLATILITY_HIGH_THRESHOLD` | aggressive_strategy_config.yaml | 5% | 高波动阈值 | 4-8% |
| `VOLATILITY_LOW_THRESHOLD` | aggressive_strategy_config.yaml | 2% | 低波动阈值 | 1-3% |
| `VOLATILITY_ADJUSTMENT_FACTOR` | aggressive_strategy_config.yaml | 30% | 高波动减仓比例 | 20-50% |

### 5.6 相关性风控

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `CORRELATION_ENABLE` | aggressive_strategy_config.yaml | True | 启用相关性限制 | - |
| `MAX_CORRELATION` | aggressive_strategy_config.yaml | 0.80 | 持仓最大相关性 | 0.70-0.90 |

### 5.7 合约特有风险

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `LIQUIDATION_WARNING_THRESHOLD` | adaptive_strategy_perp.py | 10% | 强平警告距离 | 8-15% |
| `LIQUIDATION_REDUCTION_THRESHOLD` | adaptive_strategy_perp.py | 5% | 强平减仓距离 | 3-8% |
| `LIQUIDATION_EMERGENCY_THRESHOLD` | adaptive_strategy_perp.py | 2% | 强平紧急平仓距离 | 1-3% |
| `MAINT_MARGIN_RATE` | adaptive_strategy_perp.py | 0.5% | 维持保证金率 | 0.4-1.0% |
| `FUNDING_RATE_WARNING` | adaptive_strategy_perp.py | -1% | 资金费率预警阈值 | -0.5%~-2% |

---

## 6. 仓位参数

### 6.1 基础仓位

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `POSITION_SIZE` | config.py | 10% | 单笔基础仓位 | 5-15% |
| `BASE_POSITION_SIZE` | aggressive_strategy_config.yaml | 30% | 激进策略基础仓位 | 20-40% |
| `RISK_PER_TRADE` | risk_management.py | 2% | 每笔交易风险 | 1-3% |

### 6.2 动态仓位调整

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `DYNAMIC_POSITION_ENABLE` | aggressive_strategy_config.yaml | True | 启用动态仓位 | - |
| `TREND_MULTIPLIER` | aggressive_strategy_config.yaml | 1.5 | 强趋势仓位倍数 | 1.2-2.0 |
| `VOLUME_MULTIPLIER` | aggressive_strategy_config.yaml | 1.33 | 放量仓位倍数 | 1.2-1.5 |
| `CONVICTION_MULTIPLIER` | aggressive_strategy_config.yaml | 1.2 | 高置信度仓位倍数 | 1.1-1.5 |
| `MAX_POSITION_SIZE` | aggressive_strategy_config.yaml | 80% | 单笔最大仓位 | 60-100% |

### 6.3 凯利公式仓位

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `KELLY_MAX_FRACTION` | risk_management.py | 25% | 凯利公式最大仓位 | 15-35% |
| `KELLY_DIVISOR` | risk_management.py | 2.0 | 凯利除数 (半凯利) | 1.5-3.0 |
| `KELLY_CONFIDENCE_ADJ` | risk_management.py | 1.0 | 信号置信度调整 | 0.5-1.0 |

### 6.4 币种分级仓位

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `TIER_1_ALLOCATION` | aggressive_strategy_config.yaml | 40% | 主流币资金分配 | 35-50% |
| `TIER_2_ALLOCATION` | aggressive_strategy_config.yaml | 35% | 主要币种资金分配 | 30-40% |
| `TIER_3_ALLOCATION` | aggressive_strategy_config.yaml | 25% | 次要币种资金分配 | 15-30% |
| `TIER_1_POSITION_SIZE` | adaptive_strategy_engine.py | 30% | 主流币单笔仓位 | 25-40% |
| `TIER_2_POSITION_SIZE` | adaptive_strategy_engine.py | 15% | 主要币种单笔仓位 | 10-20% |
| `TIER_3_POSITION_SIZE` | adaptive_strategy_engine.py | 5-10% | 次要币种单笔仓位 | 3-15% |

### 6.5 杠杆参数

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `LEVERAGE_DEFAULT` | adaptive_strategy_engine.py | 1.0-3.0x | 默认杠杆 | - |
| `LEVERAGE_MAJOR` | adaptive_strategy_engine.py | 1.0-2.0x | 主流币杠杆 | 1-3x |
| `LEVERAGE_ALTCOIN` | adaptive_strategy_engine.py | 2.0-3.0x | 山寨币杠杆 | 1-5x |
| `LEVERAGE_MEME` | adaptive_strategy_engine.py | 3.0-5.0x | 模因币杠杆 | 2-5x |
| `LEVERAGE_BY_VOLATILITY` | adaptive_strategy_perp.py | 动态 | 基于波动率的杠杆 | - |

### 6.6 风险平价仓位

| 参数名 | 代码位置 | 默认值 | 说明 | 建议范围 |
|--------|----------|--------|------|----------|
| `RISK_PARITY_ENABLE` | aggressive_strategy_config.yaml | True | 启用风险平价 | - |
| `TARGET_RISK_PER_TRADE` | aggressive_strategy_config.yaml | 2% | 目标每笔风险 | 1-3% |
| `ATR_RISK_ADJUST` | strategy_optimizer.py | True | 基于 ATR 调整仓位 | - |

---

## 7. 参数使用最佳实践

### 7.1 参数调优原则

#### 1️⃣ 分层调优法

```
第一层：战略参数 (月度审查)
├── 最大回撤阈值
├── 总敞口限制
└── 仓位上限

第二层：战术参数 (周度审查)
├── 入场评分阈值
├── 止盈止损比例
└── 动态仓位乘数

第三层：执行参数 (每日优化)
├── 指标周期
├── 信号权重
└── 波动率调整
```

#### 2️⃣ 参数敏感性测试

```python
# 示例：参数敏感性分析
param_ranges = {
    'STOP_LOSS_PCT': [0.03, 0.05, 0.08, 0.10],
    'TAKE_PROFIT_PCT': [0.10, 0.15, 0.20, 0.25],
    'POSITION_SIZE': [0.05, 0.10, 0.15, 0.20]
}

# 对每个参数组合进行回测
# 记录夏普比率、最大回撤、胜率
# 找出最优参数组合
```

#### 3️⃣ 参数稳健性检验

- **样本外测试**: 用 80% 数据训练，20% 数据验证
- **跨市场测试**: 在 BTC、ETH、山寨币上分别验证
- **跨周期测试**: 在牛市、熊市、震荡市中分别验证
- **参数扰动测试**: 参数±10% 变化，观察绩效稳定性

### 7.2 参数耦合关系

#### 强耦合参数组

| 参数组 | 耦合关系 | 调优建议 |
|--------|----------|----------|
| `止损` + `止盈` | 盈亏比 = 止盈/止损 | 一起调整，保持目标盈亏比 |
| `仓位` + `止损` | 单笔风险 = 仓位×止损 | 反向调整，控制单笔风险恒定 |
| `入场评分` + `胜率` | 高评分→高胜率 | 根据历史胜率反推评分阈值 |
| `波动率` + `仓位` | 高波动→低仓位 | 动态联动，风险平价 |

#### 参数耦合公式

```python
# 单笔风险计算公式
risk_per_trade = position_size * stop_loss_pct

# 目标盈亏比公式
target_rrr = take_profit_pct / stop_loss_pct

# 凯利公式
kelly_fraction = (win_rate * profit_factor - (1 - win_rate)) / profit_factor

# 动态仓位 (基于波动率)
dynamic_position = base_position * (base_volatility / current_volatility)
```

### 7.3 参数优化流程

```
1. 基线测试
   └── 使用默认参数运行回测，建立绩效基线

2. 单参数优化
   └── 每次只调整一个参数，找出最优值

3. 参数组合优化
   └── 对强耦合参数组进行网格搜索

4. 稳健性验证
   └── 样本外测试 + 跨市场测试

5. 实盘验证
   └── 小资金实盘测试，观察滑点和执行
```

### 7.4 参数文档化

每个参数应记录：

```yaml
参数名：STOP_LOSS_PCT
默认值：0.05 (5%)
位置：config.py
作用：定义单笔交易最大亏损比例
建议范围：3-8%
耦合参数：TAKE_PROFIT_PCT, POSITION_SIZE
调优频率：周度
历史最优值：
  - BTC 牛市：4%
  - BTC 熊市：6%
  - 山寨币：7%
备注：高波动市场应放宽止损
```

---

## 8. 参数组合方法论

### 8.1 策略类型与参数组合

#### 趋势跟踪策略参数组合

```yaml
策略：趋势跟踪
市场状态：牛市/熊市
参数组合:
  入场:
    - EMA_FAST: 20
    - EMA_SLOW: 50
    - MACD_CONFIRM: true
    - MIN_SCORE: 60
  
  出场:
    - STOP_LOSS_TYPE: "atr_based"
    - STOP_LOSS_ATR_MULT: 2.0
    - TAKE_PROFIT_RRR: 2.5
    - TRAILING_STOP: true
    - TRAILING_EMA_PERIOD: 20
  
  仓位:
    - BASE_POSITION: 25%
    - TREND_MULTIPLIER: 1.5
    - MAX_POSITION: 60%
  
  风控:
    - MAX_DRAWDOWN: 25%
    - DAILY_MAX_LOSS: 5%
```

#### 突破策略参数组合

```yaml
策略：突破交易
市场状态：震荡转趋势
参数组合:
  入场:
    - BREAKOUT_LOOKBACK: 20
    - BREAKOUT_THRESHOLD: 0.5%
    - VOLUME_RATIO_HIGH: 2.0
    - MIN_CONFIRMATION_COUNT: 4
    - MIN_ENTRY_SCORE: 75
  
  出场:
    - STOP_LOSS_PCT: 5%
    - TAKE_PROFIT_RRR: 3.0
    - TIME_STOP_MAX_DAYS: 7
    - SIGNAL_REVERSE_EXIT: true
  
  仓位:
    - BASE_POSITION: 20%
    - CONVICTION_MULTIPLIER: 1.3
    - MAX_POSITION: 50%
  
  风控:
    - MAX_DRAWDOWN: 20%
    - CONSECUTIVE_PAUSE_AFTER: 3
```

#### 均值回归策略参数组合

```yaml
策略：均值回归
市场状态：震荡市
参数组合:
  入场:
    - RSI_OVERBOUGHT: 70
    - RSI_OVERSOLD: 30
    - BB_TOUCH: true
    - MIN_SCORE: 65
  
  出场:
    - STOP_LOSS_PCT: 8%
    - TAKE_PROFIT_PCT: 15%
    - RSI_EXIT_LONG: 60
    - RSI_EXIT_SHORT: 40
  
  仓位:
    - BASE_POSITION: 15%
    - MAX_POSITION: 40%
  
  风控:
    - MAX_DRAWDOWN: 15%
    - TIME_STOP_MAX_DAYS: 14
```

#### 资金费率套利策略参数组合

```yaml
策略：资金费率套利
市场状态：任意 (合约专用)
参数组合:
  入场:
    - FUNDING_RATE_THRESHOLD: 1%
    - MIN_ANNUALIZED_YIELD: 36.5%
    - HOLD_TIME_MAX: 8 小时
  
  出场:
    - FUNDING_RATE_EXIT: <0 (转负)
    - TIME_EXIT: 8 小时 (结算后)
  
  仓位:
    - BASE_POSITION: 30%
    - LEVERAGE: 1-3x (根据波动率)
    - MAX_POSITION: 60%
  
  风控:
    - LIQUIDATION_BUFFER: 10%
    - DAILY_MAX_LOSS: 3%
```

### 8.2 市场状态自适应参数

#### 牛市参数配置

```yaml
市场状态：牛市
特征: 价格>EMA200, 50 日涨幅>30%

参数调整:
  入场:
    - MIN_ENTRY_SCORE: 70 → 65 (放宽)
    - RSI_TREND_MAX: 75 → 80 (允许更高)
  
  出场:
    - TRAILING_STOP: 启用
    - TAKE_PROFIT_RRR: 3.0 → 4.0 (让利润奔跑)
  
  仓位:
    - BASE_POSITION: 25% → 35%
    - MAX_POSITION: 60% → 80%
  
  风控:
    - MAX_DRAWDOWN: 25% → 35% (放宽)
```

#### 熊市参数配置

```yaml
市场状态：熊市
特征：价格<EMA200, 50 日跌幅>20%

参数调整:
  入场:
    - MIN_ENTRY_SCORE: 65 → 75 (收紧)
    - 只做空不做多
  
  出场:
    - STOP_LOSS_PCT: 5% → 4% (更紧)
    - TAKE_PROFIT_RRR: 3.0 → 2.5 (快速止盈)
  
  仓位:
    - BASE_POSITION: 25% → 15%
    - MAX_POSITION: 60% → 40%
  
  风控:
    - MAX_DRAWDOWN: 25% → 15% (收紧)
    - DAILY_MAX_LOSS: 5% → 3%
```

#### 震荡市参数配置

```yaml
市场状态：震荡市
特征：价格围绕 EMA200 波动，50 日涨跌幅<10%

参数调整:
  入场:
    - 策略切换：均值回归
    - RSI_OVERBOUGHT: 70
    - RSI_OVERSOLD: 30
  
  出场:
    - TAKE_PROFIT_PCT: 15% (固定止盈)
    - TIME_STOP_MAX_DAYS: 14
  
  仓位:
    - BASE_POSITION: 20%
    - MAX_POSITION: 50%
  
  风控:
    - MAX_DRAWDOWN: 20%
```

### 8.3 币种差异化参数

#### 主流币 (BTC/ETH) 参数

```yaml
币种等级：TIER_1 (主流币)
特征：流动性好，波动率适中，趋势性强

参数配置:
  入场:
    - MIN_SCORE: 65
    - VOLUME_RATIO_HIGH: 1.5 (放量要求低)
  
  出场:
    - STOP_LOSS_ATR_MULT: 2.0 (放宽)
    - TRAILING_STOP: true
  
  仓位:
    - BASE_POSITION: 30%
    - MAX_POSITION: 80%
    - LEVERAGE: 1-2x
  
  风控:
    - CORRELATION_LIMIT: 0.9 (可高度相关)
```

#### 山寨币参数

```yaml
币种等级：TIER_2/3 (山寨币)
特征：波动率高，流动性差，易被操纵

参数配置:
  入场:
    - MIN_SCORE: 75 (收紧)
    - VOLUME_RATIO_HIGH: 2.5 (放量要求高)
  
  出场:
    - STOP_LOSS_ATR_MULT: 1.5 (收紧)
    - TAKE_PROFIT_RRR: 3.5 (提高盈亏比)
  
  仓位:
    - BASE_POSITION: 15%
    - MAX_POSITION: 40%
    - LEVERAGE: 1x (不用杠杆)
  
  风控:
    - CORRELATION_LIMIT: 0.7 (降低相关性)
```

#### 模因币 (DOGE/SHIB) 参数

```yaml
币种等级：MEME (模因币)
特征：极高波动，社交媒体驱动，高风险

参数配置:
  入场:
    - MIN_SCORE: 85 (极严)
    - 只做强动量突破
  
  出场:
    - STOP_LOSS_PCT: 8% (放宽)
    - TAKE_PROFIT_PCT: 30% (快速止盈)
    - TIME_STOP_MAX_DAYS: 3
  
  仓位:
    - BASE_POSITION: 5%
    - MAX_POSITION: 15%
    - LEVERAGE: 1x
  
  风控:
    - DAILY_MAX_TRADES: 2
    - 禁止同时持有多个 MEME 币
```

### 8.4 参数优化实战案例

#### 案例 1：突破策略参数优化

**目标**: 提高突破策略胜率从 45% 到 55%

**步骤**:

1. **基线测试**: 默认参数回测，胜率 45%，盈亏比 2.8:1

2. **单参数优化**:
   - 调整 `MIN_ENTRY_SCORE`: 65 → 75，胜率提升至 52%
   - 调整 `VOLUME_RATIO_HIGH`: 1.5 → 2.0，胜率提升至 54%
   - 调整 `BREAKOUT_THRESHOLD`: 0.3% → 0.5%，胜率提升至 55%

3. **参数组合验证**:
   ```yaml
   最优组合:
     - MIN_ENTRY_SCORE: 75
     - VOLUME_RATIO_HIGH: 2.0
     - BREAKOUT_THRESHOLD: 0.5%
     - MIN_CONFIRMATION_COUNT: 4
   ```

4. **结果**: 胜率 55%，盈亏比 3.2:1，夏普比率 1.8

#### 案例 2：风控参数优化

**目标**: 降低最大回撤从 35% 到 20%

**步骤**:

1. **问题诊断**: 连续亏损期仓位过大，导致回撤失控

2. **参数调整**:
   ```yaml
   调整前:
     - CONSECUTIVE_PAUSE_AFTER: 5
     - DAILY_MAX_LOSS: 8%
     - DRAWDOWN_LEVEL_1: 20%
   
   调整后:
     - CONSECUTIVE_PAUSE_AFTER: 3
     - DAILY_MAX_LOSS: 5%
     - DRAWDOWN_LEVEL_1: 15%
     - CONSECUTIVE_REDUCE_AFTER: 2 (新增)
   ```

3. **结果**: 最大回撤降至 18%，年化收益从 120% 降至 85%，但夏普比率从 1.2 提升至 1.6

---

## 附录 A：参数速查表

### A.1 核心参数 (必须配置)

| 参数 | 默认值 | 位置 | 说明 |
|------|--------|------|------|
| `INITIAL_CAPITAL` | 10000 | config.py | 初始资金 |
| `POSITION_SIZE` | 10% | config.py | 基础仓位 |
| `STOP_LOSS` | 5% | config.py | 止损比例 |
| `TAKE_PROFIT` | 15% | config.py | 止盈比例 |
| `MAX_DRAWDOWN_THRESHOLD` | 5% | risk_management.py | 回撤告警 |

### A.2 进阶参数 (策略优化)

| 参数 | 默认值 | 位置 | 说明 |
|------|--------|------|------|
| `MIN_ENTRY_SCORE` | 75 | aggressive_strategy.py | 入场评分阈值 |
| `TRAILING_STOP` | true | aggressive_strategy_config.yaml | 移动止盈 |
| `KELLY_DIVISOR` | 2.0 | risk_management.py | 凯利除数 |
| `DYNAMIC_POSITION` | true | aggressive_strategy_config.yaml | 动态仓位 |

### A.3 高级参数 (精细调优)

| 参数 | 默认值 | 位置 | 说明 |
|------|--------|------|------|
| `CORRELATION_LIMIT` | 0.80 | aggressive_strategy_config.yaml | 相关性限制 |
| `VOLATILITY_ADJUST` | 30% | aggressive_strategy_config.yaml | 波动率调整 |
| `FUNDING_RATE_THRESHOLD` | 1% | adaptive_strategy_perp.py | 资金费率阈值 |

---

## 附录 B：参数优化检查清单

### 每次参数调整前检查

- [ ] 是否记录了调整前的基线绩效？
- [ ] 是否理解该参数与其他参数的耦合关系？
- [ ] 是否进行了样本内优化 + 样本外验证？
- [ ] 是否测试了不同市场状态下的表现？
- [ ] 是否考虑了交易成本和滑点影响？
- [ ] 调整幅度是否在合理范围内 (±20%)？
- [ ] 是否有足够的交易样本 (至少 30 笔交易)？

### 参数上线实盘前检查

- [ ] 回测周期是否覆盖牛熊转换 (至少 2 年)？
- [ ] 最大回撤是否在可接受范围内？
- [ ] 夏普比率是否>1.0？
- [ ] 胜率是否>40%？
- [ ] 盈亏比是否>2.0？
- [ ] 是否进行了小资金实盘测试？
- [ ] 是否设置了监控告警？

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-03-03 | 初始版本，整合所有量化参数 |

---

**🦞 龙虾王量化团队 | 参数是策略的灵魂，调优是永恒的艺术**
