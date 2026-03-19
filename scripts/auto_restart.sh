#!/bin/bash
# 🦞 大王量化系统自动检查和重启脚本

LOG_FILE="/home/admin/.openclaw/workspace/quant/v3-architecture/logs/auto_restart.log"
HEALTH_URL="http://localhost:8000/api/strategy/health"
MAX_RESTART_ATTEMPTS=3
RESTART_ATTEMPTS=0

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

check_web_service() {
    # 检查 Web 服务是否响应
    response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL 2>/dev/null)
    if [ "$response" = "200" ]; then
        return 0
    else
        return 1
    fi
}

restart_web_service() {
    log "🔄 重启 Web 服务..."
    
    # 停止现有进程
    pkill -f "uvicorn web.dashboard_api:app" 2>/dev/null
    sleep 2
    
    # 启动新进程
    cd /home/admin/.openclaw/workspace/quant/v3-architecture
    nohup python3 -m uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000 > logs/web.log 2>&1 &
    
    # 等待启动
    sleep 5
    
    # 验证启动
    if check_web_service; then
        log "✅ Web 服务重启成功"
        return 0
    else
        log "❌ Web 服务重启失败"
        return 1
    fi
}

restart_strategies() {
    log "🔄 重启策略管理器..."
    
    cd /home/admin/.openclaw/workspace/quant/v3-architecture
    PYTHONPATH=/home/admin/.openclaw/workspace/quant/v3-architecture \
        nohup python3 scripts/start_all_strategies.py > logs/strategies.log 2>&1 &
    
    sleep 5
    log "✅ 策略管理器重启完成"
}

# 主循环
log "🚀 自动检查和重启脚本启动"
log "📊 检查间隔：60 秒"
log "📊 最大重启次数：$MAX_RESTART_ATTEMPTS"

while true; do
    if ! check_web_service; then
        log "⚠️ Web 服务无响应"
        
        if [ $RESTART_ATTEMPTS -lt $MAX_RESTART_ATTEMPTS ]; then
            RESTART_ATTEMPTS=$((RESTART_ATTEMPTS + 1))
            log "🔄 尝试重启 (第 $RESTART_ATTEMPTS 次)"
            
            if restart_web_service; then
                RESTART_ATTEMPTS=0
                restart_strategies
            fi
        else
            log "❌ 达到最大重启次数，停止尝试"
            exit 1
        fi
    else
        RESTART_ATTEMPTS=0
    fi
    
    sleep 60
done
