# 🎯 V3 系统完整运行流程分析

**分析时间**: 2026-03-18 23:45  
**核心问题**: 如何判断 V3 是否完整执行到位？

---

## 🔄 V3 系统完整运行流程

```
策略运行 (每 60 秒)
  ↓
获取 K 线数据
  ↓
计算 RSI 指标
  ↓
检查信号条件 (RSI>50 且确认)
  ↓
发送信号 (signals_sent++)
  ↓
调用 API 开单
  ↓
开单成功 → signals_executed++
  ↓
设置止损单
  ↓
监控持仓盈亏
  ↓
平仓信号 → 调用 API 平仓
  ↓
清理状态
```

---

## 📋 全面监控内容

### 1. 策略层监控

| 监控点 | 检查内容 | 如何检查 |
|--------|----------|----------|
| **策略运行** | 进程是否运行 | `ps aux | grep strategy` |
| **信号产生** | RSI 是否计算 | API: `rsi != 0` |
| **信号逻辑** | 是否符合策略 | API: `signal_type` |
| **信号计数** | signals_sent 增长 | 对比上次检查 |

### 2. 执行层监控

| 监控点 | 检查内容 | 如何检查 |
|--------|----------|----------|
| **开单执行** | 信号是否开单 | 对比 signals_sent vs 持仓 |
| **止损设置** | 开单后是否有止损 | API: `/api/binance/stop-loss` |
| **止损跟踪** | 止损是否正确 | 对比开仓价 vs 止损价 |
| **信号执行计数** | signals_executed 增长 | 对比上次检查 |

### 3. 持仓层监控

| 监控点 | 检查内容 | 如何检查 |
|--------|----------|----------|
| **持仓存在** | 是否有持仓 | API: `/api/binance/positions` |
| **持仓方向** | LONG/SHORT 是否正确 | position.side |
| **持仓数量** | 是否与策略一致 | position.size |
| **杠杆倍数** | 是否正确设置 | position.leverage |
| **开仓价格** | 是否与信号一致 | position.entry_price |
| **当前盈亏** | 盈亏是否正常 | position.unrealized_pnl |

### 4. 流程层监控

| 监控点 | 检查内容 | 如何检查 |
|--------|----------|----------|
| **信号→开单** | 有信号必有开单 | signals_sent > 0 → 有持仓 |
| **开单→止损** | 有持仓必有止损 | 有持仓 → stop-loss 存在 |
| **止损→平仓** | 止损触发必平仓 | 止损触发 → 持仓消失 |

---

## 🔍 当前问题识别

### 问题 1: 信号与开单不对应

**检查方法**:
```python
# 获取策略状态
strategy = get('/api/strategy/active')
signals_sent = strategy['signals_sent']

# 获取持仓
positions = get('/api/binance/positions')

# 对比
if signals_sent > 0 and len(positions) == 0:
    print("❌ 有信号无开单")
```

### 问题 2: 开单与止损不对应

**检查方法**:
```python
# 获取持仓
positions = get('/api/binance/positions')

# 获取止损单
stop_losses = get('/api/binance/stop-loss')

# 对比
for pos in positions:
    has_stop = any(sl['symbol'] == pos['symbol'] for sl in stop_losses)
    if not has_stop:
        print(f"❌ {pos['symbol']} 有持仓无止损")
```

### 问题 3: 杠杆和金额不正确

**检查方法**:
```python
# 获取策略配置
strategy_config = {
    'ETHUSDT': {'leverage': 3, 'amount': 300},
    'LINKUSDT': {'leverage': 3, 'amount': 100},
    'AVAXUSDT': {'leverage': 3, 'amount': 200}
}

# 获取实际持仓
positions = get('/api/binance/positions')

# 对比
for pos in positions:
    symbol = pos['symbol']
    expected_leverage = strategy_config[symbol]['leverage']
    expected_amount = strategy_config[symbol]['amount']
    
    if pos['leverage'] != expected_leverage:
        print(f"❌ {symbol} 杠杆错误：{pos['leverage']} != {expected_leverage}")
    
    # 计算实际仓位价值
    actual_value = pos['size'] * pos['entry_price']
    expected_value = expected_amount * expected_leverage
    
    if abs(actual_value - expected_value) > expected_value * 0.1:  # 10% 误差
        print(f"❌ {symbol} 仓位错误：{actual_value} != {expected_value}")
```

---

## 📊 全面监控方案

### 监控层级

```
L1: 进程健康
├─ 策略进程运行
├─ Dashboard API
└─ 币安 API 连接

L2: 策略执行
├─ 信号产生 (RSI 计算)
├─ 信号发送 (signals_sent)
└─ 信号执行 (signals_executed)

L3: 开单止损
├─ 开单执行 (有信号→有持仓)
├─ 止损设置 (有持仓→有止损)
└─ 杠杆金额 (是否正确)

L4: 持仓结果
├─ 持仓盈亏
├─ 止损触发
└─ 平仓执行
```

---

## 🔧 立即实施

### 步骤 1: 创建全面监控脚本

```bash
# v3_full_monitor.sh
# 监控 V3 完整流程
```

### 步骤 2: 添加流程对比

```python
# 对比信号 vs 开单 vs 持仓 vs 止损
```

### 步骤 3: 添加杠杆金额检查

```python
# 检查实际杠杆和金额是否与策略一致
```

---

**分析人**: 龙虾王 🦞  
**分析时间**: 2026-03-18 23:45  
**状态**: 立即实施全面监控
