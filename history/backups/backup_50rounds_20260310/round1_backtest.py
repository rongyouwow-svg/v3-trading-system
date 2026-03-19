#!/usr/bin/env python3
"""
🦞 第 1 轮：周期 + 信号组合测试
测试规模：11,520 种组合
目标：找到最优周期 + 最优信号组合
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import itertools
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace/quant')

from signal_library import SignalLibrary

print("=" * 60)
print("🧪 第 1 轮：周期 + 信号组合测试")
print("=" * 60)

# 加载 ETH 数据
print("\n📊 加载数据...")
df_15m = pd.read_csv('data/ETHUSDT_15m.csv', index_col='timestamp', parse_dates=True)
print(f"15 分钟数据：{len(df_15m)} 条")

# 重采样到其他周期
df_30m = df_15m.resample('30min').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
}).dropna()
print(f"30 分钟数据：{len(df_30m)} 条")

df_1h = df_15m.resample('1h').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
}).dropna()
print(f"1 小时数据：{len(df_1h)} 条")

df_4h = df_15m.resample('4h').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
}).dropna()
print(f"4 小时数据：{len(df_4h)} 条")

# 测试配置
periods = {
    '15m': df_15m,
    '30m': df_30m,
    '1h': df_1h,
    '4h': df_4h,
}

# 信号组合
signal_combos = {
    '3 指标': ['WR70', 'J9', 'RSI7'],
    '4 指标': ['WR70', 'J9', 'RSI7', 'ADX14'],
    '5 指标': ['WR70', 'J9', 'RSI7', 'BB_Position', 'ADX14'],
    '6 指标': ['WR70', 'J9', 'RSI7', 'BB_Position', 'ADX14', 'Volume_Ratio'],
    '6+ 特殊': ['WR70', 'J9', 'RSI7', 'BB_Position', 'ADX14', 'Volume_Ratio', 'Extreme', 'OBV_Divergence'],
}

# 阈值测试
wr_thresholds = [-60, -70, -80, -90]
j_thresholds = [20, 25, 30]
rsi_thresholds = [35, 40, 45]
adx_thresholds = [20, 25, 30, 35]
time_filters = [True, False]
directions = ['long_only', 'short_only', 'both']

# 回测参数
fee_rate = 0.0003
slippage = 0.0005
initial_capital = 10000

def run_backtest(df, signal_lib, config):
    """运行回测"""
    # 获取信号
    signals = signal_lib.get_all_signals()
    
    # 根据配置生成交易信号
    if config['signal_combo'] == '3 指标':
        wr = signals['WR70']
        j = signals['J9']
        rsi = signals['RSI7']
        
        long_signal = (
            (wr > config['wr_threshold']) &
            (j < config['j_threshold']) &
            (rsi < config['rsi_threshold'])
        )
        
        short_signal = (
            (wr < -config['wr_threshold']) &
            (j > 100 - config['j_threshold']) &
            (rsi > 100 - config['rsi_threshold'])
        )
    
    elif config['signal_combo'] == '4 指标':
        wr = signals['WR70']
        j = signals['J9']
        rsi = signals['RSI7']
        adx = signals['ADX14']
        
        long_signal = (
            (wr > config['wr_threshold']) &
            (j < config['j_threshold']) &
            (rsi < config['rsi_threshold']) &
            (adx > config['adx_threshold'])
        )
        
        short_signal = (
            (wr < -config['wr_threshold']) &
            (j > 100 - config['j_threshold']) &
            (rsi > 100 - config['rsi_threshold']) &
            (adx > config['adx_threshold'])
        )
    
    elif config['signal_combo'] == '5 指标':
        wr = signals['WR70']
        j = signals['J9']
        rsi = signals['RSI7']
        bb_pos = signals['BB_Position']
        adx = signals['ADX14']
        
        long_signal = (
            (wr > config['wr_threshold']) &
            (j < config['j_threshold']) &
            (rsi < config['rsi_threshold']) &
            (bb_pos < 0.1) &
            (adx > config['adx_threshold'])
        )
        
        short_signal = (
            (wr < -config['wr_threshold']) &
            (j > 100 - config['j_threshold']) &
            (rsi > 100 - config['rsi_threshold']) &
            (bb_pos > 0.9) &
            (adx > config['adx_threshold'])
        )
    
    elif config['signal_combo'] == '6 指标':
        wr = signals['WR70']
        j = signals['J9']
        rsi = signals['RSI7']
        bb_pos = signals['BB_Position']
        adx = signals['ADX14']
        vol_ratio = signals['Volume_Ratio']
        
        long_signal = (
            (wr > config['wr_threshold']) &
            (j < config['j_threshold']) &
            (rsi < config['rsi_threshold']) &
            (bb_pos < 0.1) &
            (adx > config['adx_threshold']) &
            (vol_ratio < 0.5)
        )
        
        short_signal = (
            (wr < -config['wr_threshold']) &
            (j > 100 - config['j_threshold']) &
            (rsi > 100 - config['rsi_threshold']) &
            (bb_pos > 0.9) &
            (adx > config['adx_threshold']) &
            (vol_ratio > 2.0)
        )
    
    else:  # 6+ 特殊
        wr = signals['WR70']
        j = signals['J9']
        rsi = signals['RSI7']
        bb_pos = signals['BB_Position']
        adx = signals['ADX14']
        vol_ratio = signals['Volume_Ratio']
        extreme = signals['Extreme']
        obv_div = signals['OBV_Divergence']
        
        long_signal = (
            (wr > config['wr_threshold']) &
            (j < config['j_threshold']) &
            (rsi < config['rsi_threshold']) &
            (bb_pos < 0.1) &
            (adx > config['adx_threshold']) &
            (vol_ratio < 0.5)
        ) | (extreme == 1) | (obv_div == 1)
        
        short_signal = (
            (wr < -config['wr_threshold']) &
            (j > 100 - config['j_threshold']) &
            (rsi > 100 - config['rsi_threshold']) &
            (bb_pos > 0.9) &
            (adx > config['adx_threshold']) &
            (vol_ratio > 2.0)
        ) | (extreme == -1) | (obv_div == -1)
    
    # 时间过滤
    if config['time_filter']:
        high_vol = signal_lib.is_high_vol_hour()
        long_signal = long_signal & (high_vol == 1)
        short_signal = short_signal & (high_vol == 1)
    
    # 方向过滤
    if config['direction'] == 'long_only':
        short_signal = pd.Series(False, index=df.index)
    elif config['direction'] == 'short_only':
        long_signal = pd.Series(False, index=df.index)
    
    # 运行回测
    capital = initial_capital
    position = None
    trades = []
    equity_curve = [capital]
    
    close_prices = df['close'].values
    high_prices = df['high'].values
    low_prices = df['low'].values
    
    for i in range(100, len(df)):
        # 检查开仓信号
        if position is None:
            if long_signal.iloc[i]:
                entry_price = close_prices[i] * (1 + slippage)
                size = (capital * 0.5) / entry_price  # 50% 仓位
                position = {'side': 'long', 'entry': entry_price, 'size': size}
            
            elif short_signal.iloc[i]:
                entry_price = close_prices[i] * (1 - slippage)
                size = (capital * 0.5) / entry_price
                position = {'side': 'short', 'entry': entry_price, 'size': size}
        
        else:
            # 检查平仓信号（反向信号或固定止盈止损）
            high = high_prices[i]
            low = low_prices[i]
            close = close_prices[i]
            
            exit_price = None
            
            if position['side'] == 'long':
                # 止损 4%
                if low <= position['entry'] * 0.96:
                    exit_price = position['entry'] * 0.96 * (1 - slippage)
                # 止盈 6%
                elif high >= position['entry'] * 1.06:
                    exit_price = position['entry'] * 1.06 * (1 - slippage)
                # 反向信号
                elif short_signal.iloc[i] if isinstance(short_signal, pd.Series) else False:
                    exit_price = close * (1 - slippage)
            
            else:  # short
                # 止损 4%
                if high >= position['entry'] * 1.04:
                    exit_price = position['entry'] * 1.04 * (1 + slippage)
                # 止盈 6%
                elif low <= position['entry'] * 0.94:
                    exit_price = position['entry'] * 0.94 * (1 + slippage)
                # 反向信号
                elif long_signal.iloc[i] if isinstance(long_signal, pd.Series) else False:
                    exit_price = close * (1 + slippage)
            
            if exit_price:
                # 计算盈亏
                if position['side'] == 'long':
                    pnl = (exit_price - position['entry']) * position['size']
                else:
                    pnl = (position['entry'] - exit_price) * position['size']
                
                fee = position['size'] * position['entry'] * fee_rate * 2
                net_pnl = pnl - fee
                
                capital += net_pnl
                trades.append({
                    'pnl': net_pnl,
                    'win': net_pnl > 0,
                    'side': position['side']
                })
                
                position = None
        
        equity_curve.append(capital)
    
    # 计算统计指标
    if len(trades) == 0:
        return None
    
    final_capital = equity_curve[-1]
    total_return = (final_capital - initial_capital) / initial_capital * 100
    
    days = len(df) / (24 * 4)  # 15 分钟数据
    if '30m' in str(config.get('period', '')):
        days = len(df) / (24 * 2)
    elif '1h' in str(config.get('period', '')):
        days = len(df) / 24
    elif '4h' in str(config.get('period', '')):
        days = len(df) / 6
    
    years = days / 365
    annual_return = ((final_capital / initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0
    
    # 最大回撤
    max_dd = 0
    peak = initial_capital
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak
        if dd > max_dd:
            max_dd = dd
    
    # 胜率
    win_trades = [t for t in trades if t['win']]
    win_rate = len(win_trades) / len(trades) * 100
    
    # 盈亏比
    avg_win = np.mean([t['pnl'] for t in win_trades]) if win_trades else 0
    lose_trades = [t for t in trades if not t['win']]
    avg_lose = np.mean([t['pnl'] for t in lose_trades]) if lose_trades else 0
    profit_factor = abs(avg_win / avg_lose) if avg_lose != 0 else 0
    
    # 夏普比率
    returns = np.diff(equity_curve) / equity_curve[:-1]
    sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252 * 4) if len(returns) > 0 and np.std(returns) > 0 else 0
    
    return {
        'annual_return': annual_return,
        'max_drawdown': max_dd * 100,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'sharpe': sharpe,
        'total_trades': len(trades),
        'total_return': total_return,
        'final_capital': final_capital,
    }


# 运行批量回测
print("\n🔄 开始批量回测...")
print(f"测试规模：4 周期 × 5 信号组合 × 4WR × 3J × 3RSI × 4ADX × 2 时间 × 3 方向 = 11,520 种")

results = []
tested = 0
best_results = []

# 为了节省时间，先测试部分组合
test_configs = []

# 生成所有配置组合
for period_name, period_df in periods.items():
    for signal_combo in signal_combos.keys():
        for wr_t in wr_thresholds:
            for j_t in j_thresholds:
                for rsi_t in rsi_thresholds:
                    for adx_t in adx_thresholds:
                        for time_f in time_filters:
                            for direction in directions:
                                config = {
                                    'period': period_name,
                                    'signal_combo': signal_combo,
                                    'wr_threshold': wr_t,
                                    'j_threshold': j_t,
                                    'rsi_threshold': rsi_t,
                                    'adx_threshold': adx_t,
                                    'time_filter': time_f,
                                    'direction': direction,
                                }
                                test_configs.append(config)

print(f"总配置数：{len(test_configs)}")

# 运行回测（由于数量巨大，这里只测试前 100 个作为示例）
# 实际执行时可以调整数量
max_tests = 100  # 先测试 100 个，确认逻辑正确

for i, config in enumerate(test_configs[:max_tests]):
    period_name = config['period']
    period_df = periods[period_name]
    
    # 初始化信号库
    signal_lib = SignalLibrary()
    signal_lib.load_data(period_df)
    
    # 运行回测
    result = run_backtest(period_df, signal_lib, config)
    
    if result:
        result['config'] = config
        results.append(result)
        
        # 保留最优结果
        if len(best_results) < 20:
            best_results.append(result)
            best_results.sort(key=lambda x: x['annual_return'], reverse=True)
        else:
            if result['annual_return'] > best_results[-1]['annual_return']:
                best_results[-1] = result
                best_results.sort(key=lambda x: x['annual_return'], reverse=True)
    
    tested += 1
    if tested % 20 == 0:
        print(f"已测试：{tested}/{max_tests}, 当前最优年化：{best_results[0]['annual_return']:.1f}%")

# 输出结果
print("\n" + "=" * 60)
print("📊 第 1 轮回测结果（前 100 个配置）")
print("=" * 60)

print(f"\n总测试数：{tested}")
print(f"有效结果：{len(results)}")

if len(best_results) > 0:
    print(f"\n🏆 最优配置（Top 5）:")
    print("-" * 60)
    
    for i, result in enumerate(best_results[:5], 1):
        config = result['config']
        print(f"\n第{i}名:")
        print(f"  周期：{config['period']}")
        print(f"  信号组合：{config['signal_combo']}")
        print(f"  WR 阈值：{config['wr_threshold']}")
        print(f"  J 阈值：{config['j_threshold']}")
        print(f"  RSI 阈值：{config['rsi_threshold']}")
        print(f"  ADX 阈值：{config['adx_threshold']}")
        print(f"  时间过滤：{'启用' if config['time_filter'] else '禁用'}")
        print(f"  方向：{config['direction']}")
        print(f"\n  年化收益：{result['annual_return']:.1f}%")
        print(f"  最大回撤：{result['max_drawdown']:.1f}%")
        print(f"  胜率：{result['win_rate']:.1f}%")
        print(f"  盈亏比：{result['profit_factor']:.2f}:1")
        print(f"  夏普比率：{result['sharpe']:.2f}")
        print(f"  交易次数：{result['total_trades']}")

# 保存结果
with open('round1_results_sample.json', 'w') as f:
    json.dump({
        'total_tested': tested,
        'valid_results': len(results),
        'best_results': best_results[:5],
    }, f, indent=2, ensure_ascii=False, default=str)

print(f"\n📁 结果已保存：round1_results_sample.json")
print("=" * 60)
