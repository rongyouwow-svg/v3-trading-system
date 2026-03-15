#!/usr/bin/env python3
"""
📊 持仓管理器 v3.1

职责:
    - 持仓同步（从交易所获取真实持仓）
    - 持仓缓存（本地缓存，减少 API 调用）
    - 持仓更新监听（分批建仓场景）

特性:
    - 自动同步（每次调用从交易所获取）
    - 缓存机制（减少 API 调用频率）
    - 精度处理（币安精度要求）

用法:
    from core.execution.position_manager import PositionManager
    
    manager = PositionManager(connector)
    position = manager.sync_position('ETHUSDT')
    positions = manager.get_all_positions()
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class PositionManager:
    """
    持仓管理器
    
    核心功能:
        - 持仓同步
        - 持仓缓存
        - 精度处理
    """
    
    def __init__(self, connector: Any, cache_ttl: int = 5):
        """
        初始化持仓管理器
        
        Args:
            connector: 币安连接器
            cache_ttl: 缓存过期时间（秒，默认 5 秒）
        """
        self.connector = connector
        self.cache_ttl = cache_ttl
        
        # 持仓缓存 {symbol: {'position': data, 'timestamp': datetime}}
        self.position_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"✅ 持仓管理器初始化完成 (缓存 TTL: {cache_ttl}秒)")
    
    def sync_position(self, symbol: str, force: bool = False) -> Optional[Dict[str, Any]]:
        """
        同步持仓（从交易所获取真实持仓）
        
        Args:
            symbol: 交易对（如 'ETHUSDT'）
            force: 是否强制刷新（忽略缓存）
        
        Returns:
            持仓信息（无持仓返回 None）
        """
        # 检查缓存
        if not force and symbol in self.position_cache:
            cache = self.position_cache[symbol]
            age = (datetime.now() - cache['timestamp']).total_seconds()
            
            if age < self.cache_ttl:
                logger.debug(f"📊 使用缓存持仓：{symbol} (缓存时间：{age:.1f}秒)")
                return cache['position']
        
        # 从交易所获取持仓
        try:
            positions = self.connector.get_positions(symbol)
            
            # 查找对应持仓
            position_data = None
            for pos in positions:
                if pos['symbol'] == symbol and float(pos['positionAmt']) != 0:
                    position_data = {
                        'symbol': pos['symbol'],
                        'side': 'LONG' if float(pos['positionAmt']) > 0 else 'SHORT',
                        'size': abs(float(pos['positionAmt'])),
                        'entry_price': float(pos['entryPrice']),
                        'current_price': float(pos.get('markPrice', pos['entryPrice'])),
                        'leverage': int(pos.get('leverage', 1)),
                        'unrealized_pnl': float(pos.get('unRealizedProfit', 0)),
                        'unrealized_pnl_pct': float(pos.get('unRealizedProfit', 0)) / (float(pos['entryPrice']) * abs(float(pos['positionAmt']))) * 100 if float(pos['entryPrice']) * abs(float(pos['positionAmt'])) > 0 else 0,
                        'liquidation_price': float(pos.get('liquidationPrice', 0)),
                        'last_update': datetime.now()
                    }
                    break
            
            # 更新缓存
            if position_data:
                self.position_cache[symbol] = {
                    'position': position_data,
                    'timestamp': datetime.now()
                }
                logger.info(f"📊 持仓同步成功：{symbol} {position_data['side']} {position_data['size']} @ {position_data['entry_price']}")
            else:
                # 无持仓，清除缓存
                if symbol in self.position_cache:
                    del self.position_cache[symbol]
                logger.debug(f"📊 无持仓：{symbol}")
            
            return position_data
            
        except Exception as e:
            logger.error(f"❌ 持仓同步失败：{symbol} - {e}")
            
            # 返回缓存（如果有）
            if symbol in self.position_cache:
                logger.warning(f"⚠️ 使用过期缓存：{symbol}")
                return self.position_cache[symbol]['position']
            
            return None
    
    def get_all_positions(self, force: bool = False) -> List[Dict[str, Any]]:
        """
        获取所有持仓
        
        Args:
            force: 是否强制刷新
        
        Returns:
            持仓列表
        """
        try:
            positions = self.connector.get_positions()
            
            position_list = []
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    position_data = {
                        'symbol': pos['symbol'],
                        'side': 'LONG' if float(pos['positionAmt']) > 0 else 'SHORT',
                        'size': abs(float(pos['positionAmt'])),
                        'entry_price': float(pos['entryPrice']),
                        'current_price': float(pos.get('markPrice', pos['entryPrice'])),
                        'leverage': int(pos.get('leverage', 1)),
                        'unrealized_pnl': float(pos.get('unRealizedProfit', 0)),
                        'unrealized_pnl_pct': float(pos.get('unRealizedProfit', 0)) / (float(pos['entryPrice']) * abs(float(pos['positionAmt']))) * 100 if float(pos['entryPrice']) * abs(float(pos['positionAmt'])) > 0 else 0,
                        'liquidation_price': float(pos.get('liquidationPrice', 0)),
                        'last_update': datetime.now()
                    }
                    position_list.append(position_data)
                    
                    # 更新缓存
                    self.position_cache[pos['symbol']] = {
                        'position': position_data,
                        'timestamp': datetime.now()
                    }
            
            logger.info(f"📊 获取所有持仓成功：{len(position_list)} 个持仓")
            return position_list
            
        except Exception as e:
            logger.error(f"❌ 获取所有持仓失败：{e}")
            
            # 返回缓存
            if self.position_cache:
                logger.warning(f"⚠️ 使用缓存持仓：{len(self.position_cache)} 个")
                return [cache['position'] for cache in self.position_cache.values()]
            
            return []
    
    def clear_cache(self, symbol: Optional[str] = None):
        """
        清除缓存
        
        Args:
            symbol: 交易对（可选，不传则清除所有）
        """
        if symbol:
            if symbol in self.position_cache:
                del self.position_cache[symbol]
                logger.info(f"✅ 清除持仓缓存：{symbol}")
        else:
            self.position_cache.clear()
            logger.info("✅ 清除所有持仓缓存")
    
    def get_position_value(self, symbol: str) -> Decimal:
        """
        获取持仓价值（USDT）
        
        Args:
            symbol: 交易对
        
        Returns:
            持仓价值
        """
        position = self.sync_position(symbol)
        
        if not position:
            return Decimal('0')
        
        return Decimal(str(position['size'])) * Decimal(str(position['entry_price']))
    
    def get_total_position_value(self) -> Decimal:
        """
        获取总持仓价值（USDT）
        
        Returns:
            总持仓价值
        """
        positions = self.get_all_positions()
        
        total = Decimal('0')
        for pos in positions:
            total += Decimal(str(pos['size'])) * Decimal(str(pos['entry_price']))
        
        return total
    
    def check_position_exists(self, symbol: str) -> bool:
        """
        检查持仓是否存在
        
        Args:
            symbol: 交易对
        
        Returns:
            是否存在持仓
        """
        position = self.sync_position(symbol)
        return position is not None
    
    def get_position_side(self, symbol: str) -> Optional[str]:
        """
        获取持仓方向
        
        Args:
            symbol: 交易对
        
        Returns:
            持仓方向（LONG/SHORT/None）
        """
        position = self.sync_position(symbol)
        return position['side'] if position else None
    
    def get_position_size(self, symbol: str) -> Decimal:
        """
        获取持仓数量
        
        Args:
            symbol: 交易对
        
        Returns:
            持仓数量
        """
        position = self.sync_position(symbol)
        return Decimal(str(position['size'])) if position else Decimal('0')
    
    def get_unrealized_pnl(self, symbol: str) -> Decimal:
        """
        获取未实现盈亏（USDT）
        
        Args:
            symbol: 交易对
        
        Returns:
            未实现盈亏
        """
        position = self.sync_position(symbol)
        return Decimal(str(position['unrealized_pnl'])) if position else Decimal('0')
    
    def get_unrealized_pnl_pct(self, symbol: str) -> Decimal:
        """
        获取未实现盈亏比例（%）
        
        Args:
            symbol: 交易对
        
        Returns:
            未实现盈亏比例
        """
        position = self.sync_position(symbol)
        return Decimal(str(position['unrealized_pnl_pct'])) if position else Decimal('0')
    
    def shutdown(self):
        """
        关闭持仓管理器
        """
        logger.info("🛑 关闭持仓管理器")
        self.clear_cache()
        logger.info("✅ 持仓管理器已关闭")
