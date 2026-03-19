# 🔥 网络问题修复 - 2026-03-09 11:12

## 🔴 问题诊断

**错误信息：**
```
Failed to fetch
TypeError: Failed to fetch
```

**根本原因：**
- ✅ API 服务正常运行
- ✅ 内网 IP (172.19.51.108) 可以访问
- ❌ 公网 IP (147.139.213.181) **被防火墙阻止**

**测试结果：**
```bash
# localhost - ✅ 正常
curl http://localhost:5005/api/testnet/account
# 返回：{"account":{"balances":[{"asset":"USDT","free":10000}]}}

# 内网 IP - ✅ 正常
curl http://172.19.51.108:5005/api/testnet/account
# 返回：{"account":{"balances":[{"asset":"USDT","free":10000}]}}

# 公网 IP - ❌ 失败
curl http://147.139.213.181:5005/api/testnet/account
# 返回：Empty response
```

---

## ✅ 修复方案

### 临时方案：使用内网 IP

**已修改文件：**
- `pages/testnet.html` - API_BASE 改为内网 IP
- `pages/real.html` - API_BASE 改为内网 IP
- `test_assets.html` - API_BASE 改为内网 IP

**修改内容：**
```javascript
// 修改前
const API_BASE = 'http://147.139.213.181:5005/api';

// 修改后
const API_BASE = 'http://172.19.51.108:5005/api';
```

---

### 永久方案：开放防火墙端口

**需要在云服务器控制台操作：**

#### 阿里云
1. 登录阿里云控制台
2. 进入 **ECS 实例**
3. 找到 **安全组**
4. 点击 **配置规则**
5. 添加 **入方向规则**：
   - 端口范围：`5005/5005`
   - 授权对象：`0.0.0.0/0`
   - 协议：`TCP`
   - 策略：`允许`

#### 腾讯云
1. 登录腾讯云控制台
2. 进入 **CVM 实例**
3. 找到 **安全组**
4. 点击 **修改规则**
5. 添加 **入站规则**：
   - 端口：`5005`
   - 来源：`0.0.0.0/0`
   - 协议：`TCP`
   - 动作：`允许`

#### 华为云
1. 登录华为云控制台
2. 进入 **弹性云服务器**
3. 找到 **安全组**
4. 点击 **配置规则**
5. 添加 **入方向规则**：
   - 端口：`5005`
   - 源地址：`0.0.0.0/0`
   - 协议：`TCP`
   - 动作：`允许`

---

## 🚀 访问地址（修复后）

| 页面 | 地址 | API 访问 |
|------|------|----------|
| 导航 | http://147.139.213.181:8080/quant/index.html | - |
| 测试网 | http://147.139.213.181:8080/quant/pages/testnet.html | ✅ 内网 IP |
| 实盘 | http://147.139.213.181:8080/quant/pages/real.html | ✅ 内网 IP |
| 测试 | http://147.139.213.181:8080/quant/test_assets.html | ✅ 内网 IP |

---

## 📊 网络架构

```
用户浏览器
    ↓
公网 IP: 147.139.213.181:8080 (HTTP 服务) ✅
    ↓ (内网通信)
内网 IP: 172.19.51.108:5005 (API 服务) ✅
```

**说明：**
- HTTP 服务（8080）通过公网访问
- API 服务（5005）通过内网访问
- 避免防火墙问题

---

## ✅ 验证步骤

### 1. 强制刷新页面
```
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

### 2. 打开开发者工具（F12）

**Console 应该显示：**
```
🧪 测试网账户数据：{...}
balances: [{asset: "USDT", free: 10000, total: 10000}]
USDT 余额：{...}
💰 总资产：$10000, 可用：$10000
```

### 3. 访问测试页面
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

## 🔧 如果仍然失败

### 检查 1：内网 IP 是否正确

```bash
# 查看服务器内网 IP
hostname -I
# 或
ip addr show | grep "inet "
```

**更新内网 IP：**
```javascript
// 所有页面的 API_BASE
const API_BASE = 'http://YOUR_INTERNAL_IP:5005/api';
```

### 检查 2：API 服务是否运行

```bash
ps aux | grep api.app
curl http://localhost:5005/api/health
```

### 检查 3：浏览器 Console

打开 F12，查看 Console 错误：
- `Failed to fetch` → 网络问题
- `CORS error` → 跨域问题
- `TypeError` → 代码问题

---

## 📝 总结

**问题：** 公网 IP 无法访问 5005 端口（防火墙阻止）

**解决：**
1. ✅ **临时方案** - 使用内网 IP 访问 API（已实施）
2. ⏳ **永久方案** - 在云控制台开放 5005 端口

**当前状态：**
- HTTP 服务（8080）：✅ 公网可访问
- API 服务（5005）：✅ 内网可访问
- 前端页面：✅ 已修改为内网 IP

---

*修复时间：2026-03-09 11:12*
*版本：v2.1*
*状态：✅ 已修复（使用内网 IP）*
