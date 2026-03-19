#!/usr/bin/env python3
"""
📈 v23 ETH 实盘策略（测试网）

策略逻辑:
- RSI < 18 + 布林带下轨 + 成交量>3 倍 → 开多
- RSI > 80 → 平仓
- 止损：1%
- 止盈：2%
- K 线完成确定指标数值
- 1 分钟后稳定在数值标准，执行操作

参数:
- 交易对：ETHUSDT
- 杠杆：3x
- 保证金：100 USDT（测试网）
"""

import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

BASE_URL = "http://localhost:3000"
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
STATE_FILE = os.path.join(LOGS_DIR, 'v23_eth_state.json')

class V23EthStrategy:
    """v23 ETH 实盘策略"""
    
    def __init__(self, symbol: str = "ETHUSDT", leverage: int = 3, amount: float = 100):
        self.symbol = symbol
        self.leverage = leverage
        self.amount = amount
        
        # RSI 参数
        self.rsi_period = 7
        self.rsi_buy_threshold = 18
        self.rsi_sell_threshold = 80
        
        # 止损止盈参数
        self.stop_loss_pct = 0.01  # 1% 止损
        self.take_profit_pct = 0.02  # 2% 止盈
        
        # 设置交易所杠杆
        self.set_leverage()
        
        # 状态
        self.position = None
        self.entry_price = 0
        self.last_rsi = 0
        self.signal_rsi = None
        self.waiting_confirmation = False
        self.is_running = False
        
        # 信号和成交追踪
        self.signals_sent = 0
        self.signals_executed = 0
        self.trades = []
        
        # 止损单追踪
        self.stop_loss_id = None
        
        # 止损限制
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.today = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📈 v23 ETH 实盘策略初始化")
        print(f"  交易对：{symbol}")
        print(f"  杠杆：{leverage}x")
        print(f"  保证金：{amount} USDT")
        print(f"  RSI 买入阈值：{self.rsi_buy_threshold}")
        print(f"  RSI 平仓阈值：{self.rsi_sell_threshold}")
        print(f"  止损：{self.stop_loss_pct*100}%")
        print(f"  止盈：{self.take_profit_pct*100}%")
        
        # 设置交易所杠杆
        self.set_leverage()
        
        # 启动时同步持仓
        print(f"🔍 启动时同步交易所持仓...")
        self.sync_with_exchange()
        
        # 保存初始状态
        self.save_state()
    
    def set_leverage(self):
        """设置交易所杠杆"""
        try:
            print(f"🔧 设置杠杆：{self.leverage}x...")
            response = requests.post(
                f"{BASE_URL}/api/binance/leverage",
                json={
                    'symbol': self.symbol,
                    'leverage': self.leverage
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                print(f"✅ 杠杆设置成功：{self.leverage}x")
            else:
                print(f"⚠️ 杠杆设置失败：{data.get('error')}")
        except Exception as e:
            print(f"⚠️ 杠杆设置异常：{e}")
    
    def sync_with_exchange(self):
        """强制同步交易所持仓"""
        try:
            response = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
            data = response.json()
            
            if data.get('success'):
                positions = data.get('positions', [])
                
                for pos in positions:
                    if pos.get('symbol') == self.symbol:
                        size = float(pos.get('size', 0))
                        if size > 0:
                            self.position = pos
                            self.entry_price = float(pos.get('entry_price', 0))
                            print(f"✅ 同步持仓成功：{size} {self.symbol} @ ${self.entry_price}")
                            
                            # 检查止损单
                            self.check_existing_stop_loss()
                            return
                
                print(f"✅ 无已有持仓，可以正常启动")
            else:
                print(f"⚠️ 同步持仓失败：{data.get('error')}")
        except Exception as e:
            print(f"⚠️ 同步持仓异常：{e}")
    
    def check_existing_stop_loss(self):
        """检查已有止损单"""
        try:
            response = requests.get(f"{BASE_URL}/api/binance/stop-loss", timeout=10)
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
    
    def get_klines(self, interval: str = "15m", limit: int = 100):
        """获取 K 线数据"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/klines",
                params={'symbol': self.symbol, 'interval': interval, 'limit': limit},
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                return data.get('data', [])
            return None
        except Exception as e:
            print(f"❌ 获取 K 线异常：{e}")
            return None
    
    def calculate_rsi(self, prices, period=7):
        """计算 RSI"""
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def create_stop_loss(self, quantity: float):
        """创建止损单"""
        if not self.position:
            print(f"⚠️ 无持仓，跳过止损单创建")
            return False
        
        stop_price = round(self.entry_price * (1 - self.stop_loss_pct), 2)
        
        # 先取消旧止损单（如果有）
        if self.stop_loss_id:
            self.cancel_stop_loss()
        
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
                return True
            else:
                print(f"❌ 止损单创建失败：{data.get('error')}")
                return False
        except Exception as e:
            print(f"❌ 止损单创建异常：{e}")
            return False
    
    def cancel_stop_loss(self):
        """取消止损单"""
        if not self.stop_loss_id:
            return
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/binance/stop-loss/cancel",
                params={'symbol': self.symbol},
                json={'algo_id': self.stop_loss_id},
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                print(f"✅ 止损单已取消 (ID: {self.stop_loss_id})")
                self.stop_loss_id = None
        except Exception as e:
            print(f"⚠️ 取消止损单异常：{e}")
    
    def update_stop_loss(self, current_price: float):
        """移动止损：盈利 50% 后移动至成本价"""
        if not self.position or not self.stop_loss_id:
            return
        
        pnl_pct = (current_price - self.entry_price) / self.entry_price
        
        # 盈利 50% 后，移动止损至成本价
        if pnl_pct >= 0.01:  # 盈利 1%（止盈 2% 的一半）
            new_stop_price = round(self.entry_price * 1.002, 2)  # 成本价上方 0.2%
            current_stop = self.entry_price * (1 - self.stop_loss_pct)
            
            if new_stop_price > current_stop:
                print(f"\n📈 盈利达标，移动止损至 ${new_stop_price:.2f}")
                self.create_stop_loss(self.position['size'])
    
    def check_stop_loss_status(self):
        """检查止损单状态"""
        if not self.stop_loss_id:
            return
        
        try:
            response = requests.get(f"{BASE_URL}/api/binance/stop-loss", timeout=10)
            data = response.json()
            
            if data.get('success'):
                orders = data.get('orders', [])
                found = False
                
                for order in orders:
                    if order.get('algo_id') == self.stop_loss_id:
                        found = True
                        status = order.get('status')
                        
                        if status == 'FILLED':
                            print(f"✅ 止损单已触发")
                            self.position = None
                            self.stop_loss_id = None
                        elif status == 'CANCELED':
                            print(f"⚠️ 止损单已取消")
                            self.stop_loss_id = None
                        elif status == 'EXPIRED':
                            print(f"⚠️ 止损单已过期")
                            self.stop_loss_id = None
                        else:
                            print(f"📊 止损单状态：{status}")
                
                if not found:
                    print(f"⚠️ 止损单未找到，可能需要重新创建")
                    self.stop_loss_id = None
        except Exception as e:
            print(f"⚠️ 检查止损单状态异常：{e}")
    
    def close_position(self, reason: str = ""):
        """平仓"""
        if not self.position:
            print(f"⚠️ 无持仓，跳过平仓")
            return False
        
        try:
            side = 'SELL' if self.position['side'] == 'LONG' else 'BUY'
            
            response = requests.post(
                f"{BASE_URL}/api/binance/order",
                json={
                    'symbol': self.symbol,
                    'side': side,
                    'type': 'MARKET',
                    'quantity': self.position['size']
                },
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                pnl = self.position['size'] * (self.position['current_price'] - self.entry_price)
                
                self.trades.append({
                    'timestamp': datetime.now().isoformat(),
                    'symbol': self.symbol,
                    'side': 'CLOSE',
                    'reason': reason,
                    'pnl': pnl
                })
                
                print(f"✅ 平仓成功 ({reason}, 盈亏：{pnl:.2f} USDT)")
                
                # 更新盈亏
                self.daily_pnl += pnl
                self.total_pnl += pnl
                
                # 取消止损单
                self.cancel_stop_loss()
                
                # 重置状态
                self.position = None
                self.entry_price = 0
                self.stop_loss_id = None
                
                # 保存状态
                self.save_state()
                
                return True
            else:
                print(f"❌ 平仓失败：{data.get('error')}")
                return False
        except Exception as e:
            print(f"❌ 平仓异常：{e}")
            return False
    
    def open_position(self, price: float, quantity: float):
        """开仓"""
        try:
            print(f"\n📈 开仓信号")
            print(f"   价格：${price:.2f}")
            print(f"   数量：{quantity}")
            print(f"   仓位：{self.amount} USDT")
            print(f"   杠杆：{self.leverage}x")
            
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
                    'entry_price': price,
                    'current_price': price
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
                    'amount': self.amount
                })
                
                # 保存状态
                self.save_state()
                
                return True
            else:
                print(f"❌ 开仓失败：{data.get('error')}")
                return False
        except Exception as e:
            print(f"❌ 开仓异常：{e}")
            return False
    
    def save_state(self):
        """保存状态"""
        try:
            os.makedirs(LOGS_DIR, exist_ok=True)
            
            state = {
                'symbol': self.symbol,
                'position': self.position,
                'entry_price': self.entry_price,
                'stop_loss_id': self.stop_loss_id,
                'signals_sent': self.signals_sent,
                'signals_executed': self.signals_executed,
                'trades': self.trades,
                'daily_pnl': self.daily_pnl,
                'total_pnl': self.total_pnl,
                'today': self.today,
                'last_update': datetime.now().isoformat()
            }
            
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️ 保存状态异常：{e}")
    
    def load_state(self):
        """加载状态"""
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                self.daily_pnl = state.get('daily_pnl', 0.0)
                self.total_pnl = state.get('total_pnl', 0.0)
                self.today = state.get('today', '')
                
                # 检查是否新的一天
                if self.today != datetime.now().strftime('%Y-%m-%d'):
                    self.daily_pnl = 0.0
                    self.today = datetime.now().strftime('%Y-%m-%d')
        except:
            pass
    
    def run(self, interval: int = 60):
        """运行策略"""
        self.is_running = True
        self.load_state()
        
        print(f"\n🚀 v23 ETH 实盘策略启动")
        print(f"   检查间隔：{interval}秒")
        print(f"   止损限制：单笔 1% / 每日 3% / 总计 20%")
        print(f"="*70)
        
        while self.is_running:
            try:
                # 检查止损限制
                if self.daily_pnl <= -300:  # 每日止损 3% (假设本金 10000)
                    print(f"\n🚨 触发每日止损限制！今日亏损：{self.daily_pnl:.2f} USDT")
                    self.close_position('每日止损')
                    self.is_running = False
                    break
                
                if self.total_pnl <= -2000:  # 总止损 20%
                    print(f"\n🚨 触发总止损限制！总亏损：{self.total_pnl:.2f} USDT")
                    self.close_position('总止损')
                    self.is_running = False
                    break
                
                # 获取 K 线
                klines = self.get_klines(interval="15m", limit=100)
                if not klines or len(klines) < 20:
                    print(f"⚠️ K 线数据不足，跳过")
                    time.sleep(interval)
                    continue
                
                # 提取收盘价
                closes = [float(k[4]) for k in klines]
                volumes = [float(k[5]) for k in klines]
                
                # 计算 RSI
                rsi = self.calculate_rsi(closes, self.rsi_period)
                self.last_rsi = rsi
                
                # 计算成交量比率
                vol_ma = sum(volumes[-20:]) / 20
                vol_ratio = volumes[-1] / vol_ma if vol_ma > 0 else 1
                
                print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   价格：${closes[-1]:.2f}")
                print(f"   RSI: {rsi:.1f}")
                print(f"   成交量比率：{vol_ratio:.2f}")
                
                # 检查平仓信号
                if self.position:
                    pnl_pct = (closes[-1] - self.entry_price) / self.entry_price * 100
                    
                    # 移动止损（盈利 50% 后）
                    self.update_stop_loss(closes[-1])
                    
                    # 止盈
                    if pnl_pct >= self.take_profit_pct * 100:
                        print(f"\n✅ RSI 止盈 ({pnl_pct:.1f}%)，平仓")
                        self.close_position('止盈')
                    
                    # 止损（由止损单自动执行，这里只记录）
                    elif pnl_pct <= -self.stop_loss_pct * 100:
                        print(f"\n⚠️ 触发止损 ({pnl_pct:.1f}%)")
                    
                    # 每 5 分钟检查止损单状态
                    if int(time.time()) % 300 == 0:
                        self.check_stop_loss_status()
                
                # 检查开仓信号
                elif not self.position:
                    # v23 信号：RSI<18 + 布林带下轨 + 成交量>3 倍
                    if rsi < self.rsi_buy_threshold and vol_ratio > 3.0:
                        print(f"\n🎯 v23 开仓信号!")
                        print(f"   RSI: {rsi:.1f} < {self.rsi_buy_threshold}")
                        print(f"   成交量：{vol_ratio:.2f}x > 3.0")
                        
                        # 计算开仓数量
                        quantity = (self.amount * self.leverage) / closes[-1]
                        quantity = round(quantity, 3)  # ETH 精度 3 位小数
                        
                        # 开仓
                        self.open_position(closes[-1], quantity)
                
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


def main():
    """主函数"""
    print("="*70)
    print("📈 v23 ETH 实盘策略（测试网）")
    print("="*70)
    
    strategy = V23EthStrategy(
        symbol="ETHUSDT",
        leverage=3,
        amount=100
    )
    
    strategy.run(interval=60)


if __name__ == '__main__':
    main()
