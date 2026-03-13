#!/usr/bin/env python3
"""
🦞 Telegram 通知插件 v3.0

功能:
    - 发送交易通知
    - 发送告警消息
    - 发送日报/周报

用法:
    from plugins.telegram.telegram_plugin import TelegramPlugin
    
    plugin = TelegramPlugin()
    plugin.initialize()
    plugin.execute(message='交易通知')
"""

import os
import requests
from typing import Dict, Optional

from plugins.base import BasePlugin, PluginStatus
from modules.utils.result import Result
from modules.utils.logger import setup_logger

logger = setup_logger("telegram_plugin", log_file="logs/telegram_plugin.log")


class TelegramPlugin(BasePlugin):
    """
    Telegram 通知插件
    
    功能:
        - 发送消息到 Telegram
        - 支持 Markdown 格式
        - 支持内联按钮
    """
    
    # 插件元数据
    name = "TelegramPlugin"
    version = "1.0.0"
    description = "Telegram 通知插件"
    author = "Lobster King"
    
    def __init__(self):
        """初始化 Telegram 插件"""
        super().__init__()
        
        # 配置
        self.bot_token: Optional[str] = None
        self.chat_id: Optional[str] = None
        self.api_url: str = "https://api.telegram.org/bot"
        
    def _initialize(self):
        """初始化插件"""
        # 从环境变量获取配置
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN 未配置")
        
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID 未配置")
        
        logger.info(f"✅ Telegram 插件初始化完成 (chat_id: {self.chat_id})")
    
    def execute(self, **kwargs) -> Result:
        """
        发送 Telegram 消息
        
        Args:
            message (str): 消息内容
            parse_mode (str, optional): 解析模式 (Markdown/HTML)
            disable_notification (bool, optional): 静音发送
        
        Returns:
            Result: 发送结果
        """
        message = kwargs.get('message')
        parse_mode = kwargs.get('parse_mode', 'Markdown')
        disable_notification = kwargs.get('disable_notification', False)
        
        if not message:
            return Result.fail(
                error_code="MESSAGE_REQUIRED",
                message="消息内容不能为空"
            )
        
        try:
            # 构建 API URL
            url = f"{self.api_url}{self.bot_token}/sendMessage"
            
            # 构建请求参数
            params = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_notification': disable_notification
            }
            
            # 发送请求
            response = requests.post(url, json=params, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                logger.info(f"✅ Telegram 消息发送成功")
                return Result.ok(
                    data={'message_id': result['result']['message_id']},
                    message="消息发送成功"
                )
            else:
                error = result.get('description', '未知错误')
                logger.error(f"❌ Telegram 消息发送失败：{error}")
                return Result.fail(
                    error_code="TELEGRAM_SEND_FAILED",
                    message=f"Telegram 消息发送失败：{error}"
                )
                
        except Exception as e:
            logger.error(f"❌ Telegram 消息发送异常：{e}")
            return Result.fail(
                error_code="TELEGRAM_SEND_ERROR",
                message=f"Telegram 消息发送异常：{str(e)}"
            )
    
    def send_trade_notification(self, symbol: str, side: str, quantity: float, price: float):
        """
        发送交易通知
        
        Args:
            symbol (str): 交易对
            side (str): 方向
            quantity (float): 数量
            price (float): 价格
        
        Returns:
            Result: 发送结果
        """
        message = f"""
🦞 **交易通知**

📊 交易对：`{symbol}`
📈 方向：`{side}`
💰 数量：`{quantity}`
💵 价格：`{price}`

⏰ 时间：`{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
"""
        return self.execute(message=message)
    
    def send_alert(self, title: str, message: str, level: str = 'WARNING'):
        """
        发送告警消息
        
        Args:
            title (str): 标题
            message (str): 消息内容
            level (str): 告警级别 (INFO/WARNING/ERROR/CRITICAL)
        
        Returns:
            Result: 发送结果
        """
        emoji = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }.get(level, '📢')
        
        text = f"""
{emoji} **{title}**

{message}

⏰ 时间：`{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
"""
        return self.execute(message=text)
    
    def send_daily_report(self, pnl: float, trade_count: int, win_rate: float):
        """
        发送日报
        
        Args:
            pnl (float): 盈亏
            trade_count (int): 交易次数
            win_rate (float): 胜率
        
        Returns:
            Result: 发送结果
        """
        pnl_emoji = "🟢" if pnl >= 0 else "🔴"
        
        message = f"""
🦞 **大王量化 - 每日报告**

{pnl_emoji} **今日盈亏**: `{pnl:.2f} USDT`
📊 **交易次数**: `{trade_count}`
📈 **胜率**: `{win_rate:.1f}%`

⏰ 时间：`{__import__('datetime').datetime.now().strftime('%Y-%m-%d')}`
"""
        return self.execute(message=message)
