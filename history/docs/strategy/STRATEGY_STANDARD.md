# 🦞 量化策略标准框架 v1.0

**创建时间：** 2026-03-08  
**目的：** 统一策略格式，确保所有策略能准确导入看板并执行回测

---

## 📋 目录结构

```
quant/
├── strategies/              # 策略目录
│   ├── strategy_v23.py      # 策略实现
│   ├── strategy_v23_params.json  # 策略参数
│   └── ...
├── backtest_engine.py       # 统一回测引擎
├── strategy_params.json     # 所有策略参数汇总
└── STRATEGY_STANDARD.md     # 本规范文档
```

---

## 📝 策略参数文件格式

### 标准 JSON 结构

```json
{
    "策略 ID": {
        "name": "策略名称",
        "description": "策略描述",
        "version": "1.0.0",
        "create_date": "2026-03-08",
        "author": "作者名",
        "coins": {
            "币种": {
                "awr": 75,      // A 级 WR 阈值
                "aj": 20,       // A 级 J 值阈值
                "arsi": 40,     // A 级 RSI 阈值
                "bwr": 65,      // B 级 WR 阈值
                "bj": 25,       // B 级 J 值阈值
                "brsi": 45,     // B 级 RSI 阈值
                "cwr": 60,      // C 级 WR 阈值
                "cj": 35,       // C 级 J 值阈值
                "ap": 100,      // A 级仓位 (%)
                "bp": 80,       // B 级仓位 (%)
                "cp": 60,       // C 级仓位 (%)
                "trail": 4,     // 追踪止损 (%)
                "annual": 443.84,  // 年化收益 (%)
                "equity": 189219081.65  // 最终权益
            }
        },
        "params": {
            // 通用参数（如果不区分币种）
        }
    }
}
```

---

## 🐍 策略实现标准

### 1. 策略类结构

```python
class Strategy:
    """策略基类"""
    
    def __init__(self, params: Dict):
        """
        初始化策略
        
        Args:
            params: 策略参数字典
        """
        self.params = params
    
    def generate_signal(self, row: pd.Series) -> Optional[tuple]:
        """
        生成交易信号
        
        Args:
            row: 包含指标的数据行
        
        Returns:
            tuple: (grade, side) 或 None
            grade: 'A', 'B', 'C'
            side: 'long', 'short'
        """
        pass
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            df: OHLCV 数据
        
        Returns:
            DataFrame: 添加指标后的数据
        """
        pass
```

### 2. 指标计算标准

```python
def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # WR21 (Williams %R)
    highest_high = df['high'].rolling(21).max()
    lowest_low = df['low'].rolling(21).min()
    df['WR21'] = -100 * (highest_high - df['close']) / (highest_high - lowest_low)
    df['WR21'] = df['WR21'].fillna(0)
    
    # KDJ (J9)
    lowest_low_9 = df['low'].rolling(9).min()
    highest_high_9 = df['high'].rolling(9).max()
    rsv = (df['close'] - lowest_low_9) / (highest_high_9 - lowest_low_9) * 100
    df['K'] = rsv.ewm(com=2, adjust=False).mean()
    df['D'] = df['K'].ewm(com=2, adjust=False).mean()
    df['J9'] = 3 * df['K'] - 2 * df['D']
    df['J9'] = df['J9'].fillna(0)
    
    # RSI7
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
    rs = gain / loss
    df['RSI7'] = 100 - (100 / (1 + rs))
    df['RSI7'] = df['RSI7'].fillna(100)
    
    return df
```

### 3. 信号生成标准

```python
def generate_signal(self, row: pd.Series) -> Optional[tuple]:
    """生成交易信号（做多 + 做空）"""
    wr = row['WR21']
    j = row['J9']
    rsi = row['RSI7']
    
    p = self.params
    
    # A 级信号
    if wr < -p['awr'] and j < p['aj'] and rsi < p['arsi']:
        return ('A', 'long')
    elif wr > -p['awr']/3 and j > 100 - p['aj'] and rsi > 100 - p['arsi']:
        return ('A', 'short')
    
    # B 级信号
    if wr < -p['bwr'] and j < p['bj'] and rsi < p['brsi']:
        return ('B', 'long')
    elif wr > -p['bwr']/3 and j > 100 - p['bj'] and rsi > 100 - p['brsi']:
        return ('B', 'short')
    
    # C 级信号
    if wr < -p['cwr'] and j < p['cj']:
        return ('C', 'long')
    elif wr > -p['cwr']/3 and j > 100 - p['cj']:
        return ('C', 'short')
    
    return None
```

---

## 🔧 回测引擎标准

### 1. 回测引擎接口

```python
class BacktestEngine:
    """统一回测引擎"""
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.reset()
    
    def run(self, df: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        """
        运行回测
        
        Args:
            df: OHLCV 数据
            strategy: 策略实例
        
        Returns:
            BacktestResult: 回测结果
        """
        pass
```

### 2. 回测结果标准

```python
@dataclass
class BacktestResult:
    """回测结果"""
    total_return: float      # 总收益 (%)
    annual_return: float     # 年化收益 (%)
    sharpe_ratio: float      # 夏普比率
    max_drawdown: float      # 最大回撤 (%)
    total_trades: int        # 交易次数
    winning_trades: int      # 盈利交易数
    win_rate: float          # 胜率 (%)
    avg_win: float           # 平均盈利
    avg_loss: float          # 平均亏损
    profit_factor: float     # 盈亏比
    final_equity: float      # 最终权益
    trades: List[Trade]      # 交易记录
    equity_curve: List[float] # 权益曲线
    grade_stats: Dict[str, Dict] # 分级统计
```

---

## 🌐 看板集成标准

### 1. 策略参数加载

```javascript
// 从 JSON 文件加载策略参数
async function loadStrategyParams() {
    const response = await fetch('/api/strategies');
    const data = await response.json();
    return data.strategies;
}

// 根据币种获取参数
function getStrategyParams(strategyId, coin) {
    const strategy = strategies[strategyId];
    if (strategy.coins && strategy.coins[coin]) {
        return strategy.coins[coin];
    }
    return strategy.params; // 返回通用参数
}
```

### 2. 回测 API 调用

```javascript
// 调用回测 API
async function runBacktest(coin, timeframe, strategyId, params) {
    const response = await fetch('/api/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            symbol: coin,
            timeframe: timeframe,
            strategy: strategyId,
            params: params
        })
    });
    return await response.json();
}
```

---

## ✅ 策略导入检查清单

导入新策略前，确保完成以下步骤：

- [ ] 创建策略参数 JSON 文件
- [ ] 实现策略类（继承 Strategy 基类）
- [ ] 实现 `calculate_indicators()` 方法
- [ ] 实现 `generate_signal()` 方法
- [ ] 添加策略到 `strategy_params.json`
- [ ] 测试回测引擎与策略的兼容性
- [ ] 验证看板能正确显示策略参数
- [ ] 对比回测结果与优化结果（差异<5%）
- [ ] 更新策略文档

---

## 📊 策略参数命名规范

| 参数名 | 含义 | 类型 | 范围 |
|--------|------|------|------|
| `awr` | A 级 WR 阈值 | int | 50-90 |
| `aj` | A 级 J 值阈值 | int | 10-30 |
| `arsi` | A 级 RSI 阈值 | int | 30-50 |
| `bwr` | B 级 WR 阈值 | int | 50-90 |
| `bj` | B 级 J 值阈值 | int | 15-35 |
| `brsi` | B 级 RSI 阈值 | int | 35-55 |
| `cwr` | C 级 WR 阈值 | int | 50-90 |
| `cj` | C 级 J 值阈值 | int | 20-40 |
| `ap` | A 级仓位 | int | 50-100 (%) |
| `bp` | B 级仓位 | int | 40-90 (%) |
| `cp` | C 级仓位 | int | 30-80 (%) |
| `trail` | 追踪止损 | int | 3-10 (%) |

---

## 🎯 示例：导入新策略 v24

### 1. 创建策略参数文件

```json
{
    "v24": {
        "name": "高频策略 v24 (优化版)",
        "description": "v23 的优化版本",
        "coins": {
            "BTCUSDT": {
                "awr": 75, "aj": 20, "arsi": 40,
                "bwr": 65, "bj": 25, "brsi": 40,
                "cwr": 60, "cj": 35,
                "ap": 100, "bp": 80, "cp": 60,
                "trail": 4,
                "annual": 500.00,
                "equity": 200000000.00
            }
        }
    }
}
```

### 2. 更新看板策略列表

```javascript
const strategies = {
    'v23': { ... },
    'v24': { ... }  // 新增策略
};
```

### 3. 测试验证

```bash
# 运行回测测试
python3 test_strategy_v24.py

# 对比结果
# backtest_engine.py: $200,000,000
# 优化脚本：$200,000,000
# 差异：< 5% ✅
```

---

**最后更新：** 2026-03-08  
**维护者：** 龙虾王量化团队
