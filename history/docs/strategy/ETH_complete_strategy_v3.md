# 🦞 ETH 100% 年化 - 完整策略框架 v3.0

**生成时间：** 2026-03-05 23:20  
**核心原则：** 保护本金第一，机会分级，动态调整  
**目标：** 100% 年化收益，最大回撤<30%

---

## 🎯 策略核心哲学

### 第一原则：保护本金

```
1. 永不爆仓是底线
2. 单笔最大亏损<5%
3. 总回撤>20% 强制降仓
4. 总回撤>30% 停止交易
```

### 机会分级

| 机会等级 | 仓位 | 杠杆 | 模式 | 条件 |
|----------|------|------|------|------|
| **普通机会** | 10-20% | 1-2 倍 | 全仓 | 1-2 个信号确认 |
| **良好机会** | 20-30% | 2-3 倍 | 全仓 | 3 个信号确认 |
| **优质机会** | 30-40% | 3-4 倍 | 全仓 | 4 个信号确认 + 趋势共振 |
| **绝佳机会** | 20-30% | 5-10 倍 | 逐仓 | 多周期共振 + 大户极端 + 关键位突破 |

### 核心思想

```
- 普通行情：小仓位 + 小杠杆，积累收益
- 绝佳机会：逐仓高杠杆，博弈大收益
- 绝不用全仓高杠杆赌方向
- 绝不在趋势不明时重仓
```

---

## 📊 牛熊趋势判断系统

### 大周期趋势（日线 + 周线）

| 指标 | 牛市信号 | 熊市信号 | 震荡信号 |
|------|----------|----------|----------|
| **EMA 排列** | EMA20>50>200 | EMA20<50<200 | 均线纠缠 |
| **MACD** | DIF>DEA>0 | DIF<DEA<0 | DIF 围绕 0 轴波动 |
| **价格位置** | >200 日均线 | <200 日均线 | 围绕 200 日均线 |
| **高低点** | 高点创新高，低点抬高 | 低点创新低，高点降低 | 高低点无序 |

### 趋势强度评分

```python
trend_score = 0

# EMA 排列（0-30 分）
if EMA20 > EMA50 > EMA200:
    trend_score += 30  # 强多
elif EMA20 > EMA50:
    trend_score += 20  # 弱多
elif EMA20 < EMA50 < EMA200:
    trend_score -= 30  # 强空
elif EMA20 < EMA50:
    trend_score -= 20  # 弱空

# MACD（0-20 分）
if MACD > 0 and MACD_hist > 0:
    trend_score += 20  # 多头动能
elif MACD < 0 and MACD_hist < 0:
    trend_score -= 20  # 空头动能

# 价格位置（0-20 分）
if price > EMA200:
    trend_score += 20
else:
    trend_score -= 20

# 高低点结构（0-30 分）
if higher_highs and higher_lows:
    trend_score += 30  # 上升趋势
elif lower_highs and lower_lows:
    trend_score -= 30  # 下降趋势

# 趋势判断
if trend_score >= 50:
    market_regime = "牛市"
    max_leverage = 4
    position_size = 0.4
elif trend_score <= -50:
    market_regime = "熊市"
    max_leverage = 4
    position_size = 0.4
else:
    market_regime = "震荡"
    max_leverage = 2
    position_size = 0.2
```

### 牛熊转换识别

```python
# 牛市转熊市信号
if (previous_trend_score >= 50 and current_trend_score < 30):
    # 趋势走弱
    action = "减仓至 20%"
    leverage = 1
    
# 熊市转牛市信号
if (previous_trend_score <= -50 and current_trend_score > -30):
    # 趋势走强
    action = "逐步建仓"
    leverage = 2
```

---

## 📐 支撑压力判断系统

### 多周期支撑压力

| 周期 | 支撑/压力类型 | 强度 | 用途 |
|------|--------------|------|------|
| **周线** | 前高/前低，整数关口 | ⭐⭐⭐⭐⭐ | 大方向判断 |
| **日线** | 前高/前低，成交密集区 | ⭐⭐⭐⭐ | 主要支撑压力 |
| **4H** | 近期高低点，斐波那契 | ⭐⭐⭐ | 入场参考 |
| **1H** | 短期高低点，VWAP | ⭐⭐ | 精确入场 |
| **15M** | 微观结构，订单簿 | ⭐ | 时机选择 |

### 支撑压力强度评分

```python
support_strength = 0

# 测试次数（0-30 分）
if tested_times >= 4:
    support_strength += 30  # 强支撑
elif tested_times >= 3:
    support_strength += 20
elif tested_times >= 2:
    support_strength += 10

# 成交量（0-20 分）
if volume_at_level > avg_volume * 2:
    support_strength += 20  # 高成交量支撑
elif volume_at_level > avg_volume:
    support_strength += 10

# 时间跨度（0-20 分）
if days_since_first_test > 30:
    support_strength += 20  # 长期支撑
elif days_since_first_test > 7:
    support_strength += 10

# 整数关口（0-15 分）
if price_level is_round_number:
    support_strength += 15  # 心理关口

# 斐波那契位（0-15 分）
if price_level in [0.618, 0.5, 0.382]:
    support_strength += 15  # 黄金分割位

# 支撑强度判断
if support_strength >= 70:
    level_type = "强支撑"
    bounce_probability = 0.7
elif support_strength >= 50:
    level_type = "中等支撑"
    bounce_probability = 0.55
else:
    level_type = "弱支撑"
    bounce_probability = 0.4
```

### 关键位置交易策略

```python
# 强支撑位做多
if price near strong_support and trend_score > 0:
    entry = support_level * 1.005  # 支撑上方 0.5%
    stop_loss = support_level * 0.97  # 支撑下方 3%
    take_profit = resistance_level
    leverage = 3
    position = 0.3

# 强压力位做空
if price near strong_resistance and trend_score < 0:
    entry = resistance_level * 0.995  # 压力下方 0.5%
    stop_loss = resistance_level * 1.03  # 压力上方 3%
    take_profit = support_level
    leverage = 3
    position = 0.3

# 突破交易
if price breaks strong_resistance with volume > 2x:
    entry = breakout_level * 1.01  # 突破后 1%
    stop_loss = breakout_level * 0.97  # 突破位下方 3%
    take_profit = next_resistance
    leverage = 4
    position = 0.4
```

---

## 🎲 机会分级系统

### 信号强度评分

```python
signal_score = 0

# 趋势方向（0-30 分）
if trend_score >= 50 and signal_direction == "long":
    signal_score += 30
elif trend_score <= -50 and signal_direction == "short":
    signal_score += 30

# 支撑压力（0-25 分）
if price at strong_support and signal_direction == "long":
    signal_score += 25
elif price at strong_resistance and signal_direction == "short":
    signal_score += 25

# 多周期共振（0-25 分）
if all_timeframes_aligned:
    signal_score += 25
elif majority_timeframes_aligned:
    signal_score += 15

# 成交量确认（0-20 分）
if volume > avg_volume * 2:
    signal_score += 20
elif volume > avg_volume:
    signal_score += 10

# 大户持仓（0-10 分，反向）
if大户极端多头 and signal_direction == "short":
    signal_score += 10
elif 大户极端空头 and signal_direction == "long":
    signal_score += 10

# 机会等级判断
if signal_score >= 80:
    opportunity = "绝佳机会"
    leverage = 5-10  # 逐仓
    position = 0.2-0.3
elif signal_score >= 60:
    opportunity = "优质机会"
    leverage = 3-4
    position = 0.3-0.4
elif signal_score >= 40:
    opportunity = "良好机会"
    leverage = 2-3
    position = 0.2-0.3
else:
    opportunity = "普通机会"
    leverage = 1-2
    position = 0.1-0.2
```

### 机会等级与仓位配置

| 信号分 | 等级 | 仓位 | 杠杆 | 模式 | 止损 | 示例场景 |
|--------|------|------|------|------|------|----------|
| **80-100** | 绝佳 | 20-30% | 5-10x | 逐仓 | 5% | 多周期共振 + 关键位突破 + 大户极端 |
| **60-79** | 优质 | 30-40% | 3-4x | 全仓 | 6% | 趋势 + 支撑 + 成交量共振 |
| **40-59** | 良好 | 20-30% | 2-3x | 全仓 | 8% | 趋势 + 突破确认 |
| **20-39** | 普通 | 10-20% | 1-2x | 全仓 | 10% | 单一信号，试探性建仓 |
| **<20** | 观望 | 0% | - | - | - | 信号不明，等待 |

---

## 🛡️ 风险管理系统

### 仓位管理

```python
# 基础仓位计算
base_position = account_balance * 0.3  # 基础 30% 仓位

# 根据机会等级调整
if opportunity == "绝佳":
    position = base_position * 1.0  # 30%
elif opportunity == "优质":
    position = base_position * 1.33  # 40%
elif opportunity == "良好":
    position = base_position * 0.83  # 25%
else:
    position = base_position * 0.5  # 15%

# 根据趋势强度调整
if abs(trend_score) >= 70:
    position *= 1.2  # 趋势强，加仓
elif abs(trend_score) <= 30:
    position *= 0.7  # 趋势弱，减仓

# 根据回撤调整
if total_drawdown > 0.15:
    position *= 0.7  # 回撤>15%，减仓
if total_drawdown > 0.25:
    position *= 0.5  # 回撤>25%，大幅减仓
```

### 止损策略

```python
# 固定百分比止损
stop_loss_fixed = entry_price * (1 - 0.06)  # 6% 止损

# 支撑压力止损
if long_position:
    stop_loss_support = nearest_support * 0.97  # 支撑下方 3%
    stop_loss = min(stop_loss_fixed, stop_loss_support)
else:
    stop_loss_resistance = nearest_resistance * 1.03  # 压力上方 3%
    stop_loss = max(stop_loss_fixed, stop_loss_resistance)

# ATR 止损
atr = ATR(14)
stop_loss_atr = entry_price - 2.5 * atr  # 2.5 倍 ATR
stop_loss = min(stop_loss, stop_loss_atr)

# 时间止损
if holding_days > 5 and profit < 0:
    exit_market()  # 5 天不盈利就出场
```

### 止盈策略

```python
# 分批止盈
if profit >= 0.20:  # 盈利 20%
    close(40%)  # 平仓 40%
    stop_loss = entry_price  # 剩余保本

if profit >= 0.50:  # 盈利 50%
    close(30%)  # 再平仓 30%
    stop_loss = trailing_stop(10%)  # 追踪止盈 10%

if profit >= 1.00:  # 盈利 100%
    close(20%)  # 再平仓 20%
    # 剩余 10% 让利润奔跑
```

### 硬性风控规则

```yaml
单笔风险：
- 最大亏损：<5% 总资金
- 止损距离：根据入场点计算
- 仓位调整：确保亏损不超过 5%

每日风险：
- 最大亏损：5% 总资金
- 触发后：停止当日交易

每周风险：
- 最大亏损：10% 总资金
- 触发后：降至 1 倍杠杆

每月风险：
- 最大亏损：15% 总资金
- 触发后：停止交易，复盘

总风险：
- 最大回撤：30% 总资金
- 触发后：清仓，休息 1 个月
```

---

## 📈 完整交易流程

### 1. 趋势判断（日线）

```python
# 计算趋势分数
trend_score = calculate_trend_score()

# 判断市场状态
if trend_score >= 50:
    market = "牛市"
    bias = "做多为主"
    max_leverage = 4
elif trend_score <= -50:
    market = "熊市"
    bias = "做空为主"
    max_leverage = 4
else:
    market = "震荡"
    bias = "高抛低吸"
    max_leverage = 2
```

### 2. 支撑压力识别（4H + 1H）

```python
# 识别关键位置
supports = identify_support_levels()
resistances = identify_resistance_levels()

# 评分
for level in supports:
    level.strength = calculate_level_strength(level)

# 排序
strongest_support = max(supports, key=lambda x: x.strength)
strongest_resistance = max(resistances, key=lambda x: x.strength)
```

### 3. 信号生成（1H + 15M）

```python
# 生成交易信号
signals = []

# 突破信号
if price breaks resistance with volume:
    signals.append("突破做多")

# 支撑反弹信号
if price bounces from strong_support:
    signals.append("支撑做多")

# 压力回调信号
if price rejects from strong_resistance:
    signals.append("压力做空")
```

### 4. 机会评估

```python
# 计算信号分数
signal_score = 0
signal_score += trend_alignment * 30
signal_score += level_strength * 25
signal_score += timeframe_confluence * 25
signal_score += volume_confirmation * 20

# 确定机会等级
if signal_score >= 80:
    opportunity = "绝佳"
    leverage = 5-10  # 逐仓
elif signal_score >= 60:
    opportunity = "优质"
    leverage = 3-4
# ...
```

### 5. 仓位计算

```python
# 根据风险计算仓位
risk_per_trade = account_balance * 0.05  # 单笔风险 5%
stop_distance = abs(entry - stop_loss) / entry
position_size = risk_per_trade / stop_distance

# 确保不超过最大仓位
position_size = min(position_size, max_position)
```

### 6. 执行交易

```python
# 下单
if opportunity == "绝佳":
    order_type = "isolated_margin"
    leverage = 5-10
else:
    order_type = "cross_margin"
    leverage = calculated_leverage

# 设置止损止盈
place_stop_loss(stop_loss)
place_take_profit(take_profit_1, 40%)
place_take_profit(take_profit_2, 30%)
```

### 7. 持仓管理

```python
# 监控持仓
while position_open:
    # 移动止损
    if profit > 0.20:
        move_stop_loss_to_breakeven()
    
    # 部分止盈
    if profit > 0.50:
        close_partial(30%)
    
    # 时间止损
    if holding_days > 5 and profit < 0:
        close_all()
```

---

## 🎯 实盘执行计划

### 阶段 1：测试期（3.6-3.19）

```yaml
资金：1000 USDT
目标：验证策略，不追求收益
杠杆：1-2 倍
仓位：10-20%
重点：
- 记录每笔交易
- 验证信号准确性
- 调整参数
成功标准：胜率>50%，回撤<10%
```

### 阶段 2：验证期（3.20-4.19）

```yaml
资金：3000 USDT
目标：稳定盈利
杠杆：2-3 倍
仓位：20-30%
重点：
- 严格执行风控
- 机会分级执行
- 积累交易数据
成功标准：月收益>15%，回撤<15%
```

### 阶段 3：稳定期（4.20-6.30）

```yaml
资金：10000 USDT
目标：100% 年化
杠杆：3-4 倍（普通），5-10 倍（绝佳机会逐仓）
仓位：30-40%
重点：
- 抓住绝佳机会
- 严格控制回撤
- 定期提取利润
成功标准：月收益>20%，回撤<25%
```

---

## 📊 预期收益路径

| 阶段 | 时间 | 资金 | 月收益 | 杠杆 | 回撤控制 |
|------|------|------|--------|------|----------|
| 测试期 | 3.6-3.19 | 1000U→1200U | +10-20% | 1-2x | <10% |
| 验证期 | 3.20-4.19 | 1200U→2000U | +30-50% | 2-3x | <15% |
| 稳定期 | 4.20-6.30 | 2000U→5000U | +50-80% | 3-4x | <20% |
| 爆发期 | 7.1-12.31 | 5000U→10000U+ | +30-50% | 3-4x+ | <25% |

**保守目标：** 100% 年化（10000U→20000U）  
**中性目标：** 200% 年化（10000U→30000U）  
**乐观目标：** 500% 年化（10000U→60000U）

---

## ⚠️ 核心风控规则

### 硬性规定

```
1. 单笔亏损不超过总资金 5%
2. 单日亏损不超过总资金 5%
3. 单周亏损不超过总资金 10%
4. 单月亏损不超过总资金 15%
5. 总回撤不超过总资金 30%

触发任何一条，立即执行对应风控措施！
```

### 绝不做的事

```
❌ 永不在趋势不明时重仓
❌ 永不用全仓高杠杆赌方向
❌ 永不在亏损后加仓摊平
❌ 永不移动止损扩大风险
❌ 永不在情绪化时交易
❌ 永不借钱交易
❌ 永不 All-in
```

### 必须做的事

```
✅ 每笔交易前计算风险
✅ 严格执行止损
✅ 定期提取利润
✅ 每周复盘交易
✅ 每月调整策略
✅ 保持良好心态
✅ 记录交易日志
```

---

## 🎯 核心信念

**龙虾王交易哲学 v3.0：**

1. **本金第一** - 活着才能继续交易
2. **机会分级** - 普通机会小仓位，绝佳机会重拳出击
3. **趋势为王** - 顺大势，逆小势
4. **支撑压力** - 关键位置决定盈亏比
5. **动态杠杆** - 根据机会质量调整
6. **逐仓博弈** - 绝佳机会用逐仓高杠杆
7. **严格风控** - 硬性规则不可突破
8. **持续学习** - 市场在变，策略也要变

---

**完整策略， holistic thinking！** 🦞

---

*龙虾王量化实验室*  
*2026-03-05 23:20*
