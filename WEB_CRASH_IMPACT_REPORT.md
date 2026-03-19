# 🔍 Web 服务故障影响分析报告

**检查时间**: 2026-03-14 20:22  
**检查范围**: Web 服务/策略进程/交易系统

---

## 📊 影响分析

### 1. Web 服务 ❌

**状态**: **已恢复**

**影响**:
- ❌ 前端页面无法访问
- ❌ API 接口不可用
- ✅ **不影响后端策略运行**

**恢复时间**: <1 分钟

---

### 2. 策略进程 ⚠️

**状态**: **部分停止**

| 策略 | 状态 | 原因 |
|------|------|------|
| **ETH_RSI** | ❌ 停止 | 参数错误 (`stop_loss_pct`) |
| **LINK_RSI** | ❌ 停止 | 12:00 停止时间检查 |
| **AVAX_RSI_SCALE** | ❌ 停止 | 参数错误 (`stop_loss_pct`) |

**影响**:
- ❌ 策略不运行
- ❌ 无法检查开仓信号
- ❌ RSI 不更新

**恢复**: 需要修复参数后重启

---

### 3. 交易系统 ✅

**状态**: **正常**

**组件**:
- ✅ 执行引擎模块正常
- ✅ 止损管理器正常
- ✅ 持仓管理器正常
- ✅ 币安连接器正常

**影响**: **无影响**（只是策略未运行）

---

## 🔍 根本原因

### Web 服务崩溃

**原因**: 未知（需要查看日志）

**频率**: 今晚第 3 次（14:39, 18:16, 20:19）

**建议**: 配置 supervisor 自动重启

---

### 策略进程停止

**原因 1**: 参数错误

```python
# 错误代码
strategy = RSIStrategy(
    symbol='ETHUSDT',
    leverage=3,
    amount=100,
    stop_loss_pct=0.002  # ❌ 基类没有这个参数
)
```

**修复**:
```python
# 正确代码
strategy = RSIStrategy(
    symbol='ETHUSDT',
    leverage=3,
    amount=100
)
strategy.stop_loss_pct = 0.002  # 手动设置
```

---

**原因 2**: 停止时间检查

```python
# LINK 策略有停止时间检查
if datetime.now().hour >= 12:
    print("⏰ 到达停止时间：12:00")
    print("🛑 停止策略")
    break
```

**修复**: 移除或修改停止时间检查

---

## 📋 完整影响评估

| 组件 | 状态 | 影响 | 恢复时间 |
|------|------|------|---------|
| **Web Dashboard** | ✅ 已恢复 | 前端访问 | <1 分钟 |
| **API 接口** | ✅ 已恢复 | API 调用 | <1 分钟 |
| **ETH 策略** | ❌ 停止 | 无法开仓 | 需修复 |
| **LINK 策略** | ❌ 停止 | 无法开仓 | 需修复 |
| **AVAX 策略** | ❌ 停止 | 无法开仓 | 需修复 |
| **执行引擎** | ✅ 正常 | 无影响 | - |
| **止损管理** | ✅ 正常 | 无影响 | - |
| **持仓管理** | ✅ 正常 | 无影响 | - |

---

## 🛠️ 立即修复方案

### 修复 1: 策略参数错误

**修改文件**:
- `strategies/rsi_1min_strategy.py`
- `strategies/rsi_scale_in_strategy.py`

**修复内容**:
```python
# 删除 stop_loss_pct 参数
strategy = RSIStrategy(
    symbol='ETHUSDT',
    leverage=3,
    amount=100
    # 删除：stop_loss_pct=0.002
)

# 手动设置
strategy.stop_loss_pct = 0.002
```

---

### 修复 2: 停止时间检查

**修改文件**:
- `strategies/link_rsi_detailed_strategy.py`

**修复内容**:
```python
# 注释掉停止时间检查
# if datetime.now().hour >= 12:
#     print("⏰ 到达停止时间：12:00")
#     break
```

---

### 修复 3: 配置 supervisor

**创建配置文件**:
```ini
# /etc/supervisor/conf.d/quant-web.conf
[program:quant-web]
command=python3 -m uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000
directory=/root/.openclaw/workspace/quant/v3-architecture
autostart=true
autorestart=true
startretries=3
```

**效果**:
- ✅ Web 服务崩溃自动重启
- ✅ 系统重启自动启动
- ✅ 无需手动干预

---

## 🎯 结论

### Web 服务影响 ✅

- **影响**: 前端无法访问
- **后端**: **无影响**
- **恢复**: <1 分钟

### 策略进程影响 ❌

- **影响**: 策略停止运行
- **原因**: 参数错误 + 停止时间检查
- **恢复**: 需修复代码

### 交易系统状态 ✅

- **核心功能**: **正常**
- **模块**: 全部正常
- **影响**: **无**

---

## 📝 建议

### 立即执行

1. ⏳ 修复策略参数错误
2. ⏳ 移除停止时间检查
3. ⏳ 重启策略进程

### 短期执行

1. ⏳ 配置 supervisor 自动重启
2. ⏳ 添加策略健康检查
3. ⏳ 添加自动恢复脚本

### 长期执行

1. ⏳ 完善错误日志
2. ⏳ 添加监控告警
3. ⏳ 配置进程守护

---

**报告生成时间**: 2026-03-14 20:22  
**检查负责人**: AI Assistant  
**建议优先级**: P0（立即修复策略）
