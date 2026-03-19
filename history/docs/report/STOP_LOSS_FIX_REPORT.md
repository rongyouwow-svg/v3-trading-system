# ✅ 止损单方法名修复报告

**修复时间：** 2026-03-12 13:24  
**执行人：** 龙虾王 AI  
**状态：** ⏳ 等待大王确认清理进程

---

## 🐛 问题发现

### 错误信息
```
'BinanceClient' object has no attribute 'place_algo_order'
```

### 根本原因
**方法名不匹配：**
- `stop_loss_manager.py` 调用：`place_algo_order()`
- `binance_client.py` 中的方法：`place_stop_loss_order()`

### 影响
- ❌ 所有止损单都失败
- ❌ LINK、AVAX 开仓成功但无止损
- ❌ ETH 开仓失败（保证金不足 + 无止损）

---

## ✅ 修复方案

### 修改文件
**文件：** `api/stop_loss_manager.py` 第 172 行

### 修改前
```python
result = self.rest.place_algo_order(...)
```

### 修改后
```python
result = self.rest.place_stop_loss_order(...)
```

### 验证
```bash
grep -n "place_stop_loss_order" api/stop_loss_manager.py
# 输出：172:            result = self.rest.place_stop_loss_order(
```

---

## 📊 当前状态

### 已执行
- ✅ 方法名已修改
- ✅ 网关已重启

### 待确认
- ⚠️ 网关进程数：3 个（应该是 1 个）
- ⚠️ 等待大王确认是否清理

### 下一步
1. ⏳ 等待大王确认清理多余进程
2. ⏳ 验证止损单功能
3. ⏳ 重新开仓测试

---

## 📝 等待大王确认

**请大王确认：**
- [ ] 可以清理多余进程（保留 1 个）
- [ ] 需要更多检查
- [ ] 其他指示

**我承诺：**
- ⚠️ 等待大王明确批准后再执行
- ⚠️ 绝不擅自操作

---

**报告人：** 龙虾王 AI  
**时间：** 2026-03-12 13:24  
**状态：** ⏳ 等待大王确认
