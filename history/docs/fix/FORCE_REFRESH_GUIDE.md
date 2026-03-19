# 🦞 强制刷新指南

## 问题诊断

**症状：**
- 资金仍显示 $1000（应该是$1.00）
- 持仓和策略一直在"转圈"
- 账户类型显示"模拟盘"（应该是"实盘"）

**原因：浏览器缓存了旧版本的 HTML 文件**

## 解决方案

### 方法 1：强制刷新浏览器（推荐）

**Chrome/Edge:**
```
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

**Firefox:**
```
Ctrl + F5  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

**Safari:**
```
Cmd + Option + R  (Mac)
```

### 方法 2：清除缓存

**Chrome/Edge:**
1. 按 `F12` 打开开发者工具
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"

**Firefox:**
1. 按 `Ctrl + Shift + Delete`
2. 选择"缓存"
3. 点击"立即清除"

### 方法 3：使用隐私模式

打开新的隐私/无痕窗口：
```
Ctrl + Shift + N  (Chrome/Edge)
Ctrl + Shift + P  (Firefox)
Cmd + Shift + N   (Safari/Chrome Mac)
```

然后访问：
```
http://147.139.213.181:8080/quant/dashboard_real.html
```

## 验证修复

打开浏览器开发者工具（F12），查看 Console：

**应该看到：**
```
[DEBUG] loadAccountInfo 开始，accountType: real
[DEBUG] 实盘模式，请求 API...
[DEBUG] API 返回：{account: {...}, success: true}
[DEBUG] USDT 余额：1 可用：1
```

**不应该看到：**
```
[DEBUG] 模拟盘模式
```

## 检查网络请求

在开发者工具的 **Network** 标签中：

**应该看到这些请求：**
- `GET /api/real/account` → 200 OK
- `GET /api/real/positions` → 200 OK
- `GET /api/real/strategies` → 200 OK

**点击 `/api/real/account` 查看响应：**
```json
{
  "account": {
    "balances": [
      {
        "asset": "USDT",
        "free": 1.0,
        "locked": 0.0,
        "total": 1.0
      }
    ]
  },
  "success": true
}
```

## 预期结果

刷新后应该看到：

1. ✅ **总资产：$1.00**（不是$1000）
2. ✅ **可用资金：$1.00**（不是$1000）
3. ✅ **账户类型：实盘**（不是模拟盘）
4. ✅ **持仓：显示"未配置 API"**（不再转圈）
5. ✅ **策略：显示 4 个运行中的策略**（不再转圈）

## 如果还是不行

### 检查 1：页面版本

查看页面标题，应该包含版本号：
```
🦞 自动量化交易 - 实盘专业版 v202603090922
```

如果没有版本号，说明还在加载旧缓存。

### 检查 2：直接访问 HTML 文件

在浏览器地址栏输入：
```
http://147.139.213.181:8080/quant/dashboard_real.html?t=123456
```

添加时间戳参数强制刷新。

### 检查 3：服务器日志

查看 API 服务日志：
```bash
tail -f /tmp/real_trading_api.log
```

应该看到来自你 IP 的请求。

### 检查 4：手动测试 API

在浏览器控制台执行：
```javascript
fetch('http://147.139.213.181:5005/api/real/account')
  .then(r => r.json())
  .then(d => console.log('账户数据:', d))
```

应该看到真实的账户余额。

## 联系支持

如果以上方法都无效，请提供：
1. 浏览器类型和版本
2. 截图（包含开发者工具 Console）
3. Network 标签中的请求列表

---

*更新时间：2026-03-09 09:22*
*版本：v202603090922*
