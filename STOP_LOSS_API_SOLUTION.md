# 📋 止损单 API 问题解决方案

**问题时间**: 2026-03-14 23:13-23:35  
**问题**: 止损单创建成功但查询返回空  
**优先级**: **P0 - 最高优先级**

---

## 🔍 问题分析

### 创建成功 ✅

```json
{
    "success": true,
    "data": {
        "algoId": 1000000025251721,
        "algoType": "CONDITIONAL",
        "orderType": "STOP_MARKET",
        "symbol": "ETHUSDT",
        "side": "SELL",
        "algoStatus": "NEW",
        "triggerPrice": "2072.31",
        "quantity": "0.150"
    }
}
```

### 查询失败 ❌

**尝试 1**: 从币安 Algo Order API 查询
```
错误：Path /fapi/v1/algoOrder/list, Method GET is invalid
原因：币安测试网不支持查询 Algo Order 列表
```

**尝试 2**: 从本地策略状态文件读取
```
结果：返回空
原因：策略状态文件未同步币安实际持仓（position: null）
```

---

## 📊 历史解决方案

### 查找到的历史文档

**位置**: `/root/.openclaw/workspace/quant/history/docs/report/币安 Algo Order API 完全实现.md`

**历史成功实现** (2026-03-10):
```python
# 创建止损单 ✅
client.place_stop_loss_order(
    symbol='ETHUSDT',
    side='SELL',
    quantity=0.001,
    stop_price=1938.95,
    reduce_only=True
)

# 获取 Algo 订单列表 ✅
orders = client.get_algo_orders(symbol='ETHUSDT', limit=10)

# 取消 Algo 订单 ✅
client.cancel_algo_order('ETHUSDT', algo_id=1000000022710898)
```

**关键参数**:
- `algoType`: `CONDITIONAL`（只支持这个）
- `type`: `STOP_MARKET`
- `triggerPrice`: 触发价格（不是 `stopPrice`）
- `reduceOnly`: `true`

---

## ✅ 最终解决方案

### 方案 A: 使用连接器 API（推荐）

**连接器已实现**: `connectors/binance/usdt_futures.py`

```python
def create_stop_loss_order(
    self, symbol: str, side: str, quantity: Decimal, 
    stop_price: Decimal = None, trigger_price: Decimal = None
) -> Result:
    """创建止损单（使用 Algo Order API）"""
    params = {
        "symbol": symbol,
        "side": side,
        "algoType": "CONDITIONAL",
        "type": "STOP_MARKET",
        "triggerPrice": str(price),
        "quantity": str(quantity),
        "reduceOnly": "false",
        "newOrderRespType": "ACK"
    }
    
    data = self._request("POST", "/fapi/v1/algoOrder", params=params, signed=True)
    
    return ok(data={
        "algo_id": str(data.get("orderId", "")),
        "symbol": data.get("symbol", ""),
        "trigger_price": str(price),
        "quantity": str(quantity),
        "status": data.get("orderStatus", "")
    })
```

**使用方式**:
```python
from connectors.binance.usdt_futures import BinanceUSDTFutures

client = BinanceUSDTFutures(api_key, secret_key, testnet=True)

result = client.create_stop_loss_order(
    symbol='ETHUSDT',
    side='SELL',
    quantity=Decimal('0.15'),
    stop_price=Decimal('2072.31')
)

if result.success:
    print(f"止损单创建成功：{result.data['algo_id']}")
```

---

### 方案 B: 查询止损单（替代方案）

**问题**: 币安测试网不支持查询 Algo Order 列表

**替代方案**: 从币安实际持仓 + 策略配置估算

```python
@router.get("/stop-loss")
async def get_stop_loss_orders(symbol: str = None):
    """获取止损单列表（从币安实际持仓 + 策略配置估算）"""
    try:
        # 1. 获取币安实际持仓
        positions_result = binance_request('GET', '/fapi/v2/positionRisk', signed=True)
        positions = positions_result.get('data', [])
        
        # 2. 获取策略配置
        strategy_config = get_strategy_config()  # 从策略状态文件读取
        
        orders = []
        for pos in positions:
            if pos['positionAmt'] == '0':
                continue
            
            symbol = pos['symbol']
            entry_price = Decimal(pos['entryPrice'])
            position_amt = Decimal(pos['positionAmt'])
            
            # 3. 从策略配置获取止损比例
            stop_loss_pct = strategy_config.get(symbol, {}).get('stop_loss_pct', 0.005)
            
            # 4. 计算止损价
            if position_amt > 0:  # LONG
                stop_price = entry_price * (1 - stop_loss_pct)
                side = 'SELL'
            else:  # SHORT
                stop_price = entry_price * (1 + stop_loss_pct)
                side = 'BUY'
            
            orders.append({
                'order_id': f"stop_{symbol}_{entry_price}",
                'symbol': symbol,
                'side': side,
                'algo_type': 'CONDITIONAL',
                'trigger_price': str(stop_price),
                'quantity': str(abs(position_amt)),
                'status': 'ESTIMATED',  # 标记为估算
                'entry_price': str(entry_price),
                'stop_loss_pct': str(stop_loss_pct)
            })
        
        return {
            'success': True,
            'orders': orders,
            'count': len(orders)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'orders': [],
            'count': 0
        }
```

---

## 📝 实施步骤

### 立即执行（P0）

1. ✅ **创建止损单** - 使用连接器 API
   - 文件：`connectors/binance/usdt_futures.py`
   - 函数：`create_stop_loss_order()`
   - 状态：✅ 已实现

2. ⏳ **查询止损单** - 使用替代方案
   - 文件：`web/binance_testnet_api.py`
   - 函数：`get_stop_loss_orders()`
   - 状态：⏳ 待实施（从币安持仓 + 策略配置估算）

3. ⏳ **策略状态同步** - 同步币安实际持仓
   - 文件：`core/strategy/strategy_manager.py`
   - 函数：`sync_positions()`
   - 状态：⏳ 待实施

---

### 短期执行（P1）

1. ⏳ **实盘测试** - 验证止损单 API
   - 测试网可能不支持完整功能
   - 需要实盘环境验证

2. ⏳ **自动止损单创建** - 策略开仓后自动创建
   - 文件：`strategies/*.py`
   - 函数：`open_position()` 后调用
   - 状态：✅ 代码已修复，待验证

---

### 长期执行（P2）

1. ⏳ **止损单管理面板** - Web 界面显示和管理
   - 显示所有止损单
   - 支持手动取消
   - 支持修改止损价

2. ⏳ **追踪止损** - 移动止损功能
   - 价格上升时自动上移止损价
   - 保护利润

---

## 🎯 总结

### 核心问题

1. ✅ **创建成功** - Algo Order API 正常
2. ❌ **查询失败** - 测试网不支持查询 Algo Order 列表
3. ⚠️ **状态不同步** - 策略状态文件未同步币安实际持仓

### 解决方案

1. ✅ **创建** - 使用连接器 API（已实现）
2. ⏳ **查询** - 从币安持仓 + 策略配置估算（待实施）
3. ⏳ **同步** - 定期同步币安实际持仓到策略状态（待实施）

---

**报告生成时间**: 2026-03-14 23:35  
**检查负责人**: AI Assistant  
**状态**: ⏳ 部分完成（创建成功，查询待修复）
