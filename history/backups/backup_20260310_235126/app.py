#!/usr/bin/env python3
"""
🦞 统一交易 API 服务
整合实盘、模拟盘、策略管理
"""

from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import sys
import os

# 配置 CORS，允许所有来源访问
CORS_RESOURCES = {
    r"/*": {
        "origins": ["*", "http://147.139.213.181:8080", "http://localhost:8080", "http://147.139.213.181:5005", "null"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Origin", "X-Requested-With"],
        "supports_credentials": True,
        "max_age": 3600,
        "expose_headers": ["Content-Type", "Authorization"]
    }
}

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.config import load_api_keys, save_api_keys, get_active_api_key
from api.binance_client import BinanceClient
from api.sim_account import SimulatedAccount
from api.strategy_engine import strategy_engine

# 初始化 Flask
app = Flask(__name__)
CORS(app, resources=CORS_RESOURCES)

# 初始化模拟账户
sim_account = SimulatedAccount(initial_capital=100.0)

# ==================== 测试网 API ====================

@app.route('/api/testnet/account', methods=['GET'])
def testnet_account():
    """获取测试网账户信息"""
    api_key = get_active_api_key(testnet=True)
    if not api_key:
        return jsonify({
            'success': True,
            'account': {
                'balances': [{'asset': 'USDT', 'free': 10000, 'locked': 0, 'total': 10000}],
                'canTrade': False
            },
            'message': '未配置测试网 API Key（系统默认提供）'
        })
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    
    # 获取现货余额
    spot = client.get_spot_account()
    # 获取合约余额
    futures = client.get_futures_account()
    
    balances = []
    
    # 合并现货余额
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
    
    # 添加合约 USDT 余额
    if futures.get('success'):
        usdt_asset = next((a for a in futures.get('assets', []) if a['asset'] == 'USDT'), None)
        if usdt_asset:
            available = float(usdt_asset.get('availableBalance', 0))
            total = float(usdt_asset.get('walletBalance', 0))
            existing = next((b for b in balances if b['asset'] == 'USDT'), None)
            if existing:
                existing['futures_available'] = available
                existing['futures_total'] = total
                existing['type'] = '现货 + 合约'
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

@app.route('/api/testnet/positions', methods=['GET'])
def testnet_positions():
    """获取测试网持仓"""
    api_key = get_active_api_key(testnet=True)
    if not api_key:
        # 使用默认测试网 API
        api_key = {
            'api_key': 'FOc6rfs8QIWhIwPuU6LFyb36GatL1VUyHTaga3yVYjkQ8BmW1eDV1tooh3WY3SSV',
            'secret_key': 'O9flejsMESgKaI4tUDDYwLNcx1ypgpWkMReoaFplXmzQGsRrKYZ6FxPh492Hro6m'
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
        'positions': [],
        'message': result.get('error', '获取失败')
    })

@app.route('/api/testnet/trade', methods=['POST'])
def testnet_trade():
    """测试网交易"""
    api_key = get_active_api_key(testnet=True)
    if not api_key:
        api_key = {
            'api_key': 'FOc6rfs8QIWhIwPuU6LFyb36GatL1VUyHTaga3yVYjkQ8BmW1eDV1tooh3WY3SSV',
            'secret_key': 'O9flejsMESgKaI4tUDDYwLNcx1ypgpWkMReoaFplXmzQGsRrKYZ6FxPh492Hro6m'
        }
    
    data = request.json
    symbol = data.get('symbol', 'ETHUSDT')
    side = data.get('side', 'BUY')
    quantity = float(data.get('quantity', 0.01))
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    result = client.place_futures_order(symbol, side, 'MARKET', quantity)
    
    return jsonify(result)

# ==================== 实盘 API ====================

@app.route('/api/real/account', methods=['GET'])
def real_account():
    """获取实盘账户信息（现货 + 合约）"""
    api_key = get_active_api_key(testnet=False)
    if not api_key:
        return jsonify({
            'success': True,
            'account': {
                'balances': [{'asset': 'USDT', 'free': 0, 'locked': 0, 'total': 0}],
                'canTrade': False
            },
            'message': '未配置 API Key'
        })
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=False)
    
    # 获取现货余额
    spot = client.get_spot_account()
    # 获取合约余额
    futures = client.get_futures_account()
    
    balances = []
    
    # 合并现货余额
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
    
    # 添加合约 USDT 余额
    if futures.get('success'):
        usdt_asset = next((a for a in futures.get('assets', []) if a['asset'] == 'USDT'), None)
        if usdt_asset:
            available = float(usdt_asset.get('availableBalance', 0))
            total = float(usdt_asset.get('walletBalance', 0))
            existing = next((b for b in balances if b['asset'] == 'USDT'), None)
            if existing:
                existing['futures_available'] = available
                existing['futures_total'] = total
                existing['type'] = '现货 + 合约'
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

@app.route('/api/real/positions', methods=['GET'])
def real_positions():
    """获取实盘持仓"""
    api_key = get_active_api_key()
    if not api_key:
        return jsonify({
            'success': True,
            'positions': [],
            'message': '未配置 API Key'
        })
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'])
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

@app.route('/api/testnet/strategies', methods=['GET'])
def testnet_strategies():
    """获取测试网活跃策略"""
    strategies = strategy_engine.get_active_strategies()
    
    return jsonify({
        'success': True,
        'strategies': strategies,
        'count': len(strategies)
    })

@app.route('/api/testnet/prices', methods=['GET'])
def testnet_prices():
    """获取测试网价格"""
    # 使用默认测试网 API 获取价格
    api_key = {
        'api_key': 'FOc6rfs8QIWhIwPuU6LFyb36GatL1VUyHTaga3yVYjkQ8BmW1eDV1tooh3WY3SSV',
        'secret_key': 'O9flejsMESgKaI4tUDDYwLNcx1ypgpWkMReoaFplXmzQGsRrKYZ6FxPh492Hro6m'
    }
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=True)
    
    prices = {}
    for symbol in ['BTCUSDT', 'ETHUSDT', 'LINKUSDT', 'UNIUSDT']:
        result = client.get_spot_price(symbol)
        if result.get('success'):
            prices[symbol] = result['price']
        else:
            prices[symbol] = 0
    
    return jsonify({
        'success': True,
        'prices': prices
    })

@app.route('/api/real/prices', methods=['GET'])
def real_prices():
    """获取实盘价格"""
    api_key = get_active_api_key(testnet=False)
    if not api_key:
        return jsonify({'success': True, 'prices': {}})
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'], testnet=False)
    
    prices = {}
    for symbol in ['BTCUSDT', 'ETHUSDT', 'LINKUSDT', 'UNIUSDT']:
        result = client.get_spot_price(symbol)
        if result.get('success'):
            prices[symbol] = result['price']
        else:
            prices[symbol] = 0
    
    return jsonify({
        'success': True,
        'prices': prices
    })

@app.route('/api/real/strategies', methods=['GET'])
def real_strategies():
    """获取实盘活跃策略"""
    strategies = strategy_engine.get_active_strategies()
    
    return jsonify({
        'success': True,
        'strategies': strategies,
        'count': len(strategies)
    })

@app.route('/api/real/trade', methods=['POST'])
def real_trade():
    """实盘交易"""
    api_key = get_active_api_key()
    if not api_key:
        return jsonify({'success': False, 'error': '未配置 API Key'})
    
    data = request.json
    symbol = data.get('symbol', 'ETHUSDT')
    side = data.get('side', 'BUY')
    quantity = float(data.get('quantity', 0.01))
    
    client = BinanceClient(api_key['api_key'], api_key['secret_key'])
    result = client.place_futures_order(symbol, side, 'MARKET', quantity)
    
    return jsonify(result)

# ==================== 模拟盘 API ====================

@app.route('/api/sim/account', methods=['GET'])
def sim_account_info():
    """获取模拟账户信息"""
    info = sim_account.get_account_info()
    return jsonify({
        'success': True,
        'account': info
    })

@app.route('/api/sim/positions', methods=['GET'])
def sim_positions():
    """获取模拟持仓"""
    positions = sim_account.get_positions()
    return jsonify({
        'success': True,
        'positions': positions
    })

@app.route('/api/sim/trade', methods=['POST'])
def sim_trade():
    """模拟交易"""
    data = request.json
    symbol = data.get('symbol', 'ETHUSDT')
    side = data.get('side', 'long')
    quantity = float(data.get('quantity', 0.01))
    price = float(data.get('price', 0))
    leverage = int(data.get('leverage', 1))
    
    if price <= 0:
        return jsonify({'success': False, 'error': '价格无效'})
    
    result = sim_account.open(symbol, side, quantity, price, leverage=leverage)
    return jsonify(result)

@app.route('/api/sim/close', methods=['POST'])
def sim_close():
    """模拟平仓"""
    data = request.json
    symbol = data.get('symbol')
    price = float(data.get('price', 0))
    
    if not symbol or price <= 0:
        return jsonify({'success': False, 'error': '参数无效'})
    
    result = sim_account.close(symbol, price)
    return jsonify(result)

@app.route('/api/sim/reset', methods=['POST'])
def sim_reset():
    """重置模拟账户"""
    data = request.json
    capital = float(data.get('capital', 100.0))
    sim_account.reset(capital)
    return jsonify({'success': True, 'message': '账户已重置'})

# ==================== API Key 管理 ====================

@app.route('/api/config/apis', methods=['GET'])
def get_apis():
    """获取 API Key 列表"""
    keys = load_api_keys()
    # 隐藏敏感信息
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
    data = request.json
    keys = load_api_keys()
    
    new_key = {
        'name': data.get('name', '未命名'),
        'api_key': data.get('api_key', ''),
        'secret_key': data.get('secret_key', ''),
        'exchange': data.get('exchange', 'binance'),
        'testnet': data.get('testnet', False),
        'active': len(keys) == 0  # 第一个自动激活
    }
    
    keys.append(new_key)
    save_api_keys(keys)
    
    print(f"✅ API 已添加：{new_key['name']} (testnet={new_key['testnet']})")
    return jsonify({'success': True, 'message': 'API 已添加'})

@app.route('/api/config/apis/<int:index>', methods=['DELETE'])
def delete_api(index):
    """删除 API Key"""
    keys = load_api_keys()
    if 0 <= index < len(keys):
        keys.pop(index)
        save_api_keys(keys)
        return jsonify({'success': True, 'message': 'API 已删除'})
    return jsonify({'success': False, 'error': '索引超出范围'}), 404

@app.route('/api/config/apis/<int:index>/activate', methods=['POST'])
def activate_api(index):
    """激活 API Key"""
    keys = load_api_keys()
    if 0 <= index < len(keys):
        for i, k in enumerate(keys):
            k['active'] = (i == index)
        save_api_keys(keys)
        return jsonify({'success': True, 'message': 'API 已激活'})
    return jsonify({'success': False, 'error': '索引超出范围'}), 404

# ==================== 策略管理 ====================

# ==================== 策略引擎 API ====================

@app.route('/api/strategy/start', methods=['POST'])
def start_strategy():
    """启动策略"""
    data = request.json
    
    result = strategy_engine.start_strategy(
        symbol=data.get('symbol', 'ETHUSDT'),
        strategy=data.get('strategy', 'v23'),
        side=data.get('side', 'short'),
        entry_price=float(data.get('entry_price', 0)),
        quantity=float(data.get('quantity', 0.01))
    )
    
    return jsonify({
        'success': True,
        'message': '策略已启动',
        'strategy': result
    })

@app.route('/api/strategy/stop', methods=['POST'])
def stop_strategy():
    """停止策略"""
    data = request.json
    symbol = data.get('symbol')
    
    result = strategy_engine.stop_strategy(symbol)
    return jsonify(result)

@app.route('/api/strategy/list', methods=['GET'])
def list_strategies():
    """获取策略列表"""
    strategies = strategy_engine.get_active_strategies()
    return jsonify({
        'success': True,
        'strategies': strategies,
        'count': len(strategies)
    })

@app.route('/api/strategy/stats', methods=['GET'])
def strategy_stats():
    """获取策略统计"""
    stats = strategy_engine.get_strategy_stats()
    return jsonify({
        'success': True,
        'stats': stats
    })

@app.route('/api/strategy/signal', methods=['POST'])
def generate_signal():
    """生成交易信号"""
    data = request.json
    
    signal = strategy_engine.generate_signal(
        symbol=data.get('symbol', 'ETHUSDT'),
        signal_type=data.get('type', 'LONG'),
        confidence=float(data.get('confidence', 0.5)),
        price=float(data.get('price', 0))
    )
    
    return jsonify({
        'success': True,
        'signal': signal
    })

@app.route('/api/strategy/signals', methods=['GET'])
def get_signals():
    """获取信号列表"""
    limit = int(request.args.get('limit', 50))
    signals = strategy_engine.get_signals(limit)
    return jsonify({
        'success': True,
        'signals': signals,
        'count': len(signals)
    })

# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'status': 'ok',
        'version': 'v2.0',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

# ==================== 主程序 ====================

if __name__ == '__main__':
    print("🦞 启动统一交易 API 服务...")
    print("API 端点：http://localhost:5005")
    print("\n可用 API:")
    print("  实盘：/api/real/*")
    print("  模拟：/api/sim/*")
    print("  配置：/api/config/*")
    print("  策略：/api/strategy/*")
    print()
    
    app.run(host='0.0.0.0', port=5005, debug=False, threaded=True)
