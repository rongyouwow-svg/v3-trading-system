#!/bin/bash
# 🔄 配置恢复脚本
# 用法：./restore_config.sh <备份文件名>

BACKUP_DIR="/root/.openclaw/workspace/quant/v3-architecture/backups"

if [ -z "$1" ]; then
    echo "❌ 请指定备份文件"
    echo "用法：$0 <备份文件名>"
    echo ""
    echo "可用备份:"
    ls -lh "$BACKUP_DIR"/*.tar.gz | tail -10
    exit 1
fi

BACKUP_FILE="$BACKUP_DIR/$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 备份文件不存在：$BACKUP_FILE"
    exit 1
fi

echo "🔄 开始恢复..."
echo "备份文件：$BACKUP_FILE"

# 解压备份
cd "$BACKUP_DIR"
tar -xzf "$BACKUP_FILE"

BACKUP_NAME=$(basename "$BACKUP_FILE" .tar.gz)

# 恢复配置
cp "$BACKUP_DIR/$BACKUP_NAME/.active_strategies" /root/.openclaw/workspace/quant/v3-architecture/ 2>/dev/null
cp "$BACKUP_DIR/$BACKUP_NAME/supervisor/"* /root/.openclaw/workspace/quant/v3-architecture/supervisor/ 2>/dev/null
cp "$BACKUP_DIR/$BACKUP_NAME/scripts/"* /root/.openclaw/workspace/quant/v3-architecture/scripts/ 2>/dev/null
cp "$BACKUP_DIR/$BACKUP_NAME/strategies/"* /root/.openclaw/workspace/quant/v3-architecture/strategies/ 2>/dev/null
cp "$BACKUP_DIR/$BACKUP_NAME/MEMORY.md" /root/.openclaw/workspace/ 2>/dev/null

# 清理临时文件
rm -rf "$BACKUP_DIR/$BACKUP_NAME"

echo "✅ 恢复完成"
echo ""
echo "请重启相关服务："
echo "  supervisorctl restart all"
echo "  systemctl --user restart strategy-guardian.service"
