#!/usr/bin/env python3
"""
对比调试脚本和连接器的区别
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from connectors.binance.usdt_futures import BinanceUSDTFuturesConnector

# API 配置
API_KEY = "YOUR_API_KEY"
SECRET_KEY = "YOUR_SECRET_KEY"

# 创建连接器
connector = BinanceUSDTFuturesConnector(API_KEY, SECRET_KEY, testnet=True)

# 测试获取余额
print("\n=== 测试连接器获取余额 ===")
result = connector.get_account_balance()

print(f"Result: {result}")
print(f"Is Success: {result.is_success}")
print(f"Message: {result.message}")
if result.data:
    print(f"Data: {result.data}")
if result.error_code:
    print(f"Error Code: {result.error_code}")
