# 🦞 风控体系深度学习手册

> 量化交易的核心不是赚钱，而是**活着**  
> 创建时间：2026-03-03  
> 作者：龙虾王量化系统  
> 版本：v1.0

---

## 📚 目录

1. [回撤控制方法](#1-回撤控制方法)
2. [本金保护策略](#2-本金保护策略)
3. [利润落袋机制](#3-利润落袋机制)
4. [仓位管理最佳实践](#4-仓位管理最佳实践)
5. [风控系统实现](#5-风控系统实现)
6. [参数速查表](#6-参数速查表)

---

## 1. 回撤控制方法

### 1.1 什么是回撤 (Drawdown)

**定义**: 从资产峰值到后续谷值的跌幅，衡量策略风险的核心指标

**公式**:
```
回撤 = (峰值净值 - 当前净值) / 峰值净值
最大回撤 = Max(所有回撤)
```

**示例**:
```
净值曲线: 10000 → 12000 → 9000 → 15000
峰值: 12000
谷值: 9000
回撤 = (12000 - 9000) / 12000 = 25%
```

---

### 1.2 回撤控制的核心方法

#### 方法 1: 固定回撤阈值止损

**原理**: 当总回撤达到预设阈值时，强制平仓并暂停交易

**实现**:
```python
class DrawdownController:
    def __init__(self, max_drawdown=0.20):
        self.max_drawdown = max_drawdown  # 20% 最大回撤
        self.peak_equity = initial_capital
        self.trading_allowed = True
    
    def check(self, current_equity):
        # 更新峰值
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        # 计算当前回撤
        drawdown = (self.peak_equity - current_equity) / self.peak_equity
        
        # 检查是否触发
        if drawdown >= self.max_drawdown:
            self.trading_allowed = False
            return True  # 触发止损
        
        return False  # 正常
```

**推荐参数**:
| 风险偏好 | 最大回撤 | 适用场景 |
|---------|---------|---------|
| 保守 | 15% | 保本优先，低频交易 |
| 中性 | 25% | 平衡型，中等频率 |
| 激进 | 40-50% | 高收益目标，如 100% 年化 |

**龙虾王配置**:
```python
# 分层回撤控制
DRAWDOWN_LEVELS = {
    'level_1': 0.15,  # 15%: 减仓 50%
    'level_2': 0.25,  # 25%: 减仓 75%
    'level_3': 0.40,  # 40%: 停止交易
    'hard_stop': 0.50 # 50%: 强制清盘
}
```

---

#### 方法 2: 移动回撤止损 (Trailing Drawdown Stop)

**原理**: 随着净值创新高，回撤阈值也上移，锁定利润

**实现**:
```python
class TrailingDrawdownStop:
    def __init__(self, trail_pct=0.10):
        self.trail_pct = trail_pct  # 从峰值回撤 10% 止损
        self.peak_equity = initial_capital
        self.stop_level = initial_capital * (1 - trail_pct)
    
    def update(self, current_equity):
        # 更新峰值和止损位
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            self.stop_level = current_equity * (1 - self.trail_pct)
        
        # 检查是否触发
        if current_equity <= self.stop_level:
            return True  # 触发止损
        
        return False
```

**优势**:
- ✅ 盈利后自动提高保护位
- ✅ 让利润奔跑的同时锁定收益
- ✅ 避免"坐过山车"

**示例**:
```
初始: 10000, 止损位 9000 (10% 回撤)
→ 涨到 15000, 止损位上移至 13500
→ 跌到 13000, 触发止损，锁定 +30% 收益
```

---

#### 方法 3: 时间窗口回撤控制

**原理**: 限制特定时间窗口内的最大回撤（如 7 日、30 日）

**实现**:
```python
class RollingDrawdownController:
    def __init__(self, window_days=30, max_dd=0.15):
        self.window_days = window_days
        self.max_dd = max_dd
        self.equity_history = []
    
    def add_equity(self, equity, timestamp):
        self.equity_history.append((timestamp, equity))
        
        # 只保留窗口期内数据
        cutoff = timestamp - timedelta(days=self.window_days)
        self.equity_history = [
            (t, e) for t, e in self.equity_history if t >= cutoff
        ]
        
        # 计算窗口期回撤
        if len(self.equity_history) < 2:
            return False
        
        max_equity = max(e for t, e in self.equity_history)
        current_dd = (max_equity - equity) / max_equity
        
        return current_dd >= self.max_dd
```

**适用场景**:
- 防止短期连续亏损
- 评估策略近期表现
- 动态调整仓位

---

#### 方法 4: 风险预算回撤控制

**原理**: 将总回撤预算分配到每笔交易，动态调整仓位

**公式**:
```
剩余风险预算 = 最大回撤 - 当前回撤
单笔风险 = 剩余风险预算 / 剩余交易次数
仓位 = 单笔风险 / 止损距离
```

**实现**:
```python
class RiskBudgetController:
    def __init__(self, total_risk_budget=0.30, max_trades=20):
        self.total_budget = total_risk_budget  # 30% 总风险预算
        self.max_trades = max_trades
        self.current_drawdown = 0
        self.trades_remaining = max_trades
    
    def calculate_position_size(self, entry_price, stop_loss):
        # 计算剩余风险预算
        remaining_budget = self.total_budget - self.current_drawdown
        
        # 平均分配到剩余交易
        risk_per_trade = remaining_budget / self.trades_remaining
        
        # 计算仓位
        stop_distance = (entry_price - stop_loss) / entry_price
        position_size = risk_per_trade / stop_distance
        
        return min(position_size, 0.50)  # 单笔不超过 50%
    
    def update_after_trade(self, pnl_pct):
        if pnl_pct < 0:
            self.current_drawdown += abs(pnl_pct)
        self.trades_remaining -= 1
```

**优势**:
- 亏损后自动减仓
- 盈利后恢复仓位
- 确保不会一次性亏光预算

---

### 1.3 回撤恢复策略

#### 亏损后的仓位调整

```python
def adjust_position_after_loss(current_drawdown, base_position=0.30):
    """根据回撤程度动态调整仓位"""
    
    if current_drawdown < 0.10:
        return base_position  # 正常仓位
    elif current_drawdown < 0.20:
        return base_position * 0.7  # 减仓 30%
    elif current_drawdown < 0.30:
        return base_position * 0.5  # 减仓 50%
    elif current_drawdown < 0.40:
        return base_position * 0.3  # 减仓 70%
    else:
        return 0  # 停止交易
```

#### 连续亏损后的暂停机制

```python
class ConsecutiveLossPause:
    def __init__(self, max_consecutive=5, pause_hours=24):
        self.max_consecutive = max_consecutive
        self.pause_hours = pause_hours
        self.consecutive_losses = 0
        self.pause_until = None
    
    def record_trade(self, pnl):
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # 检查是否需要暂停
        if self.consecutive_losses >= self.max_consecutive:
            self.pause_until = datetime.now() + timedelta(hours=self.pause_hours)
            return True  # 需要暂停
        
        # 检查是否在暂停期
        if self.pause_until and datetime.now() < self.pause_until:
            return True
        
        return False  # 可以交易
```

---

## 2. 本金保护策略

### 2.1 本金保护的核心原则

**第一原则**: 永远不要让自己出局

```
生存 > 盈利
保本 > 激进
纪律 > 情绪
```

**第二原则**: 单笔损失必须可控

```
单笔最大损失 ≤ 总资金的 2-5%
连续亏损不会导致爆仓
```

**第三原则**: 极端情况必须有预案

```
黑天鹅事件应对
系统故障处理
流动性危机预案
```

---

### 2.2 本金保护的具体方法

#### 方法 1: 硬性止损 (Hard Stop Loss)

**原理**: 每笔交易必须设置止损，无条件执行

**实现**:
```python
class HardStopLoss:
    def __init__(self, max_loss_per_trade=0.05):
        self.max_loss = max_loss_per_trade  # 5% 最大损失
    
    def calculate_stop_price(self, entry_price, side='long'):
        if side == 'long':
            return entry_price * (1 - self.max_loss)
        else:
            return entry_price * (1 + self.max_loss)
    
    def check_trigger(self, entry_price, current_price, side='long'):
        stop_price = self.calculate_stop_price(entry_price, side)
        
        if side == 'long':
            return current_price <= stop_price
        else:
            return current_price >= stop_price
```

**关键要点**:
- ✅ 入场前必须设定止损价
- ✅ 止损一旦设定，不得向下调整
- ✅ 触发时必须执行，不得犹豫

**龙虾王配置**:
```python
# 基于 ATR 的动态止损
STOP_LOSS_CONFIG = {
    'type': 'atr_based',
    'atr_period': 14,
    'atr_multiplier': 1.5,  # 1.5 倍 ATR
    'max_pct': 0.08,         # 最多 8%
    'min_pct': 0.03          # 最少 3%
}
```

---

#### 方法 2: 总仓位限制

**原理**: 限制同时持仓的总风险敞口

**实现**:
```python
class PositionLimitController:
    def __init__(self, 
                 max_single_position=0.30,      # 单笔最大 30%
                 max_total_exposure=1.00,        # 总敞口 100%
                 max_correlated_exposure=0.50):  # 关联币种最大 50%
        
        self.max_single = max_single_position
        self.max_total = max_total_exposure
        self.max_correlated = max_correlated_exposure
        self.current_positions = {}
    
    def can_open_position(self, symbol, desired_size, correlation_group=None):
        # 检查单笔限制
        if desired_size > self.max_single:
            return False, "超过单笔仓位限制"
        
        # 检查总敞口
        total_exposure = sum(self.current_positions.values())
        if total_exposure + desired_size > self.max_total:
            return False, "超过总敞口限制"
        
        # 检查关联币种敞口
        if correlation_group:
            correlated_exposure = sum(
                size for sym, size in self.current_positions.items()
                if sym in correlation_group
            )
            if correlated_exposure + desired_size > self.max_correlated:
                return False, "超过关联币种限制"
        
        return True, "可以开仓"
```

**推荐限制**:
| 限制类型 | 保守 | 中性 | 激进 |
|---------|------|------|------|
| 单笔最大 | 10% | 20% | 30-40% |
| 总敞口 | 50% | 100% | 150%(杠杆) |
| 关联币种 | 20% | 40% | 60% |

---

#### 方法 3: 资金分散策略

**原理**: 不把所有鸡蛋放在一个篮子里

**分散维度**:
1. **币种分散**: 不重仓单一币种
2. **策略分散**: 多种策略并行
3. **时间分散**: 分批入场
4. **方向分散**: 多空对冲 (可选)

**实现**:
```python
class CapitalDiversifier:
    def __init__(self, total_capital):
        self.total_capital = total_capital
        
        # 币种分散配置
        self.allocation = {
            'BTC': 0.25,      # 25% 核心
            'ETH': 0.20,      # 20% 核心
            'major_alts': 0.30,  # 30% 主流山寨 (分 5-8 个)
            'small_alts': 0.15,  # 15% 小市值 (分 10-15 个)
            'cash': 0.10      # 10% 现金储备
        }
    
    def get_max_position(self, symbol):
        if symbol in ['BTC', 'ETH']:
            return self.total_capital * self.allocation[symbol]
        elif symbol in MAJOR_ALTS:
            return self.total_capital * self.allocation['major_alts'] / 5
        else:
            return self.total_capital * self.allocation['small_alts'] / 10
```

---

#### 方法 4: 现金储备策略

**原理**: 永远保留一部分现金，应对极端情况和抄底机会

**实现**:
```python
class CashReserveManager:
    def __init__(self, 
                 min_reserve=0.10,    # 最低 10% 现金
                 target_reserve=0.20, # 目标 20% 现金
                 max_deployment=0.80): # 最多部署 80%
        
        self.min_reserve = min_reserve
        self.target_reserve = target_reserve
        self.max_deployment = max_deployment
    
    def get_available_capital(self, total_capital, current_exposure):
        # 计算当前现金比例
        cash_ratio = (total_capital - current_exposure) / total_capital
        
        # 如果现金低于最低储备，禁止新开仓
        if cash_ratio < self.min_reserve:
            return 0
        
        # 计算可用资金
        available = total_capital * self.max_deployment - current_exposure
        
        return max(0, available)
    
    def adjust_reserve(self, market_condition):
        """根据市场状况调整现金储备"""
        if market_condition == 'bear':
            self.target_reserve = 0.40  # 熊市保留 40% 现金
        elif market_condition == 'bull':
            self.target_reserve = 0.10  # 牛市保留 10% 现金
        else:
            self.target_reserve = 0.20  # 震荡市 20%
```

**现金储备建议**:
| 市场状态 | 现金比例 | 理由 |
|---------|---------|------|
| 牛市 | 10-15% | 充分参与上涨 |
| 震荡市 | 20-30% | 等待明确方向 |
| 熊市 | 40-60% | 保本为主，等待抄底 |
| 极端行情 | 70-90% | 生存第一 |

---

#### 方法 5: 黑天鹅防护

**原理**: 为极端事件准备应急预案

**措施**:
```python
class BlackSwanProtection:
    def __init__(self):
        # 极端波动检测
        self.volatility_threshold = 0.10  # 10% 日波动
        
        # 流动性检测
        self.spread_threshold = 0.02  # 2% 买卖价差
        
        # 相关性崩溃检测
        self.correlation_threshold = 0.80  # 所有币种相关性>80%
    
    def check_extreme_conditions(self, market_data):
        alerts = []
        
        # 检查极端波动
        if market_data['daily_volatility'] > self.volatility_threshold:
            alerts.append('极端波动：建议减仓')
        
        # 检查流动性
        if market_data['avg_spread'] > self.spread_threshold:
            alerts.append('流动性枯竭：暂停交易')
        
        # 检查相关性
        if market_data['avg_correlation'] > self.correlation_threshold:
            alerts.append('相关性崩溃：分散失效')
        
        # 检查新闻事件
        if market_data['major_news']:
            alerts.append('重大新闻：等待市场稳定')
        
        return alerts
    
    def emergency_action(self, alert_level):
        if alert_level == 'red':
            # 红色警报：全部平仓
            return 'CLOSE_ALL'
        elif alert_level == 'orange':
            # 橙色警报：减仓 50%
            return 'REDUCE_50'
        elif alert_level == 'yellow':
            # 黄色警报：暂停新开仓
            return 'PAUSE_NEW'
        else:
            return 'NORMAL'
```

**黑天鹅应对清单**:
- [ ] 设置全市场止损 (如 BTC 跌 20% 全平)
- [ ] 保留 30%+ 现金储备
- [ ] 避免高杠杆 (≤3x)
- [ ] 分散到不同交易所
- [ ] 设置价格告警
- [ ] 准备手动干预流程

---

## 3. 利润落袋机制

### 3.1 利润落袋的核心原则

**原则 1**: 浮盈不是真钱，落袋才是

```
账面盈利 → 可能回吐
已实现盈利 → 真正属于你
```

**原则 2**: 分批止盈优于一次性

```
一次性止盈：要么太早，要么太晚
分批止盈：锁定部分，保留机会
```

**原则 3**: 让利润奔跑，但要保护

```
初期：宽止盈，让利润发展
中期：移动止盈，锁定部分
后期：收紧止盈，防止回吐
```

---

### 3.2 止盈方法详解

#### 方法 1: 固定比例止盈

**原理**: 达到预设利润率即止盈

**实现**:
```python
class FixedTakeProfit:
    def __init__(self, profit_pct=0.15):
        self.profit_pct = profit_pct  # 15% 止盈
    
    def calculate_target(self, entry_price):
        return entry_price * (1 + self.profit_pct)
    
    def check_trigger(self, entry_price, current_price):
        target = self.calculate_target(entry_price)
        return current_price >= target
```

**优缺点**:
| 优点 | 缺点 |
|------|------|
| 简单明确 | 可能过早退出 |
| 易于执行 | 不考虑趋势延续 |
| 适合回测 | 盈亏比固定 |

**推荐参数**:
- 短线交易：8-12%
- 中线交易：15-25%
- 长线交易：30-50%

---

#### 方法 2: 分批止盈 (Scaling Out)

**原理**: 在不同利润水平分批卖出

**实现**:
```python
class ScalingOutTakeProfit:
    def __init__(self):
        # 4 批止盈计划
        self.targets = [
            {'pct': 0.40, 'profit': 0.10, 'exited': False},  # 40% @ 10%
            {'pct': 0.30, 'profit': 0.20, 'exited': False},  # 30% @ 20%
            {'pct': 0.20, 'profit': 0.35, 'exited': False},  # 20% @ 35%
            {'pct': 0.10, 'profit': None, 'exited': False},  # 10% 追踪
        ]
    
    def check_exits(self, entry_price, current_price):
        exits = []
        
        for target in self.targets:
            if target['exited']:
                continue
            
            if target['profit'] is None:
                # 最后一批用追踪止盈
                continue
            
            target_price = entry_price * (1 + target['profit'])
            if current_price >= target_price:
                target['exited'] = True
                exits.append({
                    'size_pct': target['pct'],
                    'price': target_price,
                    'profit_pct': target['profit']
                })
        
        return exits
    
    def get_remaining_position(self):
        return sum(t['pct'] for t in self.targets if not t['exited'])
```

**示例**:
```
入场: 100 USDT, 1 个 BTC

→ 价格到 110 (+10%): 卖出 40%, 锁定 4 USDT 利润
→ 价格到 120 (+20%): 卖出 30%, 锁定 6 USDT 利润
→ 价格到 135 (+35%): 卖出 20%, 锁定 7 USDT 利润
→ 剩余 10%: 追踪止盈，让利润奔跑

总锁定利润: 17 USDT + 剩余仓位的浮动盈利
```

**优势**:
- ✅ 心理压力小
- ✅ 锁定部分利润
- ✅ 保留上行空间
- ✅ 平滑退出曲线

---

#### 方法 3: 移动止盈 (Trailing Stop)

**原理**: 止盈价随价格上涨而上移

**实现**:
```python
class TrailingTakeProfit:
    def __init__(self, 
                 activation_pct=0.10,  # 盈利 10% 后启动
                 trail_pct=0.05):       # 从高点回撤 5% 止盈
        
        self.activation_pct = activation_pct
        self.trail_pct = trail_pct
        self.activated = False
        self.highest_price = 0
        self.stop_price = 0
    
    def update(self, entry_price, current_price):
        # 检查是否激活
        if not self.activated:
            if current_price >= entry_price * (1 + self.activation_pct):
                self.activated = True
                self.highest_price = current_price
                self.stop_price = current_price * (1 - self.trail_pct)
            return False, 0
        
        # 更新最高价和止损价
        if current_price > self.highest_price:
            self.highest_price = current_price
            self.stop_price = current_price * (1 - self.trail_pct)
        
        # 检查是否触发
        triggered = current_price <= self.stop_price
        return triggered, self.stop_price
```

**示例**:
```
入场: 100
激活阈值: 110 (10% 盈利)
追踪比例: 5%

价格路径: 100 → 110 → 130 → 150 → 145 → 142

100→110: 激活，止损位 104.5
110→130: 止损位上移至 123.5
130→150: 止损位上移至 142.5
150→145: 未触发 (145 > 142.5)
150→142: 触发止盈 @ 142.5, 锁定 42.5% 利润
```

**推荐参数**:
| 策略类型 | 激活% | 追踪% |
|---------|------|------|
| 趋势跟踪 | 15% | 8-10% |
| 突破策略 | 10% | 5-7% |
| 震荡策略 | 8% | 3-5% |

---

#### 方法 4: 基于 ATR 的动态止盈

**原理**: 根据市场波动率动态调整止盈目标

**实现**:
```python
class ATRTakeProfit:
    def __init__(self, atr_multiplier=3.0):
        self.multiplier = atr_multiplier  # 3 倍 ATR
    
    def calculate_target(self, entry_price, atr):
        # ATR 止盈 = 入场价 + (ATR × 倍数)
        return entry_price + (atr * self.multiplier)
    
    def calculate_rr_ratio(self, entry_price, stop_loss, atr):
        # 计算风险回报比
        risk = entry_price - stop_loss
        reward = atr * self.multiplier
        return reward / risk if risk > 0 else 0
```

**优势**:
- ✅ 自适应市场波动
- ✅ 高波动时目标更远
- ✅ 低波动时目标更近
- ✅ 统计基础扎实

**推荐参数**:
- 保守：2 倍 ATR (盈亏比约 2:1)
- 中性：3 倍 ATR (盈亏比约 3:1)
- 激进：4 倍 ATR (盈亏比约 4:1)

---

#### 方法 5: 技术指标止盈

**原理**: 基于技术指标信号止盈

**支持的指标**:
| 指标 | 止盈信号 | 说明 |
|------|---------|------|
| RSI | RSI > 70 | 超买止盈 |
| MACD | 死叉 | 动能转弱 |
| 布林带 | 触及上轨 | 阻力位 |
| EMA | 死叉 | 趋势转弱 |

**实现**:
```python
class IndicatorTakeProfit:
    def __init__(self):
        self.conditions = [
            {'type': 'rsi', 'threshold': 70, 'direction': 'above'},
            {'type': 'macd', 'signal': 'dead_cross'},
            {'type': 'bb', 'band': 'upper'},
        ]
    
    def check(self, indicators):
        """检查是否触发止盈"""
        for cond in self.conditions:
            if cond['type'] == 'rsi':
                if indicators['rsi'] > cond['threshold']:
                    return True, 'RSI 超买'
            
            elif cond['type'] == 'macd':
                if indicators['macd_cross'] == 'dead':
                    return True, 'MACD 死叉'
            
            elif cond['type'] == 'bb':
                if indicators['price'] >= indicators['bb_upper']:
                    return True, '触及布林带上轨'
        
        return False, None
```

---

#### 方法 6: 时间止盈

**原理**: 持仓达到特定时间后平仓

**实现**:
```python
class TimeTakeProfit:
    def __init__(self, 
                 target_hours=48,      # 目标持仓 48 小时
                 min_profit_pct=0.02): # 最低盈利 2%
        
        self.target_hours = target_hours
        self.min_profit = min_profit_pct
        self.entry_time = None
    
    def set_entry(self, entry_time):
        self.entry_time = entry_time
    
    def check(self, current_time, entry_price, current_price):
        if not self.entry_time:
            return False
        
        # 计算持仓时间
        hold_hours = (current_time - self.entry_time).total_seconds() / 3600
        
        # 计算盈利
        profit_pct = (current_price - entry_price) / entry_price
        
        # 达到时间且盈利
        if hold_hours >= self.target_hours and profit_pct >= self.min_profit:
            return True
        
        return False
```

**适用场景**:
- 日内交易：4-12 小时
- 短线交易：24-72 小时
- 事件驱动：事件后 24-48 小时

---

### 3.3 止盈策略组合

#### 推荐组合 1: 趋势跟踪

```python
# 趋势跟踪止盈组合
take_profit_config = {
    'primary': 'trailing',          # 主要用追踪止盈
    'activation_pct': 0.15,         # 15% 盈利后激活
    'trail_pct': 0.07,              # 7% 回撤止盈
    
    'partial_exits': [              # 分批止盈
        {'at_profit': 0.20, 'sell_pct': 0.30},  # 20% 时卖 30%
        {'at_profit': 0.40, 'sell_pct': 0.30},  # 40% 时卖 30%
    ],
    
    'indicator_override': [         # 指标强制止盈
        {'type': 'rsi', 'threshold': 80},  # RSI>80 全平
        {'type': 'macd', 'signal': 'dead_cross'},  # MACD 死叉全平
    ]
}
```

#### 推荐组合 2: 突破策略

```python
# 突破策略止盈组合
take_profit_config = {
    'primary': 'atr_based',         # 基于 ATR
    'atr_multiplier': 3.0,          # 3 倍 ATR
    
    'partial_exits': [
        {'at_rr': 2.0, 'sell_pct': 0.40},   # 2 倍风险时卖 40%
        {'at_rr': 4.0, 'sell_pct': 0.30},   # 4 倍风险时卖 30%
    ],
    
    'trailing_remainder': {         # 剩余仓位追踪
        'trail_pct': 0.05,
    }
}
```

#### 推荐组合 3: 震荡策略

```python
# 震荡策略止盈组合
take_profit_config = {
    'primary': 'fixed',             # 固定止盈
    'profit_pct': 0.10,             # 10% 止盈
    
    'indicator_exit': [
        {'type': 'bb', 'band': 'upper'},  # 触及上轨
        {'type': 'rsi', 'threshold': 70},  # RSI 超买
    ],
    
    'time_exit': {                  # 时间退出
        'max_hours': 24,
        'min_profit': 0.02,
    }
}
```

---

## 4. 仓位管理最佳实践

### 4.1 仓位管理的核心原则

**原则 1**: 仓位决定生死

```
好的入场 + 差的仓位 = 可能爆仓
差的入场 + 好的仓位 = 还能活着
```

**原则 2**: 风险优先于收益

```
先问"这笔交易最多亏多少"
再问"这笔交易能赚多少"
```

**原则 3**: 动态调整优于静态

```
市场变化 → 仓位调整
账户变化 → 仓位调整
策略表现 → 仓位调整
```

---

### 4.2 仓位计算方法

#### 方法 1: 固定比例仓位

**原理**: 每笔交易使用固定比例的资金

**实现**:
```python
class FixedPositionSizing:
    def __init__(self, position_pct=0.20):
        self.position_pct = position_pct  # 20% 仓位
    
    def calculate(self, capital):
        return capital * self.position_pct
```

**优缺点**:
| 优点 | 缺点 |
|------|------|
| 简单易用 | 不考虑风险差异 |
| 稳定一致 | 可能过度/不足 |
| 易于回测 | 不随账户调整 |

**适用场景**:
- 新手入门
- 策略测试期
- 风险均匀的交易

---

#### 方法 2: 风险百分比仓位 (推荐)

**原理**: 每笔交易风险固定为账户的 X%

**公式**:
```
仓位大小 = (账户 × 风险%) / 止损距离
```

**实现**:
```python
class RiskPercentPositionSizing:
    def __init__(self, risk_per_trade=0.02):
        self.risk_per_trade = risk_per_trade  # 2% 风险
    
    def calculate(self, capital, entry_price, stop_loss):
        # 计算风险金额
        risk_amount = capital * self.risk_per_trade
        
        # 计算止损距离
        stop_distance = entry_price - stop_loss
        
        # 计算仓位
        if stop_distance <= 0:
            return 0
        
        position_size = risk_amount / stop_distance
        return position_size
    
    def calculate_value(self, capital, entry_price, stop_loss):
        size = self.calculate(capital, entry_price, stop_loss)
        return size * entry_price
```

**示例**:
```
账户: 10,000 USDT
风险: 2% = 200 USDT
入场: 100 USDT
止损: 95 USDT (5% 止损距离)

仓位 = 200 / (100 - 95) = 40 个 BTC
仓位价值 = 40 × 100 = 4,000 USDT (40% 仓位)
```

**优势**:
- ✅ 风险可控
- ✅ 自动适应止损宽度
- ✅ 亏损后自动减仓
- ✅ 专业交易者标准

**推荐参数**:
| 风险偏好 | 每笔风险 | 适用场景 |
|---------|---------|---------|
| 保守 | 1% | 保本优先 |
| 中性 | 2% | 标准配置 |
| 激进 | 3-5% | 高收益目标 |

---

#### 方法 3: 凯利公式仓位

**原理**: 根据胜率和盈亏比计算最优仓位

**公式**:
```
f* = (p × b - q) / b
其中:
  p = 胜率
  q = 1 - p (败率)
  b = 盈亏比 (平均盈利/平均亏损)
```

**实现**:
```python
class KellyPositionSizing:
    def __init__(self, 
                 kelly_divisor=2.0,    # 凯利除数 (半凯利)
                 max_position=0.25):   # 最大 25% 仓位
        
        self.kelly_divisor = kelly_divisor
        self.max_position = max_position
    
    def calculate(self, win_rate, profit_factor):
        """
        计算凯利仓位
        win_rate: 胜率 (0-1)
        profit_factor: 盈亏比 (平均盈利/平均亏损)
        """
        if profit_factor <= 0 or win_rate <= 0:
            return 0.02  # 默认 2%
        
        # 凯利公式
        kelly_fraction = (win_rate * profit_factor - (1 - win_rate)) / profit_factor
        
        # 应用除数降低风险
        kelly_fraction = kelly_fraction / self.kelly_divisor
        
        # 限制范围
        kelly_fraction = max(0, min(kelly_fraction, self.max_position))
        
        return kelly_fraction if kelly_fraction > 0 else 0.02
```

**示例**:
```
胜率: 45%
盈亏比: 3:1

凯利仓位 = (0.45 × 3 - 0.55) / 3 = 0.267 = 26.7%
半凯利 = 26.7% / 2 = 13.35%
```

**优缺点**:
| 优点 | 缺点 |
|------|------|
| 数学最优 | 需要准确的历史数据 |
| 长期增长最快 | 短期波动大 |
| 自适应策略 | 胜率和盈亏比会变化 |

**推荐用法**:
- 使用"半凯利"或"四分之一凯利"降低风险
- 定期重新计算胜率和盈亏比
- 设置上限防止过度集中

---

#### 方法 4: 波动率调整仓位

**原理**: 高波动时减仓，低波动时加仓

**实现**:
```python
class VolatilityAdjustedPositionSizing:
    def __init__(self, 
                 base_position=0.20,    # 基础仓位 20%
                 target_volatility=0.03, # 目标波动率 3%
                 adjustment_factor=0.5): # 调整系数 0.5
        
        self.base_position = base_position
        self.target_vol = target_volatility
        self.adj_factor = adjustment_factor
    
    def calculate(self, current_volatility):
        """
        根据当前波动率调整仓位
        current_volatility: 当前波动率 (如 0.05 = 5%)
        """
        if current_volatility <= 0:
            return self.base_position
        
        # 波动率比率
        vol_ratio = self.target_vol / current_volatility
        
        # 调整仓位
        position = self.base_position * (1 + (vol_ratio - 1) * self.adj_factor)
        
        # 限制范围
        position = max(0.05, min(position, 0.50))  # 5%-50%
        
        return position
```

**示例**:
```
基础仓位: 20%
目标波动率: 3%
当前波动率: 6%

波动率比率 = 3% / 6% = 0.5
调整后仓位 = 20% × (1 + (0.5 - 1) × 0.5) = 20% × 0.75 = 15%
```

**优势**:
- ✅ 高波动时自动降低风险
- ✅ 低波动时增加收益
- ✅ 平滑收益曲线

---

#### 方法 5: 信心加权仓位

**原理**: 根据信号强度调整仓位

**实现**:
```python
class ConfidenceWeightedPositionSizing:
    def __init__(self, 
                 base_position=0.20,
                 min_confidence=0.5,    # 最低信心 50%
                 max_confidence=1.0):   # 最高信心 100%
        
        self.base_position = base_position
        self.min_conf = min_confidence
        self.max_conf = max_confidence
    
    def calculate(self, confidence_score):
        """
        根据信心分数调整仓位
        confidence_score: 0-1 (如 0.75 = 75% 信心)
        """
        if confidence_score < self.min_conf:
            return 0  # 信心不足，不交易
        
        # 线性加权
        weight = (confidence_score - self.min_conf) / (self.max_conf - self.min_conf)
        
        # 基础仓位 + 信心加成
        position = self.base_position * (0.5 + 0.5 * weight)
        
        return position
```

**信心评分系统**:
```python
def calculate_signal_confidence(signals):
    """
    计算信号信心分数
    基于多重确认
    """
    score = 0
    max_score = 0
    
    # 突破确认 (25 分)
    max_score += 25
    if signals['breakout']:
        score += 25
    
    # 成交量确认 (25 分)
    max_score += 25
    if signals['volume_ratio'] > 2.0:
        score += 25
    elif signals['volume_ratio'] > 1.5:
        score += 15
    
    # RSI 确认 (20 分)
    max_score += 20
    if 50 < signals['rsi'] < 70:
        score += 20
    
    # 均线确认 (15 分)
    max_score += 15
    if signals['ema20'] > signals['ema50']:
        score += 15
    
    # MACD 确认 (15 分)
    max_score += 15
    if signals['macd'] > signals['signal']:
        score += 15
    
    return score / max_score  # 返回 0-1 的信心分数
```

---

### 4.3 仓位管理最佳实践

#### 实践 1: 分层仓位管理

```python
class TieredPositionManagement:
    """
    分层仓位管理
    根据币种重要性分配不同仓位
    """
    
    def __init__(self, total_capital):
        self.tiers = {
            'tier_1': {'coins': ['BTC', 'ETH'], 'allocation': 0.40, 'max_per_coin': 0.20},
            'tier_2': {'coins': ['SOL', 'BNB', 'XRP'], 'allocation': 0.30, 'max_per_coin': 0.10},
            'tier_3': {'coins': ['others'], 'allocation': 0.20, 'max_per_coin': 0.05},
            'cash': {'allocation': 0.10}
        }
        self.total_capital = total_capital
    
    def get_max_position(self, symbol):
        for tier_name, tier in self.tiers.items():
            if symbol in tier['coins'] or tier_name == 'tier_3':
                return self.total_capital * tier['max_per_coin']
        return 0
```

#### 实践 2: 动态仓位调整

```python
class DynamicPositionAdjuster:
    """
    根据账户表现动态调整仓位
    """
    
    def __init__(self, base_position=0.20):
        self.base_position = base_position
        self.initial_capital = 0
        self.current_capital = 0
    
    def set_capital(self, initial, current):
        self.initial_capital = initial
        self.current_capital = current
    
    def get_adjusted_position(self):
        # 计算总收益
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital
        
        # 盈利时增加仓位，亏损时减少
        if total_return > 0.20:  # 盈利 20%+
            return min(self.base_position * 1.3, 0.40)  # 增加 30%, 最多 40%
        elif total_return > 0.10:  # 盈利 10-20%
            return min(self.base_position * 1.15, 0.30)  # 增加 15%
        elif total_return < -0.10:  # 亏损 10%+
            return max(self.base_position * 0.7, 0.10)  # 减少 30%, 最少 10%
        elif total_return < -0.20:  # 亏损 20%+
            return max(self.base_position * 0.5, 0.05)  # 减少 50%
        else:
            return self.base_position
```

#### 实践 3: 相关性调整

```python
class CorrelationAdjustedPosition:
    """
    根据币种相关性调整仓位
    避免过度集中于高相关币种
    """
    
    def __init__(self, max_correlated_exposure=0.50):
        self.max_correlated = max_correlated_exposure
        self.correlation_matrix = {}
        self.current_positions = {}
    
    def update_correlation(self, symbol1, symbol2, correlation):
        if symbol1 not in self.correlation_matrix:
            self.correlation_matrix[symbol1] = {}
        self.correlation_matrix[symbol1][symbol2] = correlation
    
    def can_open_position(self, symbol, desired_size):
        # 计算与该币种高相关的现有仓位
        correlated_exposure = desired_size
        
        for existing_symbol, existing_size in self.current_positions.items():
            corr = self.correlation_matrix.get(symbol, {}).get(existing_symbol, 0)
            if corr > 0.7:  # 高相关 (>70%)
                correlated_exposure += existing_size
        
        return correlated_exposure <= self.max_correlated
```

---

### 4.4 仓位管理检查清单

**开仓前检查**:
- [ ] 计算止损位置
- [ ] 计算单笔风险 (应≤2%)
- [ ] 检查总敞口 (应≤100%)
- [ ] 检查关联币种敞口
- [ ] 检查现金储备 (应≥10%)
- [ ] 检查信号信心分数
- [ ] 检查市场波动率

**持仓中检查**:
- [ ] 每日检查回撤
- [ ] 检查止盈止损位置
- [ ] 检查是否需要调整仓位
- [ ] 检查相关性变化

**平仓后检查**:
- [ ] 记录交易结果
- [ ] 更新胜率和盈亏比
- [ ] 重新计算凯利仓位
- [ ] 检查是否触发暂停机制

---

## 5. 风控系统实现

### 5.1 完整风控系统架构

```python
"""
🦞 龙虾王完整风控系统
整合回撤控制、本金保护、利润落袋、仓位管理
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger('RiskManagement')


class RiskLevel(Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'


@dataclass
class RiskConfig:
    """风控配置"""
    # 回撤控制
    max_drawdown: float = 0.25          # 最大回撤 25%
    trailing_drawdown: float = 0.10     # 移动回撤 10%
    
    # 本金保护
    max_loss_per_trade: float = 0.02    # 单笔最大损失 2%
    max_total_exposure: float = 1.00    # 总敞口 100%
    min_cash_reserve: float = 0.10      # 最低现金 10%
    
    # 仓位管理
    base_position: float = 0.20         # 基础仓位 20%
    kelly_divisor: float = 2.0          # 凯利除数
    max_position: float = 0.40          # 单笔最大 40%
    
    # 止盈策略
    take_profit_mode: str = 'scaling'   # 分批止盈
    trailing_activation: float = 0.15   # 追踪激活 15%
    trailing_pct: float = 0.07          # 追踪 7%


class ComprehensiveRiskManager:
    """
    综合风险管理器
    整合所有风控功能
    """
    
    def __init__(self, config: RiskConfig, initial_capital: float):
        self.config = config
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_equity = initial_capital
        
        # 状态跟踪
        self.positions: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
        self.equity_curve: List[float] = [initial_capital]
        
        # 风控状态
        self.trading_allowed = True
        self.pause_until: Optional[datetime] = None
        self.consecutive_losses = 0
        self.current_drawdown = 0.0
        
        # 统计
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        
        logger.info(f"🦞 风控系统初始化 | 初始资金：{initial_capital}")
    
    def check_can_trade(self) -> Tuple[bool, str]:
        """检查是否可以交易"""
        
        # 检查是否在暂停期
        if self.pause_until and datetime.now() < self.pause_until:
            return False, f"暂停交易至 {self.pause_until}"
        
        # 检查回撤
        if self.current_drawdown >= self.config.max_drawdown:
            return False, f"达到最大回撤 {self.config.max_drawdown*100}%"
        
        # 检查现金储备
        total_exposure = sum(p['value'] for p in self.positions.values())
        cash_ratio = (self.current_capital - total_exposure) / self.current_capital
        if cash_ratio < self.config.min_cash_reserve:
            return False, f"现金储备不足 {cash_ratio*100:.1f}%"
        
        # 检查连续亏损
        if self.consecutive_losses >= 5:
            self.pause_until = datetime.now() + timedelta(hours=24)
            return False, "连续亏损 5 笔，暂停 24 小时"
        
        return True, "可以交易"
    
    def calculate_position_size(self, 
                                symbol: str,
                                entry_price: float,
                                stop_loss: float,
                                confidence: float = 0.7) -> float:
        """计算仓位大小"""
        
        # 方法 1: 风险百分比
        risk_amount = self.current_capital * self.config.max_loss_per_trade
        stop_distance = entry_price - stop_loss
        if stop_distance <= 0:
            return 0
        risk_position = risk_amount / stop_distance
        
        # 方法 2: 凯利公式
        win_rate = self.winning_trades / max(1, self.total_trades)
        avg_win = self.total_pnl / max(1, self.winning_trades) if self.winning_trades > 0 else 0
        avg_loss = abs(self.total_pnl) / max(1, self.losing_trades) if self.losing_trades > 0 else entry_price * 0.05
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 2.0
        
        kelly_position = self.current_capital * self._calculate_kelly(
            win_rate, profit_factor, self.config.kelly_divisor
        )
        
        # 方法 3: 信心加权
        confidence_position = self.current_capital * self.config.base_position * confidence
        
        # 取最小值 (最保守)
        position_value = min(risk_position * entry_price, kelly_position, confidence_position)
        
        # 应用最大仓位限制
        max_value = self.current_capital * self.config.max_position
        position_value = min(position_value, max_value)
        
        # 转换为数量
        position_size = position_value / entry_price
        
        return position_size
    
    def _calculate_kelly(self, win_rate: float, profit_factor: float, divisor: float) -> float:
        """计算凯利仓位"""
        if profit_factor <= 0 or win_rate <= 0:
            return 0.02
        
        kelly = (win_rate * profit_factor - (1 - win_rate)) / profit_factor
        kelly = kelly / divisor
        return max(0, min(kelly, self.config.max_position))
    
    def open_position(self,
                     symbol: str,
                     entry_price: float,
                     position_size: float,
                     stop_loss: float,
                     take_profit_targets: List[Dict] = None):
        """开仓"""
        
        # 检查是否可以交易
        can_trade, reason = self.check_can_trade()
        if not can_trade:
            logger.warning(f"❌ 禁止开仓：{reason}")
            return None
        
        # 计算仓位价值
        position_value = position_size * entry_price
        
        # 检查总敞口
        total_exposure = sum(p['value'] for p in self.positions.values())
        if total_exposure + position_value > self.current_capital * self.config.max_total_exposure:
            logger.warning("❌ 超过总敞口限制")
            return None
        
        # 创建仓位
        position = {
            'symbol': symbol,
            'entry_price': entry_price,
            'size': position_size,
            'value': position_value,
            'stop_loss': stop_loss,
            'take_profit_targets': take_profit_targets or [],
            'entry_time': datetime.now(),
            'highest_price': entry_price,
            'exited_targets': []
        }
        
        self.positions[symbol] = position
        logger.info(f"🟢 开仓 | {symbol} @ {entry_price} | 仓位：{position_value:.2f}")
        
        return position
    
    def update_position(self, symbol: str, current_price: float) -> Dict:
        """更新仓位，检查止盈止损"""
        
        if symbol not in self.positions:
            return {'action': 'none'}
        
        position = self.positions[symbol]
        
        # 更新最高价 (用于追踪止盈)
        if current_price > position['highest_price']:
            position['highest_price'] = current_price
        
        # 检查止损
        if current_price <= position['stop_loss']:
            return self._close_position(symbol, current_price, 'stop_loss')
        
        # 检查止盈目标
        for i, target in enumerate(position['take_profit_targets']):
            if i in position['exited_targets']:
                continue
            
            target_price = position['entry_price'] * (1 + target['profit_pct'])
            if current_price >= target_price:
                position['exited_targets'].append(i)
                exit_size = position['size'] * target['exit_pct']
                return {
                    'action': 'partial_exit',
                    'size': exit_size,
                    'price': current_price,
                    'reason': f'take_profit_target_{i}'
                }
        
        # 检查追踪止盈
        if position.get('trailing_active', False):
            trail_price = position['highest_price'] * (1 - self.config.trailing_pct)
            if current_price <= trail_price:
                return self._close_position(symbol, current_price, 'trailing_stop')
        
        # 检查是否激活追踪止盈
        profit_pct = (current_price - position['entry_price']) / position['entry_price']
        if profit_pct >= self.config.trailing_activation and not position.get('trailing_active', False):
            position['trailing_active'] = True
            position['trailing_stop_price'] = current_price * (1 - self.config.trailing_pct)
        
        return {'action': 'none'}
    
    def _close_position(self, symbol: str, price: float, reason: str) -> Dict:
        """平仓"""
        
        position = self.positions[symbol]
        
        # 计算盈亏
        pnl = (price - position['entry_price']) * position['size']
        pnl_pct = (price - position['entry_price']) / position['entry_price']
        
        # 更新资金
        self.current_capital += pnl
        self.total_pnl += pnl
        
        # 更新统计
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
            self.consecutive_losses = 0
        else:
            self.losing_trades += 1
            self.consecutive_losses += 1
        
        # 更新净值曲线
        self.equity_curve.append(self.current_capital)
        
        # 更新峰值和回撤
        if self.current_capital > self.peak_equity:
            self.peak_equity = self.current_capital
        self.current_drawdown = (self.peak_equity - self.current_capital) / self.peak_equity
        
        # 记录交易
        trade_record = {
            'symbol': symbol,
            'entry_price': position['entry_price'],
            'exit_price': price,
            'size': position['size'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': reason,
            'exit_time': datetime.now()
        }
        self.trade_history.append(trade_record)
        
        # 删除仓位
        del self.positions[symbol]
        
        logger.info(
            f"🔴 平仓 | {symbol} @ {price} | "
            f"盈亏：{pnl:.2f} ({pnl_pct*100:.2f}%) | 原因：{reason}"
        )
        
        return {
            'action': 'close',
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': reason
        }
    
    def get_risk_report(self) -> Dict:
        """获取风控报告"""
        
        total_exposure = sum(p['value'] for p in self.positions.values())
        cash = self.current_capital - total_exposure
        
        return {
            'capital': {
                'initial': self.initial_capital,
                'current': self.current_capital,
                'total_return_pct': (self.current_capital - self.initial_capital) / self.initial_capital * 100
            },
            'drawdown': {
                'current': self.current_drawdown * 100,
                'max': max(
                    (max(self.equity_curve[:i+1]) - v) / max(self.equity_curve[:i+1]) * 100
                    for i, v in enumerate(self.equity_curve)
                ) if self.equity_curve else 0
            },
            'exposure': {
                'total': total_exposure,
                'cash': cash,
                'cash_ratio': cash / self.current_capital * 100,
                'positions_count': len(self.positions)
            },
            'performance': {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': self.winning_trades / max(1, self.total_trades) * 100,
                'total_pnl': self.total_pnl,
                'consecutive_losses': self.consecutive_losses
            },
            'status': {
                'trading_allowed': self.trading_allowed and self.pause_until is None,
                'pause_until': self.pause_until.isoformat() if self.pause_until else None,
                'risk_level': self._calculate_risk_level()
            }
        }
    
    def _calculate_risk_level(self) -> str:
        """计算风险等级"""
        if self.current_drawdown >= 0.40:
            return RiskLevel.CRITICAL.value
        elif self.current_drawdown >= 0.25:
            return RiskLevel.HIGH.value
        elif self.current_drawdown >= 0.15:
            return RiskLevel.MEDIUM.value
        else:
            return RiskLevel.LOW.value
```

---

### 5.2 风控系统集成示例

```python
# 使用示例
from risk_management_mastery import ComprehensiveRiskManager, RiskConfig

# 1. 配置风控参数
config = RiskConfig(
    max_drawdown=0.25,              # 25% 最大回撤
    max_loss_per_trade=0.02,        # 2% 单笔风险
    base_position=0.20,             # 20% 基础仓位
    take_profit_mode='scaling'      # 分批止盈
)

# 2. 创建风控管理器
risk_mgr = ComprehensiveRiskManager(
    config=config,
    initial_capital=10000
)

# 3. 开仓
can_trade, reason = risk_mgr.check_can_trade()
if can_trade:
    position_size = risk_mgr.calculate_position_size(
        symbol='BTC',
        entry_price=50000,
        stop_loss=47500,  # 5% 止损
        confidence=0.75
    )
    
    position = risk_mgr.open_position(
        symbol='BTC',
        entry_price=50000,
        position_size=position_size,
        stop_loss=47500,
        take_profit_targets=[
            {'profit_pct': 0.10, 'exit_pct': 0.40},  # 10% 时卖 40%
            {'profit_pct': 0.20, 'exit_pct': 0.30},  # 20% 时卖 30%
            {'profit_pct': 0.35, 'exit_pct': 0.30},  # 35% 时卖 30%
        ]
    )

# 4. 更新仓位 (每次价格更新时调用)
result = risk_mgr.update_position('BTC', current_price=52000)
if result['action'] != 'none':
    print(f"行动：{result}")

# 5. 获取风控报告
report = risk_mgr.get_risk_report()
print(f"当前回撤：{report['drawdown']['current']:.2f}%")
print(f"胜率：{report['performance']['win_rate']:.1f}%")
print(f"风险等级：{report['status']['risk_level']}")
```

---

## 6. 参数速查表

### 6.1 回撤控制参数

| 参数 | 保守 | 中性 | 激进 | 说明 |
|------|------|------|------|------|
| 最大回撤 | 15% | 25% | 40-50% | 总账户最大回撤 |
| 移动回撤 | 8% | 10% | 15% | 从峰值回撤止损 |
| 窗口回撤 | 10% | 15% | 20% | 30 日窗口回撤 |
| 连续亏损暂停 | 3 笔 | 5 笔 | 8 笔 | 触发暂停的连续亏损数 |
| 暂停时间 | 24h | 24h | 12h | 暂停交易时长 |

---

### 6.2 本金保护参数

| 参数 | 保守 | 中性 | 激进 | 说明 |
|------|------|------|------|------|
| 单笔风险 | 1% | 2% | 3-5% | 每笔交易风险 |
| 单笔仓位 | 10% | 20% | 30-40% | 单笔最大仓位 |
| 总敞口 | 50% | 100% | 150% | 总仓位上限 |
| 现金储备 | 30% | 20% | 10% | 最低现金比例 |
| 关联敞口 | 20% | 40% | 60% | 高相关币种上限 |

---

### 6.3 止盈参数

| 方法 | 保守 | 中性 | 激进 | 说明 |
|------|------|------|------|------|
| 固定止盈 | 10% | 15% | 25% | 固定比例止盈 |
| ATR 倍数 | 2x | 3x | 4x | ATR 止盈倍数 |
| 追踪激活 | 10% | 15% | 20% | 追踪止盈激活点 |
| 追踪回撤 | 5% | 7% | 10% | 追踪止盈回撤 |
| 分批数量 | 4 批 | 3 批 | 2 批 | 分批止盈批次 |

---

### 6.4 仓位管理参数

| 方法 | 保守 | 中性 | 激进 | 说明 |
|------|------|------|------|------|
| 固定比例 | 10% | 20% | 30% | 固定仓位比例 |
| 风险% | 1% | 2% | 3% | 每笔风险比例 |
| 凯利除数 | 4 | 2 | 1 | 凯利公式除数 |
| 波动调整 | 0.7 | 0.5 | 0.3 | 波动调整系数 |
| 信心门槛 | 0.7 | 0.5 | 0.3 | 最低信心分数 |

---

### 6.5 龙虾王推荐配置 (100% 年化目标)

```yaml
# 🦞 龙虾王风控配置 v1.0
# 目标：100% 年化，最大回撤 50%

drawdown_control:
  max_drawdown: 0.50              # 50% 最大回撤
  trailing_drawdown: 0.15         # 15% 移动回撤
  rolling_window_days: 30
  rolling_max_dd: 0.25            # 30 日内最大 25%

capital_protection:
  max_loss_per_trade: 0.03        # 3% 单笔风险
  max_single_position: 0.40       # 40% 单笔仓位
  max_total_exposure: 1.20        # 120% 总敞口 (适度杠杆)
  min_cash_reserve: 0.10          # 10% 现金储备
  consecutive_loss_pause: 5       # 5 连亏暂停
  pause_duration_hours: 24

position_sizing:
  method: 'risk_percent'          # 风险百分比法
  base_risk: 0.03                 # 3% 基础风险
  kelly_divisor: 2.0              # 半凯利
  max_position: 0.40              # 40% 上限
  confidence_weighted: true       # 启用信心加权
  volatility_adjusted: true       # 启用波动调整

take_profit:
  mode: 'scaling_trailing'        # 分批 + 追踪
  targets:
    - profit: 0.15, exit: 0.40    # 15% 时卖 40%
    - profit: 0.30, exit: 0.30    # 30% 时卖 30%
    - profit: 0.50, exit: 0.30    # 50% 时卖 30%
  trailing:
    activation: 0.20              # 20% 盈利激活追踪
    trail_pct: 0.08               # 8% 回撤止盈
  atr_multiplier: 3.0             # 3 倍 ATR 目标

monitoring:
  alert_drawdown_15: true
  alert_drawdown_25: true
  alert_drawdown_40: true
  daily_report: true
  weekly_review: true
```

---

## 📊 总结

### 风控体系核心要点

1. **回撤控制是生存基础**
   - 设置硬性回撤上限
   - 使用移动回撤锁定利润
   - 亏损后自动减仓

2. **本金保护是第一要务**
   - 每笔交易必须止损
   - 限制总敞口和关联敞口
   - 保留现金储备

3. **利润落袋要分批**
   - 固定止盈 + 追踪止盈组合
   - 分批退出降低风险
   - 让利润奔跑但要保护

4. **仓位管理决定长期收益**
   - 风险百分比法是标准
   - 凯利公式优化长期增长
   - 动态调整适应市场

5. **系统化执行是关键**
   - 所有规则写成代码
   - 避免情绪化决策
   - 定期复盘优化

---

**🦞 龙虾王风控格言**:

> "市场永远有机会，但本金只有一次"  
> "宁可错过，不可做错"  
> "截断亏损，让利润奔跑"  
> "活下来，才能赚到大钱"

---

*文档版本: v1.0*  
*最后更新: 2026-03-03*  
*维护者：龙虾王量化系统*
