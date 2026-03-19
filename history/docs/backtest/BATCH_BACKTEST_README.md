# 🦞 龙虾王批量回测接口 v1.0

## 功能概述

批量回测接口提供以下功能：

1. **批量回测多个币种** - 一次回测多个交易对
2. **策略对比** - 同时测试多个策略配置
3. **并行处理** - 支持多线程加速回测
4. **汇总报告** - 自动生成 JSON/CSV/HTML 报告

## 文件结构

```
quant/
├── backtest_framework_v2.py    # 回测框架 v2（核心引擎）
├── batch_backtest.py            # 批量回测接口（新增）
├── backtest_api_server.py       # API 服务器（已更新）
└── backtest/                    # 回测结果目录
```

## 使用方法

### 1. Python 代码调用

#### 批量回测示例

```python
from batch_backtest import BatchBacktestEngine, BatchBacktestRequest
from backtest_framework_v2 import IndicatorConfig, SignalCondition, StopLossConfig, TakeProfitConfig

# 配置指标
indicator_configs = [
    IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=30),
    IndicatorConfig.macd_cross(bullish=True),
]

# 配置止盈止损
stop_loss = StopLossConfig.fixed(0.05)  # 5% 止损
take_profit = TakeProfitConfig.by_rr(3.0)  # 3 倍盈亏比

# 创建批量回测请求
request = BatchBacktestRequest(
    symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
    indicator_configs=indicator_configs,
    stop_loss=stop_loss,
    take_profit=take_profit,
    position_size=0.1,
    initial_capital=10000,
    timeframe='30m',
    parallel=True  # 启用并行处理
)

# 执行批量回测
engine = BatchBacktestEngine()
result = engine.run_batch(request)

# 打印结果
print(f"总收益：${result.total_return:.2f}")
print(f"平均收益：{result.avg_return:+.2f}%")
print(f"最佳币种：{result.best_symbol}")
```

#### 策略对比示例

```python
from batch_backtest import StrategyComparator, StrategyConfig
from backtest_framework_v2 import IndicatorConfig, SignalCondition, StopLossConfig, TakeProfitConfig

# 定义多个策略
strategies = [
    StrategyConfig(
        name="RSI 超卖策略",
        indicator_configs=[
            IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=30)
        ],
        stop_loss=StopLossConfig.fixed(0.05),
        take_profit=TakeProfitConfig.by_rr(3.0)
    ),
    StrategyConfig(
        name="多指标组合策略",
        indicator_configs=[
            IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=30),
            IndicatorConfig.macd_cross(bullish=True),
            IndicatorConfig.ema_cross(fast=12, slow=26, bullish=True)
        ],
        stop_loss=StopLossConfig.trailing(0.03),
        take_profit=TakeProfitConfig.by_rr(3.0)
    )
]

# 执行对比
comparator = StrategyComparator()
comparison = comparator.compare_strategies(
    symbols=['BTCUSDT', 'ETHUSDT'],
    strategies=strategies,
    timeframe='30m'
)

# 查看对比结果
print(f"最佳策略：{comparison['best_strategy']}")
print(f"推荐：{comparison['recommendation']}")
```

### 2. API 调用

启动 API 服务器：

```bash
cd ~/.openclaw/workspace/quant
python3 backtest_api_server.py 8000
```

#### 批量回测 API

```bash
curl -X POST http://localhost:8000/api/batch_backtest \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
    "timeframe": "30m",
    "position_size": 0.1,
    "initial_capital": 10000,
    "parallel": true,
    "indicators": ["RSI", "MACD"],
    "conditions": {
      "rsiCondition": "below_30",
      "macdCondition": "bullish_cross"
    },
    "stop_loss": {"type": "fixed", "value": 0.05},
    "take_profit": {"type": "multiple", "value": 3.0}
  }'
```

#### 策略对比 API

```bash
curl -X POST http://localhost:8000/api/compare_strategies \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "timeframe": "30m",
    "strategies": [
      {
        "name": "RSI 策略",
        "indicators": ["RSI"],
        "conditions": {"rsiCondition": "below_30"},
        "stop_loss": {"type": "fixed", "value": 0.05},
        "take_profit": {"type": "multiple", "value": 3.0}
      },
      {
        "name": "MACD 策略",
        "indicators": ["MACD"],
        "conditions": {"macdCondition": "bullish_cross"},
        "stop_loss": {"type": "fixed", "value": 0.05},
        "take_profit": {"type": "multiple", "value": 3.0}
      }
    ]
  }'
```

### 3. 命令行运行

```bash
# 运行批量回测演示
cd ~/.openclaw/workspace/quant
python3 batch_backtest.py

# 运行策略对比演示
python3 batch_backtest.py compare
```

## 输出文件

批量回测完成后会自动生成以下文件：

1. **JSON 报告** - `backtest/batch_backtest_YYYYMMDD_HHMMSS.json`
   - 完整的回测数据和配置
   
2. **CSV 汇总** - `backtest/batch_summary_YYYYMMDD_HHMMSS.csv`
   - 各币种关键指标汇总
   
3. **HTML 报告** - `backtest/batch_report.html`
   - 可视化报告（可在浏览器打开）

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/backtest` | POST | 单个币种回测 |
| `/api/batch_backtest` | POST | 批量回测 |
| `/api/compare_strategies` | POST | 策略对比 |
| `/api/symbols` | GET | 获取可用币种列表 |
| `/api/indicators` | GET | 获取可用指标列表 |

## 配置选项

### 指标配置

```python
# RSI
IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=30)

# MACD 金叉
IndicatorConfig.macd_cross(bullish=True)

# MACD 死叉
IndicatorConfig.macd_cross(bullish=False)

# EMA 金叉
IndicatorConfig.ema_cross(fast=12, slow=26, bullish=True)

# 布林带突破
IndicatorConfig.bb_breakout(breakout_above=True)
```

### 止盈止损配置

```python
# 固定止损
StopLossConfig.fixed(0.05)  # 5%

# 移动止损
StopLossConfig.trailing(0.03)  # 3%

# 固定止盈
TakeProfitConfig.fixed(0.15)  # 15%

# 盈亏比止盈
TakeProfitConfig.by_rr(3.0)  # 3 倍风险回报比
```

## 性能优化

### 并行处理

```python
# 自动根据 CPU 核心数调整
request = BatchBacktestRequest(
    symbols=symbols_list,  # 币种越多，并行效果越明显
    parallel=True,
    max_workers=None  # None = 自动，或手动指定线程数
)
```

### 批量大小建议

- **小批量** (1-5 币种): 串行或并行皆可
- **中批量** (5-20 币种): 推荐并行，节省 50-70% 时间
- **大批量** (20+ 币种): 必须并行，建议分批处理

## 错误处理

批量回测会捕获每个币种的错误，不会因单个币种失败而中断整体回测：

```python
for result in batch_result.results:
    if result.error:
        print(f"❌ {result.symbol}: {result.error}")
    else:
        print(f"✅ {result.symbol}: {result.result.total_return_pct:+.2f}%")
```

## 与新配置界面兼容

批量回测接口完全兼容 `strategy_config.html` 配置界面：

1. 配置界面保存的配置可导出为 JSON
2. JSON 配置可直接传递给 API 的 `/api/batch_backtest` 端点
3. 回测结果可在配置界面展示

### 配置界面对接示例

```javascript
// 1. 从配置界面获取配置
const config = {
    indicators: ['RSI', 'MACD'],
    conditions: {
        rsiCondition: 'below_30',
        macdCondition: 'bullish_cross'
    },
    stopLoss: {type: 'fixed', value: 0.05},
    takeProfit: {type: 'multiple', value: 3.0},
    positionSize: 0.1
};

// 2. 调用批量回测 API
fetch('/api/batch_backtest', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        ...config,
        symbols: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
        timeframe: '30m',
        parallel: true
    })
})
.then(res => res.json())
.then(data => {
    console.log('批量回测结果:', data);
    // 在界面上展示结果
});
```

## 注意事项

1. **数据准备**: 确保 `data/` 目录下有所需币种的 CSV 数据
2. **数据格式**: CSV 需包含 `open, high, low, close, volume` 列
3. **数据量**: 每个币种至少需要 100 条 K 线
4. **内存占用**: 大批量回测时注意内存使用，建议分批处理

## 常见问题

**Q: 回测速度太慢？**
A: 启用并行处理 (`parallel=True`)，或减少回测币种数量。

**Q: 某些币种回测失败？**
A: 检查数据文件是否存在，数据格式是否正确。

**Q: 如何自定义指标？**
A: 在 `backtest_framework_v2.py` 中的 `TechnicalIndicators` 类添加新方法。

**Q: 如何修改止盈止损逻辑？**
A: 在 `backtest_framework_v2.py` 中的 `RiskManager` 类修改。

---

🦞 Happy Backtesting!
