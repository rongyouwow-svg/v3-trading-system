#!/usr/bin/env python3
"""
币安测试网 API 调试脚本
"""

import time
import hashlib
import hmac
from urllib.parse import urlencode
import requests

# API 配置
API_KEY = "YOUR_API_KEY"
SECRET_KEY = "YOUR_SECRET_KEY"
BASE_URL = "https://demo-fapi.binance.com"

def test_balance():
    """测试获取余额"""
    print("\n=== 测试获取余额 ===")
    
    # 构建参数
    params = {
        'timestamp': int(time.time() * 1000),
        'recvWindow': 5000
    }
    
    # 生成签名
    query_string = urlencode(params)
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    params['signature'] = signature
    
    # 发送请求
    headers = {
        'X-MBX-APIKEY': API_KEY,
    }
    
    url = f"{BASE_URL}/fapi/v2/balance"
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功！余额：{data}")
        return True
    else:
        print(f"❌ 失败：{response.text}")
        return False

def test_time():
    """测试获取服务器时间"""
    print("\n=== 测试获取服务器时间 ===")
    
    url = f"{BASE_URL}/fapi/v1/time"
    response = requests.get(url, timeout=10)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 服务器时间：{data}")
        return True
    else:
        print(f"❌ 失败：{response.text}")
        return False

if __name__ == "__main__":
    print("🦞 币安测试网 API 调试")
    print(f"API URL: {BASE_URL}")
    
    # 测试 1: 获取时间
    test_time()
    
    # 测试 2: 获取余额
    test_balance()
