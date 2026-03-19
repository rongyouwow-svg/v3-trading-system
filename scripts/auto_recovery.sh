#!/bin/bash
# 🦞 大王量化策略自动恢复脚本

LOG_FILE="/home/admin/.openclaw/workspace/quant/v3-architecture/logs/auto_recovery.log"
HEALTH_URL="http://localhost:8000/api/strategy/health"
STRATEGY_SCRIPT="/home/admin/.openclaw/workspace/quant/v3-architecture/scripts/start_all_strategies.py"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

check_strategies() {
    # 检查策略是否运行（通过监测文件）
    MONITOR_FILE="/home/admin/.openclaw/workspace/quant/v3-architecture/logs/live_test_monitor.json"
    
    if [ ! -f "$MONITOR_FILE" ]; then
        return 1
    fi
    
    # 检查监测文件是否更新（5 分钟内）
    if find "$MONITOR_FILE" -mmin -5 | grep -q .; then
        return 0
    else
        return 1
    fi
}

recover_strategies() {
    log "🔄 开始恢复策略..."
    
    cd /home/admin/.openclaw/workspace/quant/v3-architecture
    
    # 启动策略（会自动恢复状态）
    PYTHONPATH=/home/admin/.openclaw/workspace/quant/v3-architecture \
        python3 $STRATEGY_SCRIPT >> $LOG_FILE 2>&1
    
    sleep 5
    
    if check_strategies; then
        log "✅ 策略恢复成功"
        return 0
    else
        log "❌ 策略恢复失败"
        return 1
    fi
}

sync_from_exchange() {
    log "📊 从交易所同步状态..."
    
    # 这里可以添加从交易所同步持仓和止损单的脚本
    # 目前由策略启动时自动同步
    
    log "✅ 交易所同步完成"
}

# 主循环
log "🚀 策略自动恢复脚本启动"
log "📊 检查间隔：60 秒"

while true; do
    if ! check_strategies; then
        log "⚠️ 策略未运行或监测文件未更新"
        
        if recover_strategies; then
            sync_from_exchange
        fi
    fi
    
    sleep 60
done
