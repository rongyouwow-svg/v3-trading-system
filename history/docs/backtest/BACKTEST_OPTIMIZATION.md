# 🦞 回测记录优化指南

## 功能概述

本次优化为龙虾王量化系统添加了完整的回测记录管理功能，包括：

1. ✅ **统一止损止盈设置** - 所有策略使用统一的风控参数
2. ✅ **详细交易记录** - 记录每笔交易的完整信息
3. ✅ **策略对比表格** - 自动生成 Markdown 格式的策略对比报告
4. ✅ **持久化存储** - 保存到 JSON 和 Markdown 文件

## 统一风控参数

所有策略使用以下统一设置：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 止损 (Stop Loss) | 5% | 价格反向波动 5% 自动平仓 |
| 止盈 (Take Profit) | 15% | 价格正向波动 15% 自动平仓 |
| 单笔风险 (Risk per Trade) | 2% | 每笔交易最多损失总资金的 2% |

## 详细交易记录字段

每笔交易记录包含以下信息：

### 基础信息
- `trade_id` - 交易编号（如 T00001）
- `symbol` - 交易币种（如 BTCUSDT）
- `strategy` - 使用的策略名称
- `direction` - 多空方向（LONG/SHORT）

### 价格信息
- `entry_price` - 开仓价格
- `entry_time` - 开仓时间
- `exit_price` - 平仓价格
- `exit_time` - 平仓时间
- `stop_loss` - 止损价格
- `take_profit` - 止盈价格

### 盈亏信息
- `size` - 仓位大小
- `pnl` - 盈亏金额（USDT）
- `pnl_pct` - 盈亏百分比

### 统计信息
- `exit_reason` - 平仓原因（STOP_LOSS/TAKE_PROFIT/SIGNAL_REVERSE）
- `holding_period_hours` - 持仓时间（小时）
- `indicators_used` - 使用的指标组合
- `market_condition` - 市场状态（BULL/BEAR/SIDEWAYS）

## 策略对比表格内容

生成的 Markdown 表格包含：

### 1. 策略绩效对比
- 交易次数
- 胜率
- 平均盈利百分比
- 平均亏损
- 总盈亏
- 止损触发次数
- 止盈触发次数
- 平均持仓时间

### 2. 交易周期分布
- 最短持仓时间
- 最长持仓时间
- 平均持仓时间

### 3. 多空方向统计
- 多头交易数量
- 空头交易数量
- 多头胜率
- 空头胜率

### 4. 指标组合效果
- 每个指标组合的交易次数
- 胜率
- 平均盈亏百分比

### 5. 止盈条件触发统计
- 总交易数
- 止损触发次数
- 止盈触发次数
- 信号反转次数
- 止盈占比

## 使用方法

### 快速运行

```bash
cd ~/.openclaw/workspace/quant

# 使用默认配置（5 个币种，90 天）
python3 run_optimized_backtest.py

# 自定义币种和天数
python3 run_optimized_backtest.py BTCUSDT,ETHUSDT,SOLUSDT 90
```

### 在代码中使用

```python
from strategy_optimizer_v2 import StrategyOptimizerV2

# 创建优化器
optimizer = StrategyOptimizerV2(initial_capital=10000)

# 运行回测
results = optimizer.run_mass_backtest(
    symbols=['BTCUSDT', 'ETHUSDT'],
    days=90,
    save_detailed=True  # 保存详细记录
)
```

### 自定义风控参数

```python
from backtest_engine_v2 import BacktestEngineV2

# 自定义止损止盈
engine = BacktestEngineV2(
    initial_capital=10000,
    stop_loss_pct=0.03,      # 3% 止损
    take_profit_pct=0.12,    # 12% 止盈
    risk_per_trade=0.015     # 1.5% 风险
)
```

## 输出文件

运行后会在 `backtest/` 目录生成以下文件：

1. **detailed_trade_log.json** - 详细交易记录（JSON 格式）
2. **strategy_comparison_table.md** - 策略对比表格（Markdown 格式）
3. **optimization_report_v2.json** - 优化报告汇总（JSON 格式）

## 文件位置

```
~/.openclaw/workspace/quant/backtest/
├── detailed_trade_log.json          # 详细交易记录
├── strategy_comparison_table.md     # 策略对比表格
├── optimization_report_v2.json      # 优化报告
└── optimization_report.json         # 旧版报告（兼容）
```

## 示例输出

### detailed_trade_log.json（片段）

```json
[
  {
    "trade_id": "T00001",
    "symbol": "BTCUSDT",
    "strategy": "trend_following",
    "direction": "SHORT",
    "entry_price": 73139.13,
    "entry_time": "2026-02-03 18:00:00",
    "exit_price": 70918.99,
    "exit_time": "2026-02-07 03:00:00",
    "size": 0.0547,
    "stop_loss": 76796.09,
    "take_profit": 62168.26,
    "pnl": 121.42,
    "pnl_pct": 3.04,
    "exit_reason": "SIGNAL_REVERSE",
    "holding_period_hours": 81.0,
    "indicators_used": "EMA20+EMA50+MACD",
    "market_condition": "SIDEWAYS"
  }
]
```

### strategy_comparison_table.md（片段）

```markdown
# 🦞 策略对比报告

生成时间：2026-03-03 22:10:15

总交易数：109

## 策略绩效对比

| 策略名称 | 交易次数 | 胜率 | 平均盈利% | 平均亏损 | 总盈亏 | 止损触发 | 止盈触发 | 平均持仓 (小时) |
|----------|----------|------|-----------|----------|--------|----------|----------|----------------|
| breakout | 20 | 55.0% | 1.26% | -98.90 | 1002.11 | 2 | 1 | 61.4 |
| mean_reversion | 27 | 48.1% | 0.33% | -164.38 | 305.53 | 11 | 0 | 44.7 |
| trend_following | 31 | 25.8% | -1.32% | -114.59 | -1607.74 | 5 | 1 | 41.3 |
```

## 核心模块

### backtest_engine_v2.py

回测引擎 v2，提供：
- 统一止损止盈逻辑
- 详细交易记录生成
- 交易统计计算
- 对比表格生成

### strategy_optimizer_v2.py

策略优化器 v2，提供：
- 多币种 × 多策略批量回测
- 策略绩效分析
- 市场状态检测
- 结果汇总报告

### run_optimized_backtest.py

一键运行脚本，提供：
- 命令行参数支持
- 默认配置
- 结果摘要输出

## 配置说明

### config.py 相关参数

```python
# 回测配置
INITIAL_CAPITAL = 10000       # 初始资金
POSITION_SIZE = 0.1           # 默认仓位比例
BACKTEST_DIR = 'backtest'     # 回测结果目录
```

### 策略指标映射

| 策略名称 | 使用指标 |
|----------|----------|
| trend_following | EMA20+EMA50+MACD |
| mean_reversion | RSI+Bollinger |
| breakout | Volume+Price+MA20 |
| multi_timeframe | EMA+MACD+Volume |

## 注意事项

1. **数据要求** - 确保数据文件存在且格式正确
2. **内存使用** - 大规模回测（>1000 天）可能需要较多内存
3. **运行时间** - 回测时间随币种数量和天数增长
4. **文件覆盖** - 每次运行会覆盖之前的输出文件

## 故障排查

### 问题：回测结果为空

**解决：**
```bash
# 检查数据文件
ls -lh data/*.csv

# 检查数据格式
head -5 data/BTCUSDT_1h.csv
```

### 问题：指标列缺失

**解决：**
```python
# 在回测前先运行技术分析
from advanced_analysis import AdvancedAnalyzer
analyzer = AdvancedAnalyzer()
df = analyzer.load_data('BTCUSDT', '1h')
df = analyzer.add_all_indicators(df)
```

## 未来优化方向

- [ ] 支持自定义止损止盈策略
- [ ] 添加更多退出条件（时间退出、追踪止损等）
- [ ] 支持多时间框架回测
- [ ] 添加交易成本（手续费、滑点）
- [ ] 生成可视化图表（权益曲线、回撤图等）

---

📅 最后更新：2026-03-03
🦞 龙虾王量化团队
