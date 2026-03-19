#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSI 1 分钟策略 - 实时测试脚本
获取真实 1 分钟 K 线数据，测试信号频率
"""

import requests
import pandas as pd
import time
from datetime import datetime

# 导入策略（独立测试，不依赖策略类）
import pandas as pd
import numpy as np

def calculate_rsi(prices, period=14):
    """计算 RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def fetch_klines(symbol="ETHUSDT", interval="1m", limit=100):
    """从币安获取 K 线数据"""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    
    resp = requests.get(url, params=params)
    data = resp.json()
    
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
        'taker_buy_quote', 'ignore'
    ])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    
    return df

def main():
    print("🦞 RSI 1 分钟反转策略 - 实时信号测试")
    print("=" * 60)
    
    # 获取 ETHUSDT 1 分钟 K 线
    symbol = "ETHUSDT"
    print(f"\n📊 获取 {symbol} 1 分钟 K 线数据...")
    
    try:
        df = fetch_klines(symbol=symbol, interval="1m", limit=200)
        print(f"✅ 获取成功：{len(df)} 根 K 线")
        print(f"   时间范围：{df['timestamp'].min()} ~ {df['timestamp'].max()}")
    except Exception as e:
        print(f"❌ 获取失败：{e}")
        return
    
    # 生成信号
    df = generate_signal(df, rsi_period=14)
    
    # 统计信号
    rsi_above_50 = len(df[df['rsi'] > 50])
    rsi_below_50 = len(df[df['rsi'] < 50])
    
    print(f"\n📈 RSI 统计 (最近{len(df)}根 K 线):")
    print(f"   RSI > 50: {rsi_above_50} 次 ({rsi_above_50/len(df)*100:.1f}%)")
    print(f"   RSI < 50: {rsi_below_50} 次 ({rsi_below_50/len(df)*100:.1f}%)")
    
    # 运行回测
    print(f"\n🧪 运行回测...")
    result = backtest(df, symbol=symbol, initial_balance=10000, leverage=1)
    
    print(f"\n📊 回测结果:")
    print(f"   初始资金：${result['initial_balance']}")
    print(f"   最终资金：${result['final_balance']:.2f}")
    print(f"   总收益率：{result['total_return_pct']:+.2f}%")
    print(f"   总交易次数：{result['total_trades']}")
    print(f"   开空信号：{result['open_signals']} 次")
    print(f"   平仓信号：{result['close_signals']} 次")
    print(f"   止盈触发：{result['tp_hits']} 次")
    print(f"   止损触发：{result['sl_hits']} 次")
    
    # 显示最近 10 根 K 线的信号
    print(f"\n📋 最近 10 根 K 线信号:")
    print("-" * 60)
    recent = df.tail(10)[['timestamp', 'close', 'rsi', 'signal']]
    for idx, row in recent.iterrows():
        signal_text = "无操作"
        if row['signal'] == 1:
            signal_text = "🔴 开空"
        elif row['signal'] == -1:
            signal_text = "🟢 平空"
        
        ts = row['timestamp'].strftime('%H:%M')
        print(f"   {ts} | 价格：${row['close']:.2f} | RSI: {row['rsi']:.1f} | {signal_text}")
    
    print("=" * 60)
    print("✅ 策略测试完成！")
    
    # 信号频率分析
    if result['open_signals'] > 0:
        avg_signal_interval = len(df) / result['open_signals']
        print(f"\n💡 信号频率分析:")
        print(f"   平均每 {avg_signal_interval:.1f} 根 K 线产生 1 个开空信号")
        print(f"   按 1 分钟 K 线计算，约每 {avg_signal_interval:.1f} 分钟 1 个信号")
    
    return result

if __name__ == "__main__":
    main()
