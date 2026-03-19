# 🦞 市场趋势预判系统 - 快速参考卡

## 一行命令检测

```bash
# 检测所有核心币种
cd ~/.openclaw/workspace/quant && python3 market_trend_detector.py
```

## Python 快速使用

```python
from market_trend_detector import detect_market_trend, detect_all_trends

# 单个币种
signal = detect_market_trend('BTCUSDT')
print(f"{signal.market_state.value} | 评分:{signal.trend_score} | 置信度:{signal.confidence:.1%}")

# 批量检测
signals = detect_all_trends(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
```

## 信号解读

| 指标 | 牛市信号 | 熊市信号 | 震荡信号 |
|------|----------|----------|----------|
| **MA200** | above (+5%) | below (-5%) | neutral (±5%) |
| **高低点** | HH_HL | LH_LL | mixed |
| **ADX** | > 25 (强) | > 25 (强) | < 20 (弱) |
| **评分** | > 55 | < 45 | 40-60 |
| **置信度** | > 0.75 (高) | > 0.75 (高) | 0.5-0.75 (中) |

## 决策矩阵

```
市场状态 + 置信度 → 决策
━━━━━━━━━━━━━━━━━━━━━━━━━━
牛市 + 高 (>0.75)   → 做多 (100% 仓位)
牛市 + 中 (0.5-0.75) → 做多 (70% 仓位)
熊市 + 高 (>0.75)   → 做空 (100% 仓位)
熊市 + 中 (0.5-0.75) → 做空 (50% 仓位)
震荡              → 观望或区间交易
```

## 常用代码片段

### 筛选高置信度信号
```python
high_conf = {s.symbol: s for s in signals.values() if s.confidence > 0.7}
```

### 按市场状态分组
```python
from market_trend_detector import MarketState

bulls = [s for s in signals.values() if s.market_state == MarketState.BULL]
bears = [s for s in signals.values() if s.market_state == MarketState.BEAR]
```

### 保存信号
```python
detector = MarketTrendDetector()
detector.save_signals(signals, 'backtest/today_signals.json')
```

### 生成报告
```python
report = detector.generate_report(signals)
print(report)
```

## 文件位置

```
quant/
├── market_trend_detector.py      # 主模块
├── MARKET_TREND_GUIDE.md         # 详细指南
├── TREND_SYSTEM_SUMMARY.md       # 实现总结
├── examples/
│   └── market_trend_examples.py  # 使用示例
└── backtest/
    └── trend_signals_*.json      # 信号输出
```

## 调整阈值

```python
detector = MarketTrendDetector()
detector.TREND_SCORE_BULL = 60      # 提高牛市门槛
detector.ADX_STRONG_THRESHOLD = 30  # 提高强趋势门槛
```

## 与其他模块集成

```python
# 在策略中
from market_trend_detector import detect_market_trend

signal = detect_market_trend('BTCUSDT')
if signal.market_state == MarketState.BULL:
    enter_long()
elif signal.market_state == MarketState.BEAR:
    enter_short()
else:
    standby()
```

---

🦞 **Keep it simple, keep it profitable!**
