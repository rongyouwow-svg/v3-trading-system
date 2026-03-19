# 🦞 龙虾王牛熊判断框架使用指南

## 框架概述

完整的加密货币市场情境判断系统，包含 6 大核心模块：

1. **BTC 独立判断** - 市场锚点，所有币种的基准
2. **ETH 动态权重** - 60% 自身 + 40% BTC（根据市场状态调整）
3. **山寨币分类** - 主流/ETH 生态/公链/Meme/RWA
4. **Meme 币资金面** - 持仓量 + 资金费率判断
5. **RWA 独立框架** - 基本面驱动的判断逻辑
6. **综合信号输出** - 统一接口生成报告

---

## 快速开始

### 1. 基础使用

```python
from market_regime_framework import MarketRegimeFramework

# 初始化框架
framework = MarketRegimeFramework()

# 加载数据
btc_df = framework._load_data('BTCUSDT')
eth_df = framework._load_data('ETHUSDT')

# 分析 BTC
btc_regime = framework.analyze_btc(btc_df)
print(f"BTC: {btc_regime.regime} (confidence: {btc_regime.confidence:.2f})")

# 分析 ETH（考虑 BTC 影响）
eth_regime = framework.analyze_eth(eth_df, btc_df)
print(f"ETH: {eth_regime.regime} (confidence: {eth_regime.confidence:.2f})")
```

### 2. 分析山寨币

```python
# 自动识别币种分类并应用相应判断逻辑
for symbol in ['SOLUSDT', 'UNIUSDT', 'DOGEUSDT', 'ONDOUSDT']:
    df = framework._load_data(symbol)
    regime = framework.analyze_altcoin(symbol, df, btc_df, eth_df)
    
    # 获取分类
    category = framework.altcoin_analyzer.get_category(symbol)
    
    print(f"{symbol} ({category}): {regime.regime}")
```

### 3. Meme 币资金面分析

```python
# 需要提供持仓量和资金费率数据
meme_analysis = framework.analyze_meme_funds(
    symbol='PEPEUSDT',
    open_interest=500_000_000,      # 持仓量 (USDT)
    oi_change_24h=25.5,             # 24h 变化 (%)
    funding_rate=0.008,             # 资金费率
    funding_rate_8h_avg=0.006,      # 8h 平均资金费率
    long_short_ratio=1.8            # 多空比
)

print(f"情绪：{meme_analysis.sentiment}")
print(f"过热：{meme_analysis.overheated}")

# 获取交易信号
signal = framework.meme_analyzer.get_trading_signal(meme_analysis)
print(f"信号：{signal}")
```

### 4. RWA 代币分析

```python
# RWA 需要基本面数据
ondo_df = framework._load_data('ONDOUSDT')

rwa_analysis = framework.analyze_rwa(
    symbol='ONDOUSDT',
    tvl=800_000_000,           # TVL (USDT)
    tvl_change_7d=12.5,        # 7 天 TVL 变化 (%)
    tvl_change_30d=35.0,       # 30 天 TVL 变化 (%)
    revenue_30d=5_000_000,     # 30 天收入 (USDT)
    revenue_change_30d=25.0,   # 收入变化 (%)
    market_cap=1_200_000_000,  # 市值 (USDT)
    df=ondo_df                 # K 线数据
)

print(f"牛熊判断：{rwa_analysis.regime}")
print(f"基本面得分：{rwa_analysis.fundamentals_score:.1f}/100")
print(f"市值/TVL 比率：{rwa_analysis.price_to_tvl_ratio:.4f}")
```

### 5. 生成完整报告

```python
# 生成多币种报告
report = framework.generate_report([
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 
    'UNIUSDT', 'DOGEUSDT', 'ONDOUSDT'
])

# 保存为 JSON
import json
with open('market_regime_report.json', 'w') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
```

---

## 币种分类体系

框架内置了完整的币种分类：

```python
ALTCOIN_CATEGORIES = {
    'MAINSTREAM': ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOT', 'LINK', 'MATIC'],
    'ETH_ECOSYSTEM': ['UNI', 'AAVE', 'MKR', 'SNX', 'CRV', 'LDO', 'RPL', 'PEPE', 'SHIB', 'ARB', 'OP'],
    'L1_CHAINS': ['SOL', 'AVAX', 'NEAR', 'FTM', 'ALGO', 'ATOM', 'OSMO', 'INJ', 'SUI', 'APT'],
    'MEME': ['DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BONK', 'WIF', 'BOME', 'MEME', 'POPCAT', 'BRETT'],
    'RWA': ['ONDO', 'MKR', 'PENDLE', 'GLP', 'GNS', 'LINK', 'AAVE', 'CRV', 'COMP', 'YFI'],
    'DEFI': ['UNI', 'AAVE', 'MKR', 'SNX', 'CRV', 'COMP', 'SUSHI', 'BAL', 'YFI', '1INCH'],
    'L2': ['ARB', 'OP', 'MATIC', 'IMX', 'METIS', 'BOBA', 'OPTIMISM', 'ARBITRUM'],
}
```

---

## 各类别判断逻辑

### 主流币 (MAINSTREAM)
- **权重**: 自身技术面 50% + BTC 影响 50%
- **特点**: 与 BTC 高度相关，跟随大盘

### ETH 生态 (ETH_ECOSYSTEM)
- **权重**: 自身技术面 30% + ETH 影响 70%
- **特点**: 强依赖 ETH 走势，如 UNI、AAVE、LDO

### 公链 (L1_CHAINS)
- **权重**: 自身技术面 60% + BTC 影响 40%
- **特点**: 有一定独立性，如 SOL、AVAX、NEAR

### Meme 币 (MEME)
- **判断**: 资金面驱动（持仓量 + 资金费率）
- **特点**: 情绪化严重，容易过热

### RWA (RWA)
- **权重**: 基本面 70% + 技术面 30%
- **判断维度**: TVL、协议收入、市值/TVL 比率
- **特点**: 走势独立，注重实际价值

---

## BTC 判断维度

BTC 作为市场锚点，使用多维度评分：

| 维度 | 权重 | 指标 |
|------|------|------|
| 趋势 | 40% | 均线排列、价格相对 200 日均线、30 天价格变化 |
| 动量 | 30% | RSI、MACD、10 天价格动量 |
| 成交量 | 20% | 成交量相对均线、成交量趋势 |
| 波动率 | 10% | ATR 相对历史水平 |

**判断阈值**:
- 总分 > 0.6: 牛市
- 总分 < -0.6: 熊市
- -0.3 < 总分 < 0.3: 震荡
- 其他: 混合

---

## ETH 动态权重机制

ETH 判断根据市场状态动态调整权重：

| BTC 市场状态 | ETH 权重 | BTC 权重 | 说明 |
|-------------|---------|---------|------|
| 强牛/强熊 (|得分| > 0.7) | 50% | 50% | 极端市场，BTC 主导 |
| 明显趋势 (0.4 < |得分| < 0.7) | 60% | 40% | 标准权重 |
| 震荡市 (|得分| < 0.4) | 70% | 30% | ETH 自身因素更重要 |

**额外调整**: ETH/BTC 汇率走势会影响最终置信度。

---

## Meme 币资金面判断

### 情绪判断标准

| 条件 | 情绪 |
|------|------|
| 多空比 > 2.0 且 资金费率 > 1% | 极度多头 (extreme_long) |
| 多空比 > 1.5 且 资金费率 > 0.5% | 多头 (long) |
| 多空比 < 0.5 且 资金费率 < -1% | 极度空头 (extreme_short) |
| 多空比 < 0.67 且 资金费率 < -0.5% | 空头 (short) |
| 其他 | 中性 (neutral) |

### 过热判断

同时满足以下条件视为过热：
- 24h 持仓量增长 > 50%
- 资金费率绝对值 > 2%

### 交易信号

| 情况 | 信号 |
|------|------|
| 多头过热 | 强烈做空 (strong_short) |
| 空头过热 | 强烈做多 (strong_long) |
| 多头 + 持仓量增 > 20% | 强烈做多 (strong_long) |
| 空头 + 持仓量增 > 20% | 强烈做空 (strong_short) |

---

## RWA 基本面评分

### 评分标准 (满分 100)

| 维度 | 分值 | 评分标准 |
|------|------|----------|
| TVL 规模 | 20 分 | >10 亿=20 分，>5 亿=15 分，>1 亿=10 分 |
| TVL 增长 | 30 分 | 7 天>20% 且 30 天>30%=30 分 |
| 协议收入 | 20 分 | >1000 万=20 分，>500 万=15 分 |
| 收入增长 | 20 分 | >50%=20 分，>20%=15 分 |
| 市值/TVL | 10 分 | 0.5-2.0=10 分，0.3-3.0=5 分 |

### 牛熊判断

- 综合得分 > 0.65: 牛市
- 综合得分 < 0.35: 熊市
- 其他: 震荡

---

## 数据结构

### MarketRegime

```python
@dataclass
class MarketRegime:
    symbol: str              # 币种符号
    regime: str              # 'bull', 'bear', 'sideways', 'mixed'
    confidence: float        # 0.0 - 1.0
    trend_strength: float    # -1.0 (强熊) to 1.0 (强牛)
    volatility: str          # 'low', 'medium', 'high'
    volume_trend: str        # 'increasing', 'decreasing', 'neutral'
    timestamp: datetime      # 时间戳
```

### MemeAnalysis

```python
@dataclass
class MemeAnalysis:
    symbol: str              # 币种符号
    open_interest: float     # 持仓量 (USDT)
    oi_change_24h: float     # 24h 变化 (%)
    funding_rate: float      # 资金费率
    funding_rate_avg_8h: float  # 8h 平均
    long_short_ratio: float  # 多空比
    sentiment: str           # 情绪
    overheated: bool         # 是否过热
```

### RWAAnalysis

```python
@dataclass
class RWAAnalysis:
    symbol: str              # 币种符号
    tvl: float               # 总锁仓价值
    tvl_change_7d: float     # 7 天变化 (%)
    revenue: float           # 30 天收入
    revenue_change_30d: float  # 收入变化 (%)
    token_price: float       # 币价
    price_to_tvl_ratio: float  # 市值/TVL
    fundamentals_score: float  # 基本面得分 (0-100)
    regime: str              # 牛熊判断
```

---

## 集成到现有系统

### 与 main.py 集成

```python
# 在 main.py 中添加
from market_regime_framework import MarketRegimeFramework

def daily_analysis():
    framework = MarketRegimeFramework()
    
    # 收集数据
    collector = DataCollector()
    collector.update_all_data()
    
    # 生成市场情境报告
    report = framework.generate_report(config.CORE_COINS)
    
    # 保存到文件
    with open('dashboard/data/market_regime.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    return report
```

### 与看板集成

在看板中添加市场情境展示：

```html
<div id="market-regime">
  <h3>🦞 市场情境</h3>
  <div id="btc-regime">BTC: --</div>
  <div id="eth-regime">ETH: --</div>
  <div id="overall-regime">整体: --</div>
</div>

<script>
async function loadMarketRegime() {
  const response = await fetch('/api/market_regime');
  const data = await response.json();
  
  document.getElementById('btc-regime').textContent = 
    `BTC: ${data.btc.regime} (${(data.btc.confidence * 100).toFixed(0)}%)`;
  
  document.getElementById('eth-regime').textContent = 
    `ETH: ${data.eth.regime} (${(data.eth.confidence * 100).toFixed(0)}%)`;
  
  document.getElementById('overall-regime').textContent = 
    `整体: ${data.overall.regime}`;
}
</script>
```

---

## 注意事项

1. **数据质量**: 确保 K 线数据至少有 50 条记录
2. **Meme 数据**: 持仓量和资金费率需要接入交易所 API
3. **RWA 数据**: TVL 和收入数据需要接入 DeFiLlama 等数据源
4. **性能**: 批量分析时建议并行处理
5. **更新频率**: 建议每 30 分钟更新一次（与 K 线周期一致）

---

## 扩展建议

1. **接入实时数据**: 连接 Binance API 获取实时持仓量和资金费率
2. **机器学习**: 使用历史数据训练分类模型优化判断
3. **链上数据**: 整合链上数据（如大额转账、交易所流入流出）
4. **社交媒体**: 加入社交媒体情绪分析
5. **回测验证**: 回测框架判断的准确性

---

_🦞 龙虾王量化团队 | 2026-03-04_
