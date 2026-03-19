# 🦞 大王量化系统 - 完整备份与恢复指南

**创建时间**: 2026-03-16 01:58
**系统版本**: V3.1

---

## 📂 核心文件位置

### 1. V3 交易系统 (主要)

**路径**: `/root/.openclaw/workspace/quant/v3-architecture/`
**大小**: 约 23 MB
**内容**:
```
v3-architecture/
├── strategies/           # 策略文件 (3 个)
│   ├── rsi_scale_in_strategy.py      (AVAX)
│   ├── rsi_1min_strategy.py          (ETH)
│   └── link_rsi_detailed_strategy.py (LINK)
├── web/                  # Web API
│   ├── binance_testnet_api.py
│   ├── dashboard_api.py
│   └── dashboard/        # 前端页面
├── core/                 # 核心模块
├── scripts/              # 脚本文件
│   ├── enhanced_monitor.py    # 监控脚本
│   ├── error_check_and_fix.sh # 2 小时检查脚本
│   └── telegram_alert.py      # Telegram 告警
├── supervisor/           # Supervisor 配置
├── logs/                 # 日志文件 (可选备份)
├── config/               # 配置文件
├── .env                  # ⭐ 环境变量 (API Key)
├── error_tracking.md     # 错误追踪
└── *.md                  # 文档报告 (50+ 个)
```

---

### 2. OpenClaw 工作区 (重要)

**路径**: `/root/.openclaw/workspace/`
**大小**: 约 1.2 GB
**核心文件**:
```
workspace/
├── SOUL.md                    # ⭐ 人格配置
├── USER.md                    # ⭐ 用户信息
├── IDENTITY.md                # ⭐ 身份定义
├── MEMORY.md                  # ⭐ 长期记忆
├── HEARTBEAT.md               # ⭐ 心跳记录
├── AGENTS.md                  # ⭐ 工作指南
├── TOOLS.md                   # 工具配置
├── quant/                     # 量化文件夹
│   ├── v3-architecture/       # ⭐ V3 系统
│   ├── history/               # 历史版本
│   ├── backtest/              # 回测数据
│   └── *.md                   # 策略文档
└── memory/                    # 记忆文件夹
    └── YYYY-MM-DD.md          # 每日记忆
```

---

### 3. 系统配置 (关键)

**路径**: `/etc/supervisor/conf.d/`
**内容**:
```
conf.d/
├── quant-web.conf              # Web 服务配置
├── quant-strategy-eth.conf     # ETH 策略配置
├── quant-strategy-link.conf    # LINK 策略配置
├── quant-strategy-avax.conf    # AVAX 策略配置
├── quant-deep-monitor.conf     # 深度监测配置
└── quant-enhanced-monitor.conf # 增强监测配置
```

**主配置**: `/etc/supervisor/supervisord.conf`

---

### 4. Cron 定时任务

**查看命令**: `crontab -l`
**内容**:
```bash
# 2 小时自动检查
0 */2 * * * /root/.openclaw/workspace/quant/v3-architecture/scripts/error_check_and_fix.sh

# 其他任务
30 14 14 3 * /root/.pyenv/versions/3.10.0/bin/python3 /root/.openclaw/workspace/quant/v3-architecture/scripts/generate_test_report.py
```

---

## 📦 备份方案

### 方案 A: 完整备份 (推荐) ⭐⭐⭐⭐⭐

**备份所有重要文件**:

```bash
# 1. 创建备份目录
mkdir -p /root/backup_quant_$(date +%Y%m%d_%H%M)
BACKUP_DIR="/root/backup_quant_$(date +%Y%m%d_%H%M)"

# 2. 备份 V3 系统
cp -r /root/.openclaw/workspace/quant/v3-architecture/ $BACKUP_DIR/v3-architecture/

# 3. 备份 OpenClaw 配置
cp /root/.openclaw/workspace/*.md $BACKUP_DIR/
cp -r /root/.openclaw/workspace/memory/ $BACKUP_DIR/memory/

# 4. 备份 Supervisor 配置
sudo cp /etc/supervisor/conf.d/*.conf $BACKUP_DIR/supervisor_configs/
sudo cp /etc/supervisor/supervisord.conf $BACKUP_DIR/

# 5. 备份 Cron 任务
crontab -l > $BACKUP_DIR/crontab_backup.txt

# 6. 备份环境变量
cp /root/.openclaw/workspace/quant/v3-architecture/.env $BACKUP_DIR/

# 7. 压缩备份
cd /root/
tar -czf backup_quant_$(date +%Y%m%d_%H%M).tar.gz backup_quant_$(date +%Y%m%d_%H%M)/

echo "✅ 备份完成：/root/backup_quant_$(date +%Y%m%d_%H%M).tar.gz"
```

**备份大小**: 约 50-100 MB (压缩后)

---

### 方案 B: Git 备份 (推荐) ⭐⭐⭐⭐⭐

**V3 系统已提交到 GitHub**:
- **仓库**: https://github.com/rongyouwow-svg/lobster-quant-v3
- **最新提交**: 已包含所有代码和文档

**操作**:
```bash
# 提交最新更改
cd /root/.openclaw/workspace/quant/v3-architecture/
git add -A
git commit -m "备份 before 系统重装"
git push origin main

echo "✅ Git 备份完成"
```

---

### 方案 C: 最小备份 (快速) ⭐⭐⭐

**只备份最关键文件**:

```bash
# 创建最小备份
mkdir -p /root/backup_minimal
cd /root/backup_minimal

# 1. 策略文件
cp /root/.openclaw/workspace/quant/v3-architecture/strategies/*.py ./

# 2. Web API
cp /root/.openclaw/workspace/quant/v3-architecture/web/*.py ./

# 3. 配置文件
cp /root/.openclaw/workspace/quant/v3-architecture/.env ./
cp /root/.openclaw/workspace/quant/v3-architecture/supervisor/*.conf ./

# 4. 脚本
cp /root/.openclaw/workspace/quant/v3-architecture/scripts/*.py ./
cp /root/.openclaw/workspace/quant/v3-architecture/scripts/*.sh ./

# 5. OpenClaw 配置
cp /root/.openclaw/workspace/SOUL.md ./
cp /root/.openclaw/workspace/USER.md ./
cp /root/.openclaw/workspace/MEMORY.md ./

echo "✅ 最小备份完成"
```

---

## 🔄 恢复步骤

### 重装系统后恢复

#### 第 1 步：安装基础环境

```bash
# 1. 安装 Python 3.10
curl https://pyenv.run | bash
pyenv install 3.10.0
pyenv global 3.10.0

# 2. 安装 Supervisor
pip3 install supervisor

# 3. 安装依赖
cd /root/.openclaw/workspace/quant/v3-architecture/
pip3 install -r requirements.txt  # 如果有的话
pip3 install requests fastapi uvicorn python-multipart
```

---

#### 第 2 步：恢复文件

```bash
# 1. 恢复 V3 系统
tar -xzf /root/backup_quant_*.tar.gz -C /root/
cp -r /root/backup_quant_*/v3-architecture/ /root/.openclaw/workspace/quant/

# 2. 恢复 OpenClaw 配置
cp /root/backup_quant_*.md /root/.openclaw/workspace/
cp -r /root/backup_quant_*/memory/ /root/.openclaw/workspace/

# 3. 恢复 Supervisor 配置
sudo cp /root/backup_quant_*/supervisor_configs/*.conf /etc/supervisor/conf.d/
sudo cp /root/backup_quant_*/supervisord.conf /etc/supervisor/

# 4. 恢复 Cron 任务
crontab /root/backup_quant_*/crontab_backup.txt
```

---

#### 第 3 步：启动服务

```bash
# 1. 启动 Supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor

# 2. 启动所有服务
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

# 3. 验证状态
sudo supervisorctl status
```

**预期输出**:
```
quant-web                        RUNNING
quant-strategy-eth               RUNNING
quant-strategy-link              RUNNING
quant-strategy-avax              RUNNING
quant-deep-monitor               RUNNING
quant-enhanced-monitor           RUNNING
```

---

#### 第 4 步：验证功能

```bash
# 1. 检查 Web API
curl http://localhost:3000/api/health

# 2. 检查持仓
curl http://localhost:3000/api/positions

# 3. 检查策略状态
curl http://localhost:3000/api/strategies/status

# 4. 运行监控脚本
bash /root/.openclaw/workspace/quant/v3-architecture/scripts/enhanced_monitor.py
```

---

## ⚠️ 重要提醒

### 必须备份的文件 ⭐⭐⭐⭐⭐

1. `.env` - API Key 和密钥
2. `strategies/*.py` - 3 个策略文件
3. `web/binance_testnet_api.py` - Web API
4. `scripts/enhanced_monitor.py` - 监控脚本
5. `supervisor/*.conf` - Supervisor 配置
6. `SOUL.md`, `USER.md`, `MEMORY.md` - OpenClaw 配置
7. `crontab_backup.txt` - 定时任务

---

### 可选备份的文件

- `logs/` - 日志文件 (占用空间大)
- `*.md` - 文档报告 (GitHub 已有)
- `data/` - 数据文件 (可重新生成)

---

### 重装后需要重新配置

1. **API Key** - 从 `.env` 恢复
2. **Telegram Bot** - 从配置文件恢复
3. **Cron 任务** - 从备份恢复
4. **Supervisor** - 从配置恢复

---

## 📋 快速检查清单

### 备份前检查
- [ ] 备份 V3 系统 (`v3-architecture/`)
- [ ] 备份 OpenClaw 配置 (`*.md`)
- [ ] 备份 Supervisor 配置 (`/etc/supervisor/`)
- [ ] 备份 Cron 任务 (`crontab -l`)
- [ ] 备份 `.env` 文件
- [ ] 提交到 GitHub

### 恢复后检查
- [ ] Python 3.10 已安装
- [ ] Supervisor 已安装
- [ ] 所有服务 RUNNING
- [ ] Web API 可访问 (端口 3000)
- [ ] 策略正常同步持仓
- [ ] 监控脚本正常运行
- [ ] Cron 任务已恢复

---

## 🎯 推荐方案

**最佳实践**:
1. **Git 备份** (代码和文档)
2. **完整备份** (配置和环境)
3. **双重保险** (本地 + GitHub)

**恢复时间**: 约 30 分钟

---

**备份命令 (一键执行)**:

```bash
# 完整备份脚本
mkdir -p /root/backup_$(date +%Y%m%d_%H%M)
BACKUP_DIR="/root/backup_$(date +%Y%m%d_%H%M)"
cp -r /root/.openclaw/workspace/quant/v3-architecture/ $BACKUP_DIR/
cp /root/.openclaw/workspace/*.md $BACKUP_DIR/
sudo cp /etc/supervisor/conf.d/*.conf $BACKUP_DIR/
crontab -l > $BACKUP_DIR/crontab.txt
cp /root/.openclaw/workspace/quant/v3-architecture/.env $BACKUP_DIR/
cd /root/ && tar -czf backup_$(date +%Y%m%d_%H%M).tar.gz backup_$(date +%Y%m%d_%H%M)/
echo "✅ 备份完成：/root/backup_$(date +%Y%m%d_%H%M).tar.gz"
```

---

**创建时间**: 2026-03-16 01:58
**版本**: v1.0
