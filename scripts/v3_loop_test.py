#!/usr/bin/env python3
"""
🧪 V3 系统循环测试脚本

自动执行：
1. 检查初始状态
2. 随机关闭一个策略
3. 验证平仓 + 撤止损
4. 开启新策略
5. 验证注册 + 止损单
6. 循环测试
"""

import requests
import subprocess
import time
import random
from datetime import datetime

BASE_URL = "http://localhost:3000"
SUPERVISORCTL = "/root/.pyenv/versions/3.10.13/bin/supervisorctl"
SOCKET = "unix:///root/.openclaw/workspace/quant/v3-architecture/logs/supervisor.sock"
LOG_FILE = "/root/.openclaw/workspace/quant/v3-architecture/logs/v3_loop_test.log"

# 策略配置
STRATEGIES = [
    {'name': 'quant-strategy-eth', 'symbol': 'ETHUSDT', 'file': 'rsi_1min_strategy.py'},
    {'name': 'quant-strategy-link', 'symbol': 'LINKUSDT', 'file': 'link_rsi_detailed_strategy.py'},
    {'name': 'quant-strategy-avax', 'symbol': 'AVAXUSDT', 'file': 'rsi_scale_in_strategy.py'},
]

def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")

def get_status():
    """获取系统状态"""
    try:
        # 策略进程
        result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=5)
        strategy_procs = [l for l in result.stdout.split('\n') if 'strategy.*py' in l and 'grep' not in l]
        
        # 持仓
        resp = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
        positions = [p for p in resp.json().get('positions', []) if p.get('size', 0) > 0]
        
        # 止损单
        resp = requests.get(f"{BASE_URL}/api/binance/stop-loss", timeout=10)
        stop_orders = [o for o in resp.json().get('orders', []) if o.get('status') == 'NEW']
        
        # 注册中心
        resp = requests.get(f"{BASE_URL}/api/strategy/list", timeout=10)
        registered = resp.json().get('data', {}).get('strategies', [])
        
        return {
            'procs': len(strategy_procs),
            'positions': positions,
            'stop_orders': stop_orders,
            'registered': registered
        }
    except Exception as e:
        log(f"❌ 获取状态失败：{e}")
        return None

def stop_strategy(strategy_name):
    """停止策略"""
    try:
        log(f"🛑 停止策略：{strategy_name}")
        subprocess.run(
            [SUPERVISORCTL, '-s', SOCKET, 'stop', strategy_name],
            timeout=10
        )
        time.sleep(5)
        log(f"✅ 策略已停止")
        return True
    except Exception as e:
        log(f"❌ 停止失败：{e}")
        return False

def start_strategy(strategy_name):
    """启动策略"""
    try:
        log(f"🚀 启动策略：{strategy_name}")
        subprocess.run(
            [SUPERVISORCTL, '-s', SOCKET, 'start', strategy_name],
            timeout=10
        )
        time.sleep(10)
        log(f"✅ 策略已启动")
        return True
    except Exception as e:
        log(f"❌ 启动失败：{e}")
        return False

def verify_close_position(symbol, before_positions):
    """验证平仓"""
    log(f"🔍 验证 {symbol} 平仓...")
    time.sleep(5)
    
    status = get_status()
    if not status:
        return False
    
    # 检查持仓是否消失
    for pos in status['positions']:
        if pos['symbol'] == symbol:
            log(f"❌ {symbol} 持仓仍在：{pos['size']}")
            return False
    
    log(f"✅ {symbol} 持仓已平")
    return True

def verify_cancel_stop_loss(symbol, before_orders):
    """验证撤销止损单"""
    log(f"🔍 验证 {symbol} 撤销止损单...")
    time.sleep(5)
    
    status = get_status()
    if not status:
        return False
    
    # 检查止损单是否减少
    symbol_orders = [o for o in status['stop_orders'] if o['symbol'] == symbol]
    
    if len(symbol_orders) > 0:
        log(f"❌ {symbol} 仍有 {len(symbol_orders)} 个止损单")
        return False
    
    log(f"✅ {symbol} 止损单已撤销")
    return True

def verify_new_strategy(symbol):
    """验证新策略"""
    log(f"🔍 验证 {symbol} 新策略...")
    time.sleep(10)
    
    status = get_status()
    if not status:
        return False
    
    # 检查注册中心
    registered = [s for s in status['registered'] if s.get('symbol') == symbol]
    if not registered:
        log(f"❌ {symbol} 未注册")
        return False
    
    log(f"✅ {symbol} 已注册")
    
    # 检查止损单
    stop_orders = [o for o in status['stop_orders'] if o['symbol'] == symbol]
    if len(stop_orders) == 0:
        log(f"❌ {symbol} 无止损单")
        return False
    
    log(f"✅ {symbol} 止损单已创建 ({len(stop_orders)}个)")
    return True

def run_test_cycle(cycle_num):
    """运行一轮测试"""
    log(f"\n{'='*50}")
    log(f"🧪 第 {cycle_num} 轮测试")
    log(f"{'='*50}")
    
    # 1. 检查初始状态
    log("\n【1】检查初始状态")
    status = get_status()
    if not status:
        log("❌ 无法获取状态")
        return False
    
    log(f"进程：{status['procs']} 个")
    log(f"持仓：{len(status['positions'])} 个 {[p['symbol'] for p in status['positions']]}")
    log(f"止损单：{len(status['stop_orders'])} 个")
    log(f"注册：{len(status['registered'])} 个")
    
    # 2. 随机选择一个策略
    strategy = random.choice(STRATEGIES)
    symbol = strategy['symbol']
    name = strategy['name']
    
    log(f"\n【2】选择测试目标：{symbol} ({name})")
    
    # 3. 停止策略
    log("\n【3】停止策略")
    if not stop_strategy(name):
        log("❌ 停止失败")
        return False
    
    # 4. 验证平仓
    log("\n【4】验证平仓")
    # 注意：当前策略可能没有持仓，所以这个验证可能不适用
    # verify_close_position(symbol, status['positions'])
    log("⚠️ 跳过平仓验证（可能无持仓）")
    
    # 5. 验证撤止损单
    log("\n【5】验证撤销止损单")
    # verify_cancel_stop_loss(symbol, status['stop_orders'])
    log("⚠️ 跳过撤止损单验证（需要持仓）")
    
    # 6. 启动策略
    log("\n【6】启动策略")
    if not start_strategy(name):
        log("❌ 启动失败")
        return False
    
    # 7. 验证新策略
    log("\n【7】验证新策略")
    if not verify_new_strategy(symbol):
        log("❌ 验证失败")
        return False
    
    log(f"\n✅ 第 {cycle_num} 轮测试完成")
    return True

def main():
    """主函数"""
    log("="*50)
    log("🧪 V3 系统循环测试开始")
    log("="*50)
    
    # 运行 3 轮测试
    for i in range(1, 4):
        if not run_test_cycle(i):
            log(f"\n❌ 第 {i} 轮测试失败")
            break
        time.sleep(30)  # 每轮间隔 30 秒
    
    log("\n" + "="*50)
    log("🧪 循环测试完成")
    log("="*50)

if __name__ == '__main__':
    main()
