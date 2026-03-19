# 🦞 策略热插拔系统 v2.0

## 📋 问题诊断

### 原问题
前端启动策略时报错：`未知策略：rsi1minreversal`

### 根本原因
1. `__init__.py` 中的 `AVAILABLE_STRATEGIES` 是**硬编码静态字典**
2. `loader.py` 的 `reload()` 是**动态扫描**，但不同步到 `AVAILABLE_STRATEGIES`
3. 前端调用 `/strategies/start` 时，`StrategyManager` 查 `AVAILABLE_STRATEGIES` 找不到新策略

---

## ✅ 解决方案

### 核心改进

#### 1. 动态策略注册表（`__init__.py`）
```python
# 之前：硬编码字典
AVAILABLE_STRATEGIES = {
    'teststrategy': TestStrategy,
    ...
}

# 现在：动态代理对象
AVAILABLE_STRATEGIES = _AvailableStrategiesProxy()
```

**优势：**
- ✅ 自动同步 loader 的策略列表
- ✅ 支持运行时热插拔
- ✅ 保持向后兼容（旧代码无需修改）

#### 2. 增强的策略加载器（`loader.py`）
```python
class StrategyLoader:
    # 文件缓存（避免重复扫描）
    _file_cache: Dict[str, float]
    
    # 模块缓存（避免重复导入）
    _module_cache: Dict[str, object]
    
    def reload(self, force=False):
        # 智能检测文件变化
        if not force and not self._file_has_changed(filename):
            continue  # 跳过未变化的文件
        
        # 动态导入策略类
        # 自动识别 BaseStrategy 子类
        # 自动生成策略 ID 和别名
```

**优势：**
- ✅ 智能缓存（只加载变化的文件）
- ✅ 自动别名生成（Rsi1minReversal → rsi1minreversal, rsi_1min_reversal）
- ✅ 详细错误日志和诊断

#### 3. 策略管理器升级（`strategy_manager.py`）
```python
def load_strategy(self, strategy_id, ...):
    # 标准化策略 ID（支持多种格式）
    normalized_id = strategy_id.lower().replace('_', '')
    
    # 动态加载
    from strategies import load_strategy
    return load_strategy(normalized_id, ...)
```

**优势：**
- ✅ 支持多种命名格式
- ✅ 自动重试（策略不存在时触发 reload）
- ✅ 返回可用策略列表（便于调试）

#### 4. 新增热插拔 API（`gateway_plugin_routes.py`）
```python
@strategies_bp.route('/reload', methods=['POST'])
def strategies_reload():
    """重新加载策略列表（热插拔 API）"""
    from strategies import reload_strategies
    strategies = reload_strategies()
    return jsonify({
        'success': True,
        'message': f'已重新加载 {len(strategies)} 个策略',
        'strategies': list(strategies.keys())
    })
```

**用途：**
- 前端添加"刷新策略列表"按钮
- 添加新策略后调用此 API
- 无需重启网关

---

## 🚀 使用方法

### 方法 1：添加新策略（推荐）

1. **创建策略文件**
   ```bash
   cd /home/admin/.openclaw/workspace/quant/strategies
   vim my_new_strategy.py
   ```

2. **实现策略类**
   ```python
   from strategies.base_strategy import BaseStrategy
   
   class MyNewStrategy(BaseStrategy):
       """我的新策略"""
       
       async def start(self):
           await super().start()
           # 策略逻辑
       
       def get_status(self):
           return super().get_status()
   ```

3. **刷新策略列表**
   - 方式 A：前端调用 `POST /strategies/reload`
   - 方式 B：Python 调用 `from strategies import reload_strategies; reload_strategies()`
   - 方式 C：自动检测（下次启动策略时自动 reload）

4. **启动策略**
   - 前端选择 "MyNewStrategy"
   - 或 API 调用 `POST /strategies/start` with `"strategy": "mynewstrategy"`

### 方法 2：修改现有策略

1. **编辑策略文件**
   ```bash
   vim strategies/rsi_1min_reversal.py
   ```

2. **保存即可**
   - 下次调用时自动检测变化并重新加载
   - 或主动调用 `POST /strategies/reload`

---

## 📊 策略命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 文件名 | snake_case | `rsi_1min_reversal.py` |
| 类名 | PascalCase | `Rsi1minReversal` |
| 策略 ID | 小写无下划线 | `rsi1minreversal` |
| 别名 | snake_case | `rsi_1min_reversal` |

**自动生成的别名：**
- `Rsi1minReversal` → `rsi1minreversal` (主 ID)
- `Rsi1minReversal` → `rsi_1min_reversal` (别名)

**前端使用：**
```javascript
// 以下格式都有效
{ "strategy": "rsi1minreversal" }
{ "strategy": "rsi_1min_reversal" }
{ "strategy": "Rsi1minReversal" }
```

---

## 🔍 调试命令

### 查看可用策略
```bash
cd /home/admin/.openclaw/workspace/quant
python3 -c "from strategies import get_strategy_list; print(get_strategy_list())"
```

### 测试策略加载
```bash
python3 -c "
from strategies import load_strategy, AVAILABLE_STRATEGIES
print('rsi1minreversal' in AVAILABLE_STRATEGIES)
cls = AVAILABLE_STRATEGIES['rsi1minreversal']
print(f'策略类：{cls}')
"
```

### 强制重新加载
```bash
python3 -c "
from strategies import reload_strategies
strategies = reload_strategies()
print(f'已加载 {len(strategies)} 个策略')
print(list(strategies.keys()))
"
```

### 查看策略详情
```bash
python3 -c "
from strategies.loader import get_loader
loader = get_loader()
info = loader.get_strategy_info('rsi1minreversal')
print(info)
"
```

---

## 📁 文件结构

```
/home/admin/.openclaw/workspace/quant/strategies/
├── __init__.py              # 策略注册表（动态代理）
├── loader.py                # 策略加载器（热插拔核心）
├── base_strategy.py         # 策略基类
├── rsi_1min_reversal.py     # RSI 1 分钟策略 ✅
├── test_rsi_1min.py         # 测试脚本
├── auto_sim_strategy.py
├── test_strategy.py
└── ...
```

---

## 🎯 前端集成建议

### 1. 添加"刷新策略列表"按钮
```javascript
async function refreshStrategies() {
    const resp = await fetch('/strategies/reload', { method: 'POST' });
    const data = await resp.json();
    if (data.success) {
        // 更新策略下拉框
        await loadStrategyList();
        alert(`已刷新 ${data.strategies.length} 个策略`);
    }
}
```

### 2. 策略启动错误处理
```javascript
async function startStrategy(strategyId) {
    const resp = await fetch('/strategies/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy: strategyId, symbol: 'ETHUSDT' })
    });
    const data = await resp.json();
    
    if (!data.success && data.available_strategies) {
        // 显示可用策略列表
        alert(`未知策略：${strategyId}\n可用策略：${data.available_strategies.join(', ')}`);
    }
}
```

---

##  参考项目

### Freqtrade
- **策略接口**: `IStrategy` (ABC 抽象基类)
- **加载机制**: `StrategyResolver.load_strategy()`
- **特点**: 严格的策略验证、配置文件驱动

### OctoBot
- **策略管理**: `StrategyManager`
- **热插拔**: 动态扫描 strategies/ 文件夹
- **特点**: 插件化架构、Web UI 管理

### 我们的实现
- ✅ 结合两者优点
- ✅ 更轻量级
- ✅ 更适合个人量化交易

---

## 📝 更新日志

### v2.0 (2026-03-13)
- ✅ 动态策略注册表（移除硬编码）
- ✅ 智能文件缓存（只加载变化的文件）
- ✅ 自动别名生成（支持多种命名格式）
- ✅ 新增 `/strategies/reload` API
- ✅ 增强的错误日志和诊断
- ✅ 向后兼容（旧代码无需修改）

### v1.0 (之前版本)
- ❌ 硬编码 AVAILABLE_STRATEGIES
- ❌ 手动维护策略列表
- ❌ 不支持热插拔

---

**创建时间**: 2026-03-13  
**版本**: v2.0  
**状态**: ✅ 生产就绪
