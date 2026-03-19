#!/bin/bash
# GitHub 上传脚本

REPO_URL="https://github.com/yourusername/v3-trading-system.git"
COMMIT_MESSAGE="V3 系统更新 - $(date +%Y-%m-%d)"

cd /root/.openclaw/workspace/quant/v3-architecture

# 初始化 Git（如果还没有）
if [ ! -d ".git" ]; then
    git init
    git remote add origin $REPO_URL
fi

# 添加文件
git add -A

# 提交
git commit -m "$COMMIT_MESSAGE"

# 推送
git push -u origin main

echo "✅ 上传完成！"
