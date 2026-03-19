#!/bin/bash
# 🛡️ 策略守护脚本 v2 - 智能告警版本
# 核心改进：告警合并 + 冷却机制 + 智能降噪

TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID="1233887750"
SUPERVISORCTL="/root/.pyenv/versions/3.10.13/bin/supervisorctl"
SUPERVISOR_SOCKET="unix:///root/.openclaw/workspace/quant/v3-architecture/logs/supervisor.sock"
SUPERVISOR_CONF="/root/.openclaw/workspace/quant/v3-architecture/supervisor/supervisord.conf"
LOG_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/strategy_guardian.log"
LAST_RESTART_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/.last_restart"
ALERT_COOLDOWN_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/.alert_cooldown"

# 告警冷却时间（秒）
ALERT_COOLDOWN=300  # 5 分钟
RESTART_COOLDOWN=300  # 5 分钟

# 告警队列（用于合并）
declare -a ALERT_QUEUE

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

send_alert() {
    local message="$1"
    local force="$2"
    
    # 检查冷却
    if [ "$force" != "force" ]; then
        local now=$(date +%s)
        local last_alert=$(cat "$ALERT_COOLDOWN_FILE" 2>/dev/null || echo 0)
        local diff=$((now - last_alert))
        
        if [ "$diff" -lt "$ALERT_COOLDOWN" ]; then
            log "⏳ 告警冷却中（${diff}秒前发送过），跳过"
            return
        fi
    fi
    
    # 发送告警
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\":${CHAT_ID},\"text\":\"🛡️ 策略守护告警\\n\\n${message}\",\"parse_mode\":\"Markdown\"}" > /dev/null
    
    # 更新冷却时间
    date +%s > "$ALERT_COOLDOWN_FILE"
    log "✅ 告警已发送"
}

send_startup_notification() {
    local message="🛡️ 策略守护已启动（智能版）\\n\\n"
    message+="📊 监控策略：ETH, LINK, AVAX\\n"
    message+="⏱️ 检查频率：每 60 秒\\n"
    message+="🔕 告警冷却：5 分钟\\n"
    message+="🔄 重启冷却：5 分钟\\n\\n"
    message+="✅ 系统已就绪，异常会自动修复并通知"
    
    send_alert "$message" "force"
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
        
        # 检查是否刚重启过（冷却期内）
        local last_restart=$(cat "$LAST_RESTART_FILE" 2>/dev/null || echo 0)
        local now=$(date +%s)
        local diff=$((now - last_restart))
        
        if [ "$diff" -lt "$RESTART_COOLDOWN" ]; then
            log "⏳ Supervisor 刚重启过（${diff}秒前），等待冷却"
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
            send_alert "✅ Supervisor 已重启\\n\\n所有策略已恢复运行"
        else
            log "⚠️ Supervisor 重启后 $strategy_name 仍未运行，等待下次检查"
        fi
        return
    fi
    
    # 策略异常处理
    if [ "$status" != "RUNNING" ]; then
        log "❌ $strategy_name 异常 (状态：$status)，尝试重启..."
        
        $SUPERVISORCTL -s $SUPERVISOR_SOCKET restart "$strategy_name" 2>/dev/null
        sleep 5
        
        local new_status=$(get_strategy_status "$strategy_name")
        if [ "$new_status" = "RUNNING" ]; then
            log "✅ $strategy_name 重启成功"
            # 不立即发送恢复通知，等待汇总
            return 0
        else
            log "⚠️ $strategy_name 重启失败"
            return 1
        fi
    fi
    
    return 0
}

# 主循环
log "🛡️ 策略守护启动（智能版 v2）"
send_startup_notification

while true; do
    FAILED_STRATEGIES=""
    RECOVERED_STRATEGIES=""
    
    # 动态读取激活的策略列表
    STRATEGIES_FILE="/root/.openclaw/workspace/quant/v3-architecture/.active_strategies"
    if [ -f "$STRATEGIES_FILE" ]; then
        STRATEGY_NAMES=$(grep -v "^#" "$STRATEGIES_FILE" | grep -v "^$" | sed 's/^/quant-strategy-/')
    else
        STRATEGY_NAMES="quant-strategy-rsi_1min_strategy quant-strategy-link_rsi_detailed_strategy quant-strategy-rsi_scale_in_strategy"
    fi
    
    # 检查所有策略
    for strategy in $STRATEGY_NAMES; do
        status=$(get_strategy_status "$strategy")
        
        if [ "$status" != "RUNNING" ]; then
            check_and_fix "$strategy"
            if [ $? -ne 0 ]; then
                FAILED_STRATEGIES+="$strategy ($status)\\n"
            else
                RECOVERED_STRATEGIES+="$strategy\\n"
            fi
        fi
    done
    
    # 汇总告警（避免单条发送）
    if [ -n "$FAILED_STRATEGIES" ] || [ -n "$RECOVERED_STRATEGIES" ]; then
        ALERT_MSG=""
        
        if [ -n "$FAILED_STRATEGIES" ]; then
            ALERT_MSG+="🚨 策略异常\\n\\n$FAILED_STRATEGIES\\n"
            ALERT_MSG+="⚠️ 已尝试自动重启，请检查日志\\n"
        fi
        
        if [ -n "$RECOVERED_STRATEGIES" ]; then
            ALERT_MSG+="\\n✅ 策略已恢复\\n\\n$RECOVERED_STRATEGIES"
        fi
        
        send_alert "$ALERT_MSG"
    fi
    
    # Dashboard 检查（每 5 分钟）
    if ! curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        log "⚠️ Dashboard 无响应，尝试重启..."
        pkill -9 -f uvicorn
        sleep 2
        cd /root/.openclaw/workspace/quant/v3-architecture
        nohup /root/.pyenv/versions/3.10.13/bin/python3 -m uvicorn web.dashboard_api:app \
            --host 0.0.0.0 --port 3000 --timeout-keep-alive 30 > logs/dashboard_out.log 2>&1 &
        log "✅ Dashboard 已重启"
    fi
    
    sleep 60
done
