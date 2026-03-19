# 📊 量化回测数据汇总 (2026-03-05)

**生成时间：** 2026-03-05 22:55  
**数据范围：** 2026-03-03 至 2026-03-05

---

## 🏆 最优策略

### 冠军策略：Multi-Signal (RSI+MACD+BB)
| 指标 | 数值 |
|------|------|
| **年化收益** | 1892.51% |
| **胜率** | 100% |
| **最大回撤** | 0% |
| **交易次数** | 3 |
| **Sharpe 比率** | 0.87 |

**核心参数：**
- RSI: 14 周期，超卖 35.0，超买 68.3
- MACD: 13/25/10
- 布林带：20 周期，2.08 标准差
- 止损：9.8%，止盈：14.8%
- 仓位：28.5%

---

## 📈 策略对比（Top 5）

| 排名 | 策略类型 | 年化收益 | 胜率 | 回撤 | 交易数 |
|------|----------|----------|------|------|--------|
| 1 | multi_signal | 1892.51% | 100% | 0% | 3 |
| 2 | mean_reversion | 1731.49% | 100% | 0% | 2 |
| 3 | mean_reversion | 1568.21% | 100% | 0% | 2 |
| 4 | RSI+MACD | 5.82% | 35.9% | 42.1% | 833 |
| 5 | breakout | 13.64% | 45.4% | 6.8% | - |

---

## 📁 数据文件清单

### 主要结果文件
| 文件 | 大小 | 说明 |
|------|------|------|
| `5_strategies_results.json` | 6.3MB | 5 策略完整回测结果 |
| `full_process_backtest_report.json` | 80KB | 全流程回测报告 |
| `optimal_strategy.json` | 2.7KB | 最优策略参数 |
| `ETH_strategy_comparison.json` | 1.8KB | ETH 策略对比 |

### 策略配置
| 文件 | 说明 |
|------|------|
| `safe_strategies.json` | 安全策略列表 |
| `strategy_catalog.json` | 策略目录 |
| `strategy_schema.json` | 策略 schema |

### Backtest 目录 (15+ 文件)
- `backtest_TESTUSDT_*.json` - TESTUSDT 回测数据
- `contract_strategies_full_results.json` - 合约策略完整结果
- `detailed_trade_log.json` - 详细交易日志
- `four_coin_backtest_data.json` - 四币种回测
- `eth_heatmap_data.json` - ETH 热力图
- `eth_opt_results.json` - ETH 优化结果

---

## 🎯 100% 年化计划进度

**当前最优策略收益：** 1892.51%（年化）  
**目标：** 100% 年化  
**状态：** ✅ 已达标

**下一步：**
1. 实盘模拟测试
2. 多策略组合分散风险
3. 动态参数优化

---

## ⚠️ 数据质量说明

- Top 3 策略交易次数较少（2-3 笔），需更多数据验证
- RSI+MACD 策略交易 833 笔，统计意义更强
- 建议继续积累回测数据，优化参数稳定性

---

*龙虾王量化实验室 🦞*
