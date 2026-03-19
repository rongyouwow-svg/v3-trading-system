# 代码变更记录 - 2026-03-12

**记录人：** 龙虾王  
**记录时间：** 2026-03-12 01:35  
**目的：** 完整记录所有代码修改，方便后续维护和问题排查

---

## 🎯 任务：5% 硬止损功能

### 需求背景
- **时间：** 2026-03-11 22:09
- **反馈人：** 大王
- **问题：** 策略执行无交易记录、无止损单显示
- **定位：** `execute_signal()` 读取了 `stop_loss_pct` 但未使用

### 功能描述
在策略启动时增加"5% 硬止损"开关（默认开启），开仓后自动创建币安 CONDITIONAL 止损单，策略停止时自动取消。

---

## 📝 修改清单

### 1. 前端：`quant/pages/testnet.html`

**修改位置：** 策略启动表单

**新增 HTML：**
```html
<!-- 在策略选择表单中添加 -->
<div class="form-group">
  <label>
    <input type="checkbox" id="stopLossEnabled" checked>
    启用 5% 硬止损
  </label>
  <small class="form-text">开启后，开仓时自动创建 5% 止损单</small>
</div>
```

**新增 JavaScript：**
```javascript
// 启动策略函数中
async function startStrategy() {
  const stopLossEnabled = document.getElementById('stopLossEnabled').checked;
  
  const response = await fetch('/api/strategies/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol: selectedSymbol,
      strategy: selectedStrategy,
      leverage: selectedLeverage,
      amount: selectedAmount,
      stopLossEnabled: stopLossEnabled  // ← 新增参数
    })
  });
}
```

**状态：** ⏳ 待实现

---

### 2. 后端路由：`quant/gateway_plugin_routes.py`

**修改位置：** `/api/strategies/start` 路由

**修改代码：**
```python
@strategies_bp.route('/start', methods=['POST'])
def start_strategy():
    data = request.json
    symbol = data.get('symbol')
    strategy_name = data.get('strategy')
    leverage = data.get('leverage', 1)
    amount = data.get('amount', 100)
    stop_loss_enabled = data.get('stopLossEnabled', True)  # ← 新增，默认开启
    
    # 启动策略
    result = strategy_engine.start_strategy(
        symbol=symbol,
        strategy_name=strategy_name,
        leverage=leverage,
        amount=amount,
        stop_loss_enabled=stop_loss_enabled  # ← 传递参数
    )
    
    return jsonify(result)
```

**状态：** ⏳ 待实现

---

### 3. 策略引擎：`quant/api/strategy_engine.py`

**修改位置：** 类定义和方法

#### 3.1 新增属性

```python
class StrategyEngine:
    def __init__(self):
        self.strategies = {}  # symbol -> strategy_instance
        self.stop_loss_enabled = {}  # ← 新增：symbol -> bool
        self.gateway = None
```

#### 3.2 修改 `start_strategy()` 方法

```python
def start_strategy(self, symbol, strategy_name, leverage=1, amount=100, stop_loss_enabled=True):
    """启动策略"""
    try:
        # 保存止损开关状态
        self.stop_loss_enabled[symbol] = stop_loss_enabled
        
        # 原有逻辑...
        strategy = loader.get_strategy(strategy_name, self.gateway, symbol, leverage, amount)
        self.strategies[symbol] = strategy
        
        # 调用策略的 on_start()
        if strategy.on_start():
            return {'success': True, 'message': f'策略 {strategy_name} 已启动'}
        else:
            return {'success': False, 'message': '策略启动失败'}
    
    except Exception as e:
        return {'success': False, 'message': str(e)}
```

#### 3.3 新增 `_create_stop_loss_order()` 方法

```python
def _create_stop_loss_order(self, symbol, stop_loss_pct=0.05):
    """创建 5% 止损单"""
    try:
        # 1. 获取当前持仓
        position = self.client.get_position(symbol)
        if not position or position['size'] == 0:
            logger.warning(f"{symbol} 无持仓，跳过止损单创建")
            return
        
        # 2. 获取当前价格
        ticker = self.client.get_ticker(symbol)
        current_price = float(ticker['price'])
        
        # 3. 计算止损价格
        side = position['side']
        if side == 'LONG':
            stop_price = current_price * (1 - stop_loss_pct)
            stop_side = 'SELL'
        else:  # SHORT
            stop_price = current_price * (1 + stop_loss_pct)
            stop_side = 'BUY'
        
        # 4. 四舍五入到合适精度（币安要求 2 位小数）
        stop_price = round(stop_price, 2)
        
        # 5. 调用币安止损单 API
        quantity = abs(float(position['size']))
        result = self.client.place_algo_order(
            symbol=symbol,
            side=stop_side,
            quantity=quantity,
            algo_type='CONDITIONAL',
            trigger_price=stop_price,
            working_type='MARK_PRICE'
        )
        
        logger.info(f"✅ 创建止损单：{symbol} {side} @ {stop_price} (数量：{quantity})")
        return result
    
    except Exception as e:
        logger.error(f"❌ 创建止损单失败：{e}")
        return None
```

#### 3.4 新增 `_cancel_stop_loss_orders()` 方法

```python
def _cancel_stop_loss_orders(self, symbol):
    """取消所有止损单"""
    try:
        # 1. 查询所有挂单
        orders = self.client.get_algo_orders(symbol, limit=20)
        
        # 2. 取消 CONDITIONAL 类型订单（止损/止盈）
        cancelled_count = 0
        for order in orders:
            if order.get('algoType') == 'CONDITIONAL':
                self.client.cancel_algo_order(symbol, order['algoId'])
                cancelled_count += 1
                logger.info(f"✅ 取消止损单：{symbol} {order['algoId']}")
        
        logger.info(f"✅ 共取消 {cancelled_count} 个止损单")
        return cancelled_count
    
    except Exception as e:
        logger.error(f"❌ 取消止损单失败：{e}")
        return 0
```

#### 3.5 修改 `execute_signal()` 方法

```python
def execute_signal(self, symbol, signal):
    """执行交易信号"""
    try:
        signal_type = signal.get('type')
        stop_loss_pct = signal.get('stop_loss_pct', 0.05)
        
        if signal_type == 'OPEN':
            # 执行开仓
            result = self.client.open_position(symbol, signal)
            
            # ← 新增：如果止损开关开启，创建止损单
            if self.stop_loss_enabled.get(symbol, True):
                self._create_stop_loss_order(symbol, stop_loss_pct)
            
            return result
        
        elif signal_type == 'ADD':
            # 执行加仓
            result = self.client.add_position(symbol, signal)
            
            # ← 新增：如果止损开关开启，更新止损单（先取消再创建）
            if self.stop_loss_enabled.get(symbol, True):
                self._cancel_stop_loss_orders(symbol)
                self._create_stop_loss_order(symbol, stop_loss_pct)
            
            return result
        
        elif signal_type == 'CLOSE':
            # 执行平仓
            result = self.client.close_position(symbol)
            
            # ← 新增：取消止损单
            self._cancel_stop_loss_orders(symbol)
            
            return result
        
        else:
            logger.warning(f"未知信号类型：{signal_type}")
            return None
    
    except Exception as e:
        logger.error(f"❌ 执行信号失败：{e}")
        return None
```

#### 3.6 修改 `stop_strategy()` 方法

```python
def stop_strategy(self, symbol):
    """停止策略"""
    try:
        if symbol not in self.strategies:
            return {'success': False, 'message': '策略未运行'}
        
        strategy = self.strategies[symbol]
        
        # 1. ← 新增：取消止损单
        self._cancel_stop_loss_orders(symbol)
        
        # 2. 调用策略的 on_stop()
        strategy.on_stop()
        
        # 3. 平仓所有持仓
        self.client.close_all_positions(symbol)
        
        # 4. 移除策略
        del self.strategies[symbol]
        
        # 5. ← 新增：清理开关状态
        if symbol in self.stop_loss_enabled:
            del self.stop_loss_enabled[symbol]
        
        logger.info(f"✅ 策略 {symbol} 已停止")
        return {'success': True, 'message': '策略已停止'}
    
    except Exception as e:
        logger.error(f"❌ 停止策略失败：{e}")
        return {'success': False, 'message': str(e)}
```

**状态：** ⏳ 待实现

---

### 4. 币安客户端：`quant/api/binance_client.py`

**检查现有方法：**
- ✅ `place_algo_order()` - 已存在
- ✅ `cancel_algo_order()` - 已存在
- ✅ `get_algo_orders()` - 已存在
- ✅ `get_position()` - 已存在
- ✅ `get_ticker()` - 已存在

**状态：** ✅ 无需修改

---

## 🧪 测试计划

### 测试用例

| 编号 | 测试场景 | 预期结果 | 状态 |
|------|---------|---------|------|
| TC1 | 勾选止损启动策略 | 开仓后显示止损单 | ⏳ |
| TC2 | 不勾选止损启动策略 | 开仓后无止损单 | ⏳ |
| TC3 | 停止策略 | 止损单自动取消 | ⏳ |
| TC4 | 加仓信号 | 止损单数量更新 | ⏳ |
| TC5 | 平仓信号 | 止损单自动取消 | ⏳ |
| TC6 | 止损单触发 | 币安自动平仓 | ⏳ |

### 测试步骤

1. **准备环境**
   ```bash
   cd /home/admin/.openclaw/workspace/quant
   # 确保网关运行
   curl http://localhost:8080/api/health
   ```

2. **测试 TC1：勾选止损**
   - 前端勾选"5% 硬止损"
   - 启动策略（如 auto_sim）
   - 等待开仓信号
   - 检查前端是否显示止损单
   - 检查 API：`/api/binance/algo-orders?symbol=LINKUSDT`

3. **测试 TC2：不勾选止损**
   - 前端取消勾选
   - 启动策略
   - 等待开仓信号
   - 确认无止损单

4. **测试 TC3：停止策略**
   - 启动策略（勾选止损）
   - 等待开仓
   - 点击"停止策略"
   - 确认止损单已取消

5. **测试 TC4-TC6**
   - 按类似流程测试

---

## 📊 影响评估

### 正面影响
- ✅ 增加止损保护，降低风险
- ✅ 用户可灵活选择（有些策略不需要硬止损）
- ✅ 策略停止时自动清理，不会遗留挂单

### 潜在风险
- ⚠️ 止损单可能因网络问题创建失败
- ⚠️ 加仓时需要先取消再创建，可能有短暂空窗期
- ⚠️ 币安 API 限流可能导致失败

### 缓解措施
- 添加重试逻辑（最多 3 次）
- 记录详细日志，方便排查
- 前端显示止损单创建状态

---

## 🔗 相关文件

- **设计文档：** `quant/网关策略操作手册_v2.3.md`（已更新）
- **记忆文件：** `memory/2026-03-12.md`（待创建）
- **归档文件：** `HEARTBEAT_ARCHIVE_20260309-0312_0131.md`

---

## 📝 待办事项

- [x] 实现前端修改（testnet.html）✅
- [x] 实现后端路由修改（gateway_plugin_routes.py）✅
- [x] 重启网关 ✅
- [ ] 执行测试用例（TC1-TC6）
- [ ] 记录测试结果
- [ ] 更新文档

---

## ✅ 实现状态

### 第一阶段：止损开关（01:45 完成）

**已修改文件：**
1. ✅ `pages/testnet.html` - 添加 5% 止损开关复选框 + JS 参数传递
2. ✅ `gateway_plugin_routes.py` - 接收 stopLossEnabled 参数 + GatewayWrapper 传递

### 第二阶段：仓位计算修复 + 移除自动平仓（01:55 完成）

**发现问题：**
1. ❌ 仓位计算未考虑杠杆（100 USDT × 4x 应开 0.097 ETH，实际开了 5 ETH）
2. ❌ 策略自动平仓导致无法测试止损单

**修复内容：**
1. ✅ `gateway_plugin_routes.py` - 添加杠杆计算：`position_value = amount × leverage × percentage`
2. ✅ `auto_sim_strategy.py` - 注释掉自动平仓，保持持仓状态

### 第三阶段：开仓前设置杠杆（02:15 完成）

**发现问题：**
- ❌ 只计算了杠杆仓位，但没有调用币安 API 设置实际杠杆
- ❌ 币安默认 1x 杠杆，导致"保证金不足"错误

**修复内容：**
1. ✅ `gateway_plugin_routes.py` - OPEN 信号前调用 `set_futures_leverage()`
2. ✅ `gateway_plugin_routes.py` - ADD 信号前也调用（确保）

**代码示例：**
```python
if signal_type == 'OPEN':
    # 先设置杠杆
    self.client.set_futures_leverage(symbol, self.leverage)
    # 再开仓
    self.client.place_futures_order(symbol, side, 'MARKET', quantity=quantity)
```

**网关状态：** ✅ 已重启（v2.3, 端口 8081）

**测试计划：**
- 启动策略 → 设置杠杆 → 开仓 + 加仓 → 检查止损单 → 保持持仓
- 测试用例：TC1-TC6（见上文）

---

**下一步：** 等待大王重新测试 🚀
