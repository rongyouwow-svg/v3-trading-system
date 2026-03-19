# 🦞 龙虾王合约双向交易策略系统

> 完整的双向交易框架：做多 + 做空 + 特殊情况处理 + 对冲策略  
> 版本：v1.0 | 更新时间：2026-03-03

---

## 📋 目录

1. [做多策略设计](#1-做多策略设计)
2. [做空策略设计](#2-做空策略设计)
3. [特殊情境持仓](#3-特殊情境持仓)
4. [多空对冲策略](#4-多空对冲策略)
5. [综合风控体系](#5-综合风控体系)

---

## 1. 做多策略设计

### 1.1 核心做多策略类型

#### 策略 A: 趋势突破做多 (Trend Breakout Long)

**适用场景**: 牛市初期/中期，强势币种突破关键阻力

**入场条件** (需满足至少 3 项):
- ✅ 价格突破 20 日高点
- ✅ 成交量放大至 20 日均量 1.5 倍以上
- ✅ EMA20 > EMA50 (多头排列)
- ✅ RSI 在 50-70 区间 (趋势健康)
- ✅ MACD 金叉或在零轴上方

**仓位管理**:
```python
# 基础仓位：30-50%
# 强趋势加成：最高 80%
if signal_score >= 85:
    position_size = 0.55  # 55% 仓位
elif signal_score >= 75:
    position_size = 0.40  # 40% 仓位
else:
    position_size = 0.30  # 30% 仓位

# 基于 ATR 动态调整
atr_pct = atr / entry_price
max_size_by_risk = 0.02 / atr_pct  # 每笔风险 2%
position_size = min(position_size, max_size_by_risk)
```

**止损止盈**:
- 止损：入场价下方 2 倍 ATR 或关键支撑位下方 2-3%
- 止盈：3:1 盈亏比 (止损距离的 3 倍)
- 移动止盈：盈利达到 2 倍风险后，启动 5% 回撤止盈

**出场信号**:
- 触及止损/止盈
- EMA20 下穿 EMA50 (趋势反转)
- 价格跌破 EMA200 (长期趋势转空)
- RSI 超买 >80 且出现顶背离
- 持仓超过 10 天无明显进展 (时间止损)

---

#### 策略 B: 回调买入做多 (Pullback Long)

**适用场景**: 上升趋势中的健康回调

**入场条件**:
- ✅ 整体趋势向上 (EMA20 > EMA50 > EMA200)
- ✅ 价格回调至关键支撑 (斐波那契 0.382/0.5/0.618)
- ✅ 回调至 EMA20 或 EMA50 附近
- ✅ RSI 回调至 40-50 区间后反弹
- ✅ 出现看涨 K 线形态 (锤子线、吞没形态等)

**仓位管理**:
- 基础仓位：40-60%
- 分 2-3 批建仓 (每批间隔 2-5%)
- 总风险控制在 2% 以内

**止损止盈**:
- 止损：最近摆动低点下方 2-3%
- 第一止盈：前高位置 (1:2 盈亏比)
- 第二止盈：延伸 1.618 斐波那契位 (1:3 盈亏比)

---

#### 策略 C: 区间突破做多 (Range Breakout Long)

**适用场景**: 长期盘整后向上突破

**识别区间**:
- 至少 20 天的横向整理
- 明确的支撑位和阻力位
- 波动率收缩 (布林带收窄)

**入场条件**:
- ✅ 价格放量突破区间上沿
- ✅ 突破后回踩确认不破
- ✅ 成交量持续放大
- ✅ 突破时 RSI 在 50-70 (不过热)

**仓位管理**:
- 突破时建仓 30%
- 回踩确认时加仓 20-30%
- 总仓位不超过 60%

**止损止盈**:
- 止损：区间上沿下方 3% 或区间中轴
- 止盈：区间高度的 1-1.5 倍投射

---

### 1.2 做多策略评分系统

| 指标 | 权重 | 评分标准 |
|------|------|----------|
| 突破确认 | 25 分 | 突破 20 日高点 (+25), 接近突破 (+10) |
| 成交量 | 25 分 | 2 倍均量 (+25), 1.5 倍 (+15), 1 倍 (+5) |
| RSI 位置 | 20 分 | 50-65 (+20), 65-75 (+10), >75 (-10) |
| EMA 排列 | 15 分 | 多头排列 (+15), 混乱 (0), 空头 (-15) |
| MACD | 15 分 | 金叉 (+15), 粘合 (0), 死叉 (-15) |

**入场阈值**: ≥60 分  
**强信号**: ≥80 分 (可使用更高仓位)

---

## 2. 做空策略设计

### 2.1 核心做空策略类型

#### 策略 A: 高资金费率套利做空 (Funding Arbitrage Short)

**适用场景**: 资金费率显著为正时

**核心逻辑**:
- 当资金费率 > 1% 时，做空可收取资金费
- 年化收益率 = 资金费率 × 3 × 365
- 费率 1% 对应年化 1095%

**入场条件**:
- ✅ 资金费率 > 1% (阈值可调整)
- ✅ 年化资金费率 > 36.5%
- ✅ 价格处于高位或震荡 (非单边暴涨)
- ✅ 有对冲手段 (现货对冲或配对交易)

**仓位管理**:
```python
# 根据波动率调整杠杆
if volatility > 10%:
    leverage = 1.0  # 高波动不用杠杆
elif volatility > 7%:
    leverage = 2.0
else:
    leverage = 3.0

# 最大风险敞口
max_position = capital * 0.02 * leverage  # 2% 风险
```

**出场条件**:
- 资金费率转负
- 持仓时间超过 8 小时 (一个结算周期)
- 资金费率大幅下降 (<50% 阈值)
- 价格暴涨接近强平价

**风险控制**:
- 监控强平价格，保持 5% 以上安全距离
- 设置价格止损 (入场价上方 5-8%)
- 考虑现货对冲消除方向性风险

---

#### 策略 B: 趋势跟踪做空 (Trend Following Short)

**适用场景**: 熊市趋势确立

**入场条件**:
- ✅ 日线 EMA20 < EMA50 (下降趋势)
- ✅ 价格反弹至 EMA20 附近受阻
- ✅ RSI 反弹至 50-70 后回落
- ✅ 出现看跌 K 线形态
- ✅ 成交量确认 (反弹缩量，下跌放量)

**仓位管理**:
- 基础仓位：30-50%
- 根据波动率调整杠杆 (高波动降杠杆)
- 分批次建仓 (反弹确认时分批入场)

**止损止盈**:
- 止损：EMA50 上方 2-3% 或最近摆动高点上方
- 止盈：2.5-3:1 盈亏比
- 移动止盈：盈利后下移止损至保本位

**出场信号**:
- EMA20 上穿 EMA50 (趋势反转)
- 价格突破 EMA200
- RSI 超卖 <30
- 触及止损/止盈

---

#### 策略 C: 突破做空 (Breakdown Short)

**适用场景**: 跌破关键支撑位

**入场条件**:
- ✅ 跌破 20 日低点或关键支撑
- ✅ 成交量放大 (1.5 倍以上)
- ✅ 动量指标向下 (<-3%)
- ✅ 大阴线确认 (实体>3%)

**仓位管理**:
- 仓位：30-40% (突破策略风险较高)
- 杠杆：2-3 倍
- 快进快出，不恋战

**止损止盈**:
- 止损：突破前支撑位上方 2%
- 止盈：2:1 盈亏比
- 时间止损：3-5 天内无明显下跌则离场

**出场信号**:
- 价格回到支撑上方 (假突破)
- 缩量企稳
- 触及止损/止盈

---

#### 策略 D: 反弹做空 (Rebound Short)

**适用场景**: 下跌趋势中的反弹

**入场条件**:
- ✅ 处于下降趋势 (EMA20 < EMA50)
- ✅ 反弹至斐波那契 0.618 或 0.786
- ✅ 反弹至 EMA20/EMA50 阻力
- ✅ RSI 反弹至 60 以上
- ✅ 出现看跌反转形态 (上影线、吞没等)

**优势**:
- 止损明确 (阻力位上方)
- 盈亏比优秀 (通常 2.5:1 以上)
- 风险可控

**仓位管理**:
- 仓位：40-50%
- 杠杆：3 倍左右
- 可在多个阻力位分批建仓

---

### 2.2 做空策略评分系统

| 指标 | 权重 | 评分标准 |
|------|------|----------|
| 趋势确认 | 30 分 | EMA 空头排列 (+30), 混乱 (0), 多头 (-30) |
| 突破/反弹 | 25 分 | 跌破支撑/反弹阻力 (+25), 接近 (+15) |
| 成交量 | 20 分 | 下跌放量 (+20), 反弹缩量 (+15) |
| RSI 位置 | 15 分 | 50-70 回落 (+15), >70 (+10), <30 (-20) |
| K 线形态 | 10 分 | 明确看跌 (+10), 中性 (0), 看涨 (-10) |

**入场阈值**: ≥60 分

---

## 3. 特殊情境持仓

### 3.1 高波动情境 (High Volatility)

**识别标准**:
- 24 小时波动率 > 10%
- ATR/价格 > 5%
- 布林带带宽 > 20%

**应对策略**:

#### 仓位调整
```python
if volatility > 15%:
    position_size = 0.15  # 15% 仓位
    leverage = 1.0        # 不用杠杆
elif volatility > 10%:
    position_size = 0.25  # 25% 仓位
    leverage = 2.0
else:
    position_size = 0.40  # 40% 仓位
    leverage = 3.0
```

#### 止损调整
- 放宽止损至 3 倍 ATR (避免被洗盘)
- 使用百分比止损 (8-10%) 代替技术位止损
- 考虑使用期权对冲尾部风险

#### 交易频率
- 减少交易频率 (等待明确信号)
- 只做高确定性机会 (评分≥80 分)
- 避免在重大事件前后开仓

---

### 3.2 黑天鹅事件 (Black Swan)

**典型场景**:
- 交易所暴雷 (FTX 事件)
- 监管突发利空
- 地缘政治危机
- 系统性风险爆发

**应急处理流程**:

#### 第一阶段：识别 (0-1 小时)
- [ ] 确认事件性质和严重程度
- [ ] 检查所有持仓的强平风险
- [ ] 评估市场流动性状况

#### 第二阶段：减仓 (1-4 小时)
- [ ] 优先平掉高风险仓位 (接近强平)
- [ ] 降低总仓位至 20% 以下
- [ ] 保留现金应对极端情况

#### 第三阶段：对冲 (4-24 小时)
- [ ] 建立反向仓位对冲 (如持有现货则做空合约)
- [ ] 考虑跨交易所套利 (如有价差)
- [ ] 使用期权保护 (如可用)

#### 第四阶段：恢复 (24 小时后)
- [ ] 评估市场稳定性
- [ ] 逐步恢复交易 (从小仓位开始)
- [ ] 更新风控参数

**黑天鹅期间风控参数**:
```python
# 极端风控模式
MAX_POSITION_SIZE = 0.10      # 最大 10% 仓位
MAX_LEVERAGE = 1.0            # 不用杠杆
STOP_LOSS = 0.05              # 5% 止损
TAKE_PROFIT = 0.10            # 10% 止盈
MAX_DAILY_LOSS = 0.03         # 日亏损上限 3%
```

---

### 3.3 低波动情境 (Low Volatility)

**识别标准**:
- 24 小时波动率 < 2%
- ATR/价格 < 1%
- 布林带带宽 < 5%

**应对策略**:

#### 策略选择
- 优先选择区间交易策略
- 考虑资金费率套利 (通常费率稳定)
- 避免突破策略 (假突破多)

#### 仓位管理
- 可适当提高仓位 (波动小，风险低)
- 使用较高杠杆 (3-5 倍)
- 但总风险仍控制在 2% 以内

#### 止盈调整
- 降低止盈预期 (1.5-2:1 盈亏比)
- 快速获利了结
- 避免贪心等待大行情

---

### 3.4 重大事件前后

**事件类型**:
-美联储议息会议 (FOMC)
- CPI/非农数据发布
- 比特币减半
- 以太坊升级
- 监管政策宣布

**操作建议**:

#### 事件前 (24-48 小时)
- 减少仓位至 30% 以下
- 平掉不确定性高的仓位
- 设置更紧的止损

#### 事件中
- **不建议交易** (波动剧烈且方向不明)
- 如必须交易，使用极小仓位 (<10%)
- 设置宽止损避免被洗盘

#### 事件后 (1-4 小时)
- 等待市场消化信息
- 观察成交量和方向
- 选择明确方向后入场

---

## 4. 多空对冲策略

### 4.1 现货 - 合约对冲 (Spot-Perp Hedge)

**策略逻辑**:
- 持有现货的同时做空等值合约
- 赚取资金费率 (正费率时)
- 消除价格波动风险

**操作步骤**:
```python
# 假设持有 1 BTC 现货
spot_position = 1.0  # BTC
spot_price = 50000   # USDT

# 做空等值合约
short_size_usd = spot_position * spot_price  # 50000 USDT
short_leverage = 1.0
margin_required = short_size_usd / short_leverage  # 50000 USDT

# 资金费率收益 (假设费率 0.01%)
funding_rate = 0.0001
daily_funding = short_size_usd * funding_rate * 3  # 15 USDT/天
annualized_yield = funding_rate * 3 * 365  # 10.95%
```

**适用场景**:
- 资金费率持续为正 (>0.01%)
- 长期持有现货不想卖出
- 市场震荡无明显方向

**风险点**:
- 资金费率转负 (需支付费用)
- 交易所风险 (合约账户爆仓)
- 需要监控保证金率

---

### 4.2 配对交易对冲 (Pairs Trading)

**策略逻辑**:
- 做多强势币种 + 做空弱势币种
- 赚取相对强弱变化的收益
- 降低系统性风险

**币种选择**:
```python
# 强势币种特征
- 近期涨幅领先
- 基本面利好
- 资金流入明显

# 弱势币种特征
- 近期跌幅较大
- 基本面利空
- 资金流出明显

# 经典配对
- 做多 ETH / 做空 BTC (ETH 强势时)
- 做多 L2 / 做空 L1 (生态轮动)
- 做多 DeFi / 做空 Meme (风格轮动)
```

**仓位配置**:
```python
# 等值对冲
long_position_usd = 10000
short_position_usd = 10000

# 根据波动率调整
long_volatility = 0.05
short_volatility = 0.08

# 风险平价配置
long_size = long_position_usd / long_volatility  # 200000
short_size = short_position_usd / short_volatility  # 125000
```

**出场条件**:
- 强弱关系反转
- 价差达到目标 (5-10%)
- 单边风险过大 (平仓一侧)

---

### 4.3 跨期对冲 (Calendar Spread)

**策略逻辑**:
- 做多近期合约 + 做空远期合约 (或反向)
- 赚取价差变化的收益
- 适用于期货/期权市场

**正向市场 (Contango)**:
- 远期价格 > 近期价格
- 策略：做空远期 + 做多近期
- 赚取价差收敛收益

**反向市场 (Backwardation)**:
- 远期价格 < 近期价格
- 策略：做多远期 + 做空近期
- 赚取价差收敛收益

---

### 4.4 Delta 中性策略 (Delta Neutral)

**策略逻辑**:
- 构建 Delta=0 的组合
- 赚取资金费率/期权时间价值
- 不受价格方向影响

**实现方式**:
```python
# 示例：期权 + 合约 Delta 中性
# 持有 1 BTC 现货 (Delta = +1)
# 做空 1 BTC 合约 (Delta = -1)
# 总 Delta = 0

# 示例：期权组合
# 买入 1 张看涨期权 (Delta = +0.5)
# 买入 1 张看跌期权 (Delta = -0.5)
# 总 Delta = 0 (跨式组合)
```

**适用场景**:
- 市场震荡无明显方向
- 想赚取资金费率但不想承担方向风险
- 期权隐含波动率高 (卖期权收时间价值)

---

### 4.5 网格对冲策略 (Grid Hedge)

**策略逻辑**:
- 在价格区间内设置网格
- 同时有多空双向挂单
- 震荡市自动获利

**参数设置**:
```python
# 网格参数
price_range = (45000, 55000)  # 价格区间
grid_levels = 20              # 网格数量
grid_size = (55000-45000)/20  # 每格 500 USDT

# 仓位管理
total_capital = 100000
capital_per_grid = total_capital / grid_levels  # 5000 USDT/格

# 挂单策略
for i in range(grid_levels):
    price = 45000 + i * grid_size
    # 下方挂多单，上方挂空单
    if price < current_price:
        place_buy_order(price, capital_per_grid)
    else:
        place_sell_order(price, capital_per_grid)
```

**适用场景**:
- 长期震荡市
- 无明显趋势
- 有足够资金分散风险

**风险点**:
- 单边突破导致一侧仓位被套
- 需要设置止损或对冲
- 资金利用率较低

---

## 5. 综合风控体系

### 5.1 仓位管理矩阵

| 市场状态 | 趋势强度 | 波动率 | 最大仓位 | 建议杠杆 |
|----------|----------|--------|----------|----------|
| 牛市 | 强 | 低 | 80% | 3-5x |
| 牛市 | 强 | 高 | 55% | 2-3x |
| 牛市 | 弱 | 低 | 60% | 2-3x |
| 牛市 | 弱 | 高 | 40% | 1-2x |
| 震荡 | - | 低 | 50% | 2-3x |
| 震荡 | - | 高 | 30% | 1-2x |
| 熊市 | 强 | 低 | 50% (空) | 2-3x |
| 熊市 | 强 | 高 | 30% (空) | 1-2x |
| 熊市 | 弱 | 低 | 40% (空) | 1-2x |
| 熊市 | 弱 | 高 | 20% (空) | 1x |
| 黑天鹅 | - | 极高 | 10% | 1x |

---

### 5.2 止损策略体系

#### 固定百分比止损
```python
# 适用于短线交易
STOP_LOSS_PCT = 0.05  # 5% 止损

stop_loss_price = entry_price * (1 - STOP_LOSS_PCT)  # 多单
stop_loss_price = entry_price * (1 + STOP_LOSS_PCT)  # 空单
```

#### ATR 动态止损
```python
# 适用于趋势交易
atr_multiplier = 2.0

stop_loss_price = entry_price - (atr * atr_multiplier)  # 多单
stop_loss_price = entry_price + (atr * atr_multiplier)  # 空单
```

#### 技术位止损
```python
# 多单：支撑位下方
support_level = recent_swing_low
stop_loss_price = support_level * 0.98  # 下方 2%

# 空单：阻力位上方
resistance_level = recent_swing_high
stop_loss_price = resistance_level * 1.02  # 上方 2%
```

#### 时间止损
```python
# 持仓超过 X 天无明显进展则离场
MAX_HOLDING_DAYS = 10

if (current_time - entry_time).days > MAX_HOLDING_DAYS:
    if pnl_pct < 0.05:  # 盈利<5%
        close_position("时间止损")
```

---

### 5.3 止盈策略体系

#### 固定盈亏比止盈
```python
# 3:1 盈亏比
risk_distance = abs(entry_price - stop_loss)
take_profit_price = entry_price + (risk_distance * 3)  # 多单
take_profit_price = entry_price - (risk_distance * 3)  # 空单
```

#### 分批止盈
```python
# 第一目标：1:2 盈亏比，减仓 50%
# 第二目标：1:3 盈亏比，减仓 30%
# 第三目标：移动止盈，剩余 20%

take_profit_levels = [
    {'price': entry + risk*2, 'pct': 0.5},
    {'price': entry + risk*3, 'pct': 0.3},
    {'price': 'trailing', 'pct': 0.2}
]
```

#### 移动止盈 (Trailing Stop)
```python
# 盈利达到 2 倍风险后启动
if current_profit > risk_distance * 2:
    # 启动 5% 回撤止盈
    if is_long:
        highest = max(price_since_entry)
        trail_stop = highest * 0.95
        if current_price < trail_stop:
            close_position("移动止盈触发")
    else:
        lowest = min(price_since_entry)
        trail_stop = lowest * 1.05
        if current_price > trail_stop:
            close_position("移动止盈触发")
```

---

### 5.4 强平风险管理系统

#### 强平价格计算
```python
def calculate_liquidation_price(entry_price, leverage, maint_margin_rate, is_short):
    """
    计算强平价格
    
    参数:
        entry_price: 入场价格
        leverage: 杠杆倍数
        maint_margin_rate: 维持保证金率 (通常 0.5%)
        is_short: 是否做空
    """
    initial_margin_rate = 1 / leverage
    
    if is_short:
        # 做空强平价格 (价格上涨爆仓)
        liq_price = entry_price / (1 - initial_margin_rate + maint_margin_rate)
    else:
        # 做多强平价格 (价格下跌爆仓)
        liq_price = entry_price * (1 - initial_margin_rate + maint_margin_rate)
    
    return liq_price
```

#### 安全距离监控
```python
def check_liquidation_risk(position, current_price):
    """检查爆仓风险等级"""
    liq_price = position.liquidation_price
    
    if is_short:
        distance_pct = (liq_price - current_price) / liq_price
    else:
        distance_pct = (current_price - liq_price) / liq_price
    
    if distance_pct < 0.02:
        return 'EMERGENCY'  # <2% 紧急平仓
    elif distance_pct < 0.05:
        return 'CRITICAL'   # <5% 减仓 50%
    elif distance_pct < 0.10:
        return 'WARNING'    # <10% 密切监控
    else:
        return 'SAFE'       # 安全
```

#### 阶梯式减仓机制
```python
def reduce_position_based_on_risk(risk_level, position):
    """根据风险等级减仓"""
    if risk_level == 'EMERGENCY':
        return 1.0  # 平仓 100%
    elif risk_level == 'CRITICAL':
        return 0.5  # 减仓 50%
    elif risk_level == 'WARNING':
        return 0.2  # 减仓 20%
    else:
        return 0.0  # 不减仓
```

---

### 5.5 资金管理规则

#### 单笔风险限制
```python
# 每笔交易最大风险：总资金的 2%
MAX_RISK_PER_TRADE = 0.02

# 计算仓位
risk_distance = abs(entry_price - stop_loss) / entry_price
position_size = MAX_RISK_PER_TRADE / risk_distance
```

#### 日亏损限制
```python
# 单日最大亏损：总资金的 5%
MAX_DAILY_LOSS = 0.05

if daily_pnl < -MAX_DAILY_LOSS * capital:
    stop_trading()  # 停止当日交易
```

#### 总仓位限制
```python
# 所有仓位总价值不超过总资金的 100%
MAX_TOTAL_POSITION = 1.0

total_exposure = sum(position.value for position in open_positions)
if total_exposure > MAX_TOTAL_POSITION * capital:
    reduce_positions()  # 降低仓位
```

#### 连续亏损处理
```python
# 连续亏损 3 笔后暂停交易
if consecutive_losses >= 3:
    pause_trading(hours=24)

# 连续亏损 2 笔后仓位减半
if consecutive_losses == 2:
    position_size *= 0.5
```

---

### 5.6 风险预警系统

#### 预警等级
| 等级 | 触发条件 | 响应动作 |
|------|----------|----------|
| 🟢 正常 | 回撤 <2% | 正常交易 |
| 🟡 注意 | 回撤 2-3% | 降低仓位至 50% |
| 🟠 警告 | 回撤 3-5% | 降低仓位至 30%，收紧止损 |
| 🔴 危险 | 回撤 5-8% | 仓位降至 10%，仅平仓不开新仓 |
| 🚨 紧急 | 回撤 >8% | 全部平仓，暂停交易 7 天 |

#### 预警指标
```python
risk_indicators = {
    'current_drawdown': current_dd,      # 当前回撤
    'max_drawdown': max_dd,              # 最大回撤
    'daily_pnl': daily_pnl,              # 当日盈亏
    'consecutive_losses': cons_loss,     # 连续亏损
    'total_exposure': exposure,          # 总敞口
    'liquidation_risk': liq_risk,        # 强平风险
    'volatility': vol,                   # 波动率
    'market_regime': regime              # 市场状态
}
```

---

## 附录：策略执行检查清单

### 开仓前检查
- [ ] 市场状态识别 (牛市/熊市/震荡)
- [ ] 波动率评估 (高/中/低)
- [ ] 策略评分 ≥60 分
- [ ] 止损位明确
- [ ] 止盈位明确 (盈亏比≥2:1)
- [ ] 仓位计算正确 (风险≤2%)
- [ ] 强平价格安全距离≥5%
- [ ] 无重大事件即将发布
- [ ] 当日亏损未超限
- [ ] 连续亏损未达暂停阈值

### 持仓中监控
- [ ] 每 4 小时检查强平风险
- [ ] 每 8 小时检查资金费率 (如做空)
- [ ] 每日检查趋势是否改变
- [ ] 触及移动止盈位及时减仓
- [ ] 重大事件前评估是否减仓

### 平仓后复盘
- [ ] 记录交易原因和结果
- [ ] 分析盈亏原因
- [ ] 更新策略统计
- [ ] 调整参数 (如需要)
- [ ] 记录经验教训

---

## 策略代码实现参考

详见以下文件:
- `adaptive_strategy_perp.py` - 合约做空策略实现
- `aggressive_strategy.py` - 激进做多策略实现
- `risk_management.py` - 风险管理系统
- `backtest_engine.py` - 回测引擎

---

> 🦞 龙虾王量化 | 策略文档 v1.0  
> **记住**: 纪律 > 策略，风控 > 收益，生存 > 暴利
