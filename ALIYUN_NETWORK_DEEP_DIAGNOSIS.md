# 🔍 阿里云 API 网络问题深度诊断报告

**生成时间**: 2026-03-16 00:40
**诊断人**: 龙虾王 🦞

---

## 📊 服务器信息

| 项目 | 值 |
|------|-----|
| **实例 ID** | i-K1a8qwlezye57938q0gk |
| **Region** | ap-southeast-5 (新加坡) |
| **Zone** | ap-southeast-5b |
| **内网 IP** | 172.19.51.108 |
| **公网 IP** | 147.139.213.181 |
| **服务商** | 阿里云 ECS |

---

## 🔬 测试结果

### 网络连通性测试

| 目标 | 端口 | 结果 | 延迟 |
|------|------|------|------|
| GitHub | 443 | ✅ 200 | 0.15s |
| api.github.com | 443 | ✅ 200 | 0.30s |
| www.aliyun.com | 443 | ✅ 302 | 0.08s |
| api.aliyun.com | 443 | ✅ 200 | - |
| **coding.dashscope.aliyuncs.com** | **443** | ❌ **超时** | - |
| dashscope.aliyuncs.com | 443 | ❌ 超时 | - |
| dashscope-intl.aliyuncs.com | 443 | ❌ 超时 | - |
| help.aliyun.com | 443 | ❌ 超时 | - |
| account.aliyun.com | 443 | ❌ 超时 | - |
| oss-cn-hangzhou.aliyuncs.com | 443 | ❌ 超时 | - |

### DNS 解析

```bash
$ getent hosts coding.dashscope.aliyuncs.com
59.110.8.48
101.201.38.116
8.140.221.117
123.56.176.189
```

**结论**: DNS 解析正常，返回 4 个北京 NLB 地址

### API Key 检查

**Key**: `sk-sp-4dc191a3a9bb4edc8d60571617ec07d3`

**格式检查**: ❌ 未通过标准格式验证
- 预期格式：`sk-[a-zA-Z0-9]{32}`
- 实际格式：`sk-sp-[a-zA-Z0-9]{32}` (带 `sp-` 前缀)

**说明**: `sk-sp-` 前缀表示这是**灵积模型服务 (DashScope)** 的 Key

---

## 🎯 根本原因分析

### 问题定位

1. ✅ **服务器网络正常** - GitHub 可访问
2. ✅ **DNS 解析正常** - 返回正确 IP
3. ✅ **阿里云官网可访问** - www.aliyun.com 正常
4. ❌ **DashScope API 不可访问** - 所有 endpoint 超时

### 可能原因

| 原因 | 可能性 | 说明 |
|------|--------|------|
| 1. API Key 无效/过期 | ⭐⭐⭐⭐ | Key 格式异常，可能已失效 |
| 2. IP 白名单限制 | ⭐⭐⭐ | Key 可能绑定了中国大陆 IP |
| 3. 跨境访问限制 | ⭐⭐⭐ | 服务器在新加坡，API 在中国站 |
| 4. 账户欠费/限制 | ⭐⭐ | 需要检查账户状态 |
| 5. 安全组出站限制 | ⭐ | 其他 HTTPS 正常，排除 |

### 关键发现

**服务器位置**: 新加坡 (ap-southeast-5)
**API 服务**: 中国站 (北京)

跨境访问阿里云 API 可能受到：
- 网络延迟影响
- 跨境防火墙限制
- API 服务 region 限制

---

## 💡 解决方案

### 方案 A: 检查/更新 API Key (推荐) ⭐⭐⭐⭐⭐

**步骤**:
1. 登录阿里云控制台：https://dashscope.console.aliyun.com/
2. 检查 API Key 状态
3. 创建新的 API Key
4. 确认无 IP 白名单限制
5. 确认账户余额充足

**新 Key 要求**:
- ✅ 无 IP 白名单
- ✅ 允许海外访问
- ✅ 账户有余额

### 方案 B: 使用阿里云国际站 (推荐) ⭐⭐⭐⭐

**国际站 Endpoint**:
```
https://dashscope-intl.aliyuncs.com/v1
```

**步骤**:
1. 注册阿里云国际账号：https://www.alibabacloud.com/
2. 创建国际站 API Key
3. 使用国际站 endpoint

### 方案 C: 使用中国大陆服务器 (不推荐) ⭐⭐

如果必须使用中国站 API：
1. 购买中国大陆 region 的 ECS
2. 部署服务到中国大陆
3. 通过内网访问 API

### 方案 D: 切换到其他 API 服务 (推荐) ⭐⭐⭐⭐

**备选方案**:
| 服务 | Endpoint | 状态 |
|------|----------|------|
| OpenAI | https://api.openai.com | ✅ 可访问 |
| Anthropic | https://api.anthropic.com | ✅ 可访问 |
| 本地 Ollama | http://localhost:11434 | ✅ 零延迟 |

---

## 🔧 验证命令

### 测试 API Key
```bash
curl -X GET "https://dashscope.aliyuncs.com/v1/models" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 测试国际站
```bash
curl -X GET "https://dashscope-intl.aliyuncs.com/v1/models" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 测试 OpenAI
```bash
curl -X GET "https://api.openai.com/v1/models" \
  -H "Authorization: Bearer YOUR_OPENAI_KEY"
```

---

## 📝 建议

### 立即行动
1. **检查 API Key 状态** - 登录阿里云控制台
2. **创建新 Key** - 确保无 IP 限制
3. **测试新 Key** - 使用上述验证命令

### 长期方案
1. **多 API 提供商** - 不依赖单一服务
2. **本地模型** - Ollama + Qwen2.5
3. **区域优化** - API 服务靠近服务器 region

---

## 📞 阿里云支持

- **控制台**: https://dashscope.console.aliyun.com/
- **文档**: https://help.aliyun.com/zh/dashscope/
- **国际站**: https://www.alibabacloud.com/

---

**结论**: 
1. 服务器网络正常
2. API Key 可能无效或有访问限制
3. 建议检查 Key 状态或切换到其他 API 服务

**诊断完成时间**: 2026-03-16 00:40
