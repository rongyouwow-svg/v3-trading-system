#!/usr/bin/env python3
"""
🦞 币安 API 客户端
封装币安现货和合约 API 调用
"""

import hmac
import hashlib
import time
import requests
from datetime import datetime
from typing import Dict, Optional

class BinanceClient:
    """币安 API 客户端（支持测试网/实盘）"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = False):
        """
        初始化币安客户端
        
        Args:
            api_key: API Key
            secret_key: API Secret
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        
        # 现货 API
        if testnet:
            self.spot_base = 'https://testnet.binance.vision/api/v3'
            print(f"🧪 测试网模式（现货）: {self.spot_base}")
        else:
            self.spot_base = 'https://api.binance.com/api/v3'
            print(f"🔴 实盘模式（现货）: {self.spot_base}")
        
        # 合约 API
        if testnet:
            self.futures_base = 'https://demo-fapi.binance.com'  # 官方测试网 URL（不含版本号）
            print(f"🧪 测试网模式（合约）: {self.futures_base}")
        else:
            self.futures_base = 'https://fapi.binance.com/fapi/v1'
            print(f"🔴 实盘模式（合约）: {self.futures_base}")
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def _sign(self, params: Dict) -> str:
        """生成 HMAC SHA256 签名"""
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, base_url: str, endpoint: str, 
                 params: Dict = None, signed: bool = False) -> Dict:
        """
        发送 API 请求
        
        Args:
            method: HTTP 方法
            base_url: 基础 URL
            endpoint: 端点
            params: 请求参数
            signed: 是否需要签名
            
        Returns:
            API 响应
        """
        url = f"{base_url}{endpoint}"
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = 5000
            params['signature'] = self._sign(params)
        
        try:
            if method == 'GET':
                resp = self.session.get(url, params=params, timeout=10)
            elif method == 'POST':
                resp = self.session.post(url, params=params, timeout=10)
            elif method == 'DELETE':
                resp = self.session.delete(url, params=params, timeout=10)
            else:
                return {'success': False, 'error': f'不支持的方法：{method}'}
            
            return resp.json()
        except requests.exceptions.Timeout:
            return {'success': False, 'error': '请求超时'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'网络错误：{str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'未知错误：{str(e)}'}
    
    # ==================== 现货 API ====================
    
    def get_spot_account(self) -> Dict:
        """获取现货账户余额"""
        result = self._request('GET', self.spot_base, '/account', signed=True)
        if 'balances' in result:
            # 过滤出有余额的资产
            balances = [
                b for b in result['balances'] 
                if float(b['free']) > 0 or float(b['locked']) > 0
            ]
            return {'success': True, 'balances': balances}
        return {'success': False, 'error': result.get('msg', '获取失败')}
    
    def get_spot_price(self, symbol: str) -> Dict:
        """获取现货价格"""
        result = self._request('GET', self.spot_base, '/ticker/price', 
                              params={'symbol': symbol})
        if 'price' in result:
            return {'success': True, 'price': float(result['price'])}
        return {'success': False, 'error': result.get('msg', '获取失败')}
    
    # ==================== 合约 API ====================
    
    def get_futures_account(self) -> Dict:
        """获取合约账户余额（官方 v3 API）"""
        # 使用官方 v3 API: GET /fapi/v3/balance
        # 文档：https://developers.binance.com/docs/derivatives/usds-margined-futures/account/rest-api#fapi-v3-balance-user_data
        result = self._request('GET', self.futures_base, '/fapi/v3/balance', signed=True)
        if isinstance(result, list):
            # 过滤有余额的资产
            filtered_assets = [
                a for a in result
                if float(a.get('balance', 0)) > 0
            ]
            # 计算总余额
            total_balance = sum(float(a.get('balance', 0)) for a in result)
            return {'success': True, 'assets': filtered_assets, 'totalBalance': total_balance}
        return {'success': False, 'error': result.get('msg', '获取失败') if isinstance(result, dict) else '未知错误'}
    
    def get_futures_positions(self) -> Dict:
        """获取合约持仓（增强版）"""
        # 使用 v2 API 端点
        result = self._request('GET', self.futures_base, '/fapi/v2/positionRisk', signed=True)
        if isinstance(result, list):
            positions = []
            for pos in result:
                position_amt = float(pos.get('positionAmt', 0))
                if position_amt != 0:
                    entry_price = float(pos.get('entryPrice', 0))
                    mark_price = float(pos.get('markPrice', 0))
                    leverage = int(pos.get('leverage', 1))
                    size = abs(position_amt)
                    
                    # 计算仓位价值
                    position_value = size * mark_price
                    
                    # 计算保证金
                    margin = position_value / leverage
                    
                    # 估算爆仓价（简化计算）
                    if position_amt > 0:  # 多单
                        liquidation_price = entry_price * (1 - 1/leverage + 0.005)  # 0.5% 缓冲
                    else:  # 空单
                        liquidation_price = entry_price * (1 + 1/leverage - 0.005)
                    
                    positions.append({
                        'symbol': pos['symbol'],
                        'side': 'LONG' if position_amt > 0 else 'SHORT',
                        'size': size,
                        'entry_price': entry_price,
                        'mark_price': mark_price,
                        'unrealized_pnl': float(pos.get('unRealizedProfit', 0)),
                        'leverage': leverage,
                        'position_value': round(position_value, 2),  # 仓位价值
                        'margin': round(margin, 2),  # 保证金
                        'liquidation_price': round(liquidation_price, 2)  # 爆仓价
                    })
            return {'success': True, 'positions': positions}
        return {'success': False, 'error': result.get('msg', '获取失败')}
    
    def get_futures_order_trades(self, symbol: str = None, limit: int = 50) -> Dict:
        """获取合约成交记录"""
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        
        result = self._request('GET', self.futures_base, '/fapi/v1/userTrades', 
                              params=params, signed=True)
        if isinstance(result, list):
            trades = []
            for trade in result:
                trades.append({
                    'symbol': trade.get('symbol', ''),
                    'id': trade.get('id'),
                    'orderId': trade.get('orderId'),
                    'side': trade.get('side', ''),  # BUY/SELL
                    'price': float(trade.get('price', 0)),
                    'qty': float(trade.get('qty', 0)),
                    'realizedPnl': float(trade.get('realizedPnl', 0)),
                    'time': datetime.fromtimestamp(trade.get('time', 0)/1000).isoformat(),
                    'isMaker': trade.get('isMaker', False)
                })
            return {'success': True, 'trades': trades}
        return {'success': False, 'error': result.get('msg', '获取失败')}
    
    def get_symbol_precision(self, symbol: str) -> int:
        """获取交易对数量精度"""
        try:
            result = self._request('GET', self.futures_base, '/fapi/v1/exchangeInfo', 
                                  params={'symbol': symbol}, signed=False)
            if 'symbols' in result and len(result['symbols']) > 0:
                filters = result['symbols'][0].get('filters', [])
                for f in filters:
                    if f.get('filterType') == 'LOT_SIZE':
                        step_size = f.get('stepSize', '0.001')
                        # 计算小数位数
                        return len(step_size.split('.')[-1].rstrip('0'))
        except:
            pass
        return 3  # 默认 3 位小数
    
    def format_quantity(self, symbol: str, quantity: float) -> float:
        """格式化数量到正确的精度"""
        precision = self.get_symbol_precision(symbol)
        return round(quantity, precision)
    
    def place_futures_order(self, symbol: str, side: str, order_type: str,
                           quantity: float, price: float = None) -> Dict:
        """
        下合约订单
        
        Args:
            symbol: 交易对
            side: BUY/SELL
            order_type: MARKET/LIMIT
            quantity: 数量
            price: 价格（限价单需要）
        """
        # 格式化数量到正确精度
        quantity = self.format_quantity(symbol, quantity)
        
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity
        }
        
        if order_type == 'LIMIT':
            if not price:
                return {'success': False, 'error': '限价单需要指定价格'}
            params['price'] = price
            params['timeInForce'] = 'GTC'
        
        result = self._request('POST', self.futures_base, '/fapi/v1/order', 
                              params=params, signed=True)
        
        if 'orderId' in result:
            return {'success': True, 'order': result}
        return {'success': False, 'error': result.get('msg', '下单失败')}
    
    def close_futures_position(self, symbol: str, side: str, quantity: float) -> Dict:
        """
        平仓
        
        Args:
            symbol: 交易对
            side: BUY/SELL（与持仓方向相反）
            quantity: 数量
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': quantity,
            'reduceOnly': 'true'
        }
        
        result = self._request('POST', self.futures_base, '/fapi/v1/order', 
                              params=params, signed=True)
        
        if 'orderId' in result:
            return {'success': True, 'order': result}
        return {'success': False, 'error': result.get('msg', '平仓失败')}
    
    def set_futures_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        设置合约杠杆倍数
        
        Args:
            symbol: 交易对 (如 BTCUSDT)
            leverage: 杠杆倍数 (1-125)
            
        Returns:
            设置结果
        """
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        
        # 调用币安杠杆设置 API: POST /fapi/v1/leverage
        result = self._request('POST', self.futures_base, '/fapi/v1/leverage', 
                              params=params, signed=True)
        
        if 'leverage' in result:
            return {
                'success': True, 
                'leverage': result['leverage'],
                'msg': f'杠杆已设置为 {result["leverage"]}x'
            }
        return {'success': False, 'error': result.get('msg', '设置杠杆失败')}
    
    def place_stop_loss_order(self, symbol: str, side: str, quantity: float = None,
                              stop_price: float = None, reduce_only: bool = True,
                              close_position: bool = False) -> Dict:
        """
        下止损单（使用 Algo Order API - 测试网和实盘都支持）
        
        根据币安官方文档：
        - algoType: CONDITIONAL（条件订单）
        - type: STOP_MARKET/TAKE_PROFIT_MARKET 等
        - triggerPrice: 触发价格（注意不是 stopPrice）
        - closePosition: true 表示全仓平仓（不能与 quantity/reduceOnly 同用）
        
        Args:
            symbol: 交易对
            side: BUY/SELL（与持仓方向相反）
            quantity: 数量（与 closePosition 互斥）
            stop_price: 触发价格
            reduce_only: 是否仅减仓（默认 True）
            close_position: 是否全仓平仓（默认 False）
        """
        # 使用 Algo Order API（POST /fapi/v1/algoOrder）
        params = {
            'symbol': symbol,
            'side': side,
            'positionSide': 'BOTH',
            'algoType': 'CONDITIONAL',  # 关键参数！只支持 CONDITIONAL
            'type': 'STOP_MARKET',
            'triggerPrice': stop_price,  # 触发价格（官方参数名）
            'priceProtect': 'true',  # 防止极端滑点
            'newOrderRespType': 'RESULT'
        }
        
        # closePosition 与 quantity/reduceOnly 互斥
        if close_position:
            params['closePosition'] = 'true'
            # 不能发送 quantity 和 reduceOnly
        else:
            params['quantity'] = quantity
            params['reduceOnly'] = 'true' if reduce_only else 'false'
        
        # 调用 Algo Order API
        result = self._request('POST', self.futures_base, '/fapi/v1/algoOrder', 
                              params=params, signed=True)
        
        # 检查返回结果
        if 'algoId' in result or 'orderId' in result:
            algo_id = result.get('algoId', result.get('orderId'))
            print(f"✅ 止损单已下单：{symbol} {side} @ {stop_price}, Algo ID: {algo_id}")
            return {'success': True, 'order': result, 'order_id': algo_id}
        elif 'code' in result and result['code'] == 0:
            algo_id = result.get('algoId', result.get('orderId'))
            print(f"✅ 止损单已下单：{symbol} {side} @ {stop_price}, Algo ID: {algo_id}")
            return {'success': True, 'order': result, 'order_id': algo_id}
        else:
            error_msg = result.get('msg', result.get('error', '止损单失败'))
            error_code = result.get('code', 'UNKNOWN')
            print(f"❌ 止损单失败：{error_msg} (code: {error_code})")
            return {'success': False, 'error': error_msg, 'code': error_code}
    
    def place_take_profit_order(self, symbol: str, side: str, quantity: float = None,
                                stop_price: float = None, reduce_only: bool = True,
                                close_position: bool = False) -> Dict:
        """
        下止盈单（使用 Algo Order API）
        """
        params = {
            'symbol': symbol,
            'side': side,
            'positionSide': 'BOTH',
            'algoType': 'CONDITIONAL',  # 关键参数！
            'type': 'TAKE_PROFIT_MARKET',
            'triggerPrice': stop_price,  # 触发价格
            'priceProtect': 'true',
            'newOrderRespType': 'RESULT'
        }
        
        # closePosition 与 quantity/reduceOnly 互斥
        if close_position:
            params['closePosition'] = 'true'
        else:
            params['quantity'] = quantity
            params['reduceOnly'] = 'true' if reduce_only else 'false'
        
        result = self._request('POST', self.futures_base, '/fapi/v1/algoOrder', 
                              params=params, signed=True)
        
        if 'algoId' in result or 'orderId' in result:
            algo_id = result.get('algoId', result.get('orderId'))
            print(f"✅ 止盈单已下单：{symbol} {side} @ {stop_price}, Algo ID: {algo_id}")
            return {'success': True, 'order': result, 'order_id': algo_id}
        elif 'code' in result and result['code'] == 0:
            algo_id = result.get('algoId', result.get('orderId'))
            print(f"✅ 止盈单已下单：{symbol} {side} @ {stop_price}, Algo ID: {algo_id}")
            return {'success': True, 'order': result, 'order_id': algo_id}
        else:
            error_msg = result.get('msg', result.get('error', '止盈单失败'))
            error_code = result.get('code', 'UNKNOWN')
            print(f"❌ 止盈单失败：{error_msg} (code: {error_code})")
            return {'success': False, 'error': error_msg, 'code': error_code}
    
    def cancel_algo_order(self, symbol: str, algo_id: int) -> Dict:
        """
        取消 Algo 订单
        
        Args:
            symbol: 交易对
            algo_id: Algo 订单 ID
            
        Returns:
            取消结果
        """
        params = {
            'symbol': symbol,
            'algoId': algo_id
        }
        
        result = self._request('DELETE', self.futures_base, '/fapi/v1/algoOrder', 
                              params=params, signed=True)
        
        if 'algoId' in result:
            print(f"✅ Algo 订单已取消：{symbol}, Algo ID: {algo_id}")
            return {'success': True, 'order': result}
        elif 'code' in result and result['code'] == 0:
            print(f"✅ Algo 订单已取消：{symbol}, Algo ID: {algo_id}")
            return {'success': True, 'order': result}
        else:
            error_msg = result.get('msg', result.get('error', '取消失败'))
            error_code = result.get('code', 'UNKNOWN')
            print(f"❌ 取消失败：{error_msg} (code: {error_code})")
            return {'success': False, 'error': error_msg, 'code': error_code}
    
    def get_algo_orders(self, symbol: str = None, limit: int = 50) -> Dict:
        """
        获取所有 Algo 订单（含止损/止盈）
        """
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        
        result = self._request('GET', self.futures_base, '/fapi/v1/openAlgoOrders', 
                              params=params, signed=True)
        
        if isinstance(result, list):
            return {'success': True, 'orders': result, 'count': len(result)}
        return {'success': False, 'error': result.get('msg', '获取 Algo 订单失败')}
    
    def place_take_profit_order(self, symbol: str, side: str, quantity: float,
                                stop_price: float, reduce_only: bool = True) -> Dict:
        """
        下止盈单（TAKE_PROFIT_MARKET）
        
        Args:
            symbol: 交易对
            side: BUY/SELL
            quantity: 数量
            stop_price: 触发价格
            reduce_only: 是否仅减仓
            
        Returns:
            订单结果
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'TAKE_PROFIT_MARKET',
            'stopPrice': stop_price,
            'quantity': quantity,
            'reduceOnly': 'true' if reduce_only else 'false'
        }
        
        result = self._request('POST', self.futures_base, '/fapi/v1/order', 
                              params=params, signed=True)
        
        if 'orderId' in result:
            return {'success': True, 'order': result}
        return {'success': False, 'error': result.get('msg', '止盈单失败')}
    
    def cancel_futures_order(self, symbol: str, order_id: int) -> Dict:
        """
        取消合约订单
        
        Args:
            symbol: 交易对
            order_id: 订单 ID
            
        Returns:
            取消结果
        """
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        result = self._request('DELETE', self.futures_base, '/fapi/v1/order', 
                              params=params, signed=True)
        
        if 'orderId' in result:
            return {'success': True}
        return {'success': False, 'error': result.get('msg', '取消失败')}
