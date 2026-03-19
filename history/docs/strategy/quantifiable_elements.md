# 🦞 龙虾王量化交易 - 可量化要素总览

> 本文档整理了量化交易系统中所有可量化的要素，包括技术指标、触发条件、止盈止损、仓位管理等核心参数。

---

## 一、技术指标类 (Technical Indicators)

### 1.1 趋势指标

| 指标名称 | 代码标识 | 参数 | 典型值 | 说明 |
|---------|---------|------|--------|------|
| 指数移动平均线 | `EMA` | `span` | 12, 26, 20, 50, 200 | 快速/慢速 EMA 交叉判断趋势 |
| 简单移动平均线 | `SMA/MA` | `period` | 7, 14, 21, 50, 200 | 均线排列判断多空 |
| MACD | `MACD` | `fast=12, slow=26, signal=9` | 默认 | 金叉/死叉信号 |
| ADX | `ADX` | `period=14` | >25 为强趋势 | 趋势强度指标 |

**量化规则示例：**
```python
# EMA 多头排列
ema_bullish = ema20 > ema50 and ema50 > ema200

# MACD 金叉
macd_golden_cross = macd > macd_signal and macd_prev <= macd_signal_prev
```

### 1.2 动量指标

| 指标名称 | 代码标识 | 参数 | 典型值 | 说明 |
|---------|---------|------|--------|------|
| 相对强弱指数 | `RSI` | `period=14` | 30/70 超卖超买 | 判断超买超卖 |
| 动量 | `MOM` | `period=10/30` | - | 价格变化速率 |
| 随机指标 | `KDJ` | `n=9, m1=3, m2=3` | - | 短线超买超卖 |

**量化规则示例：**
```python
# RSI 区间判断
rsi_bullish = 50 < rsi < 70
rsi_bearish = 30 < rsi < 50
rsi_overbought = rsi > 75
rsi_oversold = rsi < 25
```

### 1.3 波动率指标

| 指标名称 | 代码标识 | 参数 | 典型值 | 说明 |
|---------|---------|------|--------|------|
| 平均真实波动范围 | `ATR` | `period=14` | - | 衡量波动幅度 |
| 布林带宽度 | `BB_Width` | `period=20, std=2` | - | 波动率压缩/扩张 |
| 历史波动率 | `HV` | `period=20/30` | 年化% | 历史价格波动 |

**量化规则示例：**
```python
# ATR 止损距离
stop_distance = atr * 1.5

# 布林带突破
bb_breakout_upper = close > bb_upper
bb_breakout_lower = close < bb_lower
```

### 1.4 成交量指标

| 指标名称 | 代码标识 | 参数 | 典型值 | 说明 |
|---------|---------|------|--------|------|
| 成交量移动平均 | `Volume_MA` | `period=20` | - | 平均成交水平 |
| 成交量比率 | `Volume_Ratio` | - | >1.5 放量 | 当前量/平均量 |
| 资金流量 | `MFI` | `period=14` | - | 量价结合 |

**量化规则示例：**
```python
# 放量确认
volume_confirmed = volume > volume_ma20 * 2.0

# 缩量回调
volume_shrink = volume < volume_ma20 * 0.7
```

### 1.5 支撑阻力指标

| 指标名称 | 代码标识 | 参数 | 典型值 | 说明 |
|---------|---------|------|--------|------|
| 布林带 | `Bollinger` | `period=20, std=2` | - | 动态支撑阻力 |
| 唐奇安通道 | `Donchian` | `period=20` | - | N 日高低点 |
| 枢轴点 | `Pivot` | - | - | 日内关键位 |

---

## 二、触发条件类 (Entry/Exit Triggers)

### 2.1 入场触发条件

#### 2.1.1 突破类入场
```python
# 20 日高点突破
breakout_long = close > highest(high, 20) * 0.995

# 放量突破
breakout_confirmed = breakout_long and volume > volume_ma * 1.5

# 区间突破 (震荡市)
range_breakout = close > resistance_level or close < support_level
```

| 条件 ID | 条件名称 | 量化公式 | 权重 |
|--------|---------|---------|------|
| `BREAKOUT_20D` | 20 日突破 | `close > highest(20)` | 25 |
| `VOLUME_2X` | 成交量 2 倍 | `volume > ma20 * 2` | 25 |
| `EMA_BULLISH` | EMA 多头 | `ema20 > ema50` | 15 |
| `MACD_GOLDEN` | MACD 金叉 | `macd > signal` | 15 |
| `RSI_TREND` | RSI 趋势 | `50 < RSI < 70` | 20 |

#### 2.1.2 回调类入场
```python
# 回调至 EMA20 支撑
pullback_entry = low <= ema20 * 1.005 and close > ema20

# RSI 超卖反弹
oversold_bounce = rsi < 30 and rsi_prev < 30 and rsi > rsi_prev
```

#### 2.1.3 评分系统 (多条件确认)
```python
# 4 重确认系统 (至少 4 项确认才入场)
confirmations = sum([
    breakout_confirmed,    # 突破确认
    volume_confirmed,      # 成交量确认
    rsi_confirmed,         # RSI 确认
    ema_confirmed,         # EMA 确认
    macd_confirmed         # MACD 确认
])

entry_signal = confirmations >= 4
```

### 2.2 出场触发条件

#### 2.2.1 止损触发
| 止损类型 | 触发条件 | 说明 |
|---------|---------|------|
| `STOP_LOSS_FIXED` | `price <= entry * (1 - stop_pct)` | 固定百分比止损 |
| `STOP_LOSS_ATR` | `price <= entry - atr * 1.5` | ATR 动态止损 |
| `STOP_LOSS_SUPPORT` | `price < support_level` | 支撑位跌破止损 |
| `STOP_LOSS_TIME` | `holding_days > max_days` | 时间止损 |

#### 2.2.2 止盈触发
| 止盈类型 | 触发条件 | 说明 |
|---------|---------|------|
| `TAKE_PROFIT_FIXED` | `price >= entry * (1 + take_profit_pct)` | 固定止盈 |
| `TAKE_PROFIT_RRR` | `pnl >= risk * target_rrr` | 目标盈亏比止盈 |
| `TAKE_PROFIT_TRAILING` | `price < highest * (1 - trail_pct)` | 移动止盈 |
| `TAKE_PROFIT_PARTIAL` | `pnl >= risk * 2` (减仓 30%) | 分阶段止盈 |

#### 2.2.3 信号反转出
```python
# 多转空
reverse_exit_long = position_direction == 'LONG' and new_signal == 'SHORT'

# 空转多
reverse_exit_short = position_direction == 'SHORT' and new_signal == 'LONG'
```

---

## 三、止盈止损配置 (Stop Loss / Take Profit)

### 3.1 止损配置参数

| 参数名 | 变量名 | 典型值 | 说明 |
|-------|-------|--------|------|
| 固定止损比例 | `STOP_LOSS` | 5% (0.05) | 默认止损幅度 |
| ATR 止损倍数 | `ATR_MULTIPLIER` | 1.5 - 2.5 | ATR × 倍数 = 止损距离 |
| 最大止损 | `MAX_STOP_LOSS` | 12% | 单笔最大可接受亏损 |
| 最小止损 | `MIN_STOP_LOSS` | 3% | 避免过窄止损 |

**计算公式：**
```python
# 固定止损
stop_loss_price = entry_price * (1 - STOP_LOSS)  # 多头
stop_loss_price = entry_price * (1 + STOP_LOSS)  # 空头

# ATR 动态止损
stop_loss_price = entry_price - (ATR * ATR_MULTIPLIER)  # 多头
stop_loss_price = entry_price + (ATR * ATR_MULTIPLIER)  # 空头

# 基于风险平价
risk_amount = capital * RISK_PER_TRADE
stop_distance = entry_price - stop_loss_price
position_size = risk_amount / stop_distance
```

### 3.2 止盈配置参数

| 参数名 | 变量名 | 典型值 | 说明 |
|-------|-------|--------|------|
| 固定止盈比例 | `TAKE_PROFIT` | 15% (0.15) | 默认止盈幅度 |
| 目标盈亏比 | `TARGET_RRR` | 2.0 - 3.5 | 止盈/止损比例 |
| 移动止盈回撤 | `TRAIL_PCT` | 5% - 10% | 从最高点回撤比例 |
| 移动止盈启动 | `TRAIL_ACTIVATION` | 2.0 × 风险 | 盈利达 2 倍风险后启动 |

**计算公式：**
```python
# 固定止盈 (基于盈亏比)
take_profit_price = entry_price + (entry_price - stop_loss_price) * TARGET_RRR

# 移动止盈
if highest_since_entry > entry * (1 + risk * TRAIL_ACTIVATION):
    trailing_stop = highest_since_entry * (1 - TRAIL_PCT)
```

### 3.3 分阶段止盈配置

```yaml
partial_exit:
  enable: true
  stages:
    - at_rrr: 2.0           # 盈利达 2 倍风险
      exit_pct: 0.30        # 止盈 30% 仓位
    - at_rrr: 4.0           # 盈利达 4 倍风险
      exit_pct: 0.30        # 再止盈 30% 仓位
    - at_rrr: 6.0           # 剩余仓位博取更大收益
      exit_pct: 1.0         # 全部止盈
```

---

## 四、仓位管理 (Position Sizing)

### 4.1 基础仓位配置

| 参数名 | 变量名 | 典型值 | 说明 |
|-------|-------|--------|------|
| 初始资金 | `INITIAL_CAPITAL` | 10,000 USDT | 起始资金 |
| 单笔仓位 | `POSITION_SIZE` | 10% - 60% | 单笔投入比例 |
| 单笔风险 | `RISK_PER_TRADE` | 2% | 每笔最大风险 |
| 最大持仓数 | `MAX_POSITIONS` | 3 - 5 | 同时持仓上限 |
| 总敞口 | `MAX_EXPOSURE` | 100% - 120% | 总仓位上限 |

### 4.2 凯利公式仓位

```python
# 凯利公式
kelly_fraction = (win_rate * profit_ratio - (1 - win_rate)) / profit_ratio

# 半凯利 (降低风险)
position_size = kelly_fraction / 2

# 应用置信度调整
position_size = position_size * confidence_score
```

| 参数 | 典型值 | 说明 |
|-----|--------|------|
| 凯利除数 | `KELLY_DIVISOR` | 2.0 | 半凯利用 |
| 最大凯利仓位 | `KELLY_MAX` | 25% | 凯利公式上限 |
| 置信度 | `CONFIDENCE` | 0.5 - 1.0 | 信号置信度 |

### 4.3 动态仓位调整

```python
# 基础仓位
base_size = 0.30  # 30%

# 根据信号强度调整
if signal_score >= 85:
    size = base_size * 1.2  # 高置信度 +20%
elif signal_score >= 75:
    size = base_size        # 标准
else:
    size = base_size * 0.7  # 低置信度 -30%

# 根据趋势强度调整
if trend_strength > 0.8:
    size *= 1.5  # 强趋势 +50%

# 根据波动率调整 (风险平价)
atr_pct = atr / entry_price
size_by_risk = RISK_PER_TRADE / atr_pct
final_size = min(size, size_by_risk)
```

| 调整因子 | 变量名 | 典型值 | 说明 |
|---------|-------|--------|------|
| 趋势乘数 | `TREND_MULTIPLIER` | 1.5 | 强趋势加成 |
| 成交量乘数 | `VOLUME_MULTIPLIER` | 1.33 | 放量加成 |
| 置信度乘数 | `CONVICTION_MULTIPLIER` | 1.2 | 高分加成 |
| 波动率调整 | `VOL_ADJUSTMENT` | 0.3 | 高波动减仓 30% |

### 4.4 连续亏损减仓

| 连续亏损次数 | 仓位调整 |
|------------|---------|
| 0 | 100% 正常仓位 |
| 1 | 100% 正常仓位 |
| 2 | 50% 减半仓位 |
| 3+ | 暂停交易 24 小时 |

---

## 五、市场状态识别 (Market Regime Detection)

### 5.1 市场状态分类

| 状态 | 标识 | 判断条件 |
|-----|------|---------|
| 牛市 | `BULL` | 价格>200 日均线，50 日涨幅>30%，EMA20>EMA50 |
| 熊市 | `BEAR` | 价格<200 日均线，50 日跌幅>20%，EMA20<EMA50 |
| 震荡 | `SIDEWAYS` | 200 日均线附近，涨跌幅<10%，波动率降低 |
| 崩盘 | `CRASH` | 7 日内跌幅>40% |
| 复苏 | `RECOVERY` | 崩盘后企稳，RSI 从超卖反弹 |

### 5.2 币种分类

| 等级 | 标识 | 判断条件 | 示例 |
|-----|------|---------|------|
| 主流币 | `MAJOR` | BTC, ETH | BTCUSDT, ETHUSDT |
| 中市值 | `MID` | 大成交量 + 低波动 | SOL, BNB, XRP |
| 山寨币 | `ALTCOIN` | 其他 | ADA, DOT, LINK |
| 模因币 | `MEME` | 极高波动 + 社交媒体热度 | DOGE, SHIB, PEPE |

---

## 六、风控指标 (Risk Metrics)

### 6.1 回撤控制

| 回撤级别 | 阈值 | 应对措施 |
|---------|------|---------|
| 一级预警 | 15% | 减仓 50% |
| 二级预警 | 25% | 减仓 75% |
| 三级止损 | 40% - 50% | 停止交易 |

### 6.2 单日风控

| 参数 | 阈值 | 措施 |
|-----|------|------|
| 单日最大亏损 | 5% | 停止当日交易 |
| 单日最大交易数 | 5 笔 | 限制过度交易 |

### 6.3 绩效指标

| 指标 | 公式 | 目标值 |
|-----|------|--------|
| 胜率 | `wins / total_trades` | >45% |
| 盈亏比 | `avg_win / avg_loss` | >2.5 |
| 夏普比率 | `mean(returns) / std(returns) * sqrt(252)` | >1.5 |
| 最大回撤 | `max(drawdown)` | <30% |
| 年化收益 | `(final/initial)^(365/days) - 1` | >50% |

---

## 七、策略模板参数汇总

### 7.1 完整参数字典

```python
STRATEGY_PARAMS = {
    # 入场参数
    'entry': {
        'min_score': 75,              # 最低入场分数
        'required_confirmations': 4,  # 最少确认数
        'rsi_long_min': 50,           # 做多 RSI 下限
        'rsi_long_max': 75,           # 做多 RSI 上限
        'rsi_short_min': 25,          # 做空 RSI 下限
        'rsi_short_max': 50,          # 做空 RSI 上限
        'volume_ratio_min': 1.5,      # 最小成交量比率
    },
    
    # 出场参数
    'exit': {
        'stop_loss_pct': 0.05,        # 止损 5%
        'take_profit_pct': 0.15,      # 止盈 15%
        'target_rrr': 3.0,            # 目标盈亏比 3:1
        'trailing_activation': 2.0,   # 移动止盈启动倍数
        'trailing_pct': 0.05,         # 移动止盈回撤 5%
        'max_holding_days': 10,       # 最大持仓天数
    },
    
    # 仓位参数
    'position': {
        'base_size': 0.30,            # 基础仓位 30%
        'max_size': 0.60,             # 最大仓位 60%
        'risk_per_trade': 0.02,       # 单笔风险 2%
        'kelly_divisor': 2.0,         # 凯利除数
    },
    
    # 风控参数
    'risk': {
        'daily_max_loss': 0.05,       # 单日最大亏损 5%
        'consecutive_losses': 3,      # 连续亏损暂停
        'max_drawdown': 0.50,         # 最大回撤 50%
    },
    
    # 指标参数
    'indicators': {
        'ema_fast': 20,
        'ema_slow': 50,
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'atr_period': 14,
        'bb_period': 20,
        'bb_std': 2,
    }
}
```

---

## 八、可量化要素清单 (Checklist)

### 8.1 必须量化的要素

- [ ] **入场信号**: 明确的技术指标组合 + 阈值
- [ ] **出场信号**: 止损/止盈/反转的精确触发条件
- [ ] **仓位大小**: 基于风险或凯利公式的计算
- [ ] **市场状态**: 牛/熊/震荡的量化判断
- [ ] **风控规则**: 回撤/亏损/连续止损的限制

### 8.2 可选优化的要素

- [ ] **动态参数**: 根据波动率/趋势强度调整
- [ ] **分阶段止盈**: 多批次出场策略
- [ ] **移动止损**: 跟踪止损保护利润
- [ ] **时间止损**: 避免资金占用过久
- [ ] **相关性限制**: 避免过度集中

---

> 🦞 **龙虾王提示**: 所有参数应根据回测结果优化，并在实盘中持续监控调整。量化不是万能，但能量化的一定要量化！
