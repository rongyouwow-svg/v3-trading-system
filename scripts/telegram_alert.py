#!/usr/bin/env python3
"""
📱 Telegram 告警通知

配置:
    Bot Token: YOUR_TELEGRAM_BOT_TOKEN
    Chat ID: 1233887750
    Bot: tongzhi (@rytongzhi_bot)

用法:
    python3 telegram_alert.py "告警消息"
"""

import requests
import sys
import json
from datetime import datetime

# Telegram 配置
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "1233887750"
BOT_NAME = "tongzhi (@rytongzhi_bot)"

def send_telegram_alert(message: str, level: str = "INFO"):
    """发送 Telegram 告警"""
    
    # 添加时间戳和级别
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_message = f"[{timestamp}] [{level}]\n{message}"
    
    # Telegram API
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    data = {
        'chat_id': CHAT_ID,
        'text': formatted_message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ Telegram 告警发送成功")
            return True
        else:
            print(f"❌ Telegram 告警发送失败：{result}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram 告警异常：{e}")
        return False

def send_alert_file(alert_file: str):
    """从告警文件发送"""
    try:
        with open(alert_file, 'r', encoding='utf-8') as f:
            # 读取最后 10 行
            lines = f.readlines()[-10:]
            message = ''.join(lines)
        
        return send_telegram_alert(message, 'ALERT')
    except Exception as e:
        print(f"❌ 读取告警文件失败：{e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = ' '.join(sys.argv[1:])
        send_telegram_alert(message, 'TEST')
    else:
        print("用法：python3 telegram_alert.py \"告警消息\"")
        print("或：python3 telegram_alert.py --file logs/monitor_alerts.log")
