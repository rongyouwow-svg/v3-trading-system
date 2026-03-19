# 🦞 龙虾王实盘信号系统

## Live Trading System - 使用指南

**版本**: v1.0  
**创建日期**: 2026-03-03  
**作者**: 龙虾王 AI 市场分析师

---

## 📋 系统概述

实盘信号系统是一个完整的加密货币交易信号生成与执行模拟系统，包含以下核心模块：

```
┌─────────────────────────────────────────────────────────┐
│                  🦞 实盘信号系统                        │
├─────────────────────────────────────────────────────────┤
│  1️⃣ 实时数据接入 (RealtimeDataFeed)                    │
│     └─ Binance K 线数据获取 + 缓存管理                   │
│                                                         │
│  2️⃣ 信号生成 (SignalGenerator)                         │
│     └─ 模型预测 + 技术指标确认 + 置信度评估              │
│                                                         │
│  3️⃣ 风控检查 (RiskManager)                             │
│     └─ 止损止盈计算 + 凯利公式仓位管理 + 风险预警        │
│                                                         │
│  4️⃣ 订单执行模拟 (OrderExecutor)                       │
│     └─ 订单提交 + 模拟成交 + 佣金计算                   │
│                                                         │
│  5️⃣ 日志记录 (TradingLogger)                           │
│     └─ 信号日志 + 订单日志 + 执行报告                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 基础使用

```python
from live_trading_system import LiveTradingSystem

# 创建系统
system = LiveTradingSystem(
    symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],  # 监控币种
    initial_capital=10000,                       # 初始资金 (USDT)
    timeframe='1h',                              # 时间周期
    min_confidence=0.6                           # 最小置信度
)

# 执行单次扫描
signals = system.run_scan()

# 查看系统状态
status = system.get_status()
print(f"总信号数：{status['system_state']['total_signals']}")
print(f"当前净值：{status['risk_metrics']['capital']['total_value']:.2f}")
```

### 2. 连续运行

```python
# 连续运行（每 5 分钟扫描一次）
system.run_continuous(
    scan_interval_seconds=300,  # 扫描间隔（秒）
    max_iterations=None         # 最大迭代次数（None 为无限）
)

# 停止系统
system.stop()
```

### 3. 命令行运行

```bash
# 运行主程序（单次扫描）
cd ~/.openclaw/workspace/quant && python3 live_trading_system.py

# 后台连续运行
cd ~/.openclaw/workspace/quant && nohup python3 -c "
from live_trading_system import LiveTradingSystem
system = LiveTradingSystem()
system.run_continuous(scan_interval_seconds=300)
" > logs/live_trading.log 2>&1 &
```

---

## 📦 模块详解

### 1️⃣ 实时数据接入 (RealtimeDataFeed)

**功能**:
- 从 Binance 获取实时 K 线数据
- 数据缓存与增量更新
- 数据质量检查

**关键方法**:
```python
# 获取最新数据
df = data_feed.get_latest_data('BTCUSDT', timeframe='1h')

# 获取最新价格
price = data_feed.get_latest_price('BTCUSDT')

# 批量更新
data_feed.update_all_symbols(['BTCUSDT', 'ETHUSDT'], timeframe='1h')
```

**配置参数**:
- `update_interval`: 数据更新间隔（默认 60 秒）

---

### 2️⃣ 信号生成 (SignalGenerator)

**功能**:
- 基于训练好的模型生成预测
- 技术指标多重确认（RSI、MACD、均线、布林带、成交量）
- 市场情境识别（牛市/熊市/震荡）
- 信号置信度评估

**信号生成流程**:
```
1. 检测市场情境 → 2. 模型预测 → 3. 技术指标确认 → 4. 综合置信度 → 5. 生成信号
```

**技术指标确认系统**:
| 指标 | 买入确认条件 | 卖出确认条件 | 置信度提升 |
|------|-------------|-------------|-----------|
| RSI | < 30 (超卖) | > 70 (超买) | +0.2 |
| MACD | 金叉 | 死叉 | +0.2 |
| 均线 | 多头排列 | 空头排列 | +0.1 |
| 布林带 | 接近下轨 | 接近上轨 | +0.1 |
| 成交量 | 放大 >1.5x | 放大 >1.5x | +0.1 |

**关键方法**:
```python
# 生成单个信号
signal = signal_generator.generate_signal('BTCUSDT', df, risk_manager)

# 扫描多个币种
signals = signal_generator.scan_symbols(
    symbols=['BTCUSDT', 'ETHUSDT'],
    data_feed=data_feed,
    risk_manager=risk_manager,
    min_confidence=0.6
)
```

---

### 3️⃣ 风控检查 (RiskManager)

**功能**:
- 止损止盈自动计算（基于 ATR 动态调整）
- 凯利公式仓位管理
- 实时风险预警
- 完整交易日志

**风控检查流程**:
```
交易前检查:
1. 风险等级评估 → 2. 最大回撤检查 → 3. 持仓检查 → 4. 置信度检查
```

**仓位计算** (凯利公式):
```
f* = (p * b - q) / b

其中:
  p = 胜率
  q = 败率 = 1 - p
  b = 盈亏比 = 平均盈利 / 平均亏损

最终仓位 = f* / 除数 (默认 2，半凯利) × 置信度调整
```

**止损止盈计算**:
```python
# 基础止损止盈
stop_loss = entry_price × (1 - 0.05)    # 5% 止损
take_profit = entry_price × (1 + 0.15)  # 15% 止盈

# ATR 动态调整 (如果有 ATR 数据)
atr_stop_distance = 2 × ATR / entry_price
stop_loss_pct = max(0.05, atr_stop_distance)
take_profit_pct = max(0.15, stop_loss_pct × 2)  # 至少 2:1 盈亏比
```

**风险等级**:
| 等级 | 回撤范围 | 操作限制 |
|------|---------|---------|
| LOW | < 2.5% | 正常交易 |
| MEDIUM | 2.5% - 4% | 降低仓位 |
| HIGH | 4% - 5% | 谨慎交易 |
| CRITICAL | ≥ 5% | 停止交易 + 告警 |

**关键方法**:
```python
# 执行买入
trade = risk_manager.execute_buy(
    symbol='BTCUSDT',
    price=50000,
    confidence=0.7,
    atr=1000,
    volatility=0.03
)

# 执行卖出
trade = risk_manager.execute_sell(
    symbol='BTCUSDT',
    price=55000
)

# 获取风险报告
report = risk_manager.get_risk_report()

# 保存交易日志
risk_manager.save_journal()
```

---

### 4️⃣ 订单执行模拟 (OrderExecutor)

**功能**:
- 订单提交与跟踪
- 模拟成交（基于最新价格）
- 佣金计算（默认 0.1%）
- 订单状态管理

**订单类型**:
- `MARKET`: 市价单（立即成交）
- `LIMIT`: 限价单（价格条件成交）
- `STOP_LOSS`: 止损单（触发止损价成交）
- `TAKE_PROFIT`: 止盈单（触发止盈价成交）

**订单状态**:
- `PENDING`: 待处理
- `SUBMITTED`: 已提交
- `PARTIALLY_FILLED`: 部分成交
- `FILLED`: 已成交
- `CANCELLED`: 已取消
- `REJECTED`: 已拒绝

**关键方法**:
```python
# 提交订单
order = order_executor.submit_order(signal, order_type=OrderType.MARKET)

# 模拟成交
order_executor.simulate_fill(order, current_price=50000)

# 取消订单
order_executor.cancel_order(order_id)

# 获取订单汇总
summary = order_executor.get_order_summary()
```

---

### 5️⃣ 日志记录 (TradingLogger)

**功能**:
- 信号日志（JSONL 格式）
- 订单日志（JSONL 格式）
- 执行日志（详细操作记录）
- 性能报告生成

**日志文件结构**:
```
logs/
├── live_trading_2026-03-03.log       # 系统运行日志
├── signals_2026-03-03.jsonl          # 信号日志
├── orders_2026-03-03.jsonl           # 订单日志
├── trade_journal_20260303_123456.json # 交易日志（完整）
└── trading_report_20260303_123456.json # 执行报告
```

**关键方法**:
```python
# 记录信号
trading_logger.log_signal(signal)

# 记录订单
trading_logger.log_order(order)

# 生成报告
report = trading_logger.generate_report(period_hours=24)

# 保存报告
report_path = trading_logger.save_report()
```

---

## 🔧 配置选项

### 系统配置

```python
system = LiveTradingSystem(
    # 监控币种列表
    symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT'],
    
    # 初始资金 (USDT)
    initial_capital=10000,
    
    # 时间周期 ('15m', '30m', '1h', '4h', '1d')
    timeframe='1h',
    
    # 最小信号置信度 (0-1)
    min_confidence=0.6,
    
    # 日志文件路径
    log_file='logs/live_trading.log'
)
```

### 风控配置 (config.py)

```python
# 在 config.py 中调整
POSITION_SIZE = 0.1      # 单笔仓位 (10%)
STOP_LOSS = 0.05         # 止损 (5%)
TAKE_PROFIT = 0.15       # 止盈 (15%)
INITIAL_CAPITAL = 10000  # 初始资金
```

### 高级风控配置

```python
risk_manager = RiskManager(
    initial_capital=10000,
    max_drawdown_threshold=0.05,      # 5% 最大回撤告警
    default_risk_per_trade=0.02,      # 每笔交易风险 2%
    kelly_max_fraction=0.25,          # 凯利公式最大仓位 25%
    kelly_divisor=2.0                 # 凯利除数（半凯利）
)
```

---

## 📊 系统状态监控

### 获取完整状态

```python
status = system.get_status()

# 系统状态
print(f"运行中：{status['system_state']['is_running']}")
print(f"总信号数：{status['system_state']['total_signals']}")
print(f"总订单数：{status['system_state']['total_orders']}")
print(f"当前净值：{status['risk_metrics']['capital']['total_value']:.2f}")
print(f"总收益率：{status['risk_metrics']['capital']['total_return_pct']:.2f}%")

# 风险指标
print(f"最大回撤：{status['risk_metrics']['metrics']['max_drawdown']:.2%}")
print(f"胜率：{status['risk_metrics']['metrics']['win_rate']:.2%}")
print(f"盈亏比：{status['risk_metrics']['metrics']['profit_factor']:.2f}")
print(f"夏普比率：{status['risk_metrics']['metrics']['sharpe_ratio']:.2f}")

# 订单汇总
print(f"已成交订单：{status['order_summary']['filled_orders']}")
print(f"待处理订单：{status['order_summary']['pending_orders']}")
print(f"总佣金：{status['order_summary']['total_commission']:.4f}")
```

### 风险报告

```python
risk_report = risk_manager.get_risk_report()

# 关键指标
current_equity = risk_report['capital']['current']
total_return = risk_report['capital']['total_return_pct']
max_drawdown = risk_report['metrics']['max_drawdown']
win_rate = risk_report['metrics']['win_rate']
profit_factor = risk_report['metrics']['profit_factor']
```

---

## 🧪 测试与调试

### 单元测试

```python
# 测试数据接入
from live_trading_system import RealtimeDataFeed
from logging import getLogger

logger = getLogger('test')
data_feed = RealtimeDataFeed(logger)
df = data_feed.get_latest_data('BTCUSDT', '1h')
print(f"数据行数：{len(df)}")
print(f"最新价格：{df['close'].iloc[-1]}")

# 测试信号生成
from live_trading_system import SignalGenerator

signal_gen = SignalGenerator(logger)
signal = signal_gen.generate_signal('BTCUSDT', df, risk_manager)
if signal:
    print(f"信号：{signal.signal_type.value}")
    print(f"置信度：{signal.confidence:.2%}")
    print(f"理由：{signal.reasons}")

# 测试订单执行
from live_trading_system import OrderExecutor, OrderType

executor = OrderExecutor(logger)
order = executor.submit_order(signal, OrderType.MARKET)
executor.simulate_fill(order, current_price=signal.price)
print(f"订单状态：{order.status.value}")
print(f"成交价：{order.filled_price}")
```

### 日志级别调整

```python
import logging

# 设置为 DEBUG 级别查看详细信息
logging.getLogger('LiveTradingSystem').setLevel(logging.DEBUG)

# 设置为 WARNING 级别仅查看警告和错误
logging.getLogger('LiveTradingSystem').setLevel(logging.WARNING)
```

---

## 🚨 常见问题

### 1. 没有信号生成

**原因**: 模型未训练或置信度阈值过高

**解决方案**:
```bash
# 1. 先训练模型
cd ~/.openclaw/workspace/quant && python3 trading_model.py

# 2. 降低置信度阈值
system = LiveTradingSystem(min_confidence=0.55)

# 3. 检查数据是否充足
df = data_feed.get_latest_data('BTCUSDT', '1h')
print(f"数据行数：{len(df)}")  # 至少需要 50 行
```

### 2. 风控检查未通过

**常见原因**:
- 风险等级过高（CRITICAL）
- 最大回撤超过阈值
- 已有持仓，无法开新仓
- 信号置信度不足

**解决方案**:
```python
# 查看具体原因
status = system.get_status()
print(status['risk_metrics']['metrics'])

# 调整风控参数
risk_manager = RiskManager(
    max_drawdown_threshold=0.10,  # 提高到 10%
    kelly_max_fraction=0.30       # 提高到 30%
)
```

### 3. 数据更新失败

**原因**: 网络连接问题或 Binance API 限制

**解决方案**:
```bash
# 检查网络连接
ping api.binance.com

# 手动更新数据
cd ~/.openclaw/workspace/quant && python3 data_collector.py

# 查看日志
tail -f logs/live_trading.log
```

---

## 📈 性能优化建议

### 1. 数据缓存

```python
# 启用数据缓存（默认已启用）
data_feed.update_interval = 60  # 60 秒内不重复获取
```

### 2. 并行扫描

```python
# 使用多线程扫描多个币种（未来版本）
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    signals = list(executor.map(process_symbol, symbols))
```

### 3. 日志轮转

```python
# 定期清理旧日志（建议添加到 cron）
find logs/ -name "*.log" -mtime +30 -delete
find logs/ -name "*.jsonl" -mtime +30 -delete
```

---

## 🔐 安全注意事项

⚠️ **重要**: 本系统为**模拟交易系统**，不连接真实交易所 API

**生产环境部署建议**:

1. **API 密钥管理**
   - 使用环境变量存储 API 密钥
   - 不要将密钥硬编码到代码中
   - 限制 API 密钥权限（仅交易，不可提现）

2. **风险控制**
   - 设置严格的止损止盈
   - 限制单笔最大仓位
   - 设置每日最大亏损限额

3. **监控告警**
   - 配置异常交易告警
   - 监控系统运行状态
   - 定期检查日志

4. **备份恢复**
   - 定期备份交易日志
   - 保存系统配置
   - 测试恢复流程

---

## 📝 示例脚本

### 示例 1: 每日定时扫描

```python
#!/usr/bin/env python3
"""每日定时扫描脚本"""

from live_trading_system import LiveTradingSystem
from datetime import datetime

def daily_scan():
    """执行每日扫描"""
    print(f"🦞 开始每日扫描 | {datetime.now()}")
    
    system = LiveTradingSystem(
        symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
        min_confidence=0.65  # 提高置信度要求
    )
    
    signals = system.run_scan()
    
    # 生成报告
    status = system.get_status()
    print(f"\n📊 扫描完成 | 信号数：{len(signals)}")
    print(f"当前净值：{status['risk_metrics']['capital']['total_value']:.2f}")
    
    # 保存报告
    system.trading_logger.save_report()
    system.risk_manager.save_journal()

if __name__ == '__main__':
    daily_scan()
```

### 示例 2: 监控特定币种

```python
#!/usr/bin/env python3
"""ETH 专项监控"""

from live_trading_system import LiveTradingSystem

# 仅监控 ETH 及相关币种
system = LiveTradingSystem(
    symbols=['ETHUSDT', 'ETHBTC', 'UNIUSDT', 'LINKUSDT'],
    timeframe='30m',  # 更短周期
    min_confidence=0.6
)

# 连续运行 1 小时
system.run_continuous(
    scan_interval_seconds=60,  # 每分钟扫描
    max_iterations=60
)
```

### 示例 3: 保守策略

```python
#!/usr/bin/env python3
"""保守策略配置"""

from live_trading_system import LiveTradingSystem
from risk_management import RiskManager

# 创建系统
system = LiveTradingSystem(
    symbols=['BTCUSDT', 'ETHUSDT'],
    initial_capital=10000,
    min_confidence=0.7  # 高置信度要求
)

# 调整风控参数（更保守）
system.risk_manager = RiskManager(
    initial_capital=10000,
    max_drawdown_threshold=0.03,     # 3% 回撤告警
    default_risk_per_trade=0.01,     # 1% 风险
    kelly_max_fraction=0.15,         # 最大 15% 仓位
    kelly_divisor=3.0                # 1/3 凯利
)

# 运行
system.run_continuous(scan_interval_seconds=600)  # 10 分钟扫描
```

---

## 📚 相关文档

- [AGENTS.md](../AGENTS.md) - 量化项目指南
- [config.py](config.py) - 核心配置
- [risk_management.py](risk_management.py) - 风控模块详解
- [trading_model.py](trading_model.py) - 交易模型

---

## 🎯 下一步

1. **训练模型**: 运行 `python3 trading_model.py` 训练交易模型
2. **回测验证**: 使用 `adaptive_strategy_perp.py` 进行策略回测
3. **实盘模拟**: 运行本系统进行模拟交易
4. **性能优化**: 根据回测结果调整参数

---

_🦞 龙虾王量化 · 螯击长空！_
