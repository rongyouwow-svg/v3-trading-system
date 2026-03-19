#!/usr/bin/env python3
"""
📈 1 分钟 RSI 策略

策略逻辑:
- RSI > 50: 开多
- RSI > 80: 平仓
- 止损：0.5%
- K 线完成确定指标数值
- 1 分钟后稳定在数值标准，执行操作

参数:
- 交易对：ETHUSDT
- 杠杆：3x
- 保证金：100 USDT
"""

import requests
import time
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

BASE_URL = "http://localhost:3000"
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
STATE_FILE = os.path.join(LOGS_DIR, 'strategy_pids.json')

# 导入策略注册中心
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from strategy_registry import register_strategy, unregister_strategy, get_active_strategies

class RSIStrategy:
    """RSI 策略类"""
    
    def __init__(self, symbol: str = "ETHUSDT", leverage: int = 3, amount: float = 100):
        self.symbol = symbol
        self.leverage = leverage
        self.amount = amount
        
        # RSI 参数
        self.rsi_period = 14
        self.rsi_buy_threshold = 50
        self.rsi_sell_threshold = 80
        
        # 止损参数
        self.stop_loss_pct = 0.002  # 0.2% (单次开仓)
        
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
        
        print(f"📈 RSI 策略初始化")
        print(f"  交易对：{symbol}")
        print(f"  杠杆：{leverage}x")
        print(f"  保证金：{amount} USDT")
        print(f"  RSI 买入阈值：{self.rsi_buy_threshold}")
        print(f"  RSI 平仓阈值：{self.rsi_sell_threshold}")
        print(f"  止损：{self.stop_loss_pct*100}%")
        
        # 🛡️ 启动时强制同步交易所持仓和止损单
        print(f"🔍 启动时同步交易所持仓...")
        self.sync_with_exchange()
        
        # ✅ 关键修复：同步已有止损单
        print(f"🔍 同步已有止损单...")
        self.sync_stop_loss()
        
        # 🛡️ 如果有持仓但没有止损单，立即创建
        if self.position and not self.stop_loss_id:
            print(f"⚠️ 发现持仓但无止损单，立即创建...")
            time.sleep(5)
            self.create_stop_loss()
        
        # 同步结果
            if self.position:
            print(f"⚠️ 发现已有持仓：{self.position['size']} {symbol} @ {self.position['entry_price']}")
            print(f"   持仓价值：{self.position['size'] * self.position['entry_price']:.2f} USDT")
        else:
            print(f"✅ 无已有持仓，可以正常启动")
        
        # 📝 注册到策略注册中心
        print(f"📝 注册到策略注册中心...")
        register_strategy(
            symbol=self.symbol,
            pid=os.getpid(),
            leverage=self.leverage,
            amount=self.amount,
            script='rsi_1min_strategy.py'
        )
        
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
                            return
                
                print(f"✅ 无已有持仓")
            else:
                print(f"⚠️ 同步持仓失败：{data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ 同步持仓异常：{e}")
    
    def sync_stop_loss(self):
        """🛡️ 同步已有止损单（修复：启动时恢复 stop_loss_id）"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/stop-loss",
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                orders = data.get('orders', [])
                
                # 查找本交易对的止损单
                for order in orders:
                    if order.get('symbol') == self.symbol and order.get('status') == 'NEW':
                        self.stop_loss_id = order.get('algo_id')
                        trigger_price = order.get('trigger_price')
                        print(f"✅ 同步止损单成功：ID={self.stop_loss_id}, 触发价={trigger_price}")
                        return
                
                print(f"✅ 无已有止损单")
            else:
                print(f"⚠️ 同步止损单失败：{data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ 同步止损单异常：{e}")
    
    def save_state(self):
        """保存策略状态到文件"""
        try:
            # 读取现有状态
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    all_states = json.load(f)
            else:
                all_states = {}
            
            # 更新当前策略状态
            all_states[self.symbol] = {
                'status': 'running',
                'last_rsi': self.last_rsi,
                'signal_rsi': self.signal_rsi,
                'waiting_confirmation': self.waiting_confirmation,
                'position': self.position,
                'entry_price': self.entry_price,
                'signals_sent': self.signals_sent,
                'signals_executed': self.signals_executed,
                'trades': self.trades[-10:],  # 只保留最近 10 条成交
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 保存
            os.makedirs(LOGS_DIR, exist_ok=True)
            with open(STATE_FILE, 'w') as f:
                json.dump(all_states, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存状态失败：{e}")
    
    def get_klines(self, limit: int = 50) -> List[Dict]:
        """获取 K 线数据"""
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
            print(f"❌ 获取 K 线失败：{e}")
            return []
    
    def calculate_rsi(self, klines: List[Dict]) -> float:
        """计算 RSI 指标"""
        if len(klines) < self.rsi_period + 1:
            return 50  # 默认值
        
        # 获取收盘价
        closes = [float(k['close']) for k in klines[-(self.rsi_period + 1):]]
        
        # 计算涨跌幅
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        # 计算平均涨跌幅
        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)
        
        # 计算 RSI
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def check_signal(self, rsi: float) -> str:
        """
        检查信号（2 根 K 线确认逻辑）
        
        逻辑:
        - T 时刻：RSI>50 → 记录信号，等待确认
        - T+1 时刻：RSI 仍然>50 → 执行开多
        
        返回:
        - 'buy': 开多信号
        - 'sell': 平仓信号
        - 'wait': 等待确认
        - 'none': 无信号
        """
        # 如果已经在等待确认
        if self.waiting_confirmation:
            # 第二根 K 线，检查是否仍然满足条件
            if rsi > self.rsi_buy_threshold:
                # 确认！执行开多
                self.waiting_confirmation = False
                self.signal_rsi = None
                return 'buy'
            else:
                # 不满足，重置
                self.waiting_confirmation = False
                self.signal_rsi = None
                return 'none'
        
        # 第一根 K 线，检查是否触发信号
        if rsi > self.rsi_buy_threshold:
            # 记录信号，等待下一根 K 线确认
            self.signal_rsi = rsi
            self.waiting_confirmation = True
            return 'wait'
        
        # 平仓逻辑（有持仓且 RSI>80）
        if self.position == 'LONG' and rsi > self.rsi_sell_threshold:
            return 'sell'
        
        return 'none'
    
    def open_position(self):
        """开仓"""
        print(f"\n🚀 开仓信号")
        print(f"  RSI: {self.last_rsi:.2f}")
        
        # 仓位控制：检查已用保证金
        max_position_value = self.amount * self.leverage * 1.05  # 允许最大金额（设置×105%）
        
        # 获取当前持仓
        try:
            response = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
            data = response.json()
            positions = data.get('positions', [])
            
            # 计算当前已用保证金
            current_position_value = 0
            for pos in positions:
                if pos['symbol'] == self.symbol and pos['side'] == 'LONG':
                    current_position_value = pos['size'] * pos['current_price']
                    break
            
            # 计算本次开仓价值
            open_position_value = self.amount * self.leverage
            
            print(f"  当前持仓价值：{current_position_value:.2f} USDT")
            print(f"  本次开仓价值：{open_position_value:.2f} USDT")
            print(f"  开仓后总仓位：{current_position_value + open_position_value:.2f} USDT")
            print(f"  允许最大仓位：{max_position_value:.2f} USDT")
            
            if current_position_value + open_position_value >= max_position_value:
                print(f"⚠️ 开仓后将超过仓位上限，跳过开仓")
                return False
                
        except Exception as e:
            print(f"⚠️ 获取持仓失败：{e}，继续开仓")
        
        # 记录信号
        self.signals_sent += 1
        
        # 创建买单
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/order",
                json={
                    'symbol': self.symbol,
                    'side': 'BUY',
                    'type': 'MARKET',
                    'quantity': (self.amount * self.leverage) / 2000,  # 估算数量（100*3/2000=0.15）
                    'leverage': self.leverage
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                order = data.get('order', {})
                order_id = order.get('order_id', '-')
                
                # 等待订单成交并获取实际成交价（最多重试 5 次）
                self.entry_price = 0
                for retry in range(5):
                    time.sleep(2)
                    try:
                        response = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
                        pos_data = response.json()
                        positions = pos_data.get('positions', [])
                        
                        for pos in positions:
                            if pos['symbol'] == self.symbol and pos['side'] == 'LONG' and float(pos['size']) > 0:
                                self.entry_price = float(pos['entry_price'])
                                self.position = 'LONG'
                                print(f"  获取到入场价：{self.entry_price} (重试{retry+1}/5)")
                                break
                        
                        if self.entry_price > 0:
                            break
                    except Exception as e:
                        print(f"⚠️ 重试{retry+1}/5 获取持仓失败：{e}")
                
                # 如果还是没获取到，使用估算值
                if self.entry_price == 0:
                    self.entry_price = 2000  # 默认估算值
                    self.position = 'LONG'
                    print(f"⚠️ 使用估算入场价：{self.entry_price}")
                
                self.signals_executed += 1
                
                # 记录成交
                self.trades.append({
                    'type': 'open_long',
                    'price': self.entry_price,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'order_id': order_id
                })
                
                print(f"✅ 开仓成功")
                print(f"  订单 ID: {order_id}")
                print(f"  入场价：{self.entry_price}")
                print(f"  信号：{self.signals_sent}/{self.signals_executed}")
                
                # 开仓成功后立即创建止损单
                self.create_stop_loss()
                
                # 保存状态
                self.save_state()
                
                return True
            else:
                print(f"❌ 开仓失败：{data}")
                return False
        except Exception as e:
            print(f"❌ 开仓异常：{e}")
            return False
    
    # ⚠️ 已移除：create_stop_loss() 方法由执行引擎统一管理
    def create_stop_loss(self):
        """创建止损单（修复重复创建问题）"""
        # ✅ 关键修复：检查是否已有止损单
        if not self.position or self.entry_price <= 0:
            print(f"⚠️ 无法创建止损单：无持仓或入场价无效")
            return
        
        # ✅ 关键修复：如果已经有止损单，不再创建
        if self.stop_loss_id is not None:
            print(f"✅ 已有止损单 (ID: {self.stop_loss_id})，跳过创建")
            return
        
        # 获取当前价格
        try:
            response = requests.get(f"{BASE_URL}/api/binance/ticker?symbol={self.symbol}", timeout=10)
            ticker = response.json()
            current_price = float(ticker.get('price', self.entry_price))
        except:
            current_price = self.entry_price
        
        # 如果已亏损，使用当前价格计算止损（避免立即触发）
        if current_price < self.entry_price:
            stop_price = current_price * (1 - self.stop_loss_pct)
            print(f"⚠️ 当前已亏损，使用当前价计算止损：{current_price} → {stop_price}")
        else:
            stop_price = self.entry_price * (1 - self.stop_loss_pct)
            print(f"✅ 使用入场价计算止损：{self.entry_price} → {stop_price}")
        
        print(f"\n🛡️ 创建止损单")
        print(f"  止损价：{stop_price}")
        
        try:
            # 计算数量并保留 3 位小数（ETHUSDT 精度要求）
            quantity = round(self.amount * self.leverage / self.entry_price, 3)
            
            response = requests.post(
                f"{BASE_URL}/api/binance/stop-loss",
                json={
                    'symbol': self.symbol,
                    'side': 'SELL',
                    'trigger_price': round(stop_price, 2),  # ETHUSDT 价格精度 2 位
                    'quantity': quantity
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                print(f"✅ 止损单创建成功")
                # ✅ 关键修复：保存止损单 ID，避免重复创建
                self.stop_loss_id = data.get('algo_id')
                print(f"  止损单 ID: {self.stop_loss_id}")
            else:
                print(f"❌ 止损单创建失败：{data}")
        except Exception as e:
            print(f"❌ 止损单异常：{e}")
    
    def close_position(self):
        """平仓"""
        if not self.position:
            return
        
        print(f"\n📉 平仓信号")
        print(f"  RSI: {self.last_rsi:.2f}")
        print(f"  入场价：{self.entry_price}")
        
        # ✅ 止损单由执行引擎取消
        
        # 创建卖单
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/order",
                json={
                    'symbol': self.symbol,
                    'side': 'SELL',
                    'type': 'MARKET',
                    'quantity': self.amount * self.leverage / self.entry_price,
                    'leverage': self.leverage
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                order = data.get('order', {})
                exit_price = float(order.get('price', 0))
                pnl = (exit_price - self.entry_price) * (self.amount * self.leverage / self.entry_price)
                
                # 记录成交
                self.trades.append({
                    'type': 'close_long',
                    'price': exit_price,
                    'pnl': pnl,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'order_id': order.get('order_id', '-')
                })
                
                print(f"✅ 平仓成功")
                print(f"  出场价：{exit_price}")
                print(f"  盈亏：{pnl:.2f} USDT")
                print(f"  信号：{self.signals_sent}/{self.signals_executed}")
                
                self.position = None
                self.entry_price = 0
                self.stable_count = 0
                
                # 保存状态
                self.save_state()
                
                return True
            else:
                print(f"❌ 平仓失败：{data}")
                return False
        except Exception as e:
            print(f"❌ 平仓异常：{e}")
            return False
    
    # ⚠️ 已移除：cancel_stop_loss() 方法由执行引擎统一管理
    def cancel_stop_loss(self):
        """取消止损单（修复：必须传 algo_id）"""
        print(f"\n❌ 取消止损单")
        
        if not self.stop_loss_id:
            print(f"⚠️ 无止损单 ID，跳过取消")
            return
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/stop-loss/cancel",
                json={
                    'symbol': self.symbol,
                    'algo_id': self.stop_loss_id  # ✅ 关键：必须传 algo_id
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                print(f"✅ 止损单取消成功 (ID: {self.stop_loss_id})")
                self.stop_loss_id = None  # ✅ 清除 ID
            else:
                print(f"❌ 止损单取消失败：{data}")
        except Exception as e:
            print(f"❌ 止损单取消异常：{e}")
    
    def run(self, interval: int = 60):
        """运行策略（循环调用）"""
        print(f"\n{'='*60}")
        print(f"🚀 RSI 策略启动")
        print(f"{'='*60}")
        print(f"  - K 线间隔：{interval}秒")
        
        self.is_running = True
        
        while self.is_running:
            try:
                # 获取 K 线
                klines = self.get_klines()
                
                if not klines:
                    print(f"⚠️ 无 K 线数据")
                    time.sleep(60)
                    continue
                
                # 计算 RSI
                rsi = self.calculate_rsi(klines)
                
                # 5% 硬止损检查
                if self.position == 'LONG' and self.entry_price > 0:
                    current_price = float(klines[-1]['close'])
                    loss_pct = (current_price - self.entry_price) / self.entry_price
                    if loss_pct <= -0.05:  # -5% 硬止损
                        print(f"\n🛑 触发 5% 硬止损！亏损：{loss_pct*100:.2f}%")
                        self.close_position()
                        time.sleep(60)
                        continue
                
                # 检查信号（2 根 K 线确认）
                signal = self.check_signal(rsi)
                
                if signal == 'wait':
                    print(f"\n📊 RSI: {rsi:.2f} (等待确认...)")
                elif signal == 'buy':
                    print(f"\n📊 RSI: {rsi:.2f} (确认！)")
                    # 开仓逻辑
                    if not self.position:
                        self.open_position()
                        # 开单后立即设置止损
                        time.sleep(2)  # 等待开单完成
                        self.create_stop_loss()
                elif signal == 'sell':
                    print(f"\n📊 RSI: {rsi:.2f} (平仓信号！)")
                    # 平仓逻辑
                    if self.position:
                        self.close_position()
                else:
                    print(f"📊 RSI: {rsi:.2f} (无信号)")
                
                # 更新 RSI 并保存状态
                self.last_rsi = rsi
                self.save_state()
                
                # 等待 1 分钟
                time.sleep(60)
                
            except KeyboardInterrupt:
                print(f"\n🛑 策略停止")
                # ✅ 关键修复：策略停止时必须平仓并撤销止损单
                if self.position:
                    print(f"📉 平仓...")
                    self.close_position()
                # ✅ 撤销止损单
                if self.stop_loss_id:
                    print(f"❌ 撤销止损单...")
                    self.cancel_stop_loss()
                break
            except Exception as e:
                print(f"❌ 策略异常：{e}")
                time.sleep(10)
            
            # 更新心跳
            from strategy_registry import StrategyRegistry
            registry = StrategyRegistry()
            registry.update_heartbeat(self.symbol)
            
            # 等待下一根 K 线
            time.sleep(interval)
        
        # 📝 策略停止时注销
        print(f"📝 注销策略 {self.symbol}...")
        unregister_strategy(self.symbol)
        print(f"✅ 策略已注销")


if __name__ == "__main__":
    # 创建策略实例
    strategy = RSIStrategy(
        symbol='ETHUSDT',
        leverage=3,
        amount=100
    )
    
    # 手动设置止损比例
    strategy.stop_loss_pct = 0.002  # 0.2% 策略止损
    
    # 运行策略（循环调用，每根 K 线检查信号）
    strategy.run(interval=60)  # 60 秒=1 分钟 K 线

import signal
import sys

    print(f"\n🛑 收到信号 {signum}，停止策略...")
    if 'strategy' in locals():
        if strategy.position:
            print(f"📉 平仓...")
            strategy.close_position()
        if strategy.stop_loss_id:
            print(f"❌ 撤销止损单...")
            strategy.cancel_stop_loss()
    print(f"📝 注销策略...")
    unregister_strategy('ETHUSDT')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
