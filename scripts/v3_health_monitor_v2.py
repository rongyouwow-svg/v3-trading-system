#!/usr/bin/env python3
"""
🏥 V3 健康监控 v2 - 基于策略注册中心

核心改进：
1. 从注册中心获取保护清单
2. 只保护正在运行的策略
3. 策略注销后自动停止保护
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:3000"
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "1233887750"
LOG_FILE = "/root/.openclaw/workspace/quant/v3-architecture/logs/health_monitor_v2.log"

def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")

def send_alert(msg):
    """发送告警"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={'chat_id': CHAT_ID, 'text': f"🏥 V3 健康监控\n\n{msg}"},
            timeout=10
        )
        log("✅ 告警已发送")
    except Exception as e:
        log(f"❌ 告警发送失败：{e}")

def get_active_strategies():
    """从注册中心获取活跃策略"""
    try:
        resp = requests.get(f"{BASE_URL}/api/strategy/list", timeout=10)
        data = resp.json()
        strategies = data.get('strategies', [])
        log(f"📊 活跃策略：{len(strategies)} 个")
        return strategies
    except Exception as e:
        log(f"❌ 获取策略列表失败：{e}")
        return []

def check_strategy_stop_loss(symbol):
    """检查单个策略的止损单"""
    try:
        # 获取持仓
        resp = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
        positions = resp.json().get('positions', [])
        
        # 获取止损单
        resp = requests.get(f"{BASE_URL}/api/binance/stop-loss", timeout=10)
        stop_data = resp.json()
        stop_orders = stop_data.get('orders', [])
        
        # 查找该策略的持仓
        for pos in positions:
            if pos.get('symbol') == symbol and pos.get('size', 0) > 0:
                # 查找对应的止损单
                has_stop = any(o['symbol'] == symbol and o.get('status') == 'NEW' for o in stop_orders)
                if not has_stop:
                    log(f"❌ {symbol}: 有持仓但无止损单")
                    return False
                else:
                    log(f"✅ {symbol}: 持仓和止损单匹配")
                    return True
        
        return True  # 无持仓
    
    except Exception as e:
        log(f"❌ 检查失败：{e}")
        return False

def main():
    """主循环"""
    log("=" * 50)
    log("🏥 V3 健康监控 v2 启动")
    log("基于策略注册中心 - 动态保护清单")
    log("=" * 50)
    
    send_alert("🏥 V3 健康监控 v2 已启动\n\n从注册中心获取保护清单\n动态保护运行中的策略")
    
    fail_count = 0
    
    while True:
        try:
            # 1. 从注册中心获取活跃策略
            active_strategies = get_active_strategies()
            
            if not active_strategies:
                log("⚠️ 当前无活跃策略")
                time.sleep(60)
                continue
            
            # 2. 检查每个活跃策略
            issues = []
            for strategy in active_strategies:
                symbol = strategy.get('symbol')
                log(f"🔍 检查策略：{symbol}")
                
                if not check_strategy_stop_loss(symbol):
                    issues.append(f"{symbol}: 无止损单")
            
            # 3. 告警
            if issues:
                fail_count += 1
                log(f"⚠️ 发现 {len(issues)} 个问题")
                
                if fail_count >= 3:
                    send_alert(f"⚠️ 系统连续失败 {fail_count} 次\n\n问题:\n" + "\n".join(issues))
                    fail_count = 0
                    time.sleep(300)
            else:
                fail_count = 0
                log("✅ 所有策略正常")
            
            time.sleep(60)
        
        except KeyboardInterrupt:
            log("⬇️  监控停止")
            break
        except Exception as e:
            log(f"❌ 监控异常：{e}")
            time.sleep(60)

if __name__ == '__main__':
    main()
