#!/usr/bin/env python3
"""
📈 策略模板文件

策略逻辑:
    - 开仓条件：RSI > 50
    - 平仓条件：RSI > 80
    - 止损规则：无（可扩展）

参数:
    - 交易对：ETHUSDT
    - 杠杆：3x
    - 保证金：100 USDT

用法:
    python3 strategy_template.py
"""

# ==================== 导入依赖 ====================
import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# ==================== 常量定义 ====================
BASE_URL = "http://localhost:3000"
LOG_FILE = "logs/strategy_template.log"

# ==================== 策略类 ====================
class StrategyTemplate:
    """策略模板类"""
    
    def __init__(self, symbol: str = "ETHUSDT", leverage: int = 3, amount: float = 100):
        """
        初始化策略
        
        Args:
            symbol: 交易对
            leverage: 杠杆
            amount: 保证金
        """
        # 策略配置
        self.symbol = symbol
        self.leverage = leverage
        self.amount = amount
        
        # 状态变量（必须包含）
        self.position = None  # 当前持仓
        self.entry_price = 0
        self.last_rsi = 0
        self.is_running = False  # 运行状态
        
        # 统计信息
        self.signals_sent = 0
        self.signals_executed = 0
        self.trades = []
        
        # 日志初始化
        self.log(f"📈 策略初始化：{symbol}")
        self.log(f"  - 杠杆：{leverage}x")
        self.log(f"  - 保证金：{amount} USDT")
    
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        # 写入日志文件
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except Exception as e:
            print(f"❌ 日志写入失败：{e}")
    
    def get_klines(self, limit: int = 50) -> List[Dict]:
        """
        获取 K 线数据
        
        Args:
            limit: K 线数量
        
        Returns:
            K 线数据列表
        """
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/klines",
                params={
                    'symbol': self.symbol,
                    'interval': '1m',
                    'limit': limit
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                return data.get('klines', [])
            return []
        except Exception as e:
            self.log(f"❌ 获取 K 线失败：{e}")
            return []
    
    def calculate_rsi(self, klines: List[Dict]) -> float:
        """
        计算 RSI 指标
        
        Args:
            klines: K 线数据
        
        Returns:
            RSI 值
        """
        if len(klines) < 15:
            return 50.0
        
        # 提取收盘价
        closes = [float(k['close']) for k in klines[-15:]]
        
        # 计算涨跌幅
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        
        # 计算平均涨跌
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        
        # 计算 RSI
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def check_signal(self, rsi: float) -> Optional[str]:
        """
        检查交易信号
        
        Args:
            rsi: RSI 值
        
        Returns:
            信号类型 ('buy' / 'sell' / None)
        """
        # 开仓信号
        if rsi > 50 and not self.position:
            return 'buy'
        
        # 平仓信号
        if rsi > 80 and self.position == 'LONG':
            return 'sell'
        
        return None
    
    def open_position(self):
        """开仓"""
        self.log(f"\n🚀 开仓信号")
        self.log(f"  RSI: {self.last_rsi:.2f}")
        
        # 检查是否已有持仓
        if self.position:
            self.log(f"⚠️ 已有持仓，跳过开仓")
            return False
        
        # 创建买单
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/order",
                json={
                    'symbol': self.symbol,
                    'side': 'BUY',
                    'type': 'MARKET',
                    'quantity': self.amount * self.leverage / 2000,
                    'leverage': self.leverage
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                order = data.get('order', {})
                self.entry_price = float(order.get('price', 0))
                self.position = 'LONG'
                
                self.log(f"✅ 开仓成功")
                self.log(f"  订单 ID: {order.get('order_id', '-')}")
                self.log(f"  入场价：{self.entry_price}")
                
                # 记录成交
                self.trades.append({
                    'type': 'open_long',
                    'price': self.entry_price,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'order_id': order.get('order_id', '-')
                })
                
                return True
            else:
                self.log(f"❌ 开仓失败：{data}")
                return False
        except Exception as e:
            self.log(f"❌ 开仓异常：{e}")
            return False
    
    def close_position(self):
        """平仓"""
        if not self.position:
            return
        
        self.log(f"\n📉 平仓信号")
        self.log(f"  RSI: {self.last_rsi:.2f}")
        self.log(f"  入场价：{self.entry_price}")
        
        # 获取持仓数量
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/positions",
                timeout=10
            )
            data = response.json()
            
            quantity = 0
            for pos in data.get('positions', []):
                if pos['symbol'] == self.symbol:
                    quantity = pos['size']
                    break
            
            if quantity == 0:
                self.log(f"⚠️ 无持仓，跳过平仓")
                return
            
            # 创建卖单
            response = requests.post(
                f"{BASE_URL}/api/binance/order",
                json={
                    'symbol': self.symbol,
                    'side': 'SELL',
                    'type': 'MARKET',
                    'quantity': quantity,
                    'reduceOnly': True
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                order = data.get('order', {})
                exit_price = float(order.get('price', 0))
                pnl = (exit_price - self.entry_price) * quantity
                
                self.log(f"✅ 平仓成功")
                self.log(f"  出场价：{exit_price}")
                self.log(f"  盈亏：{pnl:.2f} USDT")
                
                # 记录成交
                self.trades.append({
                    'type': 'close_long',
                    'price': exit_price,
                    'pnl': pnl,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'order_id': order.get('order_id', '-')
                })
                
                # 重置状态
                self.position = None
                self.entry_price = 0
                
                return True
            else:
                self.log(f"❌ 平仓失败：{data}")
                return False
        except Exception as e:
            self.log(f"❌ 平仓异常：{e}")
            return False
    
    def run(self, interval: int = 60):
        """
        运行策略（循环调用）
        
        Args:
            interval: K 线间隔（秒），默认 60 秒（1 分钟）
        """
        self.log(f"\n{'='*60}")
        self.log(f"🚀 策略启动")
        self.log(f"{'='*60}")
        self.log(f"  - K 线间隔：{interval}秒")
        
        # 设置运行状态（必须）
        self.is_running = True
        
        while self.is_running:
            try:
                # 获取 K 线
                klines = self.get_klines()
                
                if not klines or len(klines) < 15:
                    self.log(f"⚠️ K 线数据不足，跳过")
                    time.sleep(interval)
                    continue
                
                # 计算 RSI
                rsi = self.calculate_rsi(klines)
                self.last_rsi = rsi
                
                # 检查信号
                signal = self.check_signal(rsi)
                
                if signal == 'buy':
                    self.open_position()
                elif signal == 'sell':
                    self.close_position()
                
                # 等待下一根 K 线
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.log(f"\n🛑 策略停止")
                if self.position:
                    self.close_position()
                self.is_running = False
                break
            except Exception as e:
                self.log(f"❌ 策略异常：{e}")
                time.sleep(10)
        
        self.log(f"✅ 策略已停止")


# ==================== 主程序 ====================
if __name__ == "__main__":
    # 创建策略实例
    strategy = StrategyTemplate(
        symbol='ETHUSDT',
        leverage=3,
        amount=100
    )
    
    # 运行策略（循环调用，每根 K 线检查信号）
    strategy.run(interval=60)  # 60 秒=1 分钟 K 线
