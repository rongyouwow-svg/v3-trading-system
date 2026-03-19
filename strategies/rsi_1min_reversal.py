#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦞 RSI 1 分钟反转策略 v2.0
- RSI > 52: 开空（迟滞区间）
- RSI < 48: 平空（迟滞区间）
- 止盈/止损：0.5%
- 最小持仓时间：3 分钟
- 使用已完成 K 线（避免实时波动）
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime
from strategies.base_strategy import BaseStrategy


def calculate_rsi(prices, period=14):
    """计算 RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


class Rsi1minReversal(BaseStrategy):
    """RSI 1 分钟反转策略类"""
    
    def __init__(self, gateway, symbol: str, leverage: int, amount: float):
        super().__init__(gateway, symbol, leverage, amount)
        
        # 策略参数
        self.rsi_period = 14
        self.rsi_threshold = 50
        
        # ✅ 迟滞区间（避免震荡）
        self.rsi_hysteresis = 2  # RSI > 52 开空，RSI < 48 平仓
        self.rsi_open_threshold = self.rsi_threshold + self.rsi_hysteresis   # 52
        self.rsi_close_threshold = self.rsi_threshold - self.rsi_hysteresis  # 48
        
        # ✅ 最小持仓时间（避免频繁交易）
        self.min_hold_time = 180  # 3 分钟（秒）
        
        self.take_profit_pct = 0.005  # 0.5%
        self.stop_loss_pct = 0.005    # 0.5%
        
        # 策略状态
        self.position_open = False
        self.entry_price = 0
        self.entry_time = None  # ✅ 开仓时间
        self.klines_cache = []
        
        # 定时器（每分钟执行）
        self.check_interval = 60  # 60 秒
    
    def fetch_klines(self, limit=50):
        """获取最新 K 线数据"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': self.symbol,
                'interval': '1m',
                'limit': limit
            }
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                'taker_buy_quote', 'ignore'
            ])
            
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            
            return df
        except Exception as e:
            self.log(f"❌ 获取 K 线失败：{e}")
            return None
    
    def check_stop_loss_take_profit(self, current_price):
        """检查止盈止损"""
        if not self.position_open or self.entry_price == 0:
            return
        
        # 空单止盈（价格下跌）
        if current_price <= self.entry_price * (1 - self.take_profit_pct):
            self.log(f"✅ 止盈触发！入场：${self.entry_price:.2f}, 当前：${current_price:.2f}")
            self.emit_signal({
                'type': 'CLOSE',
                'side': 'BUY',
                'percentage': 1.0
            })
            self.position_open = False
            self.entry_price = 0
            self.entry_time = None
            return True
        
        # 空单止损（价格上涨）
        if current_price >= self.entry_price * (1 + self.stop_loss_pct):
            self.log(f"🛑 止损触发！入场：${self.entry_price:.2f}, 当前：${current_price:.2f}")
            self.emit_signal({
                'type': 'CLOSE',
                'side': 'BUY',
                'percentage': 1.0
            })
            self.position_open = False
            self.entry_price = 0
            self.entry_time = None
            return True
        
        return False
    
    def sync_position_from_gateway(self):
        """从网关同步实际持仓状态（防止状态不同步）"""
        try:
            if hasattr(self.gateway, 'get_position'):
                position_info = self.gateway.get_position(self.symbol)
                if position_info:
                    # 如果有空单仓位
                    if position_info.get('side') == 'SHORT' and position_info.get('size', 0) > 0:
                        if not self.position_open:
                            self.log(f"📡 同步持仓状态：检测到空单，更新本地状态")
                        self.position_open = True
                        self.entry_price = position_info.get('entry_price', self.entry_price)
                        # 不更新 entry_time，避免重置最小持仓时间
                    else:
                        if self.position_open:
                            self.log(f"📡 同步持仓状态：无仓位，更新本地状态")
                        self.position_open = False
                        self.entry_price = 0
                        self.entry_time = None
                    return True
        except Exception as e:
            self.log(f"⚠️ 同步持仓失败：{e}")
        return False
    
    def on_tick(self):
        """每分钟执行一次（核心逻辑）"""
        try:
            # 第一步：同步实际持仓状态（防止策略重启后状态不一致）
            self.sync_position_from_gateway()
            
            # 获取 K 线
            df = self.fetch_klines(limit=50)
            if df is None or len(df) < self.rsi_period + 2:
                return
            
            # ✅ 计算 RSI（使用已完成的 K 线，避免实时波动）
            df['rsi'] = calculate_rsi(df['close'], self.rsi_period)
            current_rsi = df['rsi'].iloc[-2]  # ✅ 使用上一根完成 K 线
            current_price = df['close'].iloc[-1]  # 当前价格
            
            # ✅ 检查最小持仓时间
            if self.position_open and self.entry_time:
                hold_time = (datetime.now() - self.entry_time).total_seconds()
                if hold_time < self.min_hold_time:
                    # 持仓时间不足，只监控止盈止损
                    if self.check_stop_loss_take_profit(current_price):
                        return
                    self.log(f"⏳ 持仓中 ({hold_time:.0f}s/{self.min_hold_time}s) | RSI: {current_rsi:.1f}")
                    return
            
            self.log(f"RSI: {current_rsi:.1f} (阈值：开>{self.rsi_open_threshold} 平<{self.rsi_close_threshold}) | 价格：${current_price:.2f} | 持仓：{'有' if self.position_open else '无'}")
            
            # 检查止盈止损
            if self.check_stop_loss_take_profit(current_price):
                return
            
            # ✅ 交易逻辑（带迟滞区间）
            if not self.position_open:
                # 无仓位：RSI > 52 开空（有缓冲）
                if current_rsi > self.rsi_open_threshold:
                    self.log(f"🔴 开空信号！RSI={current_rsi:.1f} > {self.rsi_open_threshold} (当前无仓位)")
                    self.emit_signal({
                        'type': 'OPEN',
                        'side': 'SELL',
                        'percentage': 1.0,
                        'stop_loss_pct': self.stop_loss_pct
                    })
                    self.position_open = True
                    self.entry_price = current_price
                    self.entry_time = datetime.now()  # ✅ 记录开仓时间
                else:
                    self.log(f"⏸️ 等待开仓信号 (RSI={current_rsi:.1f} <= {self.rsi_open_threshold})")
            else:
                # 有仓位：RSI < 48 平仓（有缓冲）
                if current_rsi < self.rsi_close_threshold:
                    pnl = (self.entry_price - current_price) / self.entry_price * 100
                    self.log(f"🟢 平仓信号！RSI={current_rsi:.1f} < {self.rsi_close_threshold} (当前有仓位，盈亏：{pnl:+.2f}%)")
                    self.emit_signal({
                        'type': 'CLOSE',
                        'side': 'BUY',
                        'percentage': 1.0
                    })
                    self.position_open = False
                    self.entry_price = 0
                    self.entry_time = None  # ✅ 清除开仓时间
                else:
                    pnl = (self.entry_price - current_price) / self.entry_price * 100
                    self.log(f"⏸️ 持仓中 (RSI={current_rsi:.1f} >= {self.rsi_close_threshold}, 盈亏：{pnl:+.2f}%)")
        
        except Exception as e:
            self.log(f"❌ 策略执行错误：{e}")
    
    async def start(self):
        """启动策略"""
        await super().start()
        self.log(f"📊 策略参数：RSI 周期={self.rsi_period}, 开仓阈值={self.rsi_open_threshold}, 平仓阈值={self.rsi_close_threshold}, 最小持仓={self.min_hold_time}s")
        
        # 设置定时器（每分钟执行）
        import asyncio
        async def run_loop():
            while self.status == 'running':
                self.on_tick()
                await asyncio.sleep(self.check_interval)
        
        self.timers.append(asyncio.create_task(run_loop()))
    
    def get_status(self) -> dict:
        """获取策略状态"""
        status = super().get_status()
        status.update({
            'position_open': self.position_open,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'rsi_period': self.rsi_period,
            'rsi_open_threshold': self.rsi_open_threshold,
            'rsi_close_threshold': self.rsi_close_threshold,
            'min_hold_time': self.min_hold_time,
            'take_profit_pct': self.take_profit_pct,
            'stop_loss_pct': self.stop_loss_pct
        })
        return status
