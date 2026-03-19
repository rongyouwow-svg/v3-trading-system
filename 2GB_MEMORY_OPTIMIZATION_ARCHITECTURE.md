# 🦞 2GB 内存稳定运行架构优化方案

**创建时间**: 2026-03-16 18:08  
**目标**: 在 2GB 内存下稳定运行，无频繁崩溃

---

## 📊 当前内存使用分析

### 内存占用 TOP 10

| 进程 | 内存 | 占比 | 可优化 |
|------|------|------|--------|
| **openclaw-gateway** | 554 MB | 28.9% | ✅ 可限制 |
| **searxng worker-1** | 116 MB | 6.0% | ⚠️ 谨慎 |
| **uvicorn web** | 62 MB | 3.2% | ❌ 不建议 |
| **dockerd** | 40 MB | 2.0% | ❌ 系统 |
| **AliYunDunMonitor** | 34 MB | 1.7% | ❌ 系统 |
| **systemd-journald** | 34 MB | 1.7% | ❌ 系统 |
| **v23_realtime_monitor** | 32 MB | 1.6% | ✅ 可合并 |
| **rsi_1min_strategy** | 32 MB | 1.6% | ✅ 可合并 |
| **containerd** | 23 MB | 1.2% | ❌ 系统 |
| **searxng** | 22 MB | 1.1% | ⚠️ 谨慎 |

**量化系统总计**: ~1.0 GB (55%)

---

## 🎯 优化目标

### 内存预算分配（2GB 总内存）

| 类别 | 预算 | 说明 |
|------|------|------|
| **系统进程** | 400 MB | OS + 监控 + 安全 |
| **OpenClaw Gateway** | 300 MB | 限制后 |
| **量化策略** | 400 MB | 策略 + 监控 + Web |
| **缓冲空间** | 500 MB | 应对峰值 |
| **Swap 备用** | 400 MB | 紧急使用 |
| **总计** | **2000 MB** | |

---

## 🛠️ 优化方案

### 方案 1: 进程合并（核心优化）⭐⭐⭐⭐⭐

**问题**: 当前 7 个独立 Python 进程（4 策略 +3 监控）

```
策略进程×4: 32 MB × 4 = 128 MB
监控进程×3: 32 MB × 3 = 96 MB
总计：224 MB
```

**优化**: 合并为 2 个进程

```
多策略管理器×1: 80 MB
统一监控器×1: 50 MB
总计：130 MB
节省：94 MB (42%)
```

**实现**:
```python
# strategies/multi_strategy_manager.py

class MultiStrategyManager:
    """多策略管理器"""
    
    def __init__(self):
        self.strategies = {}
        self.active_symbols = []
    
    def add_strategy(self, symbol, strategy_class, config):
        """添加策略"""
        self.strategies[symbol] = {
            'class': strategy_class,
            'config': config,
            'instance': strategy_class(**config),
            'last_heartbeat': time.time()
        }
    
    def run_all(self, interval=60):
        """运行所有策略"""
        while True:
            for symbol, strategy in self.strategies.items():
                try:
                    # 运行策略逻辑
                    strategy['instance'].run_once()
                    strategy['last_heartbeat'] = time.time()
                except Exception as e:
                    log_error(f"{symbol} 策略异常：{e}")
            
            time.sleep(interval)
```

---

### 方案 2: Gateway 内存限制（cgroups）⭐⭐⭐⭐

**问题**: Gateway 占用 554 MB，无限制

**优化**: 限制为 300 MB

**实现**:
```bash
# 1. 安装 cgroups
sudo yum install -y libcgroup

# 2. 创建 cgroup
sudo cgcreate -g memory:/openclaw

# 3. 设置内存限制
sudo cgset -r memory.limit_in_bytes=300M openclaw

# 4. 将 gateway 加入 cgroup
GATEWAY_PID=$(pgrep -f "openclaw-gateway")
sudo cgclassify -g memory:openclaw $GATEWAY_PID
```

**风险**: 可能导致 Gateway 频繁 GC，影响性能

---

### 方案 3: 懒加载策略（按需启动）⭐⭐⭐⭐

**问题**: 4 个策略同时运行，占用 128 MB

**优化**: 只运行有持仓的策略

**实现**:
```python
# strategies/lazy_strategy_loader.py

class LazyStrategyLoader:
    """懒加载策略管理器"""
    
    def __init__(self):
        self.loaded_strategies = {}
        self.config = self.load_config()
    
    def get_strategy(self, symbol):
        """按需加载策略"""
        if symbol not in self.loaded_strategies:
            # 检查是否有持仓
            if self.has_position(symbol):
                # 加载策略
                strategy = self.load_strategy(symbol)
                self.loaded_strategies[symbol] = strategy
                return strategy
            else:
                return None
        return self.loaded_strategies[symbol]
    
    def unload_inactive(self, timeout=3600):
        """卸载不活跃策略"""
        now = time.time()
        to_unload = []
        
        for symbol, strategy in self.loaded_strategies.items():
            if now - strategy.last_activity > timeout:
                if not self.has_position(symbol):
                    to_unload.append(symbol)
        
        for symbol in to_unload:
            self.loaded_strategies[symbol].cleanup()
            del self.loaded_strategies[symbol]
```

**效果**: 通常只运行 1-2 个策略，节省 64-96 MB

---

### 方案 4: 监控进程精简（3 合 1）⭐⭐⭐⭐

**问题**: 3 个监控进程（v23/enhanced/deep），占用 96 MB

**优化**: 合并为 1 个统一监控器

**实现**:
```python
# scripts/unified_monitor.py

class UnifiedMonitor:
    """统一监控器"""
    
    def __init__(self):
        self.tasks = [
            self.check_positions,      # 持仓检查
            self.check_stop_losses,    # 止损单检查
            self.check_processes,      # 进程检查
            self.check_balance,        # 余额检查
            self.send_alerts,          # 告警发送
        ]
    
    def run(self):
        """运行监控"""
        while True:
            for task in self.tasks:
                try:
                    task()
                except Exception as e:
                    log_error(f"监控任务失败：{task.__name__}: {e}")
            
            time.sleep(60)  # 60 秒周期
```

**效果**: 节省 64 MB

---

### 方案 5: Web 服务优化（按需加载）⭐⭐⭐

**问题**: Web 服务常驻内存 62 MB

**优化**: 使用轻量级 HTTP 服务器

**实现**:
```python
# scripts/lightweight_api.py

from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class LightweightAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/strategy/active':
            strategies = get_active_strategies()
            self.send_json(strategies)
        elif self.path == '/api/binance/positions':
            positions = get_positions()
            self.send_json(positions)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

# 内存占用：~10 MB（vs 62 MB）
server = HTTPServer(('0.0.0.0', 3000), LightweightAPI)
server.serve_forever()
```

**效果**: 节省 52 MB

---

### 方案 6: 动态策略注册中心（已实现）⭐⭐⭐⭐⭐

**状态**: ✅ 已实现 (`core/strategy_registry.py`)

**效果**: 
- 支持动态策略发现
- 自动注销停止的策略
- 配合懒加载使用

---

## 📋 实施计划

### 阶段 1: 紧急优化（今天）

| 任务 | 预计节省 | 优先级 | 状态 |
|------|---------|--------|------|
| 合并监控进程（3 合 1） | 64 MB | 🔴 | ⏳ 待执行 |
| Gateway 内存限制 | 254 MB | 🔴 | ⏳ 待执行 |
| **总计** | **318 MB** | | |

### 阶段 2: 深度优化（本周）

| 任务 | 预计节省 | 优先级 | 状态 |
|------|---------|--------|------|
| 多策略管理器（4 合 1） | 96 MB | 高 | ⏳ 待执行 |
| 懒加载策略 | 64 MB | 高 | ⏳ 待执行 |
| 轻量级 Web API | 52 MB | 中 | ⏳ 待执行 |
| **总计** | **212 MB** | | |

### 阶段 3: 长期优化（下周）

| 任务 | 预计节省 | 优先级 | 状态 |
|------|---------|--------|------|
| 代码级优化 | 50 MB | 中 | ⏳ 待执行 |
| 数据库优化 | 30 MB | 低 | ⏳ 待执行 |
| **总计** | **80 MB** | | |

---

## 🎯 预期效果

### 优化前后对比

| 项目 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| **Gateway** | 554 MB | 300 MB | -254 MB |
| **策略进程** | 128 MB | 80 MB | -48 MB |
| **监控进程** | 96 MB | 32 MB | -64 MB |
| **Web 服务** | 62 MB | 10 MB | -52 MB |
| **总计** | **1.0 GB** | **422 MB** | **-578 MB** |

### 内存预算（优化后）

| 类别 | 预算 | 实际 | 状态 |
|------|------|------|------|
| 系统进程 | 400 MB | 400 MB | ✅ |
| OpenClaw Gateway | 300 MB | 300 MB | ✅ |
| 量化策略 | 400 MB | 122 MB | ✅ |
| 缓冲空间 | 500 MB | 778 MB | ✅ |
| **总计** | **1.6 GB** | **1.6 GB** | ✅ |

---

## 🚀 立即执行：阶段 1

### 任务 1: 合并监控进程

**文件**: `scripts/unified_monitor.py`

**功能**:
- ✅ 持仓检查
- ✅ 止损单检查
- ✅ 进程检查
- ✅ 余额检查
- ✅ 告警发送

### 任务 2: Gateway 内存限制

**命令**:
```bash
sudo cgcreate -g memory:/openclaw
sudo cgset -r memory.limit_in_bytes=300M openclaw
GATEWAY_PID=$(pgrep -f "openclaw-gateway")
sudo cgclassify -g memory:openclaw $GATEWAY_PID
```

---

## 📊 监控指标

### 关键指标

| 指标 | 阈值 | 告警 |
|------|------|------|
| 内存使用率 | >80% | ⚠️ 警告 |
| 内存使用率 | >90% | 🚨 紧急 |
| Swap 使用率 | >50% | ⚠️ 警告 |
| 进程崩溃频率 | >1 次/小时 | 🚨 紧急 |

### 监控命令

```bash
# 实时监控内存
watch -n 5 'free -h && echo "---" && ps aux --sort=-%mem | head -10'

# 查看进程内存
smem -tk | grep -E "python|openclaw"

# 查看 cgroup 内存限制
sudo cgget -r memory.limit_in_bytes openclaw
```

---

## ⚠️ 风险评估

### 风险 1: Gateway 内存限制过严

**影响**: Gateway 频繁 GC，性能下降

**缓解**: 
- 监控 Gateway 性能
- 如影响严重，放宽到 400 MB

### 风险 2: 进程合并导致单点故障

**影响**: 统一监控器崩溃，所有监控失效

**缓解**:
- 添加看门狗进程
- 自动重启机制

### 风险 3: 懒加载延迟

**影响**: 策略启动延迟 1-2 秒

**缓解**:
- 预加载有持仓的策略
- 异步加载

---

## 📝 总结

**核心优化**:
1. ✅ Gateway 内存限制（-254 MB）
2. ✅ 监控进程合并（-64 MB）
3. ✅ 多策略管理器（-96 MB）
4. ✅ 懒加载策略（-64 MB）
5. ✅ 轻量级 Web API（-52 MB）

**总节省**: **578 MB**

**目标**: 从 1.0 GB 降至 422 MB，在 2GB 内存下稳定运行！

---

*🦞 龙虾王量化交易系统 - 2GB 内存优化架构*  
*创建时间：2026-03-16 18:08*  
*状态：设计中 → 实施中
