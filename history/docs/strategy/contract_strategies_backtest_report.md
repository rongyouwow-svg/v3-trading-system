# 🦞 龙虾王合约策略大规模回测报告

> 回测周期：180 天  
> 生成时间：2026-03-04 10:53:21  
> 风控标准：最大回撤 ≤ 10%

---

## 📊 总览

| 指标 | 数值 |
|------|------|
| 总回测次数 | 72 |
| 通过风控 | 14 |
| 未通过风控 | 58 |
| 通过率 | 19.4% |

---

## 🏆 Top 10 策略 (通过风控)

| 排名 | 币种 | 策略 | 方向 | 收益 | 胜率 | 回撤 | 交易次数 |
|------|------|------|------|------|------|------|----------|
| 1 | BTCUSDT | supertrend | SHORT | 4.3% | 50% | 8.8% | 2 |
| 2 | BNBUSDT | breakout | LONG | 0.4% | 75% | 5.6% | 4 |
| 3 | SOLUSDT | volatility_breakout | LONG | 0.3% | 67% | 9.3% | 3 |
| 4 | BTCUSDT | supertrend | LONG | 0.0% | 0% | 0.0% | 0 |
| 5 | BTCUSDT | ema_pullback | LONG | 0.0% | 0% | 0.0% | 0 |
| 6 | ETHUSDT | supertrend | LONG | 0.0% | 0% | 0.0% | 0 |
| 7 | ETHUSDT | supertrend | SHORT | 0.0% | 0% | 0.0% | 0 |
| 8 | ETHUSDT | ema_pullback | LONG | 0.0% | 0% | 0.0% | 0 |
| 9 | SOLUSDT | supertrend | LONG | 0.0% | 0% | 0.0% | 0 |
| 10 | SOLUSDT | supertrend | SHORT | 0.0% | 0% | 0.0% | 0 |

---

## 📈 各币种最佳策略

### BTCUSDT

- **最佳策略**: supertrend (SHORT)
- **收益率**: 4.3%
- **胜率**: 50%
- **最大回撤**: 8.8%
- **交易次数**: 2
- **盈亏比**: 1.90

### ETHUSDT

- **最佳策略**: supertrend (LONG)
- **收益率**: 0.0%
- **胜率**: 0%
- **最大回撤**: 0.0%
- **交易次数**: 0
- **盈亏比**: 0.00

### SOLUSDT

- **最佳策略**: volatility_breakout (LONG)
- **收益率**: 0.3%
- **胜率**: 67%
- **最大回撤**: 9.3%
- **交易次数**: 3
- **盈亏比**: 1.08

### BNBUSDT

- **最佳策略**: breakout (LONG)
- **收益率**: 0.4%
- **胜率**: 75%
- **最大回撤**: 5.6%
- **交易次数**: 4
- **盈亏比**: 1.34


---

## 📋 完整策略列表 (通过风控)

| 币种 | 策略 | 方向 | 收益 | 胜率 | 回撤 | 夏普 | 交易数 |
|------|------|------|------|------|------|------|--------|
| BTCUSDT | supertrend | SHORT | 4.3% | 50% | 8.8% | 0.15 | 2 |
| BNBUSDT | breakout | LONG | 0.4% | 75% | 5.6% | 0.07 | 4 |
| SOLUSDT | volatility_breakout | LONG | 0.3% | 67% | 9.3% | 0.13 | 3 |
| BTCUSDT | supertrend | LONG | 0.0% | 0% | 0.0% | 0.00 | 0 |
| BTCUSDT | ema_pullback | LONG | 0.0% | 0% | 0.0% | 0.00 | 0 |
| ETHUSDT | supertrend | LONG | 0.0% | 0% | 0.0% | 0.00 | 0 |
| ETHUSDT | supertrend | SHORT | 0.0% | 0% | 0.0% | 0.00 | 0 |
| ETHUSDT | ema_pullback | LONG | 0.0% | 0% | 0.0% | 0.00 | 0 |
| SOLUSDT | supertrend | LONG | 0.0% | 0% | 0.0% | 0.00 | 0 |
| SOLUSDT | supertrend | SHORT | 0.0% | 0% | 0.0% | 0.00 | 0 |
| BNBUSDT | supertrend | LONG | 0.0% | 0% | 0.0% | 0.00 | 0 |
| BNBUSDT | supertrend | SHORT | 0.0% | 0% | 0.0% | 0.00 | 0 |
| BNBUSDT | ema_pullback | LONG | 0.0% | 0% | 0.0% | 0.00 | 0 |
| BNBUSDT | volatility_breakout | LONG | 0.0% | 0% | 0.0% | 0.00 | 0 |

---

## ❌ 未通过风控的策略

| 币种 | 策略 | 方向 | 收益 | 最大回撤 | 状态 |
|------|------|------|------|----------|------|
| ETHUSDT | volatility_breakout | SHORT | 101.5% | 54.5% | 淘汰 |
| ETHUSDT | volume_confirmation | SHORT | 105.1% | 52.1% | 淘汰 |
| ETHUSDT | breakout | SHORT | 65.5% | 46.9% | 淘汰 |
| ETHUSDT | rsi_reversal | SHORT | 49.4% | 42.0% | 淘汰 |
| BTCUSDT | volatility_breakout | SHORT | 43.1% | 41.8% | 淘汰 |
| SOLUSDT | breakout | SHORT | 59.5% | 41.4% | 淘汰 |
| SOLUSDT | momentum | SHORT | 55.5% | 41.2% | 淘汰 |
| BTCUSDT | trend_following | LONG | -33.4% | 39.1% | 淘汰 |
| SOLUSDT | mean_reversion | LONG | -25.1% | 37.1% | 淘汰 |
| BTCUSDT | momentum | LONG | -26.7% | 37.0% | 淘汰 |
| ETHUSDT | mean_reversion | LONG | -26.7% | 36.9% | 淘汰 |
| ETHUSDT | momentum | SHORT | 41.0% | 36.6% | 淘汰 |
| BTCUSDT | volume_confirmation | SHORT | 34.9% | 36.3% | 淘汰 |
| ETHUSDT | mean_reversion | SHORT | 33.0% | 35.8% | 淘汰 |
| BTCUSDT | breakout | SHORT | 40.3% | 35.6% | 淘汰 |
| ETHUSDT | momentum | LONG | -21.1% | 34.3% | 淘汰 |
| ETHUSDT | rsi_reversal | LONG | -16.4% | 34.3% | 淘汰 |
| BTCUSDT | mean_reversion | SHORT | 35.1% | 33.4% | 淘汰 |
| SOLUSDT | trend_following | SHORT | 21.6% | 33.3% | 淘汰 |
| ETHUSDT | trend_following | SHORT | 29.3% | 33.2% | 淘汰 |

*... 还有 38 个策略未通过风控*

---

## 🎯 推荐策略组合

基于回测结果，推荐以下策略组合 (均通过 10% 回撤风控):

### BTCUSDT

- **supertrend** (SHORT): 收益 4.3%, 回撤 8.8%, 胜率 50%
- **supertrend** (LONG): 收益 0.0%, 回撤 0.0%, 胜率 0%

### ETHUSDT

- **supertrend** (LONG): 收益 0.0%, 回撤 0.0%, 胜率 0%
- **supertrend** (SHORT): 收益 0.0%, 回撤 0.0%, 胜率 0%

### SOLUSDT

- **volatility_breakout** (LONG): 收益 0.3%, 回撤 9.3%, 胜率 67%
- **supertrend** (LONG): 收益 0.0%, 回撤 0.0%, 胜率 0%

### BNBUSDT

- **breakout** (LONG): 收益 0.4%, 回撤 5.6%, 胜率 75%
- **supertrend** (LONG): 收益 0.0%, 回撤 0.0%, 胜率 0%


---

## 📝 说明

1. **风控标准**: 最大回撤超过 10% 的策略直接淘汰
2. **止损止盈**: 统一止损 5%, 止盈 10%
3. **仓位管理**: 单笔 95% 仓位 (激进)
4. **回测周期**: 180 天 1 小时 K 线

---

*报告生成时间：2026-03-04 10:53:21*
