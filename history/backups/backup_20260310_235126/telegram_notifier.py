#!/usr/bin/env python3
"""
🦞 Telegram 通知模块
负责发送交易通知到 Telegram
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, Optional

TELEGRAM_CONFIG_FILE = '/tmp/telegram_bot_config.json'

class TelegramNotifier:
    """Telegram 通知器"""
    
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self) -> Optional[Dict]:
        """加载 Telegram 配置"""
        if os.path.exists(TELEGRAM_CONFIG_FILE):
            with open(TELEGRAM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_config(self, bot_token: str, chat_id: str):
        """保存 Telegram 配置"""
        config = {
            'bot_token': bot_token,
            'chat_id': chat_id
        }
        with open(TELEGRAM_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        self.config = config
    
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        发送消息到 Telegram
        
        Args:
            message: 消息内容
            parse_mode: Markdown 或 HTML
            
        Returns:
            是否发送成功
        """
        if not self.config:
            print("❌ Telegram 未配置")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.config['bot_token']}/sendMessage"
            data = {
                'chat_id': self.config['chat_id'],
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                print(f"✅ 消息已发送：{message[:50]}...")
                return True
            else:
                print(f"❌ 发送失败：{result}")
                return False
                
        except Exception as e:
            print(f"❌ 发送异常：{e}")
            return False
    
    def send_strategy_started(self, symbol: str, side: str, price: float, 
                             quantity: float, strategy: str, account_type: str = '测试盘',
                             stop_loss: float = None):
        """发送策略启动通知（含止损）"""
        emoji = '🟢' if side == 'long' else '🔴'
        side_cn = '做多' if side == 'long' else '做空'
        
        # 计算止损百分比
        stop_loss_info = ""
        if stop_loss:
            if side == 'long':
                stop_pct = (1 - stop_loss / price) * 100
            else:
                stop_pct = (stop_loss / price - 1) * 100
            stop_loss_info = f"\n🛡️ 止损价：${stop_loss:,.2f} (-{stop_pct:.1f}%)"
        
        message = f"""
{emoji} **策略启动通知** {emoji}

📊 账户类型：{account_type}
💹 交易对：{symbol}
📈 方向：{side_cn}
💰 入场价：${price:,.2f}
📦 数量：{quantity}
📋 策略：{strategy}{stop_loss_info}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 策略已成功启动（含止损单）
"""
        self.send_message(message)
    
    def send_strategy_stopped(self, symbol: str, pnl: float, pnl_pct: float,
                             entry_price: float, exit_price: float, 
                             account_type: str = '测试盘'):
        """发送策略停止通知"""
        pnl_emoji = '✅' if pnl >= 0 else '❌'
        pnl_color = '🟢' if pnl >= 0 else '🔴'
        
        message = f"""
{pnl_emoji} **策略平仓通知** {pnl_emoji}

📊 账户类型：{account_type}
💹 交易对：{symbol}
💰 入场价：${entry_price:,.2f}
💰 平仓价：${exit_price:,.2f}
{pnl_color} 盈亏：${pnl:+.2f} ({pnl_pct:+.2f}%)
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 策略已平仓
"""
        self.send_message(message)
    
    def send_trade_signal(self, symbol: str, signal_type: str, 
                         current_price: float, reason: str,
                         account_type: str = '测试盘'):
        """发送交易信号通知"""
        signal_emoji = '📈' if 'LONG' in signal_type else '📉'
        
        message = f"""
{signal_emoji} **交易信号** {signal_emoji}

📊 账户类型：{account_type}
💹 交易对：{symbol}
📡 信号：{signal_type}
💰 当前价：${current_price:,.2f}
📝 原因：{reason}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ 请确认是否执行
"""
        self.send_message(message)
    
    def send_trade_executed(self, symbol: str, action: str, price: float,
                           quantity: float, amount: float,
                           account_type: str = '测试盘'):
        """发送交易执行通知"""
        action_emoji = '🔓' if action == 'OPEN' else '🔒'
        action_cn = '开仓' if action == 'OPEN' else '平仓'
        
        message = f"""
{action_emoji} **交易执行通知** {action_emoji}

📊 账户类型：{account_type}
💹 交易对：{symbol}
📝 操作：{action_cn}
💰 价格：${price:,.2f}
📦 数量：{quantity}
💵 金额：${amount:,.2f}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 交易已成功执行
"""
        self.send_message(message)
    
    def send_asset_update(self, account_type: str, total_value: float,
                         available: float, positions_value: float,
                         unrealized_pnl: float = 0):
        """发送资产更新通知"""
        pnl_emoji = '🟢' if unrealized_pnl >= 0 else '🔴'
        
        message = f"""
💰 **资产更新** 💰

📊 账户类型：{account_type}
💵 总资产：${total_value:,.2f}
💳 可用资金：${available:,.2f}
📦 持仓价值：${positions_value:,.2f}
{pnl_emoji} 未实现盈亏：${unrealized_pnl:+.2f}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 资产实时更新
"""
        self.send_message(message)
    
    def send_position_update(self, positions: list, account_type: str = '测试盘'):
        """发送持仓更新通知"""
        if not positions:
            message = f"""
📊 **持仓更新** 📊

📊 账户类型：{account_type}
📦 持仓数量：0

💤 当前无持仓
"""
        else:
            positions_text = '\n'.join([
                f"{p['symbol']} {p['side'].upper()} | ${p['entry_price']:,.2f} | ${p['pnl']:+.2f}"
                for p in positions
            ])
            
            total_pnl = sum(p['pnl'] for p in positions)
            pnl_emoji = '🟢' if total_pnl >= 0 else '🔴'
            
            message = f"""
📊 **持仓更新** 📊

📊 账户类型：{account_type}
📦 持仓数量：{len(positions)}

{positions_text}

{pnl_emoji} 总盈亏：${total_pnl:+.2f}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 持仓实时更新
"""
        
        self.send_message(message)
    
    def send_error_notification(self, error_message: str, 
                               account_type: str = '测试盘'):
        """发送错误通知"""
        message = f"""
❌ **错误通知** ❌

📊 账户类型：{account_type}
⚠️ 错误：{error_message}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ 请检查系统状态
"""
        self.send_message(message)


# 全局实例
telegram_notifier = TelegramNotifier()
