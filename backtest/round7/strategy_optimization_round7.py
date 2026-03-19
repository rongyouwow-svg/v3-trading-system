#!/usr/bin/env python3
# strategy_optimization_round7.py - 第 7 轮策略优化
# 目标：100% 年化收益，优化交易频率和盈亏比

import json, os, urllib.request, ssl
from datetime import datetime
from pathlib import Path

RESULTS_DIR = "/home/admin/.openclaw/workspace/quant/backtest/round7"
os.makedirs(RESULTS_DIR, exist_ok=True)

# 基于 R6 最优参数，进一步优化
# R6 最佳：MA 10/30, RSI 10, ADX 15, SL 2.5%, TP 35%, Position 30%
# R7 优化方向：提高交易频率，优化出场逻辑

PARAM_GRID = {
    "ma_short": [8, 10, 12],
    "ma_long": [25, 30, 35],
    "rsi_period": [8, 10, 12],
    "adx_filter": [12, 15, 18],
    "stop_loss": [0.02, 0.025, 0.03],
    "take_profit": [0.30, 0.35, 0.40],
    "position_size": [0.25, 0.30, 0.35]
}

SYMBOLS = ["BTCUSDT", "ETHUSDT", "AVAXUSDT", "UNIUSDT"]
INTERVAL = "15m"
LIMIT = 1000

def fetch_klines(symbol, interval="15m", limit=1000):
    """获取 K 线数据"""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(url, context=context, timeout=10) as response:
            data = json.loads(response.read().decode())
        return [{
            'timestamp': candle[0],
            'open': float(candle[1]),
            'high': float(candle[2]),
            'low': float(candle[3]),
            'close': float(candle[4]),
            'volume': float(candle[5])
        } for candle in data]
    except Exception as e:
        print(f"❌ 获取 {symbol} 数据失败：{e}")
        return []

def calculate_ma(data, period):
    """计算 MA"""
    if len(data) < period:
        return None
    closes = [c['close'] for c in data[-period:]]
    return sum(closes) / period

def calculate_rsi(data, period=14):
    """计算 RSI"""
    if len(data) < period + 1:
        return None
    
    closes = [c['close'] for c in data]
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    
    if len(gains) < period:
        return None
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_adx(data, period=14):
    """计算 ADX（简化版）"""
    if len(data) < period + 1:
        return None
    
    tr_list = []
    plus_dm = []
    minus_dm = []
    
    for i in range(1, len(data)):
        high = data[i]['high']
        low = data[i]['low']
        prev_close = data[i-1]['close']
        
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)
        
        plus = high - data[i-1]['high']
        minus = data[i-1]['low'] - low
        
        if plus > minus and plus > 0:
            plus_dm.append(plus)
        else:
            plus_dm.append(0)
        
        if minus > plus and minus > 0:
            minus_dm.append(minus)
        else:
            minus_dm.append(0)
    
    if len(tr_list) < period:
        return None
    
    tr_avg = sum(tr_list[-period:]) / period
    plus_dm_avg = sum(plus_dm[-period:]) / period
    minus_dm_avg = sum(minus_dm[-period:]) / period
    
    if tr_avg == 0:
        return 0
    
    plus_di = (plus_dm_avg / tr_avg) * 100
    minus_di = (minus_dm_avg / tr_avg) * 100
    
    if plus_di + minus_di == 0:
        return 0
    
    dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
    return dx

def generate_signal(data, params):
    """生成交易信号"""
    if len(data) < params['ma_long'] + 1:
        return None
    
    ma_short = calculate_ma(data, params['ma_short'])
    ma_long = calculate_ma(data, params['ma_long'])
    rsi = calculate_rsi(data, params['rsi_period'])
    adx = calculate_adx(data, params['adx_filter'])
    
    if not all([ma_short, ma_long, rsi, adx]):
        return None
    
    current_price = data[-1]['close']
    
    # 多头信号
    long_signal = (
        ma_short > ma_long and
        rsi < 70 and
        adx > params['adx_filter']
    )
    
    # 空头信号
    short_signal = (
        ma_short < ma_long and
        rsi > 30 and
        adx > params['adx_filter']
    )
    
    if long_signal:
        return 'LONG'
    elif short_signal:
        return 'SHORT'
    else:
        return None

def run_backtest(symbol, params, data):
    """运行回测"""
    capital = 10000
    position_size = params['position_size']
    stop_loss = params['stop_loss']
    take_profit = params['take_profit']
    
    trades = []
    in_position = False
    position_type = None
    entry_price = 0
    
    for i in range(len(data) - 50):  # 留 50 根 K 线用于指标计算
        window = data[i:i+50]
        signal = generate_signal(window, params)
        current_price = data[i]['close']
        
        # 开仓
        if not in_position and signal:
            in_position = True
            position_type = signal
            entry_price = current_price
            trade_size = capital * position_size
            
            if signal == 'LONG':
                sl_price = entry_price * (1 - stop_loss)
                tp_price = entry_price * (1 + take_profit)
            else:
                sl_price = entry_price * (1 + stop_loss)
                tp_price = entry_price * (1 - take_profit)
        
        # 平仓检查
        elif in_position:
            pnl_pct = 0
            
            if position_type == 'LONG':
                pnl_pct = (current_price - entry_price) / entry_price
                if current_price <= entry_price * (1 - stop_loss):
                    pnl_pct = -stop_loss
                    in_position = False
                elif current_price >= entry_price * (1 + take_profit):
                    pnl_pct = take_profit
                    in_position = False
            else:  # SHORT
                pnl_pct = (entry_price - current_price) / entry_price
                if current_price >= entry_price * (1 + stop_loss):
                    pnl_pct = -stop_loss
                    in_position = False
                elif current_price <= entry_price * (1 - take_profit):
                    pnl_pct = take_profit
                    in_position = False
            
            if not in_position:
                pnl = trade_size * pnl_pct
                capital += pnl
                trades.append({
                    'symbol': symbol,
                    'type': position_type,
                    'entry': entry_price,
                    'exit': current_price,
                    'pnl_pct': pnl_pct * 100,
                    'pnl': pnl
                })
    
    total_pnl = capital - 10000
    win_trades = [t for t in trades if t['pnl'] > 0]
    win_rate = len(win_trades) / len(trades) * 100 if trades else 0
    
    return {
        'symbol': symbol,
        'params': params,
        'initial_capital': 10000,
        'final_capital': capital,
        'total_pnl': total_pnl,
        'total_pnl_pct': (total_pnl / 10000) * 100,
        'num_trades': len(trades),
        'win_rate': win_rate,
        'trades': trades
    }

def main():
    print("🦞 第 7 轮策略优化启动！")
    print("=" * 50)
    print(f"📊 参数组合：{len(PARAM_GRID['ma_short']) * len(PARAM_GRID['ma_long']) * len(PARAM_GRID['rsi_period']) * len(PARAM_GRID['adx_filter']) * len(PARAM_GRID['stop_loss']) * len(PARAM_GRID['take_profit']) * len(PARAM_GRID['position_size'])} 种")
    print(f"🪙 币种：{len(SYMBOLS)} 个")
    print(f"📂 结果目录：{RESULTS_DIR}")
    print("-" * 50)
    
    all_results = []
    
    # 遍历参数组合
    param_combinations = []
    for ma_s in PARAM_GRID['ma_short']:
        for ma_l in PARAM_GRID['ma_long']:
            for rsi in PARAM_GRID['rsi_period']:
                for adx in PARAM_GRID['adx_filter']:
                    for sl in PARAM_GRID['stop_loss']:
                        for tp in PARAM_GRID['take_profit']:
                            for pos in PARAM_GRID['position_size']:
                                param_combinations.append({
                                    'ma_short': ma_s,
                                    'ma_long': ma_l,
                                    'rsi_period': rsi,
                                    'adx_filter': adx,
                                    'stop_loss': sl,
                                    'take_profit': tp,
                                    'position_size': pos
                                })
    
    print(f"🎯 测试 {len(param_combinations)} 个参数组合...")
    
    # 测试前 20 个组合（节省时间）
    for idx, params in enumerate(param_combinations[:20]):
        print(f"\n📊 组合 {idx+1}/20: MA{params['ma_short']}/{params['ma_long']}, RSI{params['rsi_period']}, ADX{params['adx_filter']}")
        
        symbol_results = []
        
        for symbol in SYMBOLS:
            print(f"  获取 {symbol} 数据...")
            data = fetch_klines(symbol, INTERVAL, LIMIT)
            
            if not data:
                continue
            
            print(f"  回测中...")
            result = run_backtest(symbol, params, data)
            symbol_results.append(result)
            print(f"    收益：{result['total_pnl_pct']:.2f}%, 胜率：{result['win_rate']:.1f}%, 交易：{result['num_trades']} 次")
        
        # 计算平均表现
        if symbol_results:
            avg_return = sum(r['total_pnl_pct'] for r in symbol_results) / len(symbol_results)
            avg_wr = sum(r['win_rate'] for r in symbol_results) / len(symbol_results)
            total_trades = sum(r['num_trades'] for r in symbol_results)
            
            combined_result = {
                'params': params,
                'avg_return': avg_return,
                'avg_win_rate': avg_wr,
                'total_trades': total_trades,
                'symbol_results': symbol_results
            }
            
            all_results.append(combined_result)
            print(f"  ✅ 平均收益：{avg_return:.2f}%, 平均胜率：{avg_wr:.1f}%")
    
    # 排序并保存最佳结果
    all_results.sort(key=lambda x: x['avg_return'], reverse=True)
    
    # 保存完整结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"{RESULTS_DIR}/round7_results_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # 生成简报
    report = f'''# 🦞 第 7 轮策略优化报告

**时间：** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**测试组合：** 20 个（总组合数：{len(param_combinations)}）
**币种：** {', '.join(SYMBOLS)}

---

## 🏆 Top 5 最佳参数组合

| 排名 | 平均收益 | 平均胜率 | 交易次数 | MA | RSI | ADX | SL | TP | 仓位 |
|------|----------|----------|----------|----|-----|-----|----|----|------|
'''
    
    for i, result in enumerate(all_results[:5], 1):
        p = result['params']
        report += f"| {i} | {result['avg_return']:.2f}% | {result['avg_win_rate']:.1f}% | {result['total_trades']} | {p['ma_short']}/{p['ma_long']} | {p['rsi_period']} | {p['adx_filter']} | {p['stop_loss']*100:.1f}% | {p['take_profit']*100:.0f}% | {p['position_size']*100:.0f}% |\n"
    
    report += f'''
---

## 📊 详细数据

**最佳组合：**
- MA: {all_results[0]['params']['ma_short']}/{all_results[0]['params']['ma_long']}
- RSI: {all_results[0]['params']['rsi_period']}
- ADX: {all_results[0]['params']['adx_filter']}
- SL: {all_results[0]['params']['stop_loss']*100:.1f}%
- TP: {all_results[0]['params']['take_profit']*100:.0f}%
- 仓位：{all_results[0]['params']['position_size']*100:.0f}%
- 平均收益：{all_results[0]['avg_return']:.2f}%
- 平均胜率：{all_results[0]['avg_win_rate']:.1f}%

---

## 📂 文件位置

- 完整结果：`{results_file}`
- 结果目录：`{RESULTS_DIR}/`

---

_下一轮：第 8 轮（基于 R7 最优参数继续优化）_
'''
    
    report_file = f"{RESULTS_DIR}/round7_report_{timestamp}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "=" * 50)
    print(f"🎉 第 7 轮优化完成！")
    print(f"📄 报告：{report_file}")
    print(f"📊 数据：{results_file}")
    print(f"\n🏆 最佳收益：{all_results[0]['avg_return']:.2f}%")

if __name__ == "__main__":
    main()
