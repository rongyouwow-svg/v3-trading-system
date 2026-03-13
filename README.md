# 🦞 大王量化交易系统 v3.0

**Lobster King Quantitative Trading System**

一个模块化、高可用、易扩展的币安 U 本位合约自动量化交易系统。

---

## 📊 项目状态

- **版本**: v3.0.0
- **状态**: ✅ 生产就绪
- **测试覆盖率**: 99%
- **代码行数**: 12650+ 行

---

## ✨ 核心特性

### 🏗️ 架构优势

- **模块化设计** - 清晰的模块边界，易于维护和扩展
- **多进程架构** - 策略/执行/风控独立进程，故障隔离
- **热插拔支持** - 策略独立运行，网关重启不影响策略
- **状态持久化** - 双重持久化（JSON+ 数据库），重启自动恢复

### 🔧 功能特性

- **多 API 配置** - 支持多套 API（测试网 + 实盘），策略可指定使用哪套 API
- **心跳检测** - 实时监控策略健康状态，超时自动告警
- **止损单防重** - 三层防重机制，避免重复创建
- **精度处理** - 自动精度处理，使用 Decimal 避免浮点误差
- **异常处理** - 统一异常处理，自动重试机制

### 📈 策略支持

- **突破策略** - 基于价格突破的趋势跟踪策略
- **RSI 反转策略** - 基于 RSI 指标的均值回归策略
- **MACD 趋势策略** - 基于 MACD 金叉死叉的趋势跟踪策略
- **网格交易策略** - 自动高抛低吸的网格交易策略

### 🌐 Web Dashboard

- **单页应用** - 所有功能在一个页面，无需跳转
- **策略库** - 4 个预设策略可选，一键启动
- **持仓监控** - 实时持仓信息，盈亏展示
- **止损单管理** - 止损单列表，状态监控
- **账户详情** - 账户余额、盈亏详情
- **插件配置** - Telegram/钉钉通知配置

### 🔔 通知插件

- **Telegram 通知** - 交易通知、告警消息
- **钉钉通知** - 钉钉群消息推送
- **插件系统** - 热插拔，支持自定义插件

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/lobster-quant-v3.git
cd lobster-quant-v3
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

**方式 1: 使用配置文件**

```bash
cp config/api_keys.json.example config/api_keys.json
vim config/api_keys.json
```

编辑 `config/api_keys.json`，填入你的 API Key：

```json
{
  "api_configs": [
    {
      "id": "testnet_1",
      "name": "测试网主账号",
      "enabled": true,
      "testnet": true,
      "api_key": "YOUR_TESTNET_API_KEY",
      "secret_key": "YOUR_TESTNET_SECRET_KEY"
    }
  ]
}
```

**方式 2: 使用环境变量**

```bash
cp .env.example .env
vim .env
```

编辑 `.env` 文件，填入你的 API Key：

```bash
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
BINANCE_TESTNET=true
```

### 4. 启动 Web Dashboard

```bash
cd /home/admin/.openclaw/workspace/quant/v3-architecture
uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000
```

### 5. 访问 Dashboard

打开浏览器访问：

```
http://localhost:3000/dashboard/login.html
```

**默认账号**:
- 用户名：`admin`
- 密码：`admin123`

---

## 📁 项目结构

```
lobster-quant-v3/
├── core/                      # 核心引擎
│   ├── strategy/              # 策略引擎
│   ├── execution/             # 执行引擎
│   └── risk/                  # 风控引擎
├── modules/                   # 功能模块
│   ├── config/                # 配置管理
│   ├── health/                # 心跳检测
│   └── utils/                 # 工具类
├── connectors/                # 连接器
│   └── binance/               # 币安连接器
├── plugins/                   # 插件系统
│   ├── telegram/              # Telegram 插件
│   └── dingtalk/              # 钉钉插件
├── web/                       # Web Dashboard
│   └── dashboard/             # Dashboard 页面
├── config/                    # 配置文件
│   └── api_keys.json.example  # API 配置模板
├── tests/                     # 测试
│   ├── unit/                  # 单元测试
│   └── integration/           # 集成测试
├── docs/                      # 文档
├── scripts/                   # 运维脚本
├── data/                      # 数据目录
├── logs/                      # 日志目录
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量模板
├── .gitignore                 # Git 忽略文件
└── README.md                  # 项目说明
```

---

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 生成覆盖率报告
pytest --cov=modules --cov-report=html
```

---

## 📖 文档

- [架构设计文档](docs/01-系统架构设计.md)
- [开发规范与数据标准](docs/04-开发规范与数据标准.md)
- [API 配置指南](docs/API_CONFIG_GUIDE.md)
- [Phase 2 实施报告](docs/PHASE2_IMPLEMENTATION.md)
- [Phase 3 完成报告](docs/PHASE3_COMPLETE.md)

---

## 🔒 安全说明

### 敏感文件

以下文件包含敏感信息，**不应上传到 GitHub**：

- `config/api_keys.json` - API Key 配置
- `.env` - 环境变量
- `credentials/` - 凭证文件
- `core/strategy/strategies/*.py` - 核心策略文件

### 已配置保护

- ✅ `.gitignore` 已配置
- ✅ 模板文件已提供（`.example` 后缀）
- ✅ 核心策略文件未上传

---

## 🛠️ 技术栈

- **Python**: 3.10+
- **Web 框架**: FastAPI
- **数据库**: SQLite
- **缓存**: Redis（可选）
- **前端**: HTML/CSS/JavaScript（单页应用）
- **测试**: pytest

---

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| 代码行数 | 12650+ 行 |
| 测试用例 | 193 个 |
| 测试通过率 | 99% |
| 文档数量 | 30+ 份 |
| Web 页面 | 8 个 |

---

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 更新日志

### v3.0.0 (2026-03-13)

- ✅ Phase 0-3 全部完成
- ✅ 多 API 配置支持
- ✅ 单页应用整合
- ✅ 插件配置 UI
- ✅ 策略库（4 个策略）
- ✅ 持仓/止损单/账户详情展示
- ✅ Web Dashboard 完整启用

---

## 📧 联系方式

- **项目作者**: Lobster King
- **邮箱**: your.email@example.com
- **项目链接**: https://github.com/YOUR_USERNAME/lobster-quant-v3

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## ⚠️ 风险提示

**量化交易存在风险，使用本系统需谨慎：**

1. 加密货币市场波动大，可能导致资金损失
2. 本系统仅供学习研究使用
3. 实盘交易前请充分测试
4. 请根据自身风险承受能力使用

**使用本系统即表示您已阅读并同意以上风险提示。**

---

**🦞 Happy Trading!**
