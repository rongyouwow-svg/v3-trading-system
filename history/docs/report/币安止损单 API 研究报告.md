# 🦞 币安止损单 API 研究报告

**研究时间：** 2026-03-10 13:10  
**测试环境：** 币安合约测试网  

---

## 📊 测试结果

### 测试 1: STOP_MARKET 市价止损单 ❌
```json
{
  "code": -4120,
  "msg": "Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."
}
```

### 测试 2: TAKE_PROFIT_MARKET 市价止盈单 ❌
```json
{
  "code": -4120,
  "msg": "Order type not supported for this endpoint."
}
```

### 测试 3: STOP_LOSS 限价止损单 ❌
```json
{
  "code": -1116,
  "msg": "Invalid orderType."
}
```

### 测试 4: 当前持仓 ✅
```json
[
  {
    "symbol": "ETHUSDT",
    "positionAmt": "0.490",
    "entryPrice": "2040.59",
    "leverage": "3",
    "unRealizedProfit": "2.95"
  }
]
```

---

## 🔍 结论

### 测试网限制
**币安合约测试网不支持止损/止盈订单 API**

错误信息提示：
> Please use the Algo Order API endpoints instead.

但 Algo Order API 在测试网也不可用。

---

## 🛠️ 解决方案

### 方案 1：本地监控止损（推荐用于测试网）

**实现逻辑：**
```python
# 策略引擎定期检查价格（每 30 秒）
def check_stop_loss():
    for strategy in active_strategies:
        current_price = get_current_price(strategy['symbol'])
        
        # 多单止损检查
        if strategy['side'] == 'long':
            if current_price <= strategy['stop_loss']:
                # 触发止损，市价平仓
                client.place_futures_order(
                    symbol=strategy['symbol'],
                    side='SELL',
                    type='MARKET',
                    quantity=strategy['quantity']
                )
                log(f"止损触发：{strategy['symbol']} @ {current_price}")
        
        # 空单止损检查
        else:
            if current_price >= strategy['stop_loss']:
                # 触发止损，市价平仓
                client.place_futures_order(
                    symbol=strategy['symbol'],
                    side='BUY',
                    type='MARKET',
                    quantity=strategy['quantity']
                )
                log(f"止损触发：{strategy['symbol']} @ {current_price}")
```

**优势：**
- ✅ 测试网和实盘都可用
- ✅ 不依赖币安止损单 API
- ✅ 可以快速实现

**劣势：**
- ⚠️ 需要持续运行（不能关闭程序）
- ⚠️ 可能有延迟（取决于检查频率）
- ⚠️ 程序崩溃时止损失效

---

### 方案 2：实盘使用币安止损单 API

**实盘 API 端点：**
```
POST https://fapi.binance.com/fapi/v1/order

参数:
- symbol: ETHUSDT
- side: SELL
- type: STOP_MARKET
- stopPrice: 1900
- quantity: 0.1
- reduceOnly: true
```

**实盘支持：**
- ✅ STOP_MARKET（市价止损）
- ✅ TAKE_PROFIT_MARKET（市价止盈）
- ✅ STOP_LOSS（限价止损）
- ✅ TAKE_PROFIT（限价止盈）

**优势：**
- ✅ 币安自动监控，无需本地程序
- ✅ 触发速度快
- ✅ 程序关闭也有效

**劣势：**
- ⚠️ 测试网不支持，无法测试
- ⚠️ 实盘有风险，需谨慎

---

### 方案 3：混合方案（最佳实践）

**测试网：** 使用本地监控止损  
**实盘：** 使用币安止损单 API

**代码结构：**
```python
class StopLossManager:
    def __init__(self, testnet=True):
        self.testnet = testnet
        self.stop_orders = {}  # 本地监控的止损单
    
    def set_stop_loss(self, symbol, side, quantity, stop_price):
        if self.testnet:
            # 测试网：添加到本地监控列表
            self.stop_orders[symbol] = {
                'side': side,
                'quantity': quantity,
                'stop_price': stop_price
            }
            print(f"✅ 本地止损已设置：{symbol} @ {stop_price}")
        else:
            # 实盘：调用币安止损单 API
            result = client.place_stop_loss_order(...)
            if result['success']:
                print(f"✅ 币安止损单已下单，ID: {result['order_id']}")
            else:
                print(f"❌ 止损单失败：{result['error']}")
                # 降级为本地监控
                self.stop_orders[symbol] = {...}
    
    def check_all_stops(self, current_prices):
        """检查所有止损单（仅测试网使用）"""
        if not self.testnet:
            return
        
        for symbol, stop_info in self.stop_orders.items():
            current_price = current_prices.get(symbol, 0)
            
            # 多单止损
            if stop_info['side'] == 'long' and current_price <= stop_info['stop_price']:
                self.execute_stop(symbol, 'SELL', stop_info['quantity'])
            
            # 空单止损
            elif stop_info['side'] == 'short' and current_price >= stop_info['stop_price']:
                self.execute_stop(symbol, 'BUY', stop_info['quantity'])
    
    def execute_stop(self, symbol, side, quantity):
        """执行止损平仓"""
        result = client.place_futures_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        
        if result.get('success'):
            print(f"🔴 止损已执行：{symbol} @ {result['price']}")
            del self.stop_orders[symbol]
        else:
            print(f"❌ 止损执行失败：{result.get('error')}")
```

---

## 📋 推荐实施方案

### 短期（今天）
**实施本地监控止损（方案 1）**

**修改文件：**
1. `api/stop_loss_manager.py` - 新增止损管理器
2. `gateway.py` - 集成止损管理器
3. 添加定时任务（每 30 秒检查一次）

**预计耗时：** 2 小时

### 长期（实盘前）
**切换到币安止损单 API（方案 2）**

**修改文件：**
1. `api/binance_client.py` - 添加实盘止损单 API
2. `gateway.py` - 实盘模式调用币安 API

**预计耗时：** 1 小时

---

## 🎯 立即执行

**建议先实施本地监控止损：**

1. 创建止损管理器类
2. 集成到策略引擎
3. 添加定时检查任务
4. 测试止损功能

---

**🦞 结论：测试网不支持止损单 API，需使用本地监控止损！**

**研究时间：** 2026-03-10 13:10  
**建议方案：** 本地监控止损（测试网）+ 币安止损单（实盘）
