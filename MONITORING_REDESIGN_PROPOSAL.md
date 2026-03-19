# 🎯 监控系统整改建议

**分析时间**: 2026-03-18 23:30  
**核心问题**: 监控没有抓住共性，被策略差异迷惑

---

## 🤔 深度思考：监控的共性是什么？

### 用户的核心诉求

**"所有设计的功能都能正常且稳定的实现"**

### 不管什么策略，监控的共性

| 层面 | 监控内容 | 共性 |
|------|----------|------|
| **策略层** | 策略是否正常运行 | ✅ 进程运行 + 信号产生 |
| **执行层** | 信号是否被执行 | ✅ 开单 + 止损 |
| **结果层** | 执行结果如何 | ✅ 持仓 + 盈亏 |

---

## 📋 监控整改方案

### 方案 1: 统一信号接口（推荐）

**核心思想**: 所有策略实现统一的信号接口

```python
# 所有策略继承基类
class BaseStrategy:
    def get_signal_status(self) -> dict:
        """返回信号状态（统一接口）"""
        return {
            'last_signal_time': ...,  # 最后信号时间
            'last_signal_type': ...,  # 最后信号类型 (BUY/SELL/WAIT)
            'last_signal_rsi': ...,   # 信号触发时的 RSI
            'signals_sent': ...,      # 发送信号数
            'signals_executed': ...,  # 执行信号数
        }
```

**监控脚本**:
```bash
# 统一调用接口获取信号状态
curl http://localhost:3000/api/strategy/{symbol}/signal_status
```

**优点**:
- 统一接口，监控简单
- 不关心策略内部逻辑
- 易于扩展新策略

**缺点**:
- 需要修改所有策略代码
- 需要时间实施

---

### 方案 2: 日志分析监控（快速实施）

**核心思想**: 分析策略日志获取信号状态

```bash
# 分析策略日志
grep "📈 开多信号\|📉 平仓信号" logs/*_strategy.log

# 提取信号时间和类型
```

**优点**:
- 无需修改策略代码
- 快速实施

**缺点**:
- 依赖日志格式
- 不够实时

---

### 方案 3: 状态文件监控（折中方案）

**核心思想**: 策略定期写入状态文件

```python
# 策略每轮循环写入状态
def run(self):
    while self.is_running:
        # ... 策略逻辑
        
        # 写入状态文件
        with open(f'state/{self.symbol}.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'rsi': self.last_rsi,
                'signal': 'BUY' if buying else 'WAIT',
                'position': self.position
            }, f)
```

**监控脚本**:
```bash
# 读取状态文件
cat state/ETHUSDT.json | python3 -c "
import sys, json
state = json.load(sys.stdin)
age = datetime.now() - datetime.fromisoformat(state['timestamp'])
if age.seconds > 600:
    print('❌ 策略超过 10 分钟未更新')
"
```

**优点**:
- 实施简单
- 实时监控
- 不依赖 API

**缺点**:
- 需要修改策略代码
- 有文件 IO 开销

---

## 🎯 推荐方案：方案 1 + 方案 3 结合

### 短期（今晚实施）

**使用方案 3: 状态文件监控**

**实施步骤**:
1. 修改 3 个策略，每轮写入状态文件
2. 监控脚本读取状态文件
3. 检测策略是否正常运行

**监控内容**:
- 策略进程是否运行
- 状态文件更新时间（>10 分钟告警）
- 信号类型（BUY/SELL/WAIT）
- 信号是否执行（对比 signals_sent 和 signals_executed）

### 长期（明早实施）

**使用方案 1: 统一信号接口**

**实施步骤**:
1. 创建 BaseStrategy 基类
2. 所有策略继承基类
3. 添加 signal_status API
4. 监控调用 API

---

## 📋 监控系统架构

### 监控层级

```
L1: 功能可用性
├─ Dashboard API
├─ 策略 API
└─ 持仓 API

L2: 策略运行状态
├─ 进程是否运行
├─ 状态文件更新时间
├─ 信号产生情况
└─ 信号执行情况

L3: 业务结果
├─ 持仓盈亏
├─ 止损单状态
└─ 风险控制
```

### 监控流程

```
每 10 分钟
  ↓
检查 L1 (API 健康)
  ↓
检查 L2 (策略状态)
  ↓
检查 L3 (业务结果)
  ↓
发现异常 → 根源分析 → 自动修复 → 发送告警
```

---

## 🔧 立即行动计划

### 阶段 1: 状态文件监控（今晚）

**修改策略代码**:
```python
# 在 3 个策略的 run() 方法中添加
def save_state(self, signal_type='WAIT'):
    state = {
        'timestamp': datetime.now().isoformat(),
        'symbol': self.symbol,
        'rsi': self.last_rsi,
        'signal': signal_type,
        'position': self.position,
        'signals_sent': self.signals_sent,
        'signals_executed': self.signals_executed
    }
    with open(f'state/{self.symbol}.json', 'w') as f:
        json.dump(state, f, indent=2)
```

**修改监控脚本**:
```bash
# 检查策略状态文件
for symbol in ETHUSDT LINKUSDT AVAXUSDT; do
    if [ -f "state/${symbol}.json" ]; then
        # 检查更新时间
        # 检查信号状态
    else
        # 告警：策略未运行
    fi
done
```

### 阶段 2: 统一 API 接口（明早）

**创建 API 端点**:
```python
@app.get("/api/strategy/{symbol}/signal_status")
async def get_signal_status(symbol: str):
    # 读取状态文件
    # 返回信号状态
```

**优化监控脚本**:
```bash
# 调用 API 获取状态
curl http://localhost:3000/api/strategy/{symbol}/signal_status
```

---

## 📊 监控指标设计

### 策略运行指标

| 指标 | 正常 | 警告 | 严重 |
|------|------|------|------|
| 进程状态 | running | - | stopped |
| 状态更新 | <5 分钟 | 5-10 分钟 | >10 分钟 |
| 信号发送 | >0 | 0 (10 分钟) | 0 (30 分钟) |
| 信号执行 | =发送 | - | <发送 |

### 业务结果指标

| 指标 | 正常 | 警告 | 严重 |
|------|------|------|------|
| 持仓盈亏 | >-50 USDT | -50~-100 | <-100 |
| 止损单 | 已设置 | - | 未设置 |
| 余额 | >1000 | 500-1000 | <500 |

---

**分析人**: 龙虾王 🦞  
**分析时间**: 2026-03-18 23:30  
**状态**: 等待确认实施方案
