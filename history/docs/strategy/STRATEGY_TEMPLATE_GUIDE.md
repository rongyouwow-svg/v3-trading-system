# 🦞 龙虾王策略模板系统使用指南

> 策略模板系统提供完整的策略定义、导入导出、验证和管理功能，让策略配置标准化、可复用。

---

## 一、快速开始

### 1.1 创建第一个策略

```bash
cd ~/.openclaw/workspace/quant

# 创建一个突破策略模板
python3 strategy_io.py create \
  --name "我的突破策略" \
  --category breakout \
  --base-size 0.30 \
  --stop-loss 0.05 \
  --take-profit 3.0 \
  --risk 0.02
```

### 1.2 查看策略库

```bash
# 列出所有策略
python3 strategy_io.py list

# 按类别筛选
python3 strategy_io.py list --category breakout

# 按标签筛选
python3 strategy_io.py list --tags "突破，多币种"
```

### 1.3 导出策略

```bash
# 导出为 JSON
python3 strategy_io.py export \
  --name "我的突破策略" \
  --version "1.0.0" \
  --output ./my_strategy.json

# 导出为 YAML
python3 strategy_io.py export \
  --name "我的突破策略" \
  --version "1.0.0" \
  --output ./my_strategy.yaml \
  --format yaml
```

### 1.4 导入策略

```bash
# 导入策略
python3 strategy_io.py import --file ./my_strategy.json

# 覆盖已存在的策略
python3 strategy_io.py import --file ./my_strategy.json --overwrite
```

---

## 二、策略配置结构

### 2.1 完整策略配置示例

```json
{
  "metadata": {
    "name": "龙虾王激进突破策略",
    "version": "3.0.0",
    "description": "冲击 100% 年化的激进突破策略",
    "author": "龙虾王",
    "category": "breakout",
    "tags": ["突破", "趋势跟踪", "多币种"]
  },
  "scope": {
    "market_regimes": ["bull", "sideways"],
    "coin_tiers": ["major", "mid"],
    "timeframes": ["1h", "4h"],
    "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
  },
  "entry": {
    "type": "breakout",
    "min_score": 75,
    "required_confirmations": 4,
    "indicators": [
      {"name": "EMA", "parameters": {"span": 20}, "weight": 15},
      {"name": "RSI", "parameters": {"period": 14}, "weight": 20},
      {"name": "MACD", "parameters": {"fast": 12, "slow": 26, "signal": 9}, "weight": 15},
      {"name": "Volume", "parameters": {"ma_period": 20}, "weight": 25}
    ],
    "thresholds": {
      "rsi_long_min": 50,
      "rsi_long_max": 75,
      "volume_ratio_min": 2.0
    }
  },
  "exit": {
    "stop_loss": {
      "type": "atr",
      "atr_multiplier": 1.5,
      "max_pct": 0.12,
      "min_pct": 0.05
    },
    "take_profit": {
      "type": "rrr",
      "target_rrr": 3.0,
      "trailing": {
        "activation_rrr": 2.0,
        "trail_pct": 0.05
      },
      "partial_exit": [
        {"at_rrr": 2.0, "exit_pct": 0.30},
        {"at_rrr": 4.0, "exit_pct": 0.30}
      ]
    },
    "signal_reverse": true
  },
  "position_sizing": {
    "method": "dynamic",
    "base_size": 0.30,
    "max_size": 0.60,
    "risk_per_trade": 0.02,
    "kelly_divisor": 2.0,
    "dynamic_adjustments": {
      "trend_multiplier": 1.5,
      "volume_multiplier": 1.33,
      "conviction_multiplier": 1.2
    }
  },
  "risk_management": {
    "daily_limits": {
      "max_loss_pct": 0.05,
      "max_trades": 5
    },
    "consecutive_losses": {
      "pause_after": 3,
      "pause_duration_hours": 24,
      "reduce_size_after": 2,
      "reduction_factor": 0.5
    },
    "drawdown_control": [
      {"threshold": 0.15, "action": "reduce_50"},
      {"threshold": 0.25, "action": "reduce_75"},
      {"threshold": 0.40, "action": "stop_trading"}
    ],
    "max_positions": 3,
    "max_exposure": 1.20
  },
  "backtest": {
    "period_days": 2920,
    "initial_capital": 10000,
    "slippage": 0.001,
    "commission": 0.0004
  },
  "performance_targets": {
    "target_annual_return": 1.0,
    "max_acceptable_drawdown": 0.50,
    "min_win_rate": 0.45,
    "min_profit_factor": 2.5
  }
}
```

### 2.2 配置项说明

#### 元数据 (metadata)

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `name` | string | ✅ | 策略名称 |
| `version` | string | ✅ | 版本号 (语义化版本) |
| `description` | string | ❌ | 策略描述 |
| `author` | string | ❌ | 作者 (默认：龙虾王) |
| `category` | string | ✅ | 策略类别 |
| `tags` | array | ❌ | 标签列表 |

**策略类别:**
- `trend_following` - 趋势跟踪
- `mean_reversion` - 均值回归
- `breakout` - 突破策略
- `momentum` - 动量策略
- `arbitrage` - 套利策略

#### 适用范围 (scope)

| 字段 | 类型 | 说明 |
|-----|------|------|
| `market_regimes` | array | 适用市场状态：`bull`, `bear`, `sideways`, `crash`, `recovery`, `any` |
| `coin_tiers` | array | 适用币种等级：`major`, `mid`, `altcoin`, `meme`, `any` |
| `timeframes` | array | 适用时间周期：`1m`~`1w` |
| `symbols` | array | 具体币种列表，`*` 表示所有 |

#### 入场条件 (entry)

| 字段 | 类型 | 说明 |
|-----|------|------|
| `type` | string | 入场类型：`breakout`, `pullback`, `reversal`, `momentum` |
| `min_score` | number | 最低入场分数 (0-100) |
| `required_confirmations` | integer | 最少确认条件数 |
| `indicators` | array | 使用的技术指标 |
| `thresholds` | object | 阈值配置 |

**RSI 阈值示例:**
```json
{
  "rsi_long_min": 50,    // 做多 RSI 下限
  "rsi_long_max": 75,    // 做多 RSI 上限 (避免超买)
  "rsi_short_min": 25,   // 做空 RSI 下限
  "rsi_short_max": 50,   // 做空 RSI 上限
  "volume_ratio_min": 2.0  // 最小成交量比率
}
```

#### 出场条件 (exit)

**止损配置:**
```json
{
  "stop_loss": {
    "type": "atr",           // fixed, atr, support, time
    "atr_multiplier": 1.5,   // ATR 倍数
    "max_pct": 0.12,         // 最大止损 12%
    "min_pct": 0.05          // 最小止损 5%
  }
}
```

**止盈配置:**
```json
{
  "take_profit": {
    "type": "rrr",           // fixed, rrr, trailing, partial
    "target_rrr": 3.0,       // 目标盈亏比 3:1
    "trailing": {
      "activation_rrr": 2.0, // 盈利达 2 倍风险启动
      "trail_pct": 0.05      // 回撤 5% 止盈
    },
    "partial_exit": [        // 分阶段止盈
      {"at_rrr": 2.0, "exit_pct": 0.30},
      {"at_rrr": 4.0, "exit_pct": 0.30}
    ]
  }
}
```

#### 仓位管理 (position_sizing)

| 字段 | 类型 | 说明 | 默认值 |
|-----|------|------|--------|
| `method` | string | 计算方法：`fixed`, `kelly`, `risk_parity`, `dynamic` | `dynamic` |
| `base_size` | number | 基础仓位比例 | 0.30 |
| `max_size` | number | 最大仓位比例 | 0.60 |
| `risk_per_trade` | number | 单笔风险比例 | 0.02 |
| `kelly_divisor` | number | 凯利除数 (降低风险) | 2.0 |
| `dynamic_adjustments` | object | 动态调整因子 | - |

**动态调整因子:**
```json
{
  "trend_multiplier": 1.5,      // 强趋势×1.5
  "volume_multiplier": 1.33,    // 放量×1.33
  "conviction_multiplier": 1.2, // 高置信度×1.2
  "volatility_reduction": 0.30  // 高波动减仓 30%
}
```

#### 风险管理 (risk_management)

**单日风控:**
```json
{
  "daily_limits": {
    "max_loss_pct": 0.05,   // 单日最多亏 5%
    "max_trades": 5         // 单日最多 5 笔
  }
}
```

**连续亏损:**
```json
{
  "consecutive_losses": {
    "pause_after": 3,           // 连续 3 亏暂停
    "pause_duration_hours": 24, // 暂停 24 小时
    "reduce_size_after": 2,     // 连续 2 亏减仓
    "reduction_factor": 0.5     // 减仓 50%
  }
}
```

**回撤控制:**
```json
{
  "drawdown_control": [
    {"threshold": 0.15, "action": "reduce_50"},   // 回撤 15% 减仓 50%
    {"threshold": 0.25, "action": "reduce_75"},   // 回撤 25% 减仓 75%
    {"threshold": 0.40, "action": "stop_trading"} // 回撤 40% 停止交易
  ]
}
```

---

## 三、Python API 使用

### 3.1 创建策略

```python
from strategy_template import StrategyTemplate, StrategyMetadata, StrategyScope

# 创建策略
strategy = StrategyTemplate(
    metadata=StrategyMetadata(
        name="我的策略",
        version="1.0.0",
        category="breakout",
        description="突破策略"
    ),
    scope=StrategyScope(
        market_regimes=["bull", "sideways"],
        coin_tiers=["major", "mid"],
        timeframes=["1h", "4h"],
        symbols=["BTCUSDT", "ETHUSDT"]
    ),
    entry={
        "type": "breakout",
        "min_score": 75,
        "required_confirmations": 4
    },
    exit={
        "stop_loss": {"type": "fixed", "fixed_pct": 0.05},
        "take_profit": {"type": "rrr", "target_rrr": 3.0}
    },
    position_sizing={
        "method": "dynamic",
        "base_size": 0.30,
        "max_size": 0.60,
        "risk_per_trade": 0.02
    },
    risk_management={
        "daily_limits": {"max_loss_pct": 0.05, "max_trades": 5},
        "drawdown_control": [
            {"threshold": 0.15, "action": "reduce_50"},
            {"threshold": 0.40, "action": "stop_trading"}
        ]
    }
)

# 验证策略
if strategy.validate():
    print("✓ 策略验证通过")
    
    # 保存策略
    strategy.save("./my_strategy.json")
    
    # 显示摘要
    print(strategy.get_summary())
```

### 3.2 加载策略

```python
from strategy_template import StrategyTemplate

# 从文件加载
strategy = StrategyTemplate.from_file("./my_strategy.json")

# 从 JSON 字符串加载
json_str = '{"metadata": {...}, ...}'
strategy = StrategyTemplate.from_json(json_str)

# 从 YAML 字符串加载
yaml_str = 'metadata:\n  name: ...'
strategy = StrategyTemplate.from_yaml(yaml_str)
```

### 3.3 策略库管理

```python
from strategy_template import StrategyLibrary

# 创建策略库
library = StrategyLibrary()

# 添加策略
library.add(strategy, overwrite=True)

# 获取策略
strategy = library.get("我的策略", "1.0.0")

# 列出策略
strategies = library.list_strategies(category="breakout")

# 导出策略
library.export_strategy("我的策略", "1.0.0", "./exported.json")

# 导入策略
library.import_strategy("./imported.json", overwrite=True)

# 对比策略
comparison = library.compare_strategies([
    "策略 A@1.0.0",
    "策略 B@1.0.0"
])
```

---

## 四、策略验证规则

### 4.1 自动验证项

策略验证会自动检查以下内容:

1. **元数据完整性**
   - 名称不能为空
   - 版本号不能为空

2. **仓位合理性**
   - 基础仓位：0 < base_size ≤ 1
   - 最大仓位：0 < max_size ≤ 1
   - base_size ≤ max_size

3. **风险控制**
   - 单笔风险：0 < risk_per_trade ≤ 0.1 (10%)
   - 止损范围：0 < stop_loss ≤ 0.2 (20%)
   - 止盈范围：0 < take_profit ≤ 1 (100%)

### 4.2 验证示例

```python
strategy = StrategyTemplate.from_file("./my_strategy.json")

if strategy.validate():
    print("✓ 验证通过")
else:
    print("✗ 验证失败，请检查配置")
```

---

## 五、最佳实践

### 5.1 策略命名规范

```
{市场状态}_{币种等级}_{策略类型}_{版本}

示例:
- Bull_Major_Breakout_v3.0
- Bear_Altcoin_Short_v1.2
- Sideways_Major_Grid_v2.1
```

### 5.2 版本管理

使用语义化版本号：`主版本。次版本.修订号`

- **主版本**: 策略逻辑重大变更
- **次版本**: 参数优化，功能增强
- **修订号**: Bug 修复，小调整

### 5.3 策略分类建议

| 市场状态 | 推荐策略类型 | 仓位建议 |
|---------|------------|---------|
| 牛市 | 突破、趋势跟踪 | 30%-60% |
| 熊市 | 做空、空仓 | 10%-30% |
| 震荡 | 均值回归、网格 | 20%-40% |
| 崩盘 | 抄底、观望 | 5%-15% |

### 5.4 参数优化流程

1. **回测验证**: 使用 8 年历史数据回测
2. **参数网格搜索**: 找到最优参数组合
3. **样本外测试**: 验证参数不过拟合
4. **实盘测试**: 小资金实盘验证
5. **逐步加仓**: 确认有效后逐步增加仓位

---

## 六、常见问题

### Q1: 如何备份策略？

```bash
# 导出所有策略
python3 strategy_io.py list | while read line; do
  name=$(echo $line | awk '{print $1}')
  version=$(echo $line | awk '{print $2}')
  python3 strategy_io.py export --name "$name" --version "$version" --output "./backup/${name}_${version}.json"
done
```

### Q2: 如何分享策略？

直接分享导出的 JSON/YAML 文件即可：

```bash
# 导出策略
python3 strategy_io.py export \
  --name "我的策略" \
  --version "1.0.0" \
  --output ./my_strategy.json

# 发送文件
# 对方导入
python3 strategy_io.py import --file ./my_strategy.json
```

### Q3: 如何对比多个策略？

```bash
# 命令行对比
python3 strategy_io.py compare \
  --strategies "策略 A@1.0.0" "策略 B@1.0.0" "策略 C@1.0.0"

# Python API
library = StrategyLibrary()
comparison = library.compare_strategies([
    "策略 A@1.0.0",
    "策略 B@1.0.0"
])
```

### Q4: 策略文件存储在哪里？

默认存储在 `quant/strategies/` 目录：

```bash
ls -lh ~/.openclaw/workspace/quant/strategies/
```

---

## 七、进阶用法

### 7.1 批量导入策略

```python
from pathlib import Path
from strategy_template import StrategyLibrary

library = StrategyLibrary()

# 批量导入
for filepath in Path('./strategy_exports').glob('*.json'):
    library.import_strategy(filepath, overwrite=True)
    print(f"✓ 已导入：{filepath}")
```

### 7.2 策略参数扫描

```python
from strategy_template import StrategyTemplate, StrategyMetadata

# 参数扫描
base_sizes = [0.20, 0.30, 0.40, 0.50]
stop_losses = [0.03, 0.05, 0.08, 0.10]

for base_size in base_sizes:
    for stop_loss in stop_losses:
        strategy = StrategyTemplate(
            metadata=StrategyMetadata(
                name=f"参数扫描_{base_size}_{stop_loss}",
                version="1.0.0",
                category="breakout"
            ),
            # ... 其他配置
        )
        # 保存并回测
```

### 7.3 策略组合

```python
# 创建策略组合
portfolio = {
    "策略 A": {"weight": 0.40, "config": strategy_a},
    "策略 B": {"weight": 0.35, "config": strategy_b},
    "策略 C": {"weight": 0.25, "config": strategy_c}
}

# 总风险 = 各策略风险 × 权重
total_risk = sum(
    s["config"].position_sizing.risk_per_trade * s["weight"]
    for s in portfolio.values()
)
```

---

> 🦞 **龙虾王提示**: 策略模板是工具，不是圣杯。再好的策略也需要严格执行和持续优化！
