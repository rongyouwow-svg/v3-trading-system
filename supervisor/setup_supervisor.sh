#!/bin/bash
# 🦞 大王量化 Web 服务 supervisor 启动脚本

SUPERVISOR_CONF="/home/admin/.openclaw/workspace/quant/v3-architecture/supervisor/quant-web.conf"
SYSTEM_SUPERVISOR="/etc/supervisor/conf.d/quant-web.conf"

echo "🔧 配置 supervisor..."

# 复制配置文件到系统目录
sudo cp $SUPERVISOR_CONF $SYSTEM_SUPERVISOR
echo "✅ 配置文件已复制"

# 重新加载 supervisor
sudo supervisorctl reread
echo "✅ 配置已重新加载"

# 更新配置
sudo supervisorctl update
echo "✅ 配置已更新"

# 启动服务
sudo supervisorctl start quant-web
echo "✅ Web 服务已启动"

# 查看状态
sudo supervisorctl status quant-web
echo "✅ 查看状态"

# 设置开机自启
sudo systemctl enable supervisor
echo "✅ 已设置开机自启"

echo ""
echo "================================"
echo "🎉 supervisor 配置完成！"
echo "================================"
echo ""
echo "常用命令:"
echo "  查看状态：sudo supervisorctl status quant-web"
echo "  重启服务：sudo supervisorctl restart quant-web"
echo "  停止服务：sudo supervisorctl stop quant-web"
echo "  查看日志：sudo tail -f /home/admin/.openclaw/workspace/quant/v3-architecture/logs/supervisor_web_err.log"
echo ""
