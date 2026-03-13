-- 大王量化交易系统 v3.0
-- 初始数据库迁移
-- 创建时间：2026-03-13

-- ==================== 策略表 ====================
CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    strategy_id TEXT NOT NULL,
    strategy_name TEXT,
    side TEXT NOT NULL,
    leverage INTEGER DEFAULT 1,
    amount REAL DEFAULT 0,
    status TEXT DEFAULT 'running',
    start_time DATETIME,
    stop_time DATETIME,
    entry_price REAL,
    current_price REAL,
    position_size REAL,
    pnl REAL DEFAULT 0,
    pnl_pct REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_strategies_symbol ON strategies(symbol);
CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);

-- ==================== 订单表 ====================
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE,
    strategy_id INTEGER,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    type TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL,
    avg_price REAL,
    filled_quantity REAL DEFAULT 0,
    status TEXT DEFAULT 'PENDING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);

CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);

-- ==================== 止损单表 ====================
CREATE TABLE IF NOT EXISTS stop_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    algo_id TEXT UNIQUE,
    strategy_id INTEGER,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    trigger_price REAL NOT NULL,
    quantity REAL NOT NULL,
    status TEXT DEFAULT 'WAIT_TO_TRIGGER',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    triggered_at DATETIME,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);

CREATE INDEX IF NOT EXISTS idx_stop_orders_symbol ON stop_orders(symbol);

-- ==================== 成交表 ====================
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT UNIQUE,
    order_id TEXT,
    strategy_id INTEGER,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    commission REAL DEFAULT 0,
    commission_asset TEXT DEFAULT 'USDT',
    realized_pnl REAL DEFAULT 0,
    trade_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);

CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy_id);

-- ==================== 状态快照表 ====================
CREATE TABLE IF NOT EXISTS state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_type TEXT NOT NULL,
    snapshot_data TEXT NOT NULL,
    version INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
