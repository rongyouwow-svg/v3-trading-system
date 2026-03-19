#!/bin/bash
# 📊 V3 系统状态检查脚本

WORKDIR="/root/.openclaw/workspace/quant/v3-architecture"
SUPERVISORCTL="/root/.pyenv/versions/3.10.13/bin/supervisorctl"
SOCKET="unix://$WORKDIR/logs/supervisor.sock"

echo "======================================"
echo "📊 V3 系统状态检查"
echo "时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================"
echo ""

# Supervisor 状态
echo "【1】Supervisor 状态"
if pgrep -f supervisord > /dev/null; then
    echo "✅ Supervisor 运行中"
    $SUPERVISORCTL -s $SOCKET status 2>/dev/null | grep strategy
else
    echo "❌ Supervisor 未运行"
fi
echo ""

# Dashboard 状态
echo "【2】Dashboard 状态"
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Dashboard 正常"
    curl -s http://localhost:3000/api/health 2>/dev/null
else
    echo "❌ Dashboard 异常"
fi
echo ""

# 监控进程
echo "【3】监控进程"
if pgrep -f "monitor.sh" > /dev/null; then
    echo "✅ 监控运行中"
else
    echo "❌ 监控未运行"
fi
echo ""

# 策略进程
echo "【4】策略进程"
ps aux | grep -E "strategy.*\.py" | grep -v grep | awk '{print "✅", $11, $12}'
echo ""

# 日志最后更新
echo "【5】日志最后更新"
ls -lh $WORKDIR/logs/*.log 2>/dev/null | tail -5
echo ""

echo "======================================"
echo "🌐 Dashboard: http://47.83.115.23:3000/dashboard/"
echo "======================================"
