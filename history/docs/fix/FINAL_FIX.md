# 🦞 最终修复验证指南

## ✅ 已修复的问题

### 问题 1：账户类型不同步
**原因：** 下拉框没有默认选中值，但变量设为'real'

**修复：**
```html
<!-- 修复前 -->
<option value="sim">模拟盘</option>
<option value="real">实盘</option>

<!-- 修复后 -->
<option value="sim">模拟盘</option>
<option value="real" selected>实盘</option>
```

### 问题 2：页面加载时账户类型未同步
**原因：** window.onload 没有同步 accountType 变量

**修复：**
```javascript
window.onload = function() {
    // 同步账户类型
    accountType = document.getElementById('account-type').value;
    console.log('[INIT] 页面加载，accountType:', accountType);
    
    loadAPIList();
    loadPositions();
    loadStrategies();
    loadAccountInfo();
    // ...
};
```

## 🚀 验证步骤

### 1. 强制刷新浏览器
```
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

### 2. 打开开发者工具（F12）

**查看 Console，应该看到：**
```
[INIT] 页面加载，accountType: real
[DEBUG] loadAccountInfo 开始，accountType: real
[DEBUG] 实盘模式，请求 API...
[DEBUG] API 返回：{account: {...}, success: true}
[DEBUG] USDT 余额：1 可用：1
```

### 3. 检查 Network 请求

**应该看到：**
- `GET /api/real/account` → 200 OK
- `GET /api/real/strategies` → 200 OK（返回 4 个策略）
- `GET /api/real/positions` → 200 OK

### 4. 验证页面显示

**应该显示：**
- ✅ 总资产：$1.00
- ✅ 可用资金：$1.00
- ✅ 账户类型：实盘（下拉框默认选中"实盘"）
- ✅ 持仓：显示"未配置 API"或持仓列表
- ✅ 策略：显示 4 个运行中的策略（ETH/BTC/UNI/LINK）
- ✅ 不再转圈！

## 📊 API 状态

**币安实盘 API（5005 端口）：**
```bash
# 账户信息
curl http://localhost:5005/api/real/account
# 返回：USDT $1.00

# 持仓
curl http://localhost:5005/api/real/positions
# 返回：未配置 API（需要添加币安 API Key）

# 策略
curl http://localhost:5005/api/real/strategies
# 返回：4 个活跃策略
```

## 🔧 如果还是不行

### 检查 1：清除所有缓存
1. 按 `Ctrl + Shift + Delete`
2. 选择"所有时间"
3. 勾选"缓存的图片和文件"
4. 点击"清除数据"

### 检查 2：使用无痕模式
```
Ctrl + Shift + N  (Chrome)
Ctrl + Shift + P  (Firefox)
```
然后访问：`http://147.139.213.181:8080/quant/dashboard_real.html`

### 检查 3：添加时间戳参数
```
http://147.139.213.181:8080/quant/dashboard_real.html?t=202603090930
```

### 检查 4：查看页面源代码
在页面右键 → "查看页面源代码"
搜索：`accountType = 'real'`
应该能看到这行代码。

## 📝 修改文件

- `/home/admin/.openclaw/workspace/quant/dashboard_real.html`
  - 第 256 行：添加 `selected` 属性
  - 第 360 行：添加账户类型同步逻辑
  - 第 572 行：添加 debug 日志

---

*修复时间：2026-03-09 09:30*
*版本：v202603090930*
