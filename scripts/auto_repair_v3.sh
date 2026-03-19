#!/bin/bash
# 🦞 V3 系统自动修复脚本 v3 (优化检测逻辑)

LOG_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/auto_repair_$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local message="$1"
    python3 -c "
import requests
try:
    requests.post(
        'https://api.telegram.org/botYOUR_TELEGRAM_BOT_TOKEN/sendMessage',
        json={'chat_id': '1233887750', 'text': '''$message''', 'parse_mode': 'Markdown'},
        timeout=10
    )
except Exception as e:
    print(f'发送失败：{e}')
" 2>/dev/null
}

# 智能检测 - 使用 Python
check_api() {
    local name="$1"
    local url="$2"
    
    log "🔍 检查 $name..."
    
    result=$(python3 -c "
import requests
try:
    r = requests.get('$url', timeout=5)
    d = r.json()
    if d.get('success') or d.get('status') == 'ok':
        print('OK')
    else:
        print('FAIL: ' + str(d))
except Exception as e:
    print('ERROR: ' + str(e))
" 2>/dev/null)
    
    if [[ "$result" == "OK" ]]; then
        log "✅ $name: 正常"
        return 0
    else
        log "❌ $name: 异常 - $result"
        return 1
    fi
}

# ==================== 主循环 ====================

log "========================================"
log "🦞 V3 系统自动修复 v3 (智能检测)"
log "========================================"
log ""

# 检查 Dashboard
check_api "Dashboard" "http://localhost:3000/api/health"

# 检查策略执行
check_api "策略执行" "http://localhost:3000/api/strategy/active"

# 检查持仓
check_api "持仓" "http://localhost:3000/api/binance/positions"

log ""
log "========================================"
log "📊 本轮检查完成"
log "========================================"
log ""
log "⏰ 下次检查：10 分钟后"
