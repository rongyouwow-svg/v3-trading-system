#!/bin/bash
# Web Dashboard 自动重启脚本

LOG_FILE="/home/admin/.openclaw/workspace/quant/v3-architecture/logs/web_monitor.log"
PID_FILE="/home/admin/.openclaw/workspace/quant/v3-architecture/logs/web.pid"
PORT=3000

# 检查进程是否存在
if ! ps aux | grep "uvicorn web.dashboard_api:app" | grep -v grep > /dev/null; then
    echo "$(date): Web 服务已停止，正在重启..." >> $LOG_FILE
    
    # 启动服务
    cd /home/admin/.openclaw/workspace/quant/v3-architecture
    nohup uvicorn web.dashboard_api:app --host 0.0.0.0 --port $PORT > logs/web_dashboard.log 2>&1 &
    echo $! > $PID_FILE
    
    sleep 3
    
    # 验证是否启动成功
    if ps aux | grep "uvicorn web.dashboard_api:app" | grep -v grep > /dev/null; then
        echo "$(date): Web 服务重启成功 (PID: $(cat $PID_FILE))" >> $LOG_FILE
    else
        echo "$(date): Web 服务重启失败" >> $LOG_FILE
    fi
else
    echo "$(date): Web 服务运行正常" >> $LOG_FILE
fi
