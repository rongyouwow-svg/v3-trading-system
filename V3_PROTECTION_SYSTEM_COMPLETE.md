# 🛡️ V3 量化系统完整保障体系

**创建时间**: 2026-03-19 15:58  
**版本**: v2.0 (智能告警版本)  
**核心目标**: 策略 7x24 小时稳定运行 + 零告警疲劳

---

## 📋 保障体系架构

```
┌─────────────────────────────────────────────────────────┐
│                   L4: 用户通知层                         │
│  Telegram 告警（智能合并 + 冷却机制）                    │
│  - 告警冷却：5 分钟                                      │
│  - 重启冷却：5 分钟                                      │
│  - 汇总发送：避免单条轰炸                                │
└─────────────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────────────┐
│              L3: Strategy Guardian v2                   │
│  智能守护脚本（每 60 秒检查）                             │
│  - 自动发现异常                                          │
│  - 自动尝试修复                                          │
│  - 自动汇总告警                                          │
│  - Dashboard 健康监测                                    │
└─────────────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────────────┐
│                   L2: 健康检查层                         │
│  每小时全面健康检查                                      │
│  - Supervisor 状态                                       │
│  - 策略进程状态                                          │
│  - Dashboard 可用性                                      │
│  - API 连接测试                                          │
│  - 生成健康报告                                          │
└─────────────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────────────┐
│              L1: Supervisor 进程守护                     │
│  进程级自动重启                                          │
│  - autostart=true                                        │
│  - autorestart=true                                      │
│  - startretries=10                                       │
└─────────────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────────────┐
│              L0: systemd 基础守护                        │
│  保证 Guardian 本身持续运行                               │
│  - Restart=always                                        │
│  - 开机自启动                                            │
│  - 故障自动重启                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 核心组件

### 1. Strategy Guardian v2（智能守护）

**位置**: `/root/.openclaw/workspace/quant/v3-architecture/scripts/strategy_guardian_v2.sh`

**核心改进**:

| 功能 | v1 版本 | v2 版本 |
|------|--------|--------|
| 告警频率 | 每条都发 | 5 分钟冷却 |
| 告警方式 | 单条发送 | 汇总发送 |
| 重启频率 | 无限制 | 5 分钟冷却 |
| 启动通知 | ❌ | ✅ |
| Dashboard 监测 | ✅ | ✅ 增强 |

**检查频率**: 每 60 秒

**告警策略**:
```bash
# 告警冷却
- 相同类型告警 5 分钟内只发一次
- 避免告警风暴

# 重启冷却
- Supervisor 重启后 5 分钟内不重复重启
- 避免无限循环

# 汇总发送
- 收集所有异常后一次性发送
- 包含：异常策略 + 恢复策略
```

---

### 2. Health Check（健康检查）

**位置**: `/root/.openclaw/workspace/quant/v3-architecture/scripts/health_check.sh`

**检查项目**:
- ✅ Supervisor 状态
- ✅ 所有策略进程状态
- ✅ Dashboard HTTP 健康检查
- ✅ Guardian 进程检查
- ✅ Dashscope API 连接测试

**执行频率**: 每小时（Cron）

**报告发送**: Telegram 推送健康报告

---

### 3. Supervisor 配置

**位置**: `/root/.openclaw/workspace/quant/v3-architecture/supervisor/`

**守护进程**:
- `quant-strategy-eth` - ETH 策略
- `quant-strategy-link` - LINK 策略
- `quant-strategy-avax` - AVAX 策略
- `web_dashboard` - Dashboard（已禁用，手动启动）
- `quant-web` - 旧服务（已禁用）

**配置参数**:
```ini
autostart=true      # 自动启动
autorestart=true    # 自动重启
startretries=10     # 最多尝试 10 次
startsecs=5         # 运行 5 秒后算成功
stopwaitsecs=10     # 优雅停止等待 10 秒
```

---

### 4. systemd 服务

**服务名称**: `strategy-guardian.service`

**位置**: `/root/.config/systemd/user/strategy-guardian.service`

**配置**:
```ini
[Service]
Type=simple
ExecStart=/root/.openclaw/workspace/quant/v3-architecture/scripts/strategy_guardian_v2.sh
Restart=always
RestartSec=10
```

**管理命令**:
```bash
# 查看状态
systemctl --user status strategy-guardian.service

# 重启
systemctl --user restart strategy-guardian.service

# 日志
journalctl --user -u strategy-guardian.service -f
```

---

## 🚨 告警策略

### 告警类型

| 级别 | 图标 | 触发条件 | 冷却时间 |
|------|------|---------|----------|
| **启动通知** | 🛡️ | Guardian 启动 | 无（强制发送） |
| **恢复通知** | ✅ | 策略自动恢复 | 5 分钟 |
| **异常告警** | 🚨 | 策略无法恢复 | 5 分钟 |
| **Dashboard** | ⚠️ | Dashboard 异常 | 5 分钟 |

### 告警示例

**✅ 好的告警**（汇总 + 冷却）:
```
🛡️ 策略守护告警

🚨 策略异常

quant-strategy-eth (SUPERVISOR_DOWN)
quant-strategy-link (SUPERVISOR_DOWN)

⚠️ 已尝试自动重启，请检查日志
```

**❌ 坏的告警**（告警风暴）:
```
15:39 - 策略异常：eth
15:39 - 策略重启失败
15:40 - 策略异常：eth
15:40 - 策略重启失败
15:40 - 策略异常：link
15:40 - 策略重启失败
...（7 条/分钟）
```

---

## 📊 监测指标

### 实时指标（每 60 秒）
- 策略进程状态
- Supervisor 连接状态
- Dashboard 可用性

### 小时指标
- 健康检查报告
- API 连接成功率
- 告警次数统计

### 日志位置
| 日志 | 位置 | 用途 |
|------|------|------|
| Guardian 日志 | `logs/strategy_guardian.log` | 守护脚本运行记录 |
| Supervisor 日志 | `logs/supervisord.log` | Supervisor 事件 |
| 策略日志 | `logs/supervisor_*.log` | 各策略输出 |
| 健康报告 | `logs/health_check_*.md` | 每小时健康报告 |

---

## 🔧 运维手册

### 日常检查

```bash
# 1. 快速状态检查
/root/.openclaw/workspace/quant/v3-architecture/scripts/health_check.sh

# 2. 查看策略状态
/root/.pyenv/versions/3.10.13/bin/supervisorctl -s unix:///root/.openclaw/workspace/quant/v3-architecture/logs/supervisor.sock status

# 3. 查看 Guardian 状态
systemctl --user status strategy-guardian.service

# 4. 查看 Guardian 日志
tail -50 /root/.openclaw/workspace/quant/v3-architecture/logs/strategy_guardian.log

# 5. 查看 Dashboard
curl http://localhost:3000/api/health
```

### 故障处理流程

```
1. 收到告警
   ↓
2. 查看 Guardian 日志定位问题
   tail -100 logs/strategy_guardian.log
   ↓
3. 检查策略状态
   supervisorctl status
   ↓
4. 查看策略错误日志
   tail -100 logs/supervisor_eth_err.log
   ↓
5. 执行修复
   supervisorctl restart quant-strategy-eth
   ↓
6. 验证恢复
   supervisorctl status
   ↓
7. 记录故障原因
```

### 临时禁用告警

```bash
# 停止 Guardian
systemctl --user stop strategy-guardian.service

# 禁用 Guardian（开机不启动）
systemctl --user disable strategy-guardian.service

# 停止健康检查 Cron
crontab -r
```

### 修改告警配置

编辑 `scripts/strategy_guardian_v2.sh`:

```bash
# 修改告警冷却时间（秒）
ALERT_COOLDOWN=300  # 5 分钟

# 修改重启冷却时间（秒）
RESTART_COOLDOWN=300  # 5 分钟

# 修改检查频率（秒）
sleep 60  # 60 秒检查一次
```

---

## ✅ 当前状态

**更新时间**: 2026-03-19 15:58

| 组件 | 状态 | 说明 |
|------|------|------|
| **ETH 策略** | ✅ RUNNING | rsi_1min_strategy |
| **LINK 策略** | ✅ RUNNING | link_rsi_detailed_strategy |
| **AVAX 策略** | ✅ RUNNING | rsi_scale_in_strategy |
| **Guardian v2** | ✅ RUNNING | 智能告警版本 |
| **Dashboard** | ✅ OK | HTTP 200 |
| **健康检查** | ✅ 已配置 | 每小时执行 |

**访问地址**: http://47.83.115.23:3000/dashboard/

---

## 📝 历史故障与改进

### 2026-03-19 15:39 - 告警风暴事件

**问题**: 1 分钟内发送 7 条告警

**原因**:
1. 旧监控脚本未停止
2. Guardian v1 无告警冷却
3. 每个策略单独发告警
4. 没有汇总机制

**改进**:
1. ✅ 停止所有旧监控
2. ✅ 创建 Guardian v2（智能版）
3. ✅ 添加告警冷却（5 分钟）
4. ✅ 添加重启冷却（5 分钟）
5. ✅ 汇总发送告警

---

### 2026-03-19 15:35 - 策略进程全部挂掉

**问题**: 策略挂了 3 分钟无人发现

**原因**:
1. 旧监控停了
2. 新监控没建
3. 监测真空期

**改进**:
1. ✅ 建立三层防护体系
2. ✅ Guardian 自动守护
3. ✅ systemd 保证 Guardian 运行
4. ✅ 每小时健康检查

---

## 🎯 核心原则

### 监测原则
1. **主动发现** - 不等用户报告
2. **自动修复** - 能自动的绝不手动
3. **智能告警** - 零告警疲劳
4. **全面覆盖** - 无监测死角

### 运维原则
1. **第一次就做对** - 不依赖事后修复
2. **文档化** - 所有操作都有记录
3. **自动化** - 能脚本化的绝不手动
4. **持续改进** - 每次故障都要反思

---

## 📈 持续改进计划

### 短期（本周）
- [x] 告警冷却机制 ✅
- [x] 告警汇总发送 ✅
- [x] 停止旧监控 ✅
- [ ] 添加策略信号监测
- [ ] 添加持仓同步检查

### 中期（本月）
- [ ] 建立监测 Dashboard
- [ ] 添加历史数据分析
- [ ] 故障预测模型
- [ ] 完善运维文档

### 长期
- [ ] AI 驱动的异常预测
- [ ] 多服务器冗余
- [ ] 自动故障转移
- [ ] 完整可观测性体系

---

**保障体系已完善，策略运行有保障！** 🛡️

**创建人**: 龙虾王 🦞  
**版本**: v2.0  
**日期**: 2026-03-19 15:58
