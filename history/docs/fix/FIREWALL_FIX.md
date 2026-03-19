# 🔧 API 防火墙问题解决方案 - 2026-03-09 11:41

## 🔴 问题诊断

**测试结果：**
- ✅ API 服务正常运行（localhost:5005）
- ✅ 内网 IP 可访问（172.19.51.108:5005）
- ❌ 公网 IP 无法访问（147.139.213.181:5005）

**原因：** 云服务器安全组/防火墙阻止了 5005 端口

---

## ✅ 解决方案

### 方案 1：开放防火墙端口（推荐）

**需要在云服务器控制台操作：**

#### 阿里云
1. 登录阿里云控制台
2. 进入 **ECS 实例** → **安全组**
3. 点击 **配置规则** → **入方向**
4. 添加规则：
   - 端口范围：`5005/5005`
   - 授权对象：`0.0.0.0/0`
   - 协议：`TCP`
   - 策略：`允许`

#### 腾讯云
1. 登录腾讯云控制台
2. 进入 **CVM 实例** → **安全组**
3. 点击 **修改规则** → **入站规则**
4. 添加规则：
   - 端口：`5005`
   - 来源：`0.0.0.0/0`
   - 协议：`TCP`
   - 动作：`允许`

#### 华为云
1. 登录华为云控制台
2. 进入 **弹性云服务器** → **安全组**
3. 点击 **配置规则** → **入方向**
4. 添加规则：
   - 端口：`5005`
   - 源地址：`0.0.0.0/0`
   - 协议：`TCP`
   - 动作：`允许`

**开放后测试：**
```bash
curl http://147.139.213.181:5005/api/health
# 应该返回：{"status":"ok","success":true}
```

---

### 方案 2：SSH 隧道转发（临时）

**如果你无法修改防火墙：**

**本地执行：**
```bash
# 创建 SSH 隧道，将本地 5005 端口转发到服务器
ssh -L 5005:localhost:5005 admin@147.139.213.181 -N
```

**然后修改前端代码：**
```javascript
const API_BASE = 'http://localhost:5005/api';
```

**保持 SSH 连接不断开**

---

### 方案 3：使用 Nginx 反向代理（高级）

**安装 Nginx：**
```bash
sudo apt update
sudo apt install nginx -y
```

**配置 Nginx：**
```bash
sudo nano /etc/nginx/sites-available/quant-api
```

**添加配置：**
```nginx
server {
    listen 80;
    server_name 147.139.213.181;
    
    location /api/ {
        proxy_pass http://localhost:5005/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**启用配置：**
```bash
sudo ln -s /etc/nginx/sites-available/quant-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**访问：**
```
http://147.139.213.181/api/health
```

---

## 🚀 当前代码配置

**已修改为公网 IP：**
```javascript
const API_BASE = 'http://147.139.213.181:5005/api';
```

**文件：**
- ✅ `pages/testnet.html`
- ✅ `pages/real.html`
- ✅ `diagnostic.html`

---

## 📊 测试步骤

### 1. 开放防火墙后测试

**访问：**
```
http://147.139.213.181:5005/api/health
```

**预期：**
```json
{"status":"ok","success":true}
```

### 2. 清除浏览器缓存

```
F12 → Ctrl+Shift+Delete → 清除缓存
```

### 3. 刷新诊断页面

**访问：**
```
http://147.139.213.181:8080/quant/diagnostic.html
```

**点击"运行完整诊断"**

**预期：**
```
📊 诊断报告
API 服务：✅
测试网资产：✅ $10000
页面版本：✅ 公网 IP

✅ 所有测试通过！
```

---

## ⚠️ 如果仍然失败

### 检查 1：防火墙状态

**查看 iptables：**
```bash
sudo iptables -L INPUT -n | grep 5005
```

**查看 ufw：**
```bash
sudo ufw status | grep 5005
```

### 检查 2：安全组规则

**登录云服务器控制台，确认：**
- ✅ 入方向规则已添加
- ✅ 端口 5005 已开放
- ✅ 协议 TCP
- ✅ 来源 0.0.0.0/0

### 检查 3：本地测试

**在服务器上测试：**
```bash
curl http://localhost:5005/api/health
# 应该返回：{"status":"ok"}

curl http://147.139.213.181:5005/api/health
# 如果失败 → 防火墙问题
```

---

## 📝 总结

**问题：** 云服务器防火墙阻止 5005 端口

**解决：**
1. ✅ **推荐** - 在云控制台开放 5005 端口
2. ⏳ **临时** - 使用 SSH 隧道转发
3. ⏳ **高级** - 使用 Nginx 反向代理（80 端口）

**当前状态：**
- 代码已更新为公网 IP
- 等待防火墙开放

---

*更新时间：2026-03-09 11:41*
*状态：⏳ 等待开放防火墙*
