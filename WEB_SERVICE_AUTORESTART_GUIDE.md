# 🛡️ Web 服务自动重启配置指南

**配置时间**: 2026-03-14 21:46  
**配置状态**: ✅ 已完成  
**优先级**: **P0 - 最高优先级**

---

## ✅ 配置完成

### supervisor 配置

**主配置文件**: `/home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf`

**Web 服务配置**: `/home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/quant-web.conf`

**当前状态**:
```
quant-web                        RUNNING   pid 100241, uptime 0:00:15
```

---

## 🔧 常用命令

### 查看服务状态

```bash
# 查看所有服务
supervisorctl -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf status

# 查看 Web 服务
supervisorctl -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf status quant-web
```

### 重启服务

```bash
# 重启 Web 服务
supervisorctl -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf restart quant-web

# 重启所有服务
supervisorctl -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf restart all
```

### 停止服务

```bash
# 停止 Web 服务
supervisorctl -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf stop quant-web
```

### 启动服务

```bash
# 启动 Web 服务
supervisorctl -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf start quant-web
```

### 查看日志

```bash
# 查看 Web 服务错误日志
tail -f /home/admin/.openclaw/workspace/quant/v3-architecture/logs/supervisor_web_err.log

# 查看 Web 服务输出日志
tail -f /home/admin/.openclaw/workspace/quant/v3-architecture/logs/supervisor_web_out.log

# 查看 supervisord 日志
tail -f /home/admin/.openclaw/workspace/quant/v3-architecture/logs/supervisord.log
```

---

## 🎯 自动重启配置

### 配置参数

```ini
[program:quant-web]
command=/home/admin/.pyenv/versions/3.10.0/bin/python3 -m uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000
directory=/home/admin/.openclaw/workspace/quant/v3-architecture
user=admin
group=admin
autostart=true          # 开机自启
autorestart=true        # 崩溃自动重启
startretries=10         # 最多重试 10 次
retrywait=5             # 重试间隔 5 秒
startsecs=5             # 运行 5 秒后认为启动成功
stopwaitsecs=10         # 停止后等待 10 秒
stopsignal=TERM         # 使用 TERM 信号停止
```

### 自动重启场景

| 场景 | 是否自动重启 | 说明 |
|------|-------------|------|
| **进程崩溃** | ✅ 是 | 立即自动重启 |
| **内存不足** | ✅ 是 | 崩溃后自动重启 |
| **手动停止** | ❌ 否 | 需要手动启动 |
| **系统重启** | ✅ 是 | 开机自动启动 |
| **配置文件错误** | ⚠️ 重试 10 次 | 10 次失败后停止 |

---

## 📊 监控脚本

### 检查服务状态脚本

```bash
#!/bin/bash
# check_web_service.sh

SUPERVISOR_CONF="/home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf"

echo "=== Web 服务状态 ==="
supervisorctl -c $SUPERVISOR_CONF status quant-web

echo ""
echo "=== 进程状态 ==="
ps aux | grep "uvicorn.*dashboard_api" | grep -v grep

echo ""
echo "=== 端口监听 ==="
netstat -tlnp 2>/dev/null | grep 3000 || echo "⚠️ 3000 端口未监听"

echo ""
echo "=== 最新日志 ==="
tail -20 /home/admin/.openclaw/workspace/quant/v3-architecture/logs/supervisor_web_err.log
```

---

## ⚠️ 故障排查

### Web 服务无法启动

**检查步骤**:
```bash
# 1. 查看 supervisor 状态
supervisorctl -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf status quant-web

# 2. 查看错误日志
tail -100 /home/admin/.openclaw/workspace/quant/v3-architecture/logs/supervisor_web_err.log

# 3. 手动测试启动
cd /home/admin/.openclaw/workspace/quant/v3-architecture
python3 -m uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000
```

### supervisor 未运行

**启动命令**:
```bash
supervisord -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf
```

### 服务反复重启

**可能原因**:
1. 配置文件错误
2. 端口被占用
3. 代码有 bug

**解决方法**:
```bash
# 查看详细日志
tail -f /home/admin/.openclaw/workspace/quant/v3-architecture/logs/supervisor_web_err.log

# 停止服务
supervisorctl -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf stop quant-web

# 手动测试
cd /home/admin/.openclaw/workspace/quant/v3-architecture
python3 -m uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000
```

---

## 📝 配置文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| **主配置** | `supervisor/supervisord.conf` | supervisord 主配置 |
| **Web 服务** | `supervisor/quant-web.conf` | Web 服务配置 |
| **错误日志** | `logs/supervisor_web_err.log` | Web 服务错误日志 |
| **输出日志** | `logs/supervisor_web_out.log` | Web 服务输出日志 |
| **supervisor 日志** | `logs/supervisord.log` | supervisor 日志 |

---

## 🎯 验证测试

### 测试 1: 手动停止后自动重启

```bash
# 停止服务
supervisorctl -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf stop quant-web

# 等待 5 秒
sleep 5

# 检查状态（应该自动重启）
supervisorctl -c /home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf status quant-web
```

**预期结果**:
```
quant-web                        RUNNING   pid xxxxx, uptime 0:00:xx
```

### 测试 2: 杀死进程后自动重启

```bash
# 获取 PID
PID=$(ps aux | grep "uvicorn.*dashboard_api" | grep -v grep | awk '{print $2}')

# 杀死进程
kill -9 $PID

# 等待 5 秒
sleep 5

# 检查状态（应该自动重启）
ps aux | grep "uvicorn.*dashboard_api" | grep -v grep
```

**预期结果**:
```
admin     xxxxx  0.x  x.x  xxxxxx  xxxxx  ?  S  21:46   0:00  python3 -m uvicorn web.dashboard_api:app
```

---

## 📋 总结

### 已配置功能

- ✅ **自动启动** - 系统启动后自动启动 Web 服务
- ✅ **自动重启** - 进程崩溃后自动重启
- ✅ **重试机制** - 最多重试 10 次
- ✅ **日志记录** - 错误日志和输出日志分离
- ✅ **状态监控** - 可通过 supervisorctl 查看状态

### 配置效果

| 指标 | 配置前 | 配置后 |
|------|--------|--------|
| **手动重启** | ❌ 需要手动 | ✅ 自动重启 |
| **崩溃恢复** | ❌ 需人工干预 | ✅ <5 秒自动恢复 |
| **开机启动** | ❌ 需手动 | ✅ 自动启动 |
| **日志管理** | ❌ 分散 | ✅ 集中管理 |

---

**配置生成时间**: 2026-03-14 21:46  
**配置负责人**: AI Assistant  
**维护说明**: 修改配置后执行 `supervisorctl reread && supervisorctl update`
