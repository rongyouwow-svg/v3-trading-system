# 🔧 资产显示问题深度排查 - 2026-03-09 11:05

## 🔴 问题现象

**用户报告：** 测试网和实盘都显示 $0.00，但之前成功显示过

**Console 错误：**
```
Content Security Policy of your site blocks the use of 'eval' in JavaScript
script-src blocked
```

---

## 🔍 深度排查

### 1. API 服务检查

**测试：**
```bash
curl http://localhost:5005/api/testnet/account
```

**结果：** ✅ **正常**
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

**结论：** API 服务正常，返回正确的资产数据

---

### 2. 前端代码检查

**loadAccount() 函数：**
```javascript
async function loadAccount() {
    const resp = await fetch(`${API_BASE}/testnet/account?t=${Date.now()}`);
    const data = await resp.json();
    
    if (data.success && data.account && data.account.balances) {
        const usdt = data.account.balances.find(b => b.asset === 'USDT');
        if (usdt) {
            const total = usdt.total || 0;
            const available = usdt.free || 0;
            
            document.getElementById('total-capital').textContent = `$${total.toFixed(2)}`;
            document.getElementById('available-capital').textContent = `$${available.toFixed(2)}`;
        }
    }
}
```

**结论：** ✅ **代码逻辑正确**

---

### 3. CSP 配置检查

**问题根源：**

浏览器缓存了之前设置的严格 CSP 策略，即使我们已经移除了 CSP Meta 标签。

**解决方案：**

1. **清除浏览器缓存**（必须）
2. **强制刷新页面**
3. **清除 Service Worker**（如果有）

---

## ✅ 解决步骤

### 步骤 1：清除浏览器缓存

**Chrome/Edge:**
1. 按 `F12` 打开开发者工具
2. 按 `Ctrl + Shift + Delete`
3. 时间范围：**所有时间**
4. 勾选：
   - ✅ 浏览历史记录
   - ✅ Cookie 及其他网站数据
   - ✅ 缓存的图片和文件
5. 点击"清除数据"

**Firefox:**
1. 按 `Ctrl + Shift + Delete`
2. 时间范围：**全部**
3. 勾选：
   - ✅ Cookie
   - ✅ 缓存
4. 点击"立即清除"

---

### 步骤 2：清除 Service Worker

**Chrome/Edge:**
1. 打开开发者工具 (`F12`)
2. 切换到 **Application** 标签
3. 左侧选择 **Service Workers**
4. 点击 **Unregister** 删除所有 Service Worker
5. 勾选 **Update on reload**

---

### 步骤 3：强制刷新页面

**Windows/Linux:**
```
Ctrl + Shift + R
```

**Mac:**
```
Cmd + Shift + R
```

**或者：**
1. 按 `F12` 打开开发者工具
2. **右键点击** 刷新按钮
3. 选择 **"清空缓存并硬性重新加载"**

---

### 步骤 4：验证修复

**打开开发者工具 (`F12`)，查看：**

**Console 应该显示：**
```
🧪 测试网账户数据：{account: {...}}
balances: [{asset: "USDT", free: 10000, total: 10000}]
USDT 余额：{asset: "USDT", free: 10000, total: 10000}
💰 总资产：$10000, 可用：$10000
```

**Network 应该显示：**
- `testnet/account` → 200 OK
- `testnet/prices` → 200 OK
- `strategy/list` → 200 OK

**页面应该显示：**
- 总资产：**$10,000.00**
- 可用资金：**$10,000.00**

---

## 🧪 测试页面

**访问测试页面验证：**
```
http://147.139.213.181:8080/quant/test_assets.html
```

这个页面会：
1. 测试 API 连接
2. 显示原始 API 响应
3. 测试数据显示
4. 显示详细错误信息

**预期结果：**
```
✅ API 响应正常
💰 资产显示测试
   总资产：$10,000.00
   可用资金：$10,000.00
✅ 数据解析成功
✅ DOM 更新成功
✅ 页面显示正常
```

---

## 🐛 如果仍然显示$0.00

### 检查 1：API 服务是否运行

```bash
curl http://localhost:5005/api/health
# 应该返回：{"status":"ok","success":true}
```

### 检查 2：HTTP 服务是否运行

```bash
curl http://localhost:8080/quant/index.html
# 应该返回 HTML 内容
```

### 检查 3：Console 错误

打开 F12，查看 Console：
- 如果有 `ERR_EMPTY_RESPONSE` → API 服务崩溃
- 如果有 `CSP` 错误 → 清除浏览器缓存
- 如果有 `TypeError` → 检查 JavaScript 代码

### 检查 4：Network 请求

打开 F12 → Network 标签：
1. 刷新页面
2. 找到 `testnet/account` 请求
3. 查看 Response：
   ```json
   {
     "account": {
       "balances": [{"asset": "USDT", "free": 10000}]
     }
   }
   ```

---

## 📊 常见原因

| 原因 | 症状 | 解决方法 |
|------|------|----------|
| 浏览器缓存 | CSP 错误，显示$0 | 清除缓存 + 强制刷新 |
| API 服务崩溃 | ERR_EMPTY_RESPONSE | 重启 API 服务 |
| HTTP 服务崩溃 | 页面无法加载 | 重启 HTTP 服务 |
| 代码错误 | TypeError/ReferenceError | 检查 Console 错误 |
| Service Worker | 缓存旧版本 | 清除 Service Worker |

---

## 🚀 快速修复脚本

**一键清除缓存并重启服务：**

```bash
#!/bin/bash
# 重启所有服务
pkill -9 -f "api.app"
pkill -9 -f "http.server 8080"
sleep 2

cd /home/admin/.openclaw/workspace/quant
nohup python3 -m api.app > /tmp/api_v2.log 2>&1 &

cd /home/admin/.openclaw/workspace
nohup python3 -m http.server 8080 > /tmp/http_server.log 2>&1 &

sleep 5
echo "✅ 所有服务已重启"
curl http://localhost:5005/api/health
```

---

## ✅ 验证清单

- [ ] 清除浏览器缓存
- [ ] 清除 Service Worker
- [ ] 强制刷新页面
- [ ] Console 无 CSP 错误
- [ ] Network 所有请求 200 OK
- [ ] 页面显示 $10,000.00
- [ ] 测试页面通过所有测试

---

*排查时间：2026-03-09 11:05*
*版本：v2.1*
*状态：🔍 排查中*
