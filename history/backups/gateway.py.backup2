#!/usr/bin/env python3
"""
🦞 统一网关服务 - 8080 端口
同时提供静态文件服务和 API 代理服务
用户只需访问 8080 端口即可
"""

from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
import requests
import json
import os
import sys
import hmac
import hashlib
import time

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.config import load_api_keys, get_active_api_key, load_strategies, save_strategies
from api.binance_client import BinanceClient
from api.sim_account import SimulatedAccount
from api.strategy_engine import strategy_engine
from api.trading_record import trading_record
from api.telegram_notifier import telegram_notifier
from api.auto_sim_executor import auto_sim_executor

# 定时任务
import schedule
import time
import threading

# 初始化 Flask
app = Flask(__name__, static_folder='/home/admin/.openclaw/workspace/quant')
CORS(app)

# 初始化模拟账户
sim_account = SimulatedAccount(initial_capital=100.0)

# ==================== 静态文件服务 ====================

@app.route('/')
def index():
    """导航页面"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/pages/<path:filename>')
def pages(filename):
    """页面文件"""
    return send_from_directory(os.path.join(app.static_folder, 'pages'), filename)

@app.route('/<path:filename>')
def static_files(filename):
    """其他静态文件"""
    return send_from_directory(app.static_folder, filename)

# ==================== API 代理服务 ====================

@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'success': True,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'version': 'v2.1'
    })

# --- 测试网 API ---

@app.route('/api/testnet/account')
def testnet_account():
    """测试网账户（真实 API 获取 - 返回所有资产）"""
    api_key = {
        'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
        'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
    }
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    result = client.get_futures_account()
    
    # 币安 API 直接返回资产列表
    if isinstance(result, dict) and result.get('success') and 'assets' in result:
        assets = result['assets']
        total_balance = result.get('totalBalance', 0)
        
        # 构建所有资产列表
        balances = []
        for a in assets:
            asset = a.get('asset', '')
            balance = float(a.get('balance', 0))
            available = float(a.get('availableBalance', 0))
            if balance > 0:
                balances.append({
                    'asset': asset,
                    'free': available,
                    'locked': balance - available,
                    'total': balance
                })
        
        # 按余额排序（USDT 优先）
        balances.sort(key=lambda x: (x['asset'] not in ['USDT', 'USDC', 'BTC'], -x['total']))
        
        return jsonify({
            'success': True,
            'account': {
                'balances': balances,
                'total_balance': total_balance,
                'canTrade': True,
                'source': 'binance_testnet_usds',
                'account_type': 'U 本位合约',
                'asset_count': len(balances)
            }
        })
    
    # 默认返回 10000 USDT
    return jsonify({
        'success': True,
        'account': {
            'balances': [{
                'asset': 'USDT',
                'free': 10000,
                'locked': 0,
                'total': 10000
            }],
            'canTrade': True,
            'source': 'default'
        }
    })

@app.route('/api/testnet/prices')
def testnet_prices():
    """测试网价格"""
    api_key = {
        'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
        'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
    }
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    
    prices = {}
    for symbol in ['BTCUSDT', 'ETHUSDT', 'LINKUSDT', 'UNIUSDT']:
        result = client.get_spot_price(symbol)
        prices[symbol] = result.get('price', 0) if result.get('success') else 0
    
    return jsonify({
        'success': True,
        'prices': prices
    })

@app.route('/api/testnet/positions')
def testnet_positions():
    """测试网持仓"""
    api_key = {
        'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
        'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
    }
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    result = client.get_futures_positions()
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'positions': result.get('positions', [])
        })
    
    return jsonify({
        'success': True,
        'positions': []
    })

# --- 实盘 API ---

@app.route('/api/real/account')
def real_account():
    """实盘账户"""
    api_key = get_active_api_key(testnet=False)
    
    if not api_key:
        return jsonify({
            'success': True,
            'account': {
                'balances': [],
                'canTrade': False
            },
            'message': '未配置 API Key'
        })
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=False)
    spot = client.get_spot_account()
    futures = client.get_futures_account()
    
    balances = []
    
    if spot.get('success') and spot.get('balances'):
        for b in spot['balances']:
            free = float(b.get('free', 0))
            locked = float(b.get('locked', 0))
            if free > 0 or locked > 0:
                balances.append({
                    'asset': b['asset'],
                    'free': free,
                    'locked': locked,
                    'total': free + locked,
                    'type': '现货'
                })
    
    if futures.get('success'):
        usdt = next((a for a in futures.get('assets', []) if a['asset'] == 'USDT'), None)
        if usdt:
            available = float(usdt.get('availableBalance', 0))
            total = float(usdt.get('walletBalance', 0))
            existing = next((b for b in balances if b['asset'] == 'USDT'), None)
            if existing:
                existing['futures_available'] = available
                existing['futures_total'] = total
            else:
                balances.append({
                    'asset': 'USDT',
                    'free': available,
                    'locked': total - available,
                    'total': total,
                    'type': '合约'
                })
    
    return jsonify({
        'success': True,
        'account': {
            'balances': balances,
            'canTrade': True
        }
    })

@app.route('/api/real/prices')
def real_prices():
    """实盘价格"""
    api_key = get_active_api_key(testnet=False)
    
    if not api_key:
        return jsonify({'success': True, 'prices': {}})
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=False)
    
    prices = {}
    for symbol in ['BTCUSDT', 'ETHUSDT', 'LINKUSDT', 'UNIUSDT']:
        result = client.get_spot_price(symbol)
        prices[symbol] = result.get('price', 0) if result.get('success') else 0
    
    return jsonify({
        'success': True,
        'prices': prices
    })

@app.route('/api/real/positions')
def real_positions():
    """实盘持仓"""
    api_key = get_active_api_key(testnet=False)
    
    if not api_key:
        return jsonify({
            'success': True,
            'positions': [],
            'message': '未配置 API Key'
        })
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=False)
    result = client.get_futures_positions()
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'positions': result.get('positions', [])
        })
    
    return jsonify({
        'success': True,
        'positions': [],
        'message': result.get('error', '获取失败')
    })

# --- 策略 API ---

@app.route('/api/strategy/list')
def strategy_list():
    """策略列表"""
    strategies = strategy_engine.get_active_strategies()
    return jsonify({
        'success': True,
        'strategies': strategies,
        'count': len(strategies)
    })

@app.route('/api/strategy/start', methods=['POST'])
def strategy_start():
    """启动策略（实际下单）"""
    data = request.json
    account_type = data.get('account_type', '测试盘')
    
    symbol = data.get('symbol', 'ETHUSDT')
    strategy_name = data.get('strategy', 'v23')
    
    # 自动交易模拟策略默认开多，其他策略默认开空
    if strategy_name == 'auto_sim':
        side = data.get('side', 'long')
    else:
        side = data.get('side', 'short')
    
    # 初始化 entry_price（稍后会被实际成交价更新）
    entry_price = 0
    
    # 🔴 开单前检查币安持仓（防止重复开仓）
    api_key = {
        'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
        'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
    }
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    
    # 获取当前价格（用于计算数量和止损）
    price_result = client.get_spot_price(symbol)
    current_price = float(price_result.get('price', 0))
    
    # 根据金额和杠杆计算数量
    amount = float(data.get('amount', 500))
    leverage = int(data.get('leverage', 1))
    
    if current_price > 0:
        quantity = (amount * leverage) / current_price
    else:
        quantity = 0.01
    
    # 检查 1：是否有持仓
    positions = client.get_futures_positions()
    if positions.get('success') and positions.get('positions'):
        for pos in positions['positions']:
            if pos['symbol'] == symbol and pos['size'] > 0:
                # 已有持仓，拒绝启动
                return jsonify({
                    'success': False,
                    'error': f'{symbol} 已有持仓（{pos["side"]} {pos["size"]}），不能启动新策略，请先平仓',
                    'existing_position': pos
                })
    
    # 检查 2：是否有活跃止损单 ← 新增
    algo_orders = client.get_algo_orders(symbol=symbol, limit=10)
    if algo_orders.get('success') and algo_orders.get('orders'):
        active_orders = [o for o in algo_orders['orders'] if o.get('algoStatus') == 'NEW']
        if len(active_orders) > 0:
            order_info = []
            for order in active_orders:
                order_info.append({
                    'algoId': order['algoId'],
                    'type': order.get('orderType', 'UNKNOWN'),
                    'triggerPrice': order.get('triggerPrice', '0'),
                    'side': order.get('side', 'UNKNOWN')
                })
            
            return jsonify({
                'success': False,
                'error': f'{symbol} 有{len(active_orders)}个活跃止损单，请先取消',
                'existing_orders': order_info
            })
    
    # 先设置杠杆
    leverage = int(data.get('leverage', 1))
    if leverage < 1 or leverage > 5:
        leverage = 1  # 安全限制
    
    leverage_result = client.set_futures_leverage(symbol, leverage)
    if leverage_result.get('success'):
        print(f"✅ 杠杆已设置为 {leverage}x")
    else:
        print(f"⚠️ 设置杠杆失败：{leverage_result.get('error')}，使用默认值")
    
    # 🔴 先下单获取实际成交价
    order_result = client.place_futures_order(
        symbol=symbol,
        side='SELL' if side == 'short' else 'BUY',
        order_type='MARKET',
        quantity=quantity,
        newOrderRespType='FULL'  # ← 获取完整成交信息
    )
    
    # 从 fills 中获取实际成交价和数量
    actual_price = current_price
    actual_quantity = quantity
    
    if order_result.get('success') and order_result.get('order'):
        order_data = order_result['order']
        # 使用 fills 数组（最精确）
        if order_data.get('fills'):
            fills = order_data['fills']
            total_qty = sum(float(f['qty']) for f in fills)
            total_value = sum(float(f['price']) * float(f['qty']) for f in fills)
            if total_qty > 0:
                actual_quantity = total_qty
                actual_price = total_value / total_qty
                print(f"✅ 从 fills 获取：price={actual_price}, qty={actual_quantity}")
    
    # 🔴 用实际成交价创建策略
    result = strategy_engine.start_strategy(
        symbol=symbol,
        strategy=strategy_name,
        side=side,
        entry_price=actual_price,  # ← 使用实际成交价
        quantity=actual_quantity  # ← 使用实际成交数量
    )
        
    # 创建交易记录（开仓）
    if order_result.get('success'):
            # 🔴 从 fills 中获取实际成交价和数量（最精确）
            order_data = order_result.get('order', {})
            actual_price = current_price if current_price > 0 else 0
            actual_quantity = quantity
            
            print(f"📊 订单返回数据：{bool(order_data)}")
            print(f"📊 current_price={current_price}, quantity={quantity}")
            
            if order_data:
                # 方法 1：使用 fills 数组（最精确）
                if order_data.get('fills'):
                    fills = order_data['fills']
                    total_qty = sum(float(f['qty']) for f in fills)
                    total_value = sum(float(f['price']) * float(f['qty']) for f in fills)
                    if total_qty > 0:
                        actual_quantity = total_qty
                        actual_price = total_value / total_qty
                        print(f"✅ 从 fills 获取：price={actual_price}, qty={actual_quantity}")
                
                # 方法 2：使用 executedQty 和 cummulativeQuoteQty
                elif order_data.get('executedQty') and float(order_data['executedQty']) > 0:
                    actual_quantity = float(order_data['executedQty'])
                    if order_data.get('cummulativeQuoteQty') and float(order_data['cummulativeQuoteQty']) > 0:
                        actual_price = float(order_data['cummulativeQuoteQty']) / actual_quantity
                    print(f"✅ 从 executedQty 获取：price={actual_price}, qty={actual_quantity}")
            
            # 确保 actual_price 和 actual_quantity 不为 0
            if actual_price <= 0:
                actual_price = current_price if current_price > 0 else 0
            if actual_quantity <= 0:
                actual_quantity = quantity
            
            print(f"📊 最终：price={actual_price}, qty={actual_quantity}")
            
            # 🔴 更新策略引擎数据（同步实际成交信息）
            result['entry_price'] = actual_price
            result['quantity'] = actual_quantity
            result['leverage'] = leverage
            
            # 🔴 同步更新策略引擎中的策略（重要！）
            print(f"📊 策略引擎策略数量：{len(strategy_engine.strategies)}")
            for s in strategy_engine.strategies:
                if s['symbol'] == symbol and s['status'] == '运行中':
                    print(f"✅ 更新策略数据：entry_price={actual_price}, quantity={actual_quantity}, leverage={leverage}")
                    s['entry_price'] = actual_price
                    s['quantity'] = actual_quantity
                    s['leverage'] = leverage
                    strategy_engine.save_strategies()
                    print(f"✅ 策略数据已保存")
                    break
            
            # 同步设置止损单（默认 5%）
            stop_loss_pct = 0.05  # 5% 止损
            if side == 'long':
                stop_price = round(actual_price * (1 - stop_loss_pct), 2)  # 四舍五入到 2 位
                stop_side = 'SELL'  # 多单止损方向
            else:
                stop_price = round(actual_price * (1 + stop_loss_pct), 2)  # 四舍五入到 2 位
                stop_side = 'BUY'   # 空单止损方向
            
            # 🔴 使用 STOP_MARKET 类型设置止损单
            stop_result = client.place_futures_order(
                symbol=symbol,
                side=stop_side,
                order_type='STOP_MARKET',  # ← 触发后市价平仓
                quantity=actual_quantity,
                stopPrice=stop_price,  # ← 触发价格
                reduceOnly=True,  # ← 只减仓
                newOrderRespType='FULL'  # ← 获取完整信息
            )
            
            # 🔴 记录止损单结果
            if stop_result.get('success') and stop_result.get('order'):
                stop_order_id = stop_result['order'].get('orderId')
                print(f"✅ 止损单已设置：ID={stop_order_id}, 价格=${stop_price}")
            else:
                stop_order_id = None
                error_msg = stop_result.get('msg', stop_result.get('error', '未知错误'))
                print(f"❌ 止损单失败：{error_msg}")
                print(f"   参数：symbol={symbol}, side={stop_side}, qty={actual_quantity}, stop_price={stop_price}")
            
            # 记录止损单信息
            
            trade = trading_record.create_trade_record(
                symbol=symbol,
                side=side.upper(),
                action='OPEN',
                quantity=quantity,
                price=entry_price,
                strategy=strategy_name,
                signal_reason='策略启动',
                status='executed',
                stop_loss_price=stop_price,
                stop_order_id=stop_order_id
            )
            
            # 发送 Telegram 通知（含止损信息）
            telegram_notifier.send_strategy_started(
                symbol=symbol,
                side=side,
                price=entry_price,
                quantity=quantity,
                strategy=strategy_name,
                account_type=account_type,
                stop_loss=stop_price
            )
            
            return jsonify({
                'success': True,
                'message': '策略已启动并下单（含止损）',
                'strategy': result,
                'order': order_result,
                'stop_loss': stop_result,
                'trade_id': trade['id']
            })
        else:
            # 下单失败，回滚策略
            strategy_engine.stop_strategy(symbol)
            return jsonify({
                'success': False,
                'error': f'下单失败：{order_result.get("error", "未知错误")}'
            }), 500
    else:
        # 互斥检查失败
        return jsonify({
            'success': False,
            'error': result.get('error', '启动失败'),
            'existing_strategy': result.get('existing_strategy')
        }), 400

@app.route('/api/strategy/stop', methods=['POST'])
def strategy_stop():
    """停止策略（平仓）"""
    data = request.json
    account_type = data.get('account_type', '测试盘')
    symbol = data.get('symbol')
    
    # 获取策略信息
    strategies = strategy_engine.get_active_strategies()
    strategy = next((s for s in strategies if s['symbol'] == symbol), None)
    
    if not strategy:
        return jsonify({
            'success': False,
            'error': '未找到活跃策略'
        }), 404
    
    try:
        # 获取当前价格
        api_key = {
            'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
            'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
        }
        client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
        price_result = client.get_spot_price(symbol)
        current_price = price_result.get('price', strategy['entry_price']) if price_result.get('success') else strategy['entry_price']
        
        # 平仓下单
        order_result = None
        try:
            order_side = 'BUY' if strategy['side'] == 'short' else 'SELL'
            order_result = client.place_futures_order(
                symbol=symbol,
                side=order_side,
                order_type='MARKET',
                quantity=strategy.get('quantity', 0.01)
            )
        except Exception as e:
            print(f"⚠️ 平仓下单失败：{e}")
            order_result = {'success': False, 'error': str(e)}
        
        # 计算盈亏（添加除零检查）
        entry_price = strategy.get('entry_price', 0)
        quantity = strategy.get('quantity', 0.01)
        if entry_price > 0 and quantity > 0:
            pnl_pct = (strategy['pnl'] / (entry_price * quantity)) * 100
        else:
            pnl_pct = 0
        
        # 创建交易记录
        trade = trading_record.create_trade_record(
            symbol=symbol,
            side=strategy['side'].upper(),
            action='CLOSE',
            quantity=strategy.get('quantity', 0.01),
            price=current_price,
            strategy=strategy['strategy'],
            signal_reason='手动平仓',
            pnl=strategy['pnl'],
            pnl_pct=pnl_pct,
            status='executed'
        )
        
        # 取消所有 Algo 订单
        algo_orders = client.get_algo_orders(symbol=symbol, limit=10)
        cancelled_count = 0
        if algo_orders.get('success'):
            for order in algo_orders.get('orders', []):
                if order.get('algoStatus') == 'NEW':
                    client.cancel_algo_order(symbol, order['algoId'])
                    cancelled_count += 1
                    print(f"✅ 已取消止损单：{order['algoId']}")
        
        # 关闭策略
        strategy_engine.stop_strategy(symbol)
        
        # 发送通知
        telegram_notifier.send_strategy_stopped(
            symbol=symbol,
            pnl=strategy['pnl'],
            pnl_pct=pnl_pct,
            entry_price=strategy['entry_price'],
            exit_price=current_price,
            account_type=account_type
        )
        
        # 返回结果
        return jsonify({
            'success': True,
            'message': '策略已停止',
            'pnl': strategy['pnl'],
            'pnl_pct': pnl_pct,
            'cancelled_orders': cancelled_count
        })
        
    except Exception as e:
        print(f"❌ 停止策略失败：{e}")
        # 即使报错也尝试关闭策略
        try:
            strategy_engine.stop_strategy(symbol)
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': f'停止失败：{str(e)}'
        }), 500

@app.route('/api/strategy/reset', methods=['POST'])
def strategy_reset():
    """重置策略引擎（清空所有策略）"""
    try:
        # 清空策略文件
        import json
        with open('/tmp/strategies_v6.json', 'w') as f:
            json.dump([], f)
        
        # 清空内存中的策略
        strategy_engine.strategies = []
        
        print("✅ 策略引擎已重置")
        
        return jsonify({
            'success': True,
            'message': '策略已重置'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route('/api/strategy/signals', methods=['POST'])
def strategy_signals():
    """生成策略信号"""
    data = request.json
    symbol = data.get('symbol', 'ETHUSDT')
    
    # 获取当前价格
    api_key = {
        'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
        'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
    }
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    price_result = client.get_spot_price(symbol)
    
    if not price_result.get('success'):
        return jsonify({'success': False, 'error': '无法获取价格'})
    
    current_price = price_result['price']
    
    # 更新策略盈亏
    strategies = strategy_engine.get_active_strategies()
    for strategy in strategies:
        if strategy['symbol'] == symbol:
            strategy_engine.update_strategy_pnl(symbol, current_price)
    
    # 生成信号
    signal = strategy_engine.generate_signal(symbol, 'v23 高频', current_price)
    
    return jsonify({
        'success': True,
        'current_price': current_price,
        'signal': signal,
        'strategies': strategy_engine.get_active_strategies()
    })

@app.route('/api/strategy/execute', methods=['POST'])
def strategy_execute():
    """执行交易信号"""
    data = request.json
    signal = data.get('signal')
    
    if not signal:
        return jsonify({'success': False, 'error': '缺少信号参数'})
    
    # 获取测试网 API 客户端
    api_key = {
        'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
        'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
    }
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    
    # 执行信号（带交易记录）
    result = strategy_engine.execute_signal(signal, api_client=client)
    return jsonify(result)

# --- Telegram 配置 API ---

@app.route('/api/telegram/config', methods=['GET'])
def get_telegram_config():
    """获取 Telegram 配置状态"""
    if telegram_notifier.config:
        return jsonify({
            'success': True,
            'configured': True,
            'chat_id': telegram_notifier.config.get('chat_id', '')
        })
    return jsonify({
        'success': True,
        'configured': False
    })

@app.route('/api/telegram/config', methods=['POST'])
def set_telegram_config():
    """设置 Telegram 配置"""
    data = request.json
    bot_token = data.get('bot_token')
    chat_id = data.get('chat_id')
    
    if not bot_token or not chat_id:
        return jsonify({
            'success': False,
            'error': '缺少 bot_token 或 chat_id'
        })
    
    telegram_notifier.save_config(bot_token, chat_id)
    
    # 发送测试消息
    telegram_notifier.send_message("""
✅ **Telegram 通知已配置**

🦞 币安量化交易系统
📊 通知服务已启用

✅ 配置成功
""")
    
    return jsonify({
        'success': True,
        'message': 'Telegram 配置已保存'
    })

@app.route('/api/telegram/test', methods=['POST'])
def test_telegram():
    """测试 Telegram 通知"""
    data = request.json
    account_type = data.get('account_type', '测试盘')
    
    # 获取账户信息
    try:
        resp = requests.get('http://localhost:8080/api/testnet/account')
        account_data = resp.json()
        usdt = next((b for b in account_data.get('account', {}).get('balances', []) if b['asset'] == 'USDT'), None)
        total = usdt['total'] if usdt else 0
        
        telegram_notifier.send_asset_update(
            account_type=account_type,
            total_value=total,
            available=usdt['free'] if usdt else 0,
            positions_value=0,
            unrealized_pnl=0
        )
        
        return jsonify({
            'success': True,
            'message': '测试消息已发送'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/trades')
def get_trades():
    """获取交易记录（本地记录）"""
    limit = int(request.args.get('limit', 50))
    symbol = request.args.get('symbol')
    status = request.args.get('status')
    
    trades = trading_record.get_trades(limit=limit, symbol=symbol, status=status)
    return jsonify({
        'success': True,
        'trades': trades,
        'count': len(trades)
    })

@app.route('/api/binance/trades')
def get_binance_trades():
    """获取币安真实成交记录"""
    limit = int(request.args.get('limit', 50))
    symbol = request.args.get('symbol')
    
    api_key = {
        'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
        'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
    }
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    result = client.get_futures_order_trades(symbol=symbol, limit=limit)
    
    return jsonify(result)

@app.route('/api/binance/algo-orders')
def get_algo_orders():
    """获取 Algo 订单（止损单/止盈单）"""
    limit = int(request.args.get('limit', 50))
    symbol = request.args.get('symbol')
    
    api_key = {
        'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
        'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
    }
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    result = client.get_algo_orders(symbol=symbol, limit=limit)
    
    return jsonify(result)

@app.route('/api/binance/algo-orders/cancel', methods=['POST'])
def cancel_algo_order():
    """取消 Algo 订单"""
    data = request.json
    symbol = data.get('symbol')
    algo_id = data.get('algoId')
    
    if not symbol or not algo_id:
        return jsonify({'success': False, 'error': '缺少 symbol 或 algoId'})
    
    api_key = {
        'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
        'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
    }
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    result = client.cancel_algo_order(symbol, algo_id)
    
    return jsonify(result)

@app.route('/api/trades/stats')
def get_trade_stats():
    """获取交易统计"""
    symbol = request.args.get('symbol')
    stats = trading_record.get_trade_stats(symbol=symbol)
    return jsonify({
        'success': True,
        'stats': stats
    })

@app.route('/api/trades/<int:trade_id>')
def get_trade(trade_id):
    """获取单条交易记录"""
    trades = trading_record.get_trades(limit=1000)
    trade = next((t for t in trades if t['id'] == trade_id), None)
    
    if trade:
        return jsonify({'success': True, 'trade': trade})
    return jsonify({'success': False, 'error': '交易记录不存在'}), 404

# --- 配置 API ---

@app.route('/api/config/apis')
def get_apis():
    """获取 API Key 列表"""
    keys = load_api_keys()
    masked = []
    for k in keys:
        m = k.copy()
        if 'api_key' in m:
            m['api_key_masked'] = '***' + m['api_key'][-4:] if len(m['api_key']) > 4 else '***'
        if 'secret_key' in m:
            del m['secret_key']
        masked.append(m)
    return jsonify({'success': True, 'apis': masked})

@app.route('/api/config/apis', methods=['POST'])
def add_api():
    """添加 API Key"""
    from api.config import save_api_keys
    data = request.json
    keys = load_api_keys()
    
    new_key = {
        'name': data.get('name', '未命名'),
        'api_key': data.get('api_key', ''),
        'secret_key': data.get('secret_key', ''),
        'exchange': data.get('exchange', 'binance'),
        'testnet': data.get('testnet', False),
        'active': len(keys) == 0
    }
    
    keys.append(new_key)
    save_api_keys(keys)
    
    return jsonify({'success': True, 'message': 'API 已添加'})

# ==================== 主程序 ====================


# ==================== 定时任务：auto_sim 策略 ====================

def execute_auto_sim_cycles():
    """每分钟执行 auto_sim 策略循环"""
    try:
        api_key = get_active_api_key(testnet=True)
        if not api_key:
            return
        client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
        
        for symbol in list(auto_sim_executor.simulators.keys()):
            try:
                prices = client.get_futures_prices()
                current_price = next((p['price'] for p in prices.get('prices', []) if p['symbol'] == symbol), None)
                if current_price:
                    auto_sim_executor.execute_cycle(symbol, float(current_price))
            except Exception as e:
                print(f"❌ auto_sim 执行失败 {symbol}: {e}")
    except Exception as e:
        print(f"❌ 定时任务执行失败：{e}")

def start_scheduler():
    """启动定时任务调度器"""
    schedule.every(1).minutes.do(execute_auto_sim_cycles)
    print("✅ 定时任务已启动：auto_sim 策略每分钟执行一次")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # 清空策略文件（防止损坏策略）
    import json
    try:
        with open('/tmp/strategies_v6.json', 'w') as f:
            json.dump([], f)
        print("✅ 策略文件已清空")
    except:
        pass
    
    print("🦞 启动统一网关服务...")
    print("访问地址：http://localhost:8080")
    print("\n所有功能通过 8080 端口访问:")
    print("  静态文件：http://localhost:8080/pages/testnet.html")
    print("  API 代理：http://localhost:8080/api/testnet/account")
    print("  策略管理：http://localhost:8080/api/strategy/list")
    print()
    
    # 启动定时任务线程
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ 定时任务线程已启动")
    

    app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)

@app.route('/api/testnet/accounts')
def testnet_all_accounts():
    """测试网所有账户资产（现货+U 本位 + 币本位）"""
    api_key = {
        'api_key': 'EPmptIkZOR4vKgnx2oqZXwRSKFUriXnYGwf8x0oXWdvFE5ypzbyANlOj8oJp0lxj',
        'secret_key': '2uc3OTTTZbuQqbIrDKW4gebZsM6Ja3I9cx733SzlYg1wdnliTvmeF0djwzUbYFJx'
    }
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    
    # 1. U 本位合约账户
    usds_result = client.get_futures_account()
    usds_balances = []
    if isinstance(usds_result, dict) and usds_result.get('success') and 'assets' in usds_result:
        for a in usds_result['assets']:
            balance = float(a.get('balance', 0))
            available = float(a.get('availableBalance', 0))
            if balance > 0:
                usds_balances.append({
                    'asset': a.get('asset', ''),
                    'free': available,
                    'locked': balance - available,
                    'total': balance
                })
    
    # 按余额排序
    usds_balances.sort(key=lambda x: (x['asset'] not in ['USDT', 'USDC', 'BTC'], -x['total']))
    
    # 2. 现货账户（暂空）
    spot_balances = []
    
    # 3. 币本位合约账户（暂空）
    coin_balances = []
    
    return jsonify({
        'success': True,
        'accounts': {
            'spot': {'balances': spot_balances, 'count': len(spot_balances), 'name': '现货账户'},
            'usds': {'balances': usds_balances, 'count': len(usds_balances), 'name': 'U 本位合约'},
            'coin': {'balances': coin_balances, 'count': len(coin_balances), 'name': '币本位合约'}
        }
    })
