# 🦞 v3.1 重构 API 接口文档

**版本**: v3.1  
**创建时间**: 2026-03-14 16:45  
**状态**: 重构中

---

## 📋 目录

1. [策略管理 API](#1-策略管理-api)
2. [订单管理 API](#2-订单管理-api)
3. [持仓管理 API](#3-持仓管理-api)
4. [止损单管理 API](#4-止损单管理-api)
5. [账户管理 API](#5-账户管理-api)
6. [前端适配指南](#6-前端适配指南)

---

## 1. 策略管理 API

### 1.1 启动策略

**POST** `/api/strategy/start`

**请求**:
```json
{
  "name": "ETH_RSI",
  "symbol": "ETHUSDT",
  "type": "rsi_strategy",  // 策略类型
  "leverage": 3,
  "amount": 100,
  "stop_loss_pct": 0.002,  // 可选，不传则使用 5% 兜底
  "module": "core.strategy.modules.rsi_strategy"  // 可选，默认根据 type 推断
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "name": "ETH_RSI",
    "status": "running",
    "symbol": "ETHUSDT",
    "leverage": 3,
    "amount": 100,
    "stop_loss_pct": 0.002,
    "message": "策略已启动，止损单已创建 (0.2%)"
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "STRATEGY_ALREADY_EXISTS",
    "message": "策略已存在"
  }
}
```

---

### 1.2 停止策略

**POST** `/api/strategy/stop`

**请求**:
```json
{
  "name": "ETH_RSI",
  "close_position": true,      // 是否平仓（默认 true）
  "cancel_stop_loss": true     // 是否取消止损单（默认 true）
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "name": "ETH_RSI",
    "status": "stopped",
    "position_closed": true,
    "stop_loss_cancelled": true,
    "message": "策略已停止，持仓已平仓，止损单已取消"
  }
}
```

---

### 1.3 获取策略列表

**GET** `/api/strategy/list`

**响应**:
```json
{
  "success": true,
  "data": {
    "strategies": [
      {
        "name": "ETH_RSI",
        "status": "running",
        "symbol": "ETHUSDT",
        "leverage": 3,
        "amount": 100,
        "stop_loss_pct": 0.002,
        "last_tick": "2026-03-14T16:45:00Z",
        "error_count": 0
      },
      {
        "name": "LINK_RSI",
        "status": "running",
        "symbol": "LINKUSDT",
        "leverage": 3,
        "amount": 100,
        "stop_loss_pct": 0.002,
        "last_tick": "2026-03-14T16:45:00Z",
        "error_count": 0
      }
    ]
  }
}
```

---

### 1.4 获取策略状态

**GET** `/api/strategy/{name}/status`

**响应**:
```json
{
  "success": true,
  "data": {
    "name": "ETH_RSI",
    "status": "running",
    "symbol": "ETHUSDT",
    "leverage": 3,
    "amount": 100,
    "stop_loss_pct": 0.002,
    "last_tick": "2026-03-14T16:45:00Z",
    "error_count": 0,
    "start_time": "2026-03-14T16:00:00Z"
  }
}
```

---

## 2. 订单管理 API

### 2.1 开仓

**POST** `/api/order/open`

**请求**:
```json
{
  "symbol": "ETHUSDT",
  "side": "BUY",
  "quantity": 0.15,
  "order_type": "MARKET",
  "leverage": 3,
  "stop_loss_pct": 0.002  // 可选，不传则使用 5% 兜底
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "order_id": "8539522725",
    "symbol": "ETHUSDT",
    "side": "BUY",
    "quantity": 0.15,
    "price": 2076.1,
    "status": "FILLED",
    "stop_loss": {
      "algo_id": "1000000022710898",
      "trigger_price": 2071.97,
      "stop_loss_pct": 0.002,
      "status": "WAITING"
    },
    "message": "开仓成功，止损单已创建 (0.2%)"
  }
}
```

---

### 2.2 平仓

**POST** `/api/order/close`

**请求**:
```json
{
  "symbol": "ETHUSDT",
  "quantity": 0.15,  // 可选，不传则全平
  "order_type": "MARKET"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "order_id": "8539626305",
    "symbol": "ETHUSDT",
    "side": "SELL",
    "quantity": 0.15,
    "price": 2076.1,
    "status": "FILLED",
    "pnl": -2.37,
    "pnl_pct": -0.38,
    "stop_loss_cancelled": true,
    "message": "平仓成功，止损单已取消"
  }
}
```

---

## 3. 持仓管理 API

### 3.1 获取持仓

**GET** `/api/position`

**查询参数**:
- `symbol` (可选): 交易对，不传则返回所有持仓

**响应**:
```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "symbol": "ETHUSDT",
        "side": "LONG",
        "size": 0.15,
        "entry_price": 2076.1,
        "current_price": 2074.94,
        "leverage": 3,
        "unrealized_pnl": -0.17,
        "unrealized_pnl_pct": -0.06,
        "liquidation_price": 0.0,
        "last_update": "2026-03-14T16:45:00Z"
      }
    ]
  }
}
```

---

### 3.2 同步持仓

**POST** `/api/position/sync`

**请求**:
```json
{
  "symbol": "ETHUSDT"  // 可选，不传则同步所有
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "symbol": "ETHUSDT",
    "side": "LONG",
    "size": 0.15,
    "entry_price": 2076.1,
    "current_price": 2074.94,
    "leverage": 3,
    "unrealized_pnl": -0.17,
    "unrealized_pnl_pct": -0.06,
    "synced_at": "2026-03-14T16:45:00Z"
  }
}
```

---

## 4. 止损单管理 API

### 4.1 获取止损单列表

**GET** `/api/stop-loss`

**查询参数**:
- `symbol` (可选): 交易对
- `status` (可选): WAITING/TRIGGERED/CANCELLED

**响应**:
```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "algo_id": "1000000022710898",
        "symbol": "ETHUSDT",
        "side": "SELL",
        "trigger_price": 2071.97,
        "quantity": 0.15,
        "status": "WAITING",
        "stop_loss_pct": 0.002,
        "entry_price": 2076.1,
        "create_time": "2026-03-14T16:00:00Z"
      }
    ],
    "count": 1
  }
}
```

---

### 4.2 取消止损单

**POST** `/api/stop-loss/cancel`

**请求**:
```json
{
  "algo_id": "1000000022710898",  // 可选
  "symbol": "ETHUSDT"             // 可选，取消该交易对所有止损单
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "algo_id": "1000000022710898",
    "symbol": "ETHUSDT",
    "status": "CANCELLED",
    "message": "止损单已取消"
  }
}
```

---

## 5. 账户管理 API

### 5.1 获取账户余额

**GET** `/api/account/balance`

**响应**:
```json
{
  "success": true,
  "data": {
    "total_balance": 5000.00,
    "available_balance": 4873.38,
    "unrealized_pnl": -0.17,
    "assets": [
      {
        "asset": "USDT",
        "wallet_balance": 5000.00,
        "available_balance": 4873.38
      }
    ]
  }
}
```

---

### 5.2 获取交易记录

**GET** `/api/account/trades`

**查询参数**:
- `symbol` (可选): 交易对
- `limit` (可选): 数量限制（默认 50）

**响应**:
```json
{
  "success": true,
  "data": {
    "trades": [
      {
        "trade_id": "8539626305",
        "symbol": "ETHUSDT",
        "side": "SELL",
        "order_type": "平多",
        "price": 2076.1,
        "quantity": 0.15,
        "commission": 0.31,
        "commission_asset": "USDT",
        "realized_pnl": -2.37,
        "trade_time": "2026-03-14T16:39:30Z"
      }
    ],
    "count": 1
  }
}
```

---

## 6. 前端适配指南

### 6.1 策略启动表单

```html
<!-- 策略启动表单 -->
<div class="form-group">
    <label>策略名称</label>
    <input type="text" id="strategyName" value="ETH_RSI">
</div>

<div class="form-group">
    <label>交易对</label>
    <select id="symbol">
        <option value="ETHUSDT">ETH/USDT</option>
        <option value="LINKUSDT">LINK/USDT</option>
        <option value="AVAXUSDT">AVAX/USDT</option>
    </select>
</div>

<div class="form-group">
    <label>杠杆</label>
    <input type="number" id="leverage" value="3" min="1" max="125">
</div>

<div class="form-group">
    <label>保证金 (USDT)</label>
    <input type="number" id="amount" value="100" min="10">
</div>

<div class="form-group">
    <label>止损配置</label>
    <div class="checkbox-group">
        <input type="checkbox" id="useCustomStopLoss">
        <label for="useCustomStopLoss">启用策略止损</label>
    </div>
    <input type="number" id="stopLossPct" value="0.2" min="0.1" max="5" step="0.1" 
           style="display:none;">
    <small class="help-text">不勾选则使用 5% 硬止损兜底</small>
</div>

<button onclick="startStrategy()">启动策略</button>

<script>
// 显示/隐藏止损输入框
document.getElementById('useCustomStopLoss').addEventListener('change', function(e) {
    document.getElementById('stopLossPct').style.display = e.target.checked ? 'block' : 'none';
});

// 启动策略
async function startStrategy() {
    const useCustomStopLoss = document.getElementById('useCustomStopLoss').checked;
    const stopLossPct = document.getElementById('stopLossPct').value;
    
    const payload = {
        name: document.getElementById('strategyName').value,
        symbol: document.getElementById('symbol').value,
        leverage: parseInt(document.getElementById('leverage').value),
        amount: parseFloat(document.getElementById('amount').value),
        stop_loss_pct: useCustomStopLoss ? parseFloat(stopLossPct) / 100 : null
    };
    
    const response = await fetch('/api/strategy/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    if (result.success) {
        alert('策略启动成功！' + result.data.message);
        loadStrategyList();  // 刷新策略列表
    } else {
        alert('策略启动失败：' + result.error.message);
    }
}
</script>
```

---

### 6.2 止损单页面刷新

```html
<!-- 止损单列表 -->
<div id="stopLossTable">
    <div class="loading">加载中...</div>
</div>

<button onclick="loadStopLossOrders()">🔄 刷新</button>

<script>
async function loadStopLossOrders() {
    const container = document.getElementById('stopLossTable');
    container.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch('/api/stop-loss');
        const data = await response.json();
        
        if (data.success && data.data.orders.length > 0) {
            container.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>交易对</th>
                            <th>方向</th>
                            <th>触发价</th>
                            <th>数量</th>
                            <th>止损比例</th>
                            <th>状态</th>
                            <th>创建时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.data.orders.map(order => `
                            <tr>
                                <td><strong>${order.symbol}</strong></td>
                                <td><span class="badge badge-${order.side === 'SELL' ? 'success' : 'danger'}">${order.side}</span></td>
                                <td style="font-family: monospace;">${order.trigger_price}</td>
                                <td>${order.quantity}</td>
                                <td>${(order.stop_loss_pct * 100).toFixed(2)}%</td>
                                <td><span class="badge badge-${getStatusClass(order.status)}">${order.status}</span></td>
                                <td>${order.create_time}</td>
                                <td>
                                    ${order.status === 'WAITING' ? 
                                        `<button class="btn btn-danger" onclick="cancelStopLoss('${order.algo_id}')">取消</button>` : 
                                        '-'}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            container.innerHTML = `
                <div style="text-align: center; padding: 60px 20px; color: #666;">
                    <div style="font-size: 64px;">📊</div>
                    <div style="font-size: 18px; margin-top: 20px;">暂无止损单</div>
                    <div style="margin-top: 10px; font-size: 14px; color: #999;">策略开仓时会自动创建止损单</div>
                </div>
            `;
        }
    } catch (err) {
        container.innerHTML = `<div style="text-align: center; padding: 40px; color: #d63031;">❌ 加载失败：${err.message}</div>`;
    }
}

function getStatusClass(status) {
    switch (status) {
        case 'WAITING': return 'warning';
        case 'TRIGGERED': return 'danger';
        case 'CANCELLED': return 'secondary';
        default: return 'warning';
    }
}

async function cancelStopLoss(algoId) {
    if (!confirm('确定取消这个止损单吗？')) return;
    
    const response = await fetch('/api/stop-loss/cancel', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({algo_id: algoId})
    });
    
    const result = await response.json();
    if (result.success) {
        alert('✅ 止损单已取消');
        loadStopLossOrders();  // 刷新列表
    } else {
        alert('❌ 取消失败：' + result.error.message);
    }
}

// 页面加载时获取止损单列表
document.addEventListener('DOMContentLoaded', loadStopLossOrders);

// 每 30 秒自动刷新
setInterval(loadStopLossOrders, 30000);
</script>
```

---

## 7. 错误码说明

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| `STRATEGY_ALREADY_EXISTS` | 策略已存在 | 先停止旧策略或更换名称 |
| `STRATEGY_NOT_FOUND` | 策略不存在 | 检查策略名称是否正确 |
| `POSITION_NOT_FOUND` | 无持仓 | 先开仓再平仓 |
| `STOP_LOSS_NOT_FOUND` | 止损单不存在 | 检查止损单 ID 是否正确 |
| `INSUFFICIENT_BALANCE` | 余额不足 | 充值或减少开仓金额 |
| `POSITION_LIMIT_EXCEEDED` | 达到仓位上限 | 先平仓再开仓 |
| `API_ERROR` | 币安 API 错误 | 检查网络连接或 API 配置 |

---

**文档生成时间**: 2026-03-14 16:45  
**下次更新**: API 变更时
