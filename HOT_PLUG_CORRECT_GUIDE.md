# 🔌 策略热插拔正确指南

**版本**: v2.0 (修正版)  
**创建时间**: 2026-03-19 18:15  
**核心原则**: 无需重启 Supervisor！

---

## ❌ 错误理解

```
❌ 错误：添加策略需要重启 Supervisor
❌ 错误：热插拔加载器被删除了
❌ 错误：手动添加策略很复杂
```

---

## ✅ 正确理解

```
✅ 热插拔 = 无需重启 Supervisor
✅ 热插拔 = supervisorctl reread && update
✅ 热插拔 = 秒级生效
```

---

## 📋 两种热插拔方式

### 方式 1：手动热插拔（推荐）

**适用场景**: 偶尔添加/删除策略

**步骤**:

```bash
# 1. 编辑 Supervisor 配置
vi supervisor/quant-strategies.conf

# 2. 添加策略配置
[program:quant-strategy-new]
command=python3 -u strategies/new_strategy.py
directory=/root/.openclaw/workspace/quant/v3-architecture
autostart=true
autorestart=true
startretries=3
startsecs=5
stderr_logfile=logs/supervisor_new_err.log
stdout_logfile=logs/supervisor_new_out.log
environment=PYTHONPATH="/root/.openclaw/workspace/quant/v3-architecture"

# 3. 重新加载配置（无需重启！）
supervisorctl reread
supervisorctl update

# 4. 启动策略
supervisorctl start quant-strategy-new

# 5. 验证
supervisorctl status
```

**生效时间**: < 5 秒

---

### 方式 2：自动热插拔（待恢复）

**适用场景**: 频繁添加/删除策略

**原理**: 监控 `.active_strategies` 文件，自动调用 `reread && update`

**步骤**:

```bash
# 1. 编辑激活列表
vi .active_strategies

# 2. 添加策略名
new_strategy

# 3. 等待 60 秒自动生效
```

**状态**: ⏳ 脚本被删除，需要恢复

---

## 🆚 对比

| 方式 | 优点 | 缺点 | 推荐场景 |
|------|------|------|---------|
| **手动热插拔** | 简单、可靠、即时 | 需要手动操作 | 偶尔添加策略 |
| **自动热插拔** | 完全自动化 | 需要脚本支持 | 频繁添加策略 |

---

## 📝 示例：添加 ETH 突破策略

```bash
# 1. 编辑配置
cat >> supervisor/quant-strategies.conf << 'EOF'

[program:quant-strategy-eth-breakout]
command=python3 -u strategies/eth_breakout_strategy.py
directory=/root/.openclaw/workspace/quant/v3-architecture
autostart=true
autorestart=true
startretries=3
startsecs=5
stderr_logfile=logs/supervisor_eth_breakout_err.log
stdout_logfile=logs/supervisor_eth_breakout_out.log
environment=PYTHONPATH="/root/.openclaw/workspace/quant/v3-architecture"
EOF

# 2. 重新加载
supervisorctl reread
supervisorctl update

# 3. 验证
supervisorctl status | grep eth-breakout
```

**输出**:
```
quant-strategy-eth-breakout   RUNNING   pid 12345, uptime 0:00:10
```

---

## 🚨 常见错误

### 错误 1：重启 Supervisor

```bash
# ❌ 错误
pkill supervisord
supervisord -c supervisor/supervisord.conf

# ✅ 正确
supervisorctl reread
supervisorctl update
```

**后果**: 所有策略会短暂停止

---

### 错误 2：配置后不重新加载

```bash
# ❌ 错误
# 编辑配置后什么都不做

# ✅ 正确
supervisorctl reread
supervisorctl update
```

**后果**: 配置不生效

---

### 错误 3：使用绝对路径

```bash
# ❌ 错误
command=/root/.pyenv/versions/3.10.13/bin/python3 /root/.../strategy.py

# ✅ 正确
command=python3 -u strategies/strategy.py
directory=/root/.openclaw/workspace/quant/v3-architecture
```

**后果**: 路径错误，启动失败

---

## ✅ 热插拔验证

**验证步骤**:

```bash
# 1. 添加前状态
supervisorctl status

# 2. 添加配置
# 编辑 supervisor/quant-strategies.conf

# 3. 重新加载
supervisorctl reread
supervisorctl update

# 4. 验证新策略
supervisorctl status | grep new

# 5. 验证老策略未受影响
supervisorctl status | grep RUNNING
```

**预期结果**:
- 新策略显示为 RUNNING 或 STOPPED
- 老策略继续 RUNNING
- 无策略重启

---

## 🧠 核心教训

1. **热插拔不需要重启 Supervisor**
2. **使用 supervisorctl reread && update**
3. **自动热插拔脚本被删除了，需要恢复**
4. **手动热插拔更可靠，推荐**

---

**热插拔 = 无需重启！** 🔌✅
