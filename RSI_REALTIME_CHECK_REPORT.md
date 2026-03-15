# 📊 RSI 数据实时性检查报告

**检查时间**: 2026-03-14 19:55  
**检查范围**: RSI 计算逻辑/K 线数据源/更新频率

---

## ✅ 检查结果

### 1. RSI 计算方式 ✅

**计算方式**: **实时计算** ✅

**代码位置**: `core/strategy/modules/rsi_strategy.py`

```python
def calculate_rsi(self, klines: List[Dict[str, Any]]) -> float:
    """计算 RSI 指标"""
    if len(klines) < self.rsi_period + 1:
        return 50.0
    
    # 提取收盘价
    closes = [float(k['close']) for k in klines[-(self.rsi_period + 1):]]
    
    # 计算涨跌幅
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    
    # 计算平均涨跌
    avg_gain = sum(gains) / self.rsi_period
    avg_loss = sum(losses) / self.rsi_period
    
    # 计算 RSI
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
```

**结论**: ✅ **RSI 是实时计算的，不是缓存数据**

---

### 2. K 线数据源 ✅

**数据源**: **币安 API** ✅

**API 端点**: `/api/binance/klines`

**代码位置**: `strategies/rsi_1min_strategy.py`

```python
def get_klines(self, limit: int = 50) -> List[Dict]:
    """获取 K 线数据"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/binance/klines",
            params={
                'symbol': self.symbol,
                'interval': '1m',
                'limit': limit
            },
            timeout=10
        )
        data = response.json()
        
        if data.get('success'):
            return data.get('klines', [])
        return []
    except Exception as e:
        print(f"❌ 获取 K 线失败：{e}")
        return []
```

**结论**: ✅ **K 线数据来自币安 API，数据获取没问题**

---

### 3. 更新频率 ⚠️

**监测脚本频率**: **30 秒** ⚠️

**代码位置**: `scripts/monitor_live_test.py`

```python
MONITOR_INTERVAL = 30  # 30 秒

while True:
    # 获取策略状态
    strategies = get_strategy_status()
    
    # 记录数据
    record = {
        'timestamp': datetime.now().isoformat(),
        'strategies': strategies
    }
    
    # 保存数据
    save_monitor_data()
    
    # 等待下次监测
    time.sleep(MONITOR_INTERVAL)
```

**实际运行**:
- 总记录数：60 次
- 运行时长：29.5 分钟
- **平均间隔：30.0 秒** ✅

**结论**: ⚠️ **监测数据每 30 秒更新一次，不是实时**

---

### 4. 策略调用频率 ⚠️

**策略调用**: **每根 K 线** ✅

**代码位置**: `core/strategy/modules/rsi_strategy.py`

```python
def on_tick(self, market_data: Dict[str, Any]):
    """每根 K 线调用"""
    # 获取 K 线数据（从 API 获取最新）
    klines = market_data.get('klines', [])
    
    # 计算 RSI（实时计算）
    rsi = self.calculate_rsi(klines)
    
    # 检查信号
    signal = self.check_signal(rsi)
    
    # 保存状态
    self.save_state()
    
    return signal
```

**问题**: ⚠️ **策略脚本没有自动循环调用**

**当前状态**:
- 策略已启动
- 但**没有循环调用 `on_tick()`**
- RSI 数据来自**启动时的快照**

---

## 🔍 为什么 RSI 数据不更新？

### 问题根源

**策略启动流程**:
```
19:15 - 启动策略
        ↓
        创建策略实例
        ↓
        调用 on_tick() 一次（获取 RSI）
        ↓
        保存状态
        ↓
        策略进程退出（因为是独立脚本，不是循环）
```

**监测脚本流程**:
```
每 30 秒 - 读取策略状态文件
        ↓
        显示 RSI 数据（旧数据）
```

**问题**:
1. ❌ 策略脚本没有循环调用 `on_tick()`
2. ❌ 监测脚本读取的是状态文件（旧数据）
3. ❌ RSI 数据不是实时计算

---

## ✅ 正确的实时数据流

### 应该这样的流程

```
策略进程（循环运行）
        ↓
每根 K 线（60 秒）
        ↓
1. 从 API 获取最新 K 线
2. 实时计算 RSI
3. 检查开仓条件
4. 保存状态
        ↓
监测脚本（每 30 秒）
        ↓
读取最新状态
        ↓
前端显示实时 RSI
```

### 当前的流程

```
策略进程（运行一次后退出）
        ↓
启动时
        ↓
1. 从 API 获取 K 线
2. 计算 RSI（一次）
3. 保存状态
4. 进程退出
        ↓
监测脚本（每 30 秒）
        ↓
读取旧状态文件
        ↓
前端显示旧 RSI（不更新）
```

---

## 🛠️ 修复方案

### 方案 A: 添加循环调用（推荐）

**修改策略脚本**:
```python
# strategies/rsi_1min_strategy.py

def run(self):
    """运行策略（循环调用）"""
    print(f"🚀 RSI 策略启动")
    
    while self.is_running:
        try:
            # 获取 K 线
            klines = self.get_klines()
            
            # 构建市场数据
            market_data = {
                'klines': klines,
                'current_price': float(klines[-1]['close']),
                'timestamp': datetime.now().isoformat()
            }
            
            # 调用 on_tick
            signal = self.on_tick(market_data)
            
            # 等待下一根 K 线
            time.sleep(60)
            
        except Exception as e:
            print(f"❌ 策略异常：{e}")
            time.sleep(10)
```

**启动脚本**:
```python
# scripts/start_all_strategies.py

# 启动策略（后台循环运行）
import subprocess

subprocess.Popen(['python3', 'strategies/rsi_1min_strategy.py'])
subprocess.Popen(['python3', 'strategies/link_rsi_detailed_strategy.py'])
subprocess.Popen(['python3', 'strategies/rsi_scale_in_strategy.py'])
```

**效果**:
- ✅ RSI 实时计算（每根 K 线）
- ✅ 数据实时更新
- ✅ 自动开仓

---

### 方案 B: 监测脚本直接调用 API

**修改监测脚本**:
```python
# scripts/monitor_live_test.py

def get_strategy_status():
    """直接从 API 获取策略状态"""
    try:
        # 从 API 获取最新 K 线
        response = requests.get('http://localhost:3000/api/binance/klines',
                              params={'symbol': 'ETHUSDT', 'interval': '1m', 'limit': 20})
        klines = response.json().get('klines', [])
        
        # 实时计算 RSI
        rsi = calculate_rsi(klines)
        
        return {
            'ETH_RSI': {'rsi': rsi, 'status': 'running'}
        }
    except Exception as e:
        return {}
```

**效果**:
- ✅ RSI 实时计算
- ✅ 无需策略进程
- ⚠️ 只是显示，不能自动开仓

---

## 📊 数据对比

### 当前数据（旧）

| 时间 | ETH RSI | AVAX RSI | 来源 |
|------|---------|----------|------|
| 19:15 | 50.0 | 67.44 | 启动时快照 |
| 19:44 | 50.0 | 67.44 | 状态文件（旧） |

### 修复后数据（实时）

| 时间 | ETH RSI | AVAX RSI | 来源 |
|------|---------|----------|------|
| 19:55 | 实时值 | 实时值 | API 实时计算 |
| 19:56 | 实时值 | 实时值 | API 实时计算 |

---

## 🎯 结论

### RSI 计算 ✅

- ✅ **计算逻辑正确**（标准 RSI 公式）
- ✅ **数据源正确**（币安 API）
- ⚠️ **更新频率有问题**（不是实时）

### 数据获取 ✅

- ✅ **K 线数据没问题**（来自币安 API）
- ⚠️ **只获取了一次**（启动时）
- ❌ **没有循环获取**（策略脚本问题）

### 修复建议

**立即修复**（10 分钟）:
1. ⏳ 修改策略脚本，添加循环调用
2. ⏳ 后台运行策略进程
3. ⏳ 验证 RSI 实时更新

**效果**:
- ✅ RSI 实时更新（每根 K 线）
- ✅ 自动开仓
- ✅ 数据准确

---

**报告生成时间**: 2026-03-14 19:55  
**检查负责人**: AI Assistant  
**建议优先级**: P0（立即修复循环调用）
