#!/bin/bash
# 🛡️ 防止老系统 gateway.py 重启的守护脚本

LOG_FILE="/home/admin/.openclaw/workspace/quant/v3-architecture/logs/anti_gateway_guard.log"

# 检查是否有老系统进程
if ps aux | grep "python.*gateway.py" | grep -v grep | grep -v "openclaw-gateway" > /dev/null; then
    echo "$(date): ⚠️ 发现老系统 gateway.py 进程，正在停止..." >> $LOG_FILE
    pkill -9 -f "python.*gateway.py"
    echo "$(date): ✅ 老系统已停止" >> $LOG_FILE
else
    echo "$(date): ✅ 系统正常，无老系统进程" >> $LOG_FILE
fi

# 确保 8080 端口未被占用
if sudo netstat -tlnp 2>/dev/null | grep ":8080" | grep -v "openclaw" > /dev/null; then
    echo "$(date): ⚠️ 发现 8080 端口被占用，正在清理..." >> $LOG_FILE
    PID=$(sudo netstat -tlnp 2>/dev/null | grep ":8080" | awk '{print $7}' | cut -d'/' -f1)
    if [ -n "$PID" ]; then
        sudo kill -9 $PID 2>/dev/null
        echo "$(date): ✅ 8080 端口已释放" >> $LOG_FILE
    fi
fi
