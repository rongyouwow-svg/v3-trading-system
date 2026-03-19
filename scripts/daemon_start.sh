#!/bin/bash
# 🦞 龙虾王量化系统 - 进程守护启动脚本
# 创建时间：2026-03-17 07:45

LOGS_DIR="/home/admin/.openclaw/workspace/quant/v3-architecture/logs"
VENV_PYTHON="/home/admin/.openclaw/workspace/quant/.venv/bin/python"
WORKSPACE="/home/admin/.openclaw/workspace/quant/v3-architecture"

# 清理旧进程
echo "🧹 清理旧进程..."
pkill -f "multi_strategy_manager.py" 2>/dev/null
pkill -f "unified_monitor.py" 2>/dev/null
pkill -f "lightweight_api.py" 2>/dev/null
sleep 2

# 启动多策略管理器
echo "🚀 启动多策略管理器..."
cd $WORKSPACE
nohup $VENV_PYTHON -u scripts/multi_strategy_manager.py > $LOGS_DIR/daemon_multi_strategy.log 2>&1 &
echo "✅ 多策略管理器启动，PID: $!"

# 启动统一监控器
echo "🚀 启动统一监控器..."
nohup $VENV_PYTHON -u scripts/unified_monitor.py > $LOGS_DIR/daemon_unified_monitor.log 2>&1 &
echo "✅ 统一监控器启动，PID: $!"

# 启动轻量级 Web API（先清理端口）
echo "🚀 启动轻量级 Web API..."
pkill -9 -f "lightweight_api.py" 2>/dev/null
sleep 2
nohup $VENV_PYTHON -u scripts/lightweight_api.py > $LOGS_DIR/daemon_lightweight_api.log 2>&1 &
echo "✅ 轻量级 Web API 启动，PID: $!"

# 等待启动
sleep 10

# 检查进程状态
echo ""
echo "📊 进程状态检查..."
ps aux | grep -E "multi_strategy|unified_monitor|lightweight_api" | grep -v grep | wc -l
echo "个进程运行中"

echo ""
echo "✅ 量化系统守护进程启动完成！"
