# 🛡️ 策略保障系统文档

**创建时间**: 2026-03-19 15:38  
**核心目标**: 保证策略 7x24 小时稳定运行

---

## 📋 保障机制层次

### 第一层：Supervisor 进程守护
**作用**: 自动重启崩溃的策略进程

**配置位置**:
- `/root/.openclaw/workspace/quant/v3-architecture/supervisor/quant-strategies.conf`

**管理命令**:
```bash
# 查看状态
/root/.pyenv/versions/3.10.13/bin/supervisorctl status

# 重启单个策略
/root/.pyenv/versions/3.10.13/bin/supervisorctl restart quant-strategy-eth

# 重启所有策略
/root/.pyenv/versions/3.10.13/bin/supervisorctl restart all

# 查看日志
tail -f /root/.openclaw/workspace/quant/v3-architecture/logs/supervisor_eth_err.log
```

**保护策略**:
- `quant-strategy-eth` - ETH 策略
- `quant-strategy-link` - LINK 策略
- `quant-strategy-avax` - AVAX 策略

---

### 第二层：Strategy Guardian 守护脚本
**作用**: 每 30 秒检查策略状态，异常时自动修复并告警

**脚本位置**: `/root/.openclaw/workspace/quant/v3-architecture/scripts/strategy_guardian.sh`

**功能**:
1. ✅ 每 30 秒检查所有策略进程状态
2. ✅ 发现异常立即尝试重启
3. ✅ 重启失败时重启 Supervisor
4. ✅ 发送 Telegram 告警通知
5. ✅ 记录详细日志
6. ✅ 监控 Dashboard 健康状态

**日志位置**: `/root/.openclaw/workspace/quant/v3-architecture/logs/strategy_guardian.log`

**告警内容**:
- 策略异常告警
- 策略重启成功通知
- 策略无法恢复告警（需要人工干预）
- Dashboard 异常告警

---

### 第三层：systemd 服务
**作用**: 保证 Guardian 脚本本身持续运行

**服务名称**: `strategy-guardian.service`

**管理命令**:
```bash
# 查看状态
systemctl --user status strategy-guardian.service

# 重启服务
systemctl --user restart strategy-guardian.service

# 查看日志
journalctl --user -u strategy-guardian.service -f

# 禁用服务
systemctl --user disable strategy-guardian.service
```

**自启动**: ✅ 已启用（服务器重启后自动运行）

---

## 🚨 故障处理流程

### 自动处理（Guardian 脚本）

```
策略异常 → 尝试重启 → 成功 → 发送恢复通知
                    ↓ 失败
            重启 Supervisor → 成功 → 发送恢复通知
                           ↓ 失败
                   发送人工干预告警
```

### 人工干预

**收到告警后**:
1. 查看 Guardian 日志了解故障原因
2. 查看策略错误日志定位问题
3. 修复代码或配置问题
4. 重启策略验证

**常用排查命令**:
```bash
# 1. 检查策略状态
supervisorctl status

# 2. 查看策略错误日志
tail -100 logs/supervisor_eth_err.log

# 3. 查看 Guardian 日志
tail -100 logs/strategy_guardian.log

# 4. 检查 Dashboard
curl http://localhost:3000/api/health

# 5. 检查进程
ps aux | grep -E "strategy|supervisor"
```

---

## 📊 监控指标

### 关键指标
- 策略进程状态（RUNNING/STOPPED/FATAL）
- Dashboard 健康状态
- 告警频率
- 自动恢复成功率

### 日志轮转
建议每周清理一次旧日志：
```bash
# 保留最近 7 天的日志
find /root/.openclaw/workspace/quant/v3-architecture/logs/ -name "*.log" -mtime +7 -delete
```

---

## 🔧 维护指南

### 添加新策略
1. 在 `supervisor/quant-strategies.conf` 添加配置
2. 重新加载 Supervisor: `supervisorctl reread && supervisorctl update`
3. Guardian 脚本会自动监控新策略

### 修改告警配置
编辑 `scripts/strategy_guardian.sh`:
- `TELEGRAM_TOKEN` - Bot Token
- `CHAT_ID` - 接收告警的 Chat ID
- `sleep 30` - 检查频率（秒）

### 临时禁用 Guardian
```bash
systemctl --user stop strategy-guardian.service
```

---

## 📝 历史故障记录

### 2026-03-19 15:35 - 策略进程全部挂掉
**原因**:
1. 缺少 `requests` 模块
2. AVAX 策略初始化顺序 bug

**修复**:
1. 安装 requests 模块
2. 修复 AVAX 策略代码
3. 重启 Supervisor

**改进**: 创建 Strategy Guardian 保障系统

---

## ✅ 当前状态（2026-03-19 15:42）

| 组件 | 状态 | 说明 |
|------|------|------|
| Supervisor | ✅ 运行中 | 守护策略进程 |
| ETH 策略 | ✅ RUNNING | rsi_1min_strategy |
| LINK 策略 | ✅ RUNNING | link_rsi_detailed_strategy |
| AVAX 策略 | ✅ RUNNING | rsi_scale_in_strategy |
| Guardian | ✅ 运行中 | 每 30 秒检查 |
| Dashboard | ✅ 运行中 | 端口 3000 |

**访问地址**: http://47.83.115.23:3000/dashboard/

---

**保障系统已就绪！策略 7x24 小时稳定运行！** 🛡️
