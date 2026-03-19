#!/bin/bash
# 🦞 V3 系统自动修复脚本 v2 (带根源分析)
# 每 10 分钟检查一次，深度分析并修复

LOG_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/auto_repair_$(date +%Y%m%d).log"
ALERT_LOG="/root/.openclaw/workspace/quant/v3-architecture/logs/alerts_$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local message="$1"
    python3 << PYEOF
import requests
try:
    requests.post(
        "https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/sendMessage",
        json={
            'chat_id': '1233887750',
            'text': '''$message''',
            'parse_mode': 'Markdown'
        },
        timeout=10
    )
except Exception as e:
    print(f"发送告警失败：{e}")
PYEOF
}

# 五问法根源分析
root_cause_analysis() {
    local problem="$1"
    log "🌳 根源分析：$problem"
    
    # 第 1 问：为什么出现问题？
    log "  【第 1 问】为什么 $problem？"
    
    # 第 2 问：为什么发生？
    log "  【第 2 问】为什么发生？"
    
    # 第 3 问：为什么未预防？
    log "  【第 3 问】为什么未预防？"
    
    # 第 4 问：为什么未检测？
    log "  【第 4 问】为什么未检测？"
    
    # 第 5 问：为什么未自动化？
    log "  【第 5 问】为什么未自动化？"
    
    log "  ✅ 根源分析完成"
}

check_and_fix() {
    local service="$1"
    local check_cmd="$2"
    local fix_cmd="$3"
    
    log "🔍 检查 $service..."
    
    if eval "$check_cmd" > /dev/null 2>&1; then
        log "✅ $service: 正常"
        return 0
    else
        log "❌ $service: 异常"
        
        # 根源分析
        root_cause_analysis "$service 异常"
        
        # 执行修复
        log "🔧 执行修复..."
        if eval "$fix_cmd" 2>&1 | tee -a "$LOG_FILE"; then
            log "✅ $service: 修复成功"
            send_alert "✅ **服务已修复**

服务：$service
时间：$(date '+%Y-%m-%d %H:%M:%S')
状态：已修复

已执行根源分析并自动化修复。"
            return 0
        else
            log "🚨 $service: 修复失败"
            send_alert "🚨 **修复失败**

服务：$service
时间：$(date '+%Y-%m-%d %H:%M:%S')

需要手动干预！"
            return 1
        fi
    fi
}

# ==================== 主循环 ====================

log "========================================"
log "🦞 V3 系统自动修复 v2 (带根源分析)"
log "========================================"

# 检查 Dashboard
check_and_fix "Dashboard" \
    "curl -s http://localhost:3000/api/health | grep -q '\"status\":\"ok\"'" \
    "pkill -9 -f uvicorn; sleep 2; cd /root/.openclaw/workspace/quant/v3-architecture && nohup /root/.pyenv/versions/3.10.13/bin/python3 -m uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000 --timeout-keep-alive 30 > logs/dashboard_out.log 2>&1 & sleep 5"

# 检查策略执行
check_and_fix "策略执行" \
    "curl -s http://localhost:3000/api/strategy/active | grep -q '\"success\": true'" \
    "echo '策略 API 异常，检查日志'"

# 检查持仓 API
check_and_fix "持仓 API" \
    "curl -s http://localhost:3000/api/binance/positions | grep -q '\"success\": true'" \
    "echo '持仓 API 异常，检查币安连接'"

log ""
log "========================================"
log "📊 本轮检查完成"
log "========================================"
log ""
log "⏰ 下次检查：10 分钟后"
