# 🦞 合约双向策略系统 v2.0

> 基于 4 币种 (BTC/ETH/BNB/SOL) 历史数据的完整双向交易框架

**文件**: `contract_bidirectional_strategies_v2.py`  
**版本**: v2.0  
**日期**: 2026-03-04

---

## 📋 策略总览

### 做多策略 (5 个)

| 编号 | 策略名称 | 策略类型 | 适用场景 | 核心逻辑 |
|------|----------|----------|----------|----------|
| 1 | 趋势突破做多 | `trend_breakout_long` | 牛市初期/中期 | 突破 20 日高点 + 放量 + 多头排列 |
| 2 | 回调买入做多 | `pullback_long` | 上升趋势回调 | 回调至斐波那契支撑 + RSI 40-50 |
| 3 | 区间突破做多 | `range_breakout_long` | 长期盘整后 | 波动率收缩 + 突破区间上沿 |
| 4 | EMA 金叉做多 | `ema_cross_long` | 趋势反转初期 | EMA20 上穿 EMA50 + MACD 同步金叉 |
| 5 | RSI 超卖反弹做多 | `rsi_oversold_long` | 短期超卖 | RSI<30 + 接近支撑 + 看涨 K 线 |

### 做空策略 (5 个)

| 编号 | 策略名称 | 策略类型 | 适用场景 | 核心逻辑 |
|------|----------|----------|----------|----------|
| 6 | 资金费率套利做空 | `funding_arbitrage_short` | 高正费率 | 费率>1% + 年化>36.5% + 对冲风险 |
| 7 | 趋势跟踪做空 | `trend_following_short` | 熊市趋势 | EMA 空头排列 + 反弹至 EMA20 受阻 |
| 8 | 跌破支撑做空 | `breakdown_short` | 跌破关键位 | 跌破 20 日低点 + 放量 + 大阴线 |
| 9 | 反弹阻力做空 | `rebound_short` | 下跌趋势反弹 | 反弹至斐波那契 0.618/0.786 + RSI>60 |
| 10 | 配对交易对冲做空 | `pairs_hedge_short` | 强弱分化 | 做多强势币 + 做空弱势币 (对冲系统性风险) |

---

## 🎯 核心特性

### 1. 双向交易框架
- ✅ 做多策略：捕捉上涨趋势
- ✅ 做空策略：捕捉下跌趋势 + 资金费率套利
- ✅ 对冲策略：配对交易降低系统性风险

### 2. 智能信号评分
每个策略使用 60-100 分评分系统：
- **≥80 分**: 强信号，可使用高仓位 (50-55%)
- **≥60 分**: 有效信号，标准仓位 (30-40%)
- **<60 分**: 不入场

### 3. 动态风控系统
```python
# 仓位管理
if score >= 85:
    position_size = 0.55  # 55% 仓位
    leverage = 3.0
elif score >= 75:
    position_size = 0.40
    leverage = 2.5
else:
    position_size = 0.30
    leverage = 2.0

# 止损止盈
stop_loss = entry - ATR * 2      # 2 倍 ATR 止损
take_profit = entry + risk * 3   # 3:1 盈亏比
```

### 4. 强平风险监控
```python
# 做空强平价格计算
liq_price = entry_price / (1 - 1/leverage + maint_margin_rate)

# 风险等级
- EMERGENCY (<2%): 立即平仓
- CRITICAL (<5%): 减仓 50%
- WARNING (<10%): 密切监控
- SAFE (≥10%): 安全
```

---

## 🚀 使用方法

### 快速启动
```bash
cd ~/.openclaw/workspace/quant
python3 contract_bidirectional_strategies_v2.py
```

### 代码示例
```python
from contract_bidirectional_strategies_v2 import (
    ContractBidirectionalEngine,
    TechnicalIndicators,
    RiskManager
)

# 1. 初始化引擎
engine = ContractBidirectionalEngine(
    symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
)

# 2. 加载数据
df = engine.load_data('BTCUSDT', timeframe='30m')

# 3. 添加技术指标
df = TechnicalIndicators.add_all_indicators(df)

# 4. 扫描信号
funding_rates = {
    'BTCUSDT': 0.0001,
    'ETHUSDT': 0.0002,
    'BNBUSDT': 0.0001,
    'SOLUSDT': 0.0003
}
signals = engine.scan_all_signals(funding_rates=funding_rates)

# 5. 生成报告
report = engine.generate_report(signals)
print(report)

# 6. 扫描配对交易机会
pairs = engine.scan_pairs_opportunities()
for pair in pairs:
    print(f"{pair['pair']}: 相对强度{pair['relative_strength']*100:.1f}%")
```

### 单独使用策略
```python
from contract_bidirectional_strategies_v2 import LongStrategies, ShortStrategies

# 做多策略示例
signal = LongStrategies.trend_breakout_long(df, 'BTCUSDT')
if signal:
    print(f"入场：{signal.entry_price}")
    print(f"止损：{signal.stop_loss}")
    print(f"止盈：{signal.take_profit}")

# 做空策略示例 (资金费率套利)
signal = ShortStrategies.funding_arbitrage_short(
    funding_rate=0.015,  # 1.5%
    symbol='ETHUSDT',
    current_price=2000,
    volatility=60
)
```

---

## 📊 策略评分系统

### 做多策略评分权重

| 指标 | 权重 | 评分标准 |
|------|------|----------|
| 突破确认 | 25 分 | 突破 20 日高点 (+25), 接近突破 (+10) |
| 成交量 | 25 分 | 2 倍均量 (+25), 1.5 倍 (+15), 1 倍 (+5) |
| RSI 位置 | 20 分 | 50-65 (+20), 65-75 (+10), >75 (-10) |
| EMA 排列 | 15 分 | 多头排列 (+15), 混乱 (0), 空头 (-15) |
| MACD | 15 分 | 金叉 (+15), 粘合 (0), 死叉 (-15) |

### 做空策略评分权重

| 指标 | 权重 | 评分标准 |
|------|------|----------|
| 趋势确认 | 30 分 | EMA 空头排列 (+30), 混乱 (0), 多头 (-30) |
| 突破/反弹 | 25 分 | 跌破支撑/反弹阻力 (+25), 接近 (+15) |
| 成交量 | 20 分 | 下跌放量 (+20), 反弹缩量 (+15) |
| RSI 位置 | 15 分 | 50-70 回落 (+15), >70 (+10), <30 (-20) |
| K 线形态 | 10 分 | 明确看跌 (+10), 中性 (0), 看涨 (-10) |

---

## ⚠️ 风控要点

### 仓位管理矩阵

| 市场状态 | 趋势强度 | 波动率 | 最大仓位 | 建议杠杆 |
|----------|----------|--------|----------|----------|
| 牛市 | 强 | 低 | 80% | 3-5x |
| 牛市 | 强 | 高 | 55% | 2-3x |
| 震荡 | - | 低 | 50% | 2-3x |
| 震荡 | - | 高 | 30% | 1-2x |
| 熊市 | 强 | 低 | 50% (空) | 2-3x |
| 熊市 | 强 | 高 | 30% (空) | 1-2x |
| 黑天鹅 | - | 极高 | 10% | 1x |

### 止损策略

1. **固定百分比止损**: 5% 止损 (短线)
2. **ATR 动态止损**: 2-3 倍 ATR (趋势)
3. **技术位止损**: 支撑/阻力位±2-3%
4. **时间止损**: 持仓>10 天无明显进展则离场

### 止盈策略

1. **固定盈亏比**: 3:1 盈亏比
2. **分批止盈**: 
   - 第一目标 1:2 (减仓 50%)
   - 第二目标 1:3 (减仓 30%)
   - 移动止盈 (剩余 20%)
3. **移动止盈**: 盈利达 2 倍风险后启动 5% 回撤止盈

---

## 🔧 配置参数

### 核心配置
```python
# 信号评分阈值
ENTRY_THRESHOLD = 60      # 最低入场评分
STRONG_SIGNAL = 80        # 强信号评分

# 仓位管理
MAX_POSITION_SIZE = 0.55  # 最大仓位 55%
MAX_LEVERAGE = 5.0        # 最大杠杆 5 倍
MAX_RISK_PER_TRADE = 0.02 # 单笔风险 2%

# 止损止盈
DEFAULT_STOP_LOSS = 0.05  # 5% 止损
DEFAULT_TAKE_PROFIT = 0.15 # 15% 止盈
MIN_PROFIT_FACTOR = 2.0   # 最小盈亏比 2:1

# 资金费率套利
FUNDING_THRESHOLD = 0.01  # 1% 费率阈值
MIN_ANNUALIZED = 0.365    # 36.5% 年化最低
```

---

## 📈 回测建议

### 快速回测
```bash
# 单币种回测
cd ~/.openclaw/workspace/quant
python3 -c "
from contract_bidirectional_strategies_v2 import ContractBidirectionalEngine
engine = ContractBidirectionalEngine(symbols=['BTCUSDT'])
# 添加回测逻辑...
"
```

### 大规模回测
```bash
# 所有币种 × 所有策略
python3 strategy_optimizer.py
```

---

## 📝 输出示例

```
🦞 龙虾王合约双向策略信号报告
==================================================
扫描时间：2026-03-04 10:49

📊 BTCUSDT
------------------------------
  做多信号:
    🟢 pullback_long
       评分：90
       入场：68317.35
       止损：65448.90
       止盈：76922.71
       仓位：50% | 杠杆：3.0x
       原因：上升趋势确认，回调至fib_382, 回调至 EMA20, RSI 回调至42

📊 ETHUSDT
------------------------------
  做空信号:
    🔴 rebound_short
       评分：60
       入场：1976.87
       止损：2075.71
       止盈：1729.76
       仓位：45% | 杠杆：3.0x
       原因：下降趋势确认，反弹至fib_618, 反弹至 EMA20

📊 BNBUSDT
------------------------------
  做多信号:
    🟢 trend_breakout_long
       评分：60
       入场：648.58
       止损：638.15
       止盈：679.88
       仓位：30% | 杠杆：2.0x

📊 SOLUSDT
------------------------------
  做多信号:
    🟢 trend_breakout_long
       评分：85
       入场：89.19
       止损：87.13
       止盈：95.38
       仓位：55% | 杠杆：3.0x
```

---

## 🎓 策略设计原则

1. **纪律 > 策略**: 严格执行止损止盈
2. **风控 > 收益**: 生存优先于暴利
3. **概率 > 预测**: 追求正期望值，不追求 100% 胜率
4. **系统化 > 主观**: 量化信号，减少情绪干扰
5. **对冲 > 裸奔**: 使用配对交易降低系统性风险

---

## 🔗 相关文件

- `contract_bidirectional_strategies.md` - 策略文档 v1.0
- `adaptive_strategy_perp.py` - 合约做空策略 v1.0
- `aggressive_strategy.py` - 激进策略 (100% 年化)
- `risk_management.py` - 风险管理系统
- `backtest_engine.py` - 回测引擎

---

> 🦞 龙虾王量化 | 策略系统 v2.0  
> **记住**: 纪律 > 策略，风控 > 收益，生存 > 暴利
