#!/usr/bin/env python3
"""
📡 行情数据层

职责:
    - K 线数据管理
    - Ticker 缓存
    - 数据补全
    - 质量校验
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketDataEngine:
    """行情数据引擎"""
    
    def __init__(self):
        self.tickers: Dict[str, Dict[str, Any]] = {}
        self.klines: Dict[str, List[Dict[str, Any]]] = {}
    
    def update_ticker(self, symbol: str, ticker_data: Dict[str, Any]):
        """更新 Ticker 数据"""
        self.tickers[symbol] = {
            **ticker_data,
            'updated_at': datetime.now().isoformat()
        }
        logger.debug(f"📊 Ticker 已更新：{symbol}")
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取 Ticker"""
        return self.tickers.get(symbol)
    
    def update_klines(self, symbol: str, interval: str, klines: List[Dict[str, Any]]):
        """更新 K 线数据"""
        key = f"{symbol}_{interval}"
        self.klines[key] = klines
        logger.debug(f"📊 K 线已更新：{key}")
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取 K 线数据"""
        key = f"{symbol}_{interval}"
        klines = self.klines.get(key, [])
        return klines[-limit:]
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """获取最新价格"""
        ticker = self.get_ticker(symbol)
        if ticker:
            return ticker.get('price')
        return None
