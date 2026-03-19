#!/bin/bash
# 问题修复复查脚本

REPAIR_TIME="17:28"  # 修复时间
CHECK_NUM=$1

if [ -z "$CHECK_NUM" ]; then
    echo "用法：$0 <复查次数 1-4>"
    exit 1
fi

TIME=$(date '+%Y-%m-%d %H:%M:%S')

# 检查止损单
STOP_ORDERS=$(curl -s http://localhost:3000/api/binance/stop-loss 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(len([o for o in d.get('orders',[]) if o.get('status')=='NEW']))" 2>/dev/null || echo "?")

# 检查策略
STRATEGY_COUNT=$(ps aux | grep -E "strategy.*py" | grep -v grep | wc -l)

# 检查持仓
POSITIONS=$(curl -s http://localhost:3000/api/binance/positions 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('positions',[])))" 2>/dev/null || echo "?")

# 记录
echo "=== 第${CHECK_NUM}次复查 ===" >> /root/.openclaw/workspace/quant/v3-architecture/logs/verification.log
echo "时间：$TIME" >> /root/.openclaw/workspace/quant/v3-architecture/logs/verification.log
echo "止损单：$STOP_ORDERS 个" >> /root/.openclaw/workspace/quant/v3-architecture/logs/verification.log
echo "策略数：$STRATEGY_COUNT 个" >> /root/.openclaw/workspace/quant/v3-architecture/logs/verification.log
echo "持仓数：$POSITIONS 个" >> /root/.openclaw/workspace/quant/v3-architecture/logs/verification.log
echo "" >> /root/.openclaw/workspace/quant/v3-architecture/logs/verification.log

echo "✅ 第${CHECK_NUM}次复查完成：止损单${STOP_ORDERS}个，策略${STRATEGY_COUNT}个，持仓${POSITIONS}个"
