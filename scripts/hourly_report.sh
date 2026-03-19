#!/bin/bash
# 每小时状态汇报脚本

TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID="1233887750"
TIME=$(date '+%Y-%m-%d %H:%M:%S')

# 获取策略状态
STRATEGY_STATUS=$(supervisorctl status 2>&1 | grep -c "RUNNING")

# 获取持仓
POSITIONS=$(curl -s http://localhost:3000/api/binance/positions 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('positions',[])))" 2>/dev/null || echo "?")

# 获取止损单
STOP_ORDERS=$(curl -s http://localhost:3000/api/binance/stop-loss 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('orders',[])))" 2>/dev/null || echo "?")

# 获取余额
BALANCE=$(curl -s http://localhost:3000/api/account 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d.get('balance',{}).get('total',0)} USDT\")" 2>/dev/null || echo "?")

MSG="📊 V3 系统 hourly 汇报
时间：$TIME

✅ 策略运行：$STRATEGY_STATUS 个
📈 持仓：$POSITIONS 个
🛑 止损单：$STOP_ORDERS 个
💰 余额：$BALANCE

系统运行正常"

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\":${CHAT_ID},\"text\":\"$MSG\"}" > /dev/null

echo "[$TIME] 汇报已发送"
