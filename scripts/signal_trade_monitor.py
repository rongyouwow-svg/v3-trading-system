#!/usr/bin/env python3
"""
📊 v3 策略信号与成交对比监控

实时监控策略信号和实际成交，验证策略执行准确性
"""

import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:3000"
LOGS_DIR = "/home/admin/.openclaw/workspace/quant/v3-architecture/logs"
MONITOR_FILE = os.path.join(LOGS_DIR, "signal_trade_monitor.json")

class SignalTradeMonitor:
    def __init__(self):
        self.signals = []
        self.trades = []
        self.last_signals = {}
        self.start_time = datetime.now()
        
    def get_strategy_status(self):
        try:
            resp = requests.get(f"{BASE_URL}/api/strategy/active", timeout=10)
            return resp.json()
        except:
            return None
    
    def get_trades(self):
        try:
            resp = requests.get(f"{BASE_URL}/api/binance/trades?limit=20", timeout=10)
            return resp.json()
        except:
            return None
    
    def get_positions(self):
        try:
            resp = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
            return resp.json()
        except:
            return None
    
    def monitor(self):
        print("="*70)
        print("📊 v3 策略信号与成交对比监控")
        print("="*70)
        print(f"开始时间：{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"监控目标：ETHUSDT, LINKUSDT, AVAXUSDT")
        print(f"刷新频率：30 秒")
        print("="*70)
        print("")
        
        while True:
            try:
                # 获取策略状态
                strategy_data = self.get_strategy_status()
                trades_data = self.get_trades()
                positions_data = self.get_positions()
                
                if not strategy_data or not strategy_data.get('success'):
                    print(f"⚠️ 无法获取策略状态")
                    time.sleep(10)
                    continue
                
                print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')} - 策略状态更新")
                print("-"*70)
                
                # 检查每个策略
                for s in strategy_data.get('active_strategies', []):
                    symbol = s['symbol']
                    rsi = s.get('rsi', 0)
                    position = s.get('position')
                    signals_sent = s.get('signals_sent', 0)
                    signals_executed = s.get('signals_executed', 0)
                    stable_count = s.get('stable_count', 0)
                    
                    print(f"\n{symbol}:")
                    print(f"  RSI: {rsi:.2f} (稳定计数：{stable_count})")
                    print(f"  持仓：{position or '无'}")
                    print(f"  信号：{signals_sent} 发送 / {signals_executed} 执行")
                    
                    # 检测新信号
                    if symbol not in self.last_signals:
                        self.last_signals[symbol] = {'sent': 0, 'executed': 0}
                    
                    if signals_sent > self.last_signals[symbol]['sent']:
                        signal_time = datetime.now()
                        print(f"  📡 [{signal_time.strftime('%H:%M:%S')}] 发出开仓信号 #{signals_sent}")
                        
                        self.signals.append({
                            'time': signal_time.isoformat(),
                            'symbol': symbol,
                            'signal_id': signals_sent,
                            'rsi': rsi,
                            'position': position
                        })
                    
                    if signals_executed > self.last_signals[symbol]['executed']:
                        trade_time = datetime.now()
                        print(f"  ✅ [{trade_time.strftime('%H:%M:%S')}] 执行成交 #{signals_executed}")
                        
                        self.trades.append({
                            'time': trade_time.isoformat(),
                            'symbol': symbol,
                            'trade_id': signals_executed
                        })
                    
                    self.last_signals[symbol] = {'sent': signals_sent, 'executed': signals_executed}
                
                # 显示最新成交
                if trades_data and trades_data.get('success'):
                    trades = trades_data.get('trades', [])
                    if trades:
                        print(f"\n💹 最新成交:")
                        for t in trades[:3]:
                            print(f"  {t.get('trade_time', 'N/A')}: {t['symbol']} {t['side']} {t.get('order_type', '')} @ {t['price']}")
                
                # 显示持仓
                if positions_data and positions_data.get('success'):
                    positions = positions_data.get('positions', [])
                    if positions:
                        print(f"\n📈 当前持仓:")
                        for pos in positions:
                            pnl = pos.get('unrealized_pnl', 0)
                            pnl_pct = pos.get('unrealized_pnl_pct', 0)
                            print(f"  {pos['symbol']} {pos['side']} {pos['size']} @ {pos['entry_price']} (盈亏：{pnl:.2f} USDT, {pnl_pct:.2f}%)")
                    else:
                        print(f"\n📈 当前持仓：空仓")
                
                # 对比统计
                print(f"\n📊 信号与成交对比统计:")
                total_signals = sum(s.get('signals_sent', 0) for s in strategy_data.get('active_strategies', []))
                total_executed = sum(s.get('signals_executed', 0) for s in strategy_data.get('active_strategies', []))
                actual_trades = len(trades_data.get('trades', [])) if trades_data else 0
                
                print(f"  总信号数：{total_signals}")
                print(f"  总执行数：{total_executed}")
                print(f"  实际成交：{actual_trades}")
                print(f"  监控记录：{len(self.signals)} 信号 / {len(self.trades)} 成交")
                
                # 保存监控数据
                self.save_monitor_data()
                
                # 等待下次刷新
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n\n🛑 监控已停止")
                self.save_monitor_data()
                break
            except Exception as e:
                print(f"\n❌ 错误：{e}")
                time.sleep(10)
    
    def save_monitor_data(self):
        data = {
            'start_time': self.start_time.isoformat(),
            'last_update': datetime.now().isoformat(),
            'signals': self.signals[-50:],  # 保留最近 50 条
            'trades': self.trades[-50:],
            'last_signals': self.last_signals
        }
        
        with open(MONITOR_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    monitor = SignalTradeMonitor()
    monitor.monitor()
