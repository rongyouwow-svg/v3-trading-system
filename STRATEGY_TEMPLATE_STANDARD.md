# 📋 V3 策略标准模板

**版本**: v2.0  
**创建时间**: 2026-03-19 17:30  
**重要性**: P0 - 所有策略必须遵守

---

## ⚠️ 核心规则（必须遵守）

### 规则 1：止损单管理（P0 最高优先级）

```python
# ✅ 必须：初始化止损单 ID
self.stop_loss_id = None

# ✅ 必须：创建止损单前检查是否已存在
def create_stop_loss(self):
    # 检查是否有持仓
    if not self.position or self.entry_price <= 0:
        return
    
    # ❗关键：检查是否已有止损单
    if self.stop_loss_id is not None:
        print(f"✅ 已有止损单，跳过创建")
        return
    
    # 创建止损单...
    
    # ❗关键：保存止损单 ID
    if data.get('success'):
        self.stop_loss_id = data.get('algo_id')

# ✅ 必须：平仓后清除止损单 ID
def close_position(self):
    # 取消止损单
    cancel_stop_loss()
    # 清除 ID
    self.stop_loss_id = None
```

**违反后果**: 重复创建止损单，导致大量重复订单

---

### 规则 2：信号定义（P0）

```python
# ✅ 必须：清晰的信号状态
def generate_signal(self):
    """
    返回：
    - 'buy': 开多信号
    - 'sell': 平仓信号
    - 'wait': 等待
    """
    if condition_buy:
        return 'buy'
    elif condition_sell:
        return 'sell'
    else:
        return 'wait'

# ✅ 必须：信号确认机制
self.signal_confirmed = False
self.confirm_count = 0
self.confirm_required = 3  # 需要 3 根 K 线确认

if signal == 'buy':
    self.confirm_count += 1
    if self.confirm_count >= self.confirm_required:
        self.signal_confirmed = True
else:
    self.confirm_count = 0
    self.signal_confirmed = False
```

**违反后果**: 误信号导致频繁交易

---

### 规则 3：仓位管理（P0）

```python
# ✅ 必须：初始化仓位参数
self.position = None  # 当前持仓
self.entry_price = 0  # 入场价
self.leverage = 3     # 杠杆倍数
self.amount = 100     # 保证金（USDT）

# ✅ 必须：开仓前检查仓位
def open_position(self):
    # 检查是否已有持仓
    if self.position:
        print("⚠️ 已有持仓，跳过开仓")
        return False
    
    # 检查仓位上限
    max_position = self.amount * self.leverage * 1.05
    if current_position_value >= max_position:
        print("⚠️ 超过仓位上限，跳过开仓")
        return False
    
    # 开仓逻辑...
```

**违反后果**: 超仓位开单，风险失控

---

### 规则 4：状态持久化（P1）

```python
# ✅ 必须：保存策略状态
def save_state(self):
    """每根 K 线后保存状态"""
    state = {
        'symbol': self.symbol,
        'position': self.position,
        'entry_price': self.entry_price,
        'stop_loss_id': self.stop_loss_id,
        'last_rsi': self.last_rsi,
        'signals_sent': self.signals_sent,
        'signals_executed': self.signals_executed
    }
    
    with open(f'state/{self.symbol}_state.json', 'w') as f:
        json.dump(state, f)

# ✅ 必须：启动时恢复状态
def load_state(self):
    """启动时恢复状态"""
    try:
        with open(f'state/{self.symbol}_state.json', 'r') as f:
            state = json.load(f)
            self.stop_loss_id = state.get('stop_loss_id')
            self.position = state.get('position')
            self.entry_price = state.get('entry_price')
    except:
        pass
```

**违反后果**: 重启后丢失状态，重复开单

---

### 规则 5：异常处理（P0）

```python
# ✅ 必须：所有 API 调用必须 try-except
def run(self, interval=60):
    """主循环"""
    self.is_running = True
    
    while self.is_running:
        try:
            # 获取数据
            # 计算指标
            # 检查信号
            # 执行交易
            time.sleep(interval)
            
        except KeyboardInterrupt:
            self.is_running = False
            break
            
        except Exception as e:
            # ❗关键：记录错误但不崩溃
            print(f"[ERROR] {datetime.now()} {e}")
            time.sleep(10)  # 失败后等待
```

**违反后果**: 策略崩溃，停止交易

---

### 规则 6：日志记录（P1）

```python
# ✅ 必须：关键操作必须记录
print(f"📊 RSI: {rsi:.2f} ({signal})")  # 指标
print(f"🚀 开仓信号")  # 信号
print(f"✅ 开仓成功 @ {entry_price}")  # 成交
print(f"🛡️ 创建止损单 @ {stop_price}")  # 止损
print(f"📉 平仓信号")  # 平仓

# ✅ 必须：错误必须记录
print(f"❌ 开仓失败：{error}")
print(f"❌ API 异常：{e}")
```

**违反后果**: 无法排查问题

---

## 📐 策略标准结构

```python
#!/usr/bin/env python3
"""
策略名称：XXX 策略
币种：ETHUSDT
杠杆：3x
保证金：100 USDT
止损：0.2%
创建时间：2026-03-19
"""

import time
import requests
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:3000"

class StrategyName:
    """策略类"""
    
    def __init__(self, symbol, leverage, amount):
        """初始化"""
        # 基础配置
        self.symbol = symbol
        self.leverage = leverage
        self.amount = amount
        
        # 仓位管理
        self.position = None
        self.entry_price = 0
        
        # 止损管理
        self.stop_loss_id = None  # ❗关键
        self.stop_loss_pct = 0.002
        
        # 信号管理
        self.last_rsi = 0
        self.signal_confirmed = False
        
        # 状态管理
        self.is_running = False
        self.signals_sent = 0
        self.signals_executed = 0
        
        # 启动时同步
        self.sync_with_exchange()
        self.load_state()
    
    def run(self, interval=60):
        """主循环 - 必须实现"""
        self.is_running = True
        
        while self.is_running:
            try:
                # 1. 获取行情
                # 2. 计算指标
                # 3. 产生信号
                # 4. 执行交易
                # 5. 保存状态
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.is_running = False
                break
                
            except Exception as e:
                print(f"[ERROR] {e}")
                time.sleep(10)
    
    def generate_signal(self):
        """产生信号 - 必须实现"""
        return 'wait'
    
    def open_position(self):
        """开仓 - 必须实现"""
        # 检查是否已有持仓
        if self.position:
            return False
        
        # 开仓逻辑...
        
        # ❗关键：开仓后创建止损单
        self.create_stop_loss()
        
        return True
    
    def create_stop_loss(self):
        """创建止损单 - 必须实现"""
        # ❗关键：检查是否已有止损单
        if self.stop_loss_id is not None:
            return
        
        # 创建逻辑...
        
        # ❗关键：保存止损单 ID
        if data.get('success'):
            self.stop_loss_id = data.get('algo_id')
    
    def close_position(self):
        """平仓 - 必须实现"""
        # 取消止损单
        self.cancel_stop_loss()
        
        # 平仓逻辑...
        
        # ❗关键：清除止损单 ID
        self.stop_loss_id = None
    
    def save_state(self):
        """保存状态 - 必须实现"""
        # 保存策略状态到文件
        pass
    
    def load_state(self):
        """加载状态 - 必须实现"""
        # 从文件恢复状态
        pass
    
    def sync_with_exchange(self):
        """同步交易所 - 必须实现"""
        # 启动时同步持仓
        pass


if __name__ == '__main__':
    strategy = StrategyName('ETHUSDT', 3, 100)
    strategy.run(interval=60)
```

---

## ✅ 检查清单

创建策略前必须检查：

- [ ] 是否初始化 `stop_loss_id = None`
- [ ] `create_stop_loss()` 是否检查已有止损单
- [ ] 创建成功后是否保存 `stop_loss_id`
- [ ] 平仓后是否清除 `stop_loss_id`
- [ ] 是否有完整的异常处理
- [ ] 是否有状态持久化
- [ ] 是否有详细日志
- [ ] 是否有信号确认机制
- [ ] 是否有仓位检查

---

## 📚 参考策略

- `rsi_1min_strategy.py` - ETH 策略（已修复）
- `link_rsi_detailed_strategy.py` - LINK 策略
- `rsi_scale_in_strategy.py` - AVAX 策略

---

**所有新策略必须遵守此模板！** 📋
