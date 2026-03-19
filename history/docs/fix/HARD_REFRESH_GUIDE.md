# 🔄 强制清除缓存指南 - 2026-03-09 11:17

## 🔴 问题

**浏览器缓存了旧版本的页面代码**，仍在使用公网 IP 访问 API，导致 `Failed to fetch` 错误。

---

## ✅ 解决方案（必须按顺序执行）

### 步骤 1：打开开发者工具

**按 `F12`** 打开开发者工具

---

### 步骤 2：清除浏览器缓存

**Chrome/Edge:**

1. 按 `Ctrl + Shift + Delete`
2. 时间范围：选择 **"所有时间"**
3. 勾选：
   - ✅ 浏览历史记录
   - ✅ Cookie 及其他网站数据
   - ✅ 缓存的图片和文件
4. 点击 **"清除数据"**

**截图说明：**
```
清除浏览数据
├─ 时间范围：所有时间
├─ ☑ 浏览历史记录
├─ ☑ Cookie 及其他网站数据
├─ ☑ 缓存的图片和文件
└─ [清除数据]
```

---

### 步骤 3：清除 Service Worker

**Chrome/Edge:**

1. 在开发者工具中，切换到 **"Application"** 标签
2. 左侧选择 **"Service Workers"**
3. 点击 **"Unregister"** 删除所有 Service Worker
4. 勾选 **"Update on reload"**

**截图说明：**
```
Application → Service Workers
├─ [Unregister] (点击删除)
└─ ☑ Update on reload (勾选)
```

---

### 步骤 4：禁用缓存（开发模式）

**Chrome/Edge:**

1. 在开发者工具中，切换到 **"Network"** 标签
2. 勾选 **"Disable cache"**
3. **保持开发者工具打开状态**

**截图说明：**
```
Network 标签
└─ ☑ Disable cache (勾选此项)
```

---

### 步骤 5：强制刷新页面

**方法 A：快捷键**

**Windows/Linux:**
```
Ctrl + Shift + R
```

**Mac:**
```
Cmd + Shift + R
```

**方法 B：右键菜单（推荐）**

1. **右键点击** 浏览器的刷新按钮
2. 选择 **"清空缓存并硬性重新加载"**

**截图说明：**
```
右键点击刷新按钮
├─ 重新加载
├─ 硬性重新加载
└─ 清空缓存并硬性重新加载 ← 选择这个
```

---

### 步骤 6：验证修复

**打开开发者工具 Console，应该显示：**
```
🧪 测试网账户数据：{account: {...}}
balances: [{asset: "USDT", free: 10000, total: 10000}]
USDT 余额：{...}
💰 总资产：$10000, 可用：$10000
```

**页面应该显示：**
```
总资产：$10,000.00 ✅
可用资金：$10,000.00 ✅
```

**Network 标签应该显示：**
- `testnet/account` → 200 OK
- 请求 URL：`http://172.19.51.108:5005/api/testnet/account`

---

## 🧪 测试页面验证

**访问：**
```
http://147.139.213.181:8080/quant/test_assets.html
```

**应该显示：**
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

## ⚠️ 如果仍然显示$0.00

### 检查 1：Console 错误

**打开 F12 → Console，查看错误信息：**

- `Failed to fetch` → 仍在用公网 IP，缓存未清除
- `CORS error` → 跨域问题
- `TypeError` → 代码问题

### 检查 2：Network 请求

**打开 F12 → Network，刷新页面：**

1. 找到 `testnet/account` 请求
2. 查看 **Request URL**：
   - ✅ 正确：`http://172.19.51.108:5005/api/testnet/account`
   - ❌ 错误：`http://147.139.213.181:5005/api/testnet/account`

### 检查 3：页面源代码

**右键 → 查看页面源代码，搜索 `API_BASE`：**
```javascript
// 应该是：
const API_BASE = 'http://172.19.51.108:5005/api';

// 如果是：
const API_BASE = 'http://147.139.213.181:5005/api';
// 说明缓存未清除
```

---

## 🔧 终极解决方案

### 如果以上步骤都无效：

**1. 使用无痕模式**

**Chrome/Edge:**
```
Ctrl + Shift + N (Windows/Linux)
Cmd + Shift + N (Mac)
```

然后访问：
```
http://147.139.213.181:8080/quant/test_assets.html
```

**2. 使用其他浏览器**

- Firefox
- Safari
- Opera

**3. 添加时间戳参数**

访问时添加时间戳强制刷新：
```
http://147.139.213.181:8080/quant/pages/testnet.html?t=202603091117
```

---

## ✅ 检查清单

完成以下检查确保修复成功：

- [ ] 清除了浏览器缓存
- [ ] 清除了 Service Worker
- [ ] 禁用了 Network 缓存
- [ ] 强制刷新了页面
- [ ] Console 显示正确的 USDT 余额
- [ ] Network 请求使用内网 IP
- [ ] 页面显示 $10,000.00
- [ ] 测试页面通过所有测试

---

## 📞 仍然有问题？

**提供以下信息：**

1. **Console 截图** - F12 → Console 标签
2. **Network 截图** - F12 → Network 标签，找到 `testnet/account` 请求
3. **页面源代码** - 右键 → 查看页面源代码，搜索 `API_BASE`

---

*更新时间：2026-03-09 11:17*
*版本：v2.1*
*状态：🔍 等待用户清除缓存*
