#!/bin/bash
# 🛡️ 策略守护脚本 - 每 60 秒检查策略进程
# 发现异常立即重启并发送告警

TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID="1233887750"
SUPERVISORCTL="/root/.pyenv/versions/3.10.13/bin/supervisorctl"
SUPERVISOR_SOCKET="unix:///root/.openclaw/workspace/quant/v3-architecture/logs/supervisor.sock"
SUPERVISOR_CONF="/root/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf"
LOG_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/strategy_guardian.log"
LAST_RESTART_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/.last_restart"

send_alert() {
    local message="$1"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\":${CHAT_ID},\"text\":\"🛡️ 策略守护告警\\n\\n${message}\",\"parse_mode\":\"Markdown\"}" > /dev/null
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

get_strategy_status() {
    local strategy_name="$1"
    local status=$($SUPERVISORCTL -s $SUPERVISOR_SOCKET status "$strategy_name" 2>&1)
    
    if echo "$status" | grep -q "refused"; then
        echo "SUPERVISOR_DOWN"
        return
    fi
    
    echo "$status" | awk '{print $2}'
}

check_and_fix() {
    local strategy_name="$1"
    local status=$(get_strategy_status "$strategy_name")
    
    # 如果 Supervisor 挂了，先重启 Supervisor
    if [ "$status" = "SUPERVISOR_DOWN" ]; then
        log "⚠️ Supervisor 未运行，尝试重启..."
        
        # 检查是否刚重启过（5 分钟内），避免无限循环
        local last_restart=$(cat "$LAST_RESTART_FILE" 2>/dev/null || echo 0)
        local now=$(date +%s)
        local diff=$((now - last_restart))
        
        if [ "$diff" -lt 300 ]; then
            log "⏳ Supervisor 刚重启过（${diff}秒前），等待..."
            return
        fi
        
        echo "$now" > "$LAST_RESTART_FILE"
        
        pkill -9 supervisord
        sleep 3
        cd /root/.openclaw/workspace/quant/v3-architecture
        /root/.pyenv/versions/3.10.13/bin/supervisord -c $SUPERVISOR_CONF
        sleep 5
        
        local new_status=$(get_strategy_status "$strategy_name")
        if [ "$new_status" = "RUNNING" ]; then
            log "✅ Supervisor 重启成功，$strategy_name 已恢复"
            send_alert "✅ Supervisor 已重启\\n$strategy_name 已恢复运行"
        else
            log "⚠️ Supervisor 重启后 $strategy_name 仍未运行，等待下次检查"
        fi
        return
    fi
    
    # 策略异常处理
    if [ "$status" != "RUNNING" ]; then
        log "❌ $strategy_name 异常 (状态：$status)，尝试重启..."
        send_alert "策略异常：$strategy_name\\n状态：$status\\n操作：正在重启"
        
        $SUPERVISORCTL -s $SUPERVISOR_SOCKET restart "$strategy_name" 2>/dev/null
        sleep 5
        
        local new_status=$(get_strategy_status "$strategy_name")
        if [ "$new_status" = "RUNNING" ]; then
            log "✅ $strategy_name 重启成功"
            send_alert "✅ 策略已恢复：$strategy_name\\n新状态：RUNNING"
        else
            log "⚠️ $strategy_name 重启失败，等待 Supervisor 处理"
        fi
    fi
}

log "🛡️ 策略守护启动（增强版）"
send_alert "🛡️ 策略守护已启动（增强版）\\n检查频率：每 60 秒\\n监控策略：ETH, LINK, AVAX"

while true; do
    check_and_fix "quant-strategy-eth"
    sleep 5
    check_and_fix "quant-strategy-link"
    sleep 5
    check_and_fix "quant-strategy-avax"
    sleep 45  # 总共 60 秒检查一次
    
    # 检查 Dashboard（每 5 分钟）
    if ! curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        log "⚠️ Dashboard 无响应，尝试重启..."
        pkill -9 -f uvicorn
        sleep 2
        cd /root/.openclaw/workspace/quant/v3-architecture
        nohup /root/.pyenv/versions/3.10.13/bin/python3 -m uvicorn web.dashboard_api:app \
            --host 0.0.0.0 --port 3000 --timeout-keep-alive 30 > logs/dashboard_out.log 2>&1 &
        log "✅ Dashboard 已重启"
    fi
done
