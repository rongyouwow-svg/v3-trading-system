# 🛡️ v23 策略止损单跟进机制

**版本**: v1.0  
**创建时间**: 2026-03-16  
**状态**: ✅ 已启用

---

## 📊 止损单完整流程

### 开仓时
```
1. 开仓成功
   ↓
2. 等待 2 秒（确保订单完成）
   ↓
3. 创建止损单（触发价 = 入场价 × 0.99）
   ↓
4. 记录止损单 ID
   ↓
5. 保存状态到文件
```

### 持仓中
```
每 60 秒检查：
├─ 价格更新
├─ 计算盈亏%
├─ 如果盈利≥1% → 移动止损至成本价
├─ 每 5 分钟检查止损单状态
└─ 如果止损单丢失 → 重新创建
```

### 平仓时
```
触发条件：
├─ 止盈（+2%）→ 市价平仓 + 取消止损单
├─ 止损（-1%）→ 止损单自动触发
├─ 移动止损 → 市价平仓 + 取消止损单
└─ 手动停止 → 市价平仓 + 取消止损单
```

---

## 🎯 止损单类型

### 1. 初始止损单
```python
触发价 = 入场价 × (1 - 1%)
数量 = 持仓数量
类型 = STOP_MARKET（市价止损）
```

**示例**:
```
入场价：$2,170
止损触发价：$2,148.30（-1%）
数量：0.138 ETH
```

### 2. 移动止损单
```python
触发条件：盈利 ≥ 1%（止盈 2% 的 50%）
新触发价 = 入场价 × 1.002（成本价上方 0.2%）
```

**示例**:
```
入场价：$2,170
当前价：$2,213.40（+2%）
新止损触发价：$2,174.34（保本）
```

---

## 🛡️ 止损保护机制

### 三级保护

| 级别 | 类型 | 阈值 | 动作 |
|------|------|------|------|
| **1 级** | 单笔止损 | -1% | 自动平仓 |
| **2 级** | 每日止损 | -3% | 停止当日交易 |
| **3 级** | 总止损 | -20% | 清盘复盘 |

### 止损单状态监控

**检查频率**: 每 5 分钟

**检查内容**:
- ✅ 止损单是否存在
- ✅ 止损单状态（NEW/FILLED/CANCELED/EXPIRED）
- ✅ 止损单触发价是否正确

**异常处理**:
```
止损单丢失 → 立即重新创建
止损单已触发 → 记录交易，重置状态
止损单被取消 → 重新创建（如果仍有持仓）
```

---

## 📝 实际代码实现

### 开仓时创建止损单

```python
def open_position(self, price, quantity):
    # 开仓
    response = requests.post(...)
    
    if success:
        self.position = {...}
        self.entry_price = price
        
        # 创建止损单
        time.sleep(2)  # 等待订单完成
        self.create_stop_loss(quantity)
```

### 止损单创建

```python
def create_stop_loss(self, quantity):
    # 取消旧止损单
    if self.stop_loss_id:
        self.cancel_stop_loss()
    
    # 计算止损价
    stop_price = round(self.entry_price * 0.99, 2)
    
    # 创建新止损单
    response = requests.post(
        f"{BASE_URL}/api/binance/stop-loss",
        json={
            'symbol': self.symbol,
            'side': 'SELL',
            'trigger_price': stop_price,
            'quantity': quantity,
            'algo_type': 'CONDITIONAL',
            'order_type': 'STOP_MARKET'
        }
    )
    
    # 记录止损单 ID
    self.stop_loss_id = response['order']['algo_id']
```

### 移动止损

```python
def update_stop_loss(self, current_price):
    pnl_pct = (current_price - self.entry_price) / self.entry_price
    
    # 盈利 1% 后移动止损至成本价
    if pnl_pct >= 0.01:
        new_stop = round(self.entry_price * 1.002, 2)
        self.create_stop_loss(self.position['size'])
```

### 止损单状态检查

```python
def check_stop_loss_status(self):
    response = requests.get(f"{BASE_URL}/api/binance/stop-loss")
    orders = response['orders']
    
    for order in orders:
        if order['algo_id'] == self.stop_loss_id:
            if order['status'] == 'FILLED':
                # 止损单已触发
                self.position = None
                self.stop_loss_id = None
            elif order['status'] == 'CANCELED':
                # 止损单被取消，重新创建
                self.create_stop_loss(self.position['size'])
```

---

## 📊 日志记录

### 开仓日志
```
[2026-03-16 09:55:32] 📈 开仓成功 (0.138 ETHUSDT @ $2170.00)
[2026-03-16 09:55:34] ✅ 止损单创建成功 (ID: 1000000025504429, 触发价：$2148.30)
```

### 移动止损日志
```
[2026-03-16 10:15:42] 📈 盈利达标，移动止损至 $2174.34
[2026-03-16 10:15:43] ✅ 止损单创建成功 (ID: 1000000025504430, 触发价：$2174.34)
```

### 平仓日志
```
[2026-03-16 10:25:18] ✅ 止盈平仓 (+2.0%, 盈亏：+5.52 USDT)
[2026-03-16 10:25:19] ✅ 止损单已取消 (ID: 1000000025504430)
```

---

## ⚠️ 异常处理

### 场景 1: 止损单创建失败
```
处理：
1. 记录错误日志
2. 每 60 秒重试一次
3. 连续失败 3 次 → 强制平仓
```

### 场景 2: 止损单丢失
```
检测：
- 每 5 分钟检查止损单状态
- 未找到止损单 → 立即重新创建

预防：
- 状态持久化（保存到 JSON 文件）
- 策略重启时恢复止损单 ID
```

### 场景 3: 策略进程停止
```
保护机制：
1. 止损单在交易所独立存在（不依赖策略进程）
2. 即使策略停止，止损单仍会触发
3. 监控脚本检测到策略停止 → 发送告警
```

---

## 🔍 监控脚本

### v23_realtime_monitor.py

**功能**:
- ✅ 每 60 秒检查策略进程状态
- ✅ 策略停止时自动平仓
- ✅ 策略停止时取消止损单
- ✅ 实时记录交易日志
- ✅ 止损限制检查

**启动命令**:
```bash
cd /root/.openclaw/workspace/quant/v3-architecture
source .venv/bin/activate
nohup python scripts/v23_realtime_monitor.py > logs/v23_monitor.log 2>&1 &
```

---

## 📋 检查清单

### 开仓前
- [ ] 账户余额充足
- [ ] 杠杆设置正确（3x）
- [ ] 止损参数正确（1%）

### 开仓后
- [ ] 止损单创建成功
- [ ] 止损单 ID 已记录
- [ ] 状态已保存到文件

### 持仓中
- [ ] 每 60 秒检查价格
- [ ] 盈利 1% 后移动止损
- [ ] 每 5 分钟检查止损单状态

### 平仓后
- [ ] 止损单已取消
- [ ] 交易记录已保存
- [ ] 状态已重置

---

*🦞 龙虾王量化交易系统 - v23 止损单跟进机制*  
*最后更新：2026-03-16 09:55*  
*状态：✅ 已启用*
