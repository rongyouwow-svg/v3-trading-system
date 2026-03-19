# 🦞 币安量化交易系统 v2.0

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端层 (8080 端口)                       │
├─────────────────────────────────────────────────────────────┤
│  /quant/pages/real.html       → 实盘交易仪表板 (红色主题)    │
│  /quant/pages/sim.html        → 模拟交易仪表板 (绿色主题)    │
│  /quant/pages/api_config.html → API 配置管理 (紫色主题)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    API 服务层 (5005 端口)                      │
├─────────────────────────────────────────────────────────────┤
│  /api/real/*                → 币安实盘 API                    │
│  /api/sim/*                 → 模拟账户 API                    │
│  /api/config/*              → 配置管理 API                    │
│  /api/strategy/*            → 策略管理 API                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据层                                  │
├─────────────────────────────────────────────────────────────┤
│  币安官方 API               → 实盘数据                        │
│  /tmp/sim_state_v6.json     → 模拟账户数据                   │
│  /tmp/binance_api_keys.json → API Key 配置                   │
│  /tmp/strategies_v6.json    → 策略状态                       │
└─────────────────────────────────────────────────────────────┘
```

## 模块说明

### 后端模块 (`quant/api/`)

| 文件 | 说明 |
|------|------|
| `app.py` | Flask 主应用，整合所有路由 |
| `config.py` | 配置文件管理 |
| `binance_client.py` | 币安 API 客户端（现货 + 合约） |
| `sim_account.py` | 模拟账户模块 |

### 前端页面 (`quant/pages/`)

| 文件 | 说明 | 主题色 |
|------|------|--------|
| `real.html` | 实盘交易仪表板 | 🔴 红色 |
| `sim.html` | 模拟交易仪表板 | 🟢 绿色 |
| `api_config.html` | API 配置管理 | 🟣 紫色 |

## 快速启动

### 1. 启动 API 服务

```bash
cd /home/admin/.openclaw/workspace/quant
python3 -m api.app
```

服务将运行在 `http://localhost:5005`

### 2. 启动 HTTP 服务器

```bash
cd /home/admin/.openclaw/workspace
python3 -m http.server 8080
```

服务将运行在 `http://localhost:8080`

### 3. 访问页面

- **实盘交易：** `http://147.139.213.181:8080/quant/pages/real.html`
- **模拟交易：** `http://147.139.213.181:8080/quant/pages/sim.html`
- **API 配置：** `http://147.139.213.181:8080/quant/pages/api_config.html`

## API 端点

### 实盘 API (`/api/real/*`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/account` | GET | 获取账户余额（现货 + 合约） |
| `/positions` | GET | 获取合约持仓 |
| `/strategies` | GET | 获取活跃策略 |
| `/trade` | POST | 执行交易 |

### 模拟盘 API (`/api/sim/*`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/account` | GET | 获取模拟账户信息 |
| `/positions` | GET | 获取模拟持仓 |
| `/trade` | POST | 模拟开仓 |
| `/close` | POST | 模拟平仓 |
| `/reset` | POST | 重置账户 |

### 配置 API (`/api/config/*`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/apis` | GET | 获取 API Key 列表 |
| `/apis` | POST | 添加 API Key |
| `/apis/<index>` | DELETE | 删除 API Key |
| `/apis/<index>/activate` | POST | 激活 API Key |

### 策略 API (`/api/strategy/*`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/start` | POST | 启动策略 |
| `/stop` | POST | 停止策略 |

## 配置币安 API

### 1. 获取 API Key

1. 登录 [币安官网](https://www.binance.com)
2. 进入 **API 管理** 页面
3. 创建新的 API Key
4. 勾选权限：
   - ✅ 启用现货交易
   - ✅ 启用合约交易
   - ✅ 启用读取权限
5. **不要勾选提现权限！**

### 2. 添加到系统

1. 访问 API 配置页面
2. 输入名称、API Key、Secret Key
3. 点击"添加 API"
4. 点击"激活"启用

## 安全提示

⚠️ **重要安全注意事项：**

1. **不要分享 API Key 和 Secret Key**
2. **不要勾选提现权限**
3. **建议设置 IP 白名单**
4. **定期轮换 API Key**
5. **先用测试网测试**

## 故障排查

### API 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep 5005

# 查看日志
tail -f /tmp/api_v2.log
```

### 页面无法访问

```bash
# 检查 HTTP 服务器
ps aux | grep "http.server"

# 检查文件权限
ls -la /home/admin/.openclaw/workspace/quant/pages/
```

### API 返回错误

```bash
# 测试 API
curl http://localhost:5005/api/health

# 检查 API Key 配置
curl http://localhost:5005/api/config/apis
```

## 版本历史

### v2.0 (2026-03-09)
- ✅ 完整重构，模块化设计
- ✅ 实盘/模拟盘严格分离
- ✅ 统一 API 服务（5005 端口）
- ✅ 清晰的前端页面结构
- ✅ 完善的文档

### v1.0 (之前版本)
- ❌ 架构混乱
- ❌ 多个 API 服务冲突
- ❌ 页面缓存问题
- ❌ 代码重复

---

*文档版本：v2.0*
*更新时间：2026-03-09*
