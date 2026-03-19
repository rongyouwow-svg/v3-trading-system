# 🔄 强制刷新指南

## 问题原因

**浏览器缓存了旧版本的页面代码**，导致资产显示为$0.00

---

## 解决方法

### 方法 1：硬刷新（推荐）

**Windows/Linux:**
```
Ctrl + Shift + R
```

**Mac:**
```
Cmd + Shift + R
```

### 方法 2：清除缓存

**Chrome/Edge:**
1. 按 `F12` 打开开发者工具
2. 按 `Ctrl + Shift + Delete`
3. 选择"缓存的图片和文件"
4. 点击"清除数据"
5. 刷新页面

**Firefox:**
1. 按 `Ctrl + Shift + Delete`
2. 选择"缓存"
3. 点击"立即清除"
4. 刷新页面

### 方法 3：无痕模式

**Chrome/Edge:**
```
Ctrl + Shift + N
```

**Firefox:**
```
Ctrl + Shift + P
```

然后访问：
```
http://147.139.213.181:8080/quant/pages/testnet.html
```

### 方法 4：添加时间戳

访问时添加时间戳参数：
```
http://147.139.213.181:8080/quant/pages/testnet.html?t=123456
```

---

## 验证步骤

### 1. 打开开发者工具（F12）

### 2. 查看 Console

**应该看到：**
```
🧪 测试网账户数据：{account: {balances: [...]}}
balances: [{asset: "USDT", free: 10000, total: 10000}]
USDT 余额：{asset: "USDT", free: 10000, total: 10000}
💰 总资产：$10000, 可用：$10000
```

**不应该看到：**
```
⚠️ 无余额数据
```

### 3. 检查 Network

1. 切换到 Network 标签
2. 刷新页面
3. 找到 `testnet/account` 请求
4. 查看 Response：
```json
{
  "account": {
    "balances": [{
      "asset": "USDT",
      "free": 10000,
      "total": 10000
    }]
  },
  "success": true
}
```

### 4. 页面显示

**测试网应该显示：**
- 总资产：$10,000.00
- 可用资金：$10,000.00

**实盘应该显示：**
- 总资产：$0.00（未配置 API Key）
- 可用资金：$0.00

---

## 常见问题

### Q: 刷新后还是$0.00
**A:** 
1. 检查 Console 是否有错误
2. 确认 API 服务运行正常
3. 尝试无痕模式

### Q: Console 显示"无法连接"
**A:**
1. 检查 API 服务是否运行：`ps aux | grep api.app`
2. 重启 API 服务

### Q: 页面显示"加载中..."
**A:**
1. 检查网络连接
2. 查看 Console 错误
3. 刷新页面

---

## 快速测试

访问测试 API 页面：
```
http://147.139.213.181:8080/quant/test_api.html
```

如果 API 测试页面显示正常，说明服务正常，只是页面缓存问题。

---

*更新时间：2026-03-09*
*版本：v2.1*
