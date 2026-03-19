# 🎯 监控系统最终整改方案

**分析时间**: 2026-03-18 23:35  
**核心发现**: 现有 API 已经提供统一监控接口！

---

## 🔍 重大发现

### 策略已经有统一状态字段

所有 3 个策略都有：
```python
self.signals_sent      # 信号发送数
self.signals_executed  # 信号执行数
self.position          # 持仓状态
self.last_rsi          # 当前 RSI
```

### API 已经提供统一接口

```
GET /api/strategy/active
```

返回：
```json
{
  "active_strategies": [
    {
      "symbol": "ETHUSDT",
      "status": "running",
      "signals_sent": 0,
      "signals_executed": 0,
      "position": null,
      "rsi": 0
    },
    ...
  ]
}
```

---

## ✅ 监控共性（已实现）

### 策略层监控

| 指标 | 获取方式 | 告警条件 |
|------|----------|----------|
| 进程状态 | `status == "running"` | status != "running" |
| 信号产生 | `signals_sent > 0` | 10 分钟无增长 |
| 信号执行 | `signals_executed == signals_sent` | executed < sent |
| 策略活跃 | `rsi` 有值 | rsi == 0 (可能卡住) |

### 执行层监控

| 指标 | 获取方式 | 告警条件 |
|------|----------|----------|
| 开单执行 | 对比 signals_sent | sent 增长但无新持仓 |
| 止损设置 | /api/binance/stop-loss | 有持仓但无止损 |

### 结果层监控

| 指标 | 获取方式 | 告警条件 |
|------|----------|----------|
| 持仓盈亏 | /api/binance/positions | 亏损 > 阈值 |
| 账户余额 | /api/binance/account-info | 余额 < 阈值 |

---

## 🔧 监控脚本优化

### 当前问题

**错误做法**:
```bash
# 检查 API 是否响应（太表层）
curl http://localhost:3000/api/strategy/active | grep "success"
```

**正确做法**:
```bash
# 检查策略是否真正运行
python3 << 'PYEOF'
import requests
import json
from datetime import datetime

# 获取策略状态
response = requests.get('http://localhost:3000/api/strategy/active')
data = response.json()

last_state = {}  # 保存上次状态（用于对比）

for strategy in data.get('active_strategies', []):
    symbol = strategy['symbol']
    status = strategy['status']
    signals_sent = strategy.get('signals_sent', 0)
    signals_executed = strategy.get('signals_executed', 0)
    rsi = strategy.get('rsi', 0)
    
    # 检查 1: 进程状态
    if status != 'running':
        print(f"❌ {symbol}: 策略未运行")
        # send_alert()
    
    # 检查 2: 信号产生（对比上次）
    if symbol in last_state:
        if signals_sent == last_state[symbol]['signals_sent']:
            print(f"⚠️ {symbol}: 10 分钟无新信号")
            # send_alert()
    
    # 检查 3: 信号执行
    if signals_executed < signals_sent:
        print(f"⚠️ {symbol}: 有信号未执行 ({signals_sent}/{signals_executed})")
        # send_alert()
    
    # 检查 4: 策略活跃
    if rsi == 0 and status == 'running':
        print(f"⚠️ {symbol}: RSI=0，策略可能卡住")
        # send_alert()
    
    # 保存状态
    last_state[symbol] = {
        'signals_sent': signals_sent,
        'check_time': datetime.now()
    }

print("✅ 所有策略正常")
PYEOF
```

---

## 📋 立即实施方案

### 步骤 1: 保存监控状态（立即）

创建状态文件保存上次检查结果：
```bash
mkdir -p /root/.openclaw/workspace/quant/v3-architecture/monitor_state
```

### 步骤 2: 优化监控脚本（立即）

修改 `smart_monitor.sh`，添加策略深度检查

### 步骤 3: 添加状态对比（5 分钟）

实现信号增长检测

---

## 📊 监控指标完善

### 完整监控流程

```
每 10 分钟
  ↓
L1: API 健康检查
  ↓
L2: 策略状态检查
  ├─ 进程是否运行
  ├─ 信号是否产生（对比上次）
  ├─ 信号是否执行
  └─ 策略是否活跃
  ↓
L3: 业务结果检查
  ├─ 持仓盈亏
  ├─ 止损单状态
  └─ 账户余额
  ↓
发现异常 → 根源分析 → 自动修复 → 发送告警
```

---

**分析人**: 龙虾王 🦞  
**分析时间**: 2026-03-18 23:35  
**状态**: 立即实施
