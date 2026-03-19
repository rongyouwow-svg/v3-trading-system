# 🦞 动态策略追踪方案

**创建时间**: 2026-03-16 16:30  
**问题**: 监控如何动态追踪策略变化？

---

## 🔍 问题描述

**用户需求**:
> 如果我现在是 4 个策略，如果我关闭其中的 3 个，只运行一个，然后又开启了一个新策略，这个怎么实现追踪的任务能够更新到真实的最新变化？

**当前问题**:
- 监控脚本硬编码 4 个策略（ETH/LINK/AVAX/UNI）
- 关闭策略 → 监控仍告警"进程异常"
- 开启新策略 → 监控无法识别
- 需要手动修改代码重启监控

---

## 🎯 解决方案：策略注册中心

### 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    策略注册中心                              │
│              (strategy_registry.json)                       │
│                                                             │
│  {                                                          │
│    "ETHUSDT": {"pid": 12345, "status": "running", ...},    │
│    "LINKUSDT": {"pid": 12346, "status": "running", ...},   │
│    "BTCUSDT": {"pid": 12347, "status": "running", ...}     │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
           ↑                        ↑
           │                        │
    ┌──────┴──────┐          ┌─────┴──────┐
    │  策略进程    │          │  监控进程   │
    │  启动时注册  │          │  动态读取   │
    │  停止时注销  │          │  自动更新   │
    └─────────────┘          └────────────┘
```

### 核心组件

#### 1. 策略注册中心 (`core/strategy_registry.py`)

**功能**:
- 策略启动时自动注册
- 策略停止时自动注销
- 心跳机制（检测存活）
- 动态查询接口

**API**:
```python
# 注册策略
register_strategy(symbol='BTCUSDT', pid=12345, leverage=3, amount=100)

# 注销策略
unregister_strategy('BTCUSDT')

# 获取活跃策略
active = get_active_strategies()
# 返回：{'BTCUSDT': {'pid': 12345, 'status': 'running', ...}}

# 更新心跳
registry.update_heartbeat('BTCUSDT')
```

#### 2. 策略进程修改

**启动时注册**:
```python
# strategies/rsi_1min_strategy.py

from strategy_registry import register_strategy

def __init__(self, symbol, leverage, amount):
    # ... 初始化代码 ...
    
    # 注册到策略注册中心
    register_strategy(
        symbol=self.symbol,
        pid=os.getpid(),
        leverage=self.leverage,
        amount=self.amount,
        script='rsi_1min_strategy.py'
    )
```

**运行时心跳**:
```python
def run(self):
    while self.is_running:
        # ... 策略逻辑 ...
        
        # 更新心跳（每 60 秒）
        registry.update_heartbeat(self.symbol)
        time.sleep(60)
    
    # 停止时注销
    unregister_strategy(self.symbol)
```

#### 3. 监控进程修改

**动态获取策略**:
```python
# scripts/v23_realtime_monitor.py

from strategy_registry import StrategyRegistry

class TradingMonitor:
    def __init__(self):
        self.registry = StrategyRegistry()
    
    def get_active_strategies(self):
        """动态获取活跃策略"""
        return self.registry.get_running()
    
    def run(self):
        while True:
            # 获取当前活跃策略
            active_strategies = self.get_active_strategies()
            
            print(f"📊 活跃策略：{len(active_strategies)} 个")
            for symbol, info in active_strategies.items():
                print(f"   ✅ {symbol} (PID: {info.get('pid', 'N/A')})")
            
            # 检查持仓（只检查活跃策略）
            for pos in positions:
                symbol = pos['symbol']
                strategy_info = active_strategies.get(symbol, {})
                config = strategy_info.get('config', {})
                
                # 使用动态配置
                stop_loss_pct = config.get('stop_loss_pct', 0.01)
```

---

## 📋 使用场景演示

### 场景 1: 关闭 3 个策略，只运行 1 个

```bash
# 初始状态：4 个策略运行
$ python scripts/v23_realtime_monitor.py
📊 活跃策略：4 个
   ✅ ETHUSDT (PID: 12345)
   ✅ LINKUSDT (PID: 12346)
   ✅ AVAXUSDT (PID: 12347)
   ✅ UNIUSDT (PID: 12348)

# 用户关闭 LINK/AVAX/UNI
$ pkill -f link_rsi
$ pkill -f rsi_scale
$ pkill -f uni_rsi

# 监控自动检测到变化
📊 活跃策略：1 个
   ✅ ETHUSDT (PID: 12345)
```

### 场景 2: 开启新策略（BTC）

```bash
# 用户启动 BTC 策略
$ python strategies/btc_rsi_strategy.py
📝 注册到策略注册中心...
✅ 策略 BTCUSDT 已注册 (PID: 12349)

# 监控自动检测到新策略
📊 活跃策略：2 个
   ✅ ETHUSDT (PID: 12345)
   ✅ BTCUSDT (PID: 12349)
```

### 场景 3: 策略崩溃自动检测

```bash
# 策略进程崩溃
$ kill -9 12345

# 监控检测到心跳丢失（120 秒无心跳）
❌ ETHUSDT 心跳丢失（120 秒）
📊 活跃策略：1 个
   ✅ BTCUSDT (PID: 12349)
```

---

## 🛠️ 实施步骤

### 步骤 1: 创建注册中心
- ✅ `core/strategy_registry.py` 已创建

### 步骤 2: 修改策略脚本
- ⏳ `strategies/rsi_1min_strategy.py` - 添加注册/注销
- ⏳ `strategies/link_rsi_detailed_strategy.py` - 同上
- ⏳ `strategies/rsi_scale_in_strategy.py` - 同上
- ⏳ `strategies/uni_rsi_v24_strategy.py` - 同上

### 步骤 3: 修改监控脚本
- ⏳ `scripts/v23_realtime_monitor.py` - 动态获取策略

### 步骤 4: 修改自动检查脚本
- ⏳ `scripts/error_check_and_fix.sh` - 检查注册表

### 步骤 5: 测试验证
- ⏳ 启动 4 个策略 → 验证注册
- ⏳ 关闭 3 个策略 → 验证注销
- ⏳ 启动新策略 → 验证发现
- ⏳ 策略崩溃 → 验证检测

---

## 📊 优势对比

| 特性 | 旧方案（硬编码） | 新方案（动态注册） |
|------|-----------------|-------------------|
| 策略发现 | 手动配置 | 自动发现 |
| 策略关闭 | 告警"进程异常" | 自动更新 |
| 新策略开启 | 无法识别 | 自动识别 |
| 配置修改 | 需重启监控 | 实时生效 |
| 扩展性 | 差（改代码） | 好（自动） |

---

## 🎯 预期效果

**用户操作**:
1. 关闭 3 个策略
2. 开启 1 个新策略（如 BTC）
3. 无需修改任何配置

**系统行为**:
1. 监控自动显示 1 个活跃策略
2. 监控自动识别 BTC 策略
3. 监控使用 BTC 的策略配置

**结果**: ✅ **完全自动化，无需人工干预**

---

*🦞 龙虾王量化交易系统 - 动态策略追踪方案*  
*最后更新：2026-03-16 16:30*  
*状态：设计中
