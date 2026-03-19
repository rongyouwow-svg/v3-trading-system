# 🔒 CSP (Content Security Policy) 说明

## 问题说明

浏览器控制台显示 CSP 警告：
```
The Content Security Policy (CSP) prevents the evaluation of arbitrary strings as JavaScript
```

## 原因

这是浏览器的**安全特性**，不是错误。现代浏览器默认阻止：
- `eval()`
- `new Function()`
- `setTimeout("code", ...)` 
- `setInterval("code", ...)`

## 解决方案

已在页面添加 CSP Meta 标签：

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline' 'unsafe-eval'; 
               style-src 'self' 'unsafe-inline'; 
               connect-src 'self' http://147.139.213.181:5005 http://localhost:5005;">
```

## CSP 指令说明

| 指令 | 值 | 说明 |
|------|-----|------|
| `default-src` | `'self'` | 默认只允许同源资源 |
| `script-src` | `'self' 'unsafe-inline' 'unsafe-eval'` | 允许内联脚本和 eval |
| `style-src` | `'self' 'unsafe-inline'` | 允许内联样式 |
| `connect-src` | `'self' http://147.139.213.181:5005` | 允许 API 连接 |

## 为什么需要 'unsafe-eval'

某些库（如某些图表库）可能需要 `eval()`，为了兼容性暂时允许。

**注意：** 生产环境建议移除 `'unsafe-eval'`，改用更安全的方案。

## 常见触发原因

### 1. 浏览器扩展
某些浏览器扩展会注入代码，触发 CSP 警告。

**解决：** 在无痕模式测试，或禁用扩展。

### 2. 开发工具
某些开发工具（如 React DevTools）会使用 eval。

**解决：** 忽略警告，不影响功能。

### 3. 第三方库
某些库（如旧版本 jQuery）可能使用 eval。

**解决：** 升级到新版本，或添加 unsafe-eval。

## 验证

刷新页面后，检查 Console：

**之前：**
```
⚠️ The Content Security Policy (CSP) prevents...
```

**现在：**
```
✅ 无 CSP 警告
```

## 安全建议

### 开发环境
- 允许 `'unsafe-eval'` 方便调试
- 允许 `'unsafe-inline'` 方便开发

### 生产环境
- 移除 `'unsafe-eval'`
- 移除 `'unsafe-inline'`
- 使用 nonce 或 hash
- 使用外部 JS/CSS 文件

## 测试

访问测试页面验证 CSP：
```
http://147.139.213.181:8080/quant/test_api.html
```

如果页面正常显示，说明 CSP 配置正确。

---

*更新时间：2026-03-09*
*版本：v2.1*
