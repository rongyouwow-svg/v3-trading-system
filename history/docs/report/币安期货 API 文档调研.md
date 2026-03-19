# 🦞 币安期货 API 文档调研报告

**调研时间：** 2026-03-10 13:30  
**调研范围：** 币安 USDS 边际期货 API 文档  

---

## 📚 文档调研记录

### 1. 基础信息

**API 端点：**
- 实盘：`https://fapi.binance.com`
- 测试网：`https://demo-fapi.binance.com`

**测试网支持：**
- 大部分端点可用
- Websocket: `wss://fstream.binancefuture.com`

---

### 2. 订单类型支持

**ETHUSDT 支持的订单类型：**
```
- LIMIT
- MARKET
- STOP
- STOP_MARKET
- TAKE_PROFIT
- TAKE_PROFIT_MARKET
- TRAILING_STOP_MARKET
```

---

### 3. Algo Order API

**官方文档位置：**
- 原文档：`/apidocs/futures/en/#algo-order-post-fapi-v1-algoorder`
- 新文档：`/docs/derivatives/usds-margined-futures/trade/Algo-Order`

**问题：**
- 新文档网站返回 404
- 原文档重定向到新网站
- 无法获取完整 Algo Order API 文档

---

### 4. 测试结果汇总

#### 测试网 Algo Order API 测试

| 测试项 | 参数 | 结果 |
|-------|------|------|
| 不带 algotype | - | ❌ Mandatory parameter missing |
| algotype=STOP_LOSS | STOP_MARKET | ❌ Invalid algoType |
| algotype=TAKE_PROFIT | TAKE_PROFIT_MARKET | ❌ Invalid algoType |
| algotype=STOP | STOP_MARKET | ❌ Invalid algoType |
| algotype=1 | STOP_MARKET | ❌ Invalid algoType |
| algotype=2 | STOP_MARKET | ❌ Invalid algoType |

#### 错误代码

| 错误码 | 错误信息 | 含义 |
|-------|---------|------|
| -1102 | Mandatory parameter 'algotype' was not sent | 缺少 algotype 参数 |
| -4500 | Invalid algoType | algotype 值无效 |
| -4120 | Order type not supported for this endpoint | 端点不支持该订单类型 |

---

## 🔍 问题分析

### 问题 1：文档缺失
- 新文档网站 Algo Order 页面 404
- 无法获取官方参数说明

### 问题 2：测试网限制
- 测试网 Algo Order API 需要 algotype 参数
- 但任何 algotype 值都报错 "Invalid algoType"
- 测试网 Algo Order API 可能有 bug

### 问题 3：实盘 API 权限
- 测试网 API key 不能用于实盘
- 无法验证实盘 Algo Order API 是否可用

---

## 📋 已知信息

### STOP_MARKET 止损单（旧版 API）

**端点：** `POST /fapi/v1/order`

**参数：**
```json
{
  "symbol": "ETHUSDT",
  "side": "SELL",
  "type": "STOP_MARKET",
  "stopPrice": "1938.95",
  "quantity": "0.49",
  "reduceOnly": "true",
  "positionSide": "BOTH"
}
```

**状态：** ❌ 测试网返回 -4120 错误

### Algo Order API（新版）

**端点：** `POST /fapi/v1/algoOrder`

**已知必需参数：**
- `symbol`: 交易对
- `side`: BUY/SELL
- `type`: STOP_MARKET/TAKE_PROFIT_MARKET
- `stopPrice`: 触发价格
- `quantity`: 数量
- `reduceOnly`: true/false
- `algotype`: ???（未知正确值）

**状态：** ❌ algotype 参数值未知

---

## 🛠️ 解决方案

### 方案 A：等待文档修复

**优点：**
- 官方文档修复后就有正确答案

**缺点：**
- 等待时间未知
- 可能影响项目进度

### 方案 B：联系币安支持

**途径：**
- GitHub Issue: https://github.com/binance/binance-connector-python/issues
- 技术支持工单
- 社区论坛

**优点：**
- 可能获得官方答复

**缺点：**
- 响应时间不确定

### 方案 C：测试网继续测试

**方法：**
- 尝试更多 algotype 值
- 查看测试网公告
- 检查 API 更新日志

**优点：**
- 可能发现正确参数

**缺点：**
- 耗时且不一定成功

### 方案 D：实盘验证（推荐）

**方法：**
- 申请实盘 API key
- 小额测试 Algo Order API
- 验证实盘是否可用

**优点：**
- 直接验证实盘功能
- 不受测试网限制

**缺点：**
- 需要实盘资金
- 有风险

---

## 🎯 建议

### 短期（项目继续）
1. **接受测试网限制**
   - 测试网无止损单功能
   - 仅测试策略逻辑

2. **完成其他修复**
   - 持仓数量调查
   - 前端委托单显示

3. **记录问题**
   - 文档缺失
   - 测试网限制

### 中期（实盘准备）
1. **申请实盘 API key**
2. **测试实盘 Algo Order API**
3. **验证实盘止损功能**

### 长期（文档贡献）
1. **提交 GitHub Issue**
2. **反馈文档缺失问题**
3. **帮助社区完善文档**

---

## 📝 联系币安支持

### GitHub Issue 模板

```markdown
Title: [Futures Testnet] Algo Order API - Invalid algoType error

Description:
I'm trying to place a STOP_MARKET order using the Algo Order API on the futures testnet.

Endpoint: POST /fapi/v1/algoOrder

Parameters:
- symbol: ETHUSDT
- side: SELL
- type: STOP_MARKET
- stopPrice: 1938.95
- quantity: 0.001
- reduceOnly: true
- algotype: STOP_LOSS (also tried: TAKE_PROFIT, STOP, etc.)

Error Response:
{
  "code": -4500,
  "msg": "Invalid algoType."
}

Question:
What is the correct value for the 'algotype' parameter?
The documentation appears to be missing or inaccessible (404 error).

Environment:
- Testnet: https://testnet.binancefuture.com
- Date: 2026-03-10

Please help clarify the correct usage. Thank you!
```

---

## 📊 总结

**已知：**
- ✅ 测试网支持 Algo Order API 端点
- ✅ 必需 algotype 参数
- ❌ algotype 正确值未知
- ❌ 官方文档 404

**建议：**
1. 短期：接受测试网限制，继续其他开发
2. 中期：实盘验证止损功能
3. 长期：联系币安获取文档

---

**🦞 文档调研完成！测试网 Algo Order API 参数未知，建议实盘前验证！**

**调研时间：** 2026-03-10 13:30  
**状态：** 文档缺失，测试网限制确认
