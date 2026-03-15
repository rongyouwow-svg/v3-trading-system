#!/usr/bin/env python3
"""
🦞 币安测试网 API 集成

提供真实的币安测试网交易功能
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode

router = APIRouter(prefix="/api/binance", tags=["币安测试网"])

# 币安测试网配置
BINANCE_TESTNET_BASE = "https://testnet.binancefuture.com"
API_KEY = "q3BX9K88wS4Dzco6DxVp5fhkRc5OOUu3tKFK5VBHkpcweVJ1NDDgATDV6Db0TTOg"
SECRET_KEY = "J3rsWIqPPjdRtXzbBReq24YiKrw03CiHopRxM1B5eUTQ6xZ6pi1jLK1lmiYrqctY"


def generate_signature(params: dict) -> str:
    """生成签名"""
    query_string = urlencode(params)
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def binance_request(method: str, endpoint: str, params: dict = None, signed: bool = False) -> dict:
    """发送币安 API 请求"""
    url = f"{BINANCE_TESTNET_BASE}{endpoint}"
    
    headers = {
        'X-MBX-APIKEY': API_KEY
    }
    
    if params is None:
        params = {}
    
    if signed:
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = generate_signature(params)
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, params=params, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, params=params, timeout=10)
        else:
            raise ValueError(f"不支持的请求方法：{method}")
        
        result = response.json()
        
        if isinstance(result, dict) and 'code' in result and result['code'] != 200:
            return {
                'success': False,
                'error': result.get('msg', 'Unknown error'),
                'code': result.get('code')
            }
        
        return {
            'success': True,
            'data': result
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


class OrderConfig(BaseModel):
    """订单配置"""
    symbol: str
    side: str  # BUY/SELL
    type: str = "MARKET"  # MARKET/LIMIT
    quantity: Optional[float] = None
    price: Optional[float] = None
    leverage: int = 5


@router.get("/klines")
async def get_klines(symbol: str = "ETHUSDT", interval: str = "1m", limit: int = 50):
    """获取 K 线数据"""
    try:
        response = requests.get(
            f"{BINANCE_TESTNET_BASE}/fapi/v1/klines",
            params={
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            },
            timeout=10
        )
        klines_data = response.json()
        
        if isinstance(klines_data, list):
            klines = []
            for k in klines_data:
                klines.append({
                    'timestamp': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            
            return {'success': True, 'klines': klines}
        else:
            return {'success': False, 'error': '获取 K 线失败'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get("/account-info")
async def get_account_info():
    """获取账户信息"""
    result = binance_request('GET', '/fapi/v2/account', signed=True)
    
    if result['success']:
        data = result['data']
        usdt_asset = next((a for a in data.get('assets', []) if a['asset'] == 'USDT'), None)
        
        return {
            'success': True,
            'account': {
                'balance': float(usdt_asset['walletBalance']) if usdt_asset else 0,
                'available': float(usdt_asset['availableBalance']) if usdt_asset else 0,
                'total': float(usdt_asset['walletBalance']) if usdt_asset else 0
            }
        }
    else:
        return result


@router.get("/positions")
async def get_positions():
    """获取持仓信息"""
    result = binance_request('GET', '/fapi/v2/positionRisk', signed=True)
    
    if result['success']:
        positions = []
        for pos in result['data']:
            position_amt = float(pos.get('positionAmt', 0))
            if position_amt != 0:
                positions.append({
                    'symbol': pos['symbol'],
                    'side': 'LONG' if position_amt > 0 else 'SHORT',
                    'size': abs(position_amt),
                    'entry_price': float(pos.get('entryPrice', 0)),
                    'current_price': float(pos.get('markPrice', 0)),
                    'unrealized_pnl': float(pos.get('unRealizedProfit', 0)),
                    'unrealized_pnl_pct': round((float(pos.get('markPrice', 0)) - float(pos.get('entryPrice', 0))) / float(pos.get('entryPrice', 1)) * 100, 2) if pos.get('entryPrice') else 0,
                    'leverage': int(pos.get('leverage', 1)),
                    'liquidation_price': float(pos.get('liquidationPrice', 0))
                })
        
        return {
            'success': True,
            'positions': positions
        }
    else:
        return result


@router.post("/order")
async def create_order(config: OrderConfig):
    """创建订单"""
    params = {
        'symbol': config.symbol,
        'side': config.side,
        'type': config.type,
        'quantity': config.quantity
    }
    
    if config.type == 'LIMIT':
        params['price'] = config.price
        params['timeInForce'] = 'GTC'
    
    result = binance_request('POST', '/fapi/v1/order', params, signed=True)
    
    if result['success']:
        data = result['data']
        return {
            'success': True,
            'order': {
                'order_id': str(data['orderId']),
                'symbol': data['symbol'],
                'side': data['side'],
                'type': data['type'],
                'quantity': float(data['origQty']),
                'price': float(data['price']),
                'status': data['status']
            }
        }
    else:
        return result


@router.get("/orders")
async def get_orders(symbol: str = None, limit: int = 20):
    """获取订单列表"""
    params = {'limit': limit}
    if symbol:
        params['symbol'] = symbol
    
    result = binance_request('GET', '/fapi/v1/allOrders', params, signed=True)
    
    if result['success']:
        orders = []
        for order in result['data']:
            orders.append({
                'order_id': str(order['orderId']),
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'quantity': float(order['origQty']),
                'price': float(order['price']),
                'status': order['status'],
                'create_time': datetime.fromtimestamp(order['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S') if 'time' in order else None
            })
        
        return {
            'success': True,
            'orders': orders
        }
    else:
        return result


@router.get("/trades")
async def get_trades(symbol: str = None, limit: int = 50):
    """获取成交记录"""
    params = {'limit': limit}
    if symbol:
        params['symbol'] = symbol
    
    result = binance_request('GET', '/fapi/v1/userTrades', params, signed=True)
    
    if result['success']:
        trades = []
        for trade in result['data']:
            # 判断订单类型（根据 buyer 和 maker 标志）
            is_buyer = trade.get('buyer', False)
            is_maker = trade.get('maker', False)
            
            # 根据 buyer 和 maker 判断订单类型
            if is_buyer:
                order_type = '开多' if not is_maker else '平空'
            else:
                order_type = '平多' if not is_maker else '开空'
            
            trades.append({
                'trade_id': str(trade['id']),
                'symbol': trade['symbol'],
                'side': 'BUY' if is_buyer else 'SELL',
                'order_type': order_type,
                'quantity': float(trade['qty']),
                'price': float(trade['price']),
                'commission': float(trade.get('commission', 0)),
                'commission_asset': trade.get('commissionAsset', 'USDT'),
                'realized_pnl': float(trade.get('realizedPnl', 0)),
                'trade_time': datetime.fromtimestamp(trade['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S') if 'time' in trade else None,
                'timestamp': trade.get('time', 0)
            })
        
        # 按时间倒序排列（最新的在前面）
        trades.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'success': True,
            'trades': trades
        }
    else:
        return result


@router.post("/position/close")
async def close_position(symbol: str, quantity: float = None):
    """平仓"""
    # 先获取持仓
    pos_result = binance_request('GET', '/fapi/v2/positionRisk', signed=True)
    
    if not pos_result['success']:
        return pos_result
    
    # 查找对应持仓
    position = None
    for pos in pos_result['data']:
        if pos['symbol'] == symbol:
            position_amt = float(pos.get('positionAmt', 0))
            if position_amt != 0:
                position = pos
                break
    
    if not position:
        return {
            'success': False,
            'error': '无持仓'
        }
    
    # 平仓（反向开仓）
    position_amt = float(position['positionAmt'])
    side = 'SELL' if position_amt > 0 else 'BUY'
    quantity = abs(position_amt) if quantity is None else quantity
    
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'reduceOnly': 'true'
    }
    
    result = binance_request('POST', '/fapi/v1/order', params, signed=True)
    
    return result


@router.get("/stop-loss")
async def get_stop_loss_orders(symbol: str = None, limit: int = 50):
    """获取止损单列表（从币安 Algo Order API 查询）
    
    参考：
    - 币安官方文档：https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Cancel-Algo-Order
    - 历史实现：/home/admin/.openclaw/workspace/quant/history/docs/report/币安 Algo Order API 完全实现.md
    
    测试网 vs 实盘:
    - 测试网：https://demo-fapi.binance.com/fapi/v1/openAlgoOrders
    - 实盘：https://fapi.binance.com/fapi/v1/openAlgoOrders
    - API 端点完全相同，只需切换 base_url（连接器自动处理）
    """
    try:
        # 从币安 Algo Order API 查询
        params = {
            'limit': limit,
            'timestamp': int(time.time() * 1000)
        }
        
        if symbol:
            params['symbol'] = symbol
        
        # 使用正确的 API 端点：/fapi/v1/openAlgoOrders
        result = binance_request('GET', '/fapi/v1/openAlgoOrders', params, signed=True)
        
        if result.get('success'):
            orders = result.get('data', [])
            
            # 筛选止损单和止盈单
            stop_orders = []
            for order in orders:
                order_type = order.get('orderType', '')
                if order_type in ['STOP_MARKET', 'TAKE_PROFIT_MARKET', 'STOP', 'TAKE_PROFIT']:
                    stop_orders.append({
                        'algo_id': str(order.get('algoId', order.get('orderId', ''))),
                        'symbol': order.get('symbol', ''),
                        'side': order.get('side', ''),
                        'algo_type': order.get('algoType', 'CONDITIONAL'),
                        'order_type': order_type,
                        'trigger_price': str(order.get('triggerPrice', order.get('stopPrice', '0'))),
                        'quantity': str(order.get('quantity', '0')),
                        'status': order.get('algoStatus', order.get('status', '')),
                        'create_time': order.get('createTime', order.get('time', 0)),
                        'reduce_only': order.get('reduceOnly', False),
                        'close_position': order.get('closePosition', False)
                    })
            
            return {
                'success': True,
                'orders': stop_orders,
                'count': len(stop_orders)
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'orders': [],
                'count': 0
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'orders': [],
            'count': 0
        }


def get_stop_loss_from_local_state(symbol: str = None):
    """从本地策略状态文件估算止损单（回退方案）"""
    import json
    import os
    
    try:
        state_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'strategy_pids.json')
        
        if not os.path.exists(state_file):
            return {
                'success': True,
                'orders': [],
                'count': 0
            }
        
        with open(state_file, 'r') as f:
            strategies = json.load(f)
        
        orders = []
        for sym, data in strategies.items():
            if symbol and sym != symbol:
                continue
            
            if data.get('position') and data.get('entry_price', 0) > 0:
                entry = data['entry_price']
                stop_loss_pct = data.get('stop_loss_pct', 0.005)
                
                if data['position'] == 'LONG':
                    stop_price = entry * (1 - stop_loss_pct)
                    side = 'SELL'
                else:
                    stop_price = entry * (1 + stop_loss_pct)
                    side = 'BUY'
                
                orders.append({
                    'order_id': f"stop_{sym}_{data.get('entry_price', 0)}",
                    'symbol': sym,
                    'side': side,
                    'algo_type': 'CONDITIONAL',
                    'trigger_price': str(stop_price),
                    'quantity': str(data.get('size', 0)),
                    'status': 'ESTIMATED',  # 标记为估算
                    'create_time': data.get('start_time', '-'),
                    'entry_price': str(entry),
                    'stop_loss_pct': str(stop_loss_pct)
                })
        
        return {
            'success': True,
            'orders': orders,
            'count': len(orders)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'orders': [],
            'count': 0
        }


@router.post("/stop-loss")
async def create_stop_loss(request: Request):
    """创建止损单"""
    try:
        # 从 JSON body 获取参数
        body = await request.json()
        symbol = body.get('symbol')
        side = body.get('side', 'SELL')
        trigger_price = body.get('trigger_price')
        quantity = body.get('quantity')
        algo_type = body.get('algo_type', 'CONDITIONAL')
        
        # 根据币种精度处理数量和价格
        # ETHUSDT: quantityPrecision=3, pricePrecision=2
        # BTCUSDT: quantityPrecision=3, pricePrecision=1
        # 通用处理：数量 3 位小数，价格 2 位小数
        quantity_rounded = round(float(quantity), 3)
        trigger_price_rounded = round(float(trigger_price), 2)
        
        # 参考历史文档：/home/admin/.openclaw/workspace/quant/history/docs/report/币安 Algo Order API 完全实现.md
        # 关键参数：algoType=CONDITIONAL, type=STOP_MARKET, triggerPrice（不是 stopPrice）
        params = {
            'symbol': symbol,
            'side': side,
            'algoType': 'CONDITIONAL',  # 只支持 CONDITIONAL
            'type': 'STOP_MARKET',  # 止损单类型
            'triggerPrice': str(trigger_price_rounded),  # 使用 triggerPrice（不是 stopPrice）
            'quantity': str(quantity_rounded),  # 精度处理
            'reduceOnly': 'false',
            'newOrderRespType': 'ACK',
            'timestamp': int(time.time() * 1000)
        }
        
        # 发送到 Algo Order API 专用端点
        result = binance_request('POST', '/fapi/v1/algoOrder', params, signed=True)
        
        return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.post("/stop-loss/cancel")
async def cancel_stop_loss(symbol: str, order_id: str = None):
    """取消止损单"""
    params = {
        'symbol': symbol,
        'timestamp': int(time.time() * 1000)
    }
    
    if order_id:
        params['algoId'] = order_id
    
    result = binance_request('POST', '/fapi/v1/algoOrder', params, signed=True, method_override='DELETE')
    
    return result
