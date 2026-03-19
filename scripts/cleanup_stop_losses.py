#!/usr/bin/env python3
"""
🦞 清理无效止损单脚本
"""

import requests
import hmac
import hashlib
import time
import os

# 配置
BINANCE_TESTNET = "https://testnet.binancefuture.com"
API_KEY = "YOUR_API_KEY"
SECRET = "YOUR_SECRET_KEY"

def cancel_stop_loss(symbol, algo_id):
    """取消止损单"""
    timestamp = int(time.time() * 1000)
    
    params = {
        'symbol': symbol,
        'algoId': algo_id,
        'timestamp': timestamp
    }
    
    # 生成签名
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    
    # 发送请求
    url = f"{BINANCE_TESTNET}/fapi/v1/algoOrder"
    headers = {
        'X-MBX-APIKEY': API_KEY
    }
    params['signature'] = signature
    
    response = requests.delete(url, headers=headers, params=params)
    
    return response.json()

if __name__ == '__main__':
    print("🧹 开始清理无效止损单...")
    
    # 1. 取消 AVAX 止损单（无持仓）
    print("\n1️⃣ 取消 AVAX 止损单 (ID: 1000000025994321)...")
    result = cancel_stop_loss('AVAXUSDT', '1000000025994321')
    print(f"结果：{result}")
    
    # 2. 取消旧 ETH 止损单（2070.97 是旧价格）
    print("\n2️⃣ 取消旧 ETH 止损单 (ID: 1000000025504429)...")
    result = cancel_stop_loss('ETHUSDT', '1000000025504429')
    print(f"结果：{result}")
    
    print("\n✅ 清理完成！")
