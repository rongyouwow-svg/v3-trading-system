#!/bin/bash
# 🛡️ V3 简单监控脚本 v2
# 核心：只监控进程，简单可靠

TELEGRAM_TOKEN="8784296779:AAFYFtE69lyvOFAAuRazuNbKZxG5mUtIQHk"
CHAT_ID="1233887750"
WORKDIR="/root/.openclaw/workspace/quant/v3-architecture"
SUPERVISORCTL="/root/.pyenv/versions/3.10.13/bin/supervisorctl"
SOCKET="unix://$WORKDIR/logs/supervisor.sock"
LOG_FILE="$WORKDIR/logs/monitor.log"
FAIL_FILE="$WORKDIR/logs/.monitor_fail_count"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

send_alert() {
    local msg="$1"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\":${CHAT_ID},\"text\":\"🚨 V3 监控\\n\\n${msg}\"}" > /dev/null
}

check_supervisor() {
    if ! pgrep -f supervisord > /dev/null; then
        log "⚠️ Supervisor 未运行，启动..."
        cd "$WORKDIR"
        /root/.pyenv/versions/3.10.13/bin/supervisord -c supervisor/supervisord.conf
        return 1
    fi
    return 0
}

check_strategy() {
    local strategy="$1"
    local status=$($SUPERVISORCTL -s $SOCKET status "$strategy" 2>&1 | awk '{print $2}')
    
    if [ "$status" != "RUNNING" ]; then
        log "❌ $strategy 异常 ($status)，重启..."
        $SUPERVISORCTL -s $SOCKET restart "$strategy" 2>/dev/null
        sleep 5
        return 1
    fi
    return 0
}

check_dashboard() {
    if ! curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        log "⚠️ Dashboard 无响应，重启..."
        pkill -9 -f uvicorn
        sleep 2
        cd "$WORKDIR"
        nohup /root/.pyenv/versions/3.10.13/bin/python3 -m uvicorn web.dashboard_api:app \
            --host 0.0.0.0 --port 3000 > logs/dashboard_out.log 2>&1 &
        return 1
    fi
    return 0
}

# 主循环
log "🛡️ V3 监控启动（简化版）"
send_alert "🛡️ V3 监控已启动\\n\\n检查频率：60 秒\\n告警规则：连续失败 3 次\\n监控内容：进程状态"

FAIL_COUNT=0

while true; do
    FAILED=0
    
    # 检查 Supervisor
    check_supervisor || FAILED=1
    
    # 检查策略
    for strategy in "quant-strategy-eth" "quant-strategy-link" "quant-strategy-avax"; do
        check_strategy "$strategy" || FAILED=1
    done
    
    # 检查 Dashboard
    check_dashboard || FAILED=1
    
    # 失败计数
    if [ $FAILED -eq 1 ]; then
        FAIL_COUNT=$((FAIL_COUNT+1))
        echo $FAIL_COUNT > "$FAIL_FILE"
        
        if [ $FAIL_COUNT -ge 3 ]; then
            send_alert "⚠️ 系统连续失败 $FAIL_COUNT 次\\n\\n请检查：$LOG_FILE"
            FAIL_COUNT=0
            sleep 300
        fi
    else
        FAIL_COUNT=0
        echo 0 > "$FAIL_FILE"
    fi
    
    sleep 60
done
