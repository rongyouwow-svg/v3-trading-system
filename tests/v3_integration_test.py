#!/usr/bin/env python3
"""
🧪 v3 系统完整集成测试

测试流程:
1. 检查系统状态
2. 获取账户余额
3. 获取当前持仓
4. 获取 K 线数据
5. 计算 RSI 指标
6. 模拟交易信号
7. 创建订单（开仓）
8. 创建止损单
9. 查询订单状态
10. 平仓
11. 查询交易记录
12. 生成测试报告
"""

import requests
import time
from datetime import datetime
from typing import Dict, List

BASE_URL = "http://localhost:3000"

class V3IntegrationTest:
    """v3 系统集成测试类"""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        
    def log(self, message: str, success: bool = True):
        """记录测试结果"""
        status = "✅" if success else "❌"
        print(f"{status} {message}")
        self.results.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'message': message,
            'success': success
        })
    
    def test_api_health(self):
        """1. 检查 API 健康状态"""
        print("\n" + "="*60)
        print("📋 测试 1: API 健康检查")
        print("="*60)
        
        try:
            response = requests.get(f"{BASE_URL}/api/strategy/active", timeout=10)
            data = response.json()
            
            if data.get('success'):
                count = data.get('count', 0)
                self.log(f"策略 API 正常，当前活跃策略：{count} 个")
                return True
            else:
                self.log("策略 API 返回失败", False)
                return False
        except Exception as e:
            self.log(f"策略 API 异常：{e}", False)
            return False
    
    def test_account_balance(self):
        """2. 获取账户余额"""
        print("\n" + "="*60)
        print("📋 测试 2: 账户余额查询")
        print("="*60)
        
        try:
            response = requests.get(f"{BASE_URL}/api/binance/account-info", timeout=10)
            data = response.json()
            
            if data.get('success'):
                account = data.get('account', {})
                balance = account.get('balance', 0)
                available = account.get('available', 0)
                self.log(f"账户余额：{balance:.2f} USDT (可用：{available:.2f})")
                return True
            else:
                self.log(f"账户查询失败：{data}", False)
                return False
        except Exception as e:
            self.log(f"账户查询异常：{e}", False)
            return False
    
    def test_positions(self):
        """3. 获取当前持仓"""
        print("\n" + "="*60)
        print("📋 测试 3: 持仓查询")
        print("="*60)
        
        try:
            response = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
            data = response.json()
            
            positions = data.get('positions', [])
            if positions:
                for pos in positions:
                    self.log(f"持仓：{pos['symbol']} {pos['side']} {pos['size']} @ {pos['entry_price']}")
            else:
                self.log("当前无持仓")
            return True
        except Exception as e:
            self.log(f"持仓查询异常：{e}", False)
            return False
    
    def test_klines(self):
        """4. 获取 K 线数据"""
        print("\n" + "="*60)
        print("📋 测试 4: K 线数据查询")
        print("="*60)
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/klines",
                params={'symbol': 'ETHUSDT', 'interval': '1m', 'limit': 50},
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                klines = data.get('klines', [])
                self.log(f"获取 K 线成功：{len(klines)} 条")
                if klines:
                    latest = klines[-1]
                    self.log(f"最新 K 线：{latest.get('time', latest.get('close_time', 'N/A'))} 开盘:{latest['open']} 收盘:{latest['close']}")
                return True
            else:
                self.log(f"K 线查询失败：{data}", False)
                return False
        except Exception as e:
            self.log(f"K 线查询异常：{e}", False)
            return False
    
    def test_rsi_calculation(self):
        """5. 计算 RSI 指标"""
        print("\n" + "="*60)
        print("📋 测试 5: RSI 指标计算")
        print("="*60)
        
        try:
            # 先获取 K 线
            response = requests.get(
                f"{BASE_URL}/api/binance/klines",
                params={'symbol': 'ETHUSDT', 'interval': '1m', 'limit': 50},
                timeout=10
            )
            klines_data = response.json()
            
            if not klines_data.get('success'):
                self.log("获取 K 线失败", False)
                return False
            
            klines = klines_data.get('klines', [])
            
            # 计算 RSI
            closes = [float(k['close']) for k in klines]
            
            if len(closes) < 15:
                self.log("K 线数据不足，无法计算 RSI", False)
                return False
            
            # RSI 计算
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
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            self.log(f"RSI(14) 计算成功：{rsi:.2f}")
            
            # 判断信号
            if rsi > 50:
                self.log(f"RSI > 50，满足开多条件（等待确认）")
            elif rsi > 80:
                self.log(f"RSI > 80，满足平仓条件")
            else:
                self.log(f"RSI < 50，观望中")
            
            return True
        except Exception as e:
            self.log(f"RSI 计算异常：{e}", False)
            return False
    
    def test_stop_loss_api(self):
        """6. 测试止损单 API"""
        print("\n" + "="*60)
        print("📋 测试 6: 止损单 API 查询")
        print("="*60)
        
        try:
            response = requests.get(f"{BASE_URL}/api/binance/stop-loss", timeout=10)
            data = response.json()
            
            if data.get('success'):
                orders = data.get('orders', [])
                self.log(f"止损单查询成功，当前止损单：{len(orders)} 个")
                return True
            else:
                self.log(f"止损单查询失败：{data}", False)
                return False
        except Exception as e:
            self.log(f"止损单查询异常：{e}", False)
            return False
    
    def test_trades_history(self):
        """7. 查询交易记录"""
        print("\n" + "="*60)
        print("📋 测试 7: 交易记录查询")
        print("="*60)
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/binance/trades",
                params={'limit': 10},
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                trades = data.get('trades', [])
                self.log(f"交易记录查询成功，最近 {len(trades)} 条")
                
                for trade in trades[:3]:
                    order_type = trade.get('order_type', 'UNKNOWN')
                    self.log(f"  - {trade['trade_time']}: {trade['symbol']} {trade['side']} {order_type} @ {trade['price']}")
                
                return True
            else:
                self.log(f"交易记录查询失败：{data}", False)
                return False
        except Exception as e:
            self.log(f"交易记录查询异常：{e}", False)
            return False
    
    def test_strategy_status(self):
        """8. 查询策略状态"""
        print("\n" + "="*60)
        print("📋 测试 8: 策略状态查询")
        print("="*60)
        
        try:
            response = requests.get(f"{BASE_URL}/api/strategy/active", timeout=10)
            data = response.json()
            
            if data.get('success'):
                strategies = data.get('active_strategies', [])
                self.log(f"策略状态查询成功，活跃策略：{len(strategies)} 个")
                
                for s in strategies:
                    self.log(f"  - {s['symbol']}: RSI={s['rsi']:.2f}, 持仓={s['position'] or '无'}")
                
                return True
            else:
                self.log(f"策略状态查询失败：{data}", False)
                return False
        except Exception as e:
            self.log(f"策略状态查询异常：{e}", False)
            return False
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed
        
        print(f"\n总测试数：{total}")
        print(f"✅ 通过：{passed}")
        print(f"❌ 失败：{failed}")
        print(f"通过率：{passed/total*100:.1f}%")
        
        print("\n详细结果:")
        for r in self.results:
            status = "✅" if r['success'] else "❌"
            print(f"  [{r['time']}] {status} {r['message']}")
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        print(f"\n测试耗时：{duration:.2f} 秒")
        
        if failed == 0:
            print("\n🎉 所有测试通过！v3 系统运行正常！")
        else:
            print(f"\n⚠️ {failed} 个测试失败，请检查系统！")
        
        return failed == 0
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("🧪 v3 系统完整集成测试")
        print(f"开始时间：{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        self.test_api_health()
        self.test_account_balance()
        self.test_positions()
        self.test_klines()
        self.test_rsi_calculation()
        self.test_stop_loss_api()
        self.test_trades_history()
        self.test_strategy_status()
        
        return self.generate_report()


if __name__ == "__main__":
    tester = V3IntegrationTest()
    success = tester.run_all_tests()
    
    # 返回退出码
    exit(0 if success else 1)
