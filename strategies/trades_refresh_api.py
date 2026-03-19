#!/usr/bin/env python3
"""
📊 交易记录刷新 API

提供交易记录刷新功能
"""

from fastapi import APIRouter
from typing import Dict, List
from datetime import datetime
import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode

router = APIRouter(prefix="/api/trades", tags=["交易记录"])

# 币安测试网配置
BINANCE_TESTNET_BASE = "https://testnet.binancefuture.com"
API_KEY = "YOUR_API_KEY"
SECRET_KEY = "YOUR_SECRET_KEY"


def generate_signature(params: dict) -> str:
    """生成签名"""
    query_string = urlencode(params)
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


@router.get("/refresh")
async def refresh_trades(symbol: str = "ETHUSDT", limit: int = 50):
    """刷新交易记录"""
    try:
        # 获取用户成交记录
        params = {
            'symbol': symbol,
            'limit': limit,
            'timestamp': int(time.time() * 1000)
        }
        params['signature'] = generate_signature(params)
        
        response = requests.get(
            f"{BINANCE_TESTNET_BASE}/fapi/v1/userTrades",
            headers={'X-MBX-APIKEY': API_KEY},
            params=params,
            timeout=10
        )
        trades_data = response.json()
        
        if isinstance(trades_data, list):
            trades = []
            for t in trades_data:
                # 判断订单类型
                is_buyer = t.get('buyer', False)
                is_maker = t.get('maker', False)
                
                # 根据 buyer 和 maker 判断订单类型
                if is_buyer:
                    order_type = '开多' if not is_maker else '平空'
                else:
                    order_type = '平多' if not is_maker else '开空'
                
                trades.append({
                    'id': t['id'],
                    'symbol': t['symbol'],
                    'side': 'BUY' if is_buyer else 'SELL',
                    'order_type': order_type,
                    'price': float(t['price']),
                    'quantity': float(t['qty']),
                    'commission': float(t.get('commission', 0)),
                    'commission_asset': t.get('commissionAsset', 'USDT'),
                    'time': datetime.fromtimestamp(t['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp': t['time']
                })
            
            # 按时间倒序排序（最新在最上面）
            trades.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'success': True,
                'trades': trades,
                'count': len(trades),
                'source': 'binance_testnet'
            }
        else:
            return {
                'success': False,
                'error': '获取交易记录失败',
                'data': trades_data
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/positions/refresh")
async def refresh_positions():
    """刷新持仓信息"""
    try:
        params = {
            'timestamp': int(time.time() * 1000)
        }
        params['signature'] = generate_signature(params)
        
        response = requests.get(
            f"{BINANCE_TESTNET_BASE}/fapi/v2/positionRisk",
            headers={'X-MBX-APIKEY': API_KEY},
            params=params,
            timeout=10
        )
        positions_data = response.json()
        
        if isinstance(positions_data, list):
            positions = []
            for p in positions_data:
                position_amt = float(p.get('positionAmt', 0))
                if position_amt != 0:
                    positions.append({
                        'symbol': p['symbol'],
                        'side': 'LONG' if position_amt > 0 else 'SHORT',
                        'size': abs(position_amt),
                        'entry_price': float(p.get('entryPrice', 0)),
                        'mark_price': float(p.get('markPrice', 0)),
                        'unrealized_pnl': float(p.get('unRealizedProfit', 0)),
                        'leverage': int(p.get('leverage', 1))
                    })
            
            return {
                'success': True,
                'positions': positions,
                'count': len(positions),
                'source': 'binance_testnet'
            }
        else:
            return {
                'success': False,
                'error': '获取持仓失败',
                'data': positions_data
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
