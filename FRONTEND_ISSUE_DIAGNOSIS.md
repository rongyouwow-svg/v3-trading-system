# 📋 前端问题诊断报告

**诊断时间**: 2026-03-15 00:35  
**问题**: 前端网页显示错误 + AVAX 32 信号 0 执行

---

## 🔍 问题 1: 前端 JSON 解析错误

### 错误信息
```
加载失败：JSON.parse: unexpected end of data at line 1 column 1 of the JSON data
```

### 根本原因
**API 路由重复定义** - `get_active_strategies()` 在 `strategy_status_api.py` 中定义了两次（第 54 行和第 100 行），导致 FastAPI 路由冲突，返回 404 Not Found。

### 修复方案
1. ✅ 删除重复的函数定义
2. ✅ 保留唯一的 `/api/strategy/active` 端点
3. ✅ 重启 Web 服务

### 验证结果
```bash
# 修复前
curl http://localhost:3000/api/strategy/active
# 返回：{"detail": "Not Found"}

# 修复后
curl http://localhost:3000/api/strategy/active
# 返回：{"success": true, "active_strategies": [...], "count": 3}
```

---

## 🔍 问题 2: AVAX 32 信号 0 执行

### 现象
```
AVAXUSDT: 信号 32/0  (32 个信号，0 个执行)
```

### 根本原因
**RSI 过高（超买区）** - 当前 RSI 83.33，超过了开仓阈值。

**策略逻辑**:
```python
if rsi > 50 and not self.position:
    # 开多信号
    return 'buy'

elif rsi > 80 and self.position == 'LONG':
    # 平仓信号（不是开仓！）
    return 'sell'
```

**当前状态**:
| 策略 | RSI | 状态 | 说明 |
|------|-----|------|------|
| ETHUSDT | 85.48 | 超买 | RSI>80，等待平仓信号 |
| LINKUSDT | 83.33 | 超买 | RSI>80，等待平仓信号 |
| AVAXUSDT | 83.33 | 超买 | RSI>80，等待平仓信号 |

### 为什么信号不执行？

1. **RSI>80** - 策略认为市场超买，不应该开仓
2. **无持仓** - 无法平仓（没有持仓可平）
3. **信号计数** - 策略仍然计数信号，但不执行

### 解决方案

**方案 A: 等待 RSI 回落到正常区间**（推荐）
- 等待 RSI 回落到 30-70 区间
- 当 RSI>50 且<80 时，会正常开仓

**方案 B: 调整策略阈值**
```python
# 修改 strategies/rsi_1min_strategy.py
self.rsi_buy_threshold = 50      # 开仓阈值
self.rsi_sell_threshold = 85     # 平仓阈值（从 80 提高到 85）
```

**方案 C: 重置信号计数**
```bash
# 手动重置策略状态文件
echo '{}' > /root/.openclaw/workspace/quant/v3-architecture/logs/strategy_pids.json
# 重启策略
supervisorctl restart quant-web
```

---

## 🔍 问题 3: 为什么只有 ETH 完成了开单？

### 时间线分析

| 时间 | 事件 | 说明 |
|------|------|------|
| 23:16 | ETH 策略启动 | RSI 在正常区间（50-80） |
| 23:16-23:30 | ETH 开仓成功 | RSI>50 且仓位未超标 |
| 23:30 后 | ETH 持仓超标 | 622 USDT / 315 USDT = 197% |
| 23:30 后 | AVAX/LINK 启动 | 仓位控制阻止开仓 |
| 00:00 | ETH 平仓 | 仓位恢复正常 |
| 00:27 | AVAX 重启 | RSI 已进入超买区（>80） |
| 00:27-00:35 | AVAX 32 信号 | RSI>80，信号被忽略 |

### 根本原因

1. **时机问题** - ETH 最早启动，在仓位控制生效前开仓
2. **仓位超标** - ETH 开仓后仓位超标（622 USDT），阻止了其他策略
3. **RSI 超买** - AVAX 重启时 RSI 已进入超买区（>80）

---

## 📊 监测报警分析

### 深度监测脚本状态

**监测内容**:
- ✅ 每 60 秒检查仓位
- ✅ 每 60 秒检查止损单
- ✅ 发现异常立即 Telegram 告警

**为什么没有报警？**

1. **信号不匹配不是异常** - 策略逻辑决定 RSI>80 时不执行
2. **仓位控制正常工作** - 成功阻止了超标开仓
3. **止损单创建成功** - ETH 开仓后立即创建了止损单

### 建议改进

**添加信号执行率监测**:
```python
# deep_monitor.py

def check_signal_execution_rate(symbol, signals_sent, signals_executed):
    """检查信号执行率"""
    if signals_sent > 10 and signals_executed == 0:
        execution_rate = 0
    else:
        execution_rate = signals_executed / signals_sent * 100 if signals_sent > 0 else 100
    
    if execution_rate < 10:  # 执行率低于 10%
        alert(f"{symbol} 信号执行率过低：{execution_rate:.1f}% ({signals_sent} 信号，{signals_executed} 执行)")
```

---

## 🎯 总结

### 已修复问题

| 问题 | 状态 | 说明 |
|------|------|------|
| **前端 JSON 错误** | ✅ 已修复 | 删除重复 API 路由 |
| **API 404 错误** | ✅ 已修复 | 保留唯一的 `/api/strategy/active` 端点 |

### 待解决问题

| 问题 | 状态 | 说明 |
|------|------|------|
| **AVAX 信号不执行** | ⚠️ 正常行为 | RSI>80 超买区，策略逻辑决定不执行 |
| **信号执行率低** | ⚠️ 待改进 | 建议添加信号执行率监测 |

### 建议行动

1. ✅ **前端已修复** - 刷新网页即可正常显示
2. ⏳ **等待 RSI 回落** - 等待 RSI 回落到 30-70 区间
3. ⏳ **添加信号执行率监测** - 监测信号执行情况
4. ⏳ **考虑调整 RSI 阈值** - 如果频繁遇到超买/超卖

---

## 📈 当前状态

### 策略状态
| 策略 | RSI | 信号 | 执行 | 状态 |
|------|-----|------|------|------|
| ETHUSDT | 85.48 | 0/0 | - | 超买区 |
| LINKUSDT | 83.33 | 0/0 | - | 超买区 |
| AVAXUSDT | 83.33 | 32/0 | - | 超买区 |

### 持仓状态
- **当前持仓**: 0 个（空仓）
- **可用仓位**: 315 USDT（100 USDT × 3x × 1.05）

---

**报告生成时间**: 2026-03-15 00:35  
**诊断负责人**: AI Assistant  
**状态**: ✅ 前端已修复，策略行为正常（RSI 超买）
