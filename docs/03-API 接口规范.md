# 🦞 大王量化交易系统 v3.0
## API 接口规范文档

**文档版本**: v1.0  
**创建时间**: 2026-03-13  
**最后更新**: 2026-03-13

---

## 📋 目录

1. [概述](#1-概述)
2. [策略管理 API](#2-策略管理-api)
3. [订单管理 API](#3-订单管理-api)
4. [止损单管理 API](#4-止损单管理-api)
5. [交易记录 API](#5-交易记录-api)
6. [持仓管理 API](#6-持仓管理-api)
7. [账户管理 API](#7-账户管理-api)
8. [系统管理 API](#8-系统管理-api)
9. [错误码说明](#9-错误码说明)

---

## 1. 概述

### 1.1 基础信息

- **Base URL**: `http://localhost:8080`
- **认证方式**: API Key (Header: `X-API-Key`)
- **数据格式**: JSON
- **字符编码**: UTF-8

### 1.2 通用响应格式

**成功响应**:
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2026-03-13T14:00:00Z"
}
```

**失败响应**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAM",
    "message": "参数错误",
    "details": {}
  },
  "timestamp": "2026-03-13T14:00:00Z"
}
```

---

## 2. 策略管理 API

### 2.1 启动策略

**POST** `/api/strategy/start`

**请求**:
```json
{
  "symbol": "ETHUSDT",
  "strategy_id": "breakout",
  "side": "LONG",
  "leverage": 5,
  "amount": 100,
  "params": {
    "threshold": 0.02,
    "position_size": 0.2
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "strategy_id": "breakout",
    "symbol": "ETHUSDT",
    "status": "running",
    "start_time": "2026-03-13T14:00:00Z",
    "entry_price": 2050.5,
    "leverage": 5,
    "amount": 100
  },
  "message": "策略已启动"
}
```

### 2.2 停止策略

**POST** `/api/strategy/stop`

**请求**:
```json
{
  "symbol": "ETHUSDT",
  "close_position": true,
  "cancel_stop_loss": true
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "symbol": "ETHUSDT",
    "status": "stopped",
    "stop_time": "2026-03-13T15:00:00Z",
    "pnl": 15.3,
    "pnl_pct": 1.5,
    "position_closed": true,
    "stop_loss_cancelled": true
  },
  "message": "策略已停止"
}
```

### 2.3 获取策略列表

**GET** `/api/strategy/list`

**查询参数**:
- `status` (可选): running/stopped/all
- `symbol` (可选): 交易对

**响应**:
```json
{
  "success": true,
  "data": {
    "strategies": [
      {
        "id": 1,
        "symbol": "ETHUSDT",
        "strategy_id": "breakout",
        "strategy_name": "突破策略",
        "side": "LONG",
        "status": "running",
        "leverage": 5,
        "amount": 100,
        "start_time": "2026-03-13T14:00:00Z",
        "entry_price": 2050.5,
        "current_price": 2065.3,
        "position_size": 0.2439,
        "pnl": 15.3,
        "pnl_pct": 1.5,
        "is_hot_plug": true
      }
    ],
    "count": 1,
    "total_pnl": 15.3,
    "total_pnl_pct": 1.5
  }
}
```

### 2.4 获取策略状态

**GET** `/api/strategy/status/:symbol`

**响应**:
```json
{
  "success": true,
  "data": {
    "symbol": "ETHUSDT",
    "strategy_id": "breakout",
    "status": "running",
    "start_time": "2026-03-13T14:00:00Z",
    "uptime_seconds": 3600,
    "entry_price": 2050.5,
    "current_price": 2065.3,
    "position_size": 0.2439,
    "pnl": 15.3,
    "pnl_pct": 1.5,
    "stop_loss": {
      "algo_id": "SL123456",
      "trigger_price": 2000.0,
      "status": "WAIT_TO_TRIGGER"
    },
    "signals": {
      "total": 10,
      "buy": 2,
      "sell": 0
    }
  }
}
```

### 2.5 获取信号历史

**GET** `/api/strategy/signals`

**查询参数**:
- `symbol` (可选): 交易对
- `limit` (可选): 默认 50

**响应**:
```json
{
  "success": true,
  "data": {
    "signals": [
      {
        "id": 1,
        "symbol": "ETHUSDT",
        "type": "BUY",
        "confidence": 0.85,
        "price": 2050.5,
        "timestamp": "2026-03-13T14:00:00Z",
        "executed": true
      }
    ],
    "count": 1
  }
}
```

---

## 3. 订单管理 API

### 3.1 创建订单

**POST** `/api/order/create`

**请求**:
```json
{
  "symbol": "ETHUSDT",
  "side": "BUY",
  "type": "MARKET",
  "quantity": 0.1,
  "leverage": 5,
  "reduce_only": false
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "order_id": "123456789",
    "symbol": "ETHUSDT",
    "side": "BUY",
    "type": "MARKET",
    "quantity": 0.1,
    "price": null,
    "avg_price": 2050.5,
    "status": "FILLED",
    "created_at": "2026-03-13T14:00:00Z",
    "filled_at": "2026-03-13T14:00:01Z"
  },
  "message": "订单已创建"
}
```

### 3.2 取消订单

**POST** `/api/order/cancel`

**请求**:
```json
{
  "symbol": "ETHUSDT",
  "order_id": "123456789"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "order_id": "123456789",
    "symbol": "ETHUSDT",
    "status": "CANCELED",
    "canceled_at": "2026-03-13T14:00:00Z"
  },
  "message": "订单已取消"
}
```

### 3.3 获取订单列表

**GET** `/api/order/list`

**查询参数**:
- `symbol` (可选)
- `status` (可选): PENDING/OPEN/FILLED/CANCELED
- `limit` (可选): 默认 100

**响应**:
```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "order_id": "123456789",
        "symbol": "ETHUSDT",
        "side": "BUY",
        "type": "MARKET",
        "quantity": 0.1,
        "avg_price": 2050.5,
        "filled_quantity": 0.1,
        "status": "FILLED",
        "created_at": "2026-03-13T14:00:00Z"
      }
    ],
    "count": 1
  }
}
```

### 3.4 获取订单状态

**GET** `/api/order/status/:order_id`

**响应**:
```json
{
  "success": true,
  "data": {
    "order_id": "123456789",
    "symbol": "ETHUSDT",
    "side": "BUY",
    "type": "MARKET",
    "quantity": 0.1,
    "avg_price": 2050.5,
    "filled_quantity": 0.1,
    "status": "FILLED",
    "fills": [
      {
        "trade_id": "987654321",
        "price": 2050.5,
        "quantity": 0.1,
        "commission": 0.0001,
        "commission_asset": "ETH",
        "time": "2026-03-13T14:00:01Z"
      }
    ],
    "created_at": "2026-03-13T14:00:00Z",
    "updated_at": "2026-03-13T14:00:01Z"
  }
}
```

### 3.5 获取成交记录

**GET** `/api/order/fills`

**查询参数**:
- `symbol` (可选)
- `order_id` (可选)
- `limit` (可选)

**响应**:
```json
{
  "success": true,
  "data": {
    "fills": [
      {
        "trade_id": "987654321",
        "order_id": "123456789",
        "symbol": "ETHUSDT",
        "side": "BUY",
        "price": 2050.5,
        "quantity": 0.1,
        "commission": 0.0001,
        "commission_asset": "ETH",
        "time": "2026-03-13T14:00:01Z"
      }
    ],
    "count": 1
  }
}
```

---

## 4. 止损单管理 API

### 4.1 创建止损单

**POST** `/api/stoploss/create`

**请求**:
```json
{
  "symbol": "ETHUSDT",
  "side": "SELL",
  "trigger_price": 2000.0,
  "quantity": 0.1,
  "stop_price": 1999.0
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "algo_id": "SL123456",
    "symbol": "ETHUSDT",
    "side": "SELL",
    "trigger_price": 2000.0,
    "stop_price": 1999.0,
    "quantity": 0.1,
    "status": "WAIT_TO_TRIGGER",
    "created_at": "2026-03-13T14:00:00Z"
  },
  "message": "止损单已创建"
}
```

### 4.2 取消止损单

**POST** `/api/stoploss/cancel`

**请求**:
```json
{
  "symbol": "ETHUSDT",
  "algo_id": "SL123456"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "algo_id": "SL123456",
    "symbol": "ETHUSDT",
    "status": "CANCELED",
    "canceled_at": "2026-03-13T15:00:00Z"
  },
  "message": "止损单已取消"
}
```

### 4.3 获取止损单列表

**GET** `/api/stoploss/list`

**查询参数**:
- `symbol` (可选)
- `status` (可选)

**响应**:
```json
{
  "success": true,
  "data": {
    "stop_orders": [
      {
        "algo_id": "SL123456",
        "symbol": "ETHUSDT",
        "side": "SELL",
        "trigger_price": 2000.0,
        "quantity": 0.1,
        "status": "WAIT_TO_TRIGGER",
        "created_at": "2026-03-13T14:00:00Z"
      }
    ],
    "count": 1
  }
}
```

### 4.4 获取止损单状态

**GET** `/api/stoploss/status/:algo_id`

**响应**:
```json
{
  "success": true,
  "data": {
    "algo_id": "SL123456",
    "symbol": "ETHUSDT",
    "side": "SELL",
    "trigger_price": 2000.0,
    "stop_price": 1999.0,
    "quantity": 0.1,
    "status": "WAIT_TO_TRIGGER",
    "created_at": "2026-03-13T14:00:00Z",
    "updated_at": "2026-03-13T14:00:00Z"
  }
}
```

---

## 5. 交易记录 API

### 5.1 获取交易记录

**GET** `/api/trades`

**查询参数**:
- `symbol` (可选)
- `event_type` (可选): OPEN/CLOSE/STOP_LOSS
- `start_time` (可选): ISO 格式
- `end_time` (可选): ISO 格式
- `limit` (可选): 默认 100

**响应**:
```json
{
  "success": true,
  "data": {
    "trades": [
      {
        "id": 1,
        "timestamp": "2026-03-13T14:00:00Z",
        "event_type": "OPEN",
        "symbol": "ETHUSDT",
        "side": "BUY",
        "quantity": 0.1,
        "price": 2050.5,
        "order_id": "123456789",
        "strategy_id": "breakout",
        "pnl": 0,
        "commission": 0.0001
      }
    ],
    "count": 1
  }
}
```

### 5.2 获取交易统计

**GET** `/api/trades/summary`

**响应**:
```json
{
  "success": true,
  "data": {
    "date": "2026-03-13",
    "total_trades": 10,
    "by_type": {
      "OPEN": 5,
      "CLOSE": 5
    },
    "by_symbol": {
      "ETHUSDT": 6,
      "BTCUSDT": 4
    },
    "total_pnl": 153.5,
    "total_commission": 0.5,
    "win_rate": 0.6,
    "avg_win": 25.3,
    "avg_loss": -12.5
  }
}
```

### 5.3 导出交易记录

**GET** `/api/trades/export`

**查询参数**:
- `format` (可选): csv/json
- `start_date` (可选)
- `end_date` (可选)

**响应**: CSV 文件或 JSON 文件下载

### 5.4 获取 PnL 统计

**GET** `/api/trades/pnl`

**查询参数**:
- `period` (可选): day/week/month/year
- `symbol` (可选)

**响应**:
```json
{
  "success": true,
  "data": {
    "period": "day",
    "pnl_history": [
      {
        "date": "2026-03-13",
        "realized_pnl": 153.5,
        "unrealized_pnl": 15.3,
        "total_pnl": 168.8
      }
    ],
    "total_realized": 153.5,
    "total_unrealized": 15.3
  }
}
```

---

## 6. 持仓管理 API

### 6.1 获取持仓列表

**GET** `/api/positions`

**响应**:
```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "symbol": "ETHUSDT",
        "side": "LONG",
        "size": 0.2439,
        "entry_price": 2050.5,
        "mark_price": 2065.3,
        "notional": 503.6,
        "unrealized_pnl": 15.3,
        "unrealized_pnl_pct": 1.5,
        "leverage": 5,
        "margin": 100.72,
        "liquidation_price": 1640.4
      }
    ],
    "count": 1,
    "total_notional": 503.6,
    "total_unrealized_pnl": 15.3
  }
}
```

### 6.2 获取指定持仓

**GET** `/api/positions/:symbol`

**响应**:
```json
{
  "success": true,
  "data": {
    "symbol": "ETHUSDT",
    "side": "LONG",
    "size": 0.2439,
    "entry_price": 2050.5,
    "mark_price": 2065.3,
    "notional": 503.6,
    "unrealized_pnl": 15.3,
    "unrealized_pnl_pct": 1.5,
    "leverage": 5,
    "margin": 100.72,
    "liquidation_price": 1640.4,
    "strategy_id": "breakout",
    "start_time": "2026-03-13T14:00:00Z"
  }
}
```

### 6.3 平仓

**POST** `/api/positions/close`

**请求**:
```json
{
  "symbol": "ETHUSDT",
  "quantity": 0.2439,
  "type": "MARKET"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "symbol": "ETHUSDT",
    "closed_quantity": 0.2439,
    "avg_price": 2065.3,
    "realized_pnl": 15.3,
    "order_id": "987654321"
  },
  "message": "平仓成功"
}
```

---

## 7. 账户管理 API

### 7.1 获取账户余额

**GET** `/api/account/balance`

**响应**:
```json
{
  "success": true,
  "data": {
    "balances": [
      {
        "asset": "USDT",
        "free": 9500.5,
        "locked": 500.0,
        "total": 10000.5
      }
    ],
    "total_equity": 10000.5,
    "available_balance": 9500.5,
    "total_unrealized_pnl": 15.3
  }
}
```

### 7.2 获取账户信息

**GET** `/api/account/info`

**响应**:
```json
{
  "success": true,
  "data": {
    "account_type": "UMFUTURE",
    "can_trade": true,
    "can_deposit": true,
    "can_withdraw": true,
    "maker_commission": 0.0002,
    "taker_commission": 0.0005,
    "total_wallet_balance": 10000.5,
    "total_unrealized_pnl": 15.3,
    "total_margin_balance": 10015.8,
    "available_balance": 9500.5,
    "max_withdraw_amount": 9500.5
  }
}
```

### 7.3 获取风险指标

**GET** `/api/account/risk`

**响应**:
```json
{
  "success": true,
  "data": {
    "total_exposure": 503.6,
    "exposure_limit": 10000.0,
    "utilization": 5.04,
    "margin_ratio": 0.05,
    "liquidation_risk": "LOW",
    "positions_count": 1,
    "max_positions": 10,
    "daily_pnl": 153.5,
    "daily_pnl_pct": 1.53,
    "max_drawdown": -50.0,
    "max_drawdown_pct": -0.5
  }
}
```

---

## 8. 系统管理 API

### 8.1 健康检查

**GET** `/api/health`

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "v3.0.0",
    "uptime_seconds": 86400,
    "services": {
      "strategy_engine": "running",
      "execution_engine": "running",
      "risk_engine": "running",
      "market_data": "running",
      "database": "connected",
      "redis": "connected"
    },
    "timestamp": "2026-03-13T14:00:00Z"
  }
}
```

### 8.2 获取系统状态

**GET** `/api/system/status`

**响应**:
```json
{
  "success": true,
  "data": {
    "cpu_usage": 25.5,
    "memory_usage": 512.3,
    "disk_usage": 45.2,
    "active_strategies": 2,
    "active_orders": 5,
    "today_trades": 10,
    "today_pnl": 153.5,
    "system_load": {
      "1min": 0.5,
      "5min": 0.6,
      "15min": 0.7
    }
  }
}
```

### 8.3 获取系统日志

**GET** `/api/system/logs`

**查询参数**:
- `level` (可选): INFO/WARNING/ERROR
- `service` (可选): strategy/execution/risk/gateway
- `limit` (可选): 默认 100

**响应**:
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "timestamp": "2026-03-13T14:00:00Z",
        "level": "INFO",
        "service": "strategy",
        "message": "策略已启动：ETHUSDT - breakout"
      }
    ],
    "count": 1
  }
}
```

### 8.4 重启服务

**POST** `/api/system/restart`

**请求**:
```json
{
  "service": "gateway",
  "delay_seconds": 5
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "service": "gateway",
    "status": "restarting",
    "expected_ready_at": "2026-03-13T14:00:10Z"
  },
  "message": "服务重启中"
}
```

---

## 9. 错误码说明

### 9.1 通用错误

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-----------|
| `INVALID_PARAM` | 参数错误 | 400 |
| `UNAUTHORIZED` | 未授权 | 401 |
| `FORBIDDEN` | 禁止访问 | 403 |
| `NOT_FOUND` | 资源不存在 | 404 |
| `INTERNAL_ERROR` | 内部错误 | 500 |

### 9.2 业务错误

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-----------|
| `STRATEGY_EXISTS` | 策略已存在 | 409 |
| `STRATEGY_NOT_FOUND` | 策略不存在 | 404 |
| `ORDER_EXISTS` | 订单已存在 | 409 |
| `ORDER_NOT_FOUND` | 订单不存在 | 404 |
| `INSUFFICIENT_BALANCE` | 余额不足 | 400 |
| `POSITION_NOT_FOUND` | 持仓不存在 | 404 |
| `STOP_LOSS_EXISTS` | 止损单已存在 | 409 |
| `EXCHANGE_ERROR` | 交易所错误 | 502 |
| `RATE_LIMIT` | 限流 | 429 |

### 9.3 错误响应示例

```json
{
  "success": false,
  "error": {
    "code": "STRATEGY_EXISTS",
    "message": "ETHUSDT 已有活跃策略",
    "details": {
      "symbol": "ETHUSDT",
      "existing_strategy": "breakout"
    }
  },
  "timestamp": "2026-03-13T14:00:00Z"
}
```

---

## 附录

### A. WebSocket 接口

**连接地址**: `ws://localhost:8081/ws`

**订阅行情**:
```json
{
  "action": "subscribe",
  "channel": "ticker",
  "symbol": "ETHUSDT"
}
```

**推送数据**:
```json
{
  "channel": "ticker",
  "symbol": "ETHUSDT",
  "data": {
    "price": 2065.3,
    "change_24h": 1.5,
    "volume_24h": 1000000,
    "timestamp": "2026-03-13T14:00:00Z"
  }
}
```

### B. 认证方式

在请求 Header 中添加:
```
X-API-Key: your_api_key_here
```

### C. 限流说明

- **普通接口**: 100 次/分钟
- **交易接口**: 300 次/分钟
- **行情接口**: 600 次/分钟

---

**文档结束**
