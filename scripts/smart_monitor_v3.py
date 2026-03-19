#!/usr/bin/env python3
"""
🏥 智能监测系统 v3

核心改进：
1. 监测进程数量（应该 3 个）
2. 监测持仓 - 止损单匹配（1:1）
3. 监测注册中心状态
4. 监测策略生命周期
5. 自动清理重复止损单
"""

import requests
import time
from datetime import datetime
from collections import defaultdict

BASE_URL = "http://localhost:3000"
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "1233887750"
LOG_FILE = "/root/.openclaw/workspace/quant/v3-architecture/logs/smart_monitor_v3.log"

# 预期配置（动态获取）
EXPECTED_STRATEGIES = None  # 从 Supervisor 配置动态获取
EXPECTED_SYMBOLS = None  # 从配置动态获取

def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")

def send_alert(msg, force=False):
    """发送告警"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={'chat_id': CHAT_ID, 'text': f"🏥 智能监测 v3\n\n{msg}"},
            timeout=10
        )
        log("✅ 告警已发送")
    except Exception as e:
        log(f"❌ 告警发送失败：{e}")

def get_expected_strategies():
    """从 Supervisor 配置获取预期的策略"""
    try:
        import subprocess
        result = subprocess.run(
            ['grep', '-r', '^\[program:quant-strategy-', 
             '/root/.openclaw/workspace/quant/v3-architecture/supervisor/'],
            capture_output=True, text=True, timeout=5
        )
        
        strategies = []
        for line in result.stdout.split('\n'):
            if '[program:quant-strategy-' in line:
                # 提取策略名
                name = line.split('[program:')[1].split(']')[0]
                strategies.append(name)
        
        return strategies
    except:
        return []

def check_process_count():
    """检查策略进程数量（动态获取预期数量）"""
    log("🔍 检查进程数量...")
    
    try:
        import subprocess
        
        # 动态获取预期的策略
        expected = get_expected_strategies()
        expected_count = len(expected)
        
        # 统计实际进程
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True, text=True, timeout=5
        )
        
        strategy_procs = []
        for line in result.stdout.split('\n'):
            if 'strategy.*py' in line and 'grep' not in line:
                strategy_procs.append(line)
        
        actual_count = len(strategy_procs)
        
        # 允许一定弹性（策略重启时可能短暂多进程）
        if actual_count < expected_count:
            log(f"❌ 进程数量不足：{actual_count} 个（应该至少 {expected_count} 个）")
            send_alert(f"❌ 进程数量不足\n\n当前：{actual_count} 个\n应该：{expected_count} 个\n\n可能原因：\n1. 策略崩溃\n2. Supervisor 配置错误")
            return False
        elif actual_count > expected_count * 2:
            log(f"⚠️ 进程数量过多：{actual_count} 个（应该 {expected_count} 个）")
            send_alert(f"⚠️ 进程数量过多\n\n当前：{actual_count} 个\n应该：{expected_count} 个\n\n可能原因：\n1. 旧进程没清理\n2. 配置重复\n3. 需要重启服务器")
            return False
        else:
            log(f"✅ 进程数量正常：{actual_count} 个（预期 {expected_count} 个）")
            return True
    
    except Exception as e:
        log(f"❌ 进程检查失败：{e}")
        return None

def check_position_stop_loss_match():
    """检查持仓和止损单匹配（1:1）+ 币种维度检查"""
    log("🔍 检查持仓 - 止损单匹配...")
    
    try:
        # 获取持仓
        resp = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
        positions = [p for p in resp.json().get('positions', []) if p.get('size', 0) > 0]
        
        # 获取止损单
        resp = requests.get(f"{BASE_URL}/api/binance/stop-loss", timeout=10)
        stop_orders = [o for o in resp.json().get('orders', []) if o.get('status') == 'NEW']
        
        # 获取注册中心策略
        resp = requests.get(f"{BASE_URL}/api/strategy/list", timeout=10)
        strategies = resp.json().get('data', {}).get('strategies', [])
        
        # 按币种分组
        position_symbols = {p['symbol'] for p in positions}
        stop_symbols = defaultdict(list)
        for o in stop_orders:
            stop_symbols[o['symbol']].append(o)
        
        # 按币种分组策略
        strategy_symbols = defaultdict(list)
        for s in strategies:
            strategy_symbols[s.get('symbol')].append(s)
        
        log(f"  持仓：{len(positions)} 个 {list(position_symbols)}")
        log(f"  止损单：{len(stop_orders)} 个 {[(k,len(v)) for k,v in stop_symbols.items()]}")
        log(f"  注册策略：{len(strategies)} 个 {[(k,len(v)) for k,v in strategy_symbols.items()]}")
        
        issues = []
        
        # 检查 1：每个币种是否有且仅有 1 个策略在运行
        for symbol, strat_list in strategy_symbols.items():
            if len(strat_list) > 1:
                issues.append(f"{symbol}: 有{len(strat_list)}个策略同时运行（应该 1 个）❌")
                log(f"  ❌ {symbol}: {len(strat_list)} 个策略同时运行")
        
        # 检查 2：每个持仓是否有且仅有 1 个止损单
        for symbol in position_symbols:
            stop_count = len(stop_symbols.get(symbol, []))
            strat_count = len(strategy_symbols.get(symbol, []))
            
            if stop_count == 0 and strat_count > 0:
                issues.append(f"{symbol}: 策略运行中但无止损单 ❌")
            elif stop_count > 1:
                issues.append(f"{symbol}: 有{stop_count}个止损单（应该 1 个）❌")
            elif stop_count == 1:
                log(f"  ✅ {symbol}: 1 策略 = 1 止损单")
        
        # 检查 3：孤儿止损单
        for symbol in stop_symbols:
            if symbol not in position_symbols and symbol not in strategy_symbols:
                issues.append(f"{symbol}: 无策略无止损但有{len(stop_symbols[symbol])}个止损单（孤儿单）❌")
        
        if issues:
            log(f"❌ 发现 {len(issues)} 个问题")
            send_alert(f"持仓 - 止损单匹配异常\n\n" + "\n".join(issues))
            
            # 自动清理重复止损单
            if len(stop_orders) > len(position_symbols):
                log("🗑️ 自动清理重复止损单...")
                cleanup_duplicate_stop_loss(position_symbols, stop_symbols)
            
            return False
        else:
            log("✅ 持仓 - 止损单 - 策略匹配正常")
            return True
    
    except Exception as e:
        log(f"❌ 匹配检查失败：{e}")
        return None

def cleanup_duplicate_stop_loss(position_symbols, stop_symbols):
    """清理重复止损单"""
    import hmac, hashlib, urllib.parse, requests as req
    
    API_KEY = "YOUR_API_KEY"
    SECRET = "YOUR_SECRET_KEY"
    BINANCE = "https://testnet.binancefuture.com"
    
    def sign(params):
        return hmac.new(SECRET.encode(), urllib.parse.urlencode(params).encode(), hashlib.sha256).hexdigest()
    
    cancelled = 0
    for symbol, orders in stop_symbols.items():
        if len(orders) > 1:
            # 保留最新的
            orders.sort(key=lambda x: x.get('create_time', 0), reverse=True)
            for order in orders[1:]:
                algo_id = order.get('algo_id')
                ts = int(time.time() * 1000)
                params = {'symbol': symbol, 'algoId': algo_id, 'timestamp': ts}
                params['signature'] = sign(params)
                
                resp = req.delete(f"{BINANCE}/fapi/v1/algoOrder",
                    headers={'X-MBX-APIKEY': API_KEY}, params=params, timeout=10)
                
                if resp.status_code == 200:
                    log(f"  ✅ 取消 {symbol} {algo_id}")
                    cancelled += 1
    
    log(f"✅ 清理了 {cancelled} 个重复止损单")
    send_alert(f"🗑️ 自动清理完成\n\n清理了 {cancelled} 个重复止损单")

def check_registry():
    """检查注册中心状态（动态）"""
    log("🔍 检查注册中心...")
    
    try:
        resp = requests.get(f"{BASE_URL}/api/strategy/list", timeout=10)
        data = resp.json()
        strategies = data.get('data', {}).get('strategies', [])
        
        count = len(strategies)
        symbols = {s.get('symbol') for s in strategies}
        
        log(f"  注册策略：{count} 个 {symbols}")
        
        # 动态获取预期策略
        expected = get_expected_strategies()
        
        if count == 0 and len(expected) > 0:
            log("⚠️ 注册中心为空（可能策略未注册）")
            return False
        else:
            log("✅ 注册中心正常")
            return True
    
    except Exception as e:
        log(f"❌ 注册中心检查失败：{e}")
        return None

def check_protection_list():
    """检查保护清单是否基于注册中心"""
    log("🔍 检查保护清单...")
    # TODO: 检查监控系统是否基于注册中心
    return True

def main():
    """主循环"""
    log("=" * 50)
    log("🏥 智能监测系统 v3 启动")
    log("=" * 50)
    
    send_alert("🏥 智能监测系统 v3 已启动\n\n监测内容：\n1. 进程数量\n2. 持仓 - 止损单匹配\n3. 注册中心状态\n4. 自动清理重复止损单")
    
    check_count = 0
    
    while True:
        try:
            check_count += 1
            log(f"\n=== 第 {check_count} 次检查 ===")
            
            # 1. 检查进程数量
            process_ok = check_process_count()
            
            # 2. 检查持仓 - 止损单匹配
            match_ok = check_position_stop_loss_match()
            
            # 3. 检查注册中心
            registry_ok = check_registry()
            
            # 4. 汇总
            if process_ok and match_ok and registry_ok:
                log("✅ 所有检查通过")
            else:
                log(f"⚠️ 发现问题：进程={process_ok}, 匹配={match_ok}, 注册={registry_ok}")
            
            # 每 5 分钟检查一次
            time.sleep(300)
        
        except KeyboardInterrupt:
            log("⬇️  监测停止")
            break
        except Exception as e:
            log(f"❌ 监测异常：{e}")
            time.sleep(60)

if __name__ == '__main__':
    main()
