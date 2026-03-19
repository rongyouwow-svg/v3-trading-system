#!/bin/bash
# 🦞 大王量化系统 - 2 小时自动检查修复脚本
# 功能：检查错误 → 自动修复 → 记录报告

# 不因为错误退出，继续执行修复
# set -e

# 配置
WORKSPACE="/home/admin/.openclaw/workspace/quant/v3-architecture"
LOGS_DIR="$WORKSPACE/logs"
ERROR_TRACKING="$WORKSPACE/error_tracking.md"
REPORT_FILE="$WORKSPACE/logs/error_check_$(date +%Y%m%d_%H%M).log"
SUPERVISOR_CONF="/etc/supervisor/supervisord.conf"
PYENV_PYTHON="/home/admin/.pyenv/versions/3.10.0/bin/python3"
SUPERVISORCTL="/home/admin/.pyenv/versions/3.10.0/bin/supervisorctl"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$REPORT_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$REPORT_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$REPORT_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ $1${NC}" | tee -a "$REPORT_FILE"
}

# 开始检查
log "🚀 开始 2 小时自动检查修复任务"
log "================================"

# 1. 检查 Supervisor 进程状态
log "📊 检查 Supervisor 进程状态..."
SUPERVISOR_STATUS=$($SUPERVISORCTL -c "$SUPERVISOR_CONF" status 2>&1 || echo "获取状态失败")
echo "$SUPERVISOR_STATUS" | tee -a "$REPORT_FILE"

# 2. 检查并修复 FATAL 进程
log "🔍 检查 FATAL 进程..."
FATAL_PROCS=$(echo "$SUPERVISOR_STATUS" | grep "FATAL" || true)
if [ -n "$FATAL_PROCS" ]; then
    log_warning "发现 FATAL 进程:"
    echo "$FATAL_PROCS" | tee -a "$REPORT_FILE"
    
    # 提取进程名并重启
    for proc in $(echo "$FATAL_PROCS" | awk '{print $1}'); do
        if [ "$proc" != "web_dashboard:web_dashboard_00" ]; then  # 跳过非关键服务
            log "🔄 重启进程：$proc"
            $SUPERVISORCTL -c "$SUPERVISOR_CONF" restart "$proc" 2>&1 | tee -a "$REPORT_FILE"
            sleep 2
            
            # 验证重启成功
            NEW_STATUS=$($SUPERVISORCTL -c "$SUPERVISOR_CONF" status "$proc" 2>&1)
            if echo "$NEW_STATUS" | grep -q "RUNNING"; then
                log_success "✅ 进程 $proc 重启成功"
            else
                log_error "❌ 进程 $proc 重启失败"
            fi
        fi
    done
else
    log_success "✅ 无 FATAL 进程"
fi

# 3. 检查并修复 BACKOFF 进程
log "🔍 检查 BACKOFF 进程..."
BACKOFF_PROCS=$(echo "$SUPERVISOR_STATUS" | grep "BACKOFF" || true)
if [ -n "$BACKOFF_PROCS" ]; then
    log_warning "发现 BACKOFF 进程:"
    echo "$BACKOFF_PROCS" | tee -a "$REPORT_FILE"
    
    for proc in $(echo "$BACKOFF_PROCS" | awk '{print $1}'); do
        log "🔄 重启进程：$proc"
        $SUPERVISORCTL -c "$SUPERVISOR_CONF" restart "$proc" 2>&1 | tee -a "$REPORT_FILE"
        sleep 3
    done
else
    log_success "✅ 无 BACKOFF 进程"
fi

# 4. 扫描错误日志
log "🔍 扫描错误日志..."
ERROR_COUNT=0

for logfile in "$LOGS_DIR"/*.log; do
    if [ -f "$logfile" ]; then
        filename=$(basename "$logfile")
        errors=$(grep -i "error\|fail\|exception\|critical" "$logfile" 2>/dev/null | tail -20 || true)
        
        if [ -n "$errors" ]; then
            log_warning "发现错误 ($filename):"
            echo "$errors" | head -10 | tee -a "$REPORT_FILE"
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi
    fi
done

if [ $ERROR_COUNT -eq 0 ]; then
    log_success "✅ 日志清洁，无严重错误"
else
    log_warning "⚠️ 共 $ERROR_COUNT 个日志文件包含错误"
fi

# 5. 检查语法错误并修复
log "🔍 检查 Python 语法错误..."
SYNTAX_ERRORS=$(grep -r "SyntaxError" "$LOGS_DIR"/*.log 2>/dev/null | tail -5 || true)
if [ -n "$SYNTAX_ERRORS" ]; then
    log_warning "发现语法错误:"
    echo "$SYNTAX_ERRORS" | tee -a "$REPORT_FILE"
    
    # 提取错误文件
    ERROR_FILE=$(echo "$SYNTAX_ERRORS" | grep -oP 'File "\K[^"]+' | head -1)
    if [ -n "$ERROR_FILE" ] && [ -f "$ERROR_FILE" ]; then
        log "🔍 错误文件：$ERROR_FILE"
        
        # 检查语法
        if ! $PYENV_PYTHON -m py_compile "$ERROR_FILE" 2>/dev/null; then
            log_error "❌ 语法检查失败，需要手动修复"
            echo "   文件：$ERROR_FILE" | tee -a "$REPORT_FILE"
        else
            log_success "✅ 语法检查通过"
        fi
    fi
else
    log_success "✅ 无语法错误"
fi

# 6. 检查 Web API 健康
log "🔍 检查 Web API 健康状态..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    log_success "✅ Web API 健康检查通过 (HTTP $HEALTH_RESPONSE)"
else
    log_error "❌ Web API 健康检查失败 (HTTP $HEALTH_RESPONSE)"
    log "🔄 尝试重启 Web 服务..."
    $SUPERVISORCTL -c "$SUPERVISOR_CONF" restart quant-web 2>&1 | tee -a "$REPORT_FILE"
    sleep 5
    
    # 再次检查
    HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null || echo "000")
    if [ "$HEALTH_RESPONSE" = "200" ]; then
        log_success "✅ Web API 重启成功"
    else
        log_error "❌ Web API 重启失败"
    fi
fi

# 7. 检查策略状态文件
log "🔍 检查策略状态文件..."
STATE_FILE="$LOGS_DIR/strategy_pids.json"
if [ -f "$STATE_FILE" ]; then
    # 检查是否有 entry_price=0 的异常状态
    ZERO_PRICE=$(grep -o '"entry_price": 0.0' "$STATE_FILE" 2>/dev/null || true)
    if [ -n "$ZERO_PRICE" ]; then
        log_warning "⚠️ 发现 entry_price=0.0 的异常状态"
        log "🔄 清理状态文件..."
        rm -f "$STATE_FILE"
        log_success "✅ 已清理异常状态文件"
    else
        log_success "✅ 策略状态正常"
    fi
else
    log_success "✅ 无策略状态文件 (空仓状态)"
fi

# 8. 检查监控进程（新增）
log "🔍 检查监控进程状态..."
MONITOR_PROCS="v23_realtime_monitor.py enhanced_monitor.py deep_monitor.py"
MONITOR_DOWN=""

for proc in $MONITOR_PROCS; do
    if ! pgrep -f "$proc" > /dev/null 2>&1; then
        log_error "❌ 监控进程 $proc 未运行"
        MONITOR_DOWN="$MONITOR_DOWN $proc"
    else
        log_success "✅ 监控进程 $proc 运行正常"
    fi
done

if [ -n "$MONITOR_DOWN" ]; then
    log "🔄 重启监控进程..."
    cd "$WORKSPACE"
    source .venv/bin/activate
    
    for proc in $MONITOR_DOWN; do
        case $proc in
            v23_realtime_monitor.py)
                python -u scripts/v23_realtime_monitor.py > logs/v23_monitor.log 2>&1 &
                ;;
            enhanced_monitor.py)
                python -u scripts/enhanced_monitor.py > logs/enhanced_monitor.log 2>&1 &
                ;;
            deep_monitor.py)
                python -u scripts/deep_monitor.py > logs/deep_monitor.log 2>&1 &
                ;;
        esac
        log "✅ 已重启 $proc"
    done
    
    sleep 10
    
    # 验证重启成功
    for proc in $MONITOR_DOWN; do
        if pgrep -f "$proc" > /dev/null 2>&1; then
            log_success "✅ 监控进程 $proc 重启成功"
        else
            log_error "❌ 监控进程 $proc 重启失败"
        fi
    done
else
    log_success "✅ 所有监控进程运行正常"
fi

# 9. 更新 error_tracking.md
log "📝 更新错误追踪记录..."
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
cat >> "$ERROR_TRACKING" << EOF

---

## 📊 $TIMESTAMP 自动检查报告

**检查时间**: $TIMESTAMP
**检查类型**: 2 小时自动检查

### 系统状态
- **FATAL 进程**: $(echo "$SUPERVISOR_STATUS" | grep -c "FATAL" || echo "0") 个
- **BACKOFF 进程**: $(echo "$SUPERVISOR_STATUS" | grep -c "BACKOFF" || echo "0") 个
- **日志错误**: $ERROR_COUNT 个文件
- **Web API**: HTTP $HEALTH_RESPONSE
- **总体状态**: $([ "$HEALTH_RESPONSE" = "200" ] && echo "🟢 正常" || echo "🔴 异常")

### 自动修复动作
$(if [ -n "$FATAL_PROCS" ]; then echo "- ✅ 重启 FATAL 进程"; else echo "- ✅ 无 FATAL 进程"; fi)
$(if [ -n "$BACKOFF_PROCS" ]; then echo "- ✅ 重启 BACKOFF 进程"; else echo "- ✅ 无 BACKOFF 进程"; fi)
$(if [ -n "$SYNTAX_ERRORS" ]; then echo "- ⚠️ 发现语法错误 (需手动修复)"; else echo "- ✅ 无语法错误"; fi)
$(if [ -n "$ZERO_PRICE" ]; then echo "- ✅ 清理异常状态文件"; else echo "- ✅ 策略状态正常"; fi)
$(if [ -n "$MONITOR_DOWN" ]; then echo "- ✅ 重启监控进程"; else echo "- ✅ 监控进程正常"; fi)

---
EOF

log_success "✅ 已更新 error_tracking.md"

# 9. 总结报告
log "================================"
log "📊 检查总结:"
log "   - FATAL 进程：$(echo "$SUPERVISOR_STATUS" | grep -c "FATAL" || echo "0") 个"
log "   - BACKOFF 进程：$(echo "$SUPERVISOR_STATUS" | grep -c "BACKOFF" || echo "0") 个"
log "   - 日志错误：$ERROR_COUNT 个文件"
log "   - Web API: HTTP $HEALTH_RESPONSE"
log "   - 修复动作：$(if [ -n "$FATAL_PROCS" ] || [ -n "$BACKOFF_PROCS" ]; then echo "已重启"; else echo "无"; fi)"
log "================================"
log "✅ 2 小时自动检查修复任务完成"

# 10. 严重问题告警 (可选)
if [ "$HEALTH_RESPONSE" != "200" ]; then
    log_error "🚨 严重问题：Web API 无法访问，已尝试自动修复"
    # 这里可以添加 Telegram 告警逻辑
fi

exit 0
