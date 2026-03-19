# V3 量化交易系统 - 总结文档

## 系统概述

智能量化交易系统，支持多策略、多币种自动交易，具备完整的监控和自愈能力。

## 核心功能 ✅

### 1. 智能监测系统
- 每 5 分钟自动检查
- 进程状态监控
- 持仓 - 止损单匹配检查
- 自动清理重复止损单
- Telegram 告警通知

### 2. 异常重启恢复
- 系统重启后自动恢复策略
- 检测交易所持仓
- 自动启动对应策略
- 同步止损单

### 3. 策略管理
- 动态策略数量（从 Supervisor 配置获取）
- 同币种策略切换检测
- 策略注册中心
- 策略生命周期管理

### 4. 交易功能
- 自动开仓
- 自动止损单创建
- 自动平仓
- 自动撤销止损单

## 测试结果 ✅

| 测试项 | 结果 | 说明 |
|--------|------|------|
| 循环测试 | 4/5 通过 | 开仓→平仓→撤单 |
| 平仓测试 | ✅ 通过 | ETH/AVAX测试通过 |
| 撤单测试 | ✅ 通过 | 止损单正常撤销 |
| 监控测试 | ✅ 通过 | 所有 API 正常 |

## 文件结构

```
v3-trading-system/
├── strategies/          # 策略文件
│   ├── rsi_1min_strategy.py
│   ├── link_rsi_detailed_strategy.py
│   └── rsi_scale_in_strategy.py
├── scripts/            # 脚本文件
│   ├── smart_monitor_v3.py      # 智能监控
│   ├── auto_recovery.py         # 自动恢复
│   └── strategy_registry.py     # 策略注册
├── supervisor/         # Supervisor 配置
│   ├── supervisord.conf
│   └── quant-strategies.conf
├── web/               # Dashboard
│   └── dashboard_api.py
├── strategy_registry.py    # 策略注册中心
├── README.md              # 说明文档
├── requirements.txt       # 依赖
├── .env.example          # 配置示例
└── .gitignore            # Git 忽略
```

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/yourusername/v3-trading-system.git
cd v3-trading-system
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入真实 API Key
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 启动系统
```bash
# 启动 Supervisor
supervisord -c supervisor/supervisord.conf

# 启动 Dashboard
python3 web/dashboard_api.py

# 启动监控
python3 scripts/smart_monitor_v3.py
```

## 安全注意事项 ⚠️

**不要提交到 Git**:
- `.env` 文件
- 真实 API Key
- 真实 Secret Key
- Telegram Token
- 任何密码/密钥

**使用示例文件**:
- `.env.example`
- `config.example.json`

## 监控告警

系统会自动监控并在以下情况发送 Telegram 告警：
- 进程数量异常
- 持仓 - 止损单不匹配
- 重复止损单
- 策略未注册

## 测试方法

### 循环测试
```bash
python3 scripts/v3_loop_test.py
```

### 监控测试
```bash
python3 scripts/smart_monitor_v3.py
```

## 常见问题

### Q: 策略不启动？
A: 检查 Supervisor 配置和日志

### Q: 止损单重复？
A: 监控系统会自动清理

### Q: 如何添加新策略？
A: 编辑 `supervisor/quant-strategies.conf` 并重启 Supervisor

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
