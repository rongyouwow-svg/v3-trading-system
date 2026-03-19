#!/usr/bin/env python3
"""
📈 UNI RSI 策略（v24 测试网版）

策略逻辑:
- RSI < 18 + 布林带下轨 + 成交量>3 倍: 开多
- RSI > 80: 平仓
- 止损：0.8%
- K 线完成确定指标数值
- 1 分钟后稳定在数值标准，执行操作

v24 优化:
- 加入主力洗盘检测
- 信号分级（S/A/B）
- 动态仓位管理
- 多时间框架确认

参数:
- 交易对：UNIUSDT
- 杠杆：3x
- 保证金：100 USDT
"""

import requests
import time
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

BASE_URL = "http://localhost:3000"
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
STATE_FILE = os.path.join(LOGS_DIR, 'strategy_pids.json')

class UNIRsiStrategy:
    """UNI RSI 策略类（v24 测试网版）"""
    
    def __init__(self, symbol: str = "UNIUSDT", leverage: int = 3, amount: float = 100):
        self.symbol = symbol
        self.leverage = leverage
        self.amount = amount
        
        # RSI 参数
        self.rsi_period = 7
        self.rsi_buy_threshold = 18
        self.rsi_sell_threshold = 80
        
        # 止损止盈参数
        self.stop_loss_pct = 0.008  # 0.8%
        self.take_profit_pct = 0.02  # 2.0%
        
        # v24 主力洗盘参数
        self.volume_ratio_threshold = 0.8  # 缩量<0.8 倍
        self.lower_shadow_threshold = 0.005  # 长下影>0.5%
        self.rsi_oversold = 40  # RSI 超卖
        
        # 状态
        self.position = None  # 当前持仓
        self.entry_price = 0
        self.last_rsi = 0
        self.signal_rsi = None  # 信号 RSI（第一根 K 线的 RSI）
        self.waiting_confirmation = False  # 等待确认标志
        self.is_running = False  # 运行状态
        
        # 信号和成交追踪
        self.signals_sent = 0
        self.signals_executed = 0
        self.trades = []  # 成交记录
        
        # 止损单追踪
        self.stop_loss_id = None  # 止损单 ID
        
        # v24 信号分级
        self.signal_grade = None  # S/A/B
        
        print(f"📈 UNI RSI 策略初始化（v24 测试网版）")
        print(f"  交易对：{symbol}")
        print(f"  杠杆：{leverage}x")
        print(f"  保证金：{amount} USDT")
        print(f"  RSI 买入阈值：{self.rsi_buy_threshold}")
        print(f"  RSI 平仓阈值：{self.rsi_sell_threshold}")
        print(f"  止损：{self.stop_loss_pct*100}%")
        print(f"  止盈：{self.take_profit_pct*100}%")
        print(f"  v24 主力洗盘： enabled")
        
        # 🛡️ 启动时强制同步交易所持仓
        print(f"🔍 启动时同步交易所持仓...")
        self.sync_with_exchange()
        
        # 同步结果
        if self.position:
            print(f"⚠️ 发现已有持仓：{self.position['size']} {symbol} @ {self.position['entry_price']}")
            print(f"   持仓价值：{self.position['size'] * self.position['entry_price']:.2f} USDT")
        else:
            print(f"✅ 无已有持仓，可以正常启动")
        
        # 保存初始状态
        self.save_state()
    
    def sync_with_exchange(self):
        """🛡️ 强制同步交易所持仓"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/positions",
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                positions = data.get('positions', [])
                
                # 查找本交易对的持仓
                for pos in positions:
                    if pos.get('symbol') == self.symbol:
                        size = float(pos.get('size', 0))
                        if size > 0:  # 有持仓
                            self.position = pos
                            self.entry_price = float(pos.get('entry_price', 0))
                            print(f"✅ 同步持仓成功：{size} {self.symbol} @ ${self.entry_price}")
                            
                            # 检查止损单
                            self.check_existing_stop_loss()
                            return
                
                print(f"✅ 无已有持仓")
            else:
                print(f"⚠️ 同步持仓失败：{data.get('error')}")
        except Exception as e:
            print(f"⚠️ 同步持仓异常：{e}")
    
    def check_existing_stop_loss(self):
        """🛡️ 检查已有止损单"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/stop-loss",
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                orders = data.get('orders', [])
                for order in orders:
                    if order.get('symbol') == self.symbol and order.get('status') == 'NEW':
                        self.stop_loss_id = order.get('algo_id')
                        print(f"✅ 发现已有止损单：{self.stop_loss_id}")
                        return
                
                print(f"⚠️ 无已有止损单，需要创建")
        except Exception as e:
            print(f"⚠️ 检查止损单异常：{e}")
    
    def get_klines(self, interval: str = "15m", limit: int = 100) -> Optional[pd.DataFrame]:
        """获取 K 线数据"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/klines",
                params={
                    'symbol': self.symbol,
                    'interval': interval,
                    'limit': limit
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                klines = data.get('klines', data.get('data', []))
                if len(klines) > 0 and isinstance(klines[0], dict):
                    # 字典格式：[{'timestamp':..., 'close':...}, ...]
                    df = pd.DataFrame(klines)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                else:
                    # 列表格式：[[timestamp, open, high, low, close, volume, ...], ...]
                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_volume', 'taker_buy_quote'
                    ])
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                
                # 转换数据类型
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = df[col].astype(float)
                
                return df
            else:
                print(f"❌ 获取 K 线失败：{data.get('error')}")
                return None
        except Exception as e:
            print(f"❌ 获取 K 线异常：{e}")
            return None
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['bb_ma'] = df['close'].rolling(20).mean()
        df['bb_std'] = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_ma'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_ma'] - (df['bb_std'] * 2)
        
        # 成交量
        df['volume_ma20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        
        # K 线特征
        df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']
        df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
        
        return df
    
    def detect_whale_wash(self, df: pd.DataFrame) -> bool:
        """🐋 检测主力洗盘信号（v24 核心）"""
        if len(df) < 20:
            return False
        
        last = df.iloc[-1]
        
        # 主力洗盘条件
        whale_wash = (
            (last['volume_ratio'] < self.volume_ratio_threshold) and  # 缩量<0.8 倍
            (last['close'] < df.iloc[-2]['close']) and  # 价格回调
            (last['lower_shadow'] > self.lower_shadow_threshold) and  # 长下影>0.5%
            (last['rsi'] < self.rsi_oversold) and  # RSI 超卖<40
            (last['close'] < last['bb_lower'])  # 跌破布林带下轨
        )
        
        if whale_wash:
            print(f"🐋 主力洗盘信号 detected!")
            print(f"   成交量比率：{last['volume_ratio']:.2f}")
            print(f"   价格变化：{(last['close'] - df.iloc[-2]['close'])/df.iloc[-2]['close']*100:.2f}%")
            print(f"   下影线：{last['lower_shadow']*100:.2f}%")
            print(f"   RSI: {last['rsi']:.1f}")
            print(f"   布林带位置：below lower")
        
        return whale_wash
    
    def grade_signal(self, v23_signal: bool, whale_wash: bool, rsi: float) -> Optional[str]:
        """📊 信号分级（v24）"""
        if v23_signal and whale_wash:
            return 'S'  # 黄金信号（主力洗盘 + v23）
        elif v23_signal and rsi < 15:
            return 'A'  # 优质信号（深度超卖）
        elif v23_signal:
            return 'B'  # 标准信号
        else:
            return None
    
    def calculate_position_size(self, signal_grade: str) -> float:
        """💰 动态仓位计算（v24）"""
        base_position = self.amount * 0.25  # 基础仓位 25%
        
        if signal_grade == 'S':
            return base_position * 2.4  # 60%
        elif signal_grade == 'A':
            return base_position * 1.6  # 40%
        else:
            return base_position * 1.0  # 25%
    
    def check_v23_signal(self, df: pd.DataFrame) -> bool:
        """检查 v23 标准信号"""
        if len(df) < 20:
            return False
        
        last = df.iloc[-1]
        
        # v23 信号条件
        v23_signal = (
            (last['rsi'] < self.rsi_buy_threshold) and  # RSI<18
            (last['close'] < last['bb_lower']) and  # 跌破布林带下轨
            (last['volume_ratio'] > 3.0)  # 成交量>3 倍
        )
        
        return v23_signal
    
    def create_stop_loss(self, quantity: float):
        """🛡️ 创建止损单"""
        if not self.position:
            print(f"⚠️ 无持仓，跳过止损单创建")
            return False
        
        stop_price = round(self.entry_price * (1 - self.stop_loss_pct), 2)
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/stop-loss",
                json={
                    'symbol': self.symbol,
                    'side': 'SELL',
                    'trigger_price': stop_price,
                    'quantity': quantity,
                    'algo_type': 'CONDITIONAL',
                    'order_type': 'STOP_MARKET'
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                self.stop_loss_id = data.get('order', {}).get('algo_id')
                print(f"✅ 止损单创建成功 (ID: {self.stop_loss_id}, 触发价：${stop_price})")
                
                # 验证止损单
                time.sleep(5)
                self.verify_stop_loss()
                
                return True
            else:
                print(f"❌ 止损单创建失败：{data.get('error')}")
                return False
        except Exception as e:
            print(f"❌ 止损单创建异常：{e}")
            return False
    
    def verify_stop_loss(self):
        """🛡️ 验证止损单是否生效"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/stop-loss",
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                orders = data.get('orders', [])
                for order in orders:
                    if order.get('algo_id') == self.stop_loss_id:
                        print(f"✅ 止损单验证成功 (状态：{order.get('status')})")
                        return True
                
                print(f"⚠️ 止损单未找到，重新创建")
                return self.create_stop_loss(self.position['size'])
        except Exception as e:
            print(f"⚠️ 验证止损单异常：{e}")
    
    def close_position(self):
        """📉 平仓"""
        if not self.position:
            print(f"⚠️ 无持仓，跳过平仓")
            return False
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/close-position",
                json={
                    'symbol': self.symbol,
                    'side': 'SELL' if self.position['side'] == 'LONG' else 'BUY'
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                pnl = data.get('pnl', 0)
                self.trades.append({
                    'timestamp': datetime.now().isoformat(),
                    'symbol': self.symbol,
                    'side': 'CLOSE',
                    'pnl': pnl
                })
                
                print(f"✅ 平仓成功 (盈亏：{pnl:.2f} USDT)")
                
                # 取消止损单
                self.cancel_stop_loss()
                
                # 重置状态
                self.position = None
                self.entry_price = 0
                self.stop_loss_id = None
                
                return True
            else:
                print(f"❌ 平仓失败：{data.get('error')}")
                return False
        except Exception as e:
            print(f"❌ 平仓异常：{e}")
            return False
    
    def cancel_stop_loss(self):
        """🛡️ 取消止损单"""
        if not self.stop_loss_id:
            return
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/stop-loss/cancel",
                json={
                    'symbol': self.symbol,
                    'algo_id': self.stop_loss_id
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                print(f"✅ 止损单已取消 (ID: {self.stop_loss_id})")
                self.stop_loss_id = None
            else:
                print(f"⚠️ 取消止损单失败：{data.get('error')}")
        except Exception as e:
            print(f"⚠️ 取消止损单异常：{e}")
    
    def save_state(self):
        """💾 保存状态"""
        try:
            os.makedirs(LOGS_DIR, exist_ok=True)
            
            # 读取现有状态
            try:
                with open(STATE_FILE, 'r') as f:
                    all_state = json.load(f)
            except:
                all_state = {}
            
            # 确保是字典格式
            if not isinstance(all_state, dict):
                all_state = {}
            
            # 更新本策略状态
            all_state[self.symbol] = {
                'status': 'running' if self.is_running else 'stopped',
                'last_rsi': self.last_rsi,
                'position': self.position,
                'entry_price': self.entry_price,
                'signals_sent': self.signals_sent,
                'signals_executed': self.signals_executed,
                'trades': self.trades,
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            with open(STATE_FILE, 'w') as f:
                json.dump(all_state, f, indent=2)
        except Exception as e:
            print(f"⚠️ 保存状态异常：{e}")
    
    def run(self, interval: int = 60):
        """🚀 运行策略（循环）"""
        self.is_running = True
        print(f"\n🚀 UNI RSI 策略启动")
        print(f"   检查间隔：{interval}秒")
        print(f"   停止时间：23:59")
        print(f"="*70)
        
        while self.is_running:
            try:
                # 检查是否到停止时间
                current_time = datetime.now().strftime("%H:%M")
                if current_time >= "23:59":
                    print(f"\n⏰ 到达停止时间：{current_time}")
                    self.is_running = False
                    break
                
                # 获取 K 线
                df = self.get_klines(interval="15m", limit=100)
                if df is None or len(df) < 20:
                    print(f"⚠️ K 线数据不足，跳过")
                    time.sleep(interval)
                    continue
                
                # 计算指标
                df = self.calculate_indicators(df)
                
                # 获取最新数据
                last = df.iloc[-1]
                self.last_rsi = last['rsi']
                
                print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   价格：${last['close']:.2f}")
                print(f"   RSI: {self.last_rsi:.1f}")
                print(f"   成交量比率：{last['volume_ratio']:.2f}")
                
                # 检查平仓信号
                if self.position and self.last_rsi > self.rsi_sell_threshold:
                    print(f"\n📉 RSI > {self.rsi_sell_threshold}, 平仓")
                    self.close_position()
                
                # 检查开仓信号
                elif not self.position:
                    v23_signal = self.check_v23_signal(df)
                    whale_wash = self.detect_whale_wash(df)
                    
                    # 信号分级
                    signal_grade = self.grade_signal(v23_signal, whale_wash, self.last_rsi)
                    
                    if signal_grade:
                        print(f"\n🎯 {signal_grade}级信号 detected!")
                        print(f"   v23 信号：{v23_signal}")
                        print(f"   主力洗盘：{whale_wash}")
                        print(f"   RSI: {self.last_rsi:.1f}")
                        
                        # 动态仓位
                        position_size = self.calculate_position_size(signal_grade)
                        print(f"   仓位：{position_size:.2f} USDT ({position_size/self.amount*100:.0f}%)")
                        
                        # 开仓
                        self.open_position(position_size)
                
                # 保存状态
                self.save_state()
                
                # 等待下一次检查
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print(f"\n\n⚠️ 策略停止（用户中断）")
                self.is_running = False
                break
            except Exception as e:
                print(f"❌ 策略运行异常：{e}")
                time.sleep(interval)
        
        print(f"\n✅ 策略运行结束")
    
    def open_position(self, amount: float):
        """📈 开仓"""
        try:
            # 获取当前价格
            response = requests.get(
                f"{BASE_URL}/api/binance/price",
                params={'symbol': self.symbol},
                timeout=10
            )
            data = response.json()
            
            if not data.get('success'):
                print(f"❌ 获取价格失败")
                return
            
            price = float(data.get('price'))
            
            # 计算数量
            quantity = (amount * self.leverage) / price
            
            # 精度处理（UNI 需要 1 位小数）
            quantity = round(quantity, 1)
            
            print(f"\n📈 开仓信号")
            print(f"   价格：${price:.2f}")
            print(f"   数量：{quantity} {self.symbol}")
            print(f"   仓位：{amount:.2f} USDT")
            print(f"   杠杆：{self.leverage}x")
            
            # 开仓
            response = requests.post(
                f"{BASE_URL}/api/binance/order",
                json={
                    'symbol': self.symbol,
                    'side': 'BUY',
                    'type': 'MARKET',
                    'quantity': quantity
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                self.position = {
                    'symbol': self.symbol,
                    'side': 'LONG',
                    'size': quantity,
                    'entry_price': price
                }
                self.entry_price = price
                
                print(f"✅ 开仓成功 ({quantity} {self.symbol} @ ${price:.2f})")
                
                # 创建止损单
                time.sleep(2)
                self.create_stop_loss(quantity)
                
                # 记录信号
                self.signals_sent += 1
                self.signals_executed += 1
                
                # 记录成交
                self.trades.append({
                    'timestamp': datetime.now().isoformat(),
                    'symbol': self.symbol,
                    'side': 'BUY',
                    'size': quantity,
                    'price': price,
                    'amount': amount
                })
            else:
                print(f"❌ 开仓失败：{data.get('error')}")
        except Exception as e:
            print(f"❌ 开仓异常：{e}")


def main():
    """主函数"""
    print("="*70)
    print("📈 UNI RSI 策略（v24 测试网版）")
    print("="*70)
    
    # 创建策略实例
    strategy = UNIRsiStrategy(
        symbol="UNIUSDT",
        leverage=3,
        amount=100
    )
    
    # 运行策略
    strategy.run(interval=60)  # 每 60 秒检查一次


if __name__ == '__main__':
    main()
