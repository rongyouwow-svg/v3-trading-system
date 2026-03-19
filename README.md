# V3 量化交易系统

智能量化交易系统，支持多策略、多币种自动交易。

## 核心功能

- ✅ 智能监测系统（自动运行）
- ✅ 异常重启恢复（自动运行）
- ✅ 动态策略管理
- ✅ 策略注册中心
- ✅ 自动清理重复止损单
- ✅ 开仓 + 止损功能
- ✅ 平仓 + 撤单功能

## 系统架构

```
V3 策略进程 → Supervisor（守护）→ monitor.sh（监控）→ Dashboard（展示）
```

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入真实 API Key
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动系统

```bash
# 启动 Supervisor
supervisord -c supervisor/supervisord.conf

# 启动 Dashboard
python3 web/dashboard_api.py

# 启动监控
bash scripts/monitor.sh
```

## 目录结构

```
├── strategies/          # 策略文件
├── scripts/            # 脚本文件
├── supervisor/         # Supervisor 配置
├── web/               # Dashboard
├── logs/              # 日志文件
└── README.md          # 说明文档
```

## 监控功能

- 每 5 分钟自动检查
- 进程状态监控
- 持仓 - 止损单匹配检查
- 自动清理重复止损单
- Telegram 告警通知

## 注意事项

⚠️ **不要提交敏感信息到 Git！**

- API Key
- Secret Key
- Token
- 密码

使用 `.env.example` 作为配置模板。

## 测试

已通过的测试：
- ✅ 4/5 循环测试（开仓→平仓→撤单）
- ✅ 监控系统测试
- ✅ API 功能测试

## 许可证

MIT License
