# 🦞 实盘仪表板修复总结

## 问题诊断

### 问题 1：资产显示固定值 $1000
**原因：** 前端代码期望 `data.account.total`，但 API 返回 `data.account.balances[0].total`

**修复：**
```javascript
// 修复前
const total = data.account.total || 0;

// 修复后
const usdt = data.account.balances.find(b => b.asset === 'USDT');
const total = usdt ? usdt.total : 0;
```

### 问题 2：持仓和策略一直在"转圈"
**原因：** 
1. 使用 `resp.text()` + `JSON.parse()` 容易出错
2. 没有正确处理空数据和错误消息
3. 策略的 `side` 字段大小写不匹配（API 返回 `SHORT`，前端期望 `short`）

**修复：**
```javascript
// 修复前
const text = await resp.text(); 
let data; try { data = JSON.parse(text); } catch(e) { alert("检查失败"); };

// 修复后
const data = await resp.json();
// 添加 console.error 用于调试
```

## API 端点状态

| 端点 | 状态 | 说明 |
|------|------|------|
| `/api/real/account` | ✅ 正常 | 返回现货 + 合约余额 |
| `/api/real/positions` | ✅ 正常 | 返回持仓列表（需配置 API） |
| `/api/real/strategies` | ✅ 正常 | 返回活跃策略（4 个） |
| `/api/real/apis` | ✅ 正常 | API Key 管理 |
| `/api/real/strategy/close` | ✅ 正常 | 关闭策略 |

## 当前账户状态

**币安现货账户：**
- USDT: $1.00 (可用：$1.00)

**活跃策略（4 个）：**
1. ETHUSDT - v23 高频 - SHORT @ $1957.16
2. BTCUSDT - v23 高频 - SHORT @ $67482.30
3. UNIUSDT - v23 高频 - SHORT @ $3.734
4. LINKUSDT - v23 高频 - SHORT @ $8.644

## 访问地址

**实盘仪表板：**
```
http://147.139.213.181:8080/quant/dashboard_real.html
```

**币安 API 服务：**
```
http://147.139.213.181:5005
```

## 配置 API Key 步骤

1. 打开实盘仪表板
2. 左侧 "API 配置管理"
3. 输入 API Key 和 Secret Key
4. 点击 "添加 API"
5. 点击 "测试" 验证连接

## 修复文件

- `/home/admin/.openclaw/workspace/quant/dashboard_real.html` - 前端修复
- `/home/admin/.openclaw/workspace/quant/binance_data/real_trading_api.py` - 后端 API

## 测试命令

```bash
# 测试账户 API
curl http://localhost:5005/api/real/account

# 测试持仓 API
curl http://localhost:5005/api/real/positions

# 测试策略 API
curl http://localhost:5005/api/real/strategies

# 检查服务状态
ps aux | grep real_trading_api
```

---

*修复时间：2026-03-09 09:15*
*版本：v2.0*
