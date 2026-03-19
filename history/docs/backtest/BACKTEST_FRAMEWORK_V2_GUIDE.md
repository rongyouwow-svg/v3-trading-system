# 🦞 量化回测框架 v2.0 使用指南

## 功能概览

### 1️⃣ 指标选择器（支持多选）

支持以下技术指标自由组合：

| 指标 | 说明 | 典型用法 |
|------|------|----------|
| **RSI** | 相对强弱指标 | 超卖买入 (<30)，超买卖出 (>70) |
| **MACD** | 趋势跟踪指标 | 金叉买入，死叉卖出 |
| **Bollinger Bands** | 布林带 | 突破上轨买入，跌破下轨卖出 |
| **Volume** | 成交量 | 放量确认突破 |
| **EMA** | 指数移动平均 | 快慢线金叉/死叉 |

### 2️⃣ 触发条件配置

每个指标支持多种触发条件：

```python
# RSI 条件
RSI < 20    # 极度超卖
RSI < 30    # 超卖
RSI > 70    # 超买
RSI > 80    # 极度超买

# MACD 条件
金叉 (DIF 上穿 DEA)
死叉 (DIF 下穿 DEA)

# EMA 交叉
EMA12 上穿 EMA26   # 短期金叉
EMA50 上穿 EMA200  # 黄金交叉
EMA12 下穿 EMA26   # 短期死叉
EMA50 下穿 EMA200  # 死亡交叉

# 布林带
价格突破上轨
价格跌破下轨

# 成交量
成交量 > 1.5 倍均量
```

### 3️⃣ 止盈止损设置

#### 止损类型

```python
# 固定止损
StopLossConfig.fixed(percent=0.05)  # 5% 止损

# 移动止损
StopLossConfig.trailing(percent=0.03)  # 3% 跟踪止损

# 时间止损
StopLossConfig.time_based(periods=10)  # 10 个周期后强制平仓
```

#### 止盈类型

```python
# 固定止盈
TakeProfitConfig.fixed(percent=0.15)  # 15% 止盈

# 盈亏比倍数
TakeProfitConfig.by_rr(ratio=3.0)  # 3 倍风险回报比

# 移动止盈
TakeProfitConfig.trailing(percent=0.05)  # 5% 跟踪止盈
```

### 4️⃣ 回测引擎（统一框架）

```python
from backtest_framework_v2 import (
    BacktestEngine, SignalGenerator, IndicatorConfig,
    StopLossConfig, TakeProfitConfig
)

# 1. 配置指标
indicator_configs = [
    IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=30),
    IndicatorConfig.macd_cross(bullish=True),
    IndicatorConfig.ema_cross(fast=12, slow=26, bullish=True),
]

# 2. 配置止盈止损
stop_loss = StopLossConfig.trailing(0.03)
take_profit = TakeProfitConfig.by_rr(3.0)

# 3. 创建信号生成器
signal_gen = SignalGenerator(indicator_configs)

# 4. 创建回测引擎
engine = BacktestEngine(
    initial_capital=10000,
    stop_loss=stop_loss,
    take_profit=take_profit,
    position_size=0.1
)

# 5. 加载数据
df = pd.read_csv('data/BTCUSDT_30m.csv', index_col=0, parse_dates=True)

# 6. 运行回测
result = engine.run_backtest(df, signal_gen, symbol='BTCUSDT')

# 7. 保存结果
engine.save_result(result)
```

### 5️⃣ 交易明细生成

回测结果包含完整的交易记录：

```python
# 访问交易明细
for trade in result.trades:
    print(f"交易 {trade.trade_id}:")
    print(f"  方向：{trade.direction}")
    print(f"  入场：{trade.entry_price} @ {trade.entry_date}")
    print(f"  出场：{trade.exit_price} @ {trade.exit_date}")
    print(f"  盈亏：{trade.pnl} ({trade.pnl_percent}%)")
    print(f"  出场原因：{trade.exit_reason}")
```

交易字段：
- `trade_id`: 交易编号
- `symbol`: 交易标的
- `entry_date/price`: 入场时间/价格
- `exit_date/price`: 出场时间/价格
- `position_size`: 仓位大小
- `direction`: 方向 (LONG/SHORT)
- `pnl/pnl_percent`: 盈亏金额/百分比
- `exit_reason`: 出场原因 (TP_FIXED/SL_TRAILING/等)
- `highest_price/lowest_price`: 持仓期间最高/最低价

### 6️⃣ K 线买卖点展示

```python
from backtest_framework_v2 import KLineVisualizer

# 生成图表数据
chart_data = KLineVisualizer.generate_chart_data(df, result)

# 生成 HTML 报告
KLineVisualizer.generate_html_report(
    result, 
    'backtest/report_BTCUSDT.html'
)
```

HTML 报告包含：
- 📊 绩效概览卡片
- 📈 权益曲线图
- 📝 交易明细表格
- 🎯 买卖点标记

---

## 快速开始

### 方法 1：命令行运行

```bash
cd ~/.openclaw/workspace/quant

# 运行演示
python3 backtest_framework_v2.py

# 启动 API 服务器
python3 backtest_api_server.py 8000

# 访问 Web 界面
# http://localhost:8000/backtest_framework.html
```

### 方法 2：Python 脚本

```python
from backtest_framework_v2 import *
import pandas as pd

# 加载数据
df = pd.read_csv('data/BTCUSDT_30m.csv', index_col=0, parse_dates=True)

# 配置策略
indicator_configs = [
    IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=30),
    IndicatorConfig.macd_cross(bullish=True),
]

stop_loss = StopLossConfig.fixed(0.05)
take_profit = TakeProfitConfig.fixed(0.15)

# 运行回测
signal_gen = SignalGenerator(indicator_configs)
engine = BacktestEngine(
    initial_capital=10000,
    stop_loss=stop_loss,
    take_profit=take_profit,
    position_size=0.1
)

result = engine.run_backtest(df, signal_gen, symbol='BTCUSDT')

# 查看结果
print(f"总收益：{result.total_return_pct:.2f}%")
print(f"最大回撤：{result.max_drawdown_pct:.2f}%")
print(f"夏普比率：{result.sharpe_ratio:.2f}")
print(f"胜率：{result.win_rate:.1f}%")
print(f"交易次数：{result.total_trades}")
```

### 方法 3：Web 界面

1. 启动 API 服务器：
```bash
cd ~/.openclaw/workspace/quant
python3 backtest_api_server.py 8000
```

2. 浏览器访问：
```
http://localhost:8000/backtest_framework.html
```

3. 配置策略参数：
   - 选择币种和时间周期
   - 勾选技术指标（支持多选）
   - 设置触发条件
   - 配置止盈止损
   - 设置仓位比例

4. 点击"运行回测"查看结果

---

## 策略示例

### 示例 1：RSI 超卖反弹策略

```python
indicator_configs = [
    IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=20),
]

stop_loss = StopLossConfig.fixed(0.05)
take_profit = TakeProfitConfig.fixed(0.15)
```

### 示例 2：MACD + EMA 双确认策略

```python
indicator_configs = [
    IndicatorConfig.macd_cross(bullish=True),
    IndicatorConfig.ema_cross(fast=12, slow=26, bullish=True),
]

stop_loss = StopLossConfig.trailing(0.03)
take_profit = TakeProfitConfig.by_rr(3.0)
```

### 示例 3：布林带突破策略

```python
indicator_configs = [
    IndicatorConfig.bb_breakout(breakout_above=True),
    IndicatorConfig(
        indicator=IndicatorType.VOLUME,
        params={'period': 20},
        condition=SignalCondition.ABOVE,
        threshold=1.5
    ),
]

stop_loss = StopLossConfig.fixed(0.04)
take_profit = TakeProfitConfig.fixed(0.12)
```

### 示例 4：多指标共振策略（激进）

```python
indicator_configs = [
    IndicatorConfig.rsi(condition=SignalCondition.BELOW, threshold=30),
    IndicatorConfig.macd_cross(bullish=True),
    IndicatorConfig.ema_cross(fast=12, slow=26, bullish=True),
    IndicatorConfig.bb_breakout(breakout_above=False),  # 从下轨反弹
]

stop_loss = StopLossConfig.trailing(0.02)
take_profit = TakeProfitConfig.by_rr(4.0)
position_size = 0.2  # 20% 仓位
```

---

## 回测结果解读

### 关键指标

| 指标 | 含义 | 理想值 |
|------|------|--------|
| **总收益** | 策略总回报率 | > 50% (8 年回测) |
| **最大回撤** | 最大资金回撤 | < 30% |
| **夏普比率** | 风险调整后收益 | > 1.0 |
| **胜率** | 盈利交易占比 | > 45% |
| **盈亏比** | 平均盈利/平均亏损 | > 2.0 |
| **交易次数** | 总交易数 | 适中 (避免过度交易) |

### 出场原因说明

| 代码 | 含义 |
|------|------|
| `TP_FIXED` | 固定止盈触发 |
| `TP_TRAILING` | 移动止盈触发 |
| `TP_RR` | 盈亏比目标达成 |
| `SL_FIXED` | 固定止损触发 |
| `SL_TRAILING` | 移动止损触发 |
| `SL_TIME` | 时间止损触发 |
| `MANUAL` | 强制平仓（回测结束） |

---

## 文件结构

```
quant/
├── backtest_framework_v2.py      # 核心回测框架
├── backtest_api_server.py        # API 服务器
├── web/
│   └── backtest_framework.html   # Web 界面
├── backtest/                      # 回测结果存储
│   └── *.json                     # 回测报告
└── BACKTEST_FRAMEWORK_V2_GUIDE.md # 使用指南
```

---

## 常见问题

### Q1: 回测结果为空？
- 检查数据文件是否存在
- 确保数据量足够（至少 100 条 K 线）
- 验证指标配置是否合理

### Q2: 胜率很低但盈利？
- 这是正常现象，关键看盈亏比
- 趋势策略通常胜率 40-50%，但盈亏比 > 2

### Q3: 如何优化策略？
- 调整指标参数（RSI 周期、EMA 周期等）
- 修改止盈止损比例
- 增加/减少确认指标数量
- 使用多时间周期验证

### Q4: 支持做空吗？
- 支持！框架内置 LONG/SHORT 双向交易
- 修改信号逻辑即可生成做空信号

---

## 下一步

1. **参数优化**: 使用网格搜索找到最优参数组合
2. **多币种回测**: 批量测试所有币种
3. **实盘对接**: 连接交易所 API 执行真实交易
4. **风险控制**: 增加仓位管理、相关性分析

---

_🦞 龙虾王量化 · 让回测更简单_
