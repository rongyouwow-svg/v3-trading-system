#!/bin/bash
# 🗄️ 自动备份脚本
# 功能：自动备份所有关键配置文件

BACKUP_DIR="/root/.openclaw/workspace/quant/v3-architecture/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"

# 创建备份目录
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

echo "🗄️ 开始备份..."
echo "备份目录：$BACKUP_DIR/$BACKUP_NAME"

# 备份配置文件
cp -r /root/.openclaw/workspace/quant/v3-architecture/.active_strategies "$BACKUP_DIR/$BACKUP_NAME/" 2>/dev/null
cp -r /root/.openclaw/workspace/quant/v3-architecture/supervisor/*.conf "$BACKUP_DIR/$BACKUP_NAME/" 2>/dev/null
cp -r /root/.openclaw/workspace/quant/v3-architecture/scripts/*.sh "$BACKUP_DIR/$BACKUP_NAME/scripts/" 2>/dev/null
cp -r /root/.openclaw/workspace/quant/v3-architecture/scripts/*.py "$BACKUP_DIR/$BACKUP_NAME/scripts/" 2>/dev/null
cp -r /root/.openclaw/workspace/quant/v3-architecture/strategies/*.py "$BACKUP_DIR/$BACKUP_NAME/strategies/" 2>/dev/null

# 备份 MEMORY.md
cp /root/.openclaw/workspace/MEMORY.md "$BACKUP_DIR/$BACKUP_NAME/" 2>/dev/null

# 压缩备份
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# 清理旧备份（保留最近 10 个）
cd "$BACKUP_DIR"
ls -t backup_*.tar.gz | tail -n +11 | xargs rm -f 2>/dev/null

echo "✅ 备份完成：$BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo ""
echo "备份列表:"
ls -lh "$BACKUP_DIR"/*.tar.gz | tail -10
