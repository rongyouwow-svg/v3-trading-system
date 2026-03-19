# 🦞 大王量化系统恢复手册

**版本**: v3.1.0
**最后更新**: 2026-03-16 00:25
**适用系统**: V3 量化交易系统

---

## 📋 目录

1. [快速恢复](#快速恢复)
2. [服务器重启后恢复](#服务器重启后恢复)
3. [常见问题处理](#常见问题处理)
4. [系统检查清单](#系统检查清单)
5. [联系信息](#联系信息)

---

## 🚨 快速恢复

### 场景 1: 服务器重启后

```bash
# 1. 检查 Supervisor 是否运行
ps aux | grep supervisord | grep -v grep

# 2. 如果没有运行，启动 Supervisor
/root/.pyenv/versions/3.10.0/bin/supervisord -c /etc/supervisor/supervisord.conf

# 3. 检查所有服务状态
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf status

# 4. 验证 Web API
curl http://localhost:3000/api/health
```

**预期输出**:
```
✅ quant-web               RUNNING
✅ quant-strategy-eth      RUNNING
✅ quant-strategy-link     RUNNING
✅ quant-strategy-avax     RUNNING
✅ quant-deep-monitor      RUNNING
✅ quant-enhanced-monitor  RUNNING
```

### 场景 2: 策略进程崩溃

```bash
# 1. 查看策略状态
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf status

# 2. 重启单个策略
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf restart quant-strategy-eth

# 3. 重启所有策略
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf restart all

# 4. 查看日志
tail -f /root/.openclaw/workspace/quant/v3-architecture/logs/supervisor_eth_out.log
```

### 场景 3: Web 服务崩溃

```bash
# 1. 检查端口占用
netstat -tlnp | grep 3000

# 2. 停止旧进程
pkill -f "uvicorn web.dashboard_api:app"

# 3. 重启 Web 服务
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf restart quant-web

# 4. 验证
curl http://localhost:3000/api/health
```

---

## 🔧 服务器重启后恢复

### 完整恢复流程

#### Step 1: 检查自动启动状态

```bash
# 检查 Supervisor
ps aux | grep supervisord | grep -v grep

# 检查所有服务
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf status
```

#### Step 2: 如果 Supervisor 未运行

```bash
# 启动 Supervisor
/root/.pyenv/versions/3.10.0/bin/supervisord -c /etc/supervisor/supervisord.conf

# 验证启动
sleep 3
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf status
```

#### Step 3: 如果配置文件丢失

```bash
# 1. 创建系统目录
sudo mkdir -p /etc/supervisor/conf.d

# 2. 复制配置文件
cd /root/.openclaw/workspace/quant/v3-architecture
sudo cp supervisor/*.conf /etc/supervisor/conf.d/
sudo cp supervisor/supervisord.conf /etc/supervisor/supervisord.conf

# 3. 启动 Supervisor
/root/.pyenv/versions/3.10.0/bin/supervisord -c /etc/supervisor/supervisord.conf

# 4. 验证
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf status
```

#### Step 4: 验证系统功能

```bash
# Web API
curl http://localhost:3000/api/health

# 策略状态
curl http://localhost:3000/api/strategies/status

# 持仓状态
curl http://localhost:3000/api/positions

# 账户信息
curl http://localhost:3000/api/binance/account
```

---

## ⚠️ 常见问题处理

### 问题 1: 策略精度错误

**错误信息**:
```
❌ 开仓失败：{'success': False, 'error': 'Precision is over the maximum defined for this asset.', 'code': -1111}
```

**解决方案**:
```bash
# 检查策略文件中的精度处理
cat strategies/rsi_scale_in_strategy.py | grep -A 5 "quantity.*round"

# 修复 AVAX 精度 (整数)
# 修复 ETH 精度 (3 位小数)

# 重启策略
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf restart quant-strategy-avax
```

### 问题 2: Web 服务端口占用

**错误信息**:
```
ERROR: [Errno 98] error while attempting to bind on address ('0.0.0.0', 3000): address already in use
```

**解决方案**:
```bash
# 1. 查找占用端口的进程
lsof -i :3000

# 2. 停止旧进程
pkill -f "uvicorn web.dashboard_api:app"

# 3. 重启服务
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf restart quant-web
```

### 问题 3: 策略无法获取 K 线数据

**错误信息**:
```
❌ 获取 K 线失败：HTTPConnectionPool(host='localhost', port=3000): Connection refused
```

**解决方案**:
```bash
# 1. 检查 Web API 是否运行
curl http://localhost:3000/api/health

# 2. 如果 Web API 未运行，重启
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf restart quant-web

# 3. 等待 5 秒后重启策略
sleep 5
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf restart quant-strategy-eth
```

### 问题 4: Supervisor 配置未加载

**症状**: 服务状态显示 FATAL 或 BACKOFF

**解决方案**:
```bash
# 1. 检查配置文件
ls -la /etc/supervisor/conf.d/

# 2. 重新加载配置
sudo cp /root/.openclaw/workspace/quant/v3-architecture/supervisor/*.conf /etc/supervisor/conf.d/

# 3. 重启 Supervisor
pkill supervisord
sleep 2
/root/.pyenv/versions/3.10.0/bin/supervisord -c /etc/supervisor/supervisord.conf

# 4. 验证
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf status
```

---

## ✅ 系统检查清单

### 每日检查

- [ ] Web API 响应正常
- [ ] 所有策略进程运行中
- [ ] 监测进程运行中
- [ ] 日志无异常错误
- [ ] 持仓状态正常
- [ ] 止损单状态正常

### 每周检查

- [ ] 系统资源使用率 (CPU/内存/磁盘)
- [ ] 策略性能统计
- [ ] 日志文件大小 (是否需要清理)
- [ ] GitHub 备份是否最新
- [ ] 测试重启流程

### 每月检查

- [ ] 完整系统重启测试
- [ ] 备份恢复测试
- [ ] 策略参数优化
- [ ] 文档更新

---

## 📞 联系信息

### 系统信息

- **项目名称**: 大王量化交易系统 v3
- **GitHub**: https://github.com/rongyouwow-svg/lobster-quant-v3
- **部署位置**: 阿里云 ECS (147.139.213.181)
- **部署时间**: 2026-03-14

### 关键路径

| 类型 | 路径 |
|------|------|
| 项目根目录 | `/root/.openclaw/workspace/quant/v3-architecture` |
| 日志目录 | `/root/.openclaw/workspace/quant/v3-architecture/logs` |
| Supervisor 配置 | `/etc/supervisor/conf.d/` |
| 策略文件 | `strategies/*.py` |
| Web API | `web/dashboard_api.py` |

### 常用命令速查

```bash
# Supervisor 状态
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf status

# 重启单个服务
/root/.pyenv/versions/3.10.0/bin/supervisorctl -c /etc/supervisor/supervisord.conf restart <service-name>

# 查看日志
tail -f /root/.openclaw/workspace/quant/v3-architecture/logs/<log-file>.log

# 验证 API
curl http://localhost:3000/api/health
```

---

## 📚 相关文档

- [重启诊断报告](REBOOT_DIAGNOSIS_REPORT.md)
- [P0 任务完成报告](P0_TASKS_COMPLETE_REPORT.md)
- [阿里云 API 诊断](ALIYUN_API_DIAGNOSIS.md)
- [API 参考文档](API_REFERENCE_v3.1.md)

---

**手册版本**: v1.0
**最后更新**: 2026-03-16 00:25
**下次审查**: 2026-04-16
