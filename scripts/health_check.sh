#!/bin/bash
# 🏥 V3 系统健康检查脚本
# 用途：全面检查系统状态，生成健康报告

TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID="1233887750"
REPORT_FILE="/root/.openclaw/workspace/quant/v3-architecture/logs/health_check_$(date +%Y%m%d_%H%M%S).md"

send_report() {
    local message="$1"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\":${CHAT_ID},\"text\":\"${message}\",\"parse_mode\":\"Markdown\"}" > /dev/null
}

check_supervisor() {
    local status=$(/root/.pyenv/versions/3.10.13/bin/supervisorctl status 2>&1)
    if echo "$status" | grep -q "refused"; then
        echo "❌ Supervisor 未运行"
        return 1
    fi
    
    local running=$(echo "$status" | grep -c "RUNNING")
    local total=5  # 3 策略 + 2 服务
    
    if [ "$running" -ge 3 ]; then
        echo "✅ Supervisor 正常 ($running/$total 进程运行)"
        return 0
    else
        echo "⚠️ Supervisor 异常 ($running/$total 进程运行)"
        return 1
    fi
}

check_dashboard() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health 2>/dev/null)
    if [ "$response" = "200" ]; then
        echo "✅ Dashboard 正常 (HTTP $response)"
        return 0
    else
        echo "❌ Dashboard 异常 (HTTP $response)"
        return 1
    fi
}

check_strategies() {
    local status=$(/root/.pyenv/versions/3.10.13/bin/supervisorctl status 2>/dev/null)
    local all_ok=true
    
    for strategy in "quant-strategy-eth" "quant-strategy-link" "quant-strategy-avax"; do
        if echo "$status" | grep -q "$strategy.*RUNNING"; then
            echo "✅ $strategy: RUNNING"
        else
            echo "❌ $strategy: 异常"
            all_ok=false
        fi
    done
    
    if $all_ok; then
        return 0
    else
        return 1
    fi
}

check_guardian() {
    if pgrep -f "strategy_guardian.sh" > /dev/null; then
        echo "✅ Guardian 守护进程运行中"
        return 0
    else
        echo "❌ Guardian 守护进程未运行"
        return 1
    fi
}

check_api() {
    local response=$(curl -s -X POST "https://coding.dashscope.aliyuncs.com/v1/chat/completions" \
        -H "Authorization: Bearer sk-sp-4075c1a27bf14ebb94e8ed3974b5f034" \
        -H "Content-Type: application/json" \
        -d '{"model":"qwen3.5-plus","messages":[{"role":"user","content":"ok"}],"max_tokens":5}' 2>/dev/null)
    
    if echo "$response" | grep -q "choices"; then
        echo "✅ Dashscope API 正常"
        return 0
    else
        echo "⚠️ Dashscope API 响应异常"
        return 1
    fi
}

# 生成报告
echo "# 🏥 V3 系统健康检查报告" > "$REPORT_FILE"
echo "**时间**: $(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "## 检查结果" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"

check_supervisor >> "$REPORT_FILE" 2>&1
check_dashboard >> "$REPORT_FILE" 2>&1
check_strategies >> "$REPORT_FILE" 2>&1
check_guardian >> "$REPORT_FILE" 2>&1
check_api >> "$REPORT_FILE" 2>&1

echo '```' >> "$REPORT_FILE"

# 发送报告
summary=$(cat "$REPORT_FILE" | head -20)
send_report "$summary"

echo "✅ 健康检查完成，报告：$REPORT_FILE"
