#!/usr/bin/env python3
"""
🦞 Auto Sim 策略执行器
负责 auto_sim 策略的定时执行（开仓→加仓→平仓循环）
"""

from api.binance_client import BinanceClient
from auto_trading_sim import AutoTradingSimulator
import time

# API 配置
API_KEY = {
    'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
    'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
}

class AutoSimExecutor:
    """Auto Sim 策略执行器"""
    
    def __init__(self):
        self.simulators = {}  # {symbol: simulator}
        self.client = BinanceClient(API_KEY['api_key'], API_KEY['secret_key'], testnet=True)
    
    def start_strategy(self, symbol: str, leverage: int, trade_amount: float):
        """启动策略"""
        simulator = AutoTradingSimulator(
            symbol=symbol,
            initial_capital=trade_amount * leverage
        )
        simulator.update_params(leverage=leverage, trade_amount=trade_amount)
        self.simulators[symbol] = simulator
        print(f"🚀 Auto Sim 策略已启动：{symbol}, 杠杆：{leverage}x, 金额：${trade_amount}")
    
    def stop_strategy(self, symbol: str):
        """停止策略"""
        if symbol in self.simulators:
            del self.simulators[symbol]
            print(f"⏹️ Auto Sim 策略已停止：{symbol}")
    
    def execute_cycle(self, symbol: str, current_price: float):
        """执行一个循环"""
        if symbol not in self.simulators:
            print(f"⚠️ 策略未启动：{symbol}")
            return
        
        simulator = self.simulators[symbol]
        signal = simulator.generate_signal(current_price)
        
        if not signal:
            return
        
        # 根据信号执行
        action = signal.get('action')
        type_ = signal.get('type')
        size = signal.get('size')
        
        print(f"📊 执行信号：{symbol} {action} {type_} {size} @ ${current_price}")
        
        try:
            if action == 'BUY':
                # 开仓或加仓
                if type_ == 'OPEN':
                    # 开仓
                    order_result = self.client.place_futures_order(
                        symbol=symbol,
                        side='BUY',
                        order_type='MARKET',
                        quantity=size
                    )
                    if order_result.get('success'):
                        print(f"✅ 开仓成功：{symbol} BUY {size} @ ${current_price}")
                        
                        # 设置止损单
                        stop_price = current_price * 0.95  # 5% 止损
                        self.client.place_stop_loss_order(
                            symbol=symbol,
                            side='SELL',
                            quantity=size,
                            stop_price=stop_price,
                            reduce_only=True
                        )
                        print(f"✅ 止损单已设置：{stop_price}")
                
                elif type_ == 'ADD':
                    # 加仓
                    order_result = self.client.place_futures_order(
                        symbol=symbol,
                        side='BUY',
                        order_type='MARKET',
                        quantity=size
                    )
                    if order_result.get('success'):
                        print(f"✅ 加仓成功：{symbol} BUY {size} @ ${current_price}")
            
            elif action == 'SELL':
                # 平仓
                if type_ == 'CLOSE':
                    # 先获取当前持仓
                    positions = self.client.get_futures_positions()
                    quantity = size  # 使用信号中的数量
                    
                    for pos in positions.get('positions', []):
                        if pos['symbol'] == symbol and pos['size'] > 0:
                            quantity = pos['size']
                            break
                    
                    order_result = self.client.place_futures_order(
                        symbol=symbol,
                        side='SELL',
                        order_type='MARKET',
                        quantity=quantity,
                        reduce_only=True
                    )
                    
                    if order_result.get('success'):
                        print(f"✅ 平仓成功：{symbol} SELL {quantity} @ ${current_price}")
                        
                        # 取消所有止损单
                        algo_orders = self.client.get_algo_orders(symbol=symbol, limit=10)
                        if algo_orders.get('success'):
                            for order in algo_orders.get('orders', []):
                                if order.get('algoStatus') == 'NEW':
                                    self.client.cancel_algo_order(symbol, order['algoId'])
                                    print(f"✅ 止损单已取消：Algo ID {order['algoId']}")
        
        except Exception as e:
            print(f"❌ 执行失败：{e}")
    
    def get_status(self, symbol: str):
        """获取策略状态"""
        if symbol not in self.simulators:
            return {'active': False}
        
        simulator = self.simulators[symbol]
        return {
            'active': True,
            'cycle_count': simulator.cycle_count,
            'next_step': simulator.get_status().get('next_step', 'Unknown')
        }


# 全局执行器实例
auto_sim_executor = AutoSimExecutor()
