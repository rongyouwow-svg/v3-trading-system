# 🦞 服务监控和故障告警指南

**创建时间**: 2026-03-18 20:00  
**状态**: ✅ 已部署

---

## 📋 监控范围

| 服务 | 监控 | 告警 | 自动重启 |
|------|------|------|----------|
| **Dashboard** | ✅ | ✅ | ✅ |
| **Deep Monitor** | ✅ | ✅ | ✅ |
| **Enhanced Monitor** | ✅ | ✅ | ✅ |
| **ETH 策略** | ✅ | ✅ | ✅ |
| **AVAX 策略** | ✅ | ✅ | ✅ |
| **UNI 策略** | ✅ | ✅ | ✅ |

---

## 🚨 故障告警

### 告警级别

| 级别 | 说明 | 通知方式 |
|------|------|----------|
| **INFO** | 服务启动/停止 | Telegram |
| **WARNING** | 服务异常，正在重启 | Telegram |
| **CRITICAL** | 服务故障，需手动干预 | Telegram |

### 告警场景

1. **服务停止** → WARNING → 自动重启
2. **重启失败** → CRITICAL → 手动检查
3. **Dashboard 故障** → CRITICAL → 自动重启 + 告警
4. **达到最大重启次数** → CRITICAL → 停止重启，手动检查

---

## 🔧 自动重启机制

### 配置参数

```python
CHECK_INTERVAL = 30  # 30 秒检查一次
MAX_RESTART_ATTEMPTS = 3  # 最大重启 3 次
RESTART_COOLDOWN = 300  # 冷却时间 5 分钟
```

### 重启流程

```
服务故障
  ↓
发送 Telegram 告警
  ↓
尝试重启
  ↓
检查重启结果
  ├─ 成功 → 继续监控
  └─ 失败 → 计数 +1
      ↓
      检查是否达到最大次数
      ├─ 未达到 → 等待冷却时间后重试
      └─ 已达到 → 停止重启，发送 CRITICAL 告警
```

---

## 📱 Telegram 告警示例

### 服务故障告警

```
🚨 服务故障告警

服务：quant-web
状态：FATAL
重启次数：1/3
正在自动重启...
```

### 重启失败告警

```
❌ 重启失败

服务：quant-strategy-eth
请手动检查！
```

### 达到最大重启次数

```
🚨 服务故障

服务：quant-deep-monitor
状态：BACKOFF
已达到最大重启次数 (3)，请手动检查！
```

---

## 🚀 启动服务监控

### 方法 1: Supervisor 启动

```bash
cd /root/.openclaw/workspace/quant/v3-architecture
/root/.pyenv/versions/3.10.13/bin/supervisorctl -c supervisor/supervisord.conf start service-monitor
```

### 方法 2: 直接运行

```bash
cd /root/.openclaw/workspace/quant/v3-architecture
/root/.pyenv/versions/3.10.13/bin/python3 supervisor/service_monitor.py
```

### 方法 3: 开机自启

已配置 Supervisor 自动启动：
- `autostart=true`
- `autorestart=true`

---

## 📊 监控日志

### 日志文件

| 日志 | 路径 |
|------|------|
| **监控日志** | `logs/service_monitor.log` |
| **监控输出** | `logs/service_monitor_out.log` |
| **监控错误** | `logs/service_monitor_err.log` |

### 查看日志

```bash
# 实时监控
tail -f /root/.openclaw/workspace/quant/v3-architecture/logs/service_monitor.log

# 查看错误
tail -50 /root/.openclaw/workspace/quant/v3-architecture/logs/service_monitor_err.log
```

---

## 🛠️ 手动干预

### 重启单个服务

```bash
/root/.pyenv/versions/3.10.13/bin/supervisorctl -c supervisor/supervisord.conf restart quant-web
```

### 重启所有服务

```bash
/root/.pyenv/versions/3.10.13/bin/supervisorctl -c supervisor/supervisord.conf restart all
```

### 查看服务状态

```bash
/root/.pyenv/versions/3.10.13/bin/supervisorctl -c supervisor/supervisord.conf status
```

---

## 📝 策略模板 V2（止损在策略内部）

### 核心特性

1. **止损在策略内部** - 策略自己管理止损单
2. **开仓立即创建止损** - 防止忘记设置止损
3. **跟车止损** - 价格上涨时自动上移止损
4. **平仓自动取消止损** - 防止止损单残留

### 使用示例

```python
from strategy_template_v2 import StrategyTemplateV2

class MyStrategy(StrategyTemplateV2):
    def check_entry_condition(self, indicators, current_price):
        # 实现入场逻辑
        return True
    
    def check_exit_condition(self, indicators, current_price):
        # 实现出场逻辑
        return True
    
    def calculate_indicators(self, klines):
        # 实现指标计算
        return {'rsi': 50}

# 运行策略
strategy = MyStrategy(
    symbol="ETHUSDT",
    leverage=3,
    amount=300,
    stop_loss_pct=0.05,
    trailing_stop_pct=0.02
)
strategy.run()
```

### 止损流程

```
开仓
  ↓
立即创建止损单
  ↓
价格监控
  ├─ 价格上涨 → 上移止损（跟车）
  ├─ 价格下跌 → 保持止损不变
  └─ 触及止损 → 自动平仓
  ↓
平仓
  ↓
取消止损单
```

---

## ⚠️ 注意事项

1. **Telegram Bot Token** - 确保配置正确
2. **检查间隔** - 不要太频繁（建议 30 秒）
3. **冷却时间** - 避免频繁重启（建议 5 分钟）
4. **最大重启次数** - 防止无限重启（建议 3 次）

---

**维护者**: 龙虾王 🦞  
**更新时间**: 2026-03-18 20:00
