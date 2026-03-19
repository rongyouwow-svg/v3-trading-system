# 🎯 V3 系统重新设计方案

**创建时间**: 2026-03-19 16:30  
**核心原则**: 简单、实用、能赚钱

---

## 🧠 深度理解

### V3 系统是什么？

**定义**: 自动量化交易系统

**核心功能**:
```
1. 获取行情数据
2. 计算策略信号
3. 自动开仓
4. 自动止损
5. 自动平仓
6. 记录交易
```

**工作流程**:
```
行情数据 → 策略计算 → 产生信号 → 执行交易 → 记录结果
   ↑                                        ↓
   └────────────── 循环执行 ─────────────────┘
```

---

### 监控系统的作用

**定位**: 为 V3 系统服务，不是主角

**核心职责**:
```
1. 检查 V3 是否在运行
2. 发现异常自动重启
3. 修复不了才告警
4. 记录故障供分析
```

**不应该做的**:
```
❌ 复杂的告警风暴
❌ 多层守护嵌套
❌ 为了监控而监控
```

---

## 🎯 核心问题识别

### 这一周暴露的问题

| 问题 | 根本原因 | 解决方案 |
|------|---------|---------|
| 策略进程挂掉 | 依赖缺失、代码 bug | 启动前检查依赖 + 代码测试 |
| 告警太多 | 无冷却、汇总机制 | 简化告警逻辑 |
| 配置丢失 | 无备份 | 自动备份配置 |
| 重复犯错 | 无记忆 | MEMORY.md 记录 |
| 系统复杂 | 过度设计 | 简化架构 |

---

## 📐 简化架构设计

### 新架构（极简版）

```
┌─────────────────────────────────────────────────┐
│              V3 核心系统                         │
│  ┌─────────────────────────────────────────┐   │
│  │  策略进程 (strategy_*.py)                │   │
│  │  - 获取行情                              │   │
│  │  - 计算信号                              │   │
│  │  - 执行交易                              │   │
│  │  - 设置止损                              │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
           ↑
┌─────────────────────────────────────────────────┐
│              简单监控                            │
│  ┌─────────────────────────────────────────┐   │
│  │  monitor.sh (简单脚本)                   │   │
│  │  - 每 60 秒检查进程                       │   │
│  │  - 挂了自动重启                          │   │
│  │  - 连续失败 3 次才告警                     │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
           ↑
┌─────────────────────────────────────────────────┐
│              Supervisor                         │
│  - 进程守护                                     │
│  - 自动重启                                     │
└─────────────────────────────────────────────────┘
```

---

## 🔧 核心组件

### 1. 策略进程（核心）

**要求**:
- ✅ 独立运行，不依赖外部
- ✅ 循环执行，永不退出
- ✅ 异常捕获，不崩溃
- ✅ 自动设置止损
- ✅ 记录交易日志

**标准模板**:
```python
#!/usr/bin/env python3
"""策略模板 - 所有策略必须遵循"""

import time
import requests
from datetime import datetime

class Strategy:
    def __init__(self, symbol, leverage, amount):
        self.symbol = symbol
        self.leverage = leverage
        self.amount = amount
        self.position = None
        self.stop_loss_id = None
        self.is_running = True
    
    def run(self, interval=60):
        """主循环 - 必须实现"""
        while self.is_running:
            try:
                # 1. 获取行情
                # 2. 计算信号
                # 3. 执行交易
                # 4. 设置止损
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[ERROR] {datetime.now()} {e}")
                time.sleep(10)  # 失败后等待

if __name__ == '__main__':
    strategy = Strategy('ETHUSDT', 3, 100)
    strategy.run()
```

---

### 2. 简单监控（服务核心）

**脚本**: `monitor.sh`

**功能**:
```bash
#!/bin/bash
# 极简监控脚本

# 每 60 秒检查
while true; do
    # 检查策略进程
    if ! pgrep -f "strategy_.*\.py" > /dev/null; then
        echo "策略挂了，重启..."
        # 重启 Supervisor
        supervisorctl restart all
    fi
    
    # 检查 Dashboard
    if ! curl -s http://localhost:3000/api/health > /dev/null; then
        echo "Dashboard 挂了，重启..."
        pkill -f uvicorn
        # 重启 Dashboard
    fi
    
    sleep 60
done
```

**告警规则**:
- ✅ 连续失败 3 次才告警
- ✅ 5 分钟冷却
- ✅ 汇总发送

---

### 3. Supervisor 配置（进程守护）

**配置**:
```ini
[program:quant-strategy-eth]
command=python3 -u strategies/eth_strategy.py
autostart=true
autorestart=true
startretries=3
startsecs=5
```

**原则**:
- ✅ 配置简单
- ✅ 自动重启
- ✅ 失败限制

---

## 📋 实施步骤

### 第 1 步：清理现有系统（1 小时）

```bash
# 1. 停止所有进程
systemctl --user stop strategy-guardian
pkill -9 -f strategy_guardian
pkill -9 -f auto_strategy_loader
pkill -9 -f monitor

# 2. 清理旧配置
rm -f supervisor/auto_strategies.conf
rm -f scripts/strategy_guardian*.sh

# 3. 保留核心
# - Supervisor 配置
# - 策略文件
# - Dashboard
```

---

### 第 2 步：验证策略能运行（2 小时）

**测试每个策略**:
```bash
# 1. 检查依赖
pip install requests python-binance

# 2. 手动测试策略
cd /root/.openclaw/workspace/quant/v3-architecture
python3 strategies/eth_strategy.py

# 3. 观察输出
# - 是否正常获取行情
# - 是否正常计算信号
# - 是否有异常

# 4. 修复 bug
# - 所有报错必须修复
# - 不能有未捕获异常
```

---

### 第 3 步：配置 Supervisor（1 小时）

**创建简单配置**:
```bash
# supervisor/strategies.conf
[program:quant-strategy-eth]
command=/root/.pyenv/versions/3.10.13/bin/python3 -u strategies/eth_strategy.py
directory=/root/.openclaw/workspace/quant/v3-architecture
autostart=true
autorestart=true
startretries=3
startsecs=5
stderr_logfile=logs/eth_err.log
stdout_logfile=logs/eth_out.log

[program:quant-strategy-link]
...

[program:quant-strategy-avax]
...
```

**启动**:
```bash
supervisord -c supervisor/supervisord.conf
supervisorctl status
```

---

### 第 4 步：创建简单监控（1 小时）

**脚本**: `monitor.sh`
```bash
#!/bin/bash
# 简单监控脚本

TELEGRAM_TOKEN="8784296779:AAFYFtE69lyvOFAAuRazuNbKZxG5mUtIQHk"
CHAT_ID="1233887750"
FAIL_COUNT=0

send_alert() {
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\":${CHAT_ID},\"text\":\"🚨 V3 告警\\n\\n$1\"}" > /dev/null
}

while true; do
    # 检查 Supervisor
    if ! pgrep -f supervisord > /dev/null; then
        echo "Supervisor 挂了"
        supervisord -c supervisor/supervisord.conf
        FAIL_COUNT=$((FAIL_COUNT+1))
    else
        FAIL_COUNT=0
    fi
    
    # 连续失败 3 次才告警
    if [ $FAIL_COUNT -ge 3 ]; then
        send_alert "Supervisor 连续失败 $FAIL_COUNT 次"
        FAIL_COUNT=0
        sleep 300  # 5 分钟冷却
    fi
    
    sleep 60
done
```

**启动**:
```bash
nohup bash monitor.sh > logs/monitor.log 2>&1 &
```

---

### 第 5 步：验证系统（1 小时）

**检查清单**:
```
□ 所有策略进程 RUNNING
□ Dashboard 可访问
□ 监控脚本运行中
□ 日志正常无 ERROR
□ 收到一次启动通知
```

**测试自动修复**:
```bash
# 1. 手动杀掉一个策略
pkill -f eth_strategy.py

# 2. 等待 60 秒

# 3. 检查是否自动重启
supervisorctl status

# 4. 应该看到策略重新 RUNNING
```

---

## ✅ 验收标准

### 功能验收

| 测试项 | 预期结果 | 实际结果 |
|--------|---------|---------|
| 策略启动 | 全部 RUNNING | ⬜ |
| 策略运行 | 正常获取行情 | ⬜ |
| 策略交易 | 信号→开单→止损 | ⬜ |
| 进程挂掉 | 60 秒内自动重启 | ⬜ |
| Dashboard | 可访问 | ⬜ |
| 告警通知 | 连续失败才发送 | ⬜ |

### 稳定性验收

| 指标 | 目标 | 实际 |
|------|------|------|
| 策略在线率 | > 99% | ⬜ |
| 故障恢复时间 | < 2 分钟 | ⬜ |
| 告警准确率 | > 90% | ⬜ |
| 误报率 | < 10% | ⬜ |

---

## 📊 与旧方案对比

| 方面 | 旧方案 | 新方案 |
|------|--------|--------|
| **复杂度** | 复杂（多层守护） | 简单（单层监控） |
| **配置文件** | 多个（热插拔等） | 1 个（Supervisor） |
| **监控脚本** | Guardian v2（复杂） | monitor.sh（简单） |
| **告警策略** | 汇总 + 冷却 | 连续失败才告警 |
| **代码量** | ~2000 行 | ~200 行 |
| **维护成本** | 高 | 低 |
| **可靠性** | 复杂易出错 | 简单可靠 |

---

## 🎯 核心原则

### 设计原则

1. **简单优先** - 能简单就不复杂
2. **核心优先** - 先保证交易，再考虑其他
3. **自动修复** - 能自动就不手动
4. **少告警** - 真有问题才告警
5. **易维护** - 一眼能看懂

### 不做的事情

```
❌ 热插拔系统（不需要频繁添加策略）
❌ 多层守护（一层就够了）
❌ 复杂告警（简单直接）
❌ 自动备份（手动备份即可）
❌ Web 管理（有 Dashboard 够了）
❌ 数据持久化（币安有记录）
```

---

## 📅 实施时间表

| 时间 | 任务 | 状态 |
|------|------|------|
| **今天** | 清理旧系统 + 验证策略 | ⬜ |
| **今天** | 配置 Supervisor | ⬜ |
| **今天** | 创建简单监控 | ⬜ |
| **今天** | 验证系统运行 | ⬜ |
| **明天** | 观察稳定性 | ⬜ |
| **明天** | 优化调整 | ⬜ |

---

## 🧠 记忆要点

### 必须记录到 MEMORY.md

```markdown
## V3 系统核心设计（2026-03-19 16:30）

**核心原则**: 简单、实用、能赚钱

**架构**:
- V3 策略进程（核心）
- Supervisor（进程守护）
- monitor.sh（简单监控）

**不做**:
- 热插拔
- 多层守护
- 复杂告警
- 自动备份

**监控规则**:
- 60 秒检查一次
- 连续失败 3 次才告警
- 5 分钟冷却
```

---

**新方案已设计完成，现在立即执行！** 🎯

**创建人**: 龙虾王 🦞  
**日期**: 2026-03-19 16:30
