#!/bin/bash
# Dashboard 看门狗 - 每 60 秒检查一次

LOG_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/dashboard_watchdog.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

while true; do
    # 检查 Dashboard 进程
    if ! pgrep -f "uvicorn.*3000" > /dev/null; then
        log "🚨 Dashboard 进程丢失！尝试重启..."
        
        # 清理残留
        pkill -9 -f uvicorn 2>/dev/null
        rm -f /root/.openclaw/workspace/quant/v3-architecture/logs/*.sock
        
        # 重启
        cd /root/.openclaw/workspace/quant/v3-architecture
        nohup /root/.pyenv/versions/3.10.13/bin/python3 -m uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000 --timeout-keep-alive 30 > logs/dashboard_out.log 2>&1 &
        
        sleep 5
        
        # 验证
        if pgrep -f "uvicorn.*3000" > /dev/null; then
            log "✅ Dashboard 重启成功"
        else
            log "❌ Dashboard 重启失败"
        fi
    else
        log "✅ Dashboard 正常运行"
    fi
    
    sleep 60
done
