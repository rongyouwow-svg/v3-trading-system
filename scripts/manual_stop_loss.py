#!/usr/bin/env python3
"""
🛑 手动设置止损单脚本
用途：为已有持仓快速设置止损单
"""

import requests
import json

BASE_URL = "http://localhost:3000"

def get_positions():
    """获取当前持仓"""
    resp = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
    data = resp.json()
    return data.get('positions', [])

def create_stop_loss(symbol, side, size, stop_price):
    """创建止损单"""
    resp = requests.post(f"{BASE_URL}/api/binance/stop-loss", json={
        'symbol': symbol,
        'side': side,
        'trigger_price': stop_price,
        'quantity': size
    }, timeout=10)
    return resp.json()

def main():
    print("=" * 50)
    print("🛑 手动设置止损单")
    print("=" * 50)
    print()
    
    # 获取持仓
    positions = get_positions()
    if not positions:
        print("✅ 无持仓")
        return
    
    print(f"📊 当前持仓 ({len(positions)} 个):")
    for pos in positions:
        print(f"  - {pos['symbol']}: {pos['size']} {pos['side']} @ {pos['entry_price']} (盈亏：{pos['unrealized_pnl_pct']}%)")
    print()
    
    # 为每个持仓设置止损
    for pos in positions:
        if pos['size'] <= 0:
            continue
        
        symbol = pos['symbol']
        entry_price = pos['entry_price']
        current_price = pos['current_price']
        size = pos['size']
        
        # 计算止损价（当前价的 98%）
        stop_price = current_price * 0.98
        
        print(f"🔧 为 {symbol} 设置止损...")
        print(f"  入场价：{entry_price}")
        print(f"  当前价：{current_price}")
        print(f"  止损价：{stop_price:.2f} (-2%)")
        
        result = create_stop_loss(symbol, 'SELL', size, stop_price)
        if result.get('success'):
            print(f"  ✅ 止损单创建成功")
        else:
            print(f"  ❌ 止损单创建失败：{result.get('error', 'Unknown')}")
        print()

if __name__ == '__main__':
    main()
