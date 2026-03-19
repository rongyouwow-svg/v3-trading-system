#!/usr/bin/env python3
"""
📈 RSI 分批建仓策略 (Scale-In Strategy)

策略逻辑:
- RSI > 50: 分批开多 (30% → 50% → 20%)
- RSI > 80: 全部平仓
- 止损：0.5% (策略) + 5% (硬止损兜底)
- K 线完成确定指标数值
- 1 分钟后稳定在数值标准，执行操作

参数:
- 交易对：AVAXUSDT
- 杠杆：3x
- 总保证金：200 USDT
- 分批比例：30% / 50% / 20%
"""

import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

BASE_URL = "http://localhost:3000"
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
STATE_FILE = os.path.join(LOGS_DIR, 'strategy_pids.json')

class RSIScaleInStrategy:
    """RSI 分批建仓策略类"""
    
    def __init__(self, symbol: str = "AVAXUSDT", leverage: int = 3, total_amount: float = 200):
        self.symbol = symbol
        self.leverage = leverage
        self.total_amount = total_amount
        
        # 分批建仓比例
        self.scale_in_ratios = [0.30, 0.50, 0.20]  # 30% / 50% / 20%
        self.current_scale_index = 0  # 当前建仓批次
        # 分批建仓金额
        self.scale_amounts = [
            self.total_amount * self.scale_in_ratios[0],  # 30%
            self.total_amount * self.scale_in_ratios[1],  # 50%
            self.total_amount * self.scale_in_ratios[2]   # 20%
        ]
        
        # RSI 参数
        self.rsi_period = 14
        self.rsi_buy_threshold = 50
        self.rsi_sell_threshold = 80
        
        # 止损参数
        self.strategy_stop_loss_pct = 0.005  # 0.5% 策略止损
        self.hard_stop_loss_pct = 0.05  # 5% 硬止损（执行引擎兜底）
        
        # 状态
        self.position = None  # 当前持仓
        self.is_running = False  # 运行状态
        self.entry_price = 0
        self.last_rsi = 0
        self.signal_rsi = None  # 信号 RSI（第一根 K 线的 RSI）
        self.waiting_confirmation = False  # 等待确认标志
        
        # 信号和成交追踪
        self.signals_sent = 0
        self.signals_executed = 0
        self.trades = []  # 成交记录
        
        # 止损单追踪
        self.stop_loss_id = None  # 止损单 ID
        
        # 计算各批次开仓金额（必须在 sync_with_exchange 之前）
        self.scale_amounts = [
            self.total_amount * self.scale_in_ratios[0],  # 60 USDT
            self.total_amount * self.scale_in_ratios[1],  # 100 USDT
            self.total_amount * self.scale_in_ratios[2]   # 40 USDT
        ]
        
        # 🛡️ 启动时强制同步交易所持仓
        print(f"🔍 启动时同步交易所持仓...")
        self.sync_with_exchange()
        
        # 🛡️ 如果有持仓但没有止损单，立即创建
        if self.position and not self.stop_loss_id:
            print(f"⚠️ 发现持仓但无止损单，立即创建...")
            time.sleep(5)
            self.create_stop_loss()
    
    def sync_with_exchange(self):
        """🛡️ 强制同步交易所持仓"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/positions",
                timeout=10
            )
            data = response.json()
            
            if data.get("success"):
                # ✅ 保存止损单 ID
                self.stop_loss_id = data.get("algo_id")
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
        
        print(f"📈 RSI 分批建仓策略初始化")
        print(f"  交易对：{self.symbol}")
        print(f"  杠杆：{self.leverage}x")
        print(f"  总保证金：{self.total_amount} USDT")
        print(f"  分批建仓：30% ({self.scale_amounts[0]:.0f}U) → 50% ({self.scale_amounts[1]:.0f}U) → 20% ({self.scale_amounts[2]:.0f}U)")
        print(f"  RSI 买入阈值：{self.rsi_buy_threshold}")
        print(f"  RSI 平仓阈值：{self.rsi_sell_threshold}")
        print(f"  策略止损：{self.strategy_stop_loss_pct*100}%")
        print(f"  硬止损：{self.hard_stop_loss_pct*100}%")
        
        # 同步结果
        if self.position:
            print(f"⚠️ 发现已有持仓：{self.position['size']} {self.symbol} @ {self.position['entry_price']}")
            print(f"   持仓价值：{self.position['size'] * self.position['entry_price']:.2f} USDT")
            print(f"   请手动处理或设置自动平仓")
        else:
            print(f"✅ 无已有持仓，可以正常启动")
        
        # 保存初始状态
        self.save_state()
    
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
                'scale_index': self.current_scale_index,
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
            
            if data.get("success"):
                # ✅ 保存止损单 ID
                self.stop_loss_id = data.get("algo_id")
                return data.get('klines', [])
            return []
        except Exception as e:
            print(f"❌ 获取 K 线失败：{e}")
            return []
    
    def calculate_rsi(self, klines: List[Dict]) -> float:
        """计算 RSI 指标"""
        if len(klines) < 15:
            return 50.0
        
        closes = [float(k['close']) for k in klines]
        
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
        
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def check_signal(self, rsi: float) -> str:
        """
        检查信号（2 根 K 线确认）
        
        逻辑:
        - T 时刻：RSI>50 → 记录信号，等待确认
        - T+1 时刻：RSI 仍然>50 → 执行开仓（分批）
        
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
                # 确认！执行开仓
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
    
    def get_current_position_value(self) -> float:
        """获取当前持仓价值"""
        try:
            response = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
            data = response.json()
            positions = data.get('positions', [])
            
            for pos in positions:
                if pos['symbol'] == self.symbol and pos['side'] == 'LONG':
                    return pos['size'] * pos['current_price']
            
            return 0
        except Exception as e:
            print(f"⚠️ 获取持仓失败：{e}")
            return 0
    
    def open_position(self):
        """分批开仓"""
        print(f"\n🚀 分批开仓信号")
        print(f"  RSI: {self.last_rsi:.2f}")
        print(f"  当前批次：{self.current_scale_index + 1}/{len(self.scale_in_ratios)}")
        
        # 检查是否已完成所有批次
        if self.current_scale_index >= len(self.scale_in_ratios):
            print(f"⚠️ 已完成所有分批建仓，跳过开仓")
            return False
        
        # 仓位控制：检查已用保证金
        max_position_value = self.total_amount * self.leverage * 1.05  # 允许最大金额（设置×105%）
        current_position_value = self.get_current_position_value()
        
        print(f"  当前持仓价值：{current_position_value:.2f} USDT")
        print(f"  允许最大仓位：{max_position_value:.2f} USDT")
        
        if current_position_value >= max_position_value:
            print(f"⚠️ 达到仓位上限，跳过开仓")
            return False
        
        # 计算本批次开仓金额和数量
        scale_amount = self.scale_amounts[self.current_scale_index]
        # 获取当前价格并计算数量，根据币种精度处理
        klines = self.get_klines()
        if not klines:
            print(f"❌ 无法获取 K 线数据，跳过开仓")
            return False
        current_price = float(klines[-1]['close'])
        # AVAXUSDT: stepSize=1 (整数), ETHUSDT: stepSize=0.001 (3 位小数)
        if self.symbol == "AVAXUSDT":
            quantity = int((scale_amount * self.leverage) / current_price)  # 整数
        else:
            quantity = round((scale_amount * self.leverage) / current_price, 3)  # 3 位小数
        
        print(f"  本批次开仓：{scale_amount:.0f} USDT × {self.leverage}x = {quantity:.4f} {self.symbol} @ ${current_price}")
        
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
                    'quantity': quantity,
                    'leverage': self.leverage
                },
                timeout=10
            )
            data = response.json()
            
            if data.get("success"):
                # ✅ 保存止损单 ID
                self.stop_loss_id = data.get("algo_id")
                order = data.get('order', {})
                self.entry_price = float(order.get('price', 0))
                self.position = 'LONG'
                self.signals_executed += 1
                
                # 记录成交
                self.trades.append({
                    'type': f'scale_in_{self.current_scale_index + 1}',
                    'price': self.entry_price,
                    'quantity': quantity,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'order_id': order.get('order_id', '-')
                })
                
                print(f"✅ 第{self.current_scale_index + 1}批开仓成功")
                print(f"  订单 ID: {order.get('order_id', '-')}")
                print(f"  入场价：{self.entry_price}")
                print(f"  信号：{self.signals_sent}/{self.signals_executed}")
                
                # 移动到下一批次
                self.current_scale_index += 1
                
                # 创建止损单
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
    
    def create_stop_loss(self):
        """🛡️ 创建止损单 (使用 Algo Order API + 精度处理 + 验证)"""
        if not self.position or self.entry_price <= 0:
            return
        
        stop_price = self.entry_price * (1 - self.strategy_stop_loss_pct)
        raw_quantity = self.total_amount * self.leverage / self.entry_price
        
        # 🛡️ 精度处理
        if self.symbol == "AVAXUSDT":
            quantity = int(raw_quantity)  # 整数
        else:
            quantity = round(raw_quantity, 3)  # 3 位小数
        
        print(f"\n🛡️ 创建止损单")
        print(f"  止损价：{stop_price} (策略止损 {self.strategy_stop_loss_pct*100}%)")
        print(f"  硬止损：{self.entry_price * (1 - self.hard_stop_loss_pct)} (5%)")
        print(f"  数量：{quantity} {self.symbol}")
        
        try:
            # 🛡️ 使用 Algo Order API
            response = requests.post(
                f"{BASE_URL}/api/binance/stop-loss",
                json={
                    'symbol': self.symbol,
                    'side': 'SELL',
                    'trigger_price': stop_price,
                    'quantity': quantity,
                    'algo_type': 'CONDITIONAL',  # ← 条件订单
                    'order_type': 'STOP_MARKET'
                },
                timeout=10
            )
            data = response.json()
            
            # 🛡️ 验证创建结果
            if data.get("success"):
                # ✅ 保存止损单 ID
                self.stop_loss_id = data.get("algo_id")
                self.stop_loss_id = data.get('data', {}).get('algoId')
                print(f"✅ 止损单创建成功 (ID: {self.stop_loss_id})")
                
                # 🛡️ 5 秒后验证是否生效
                self.verify_stop_loss()
            else:
                error_msg = data.get('error', 'Unknown error')
                print(f"❌ 止损单创建失败：{error_msg}")
                
                # 🛡️ 失败后强制平仓
                print(f"⚠️ 止损单创建失败，触发强制平仓")
                self.force_close_position()
        except Exception as e:
            print(f"❌ 止损单异常：{e}")
    
    def verify_stop_loss(self):
        """🛡️ 验证止损单是否生效"""
        import time
        time.sleep(5)  # 等待 5 秒
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/stop-loss/list",
                params={'symbol': self.symbol},
                timeout=10
            )
            data = response.json()
            
            if data.get("success"):
                # ✅ 保存止损单 ID
                self.stop_loss_id = data.get("algo_id")
                orders = data.get('orders', [])
                
                # 检查我们的止损单是否存在
                for order in orders:
                    if order.get('algo_id') == self.stop_loss_id:
                        print(f"✅ 止损单验证成功 (状态：{order.get('status')})")
                        return True
                
                print(f"⚠️ 止损单未找到，重新创建")
                return self.create_stop_loss()  # 递归重试
            else:
                print(f"⚠️ 验证失败：{data.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"⚠️ 验证异常：{e}")
            return False
    
    def force_close_position(self):
        """🛡️ 强制平仓 (止损单失败时的兜底)"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/order/close",
                json={
                    'symbol': self.symbol,
                    'order_type': 'MARKET'
                },
                timeout=10
            )
            data = response.json()
            
            if data.get("success"):
                # ✅ 保存止损单 ID
                self.stop_loss_id = data.get("algo_id")
                print(f"✅ 强制平仓成功")
                self.position = None
                self.entry_price = 0
                self.stop_loss_id = None
            else:
                print(f"❌ 强制平仓失败：{data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ 强制平仓异常：{e}")
    
    def close_position(self):
        """全部平仓"""
        if not self.position:
            return
        
        print(f"\n📉 平仓信号")
        print(f"  RSI: {self.last_rsi:.2f}")
        print(f"  入场价：{self.entry_price}")
        
        # 取消止损单
        self.cancel_stop_loss()
        
        # 获取当前持仓数量
        try:
            response = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
            data = response.json()
            positions = data.get('positions', [])
            
            quantity = 0
            for pos in positions:
                if pos['symbol'] == self.symbol and pos['side'] == 'LONG':
                    quantity = pos['size']
                    break
            
            if quantity == 0:
                print(f"⚠️ 无持仓，跳过平仓")
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
            
            if data.get("success"):
                # ✅ 保存止损单 ID
                self.stop_loss_id = data.get("algo_id")
                order = data.get('order', {})
                exit_price = float(order.get('price', 0))
                pnl = (exit_price - self.entry_price) * (self.total_amount * self.leverage / self.entry_price)
                
                # 记录成交
                self.trades.append({
                    'type': 'close_all',
                    'price': exit_price,
                    'pnl': pnl,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'order_id': order.get('order_id', '-')
                })
                
                print(f"✅ 全部平仓成功")
                print(f"  出场价：{exit_price}")
                print(f"  盈亏：{pnl:.2f} USDT")
                print(f"  信号：{self.signals_sent}/{self.signals_executed}")
                
                self.position = None
                self.entry_price = 0
                self.current_scale_index = 0  # 重置批次
                
                # 保存状态
                self.save_state()
                
                return True
            else:
                print(f"❌ 平仓失败：{data}")
                return False
        except Exception as e:
            print(f"❌ 平仓异常：{e}")
            return False
    
    def cancel_stop_loss(self):
        """取消止损单"""
        print(f"\n❌ 取消止损单")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/stop-loss/cancel",
                json={
                    'symbol': self.symbol
                },
                timeout=10
            )
            data = response.json()
            
            if data.get("success"):
                # ✅ 保存止损单 ID
                self.stop_loss_id = data.get("algo_id")
                print(f"✅ 止损单取消成功")
            else:
                print(f"❌ 止损单取消失败：{data}")
        except Exception as e:
            print(f"❌ 止损单取消异常：{e}")
    
    def run(self, interval: int = 60):
        """运行策略"""
        print(f"\n{'='*60}")
        print(f"🚀 RSI 分批建仓策略启动")
        print(f"{'='*60}")
        
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
                
                # 5% 硬止损检查（执行引擎兜底）
                if self.position == 'LONG' and self.entry_price > 0:
                    current_price = float(klines[-1]['close'])
                    loss_pct = (current_price - self.entry_price) / self.entry_price
                    
                    # 策略止损优先级更高
                    if loss_pct <= -self.strategy_stop_loss_pct:
                        print(f"\n🛑 触发策略止损：{loss_pct*100:.2f}%")
                        self.close_position()
                        time.sleep(60)
                        continue
                    
                    # 硬止损兜底
                    elif loss_pct <= -self.hard_stop_loss_pct:
                        print(f"\n🛑 触发硬止损：{loss_pct*100:.2f}%")
                        self.close_position()
                        time.sleep(60)
                        continue
                
                # 检查信号（2 根 K 线确认）
                signal = self.check_signal(rsi)
                
                if signal == 'wait':
                    print(f"\n📊 RSI: {rsi:.2f} (等待确认...)")
                elif signal == 'buy':
                    print(f"\n📊 RSI: {rsi:.2f} (确认！)")
                    # 分批开仓逻辑
                    self.open_position()
                elif signal == 'sell':
                    print(f"\n📊 RSI: {rsi:.2f} (平仓信号！)")
                    # 全部平仓逻辑
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
                if self.position:
                    self.close_position()
                break
            except Exception as e:
                print(f"❌ 策略异常：{e}")
                time.sleep(60)


if __name__ == "__main__":
    # 创建策略实例
    strategy = RSIScaleInStrategy(
        symbol='AVAXUSDT',
        leverage=3,
        total_amount=200
    )
    
    # 手动设置止损比例
    strategy.stop_loss_pct = 0.005  # 0.5% 策略止损
    
    # 运行策略（循环调用，每根 K 线检查信号）
    strategy.run(interval=60)  # 60 秒=1 分钟 K 线
