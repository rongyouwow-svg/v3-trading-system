#!/usr/bin/env python3
"""
对比调试脚本和连接器的区别
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from connectors.binance.usdt_futures import BinanceUSDTFuturesConnector

# API 配置
API_KEY = "q3BX9K88wS4Dzco6DxVp5fhkRc5OOUu3tKFK5VBHkpcweVJ1NDDgATDV6Db0TTOg"
SECRET_KEY = "J3rsWIqPPjdRtXzbBReq24YiKrw03CiHopRxM1B5eUTQ6xZ6pi1jLK1lmiYrqctY"

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
