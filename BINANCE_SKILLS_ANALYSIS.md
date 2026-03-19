# 🟡 Binance Skills 分析报告

**分析时间**: 2026-03-16 16:45  
**来源**: clawhub list + SKILL.md 文档

---

## 📦 已安装的 Binance 相关 Skills

| Skill | 版本 | 说明 | 状态 |
|-------|------|------|------|
| **binance-pro** | 1.0.0 | 完整币安集成 | ✅ 已安装 |
| **binance-futures-trading** | 1.0.0 | 合约交易支持 | ✅ 已安装 |
| **binance-stop-loss-manager** | 1.0.1 | 止损止盈管理 | ✅ 已安装 |

---

## 🟡 binance-pro（核心技能）

### 功能概览

**完整币安集成** - 世界最大加密货币交易所

- ✅ 现货交易（Spot）
- ✅ 合约交易（Futures，最高 125x 杠杆）
- ✅ 理财质押（Staking）
- ✅ 账户管理
- ✅ 持仓查询
- ✅ 止损止盈设置

### 核心功能

#### 1. 账户查询
```bash
# 现货余额
curl -s "https://api.binance.com/api/v3/account" | jq '[.balances[] | select(.free != "0")]'

# 合约持仓
curl -s "https://fapi.binance.com/fapi/v2/positionRisk" | jq '[.[] | select(.positionAmt != "0")]'

# 详细余额
curl -s "https://fapi.binance.com/fapi/v2/balance" | jq '[.[] | select(.balance != "0")]'
```

#### 2. 合约交易
```bash
# 开多（BUY LONG）
curl -X POST "https://fapi.binance.com/fapi/v1/order" \
  -d "symbol=BTCUSDT&side=BUY&type=MARKET&quantity=0.001"

# 开空（SELL SHORT）
curl -X POST "https://fapi.binance.com/fapi/v1/order" \
  -d "symbol=BTCUSDT&side=SELL&type=MARKET&quantity=0.001"

# 设置杠杆
curl -X POST "https://fapi.binance.com/fapi/v1/leverage" \
  -d "symbol=BTCUSDT&leverage=10"
```

#### 3. 止损止盈
```bash
# 设置止损
curl -X POST "https://fapi.binance.com/fapi/v1/order" \
  -d "symbol=BTCUSDT&side=SELL&type=STOP_MARKET&stopPrice=75000&closePosition=true"

# 设置止盈
curl -X POST "https://fapi.binance.com/fapi/v1/order" \
  -d "symbol=BTCUSDT&side=SELL&type=TAKE_PROFIT_MARKET&stopPrice=85000&closePosition=true"
```

#### 4. 现货交易
```bash
# 买入
curl -X POST "https://api.binance.com/api/v3/order" \
  -d "symbol=ETHUSDT&side=BUY&type=MARKET&quantity=0.1"

# 卖出
curl -X POST "https://api.binance.com/api/v3/order" \
  -d "symbol=ETHUSDT&side=SELL&type=MARKET&quantity=0.1"
```

### 配置要求

**凭证文件**: `~/.openclaw/credentials/binance.json`
```json
{
  "apiKey": "YOUR_API_KEY",
  "secretKey": "YOUR_SECRET_KEY"
}
```

**或环境变量**:
```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_SECRET="your_secret_key"
```

### 支持的交易对

| 交易对 | 说明 |
|--------|------|
| BTCUSDT | 比特币 |
| ETHUSDT | 以太坊 |
| BNBUSDT | BNB |
| SOLUSDT | Solana |
| XRPUSDT | XRP |
| DOGEUSDT | 狗狗币 |
| ADAUSDT | Cardano |
| AVAXUSDT | Avalanche |

---

## 🔵 binance-futures-trading

### 功能

- ✅ 账户余额查询
- ✅ 持仓信息查看
- ✅ 开仓平仓操作
- ✅ 杠杆管理

### 使用示例

```json
{ "action": "balance" }      // 查询余额
{ "action": "position" }     // 查询持仓
```

### 费用

**每次调用**: 0.001 USDT（通过 SkillPay 自动扣费）

### 配置要求

**环境变量**: `SKILLPAY_API_KEY`

---

## 🟢 binance-stop-loss-manager

### 功能

**专业止损止盈管理器**

- ✅ 止损单设置
- ✅ 止盈单设置
- ✅ 移动止损（Trailing Stop）
- ✅ 订单管理
- ✅ 风险计算器
- ✅ 多交易对支持

### 使用示例

```json
{
  "action": "set",
  "pair": "BTC/USDT",
  "entryPrice": 42000,
  "stopLoss": 41000,
  "takeProfit": 45000,
  "riskPercent": 2
}
```

### 输出示例

```json
{
  "success": true,
  "orderId": "123456789",
  "stopLoss": 41000,
  "takeProfit": 45000,
  "riskReward": "1:2",
  "message": "Stop loss and take profit orders placed successfully"
}
```

### 费用

**每次调用**: 0.001 USDT（通过 SkillPay 自动扣费）

### 配置要求

**环境变量**: `SKILLPAY_API_KEY`

---

## 🆚 与现有系统对比

### 现有系统（v3-architecture）

| 功能 | 现有系统 | Binance Skills |
|------|---------|----------------|
| **持仓查询** | ✅ 已实现 | ✅ 支持 |
| **开仓平仓** | ✅ 已实现 | ✅ 支持 |
| **止损单** | ✅ 已实现 | ✅ 支持 |
| **止盈单** | ✅ 已实现 | ✅ 支持 |
| **杠杆设置** | ✅ 已实现 | ✅ 支持 |
| **实盘交易** | ⚠️ 测试网 | ✅ 支持实盘 |
| **多交易所** | ❌ 仅币安 | ✅ 未来可能 |
| **社区维护** | ✅ 自研 | ✅ 社区维护 |

### 优势对比

**现有系统优势**:
- ✅ 完全免费（无 SkillPay 费用）
- ✅ 深度集成（与监控系统整合）
- ✅ 可定制（源码可修改）
- ✅ 测试网支持（无风险测试）

**Binance Skills 优势**:
- ✅ 支持实盘交易
- ✅ 社区维护（持续更新）
- ✅ 标准化接口
- ✅ 多技能协作（未来扩展）

---

## 💡 使用建议

### 场景 1: 测试和开发
**推荐**: 使用现有 v3-architecture 系统
- 测试网无风险
- 可自由修改
- 无额外费用

### 场景 2: 实盘交易
**推荐**: 结合使用
- 现有系统：策略执行 + 监控
- Binance Skills：实盘订单执行（备用）

### 场景 3: 快速原型
**推荐**: Binance Skills
- 快速部署
- 标准化接口
- 社区支持

---

## 📊 总结

### binance-pro（核心推荐）⭐⭐⭐⭐⭐
- **完整功能**: 现货 + 合约 + 理财
- **免费使用**: 无额外费用
- **推荐场景**: 所有 Binance 操作

### binance-futures-trading（可选）⭐⭐⭐
- **专注合约**: 简化接口
- **费用**: 0.001 USDT/次
- **推荐场景**: 快速合约交易

### binance-stop-loss-manager（可选）⭐⭐⭐
- **专业风控**: 止损止盈管理
- **费用**: 0.001 USDT/次
- **推荐场景**: 复杂止损策略

---

## 🎯 最终建议

**大王，Binance Skills Hub 已分析完成！**

**核心价值**:
1. ✅ **binance-pro** - 完整币安集成，免费，强烈推荐
2. ⚠️ **binance-futures-trading** - 功能重复，需付费（0.001 USDT/次）
3. ⚠️ **binance-stop-loss-manager** - 功能重复，需付费（0.001 USDT/次）

**建议**:
- **现有系统已足够** - v3-architecture 功能完整，免费，深度集成
- **binance-pro 可作为备用** - 实盘时可作为备选方案
- **无需安装付费技能** - 现有止损管理器已足够

**下一步**:
- 继续使用现有 v3-architecture 系统
- 如需实盘，配置 binance-pro 凭证即可
- 无需额外安装付费技能

---

*🦞 龙虾王量化交易系统 - Binance Skills 分析*  
*分析时间：2026-03-16 16:45*  
*结论：现有系统已足够，无需额外安装*
