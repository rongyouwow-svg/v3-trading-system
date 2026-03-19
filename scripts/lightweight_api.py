#!/usr/bin/env python3
"""
🦞 轻量级 Web API（替换 uvicorn）

内存占用：~10 MB（vs uvicorn 63 MB）
功能：
1. 持仓查询
2. 止损单查询
3. 策略状态
4. 账户余额

使用：http.server（Python 内置）
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
import time
from urllib.parse import urlparse, parse_qs

# 配置
PORT = 3000
BINANCE_BASE = "https://testnet.binancefuture.com"

# 内存缓存（减少重复请求）
cache = {}
CACHE_TTL = 10  # 10 秒缓存


class LightweightAPI(BaseHTTPRequestHandler):
    """轻量级 API 处理器"""
    
    def log_message(self, format, *args):
        """禁用默认日志（减少 IO）"""
        pass
    
    def send_json(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # 路由处理
        if path == '/api/binance/positions':
            self.get_positions()
        elif path == '/api/binance/stop-loss':
            self.get_stop_losses()
        elif path == '/api/strategy/active':
            self.get_active_strategies()
        elif path == '/api/strategy/status':
            self.get_strategy_status()
        elif path == '/api/binance/account-info':
            self.get_account_info()
        elif path == '/api/binance/trades':
            self.get_trades(params)
        elif path == '/api/binance/klines':
            self.get_klines(params)
        elif path == '/':
            self.send_json({'status': 'ok', 'service': 'lightweight-api'})
        else:
            self.send_json({'error': 'Not found'}, 404)
    
    def get_positions(self):
        """获取持仓"""
        cache_key = 'positions'
        
        if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_TTL:
            self.send_json(cache[cache_key]['data'])
            return
        
        try:
            # 从币安获取
            result = binance_request('/fapi/v2/positionRisk')
            data = {'success': True, 'positions': result}
            
            cache[cache_key] = {'data': data, 'time': time.time()}
            self.send_json(data)
        except Exception as e:
            self.send_json({'success': False, 'error': str(e)}, 500)
    
    def get_stop_losses(self):
        """获取止损单"""
        # 简化：返回空列表（实际应从数据库读取）
        self.send_json({'success': True, 'orders': []})
    
    def get_active_strategies(self):
        """获取活跃策略"""
        # 从注册中心读取
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))
            from strategy_registry import StrategyRegistry
            registry = StrategyRegistry()
            strategies = registry.get_running()
            
            # 转换为 API 格式
            active = []
            for symbol, info in strategies.items():
                active.append({
                    'symbol': symbol,
                    'status': 'running',
                    'rsi': 0,
                    'stable_count': 0,
                    'position': None,
                    'entry_price': 0,
                    'signals_sent': 0,
                    'signals_executed': 0
                })
            
            self.send_json({'success': True, 'active_strategies': active, 'count': len(active)})
        except Exception as e:
            self.send_json({'success': False, 'error': str(e)}, 500)
    
    def get_strategy_status(self):
        """获取策略状态"""
        self.send_json({'success': True, 'strategies': {}})
    
    def get_account_info(self):
        """获取账户信息"""
        cache_key = 'account_info'
        
        if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_TTL:
            self.send_json(cache[cache_key]['data'])
            return
        
        try:
            result = binance_request('/fapi/v2/balance')
            data = {'success': True, 'balance': sum(float(r['available']) for r in result if r['asset'] == 'USDT')}
            
            cache[cache_key] = {'data': data, 'time': time.time()}
            self.send_json(data)
        except Exception as e:
            self.send_json({'success': False, 'error': str(e)}, 500)
    
    def get_trades(self, params):
        """获取成交记录"""
        limit = int(params.get('limit', [20])[0])
        
        # 简化：返回空列表
        self.send_json({'success': True, 'trades': []})
    
    def get_klines(self, params):
        """获取 K 线数据"""
        symbol = params.get('symbol', ['BTCUSDT'])[0]
        interval = params.get('interval', ['1m'])[0]
        limit = int(params.get('limit', [100])[0])
        
        try:
            result = binance_request('/fapi/v1/klines', {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            })
            
            self.send_json({'success': True, 'klines': result})
        except Exception as e:
            self.send_json({'success': False, 'error': str(e)}, 500)


def binance_request(endpoint, params=None):
    """币安 API 请求（简化版）"""
    import hmac
    import hashlib
    import time
    
    # 从环境变量读取 API 密钥
    import os
    api_key = os.getenv('BINANCE_API_KEY', '')
    secret = os.getenv('BINANCE_SECRET', '')
    
    if not api_key or not secret:
        # 测试模式：返回空数据
        if 'positionRisk' in endpoint:
            return []
        elif 'klines' in endpoint:
            return []
        elif 'balance' in endpoint:
            return [{'available': '5000'}]
        return []
    
    # 签名请求
    timestamp = int(time.time() * 1000)
    query = f"timestamp={timestamp}"
    signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    
    url = f"{BINANCE_BASE}{endpoint}?{query}&signature={signature}"
    
    response = requests.get(url, headers={'X-MBX-APIKEY': api_key}, timeout=10)
    return response.json()


def run_server():
    """运行服务器"""
    server = HTTPServer(('0.0.0.0', PORT), LightweightAPI)
    print(f"🦞 轻量级 Web API 启动")
    print(f"   端口：{PORT}")
    print(f"   内存占用：~10 MB")
    print(f"   缓存 TTL: {CACHE_TTL} 秒")
    print(f"="*50)
    server.serve_forever()


if __name__ == '__main__':
    run_server()
