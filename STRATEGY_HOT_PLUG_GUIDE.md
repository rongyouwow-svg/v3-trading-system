# 🔌 策略热插拔使用指南

**创建时间**: 2026-03-19 16:05  
**版本**: v1.0

---

## 📋 什么是热插拔？

**热插拔** = 添加/删除策略无需重启 Supervisor，系统自动识别并生效。

**传统方式**（❌ 已淘汰）:
```bash
# 修改 Supervisor 配置
vi supervisor/quant-strategies.conf

# 重启 Supervisor
supervisorctl restart all

# 问题：需要手动操作，容易出错
```

**热插拔方式**（✅ 推荐）:
```bash
# 编辑激活列表
vi .active_strategies

# 等待 60 秒自动生效
# 无需重启！
```

---

## 🚀 快速开始

### 添加新策略

**步骤 1**: 将策略文件放入 `strategies/` 目录
```bash
cp my_new_strategy.py strategies/
```

**步骤 2**: 编辑激活列表
```bash
vi /root/.openclaw/workspace/quant/v3-architecture/.active_strategies
```

**步骤 3**: 添加策略名（不含 .py）
```
# 现有策略
rsi_1min_strategy
link_rsi_detailed_strategy
rsi_scale_in_strategy

# 添加新策略
my_new_strategy
```

**步骤 4**: 等待 60 秒自动生效

**验证**:
```bash
# 查看 Supervisor 状态
supervisorctl status

# 应该看到新策略
quant-strategy-my_new_strategy    RUNNING
```

---

### 删除策略

**步骤 1**: 编辑激活列表
```bash
vi .active_strategies
```

**步骤 2**: 删除或注释掉策略名
```
# rsi_1min_strategy  (已删除)
link_rsi_detailed_strategy
rsi_scale_in_strategy
```

**步骤 3**: 等待 60 秒自动停止

**验证**:
```bash
supervisorctl status
# 策略应该显示 STOPPED
```

---

### 临时禁用策略

**方法 1**: 注释掉（推荐）
```bash
# rsi_1min_strategy  # 临时禁用
link_rsi_detailed_strategy
```

**方法 2**: Supervisor 手动停止
```bash
supervisorctl stop quant-strategy-rsi_1min_strategy
```

---

## 🛠️ 核心组件

### 1. 激活列表 (`.active_strategies`)

**位置**: `/root/.openclaw/workspace/quant/v3-architecture/.active_strategies`

**格式**:
```
# 注释行以 # 开头
# 每行一个策略名（不含 .py 扩展名）

strategy_name_1
strategy_name_2
strategy_name_3
```

**示例**:
```
# ETH 策略
rsi_1min_strategy

# LINK 策略
link_rsi_detailed_strategy

# AVAX 策略
rsi_scale_in_strategy
```

---

### 2. 自动加载器 (`auto_strategy_loader.py`)

**位置**: `scripts/auto_strategy_loader.py`

**功能**:
- ✅ 每 60 秒扫描 `strategies/` 目录
- ✅ 读取 `.active_strategies` 激活列表
- ✅ 自动生成 Supervisor 配置
- ✅ 自动调用 `supervisorctl reread && update`
- ✅ 记录详细日志

**日志位置**: `logs/auto_loader.log`

**手动触发**:
```bash
python3 scripts/auto_strategy_loader.py
```

**守护运行**:
```bash
# 已自动启动，无需手动操作
ps aux | grep auto_strategy_loader
```

---

### 3. 自动生成的 Supervisor 配置

**位置**: `supervisor/auto_strategies.conf`

**注意**: 
- ❌ **不要手动编辑** - 会被自动覆盖
- ✅ 由加载器自动生成
- ✅ 每次检查都会更新

---

## 📊 监控和维护

### 查看加载器状态

```bash
# 查看进程
ps aux | grep auto_strategy_loader

# 查看日志
tail -50 logs/auto_loader.log

# 查看激活的策略
cat .active_strategies
```

### 查看策略状态

```bash
# 所有策略状态
supervisorctl status

# 单个策略状态
supervisorctl status quant-strategy-rsi_1min_strategy

# 重启策略
supervisorctl restart quant-strategy-rsi_1min_strategy

# 停止策略
supervisorctl stop quant-strategy-rsi_1min_strategy
```

### 查看 Guardian 监控

```bash
# Guardian 日志
tail -50 logs/strategy_guardian.log

# Guardian 状态
systemctl --user status strategy-guardian.service
```

---

## 🔧 故障排查

### 问题 1: 新策略没有自动启动

**检查步骤**:
```bash
# 1. 检查是否在激活列表
cat .active_strategies | grep my_strategy

# 2. 检查策略文件是否存在
ls -la strategies/my_strategy.py

# 3. 检查加载器日志
tail -50 logs/auto_loader.log

# 4. 手动触发加载器
python3 scripts/auto_strategy_loader.py

# 5. 检查 Supervisor 配置
cat supervisor/auto_strategies.conf | grep my_strategy
```

**常见原因**:
- ❌ 策略名写错（注意大小写）
- ❌ 策略文件不存在
- ❌ 策略文件没有 Strategy 类
- ❌ 加载器未运行

---

### 问题 2: 策略停止后没有自动删除

**检查步骤**:
```bash
# 1. 确认已从激活列表删除
cat .active_strategies

# 2. 等待 60 秒

# 3. 检查 Supervisor 状态
supervisorctl status

# 4. 手动更新
supervisorctl reread
supervisorctl update
```

---

### 问题 3: 加载器不工作

**检查步骤**:
```bash
# 1. 检查进程
ps aux | grep auto_strategy_loader

# 2. 如果没有运行，手动启动
cd /root/.openclaw/workspace/quant/v3-architecture
nohup /root/.pyenv/versions/3.10.13/bin/python3 scripts/auto_strategy_loader.py > logs/auto_loader.log 2>&1 &

# 3. 查看错误日志
tail -100 logs/auto_loader.log
```

---

## 📝 最佳实践

### 1. 策略命名规范

**推荐**:
```
{币种}_{策略类型}_strategy.py
```

**示例**:
```
eth_bb_rsi_strategy.py
avax_breakout_strategy.py
link_rsi_detailed_strategy.py
```

---

### 2. 激活列表管理

**推荐格式**:
```
# 按币种分组
# ETH 策略
eth_bb_rsi_strategy
eth_rsi_1min_strategy

# LINK 策略
link_rsi_detailed_strategy

# AVAX 策略
rsi_scale_in_strategy
```

**注释说明**:
- 使用 `#` 添加注释
- 空行分隔不同组
- 保持列表整洁

---

### 3. 测试新策略

**步骤**:
```bash
# 1. 先临时添加到激活列表
vi .active_strategies

# 2. 等待自动启动
# 3. 观察日志
tail -f logs/supervisor_new_strategy_err.log

# 4. 确认正常后保留
# 5. 有问题立即删除
```

---

### 4. 批量管理

**同时启动多个策略**:
```bash
# 编辑激活列表
vi .active_strategies

# 添加多个策略
strategy_1
strategy_2
strategy_3

# 等待自动生效
```

**同时停止多个策略**:
```bash
# 注释掉或删除
# strategy_1
# strategy_2
# strategy_3

# 等待自动停止
```

---

## 🎯 核心优势

### vs 传统方式

| 功能 | 传统方式 | 热插拔方式 |
|------|---------|-----------|
| 添加策略 | 手动改配置 + 重启 | 编辑列表 + 等待 |
| 删除策略 | 手动改配置 + 重启 | 删除行 + 等待 |
| 临时禁用 | 手动停止 | 注释掉即可 |
| 出错风险 | 高（配置复杂） | 低（自动检查） |
| 学习成本 | 需要了解 Supervisor | 只需编辑文本 |

---

## 📚 相关文件

| 文件 | 位置 | 用途 |
|------|------|------|
| 激活列表 | `.active_strategies` | 控制哪些策略运行 |
| 加载器 | `scripts/auto_strategy_loader.py` | 自动检测变化 |
| 自动配置 | `supervisor/auto_strategies.conf` | Supervisor 配置 |
| 加载器日志 | `logs/auto_loader.log` | 查看加载器状态 |
| Guardian | `scripts/strategy_guardian_v2.sh` | 策略守护 |

---

## ✅ 当前配置

**激活的策略** (截至 2026-03-19 16:05):
```
rsi_1min_strategy      # ETH 策略
link_rsi_detailed_strategy  # LINK 策略
rsi_scale_in_strategy  # AVAX 策略
```

**访问地址**: http://47.83.115.23:3000/dashboard/

---

**热插拔系统已就绪，添加策略只需编辑一个文件！** 🔌

**创建人**: 龙虾王 🦞  
**日期**: 2026-03-19 16:05
