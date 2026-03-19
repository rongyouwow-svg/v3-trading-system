# 🦞 四币种批量回测系统

## 概述

本系统支持对 BTC、ETH、BNB、SOL 四个主流币种进行统一回测，包含完整的数据验证、参数配置、批量执行和报告生成流程。

## 文件结构

```
quant/
├── four_coin_backtest_config.yaml    # 回测配置文件
├── run_four_coin_backtest.py         # 批量回测执行脚本
├── backtest_framework_v2.py          # 回测框架核心
├── indicator_based_exit.py           # 指标条件退出模块
├── data/
│   ├── BTCUSDT_30m.csv              # BTC 30 分钟数据 (149,530 条)
│   ├── ETHUSDT_30m.csv              # ETH 30 分钟数据 (149,530 条)
│   ├── BNBUSDT_30m.csv              # BNB 30 分钟数据 (90,544 条)
│   └── SOLUSDT_30m.csv              # SOL 30 分钟数据 (90,544 条)
└── backtest/four_coin/               # 回测结果输出目录
    ├── batch_report_YYYYMMDD_HHMMSS.json
    ├── batch_summary_YYYYMMDD_HHMMSS.md
    └── detailed_trade_log.json
```

## 数据完整性验证

### 数据概览

| 币种 | K 线条数 | 时间范围 | 价格范围 |
|------|---------|---------|---------|
| BTCUSDT | 149,530 | 2017-08-17 ~ 2026-03-04 | $2,817 - $126,199 |
| ETHUSDT | 149,530 | 2017-08-17 ~ 2026-03-04 | $81.79 - $4,956 |
| BNBUSDT | 90,544 | 2020-12-31 ~ 2026-03-02 | $35.04 - $1,375 |
| SOLUSDT | 90,544 | 2020-12-31 ~ 2026-03-02 | $1.45 - $295.83 |

### 数据质量检查

自动验证以下内容：
- ✅ 必要列完整性 (timestamp/open/high/low/close/volume)
- ✅ 最小数据条数 (≥1000 条)
- ✅ 空值检测
- ✅ 价格合理性 (无负值/零值)
- ✅ 成交量合理性 (无负值)

## 回测参数配置

### 核心参数 (four_coin_backtest_config.yaml)

```yaml
backtest:
  initial_capital: 10000      # 初始资金 10,000 USDT
  position_size: 0.1          # 单笔仓位 10%
  leverage: 1                 # 1 倍杠杆 (现货模式)
  
risk_management:
  stop_loss:
    type: fixed
    value: 0.05               # 5% 固定止损
  take_profit:
    type: multiple
    risk_reward_ratio: 3.0    # 3 倍盈亏比

indicators:
  rsi:
    enabled: true
    period: 14
    buy_threshold: 30         # RSI<30 超卖买入
  macd:
    enabled: true
    bullish_cross: true       # 金叉买入信号
  ema:
    enabled: true
    fast_period: 12
    slow_period: 26
```

### 可调整参数

| 参数 | 当前值 | 建议范围 | 说明 |
|------|-------|---------|------|
| `initial_capital` | 10,000 | 1,000 - 100,000 | 初始资金 |
| `position_size` | 0.1 (10%) | 0.05 - 0.20 | 单笔仓位占比 |
| `stop_loss` | 0.05 (5%) | 0.03 - 0.10 | 止损百分比 |
| `risk_reward_ratio` | 3.0 | 2.0 - 5.0 | 盈亏比倍数 |
| `min_confirmations` | 2 | 1 - 3 | 指标确认数量 |

## 使用方法

### 1. 快速回测 (使用默认配置)

```bash
cd ~/.openclaw/workspace/quant
python3 run_four_coin_backtest.py
```

### 2. 自定义配置文件回测

```bash
# 编辑配置文件
vim four_coin_backtest_config.yaml

# 运行回测
python3 run_four_coin_backtest.py four_coin_backtest_config.yaml
```

### 3. Python API 调用

```python
from run_four_coin_backtest import run_batch

# 运行批量回测
report = run_batch('four_coin_backtest_config.yaml')

# 查看结果
print(f"平均收益：{report['summary']['avg_return']:.2f}%")
print(f"最佳币种：{report['summary']['best_performer']['symbol']}")
```

### 4. 单币种快速测试

```bash
# 仅回测 BTC (使用最近 1000 条数据)
python3 -c "
from backtest_framework_v2 import *
import pandas as pd

df = pd.read_csv('data/BTCUSDT_30m.csv').tail(1000)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

signal_gen = SignalGenerator([
    IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=30),
    IndicatorConfig.macd_cross(bullish=True)
])

engine = BacktestEngine(
    initial_capital=10000,
    stop_loss=StopLossConfig.fixed(0.05),
    take_profit=TakeProfitConfig.by_rr(3.0)
)

result = engine.run_backtest(df, signal_gen, 'BTCUSDT')
print(f'收益：{result.total_return_pct:.2f}%')
"
```

## 输出结果

### JSON 报告 (batch_report_*.json)

包含完整回测数据：
- 配置摘要
- 各币种详细回测结果
- 绩效指标排名
- 交易明细
- 权益曲线数据

### Markdown 摘要 (batch_summary_*.md)

包含：
- 配置概览
- 回测统计
- 收益排名表格
- 夏普比率排名

### 详细交易记录 (detailed_trade_log.json)

每笔交易的详细信息：
- 入场时间/价格
- 出场时间/价格
- 盈亏金额/百分比
- 出场原因 (TP/SL/TIME)

## 回测策略说明

### 信号生成逻辑

采用**多指标多数决**原则：

1. **RSI 超卖** (RSI < 30) → 买入信号 +1
2. **MACD 金叉** → 买入信号 +1
3. **EMA 金叉** (12/26) → 买入信号 +1

当买入信号数量 ≥ `min_confirmations` (默认 2) 时，生成 BUY 信号。

### 止盈止损逻辑

**止损** (满足任一即触发)：
- 固定止损：价格下跌 5%

**止盈** (满足任一即触发)：
- 盈亏比止盈：价格上涨 15% (3 倍于止损距离)

### 仓位管理

- 单笔仓位：10% 总资金
- 最大仓位：55% (防止过度集中)
- 不支持加仓/减仓 (简化模型)

## 性能优化建议

### 1. 参数优化方向

```yaml
# 保守策略 (低回撤)
position_size: 0.05
stop_loss: 0.03
risk_reward_ratio: 4.0

# 激进策略 (高收益)
position_size: 0.20
stop_loss: 0.08
risk_reward_ratio: 2.5
```

### 2. 指标组合优化

```yaml
# 趋势跟踪组合
indicators:
  rsi: {enabled: false}
  macd: {enabled: true}
  ema: {enabled: true}
  bollinger: {enabled: true}

# 反转策略组合
indicators:
  rsi: {enabled: true, buy_threshold: 25}
  macd: {enabled: false}
  ema: {enabled: false}
  bollinger: {enabled: true}
```

### 3. 多时间周期测试

```bash
# 修改配置文件中的 timeframe
data:
  timeframe: 1h  # 或 4h, 1d

# 重新运行回测
python3 run_four_coin_backtest.py
```

## 常见问题

### Q1: 回测结果为负收益怎么办？

**可能原因**：
- 参数不适合当前市场
- 指标组合效果差
- 数据周期包含大熊市

**解决方案**：
1. 调整止损止盈比例
2. 增加指标确认数量
3. 缩短回测周期 (仅测试近期数据)

### Q2: 交易次数太少？

**可能原因**：
- 指标确认要求过高
- 止损过紧频繁触发

**解决方案**：
1. 降低 `min_confirmations` 到 1
2. 放宽止损到 8-10%
3. 增加更多买入信号指标

### Q3: 如何对比不同参数组合？

使用配置文件的网格搜索功能：

```yaml
batch_backtest:
  optimization:
    enabled: true
    param_grid:
      position_size: [0.05, 0.1, 0.15]
      stop_loss: [0.03, 0.05, 0.08]
      take_profit_rr: [2.0, 3.0, 4.0]
    objective: max_sharpe
```

## 下一步计划

- [ ] 添加参数优化网格搜索
- [ ] 支持多时间周期回测
- [ ] 添加 Walk-Forward 分析
- [ ] 集成实时信号生成
- [ ] 添加 Monte Carlo 模拟

## 联系与反馈

🦞 龙虾王量化系统  
有问题请联系：大王

---

**最后更新**: 2026-03-04  
**版本**: v1.0
