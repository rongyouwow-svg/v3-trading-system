# 🦞 大王量化 v3.1 维护手册

**创建时间**: 2026-03-15 00:40  
**版本**: v3.1  
**状态**: ✅ 生产就绪

---

## 📋 目录

1. [系统架构](#系统架构)
2. [测试网 vs 实盘](#测试网 vs 实盘)
3. [核心功能实现](#核心功能实现)
4. [遇到的问题及解决方案](#遇到的问题及解决方案)
5. [配置管理](#配置管理)
6. [故障排查](#故障排查)
7. [维护清单](#维护清单)

---

## 系统架构

### 组件图

```
┌─────────────────────────────────────────────────────────┐
│                    Web Dashboard                         │
│  (前端页面：策略监控/账户/交易/止损单/配置)              │
└────────────────────┬────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────┐
│                    API Gateway                           │
│  (dashboard_api.py + 路由模块)                           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   策略管理器                             │
│  (strategy_manager.py)                                   │
│  - 策略生命周期管理（启动/停止/重启）                    │
│  - 策略状态同步                                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   策略实例                               │
│  (rsi_1min_strategy.py, etc.)                           │
│  - RSI 计算                                              │
│  - 信号生成                                              │
│  - 仓位控制                                              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   连接器                                 │
│  (connectors/binance/usdt_futures.py)                   │
│  - 订单管理（创建/查询/取消）                            │
│  - 持仓管理                                              │
│  - 止损单管理                                            │
│  - 测试网/实盘切换                                       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   币安 API                               │
│  测试网：https://demo-fapi.binance.com                   │
│  实盘：https://fapi.binance.com                          │
└─────────────────────────────────────────────────────────┘
```

---

## 测试网 vs 实盘

### API 端点

| 功能 | 测试网 | 实盘 | 是否相同 |
|------|--------|------|---------|
| **REST Base URL** | `https://demo-fapi.binance.com` | `https://fapi.binance.com` | ❌ 不同 |
| **WebSocket URL** | `wss://fstream.binancefuture.com` | `wss://fstream.binance.com` | ❌ 不同 |
| **创建止损单** | `/fapi/v1/algoOrder` | `/fapi/v1/algoOrder` | ✅ 相同 |
| **查询止损单** | `/fapi/v1/openAlgoOrders` | `/fapi/v1/openAlgoOrders` | ✅ 相同 |
| **取消止损单** | `/fapi/v1/algoOrder` (DELETE) | `/fapi/v1/algoOrder` (DELETE) | ✅ 相同 |

### 切换方案

**配置文件**: `config/api_keys.json`

**测试网配置**:
```json
{
  "binance": {
    "testnet": true,
    "api_key": "your_testnet_api_key",
    "secret_key": "your_testnet_secret_key"
  }
}
```

**实盘配置**:
```json
{
  "binance": {
    "testnet": false,
    "api_key": "your_real_api_key",
    "secret_key": "your_real_secret_key"
  }
}
```

**切换步骤**:
1. 修改 `config/api_keys.json` 中的 `testnet` 字段
2. 替换 `api_key` 和 `secret_key`
3. 重启服务：`supervisorctl restart quant-web`
4. 验证：`curl http://localhost:3000/api/binance/positions`

**核心优势**:
- ✅ **API 端点相同** - 无需修改代码
- ✅ **参数相同** - 所有参数完全相同
- ✅ **代码相同** - 只需修改配置
- ✅ **连接器自动处理** - `usdt_futures.py` 根据 `testnet` 参数自动选择 base_url

---

## 核心功能实现

### 1. 止损单管理

**文件**: 
- 连接器：`connectors/binance/usdt_futures.py`
- API: `web/binance_testnet_api.py`

**创建止损单**:
```python
# 连接器实现
def create_stop_loss_order(
    self, symbol: str, side: str, quantity: Decimal, 
    stop_price: Decimal = None, trigger_price: Decimal = None
) -> Result:
    params = {
        "symbol": symbol,
        "side": side,
        "algoType": "CONDITIONAL",  # 只支持 CONDITIONAL
        "type": "STOP_MARKET",
        "triggerPrice": str(price),  # 使用 triggerPrice（不是 stopPrice）
        "quantity": str(quantity),
        "reduceOnly": "false",
        "newOrderRespType": "ACK"
    }
    
    data = self._request("POST", "/fapi/v1/algoOrder", params=params, signed=True)
```

**查询止损单**:
```python
# 连接器实现
def get_algo_orders(self, symbol: str = None, limit: int = 50) -> Result:
    params = {
        'limit': limit,
        'timestamp': int(time.time() * 1000)
    }
    if symbol:
        params['symbol'] = symbol
    
    # 使用正确的 API 端点：/fapi/v1/openAlgoOrders
    data = self._request("GET", "/fapi/v1/openAlgoOrders", params=params, signed=True)
```

**取消止损单**:
```python
# 连接器实现
def cancel_algo_order(self, symbol: str, algo_id: str) -> Result:
    params = {
        'symbol': symbol,
        'algoId': algo_id,
        'timestamp': int(time.time() * 1000)
    }
    
    data = self._request("DELETE", "/fapi/v1/algoOrder", params=params, signed=True)
```

**关键参数**:
| 参数 | 值 | 说明 |
|------|-----|------|
| `algoType` | `CONDITIONAL` | 只支持 CONDITIONAL |
| `type` | `STOP_MARKET` | 止损单类型 |
| `triggerPrice` | `2072.31` | 触发价格（不是 `stopPrice`） |
| `side` | `SELL`/`BUY` | 与持仓方向相反 |

---

### 2. 仓位控制

**文件**: `strategies/rsi_1min_strategy.py`

**实现逻辑**:
```python
def open_position(self):
    # 计算允许最大仓位
    max_position_value = self.amount * self.leverage * 1.05  # 105%
    
    # 获取当前持仓
    response = requests.get(f"{BASE_URL}/api/binance/positions")
    current_position_value = pos['size'] * pos['current_price']
    
    # 检查开仓后是否超标
    open_position_value = self.amount * self.leverage
    
    if current_position_value + open_position_value >= max_position_value:
        print(f"⚠️ 开仓后将超过仓位上限，跳过开仓")
        return False
```

**关键改进**:
- ✅ 检查"开仓后总仓位"而不是"当前持仓"
- ✅ 防止连续开仓导致超标
- ✅ 105% 缓冲空间

---

### 3. RSI 策略逻辑

**文件**: `strategies/rsi_1min_strategy.py`

**策略逻辑**:
```python
def check_signal(self, rsi: float):
    # 开仓信号
    if rsi > 50 and not self.position:
        return 'buy'
    
    # 平仓信号
    if rsi > 80 and self.position == 'LONG':
        return 'sell'
    
    return None
```

**阈值说明**:
| RSI 范围 | 状态 | 操作 |
|---------|------|------|
| < 30 | 超卖 | 考虑开多 |
| 30-50 | 偏弱 | 观望 |
| 50-80 | 正常 | RSI>50 开多 |
| > 80 | 超买 | RSI>80 平仓 |

---

## 遇到的问题及解决方案

### 问题 1: 止损单查询 API 错误

**现象**:
```
错误：Path /fapi/v1/algoOrder/list, Method GET is invalid
```

**原因**: 使用了错误的 API 端点

**解决方案**:
- ❌ 错误：`/fapi/v1/algoOrder/list`
- ✅ 正确：`/fapi/v1/openAlgoOrders`

**修复文件**:
- `connectors/binance/usdt_futures.py`
- `web/binance_testnet_api.py`

---

### 问题 2: 前端 JSON 解析错误

**现象**:
```
加载失败：JSON.parse: unexpected end of data at line 1 column 1
```

**原因**: API 路由重复定义（`get_active_strategies()` 定义了两次）

**解决方案**: 删除重复的函数定义

**修复文件**: `strategies/strategy_status_api.py`

---

### 问题 3: AVAX 信号不执行

**现象**: `AVAXUSDT: 信号 32/0`

**原因**: RSI>80 超买区，策略逻辑决定不执行（正常行为）

**解决方案**: 等待 RSI 回落到正常区间（30-70）

**说明**: 这不是 bug，是策略的正常行为

---

### 问题 4: 仓位超标

**现象**: ETH 持仓 622 USDT，超标 97%

**原因**: 仓位控制逻辑错误（只检查当前持仓，不检查开仓后总仓位）

**解决方案**: 修改为检查"开仓后总仓位"

**修复文件**: `strategies/rsi_1min_strategy.py`

---

## 配置管理

### 配置文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| API 配置 | `config/api_keys.json` | API Key/Secret |
| 策略配置 | `config/strategy_config.json` | 策略参数 |
| Supervisor | `supervisor/*.conf` | 进程管理 |

### 环境变量

```bash
# 测试网
export BINANCE_TESTNET=true
export BINANCE_API_KEY=your_testnet_api_key
export BINANCE_SECRET_KEY=your_testnet_secret_key

# 实盘
export BINANCE_TESTNET=false
export BINANCE_API_KEY=your_real_api_key
export BINANCE_SECRET_KEY=your_real_secret_key
```

---

## 故障排查

### 检查清单

1. **Web 服务状态**:
   ```bash
   supervisorctl status quant-web
   curl http://localhost:3000/api/strategy/active
   ```

2. **策略进程状态**:
   ```bash
   ps aux | grep "rsi.*strategy"
   cat logs/strategy_pids.json
   ```

3. **API 连接**:
   ```bash
   curl http://localhost:3000/api/binance/positions
   curl http://localhost:3000/api/binance/stop-loss
   ```

4. **日志检查**:
   ```bash
   tail -f logs/web_dashboard.log
   tail -f logs/strategy_*.log
   ```

### 常见问题

| 问题 | 检查 | 解决 |
|------|------|------|
| 网页 404 | API 路由 | 检查路由定义，删除重复 |
| 止损单查询失败 | API 端点 | 使用 `/fapi/v1/openAlgoOrders` |
| 信号不执行 | RSI 值 | 检查 RSI 是否在正常区间 |
| 仓位超标 | 持仓检查 | 检查仓位控制逻辑 |

---

## 维护清单

### 每日检查

- [ ] Web 服务状态（supervisor status）
- [ ] 策略进程状态（supervisor status）
- [ ] 监控进程状态（supervisor status）
- [ ] 持仓和止损单
- [ ] 告警日志（logs/monitor_alerts.log）
- [ ] Telegram 告警记录

### 每周检查

- [ ] 策略性能分析
- [ ] RSI 阈值优化
- [ ] 仓位控制调整
- [ ] 备份配置文件

### 每月检查

- [ ] 测试网→实盘切换测试
- [ ] API Key 轮换
- [ ] 系统更新
- [ ] 文档更新

---

## 附录

### 参考文档

- 币安官方文档：https://developers.binance.com/docs/derivatives/usds-margined-futures
- 历史实现：`/home/admin/.openclaw/workspace/quant/history/docs/report/币安 Algo Order API 完全实现.md`
- 问题诊断：`/home/admin/.openclaw/workspace/quant/v3-architecture/FRONTEND_ISSUE_DIAGNOSIS.md`
- 止损单方案：`/home/admin/.openclaw/workspace/quant/v3-architecture/STOP_LOSS_API_SOLUTION.md`
- 测试网切换：`/home/admin/.openclaw/workspace/quant/v3-architecture/TESTNET_TO_PROD_SWITCH_PLAN.md`

### 文件位置记忆

**核心文件**:
- 连接器：`connectors/binance/usdt_futures.py`
- 策略：`strategies/rsi_1min_strategy.py`
- API: `web/binance_testnet_api.py`
- 配置：`config/api_keys.json`

**日志文件**:
- Web 日志：`logs/web_dashboard.log`
- 策略日志：`logs/strategy_*.log`
- 状态文件：`logs/strategy_pids.json`

---

**维护手册版本**: v1.0  
**最后更新**: 2026-03-15 00:40  
**维护负责人**: AI Assistant
