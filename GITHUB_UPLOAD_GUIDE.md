# GitHub 上传指南

## 准备工作

### 1. 创建 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token"
3. 选择权限：`repo` (完整仓库权限)
4. 生成并复制 Token

### 2. 设置环境变量

```bash
export GITHUB_TOKEN="your_token_here"
export GITHUB_USERNAME="your_username"
export GITHUB_REPO="v3-trading-system"
```

## 上传方法

### 方法 1：使用上传脚本

```bash
cd /root/.openclaw/workspace/quant/v3-architecture
./upload_to_github.sh
```

### 方法 2：手动 Git 命令

```bash
cd /root/.openclaw/workspace/quant/v3-architecture

# 初始化
git init
git remote add origin https://GITHUB_TOKEN@github.com/USERNAME/REPO.git

# 添加文件
git add -A
git commit -m "V3 系统初始化"

# 推送
git push -u origin main
```

### 方法 3：使用 GitHub API

```bash
# 示例：上传单个文件
curl -X PUT \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Upload file",
    "content": "BASE64_ENCODED_CONTENT"
  }' \
  "https://api.github.com/repos/USERNAME/REPO/contents/path/to/file"
```

## 安全注意事项

⚠️ **绝对不要提交的内容**:

- `.env` 文件（真实 API Key）
- `config/api_keys.json`（真实密钥）
- 任何包含真实 Token 的文件
- 日志文件
- 密码文件

✅ **可以提交的内容**:

- 代码文件（.py）
- 配置文件示例（.example）
- 文档（.md）
- 依赖文件（requirements.txt）

## 验证上传

上传后检查：

1. 仓库中是否有代码
2. 是否有敏感信息泄露
3. README.md 是否正确显示

## 后续更新

```bash
# 日常更新
git add -A
git commit -m "更新内容"
git push
```

## 问题排查

### Git 未安装
```bash
yum install git -y
```

### Token 无效
重新生成 Token 并更新环境变量

### 推送失败
检查仓库权限和 Token 权限
