# 🦞 自动量化交易系统架构设计

**创建时间：** 2026-03-08 02:00  
**目标：** 高盈利、低回撤的币安合约自动交易系统

---

## 📊 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     前端看板 (Web UI)                        │
│  - 策略选择与配置                                            │
│  - 实时价格显示                                              │
│  - 持仓和盈亏监控                                            │
│  - 交易记录和信号展示                                        │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                    API 服务层 (Flask)                        │
│  - /api/strategies    - 策略管理                            │
│  - /api/backtest      - 回测执行                            │
│  - /api/trading       - 实盘交易                            │
│  - /api/positions     - 持仓管理                            │
│  - /api/signals       - 信号生成                            │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    核心引擎层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 策略引擎     │  │ 回测引擎     │  │ 信号引擎     │      │
│  │ Strategy    │  │ Backtest    │  │ Signal      │      │
│  │ Engine      │  │ Engine      │  │ Generator   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 风险管理     │  │ 资金管理     │  │ 订单执行     │      │
│  │ Risk        │  │ Capital     │  │ Order       │      │
│  │ Manager     │  │ Manager     │  │ Executor    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    数据层                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 币安 API     │  │ 本地数据库   │  │ 缓存层       │      │
│  │ Binance API │  │ SQLite/CSV  │  │ Redis       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 核心模块设计

### 1. 策略引擎 (Strategy Engine)

**职责：**
- 策略参数管理
- 信号生成逻辑
- 策略版本控制

**接口设计：**
```python
class Strategy:
    def __init__(self, params: Dict)
    def generate_signal(self, indicators: Dict) -> Signal
    def get_params(self) -> Dict
    def update_params(self, new_params: Dict)
```

**策略参数结构：**
```json
{
    "strategy_id": "v23",
    "name": "高频策略 v23",
    "timeframe": "15m",
    "symbols": ["BTCUSDT", "ETHUSDT", "LINKUSDT", "UNIUSDT"],
    "params": {
        "awr": 80, "aj": 20, "arsi": 40,
        "bwr": 65, "bj": 25, "brsi": 45,
        "cwr": 60, "cj": 35,
        "ap": 1.0, "bp": 0.8, "cp": 0.6,
        "trail": 0.04
    },
    "risk": {
        "max_position": 0.2,
        "max_loss_per_trade": 0.02,
        "max_daily_loss": 0.05
    }
}
```

---

### 2. 回测引擎 (Backtest Engine)

**职责：**
- 历史数据加载
- 策略回测执行
- 性能指标计算
- 结果可视化数据生成

**关键指标：**
- 年化收益 (Annual Return)
- 最大回撤 (Max Drawdown)
- 夏普比率 (Sharpe Ratio)
- 胜率 (Win Rate)
- 盈亏比 (Profit Factor)
- 交易次数 (Total Trades)

**回测结果结构：**
```json
{
    "strategy_id": "v23",
    "symbol": "ETHUSDT",
    "timeframe": "15m",
    "period": "2019-01-01 to 2026-03-08",
    "stats": {
        "annual_return": 974.30,
        "total_return": 10701.07,
        "max_drawdown": 15.2,
        "sharpe_ratio": 2.15,
        "win_rate": 45.5,
        "profit_factor": 3.2,
        "total_trades": 1234
    },
    "trades": [...],
    "equity_curve": [...]
}
```

---

### 3. 信号引擎 (Signal Engine)

**职责：**
- 实时数据获取
- 指标计算
- 信号生成
- 信号推送

**信号结构：**
```json
{
    "signal_id": "sig_20260308_020000_ETHUSDT",
    "timestamp": "2026-03-08T02:00:00Z",
    "symbol": "ETHUSDT",
    "timeframe": "15m",
    "type": "long",  // long/short
    "grade": "A",    // A/B/C
    "strength": 0.95,
    "indicators": {
        "wr21": -85.5,
        "j9": 15.2,
        "rsi7": 32.1
    },
    "suggested_action": {
        "action": "open",  // open/close/add/reduce
        "position_size": 0.2,
        "entry_price": 2000.0,
        "stop_loss": 1950.0,
        "take_profit": 2100.0
    }
}
```

---

### 4. 风险管理 (Risk Manager)

**职责：**
- 仓位控制
- 止损管理
- 资金管理
- 风险控制

**风险控制规则：**
```python
class RiskManager:
    # 单笔交易最大亏损
    max_loss_per_trade = 0.02  # 2%
    
    # 每日最大亏损
    max_daily_loss = 0.05  # 5%
    
    # 最大仓位
    max_position = 0.2  # 20%
    
    # 最大总仓位
    max_total_position = 0.6  # 60%
    
    def check_trade(self, signal: Signal, current_position: float) -> bool:
        # 检查是否超过日亏损限制
        if self.daily_loss > self.max_daily_loss:
            return False
        
        # 检查是否超过仓位限制
        if current_position + signal.suggested_action.position_size > self.max_position:
            return False
        
        return True
```

---

### 5. 订单执行 (Order Executor)

**职责：**
- 连接币安 API
- 订单提交
- 订单状态跟踪
- 成交记录保存

**币安 API 集成：**
```python
class BinanceExecutor:
    def __init__(self, api_key: str, api_secret: str):
        self.client = Client(api_key, api_secret)
    
    def open_position(self, symbol: str, side: str, quantity: float):
        """开仓"""
        order = self.client.futures_create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        return order
    
    def close_position(self, symbol: str, quantity: float):
        """平仓"""
        order = self.client.futures_create_order(
            symbol=symbol,
            side='SELL' if self.position_side == 'long' else 'BUY',
            type='MARKET',
            quantity=quantity,
            reduceOnly=True
        )
        return order
    
    def set_stop_loss(self, symbol: str, side: str, price: float, quantity: float):
        """设置止损"""
        order = self.client.futures_create_order(
            symbol=symbol,
            side=side,
            type='STOP_MARKET',
            stopPrice=price,
            quantity=quantity
        )
        return order
```

---

## 🔄 交易流程

### 回测流程
```
1. 选择策略参数
   ↓
2. 加载历史数据
   ↓
3. 执行回测
   ↓
4. 计算性能指标
   ↓
5. 显示回测结果
   ↓
6. 优化参数（可选）
```

### 实盘流程
```
1. 选择已验证策略
   ↓
2. 设置风险参数
   ↓
3. 启动实时信号监控
   ↓
4. 生成交易信号
   ↓
5. 风险检查
   ↓
6. 执行订单
   ↓
7. 监控持仓
   ↓
8. 平仓/止损
```

---

## 📁 数据库设计

### 策略表 (strategies)
```sql
CREATE TABLE strategies (
    id INTEGER PRIMARY KEY,
    strategy_id TEXT UNIQUE,
    name TEXT,
    params TEXT,
    risk_params TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    backtest_stats TEXT
);
```

### 信号表 (signals)
```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY,
    signal_id TEXT UNIQUE,
    timestamp TIMESTAMP,
    symbol TEXT,
    type TEXT,
    grade TEXT,
    indicators TEXT,
    action TEXT,
    status TEXT,
    created_at TIMESTAMP
);
```

### 交易记录表 (trades)
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    trade_id TEXT UNIQUE,
    signal_id TEXT,
    symbol TEXT,
    side TEXT,
    entry_price REAL,
    exit_price REAL,
    quantity REAL,
    pnl REAL,
    pnl_pct REAL,
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    status TEXT
);
```

### 持仓表 (positions)
```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    symbol TEXT UNIQUE,
    side TEXT,
    quantity REAL,
    entry_price REAL,
    current_price REAL,
    unrealized_pnl REAL,
    stop_loss REAL,
    take_profit REAL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 🌐 前端看板设计

### 页面结构
```
/dashboard           - 主仪表板（总览）
/strategies          - 策略管理
  /backtest         - 回测界面
  /live            - 实盘监控
/trading           - 交易界面
  /signals         - 信号列表
  /positions       - 持仓管理
  /history         - 交易历史
/settings          - 系统设置
  /api_keys        - API 密钥管理
  /risk            - 风险参数
```

### 实时数据推送
```javascript
// WebSocket 连接
const ws = new WebSocket('ws://localhost:5000/ws/signals');

ws.onmessage = (event) => {
    const signal = JSON.parse(event.data);
    updateSignalDisplay(signal);
};

// 获取实时价格
setInterval(() => {
    fetch('/api/prices')
        .then(r => r.json())
        .then(data => updatePriceDisplay(data));
}, 5000);
```

---

## 🚀 实施计划

### 阶段 1：回测系统完善（本周）
- [x] 回测引擎修复（与 v23 一致）
- [x] 币安 API 数据获取
- [ ] 策略参数管理界面
- [ ] 回测结果可视化
- [ ] 策略优化功能

### 阶段 2：信号系统（下周）
- [ ] 实时信号生成
- [ ] 信号推送 WebSocket
- [ ] 信号历史记录
- [ ] 信号准确率统计

### 阶段 3：实盘交易（下周）
- [ ] 币安 API 集成
- [ ] 订单执行模块
- [ ] 持仓管理
- [ ] 止损/止盈自动执行

### 阶段 4：风险管理（下周）
- [ ] 仓位控制
- [ ] 日亏损限制
- [ ] 风险参数配置
- [ ] 风险告警

### 阶段 5：系统集成（下周）
- [ ] 前端看板完善
- [ ] 数据库集成
- [ ] 日志系统
- [ ] 监控告警

---

## ⚠️ 安全考虑

### API 密钥安全
- 密钥加密存储
- 环境变量隔离
- 访问权限控制

### 交易安全
- 最大仓位限制
- 止损强制设置
- 异常交易检测

### 系统安全
- 输入验证
- SQL 注入防护
- XSS 防护

---

**设计完成时间：** 2026-03-08 02:00  
**下一步：** 开始实施阶段 1
