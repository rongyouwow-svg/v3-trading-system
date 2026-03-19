#!/bin/bash
# 🦞 V3 系统快速监控 (L1 关键基础设施)
# 监控频率：每 2 分钟

LOG_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/v3_fast_monitor_$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local level="$1"
    local message="$2"
    python3 -c "
import requests
try:
    requests.post(
        'https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/sendMessage',
        json={'chat_id': '1233887750', 'text': '''$level

$message''', 'parse_mode': 'Markdown'},
        timeout=10
    )
except Exception as e:
    print(f'发送失败：{e}')
" 2>/dev/null
}

# L1: 基础设施检查 (每 2 分钟)
check_infrastructure() {
    log "【L1】基础设施快速检查..."
    local has_issue=false
    
    # Dashboard API
    local health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health 2>/dev/null)
    if [[ "$health" != "200" ]]; then
        log "  ❌ Dashboard API: 异常 ($health)"
        send_alert "🔴 **P0 - Dashboard 异常**" "Dashboard API 无响应 (HTTP $health)"
        has_issue=true
    else
        log "  ✅ Dashboard API: 正常"
    fi
    
    # 策略进程
    local count=$(ps aux | grep -E "rsi_.*strategy.py" | grep -v grep | wc -l)
    if [[ $count -lt 3 ]]; then
        log "  ❌ 策略进程：只有 $count 个运行中"
        send_alert "🔴 **P0 - 策略进程异常**" "只有 $count 个策略进程运行"
        has_issue=true
    else
        log "  ✅ 策略进程：$count 个运行中"
    fi
    
    if [[ "$has_issue" == "false" ]]; then
        log "  ✅ L1 检查通过"
    fi
    log ""
}

# 主循环：每 2 分钟
while true; do
    check_infrastructure
    sleep 120  # 2 分钟
done
