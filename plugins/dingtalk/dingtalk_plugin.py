#!/usr/bin/env python3
"""
🦞 钉钉通知插件 v3.0

功能:
    - 发送交易通知
    - 发送告警消息
    - 发送日报/周报
    - 支持@特定用户

用法:
    from plugins.dingtalk.dingtalk_plugin import DingTalkPlugin
    
    plugin = DingTalkPlugin()
    plugin.initialize()
    plugin.execute(message='交易通知')
"""

import os
import time
import hmac
import hashlib
import base64
import urllib.parse
from typing import Dict, Optional, List

import requests

from plugins.base import BasePlugin
from modules.utils.result import Result
from modules.utils.logger import setup_logger

logger = setup_logger("dingtalk_plugin", log_file="logs/dingtalk_plugin.log")


class DingTalkPlugin(BasePlugin):
    """
    钉钉通知插件
    
    功能:
        - 发送消息到钉钉群
        - 支持 Markdown 格式
        - 支持@特定用户
        - 支持加签安全验证
    """
    
    # 插件元数据
    name = "DingTalkPlugin"
    version = "1.0.0"
    description = "钉钉通知插件"
    author = "Lobster King"
    
    def __init__(self):
        """初始化钉钉插件"""
        super().__init__()
        
        # 配置
        self.webhook: Optional[str] = None
        self.secret: Optional[str] = None
        self.mobiles: List[str] = []
        
    def _initialize(self):
        """初始化插件"""
        # 从环境变量获取配置
        self.webhook = os.getenv('DINGTALK_WEBHOOK')
        self.secret = os.getenv('DINGTALK_SECRET')
        self.mobiles = os.getenv('DINGTALK_MOBILE', '').split(',')
        
        if not self.webhook:
            raise ValueError("DINGTALK_WEBHOOK 未配置")
        
        logger.info(f"✅ 钉钉插件初始化完成 (webhook: {self.webhook[:50]}...)")
    
    def _generate_sign(self) -> str:
        """
        生成加签签名
        
        Returns:
            str: 签名后的 URL
        """
        if not self.secret:
            return self.webhook
        
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        
        hmac_code = hmac.new(
            secret_enc,
            string_to_sign_enc,
            digestmod=hashlib.sha256
        ).digest()
        
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        return f'{self.webhook}&timestamp={timestamp}&sign={sign}'
    
    def execute(self, **kwargs) -> Result:
        """
        发送钉钉消息
        
        Args:
            message (str): 消息内容
            title (str, optional): 标题
            at_mobiles (List[str], optional): @的手机号列表
            is_at_all (bool, optional): 是否@所有人
        
        Returns:
            Result: 发送结果
        """
        message = kwargs.get('message')
        title = kwargs.get('title', '大王量化通知')
        at_mobiles = kwargs.get('at_mobiles', self.mobiles)
        is_at_all = kwargs.get('is_at_all', False)
        
        if not message:
            return Result.fail(
                error_code="MESSAGE_REQUIRED",
                message="消息内容不能为空"
            )
        
        try:
            # 生成带签名的 URL
            webhook_url = self._generate_sign()
            
            # 构建消息体
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": message
                },
                "at": {
                    "atMobiles": at_mobiles,
                    "isAtAll": is_at_all
                }
            }
            
            # 发送请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(webhook_url, json=data, headers=headers, timeout=10)
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"✅ 钉钉消息发送成功")
                return Result.ok(message="消息发送成功")
            else:
                error = result.get('errmsg', '未知错误')
                logger.error(f"❌ 钉钉消息发送失败：{error}")
                return Result.fail(
                    error_code="DINGTALK_SEND_FAILED",
                    message=f"钉钉消息发送失败：{error}"
                )
                
        except Exception as e:
            logger.error(f"❌ 钉钉消息发送异常：{e}")
            return Result.fail(
                error_code="DINGTALK_SEND_ERROR",
                message=f"钉钉消息发送异常：{str(e)}"
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
        side_emoji = "🟢" if side == "BUY" else "🔴"
        
        message = f"""
## 🦞 大王量化 - 交易通知

{side_emoji} **交易对**: `{symbol}`
📈 **方向**: `{side}`
💰 **数量**: `{quantity}`
💵 **价格**: `{price}`

⏰ 时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.execute(message=message, title="交易通知")
    
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
## {emoji} {title}

{message}

⏰ 时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        # 错误和严重告警@所有人
        is_at_all = level in ['ERROR', 'CRITICAL']
        
        return self.execute(message=text, title=title, is_at_all=is_at_all)
    
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
## 🦞 大王量化 - 每日报告

{pnl_emoji} **今日盈亏**: `{pnl:.2f} USDT`
📊 **交易次数**: `{trade_count}`
📈 **胜率**: `{win_rate:.1f}%`

⏰ 时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
"""
        return self.execute(message=message, title="每日报告")
