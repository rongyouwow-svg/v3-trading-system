#!/usr/bin/env python3
"""
测试新的测试网 API Key 下单功能
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace/quant')

from api.binance_client import BinanceClient

# 新的测试网 API Key
API_KEY = {
    'api_key': 'S10pBsm41EGeotI8WXHlfvrv1TmT8vA1kSQKBNCHx3PmiGiOdtmzqeg06k25u3ns',
    'secret_key': 'us7IDPAPXCUPvr7Y23iVnAj9AmoI7o5GWieAs7HgwpARGOJvOZEqLwuvPBjRwyUf'
}

print("="*60)
print("🧪 测试新的测试网 API Key")
print("="*60)

client = BinanceClient(API_KEY['api_key'], API_KEY['secret_key'], testnet=True)

# 测试 1: 获取账户余额
print("\n1. 获取账户余额...")
account = client.get_futures_account()
print(f"   结果：{account.get('success', False)}")
if account.get('success'):
    usdt = next((a for a in account.get('assets', []) if a['asset'] == 'USDT'), None)
    if usdt:
        print(f"   USDT 可用余额：${usdt.get('availableBalance', 0)}")
        print(f"   USDT 总余额：${usdt.get('walletBalance', 0)}")

# 测试 2: 获取 BTC 价格
print("\n2. 获取 BTCUSDT 价格...")
price_result = client.get_spot_price('BTCUSDT')
print(f"   结果：{price_result.get('success', False)}")
if price_result.get('success'):
    print(f"   BTC 价格：${price_result['price']}")

# 测试 3: 尝试下单
print("\n3. 尝试下单（0.001 BTC LONG）...")
if price_result.get('success'):
    quantity = 0.001
    order = client.place_futures_order(
        symbol='BTCUSDT',
        side='BUY',
        order_type='MARKET',
        quantity=quantity
    )
    print(f"   下单结果：{order}")

print("\n" + "="*60)
print("✅ 测试完成")
print("="*60)
