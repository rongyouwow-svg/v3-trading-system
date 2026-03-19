# 🦞 市场趋势预判系统使用指南

## 快速开始

### 1. 单个币种检测

```python
from market_trend_detector import detect_market_trend

# 检测 BTC 趋势
signal = detect_market_trend('BTCUSDT', timeframe='1d')

if signal:
    print(f"市场状态：{signal.market_state.value}")
    print(f"趋势评分：{signal.trend_score}/100")
    print(f"置信度：{signal.confidence:.1%}")
```

### 2. 批量检测

```python
from market_trend_detector import detect_all_trends, MarketTrendDetector

# 检测所有核心币种
signals = detect_all_trends(timeframe='1d')

# 或使用自定义列表
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
signals = detect_all_trends(symbols, timeframe='4h')
```

### 3. 生成报告

```python
detector = MarketTrendDetector()
signals = detector.detect_all()

# 生成文本报告
report = detector.generate_report(signals)
print(report)

# 保存信号到 JSON
detector.save_signals(signals)
```

## 核心指标说明

### MA200 (200 日均线)
- **above**: 价格 > MA200 (5% 以上) → 长期看涨
- **below**: 价格 < MA200 (5% 以上) → 长期看跌
- **neutral**: 价格在 MA200 附近 (±5%) → 方向不明

### 高低点序列
- **HH_HL**: Higher High + Higher Low → 牛市结构
- **LH_LL**: Lower High + Lower Low → 熊市结构
- **mixed**: 混合模式 → 震荡或过渡期

### ADX (平均趋向指数)
- **ADX > 25**: 强趋势 (无论涨跌)
- **ADX < 20**: 无趋势 (震荡市场)
- **20-25**: 过渡区域

### 趋势评分 (0-100)
- **> 55**: 牛市
- **< 45**: 熊市
- **40-60**: 震荡

### 置信度 (0-1)
- **> 0.75**: 高置信度 (数据充足 + 信号一致)
- **0.5-0.75**: 中等置信度
- **< 0.5**: 低置信度 (数据不足或信号冲突)

## 与其他模块集成

### 在交易策略中使用

```python
from market_trend_detector import MarketTrendDetector
from adaptive_strategy_engine import AdaptiveStrategy

detector = MarketTrendDetector()
strategy = AdaptiveStrategy()

# 检测市场状态
signals = detector.detect_all()

for symbol, signal in signals.items():
    if signal.market_state.value == 'bull' and signal.confidence > 0.7:
        # 牛市高置信度 → 做多
        strategy.enter_long(symbol)
    elif signal.market_state.value == 'bear' and signal.confidence > 0.7:
        # 熊市高置信度 → 做空
        strategy.enter_short(symbol)
    else:
        # 震荡 → 观望或区间交易
        strategy.standby(symbol)
```

### 在风控模块中使用

```python
def adjust_position_size(symbol, base_size):
    """根据趋势强度调整仓位"""
    signal = detect_market_trend(symbol)
    
    if not signal:
        return base_size * 0.5  # 数据不足，减仓
    
    # 高置信度 → 标准仓位
    if signal.confidence > 0.75:
        return base_size
    
    # 中等置信度 → 70% 仓位
    elif signal.confidence > 0.5:
        return base_size * 0.7
    
    # 低置信度 → 50% 仓位
    else:
        return base_size * 0.5
```

### 在回测中使用

```python
from market_trend_detector import MarketTrendDetector

detector = MarketTrendDetector()

# 获取历史信号
signals = detector.detect_all()

# 筛选高置信度信号
high_conf_signals = {
    symbol: signal 
    for symbol, signal in signals.items() 
    if signal.confidence > 0.7
}

# 仅回测高置信度信号
backtest_results = run_backtest(high_conf_signals)
```

## 定时任务集成

### 添加到每日调度

```bash
# 编辑 scheduler.sh
# 在每日任务中添加：

# 市场趋势检测 (每日 8:00)
0 8 * * * cd ~/.openclaw/workspace/quant && python3 -c "
from market_trend_detector import MarketTrendDetector
detector = MarketTrendDetector()
signals = detector.detect_all()
detector.save_signals(signals)
"
```

### 在 main.py 中集成

```python
# 在 main.py 的主流程中添加
from market_trend_detector import MarketTrendDetector

def main():
    # ... 数据收集 ...
    # ... 技术分析 ...
    
    # 趋势检测
    detector = MarketTrendDetector()
    trend_signals = detector.detect_all()
    detector.save_signals(trend_signals)
    
    # 生成报告
    report = detector.generate_report(trend_signals)
    print(report)
    
    # ... 训练模型 ...
    # ... 回测 ...
```

## API 参考

### MarketTrendDetector 类

#### 方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `detect_trend(symbol, timeframe)` | 检测单个币种 | `TrendSignal` 或 `None` |
| `detect_all(symbols, timeframe)` | 批量检测 | `Dict[str, TrendSignal]` |
| `generate_report(signals)` | 生成文本报告 | `str` |
| `save_signals(signals, output_path)` | 保存信号到 JSON | `Path` |

#### 参数

- `symbol`: 币种符号 (如 'BTCUSDT')
- `timeframe`: 时间周期 ('1h', '4h', '1d')
- `symbols`: 币种列表，默认使用 config.CORE_COINS
- `output_path`: 输出路径，默认保存到 backtest/ 目录

### TrendSignal 数据类

```python
@dataclass
class TrendSignal:
    symbol: str              # 币种符号
    market_state: MarketState  # 市场状态枚举
    trend_score: float       # 趋势评分 (0-100)
    ma200_signal: str        # 'above'/'below'/'neutral'
    swing_pattern: str       # 'HH_HL'/'LH_LL'/'mixed'
    adx_value: float         # ADX 值
    adx_signal: str          # 'strong'/'weak'/'none'
    confidence: float        # 置信度 (0-1)
    timestamp: pd.Timestamp  # 时间戳
```

### MarketState 枚举

```python
class MarketState(Enum):
    BULL = "bull"           # 牛市
    BEAR = "bear"           # 熊市
    SIDEWAYS = "sideways"   # 震荡
    UNKNOWN = "unknown"     # 数据不足
```

## 输出示例

### JSON 信号文件

```json
{
  "timestamp": "2026-03-04T11:10:00",
  "signals": {
    "BTCUSDT": {
      "market_state": "bear",
      "trend_score": 10.5,
      "ma200_signal": "below",
      "swing_pattern": "mixed",
      "adx_value": 23.1,
      "adx_signal": "none",
      "confidence": 0.65,
      "timestamp": "2026-03-04 00:00:00"
    }
  }
}
```

### 文本报告

```
🦞 ============================================================
🦞 市场趋势预判报告
🦞 ============================================================

📊 总体统计:
   🐂 牛市：0 个 (0.0%)
   🐻 熊市：8 个 (88.9%)
   ➡️  震荡：1 个 (11.1%)

📈 趋势强度排名 (从高到低):
------------------------------------------------------------
➡️ AVAXUSDT     | 评分: 50.0 | ADX: 16.3 | HH_HL   | MA200:below  
🐻 ADAUSDT      | 评分: 45.0 | ADX: 20.7 | HH_HL   | MA200:below  
🐻 SOLUSDT      | 评分: 15.0 | ADX: 13.9 | mixed   | MA200:below  

🔑 图例:
   HH_HL = 更高高点 + 更高低点 (牛市结构)
   LH_LL = 更低高点 + 更低低点 (熊市结构)
   ADX > 25 = 强趋势，ADX < 20 = 震荡
   评分 > 70 = 牛市，评分 < 30 = 熊市，40-60 = 震荡
```

## 故障排查

### 数据不足错误

```
🦞 数据不足 BTCUSDT: 150 < 200
```

**解决**: 确保数据文件包含至少 200 根 K 线。运行数据收集器:

```bash
python3 data_collector.py
```

### 文件不存在

```
🦞 数据不存在：/home/admin/.openclaw/workspace/quant/data/BTCUSDT_1d.csv
```

**解决**: 检查文件名格式是否正确 (应该是 `SYMBOL_TIMEFRAME.csv`)

### 评分异常

如果所有币种都显示为同一状态 (如全部熊市),检查:

1. MA200 计算是否正确
2. 高低点检测窗口是否合适
3. ADX 阈值是否需要调整

可在 `__init__` 中调整阈值:

```python
detector = MarketTrendDetector()
detector.ADX_STRONG_THRESHOLD = 30  # 提高强趋势门槛
detector.TREND_SCORE_BULL = 60      # 提高牛市门槛
```

## 性能优化

### 缓存结果

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_signal(symbol: str, timeframe: str) -> TrendSignal:
    detector = MarketTrendDetector()
    return detector.detect_trend(symbol, timeframe)
```

### 并行检测

```python
from multiprocessing import Pool

symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

with Pool(processes=4) as pool:
    results = pool.starmap(
        detector.detect_trend,
        [(s, '1d') for s in symbols]
    )
```

---

🦞 **Make It Yours**: 根据你的交易风格调整阈值和权重!
