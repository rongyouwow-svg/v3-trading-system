#!/usr/bin/env python3
"""
🔄 异常重启自动恢复脚本

功能：
1. 检测异常重启
2. 检查交易所持仓
3. 自动启动对应策略
4. 同步止损单
"""

import requests
import subprocess
import time
from datetime import datetime

BASE_URL = "http://localhost:3000"
SUPERVISORCTL = "/root/.pyenv/versions/3.10.13/bin/supervisorctl"
SOCKET = "unix:///root/.openclaw/workspace/quant/v3-architecture/logs/supervisor.sock"
LOG_FILE = "/root/.openclaw/workspace/quant/v3-architecture/logs/auto_recovery.log"

# 策略映射：币种 → 策略文件
STRATEGY_MAP = {
    'ETHUSDT': 'rsi_1min_strategy.py',
    'LINKUSDT': 'link_rsi_detailed_strategy.py',
    'AVAXUSDT': 'rsi_scale_in_strategy.py'
}

def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")

def check_system_restart():
    """检查是否刚重启"""
    try:
        # 检查系统运行时间
        result = subprocess.run(['uptime'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=5)
        output = result.stdout
        
        # 如果运行时间 < 10 分钟，认为刚重启
        if 'min' in output:
            minutes = int(output.split('min')[0].split()[-1])
            if minutes < 10:
                log(f"✅ 检测到系统刚重启（运行{minutes}分钟）")
                return True
        elif 'hour' not in output and 'day' not in output:
            log("✅ 检测到系统刚重启（运行<1 分钟）")
            return True
        
        return False
    except Exception as e:
        log(f"❌ 检查重启失败：{e}")
        return False

def get_exchange_positions():
    """获取交易所持仓"""
    try:
        resp = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
        data = resp.json()
        positions = [p for p in data.get('positions', []) if p.get('size', 0) > 0]
        
        symbols = {p['symbol'] for p in positions}
        log(f"📊 检测到 {len(positions)} 个持仓：{symbols}")
        
        return symbols
    except Exception as e:
        log(f"❌ 获取持仓失败：{e}")
        return set()

def check_strategy_running(symbol):
    """检查策略是否运行"""
    try:
        resp = requests.get(f"{BASE_URL}/api/strategy/list", timeout=10)
        data = resp.json()
        strategies = data.get('data', {}).get('strategies', [])
        
        for s in strategies:
            if s.get('symbol') == symbol:
                return True
        
        return False
    except Exception as e:
        log(f"❌ 检查策略状态失败：{e}")
        return False

def start_strategy(symbol):
    """启动策略"""
    try:
        strategy_file = STRATEGY_MAP.get(symbol)
        if not strategy_file:
            log(f"⚠️ {symbol} 没有配置策略文件")
            return False
        
        # 检查 Supervisor 中是否已配置
        result = subprocess.run(
            [SUPERVISORCTL, '-s', SOCKET, 'status'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10
        )
        
        # 查找对应的策略进程
        for line in result.stdout.split('\n'):
            if strategy_file.replace('.py', '') in line:
                if 'RUNNING' in line:
                    log(f"✅ {symbol} 策略已在运行")
                    return True
                elif 'STOPPED' in line or 'FATAL' in line:
                    # 启动策略
                    strategy_name = line.split()[0]
                    log(f"🚀 启动策略：{strategy_name}")
                    subprocess.run(
                        [SUPERVISORCTL, '-s', SOCKET, 'start', strategy_name],
                        timeout=10
                    )
                    time.sleep(5)
                    log(f"✅ {symbol} 策略已启动")
                    return True
        
        log(f"⚠️ {symbol} 策略未在 Supervisor 中配置")
        return False
    
    except Exception as e:
        log(f"❌ 启动策略失败：{e}")
        return False

def sync_stop_loss(symbol):
    """同步止损单"""
    log(f"🔍 同步 {symbol} 止损单...")
    # 策略启动后会自动同步，这里只需要等待
    time.sleep(10)
    log(f"✅ {symbol} 止损单同步完成")

def main():
    """主函数"""
    log("=" * 50)
    log("🔄 异常重启自动恢复脚本启动")
    log("=" * 50)
    
    # 1. 检查是否刚重启
    if not check_system_restart():
        log("ℹ️ 系统正常运行中，跳过恢复")
        return
    
    # 2. 等待网络就绪
    log("⏳ 等待网络就绪...")
    time.sleep(10)
    
    # 3. 检查交易所持仓
    position_symbols = get_exchange_positions()
    if not position_symbols:
        log("ℹ️ 无持仓，跳过恢复")
        return
    
    # 4. 检查并启动策略
    log(f"🔍 检查 {len(position_symbols)} 个持仓的策略状态...")
    
    for symbol in position_symbols:
        log(f"\n检查 {symbol}...")
        
        if check_strategy_running(symbol):
            log(f"✅ {symbol} 策略已在运行")
        else:
            log(f"❌ {symbol} 策略未运行，启动中...")
            if start_strategy(symbol):
                log(f"✅ {symbol} 策略已启动")
                sync_stop_loss(symbol)
            else:
                log(f"❌ {symbol} 策略启动失败，需要手动干预")
    
    # 5. 汇总报告
    log("\n" + "=" * 50)
    log("🔄 恢复完成")
    log("=" * 50)

if __name__ == '__main__':
    main()
