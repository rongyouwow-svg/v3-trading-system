# 🦞 币安实盘 API 配置指南

## 服务架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端页面 (8080 端口)                    │
│  - real_trading_dashboard.html (实盘)                     │
│  - sim_trading_dashboard.html (模拟盘)                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│              币安实盘 API 服务 (5005 端口)                  │
│  - /api/real/account → 币安现货 + 合约余额               │
│  - /api/real/positions → 币安合约持仓                    │
│  - /api/real/apis → API Key 管理                         │
│  - /api/real/trade → 交易执行                           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│                    币安 API                              │
│  - https://api.binance.com (现货)                        │
│  - https://fapi.binance.com (合约)                       │
└─────────────────────────────────────────────────────────┘
```

## 配置步骤

### 1. 获取币安 API Key

1. 登录 [币安官网](https://www.binance.com)
2. 进入 **API 管理** 页面
3. 创建新的 API Key
4. 勾选权限：
   - ✅ 启用现货交易
   - ✅ 启用合约交易
   - ✅ 启用读取权限
5. **重要：** 复制并保存 API Key 和 Secret Key（只显示一次！）

### 2. 添加 API Key 到系统

**方法 A：通过网页界面**
1. 访问 `http://147.139.213.181:8080/quant/real_trading_dashboard.html`
2. 点击"配置 API"按钮
3. 输入 API Key 和 Secret Key
4. 点击保存

**方法 B：直接创建配置文件**

创建 `/tmp/binance_apis.json`：
```json
{
  "apis": [
    {
      "name": "主账户",
      "api_key": "你的 API Key",
      "secret_key": "你的 Secret Key",
      "exchange": "binance"
    }
  ]
}
```

### 3. 测试 API 连接

```bash
# 测试 API 列表
curl http://147.139.213.181:5005/api/real/apis

# 测试账户信息（需要先配置 API）
curl http://147.139.213.181:5005/api/real/account

# 测试持仓
curl http://147.139.213.181:5005/api/real/positions
```

## API 端点

### 账户相关
- `GET /api/real/apis` - 获取 API Key 列表
- `POST /api/real/apis` - 添加 API Key
- `DELETE /api/real/apis/<index>` - 删除 API Key
- `GET /api/real/account` - 获取账户余额（现货 + 合约）

### 持仓相关
- `GET /api/real/positions` - 获取合约持仓
- `POST /api/real/orders/check` - 检查订单风险

### 交易相关
- `POST /api/real/order/market` - 市价单
- `POST /api/real/trade` - 开仓交易
- `GET /api/real/strategies` - 活跃策略

### 监控相关
- `GET /api/real/monitor` - 监控状态
- `GET /api/real/monitor/check` - 健康检查

## 访问地址

**实盘仪表板：**
```
http://147.139.213.181:8080/quant/real_trading_dashboard.html
```

**模拟盘仪表板：**
```
http://147.139.213.181:8080/quant/sim_trading_dashboard.html
```

## 服务状态检查

```bash
# 检查 HTTP 服务器（8080）
ps aux | grep "http.server 8080"

# 检查币安 API 服务（5005）
ps aux | grep "real_trading_api"

# 查看 API 服务日志
tail -f /tmp/real_trading_api.log
```

## 安全提示

⚠️ **重要安全注意事项：**

1. **不要分享 API Key 和 Secret Key**
2. **不要勾选提现权限**（我们只需要交易权限）
3. **建议设置 IP 白名单**（限制只能从服务器 IP 访问）
4. **定期轮换 API Key**
5. **使用测试网测试**（testnet.binance.com）

## 故障排查

### 问题：显示"请先配置 API"
**解决：** 需要先添加币安 API Key

### 问题：API 请求超时
**解决：** 检查网络连接，可能需要配置代理

### 问题：签名错误
**解决：** 检查系统时间是否准确（币安要求时间同步）

```bash
# 同步系统时间
sudo ntpdate pool.ntp.org
```

---

*最后更新：2026-03-09*
*服务版本：v1.0*
