#!/usr/bin/env python3
"""
币安连接器 - U 本位合约

实现 IConnector 接口，提供币安 U 本位合约交易功能。

用法:
    from connectors.binance.usdt_futures import BinanceUSDTFuturesConnector

    connector = BinanceUSDTFuturesConnector(api_key, secret_key)
    result = connector.get_account_balance()
"""

from typing import Dict, Optional
from decimal import Decimal
import time
import hashlib
import hmac
from urllib.parse import urlencode

import requests


from modules.models.order import Order, OrderType, OrderSide
from modules.utils.result import Result, ok, fail
from modules.utils.exceptions import (
    NetworkException,
    InsufficientBalanceException,
    RateLimitException,
    ExchangeException,
)
from modules.utils.logger import setup_logger

logger = setup_logger("binance_connector", log_file="logs/binance.log")


class BinanceUSDTFuturesConnector:
    """
    币安 U 本位合约连接器

    功能:
        - 账户管理（余额、持仓）
        - 订单管理（下单、撤单、查询）
        - 行情数据（K 线、Ticker、深度）
        - 止损单管理

    参考:
        - 币安 API 文档：https://binance-docs.github.io/apidocs/futures/en/
    """

    # API 端点
    BASE_URL = "https://fapi.binance.com"
    # 币安测试网 REST API: https://demo-fapi.binance.com
    TESTNET_BASE_URL = "https://demo-fapi.binance.com"

    # API 版本
    API_VERSION = "v1"

    # 超时设置
    TIMEOUT = 10  # 秒

    def __init__(self, api_key: str, secret_key: str, testnet: bool = True):
        """
        初始化连接器

        Args:
            api_key: API Key
            secret_key: Secret Key
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.base_url = self.TESTNET_BASE_URL if testnet else self.BASE_URL

        # 创建 Session
        self.session = requests.Session()
        self.session.headers.update(
            {"X-MBX-APIKEY": self.api_key}
        )

        # 服务器时间偏移（毫秒）
        self.server_time_offset = 0

        # 初始化时间偏移
        self._sync_server_time()

        logger.info(f"币安连接器初始化完成 (testnet={testnet})")

    def _sync_server_time(self):
        """同步服务器时间"""
        try:
            response = self.session.get(
                f"{self.base_url}/fapi/{self.API_VERSION}/time", timeout=self.TIMEOUT
            )
            data = response.json()
            server_time = data["serverTime"]
            local_time = int(time.time() * 1000)
            self.server_time_offset = server_time - local_time
            logger.debug(f"服务器时间同步完成，偏移：{self.server_time_offset}ms")
        except Exception as e:
            logger.warning(f"服务器时间同步失败：{e}")

    def _get_timestamp(self) -> int:
        """获取带时间戳的服务器时间"""
        return int(time.time() * 1000) + self.server_time_offset

    def _sign(self, params: Dict) -> str:
        """生成签名"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.secret_key.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return signature

    def _request(
        self, method: str, path: str, params: Optional[Dict] = None, signed: bool = False
    ) -> Dict:
        """
        发送 API 请求

        Args:
            method: HTTP 方法
            path: API 路径
            params: 请求参数
            signed: 是否需要签名

        Returns:
            Dict: 响应数据

        Raises:
            NetworkException: 网络错误
            RateLimitException: 限流
            ExchangeException: 交易所错误
        """
        url = f"{self.base_url}{path}"

        if params is None:
            params = {}

        # 添加默认参数
        if signed:
            params["timestamp"] = self._get_timestamp()
            params["recvWindow"] = 5000  # 5 秒接收窗口
            # 签名必须在所有参数添加后计算
            params["signature"] = self._sign(params)

        try:
            # GET 请求使用 params，POST 请求使用 data
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            else:
                response = self.session.post(url, data=params, timeout=self.TIMEOUT)

            data = response.json()

            # 检查错误
            if "code" in data and data["code"] != 200:
                error_code = data.get("code")
                error_msg = data.get("msg", str(data))

                # 错误码处理
                if error_code == -1021:  # 时间偏移
                    self._sync_server_time()
                    raise NetworkException("时间偏移，已重新同步")
                elif error_code == -1003:  # 限流
                    raise RateLimitException(f"请求频率超限：{error_msg}")
                elif error_code == -2021:  # 余额不足
                    raise InsufficientBalanceException(error_msg)
                else:
                    raise ExchangeException(error_msg, f"EXCHANGE_{error_code}")

            return data

        except requests.exceptions.Timeout:
            raise NetworkException("请求超时")
        except requests.exceptions.ConnectionError:
            raise NetworkException("连接失败")
        except Exception as e:
            if isinstance(
                e,
                (
                    NetworkException,
                    RateLimitException,
                    InsufficientBalanceException,
                    ExchangeException,
                ),
            ):
                raise
            raise NetworkException(f"请求失败：{str(e)}")

    # ==================== IConnector 接口实现 ====================

    def get_account_balance(self) -> Result:
        """
        获取账户余额

        Returns:
            Result: 账户余额信息
        """
        try:
            data = self._request("GET", "/fapi/v2/balance", signed=True)

            # 解析余额
            balances = []
            for item in data:
                available = Decimal(item.get("availableBalance", "0"))
                total = Decimal(item.get("walletBalance", "0"))
                if available > 0 or total > 0:
                    balances.append(
                        {
                            "asset": item["asset"],
                            "available": available,
                            "total": total,
                            "locked": total - available,
                        }
                    )

            return ok(data={"balances": balances}, message="获取余额成功")

        except Exception as e:
            logger.error(f"获取余额失败：{e}")
            return fail(error_code="GET_BALANCE_FAILED", message=str(e))

    def get_positions(self) -> Result:
        """
        获取持仓

        Returns:
            Result: 持仓信息
        """
        try:
            data = self._request("GET", "/fapi/v2/positionRisk", signed=True)

            # 解析持仓
            positions = []
            for item in data:
                position_amt = Decimal(item.get("positionAmt", "0"))
                if position_amt != 0:
                    positions.append(
                        {
                            "symbol": item["symbol"],
                            "side": "LONG" if position_amt > 0 else "SHORT",
                            "size": abs(position_amt),
                            "entry_price": Decimal(item.get("entryPrice", "0")),
                            "mark_price": Decimal(item.get("markPrice", "0")),
                            "unrealized_pnl": Decimal(item.get("unRealizedProfit", "0")),
                            "leverage": int(item.get("leverage", 1)),
                            "margin": Decimal(item.get("positionInitialMargin", "0")),
                        }
                    )

            return ok(data={"positions": positions}, message="获取持仓成功")

        except Exception as e:
            logger.error(f"获取持仓失败：{e}")
            return fail(error_code="GET_POSITIONS_FAILED", message=str(e))

    def place_order(self, order: Order) -> Result:
        """
        下单

        Args:
            order: 订单对象

        Returns:
            Result: 订单结果
        """
        try:
            # 构建请求参数
            params = {
                "symbol": order.symbol,
                "side": order.side.value,
                "type": order.type.value,
                "quantity": str(order.quantity),
            }

            # 限价单添加价格
            if order.type == OrderType.LIMIT:
                params["price"] = str(order.price)
                params["timeInForce"] = "GTC"

            # 止损单添加止损价
            if order.type in [OrderType.STOP_MARKET, OrderType.STOP_LIMIT]:
                params["stopPrice"] = str(order.stop_price)

            # 发送请求
            data = self._request("POST", "/fapi/v1/order", params=params, signed=True)

            # 解析订单
            order_result = {
                "order_id": str(data.get("orderId", "")),
                "symbol": data.get("symbol", ""),
                "side": data.get("side", ""),
                "type": data.get("type", ""),
                "quantity": Decimal(data.get("origQty", "0")),
                "price": Decimal(data.get("price", "0")) if data.get("price") else None,
                "avg_price": Decimal(data.get("avgPrice", "0")) if data.get("avgPrice") else None,
                "filled_quantity": Decimal(data.get("executedQty", "0")),
                "status": data.get("status", ""),
                "created_time": data.get("time", data.get("transactTime", 0)),
            }

            return ok(data=order_result, message="订单已创建")

        except Exception as e:
            logger.error(f"下单失败：{e}")
            return fail(error_code="PLACE_ORDER_FAILED", message=str(e))

    def cancel_order(self, symbol: str, order_id: str) -> Result:
        """
        取消订单

        Args:
            symbol: 交易对
            order_id: 订单 ID

        Returns:
            Result: 取消结果
        """
        try:
            params = {"symbol": symbol, "orderId": order_id}

            data = self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

            return ok(
                data={"order_id": order_id, "symbol": symbol, "status": "CANCELED"},
                message="订单已取消",
            )

        except Exception as e:
            logger.error(f"取消订单失败：{e}")
            return fail(error_code="CANCEL_ORDER_FAILED", message=str(e))

    def get_precision_info(self, symbol: str) -> Dict:
        """
        获取精度信息

        Args:
            symbol: 交易对

        Returns:
            Dict: 精度信息（stepSize, tickSize）
        """
        try:
            data = self._request("GET", "/fapi/v1/exchangeInfo")

            # 查找交易对
            for s in data.get("symbols", []):
                if s["symbol"] == symbol:
                    # 查找数量精度
                    for f in s.get("filters", []):
                        if f["filterType"] == "LOT_SIZE":
                            step_size = Decimal(f["stepSize"])
                        elif f["filterType"] == "PRICE_FILTER":
                            tick_size = Decimal(f["tickSize"])

                    return {
                        "step_size": step_size,
                        "tick_size": tick_size,
                        "min_qty": Decimal(s["filters"][0].get("minQty", "0")),
                        "max_qty": Decimal(s["filters"][0].get("maxQty", "0")),
                    }

            return {}

        except Exception as e:
            logger.error(f"获取精度信息失败：{e}")
            return {}

    def health_check(self) -> Result:
        """
        健康检查

        Returns:
            Result: 健康状态
        """
        try:
            # 简单检查：获取服务器时间
            url = f"{self.base_url}/fapi/v1/time"
            response = self.session.get(url, timeout=self.TIMEOUT)
            
            if response.status_code == 200:
                return ok(data={"status": "ok", "testnet": self.testnet, "url": self.base_url}, message="健康检查通过")
            else:
                return fail(error_code="HEALTH_CHECK_FAILED", message=f"HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"健康检查失败：{e}")
            return fail(error_code="HEALTH_CHECK_FAILED", message=str(e))

    # ==================== 额外功能 ====================

    def get_ticker(self, symbol: str) -> Result:
        """
        获取 Ticker

        Args:
            symbol: 交易对

        Returns:
            Result: Ticker 信息
        """
        try:
            params = {"symbol": symbol}
            data = self._request("GET", "/fapi/v1/ticker/24hr", params=params)

            return ok(
                data={
                    "symbol": data["symbol"],
                    "price": Decimal(data["lastPrice"]),
                    "change_24h": Decimal(data["priceChangePercent"]),
                    "volume_24h": Decimal(data["volume"]),
                    "high_24h": Decimal(data["highPrice"]),
                    "low_24h": Decimal(data["lowPrice"]),
                }
            )

        except Exception as e:
            return fail(error_code="GET_TICKER_FAILED", message=str(e))

    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> Result:
        """
        获取 K 线数据

        Args:
            symbol: 交易对
            interval: 时间周期（1m, 5m, 15m, 1h, 4h, 1d）
            limit: 数量（最多 1500）

        Returns:
            Result: K 线数据
        """
        try:
            params = {"symbol": symbol, "interval": interval, "limit": limit}

            data = self._request("GET", "/fapi/v1/klines", params=params)

            # 解析 K 线
            klines = []
            for k in data:
                klines.append(
                    {
                        "timestamp": k[0],
                        "open": Decimal(k[1]),
                        "high": Decimal(k[2]),
                        "low": Decimal(k[3]),
                        "close": Decimal(k[4]),
                        "volume": Decimal(k[5]),
                    }
                )

            return ok(data={"klines": klines, "symbol": symbol, "interval": interval})

        except Exception as e:
            return fail(error_code="GET_KLINES_FAILED", message=str(e))

    def get_open_orders(self, symbol: Optional[str] = None) -> Result:
        """
        获取当前挂单

        Args:
            symbol: 交易对（可选，不传获取所有）

        Returns:
            Result: 挂单列表
        """
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol

            data = self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

            orders = []
            for o in data:
                orders.append(
                    {
                        "order_id": str(o["orderId"]),
                        "symbol": o["symbol"],
                        "side": o["side"],
                        "type": o["type"],
                        "quantity": Decimal(o["origQty"]),
                        "price": Decimal(o["price"]),
                        "filled_quantity": Decimal(o["executedQty"]),
                        "status": o["status"],
                    }
                )

            return ok(data={"orders": orders})

        except Exception as e:
            return fail(error_code="GET_OPEN_ORDERS_FAILED", message=str(e))

    def create_stop_loss_order(
        self, symbol: str, side: str, quantity: Decimal, stop_price: Decimal = None, trigger_price: Decimal = None
    ) -> Result:
        """
        创建止损单（使用 Algo Order API）
        参考：/home/admin/.openclaw/workspace/quant/history/docs/report/币安 Algo Order API 完全实现.md

        Args:
            symbol: 交易对
            side: 方向（BUY/SELL）
            quantity: 数量
            stop_price: 止损触发价

        Returns:
            Result: 止损单结果
        """
        price = stop_price if stop_price is not None else trigger_price
        
        try:
            # 使用 Algo Order API（参考历史文档）
            # 关键参数：algoType=CONDITIONAL, triggerPrice（不是 stopPrice）
            params = {
                "symbol": symbol,
                "side": side,
                "algoType": "CONDITIONAL",  # 只支持 CONDITIONAL
                "type": "STOP_MARKET",
                "triggerPrice": str(price),  # 使用 triggerPrice（不是 stopPrice）
                "quantity": str(quantity),
                "reduceOnly": "false",
                "newOrderRespType": "ACK"
            }

            # 发送到 Algo Order API 专用端点（参考历史文档）
            data = self._request("POST", "/fapi/v1/algoOrder", params=params, signed=True)

            # 解析结果（参考历史文档返回 algoId）
            result = {
                "algo_id": str(data.get("orderId", "")),
                "symbol": data.get("symbol", ""),
                "side": data.get("side", ""),
                "trigger_price": str(price),
                "quantity": str(quantity),
                "status": data.get("orderStatus", data.get("status", "")),
                "algoType": data.get("algoType", "CONDITIONAL")
            }

            return ok(data=result, message="止损单已创建")

        except Exception as e:
            logger.error(f"止损单创建失败：{e}")
            return fail(error_code="CREATE_STOP_LOSS_FAILED", message=str(e))
    
    def cancel_algo_order(self, symbol: str, algo_id: str) -> Result:
        """
        取消 Algo 订单（止损单/止盈单）
        参考：/home/admin/.openclaw/workspace/quant/history/docs/report/币安 Algo Order API 完全实现.md

        Args:
            symbol: 交易对
            algo_id: Algo 订单 ID

        Returns:
            Result: 取消结果
        """
        try:
            params = {
                "symbol": symbol,
                "algoId": algo_id
            }

            # 取消 Algo 订单
            data = self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

            result = {
                "algo_id": algo_id,
                "symbol": symbol,
                "status": data.get("orderStatus", "CANCELED")
            }

            return ok(data=result, message="Algo 订单已取消")

        except Exception as e:
            logger.error(f"取消 Algo 订单失败：{e}")
            return fail(error_code="CANCEL_ALGO_ORDER_FAILED", message=str(e))
    
    def get_algo_orders(self, symbol: str = None, limit: int = 50) -> Result:
        """
        获取 Algo 订单列表（止损单/止盈单）
        参考：/home/admin/.openclaw/workspace/quant/history/docs/report/币安 Algo Order API 完全实现.md
        注意：币安测试网 Algo Order API 端点可能不可用，使用普通订单 API 替代

        Args:
            symbol: 交易对（可选）
            limit: 数量限制

        Returns:
            Result: Algo 订单列表
        """
        try:
            # 获取所有挂单（包含止损单）
            params = {}
            if symbol:
                params["symbol"] = symbol

            # 使用普通订单 API 获取挂单
            data = self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

            # 筛选止损单和止盈单
            orders = []
            for order in data:
                order_type = order.get("type", "")
                if order_type in ["STOP_MARKET", "TAKE_PROFIT_MARKET", "STOP", "TAKE_PROFIT"]:
                    orders.append({
                        "algo_id": str(order.get("orderId", "")),
                        "symbol": order.get("symbol", ""),
                        "side": order.get("side", ""),
                        "type": order_type,
                        "trigger_price": order.get("stopPrice", ""),
                        "quantity": order.get("origQty", ""),
                        "status": order.get("status", "")
                    })

            return ok(data={"orders": orders, "count": len(orders)}, message="Algo 订单列表获取成功")

        except Exception as e:
            logger.error(f"获取 Algo 订单失败：{e}")
            return fail(error_code="GET_ALGO_ORDERS_FAILED", message=str(e))
    
    def check_stop_loss_exists(self, symbol: str, side: str = None) -> Result:
        """
        检查指定交易对是否已有活跃止损单（查重机制）
        参考：/home/admin/.openclaw/workspace/quant/history/docs/report/币安 Algo Order API 完全实现.md

        Args:
            symbol: 交易对
            side: 方向（可选，BUY/SELL）

        Returns:
            Result: 查重结果
        """
        try:
            # 获取该交易对的所有 Algo 订单
            result = self.get_algo_orders(symbol=symbol, limit=100)
            
            if not result.is_success:
                return fail(
                    error_code="CHECK_STOP_LOSS_FAILED",
                    message=f"获取 Algo 订单失败：{result.message}"
                )
            
            orders = result.data.get("orders", [])
            
            # 筛选止损单（STOP_MARKET 或 TAKE_PROFIT_MARKET）
            stop_orders = [
                o for o in orders 
                if o.get("type") in ["STOP_MARKET", "TAKE_PROFIT_MARKET"]
                and o.get("status") in ["NEW", "PARTIALLY_FILLED"]
            ]
            
            # 如果指定了方向，进一步筛选
            if side:
                stop_orders = [o for o in stop_orders if o.get("side") == side]
            
            if stop_orders:
                # 已有活跃止损单
                return ok(
                    data={
                        "exists": True,
                        "count": len(stop_orders),
                        "orders": stop_orders
                    },
                    message=f"{symbol} 已有 {len(stop_orders)} 个活跃止损单"
                )
            else:
                # 没有活跃止损单
                return ok(
                    data={"exists": False, "count": 0, "orders": []},
                    message=f"{symbol} 没有活跃止损单"
                )
            
        except Exception as e:
            logger.error(f"止损单查重失败：{e}")
            return fail(error_code="CHECK_STOP_LOSS_FAILED", message=str(e))

    def cancel_stop_loss_order(self, symbol: str, order_id: str) -> Result:
        """
        取消止损单

        Args:
            symbol: 交易对
            order_id: 订单 ID

        Returns:
            Result: 取消结果
        """
        return self.cancel_order(symbol, order_id)
