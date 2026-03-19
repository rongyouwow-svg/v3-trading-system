# 🦞 龙虾王牛熊拐点判断系统

## 概述

`market_turning_point_detector.py` 是一个综合性的市场拐点判断系统，通过多维度指标分析来识别加密货币市场的牛市顶部和熊市底部。

## 核心功能

### 1. 技术面拐点分析
- **月线 RSI**: 识别长期超买/超卖
- **周线 RSI**: 识别中期趋势转折
- **BTC 优势指数 (BTC.D)**: 资金流向判断

### 2. 链上拐点分析
- **MVRV (Market Value to Realized Value)**: 市值与实现价值比
- **NUPL (Net Unrealized Profit/Loss)**: 未实现盈亏净值
- **Puell Multiple**: 矿工收入指标

### 3. 成本面拐点分析
- **实现价格 (Realized Price)**: 市场平均成本
- **Mayer Multiple**: 价格与 200 日均线比
- **平均持仓成本**: 投资者平均成本

### 4. 情绪面拐点分析
- **恐慌贪婪指数**: 市场情绪量化
- **资金费率**: 合约市场情绪
- **持仓量变化**: 杠杆水平监控

### 5. 综合评分系统
- 四维加权评分（技术 25% + 链上 30% + 成本 25% + 情绪 20%）
- 信号分级：强烈买入/买入/中性/卖出/强烈卖出
- 置信度计算
- 智能操作建议

## 使用方法

### 基础用法

```python
from market_turning_point_detector import MarketTurningPointDetector

detector = MarketTurningPointDetector()

# 分析单个币种
result = detector.detect_turning_point('BTCUSDT')

# 生成报告
report = detector.generate_report(result)
print(report)

# 保存报告
detector.save_report(result)
```

### 批量分析

```python
# 分析多个币种
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
results = detector.analyze_multiple_symbols(symbols)

# 查看结果
for symbol, result in results.items():
    print(f"{symbol}: {result.overall_signal.value} (评分：{result.overall_score:.1f})")
```

### 命令行运行

```bash
# 分析 BTC 并生成报告
cd ~/.openclaw/workspace/quant && python3 market_turning_point_detector.py

# 报告保存在 logs/turning_point_YYYYMMDD_HHMMSS.json
```

## 信号说明

| 信号类型 | 分数范围 | 含义 | 建议操作 |
|---------|---------|------|---------|
| 🟢🟢 STRONG_BUY | ≥70 | 强烈买入 | 历史大底，分批建仓 |
| 🟢 BUY | 40-69 | 买入 | 风险收益比好，逐步建仓 |
| 🟡 NEUTRAL | -20~39 | 中性 | 观望为主 |
| 🔴 SELL | -50~-21 | 卖出 | 建议减仓，锁定利润 |
| 🔴🔴 STRONG_SELL | ≤-50 | 强烈卖出 | 历史大顶，清仓或做空 |

## 评分逻辑

### 熊市底部特征
- 月线 RSI < 40
- 周线 RSI < 35
- MVRV < 1.0
- NUPL < -0.25
- Puell Multiple < 0.8
- 恐慌贪婪 < 25
- 资金费率 < 0

### 牛市顶部特征
- 月线 RSI > 70
- 周线 RSI > 65
- MVRV > 4.0
- NUPL > 0.5
- Puell Multiple > 2.0
- 恐慌贪婪 > 75
- 资金费率 > 0.001

## 置信度计算

置信度基于三个因素：
1. **指标数量** (30%): 使用的指标越多，置信度越高
2. **指标一致性** (40%): 各指标方向越一致，置信度越高
3. **极端值数量** (30%): 极端信号越多，置信度越高

## 输出格式

### JSON 报告结构

```json
{
  "timestamp": "2026-03-04T11:51:44",
  "overall_signal": "neutral",
  "overall_score": 38.9,
  "technical_score": 18.0,
  "on_chain_score": 70.5,
  "cost_score": 80.8,
  "sentiment_score": -34.5,
  "confidence": 79.6,
  "recommendation": "🦞 观望为主，等待更明确信号",
  "indicators": [
    {
      "name": "月线 RSI",
      "category": "technical",
      "value": 40.42,
      "signal": "buy",
      "score": 50.0,
      "weight": 0.4,
      "description": "月线 RSI=40.4 超卖，接近底部"
    }
  ]
}
```

## 集成到现有系统

### 与主程序集成

```python
# 在 main.py 中添加
from market_turning_point_detector import MarketTurningPointDetector

def run_turning_point_analysis():
    detector = MarketTurningPointDetector()
    
    # 分析核心币种
    core_coins = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']
    results = detector.analyze_multiple_symbols([c + 'USDT' for c in core_coins])
    
    # 保存结果
    output_file = Path(config.BACKTEST_DIR) / 'turning_point_analysis.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': {s: r.to_dict() for s, r in results.items()}
        }, f, ensure_ascii=False, indent=2)
    
    return results
```

### 定时任务

```bash
# 添加到 crontab，每周日运行一次
0 23 * * 0 cd ~/.openclaw/workspace/quant && python3 market_turning_point_detector.py
```

## 注意事项

1. **数据依赖**: 需要 `data/` 目录中有足够的历史 K 线数据
2. **链上数据**: 当前使用模拟数据，实际部署应接入 Glassnode/CryptoQuant API
3. **情绪数据**: 恐慌贪婪指数应接入 Alternative.me API
4. **权重调整**: 可根据市场变化调整各维度权重（`self.weights`）
5. **阈值优化**: 阈值参数（`self.thresholds`）应定期回测优化

## 扩展方向

1. **实时数据接入**: 连接 CoinGecko、Glassnode、Alternative.me 等 API
2. **机器学习增强**: 使用历史拐点数据训练分类模型
3. **多时间周期**: 增加日线/4 小时级别的短期拐点判断
4. **回测验证**: 对历史拐点进行回测，验证策略有效性
5. **警报系统**: 当检测到拐点时自动发送通知

## 示例输出

```
============================================================
🦞 龙虾王牛熊拐点判断报告
============================================================
时间：2026-03-04 11:51:44
综合信号：NEUTRAL
综合评分：38.9 / 100
置信度：79.6%

【各维度评分】
  技术面：18.0
  链上面：70.5
  成本面：80.8
  情绪面：-34.5

【详细指标】

  技术面:
    🟢 月线 RSI: 40.42 (月线 RSI=40.4 超卖，接近底部)
    🟡 周线 RSI: 52.13 (周线 RSI=52.1 中性)
    🟡 BTC 优势：46.96 (BTC 优势=47.0% 中性)

  链上面:
    🟢🟢 MVRV: 0.69 (MVRV=0.69 极度低估，历史大底)
    🟢 NUPL: -0.44 (NUPL=-0.44 恐慌区域)
    🟢 Puell Multiple: 0.69 (Puell=0.69 矿工压力大)

  成本面:
    🟢🟢 实现价格比：0.71 (价格/实现价格=0.71 远低于成本，大底)
    🟢🟢 Mayer Multiple: 0.71 (Mayer=0.71 远低于 200 日均线)
    🟢🟢 持仓成本比：0.69 (价格/持仓成本=0.69 深度套牢区)

  情绪面:
    🟡 恐慌贪婪：51.80 (恐慌贪婪=52 中性)
    🔴 资金费率：0.0009 (资金费率=0.09% 极高)
    🔴 持仓量变化：0.13 (持仓量变化=13.3% 杠杆增加)

【操作建议】
  🦞 观望为主，等待更明确信号
============================================================
```

---

**🦞 龙虾王量化 · 让数据说话**
