#!/usr/bin/env python3
"""
💰 资金管理引擎

职责:
    - 仓位计算
    - PnL 计算
    - 手续费统计
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CapitalEngine:
    """资金管理引擎"""
    
    def __init__(self):
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.positions: Dict[str, Dict[str, Any]] = {}
    
    def update_account(self, account_id: str, balance: float, available: float):
        """更新账户信息"""
        self.accounts[account_id] = {
            'balance': balance,
            'available': available,
            'locked': balance - available,
            'updated_at': datetime.now().isoformat()
        }
        logger.debug(f"💰 账户已更新：{account_id}")
    
    def calculate_position_size(self, amount: float, price: float, leverage: int) -> float:
        """
        计算仓位大小
        
        Args:
            amount: 保证金
            price: 价格
            leverage: 杠杆
        
        Returns:
            仓位大小
        """
        if price <= 0:
            return 0
        
        position_value = amount * leverage
        position_size = position_value / price
        
        return position_size
    
    def calculate_pnl(self, entry_price: float, current_price: float, position_size: float, side: str) -> float:
        """
        计算盈亏
        
        Args:
            entry_price: 入场价
            current_price: 当前价
            position_size: 仓位大小
            side: 方向 (LONG/SHORT)
        
        Returns:
            盈亏
        """
        if side.upper() == 'LONG':
            pnl = (current_price - entry_price) * position_size
        else:
            pnl = (entry_price - current_price) * position_size
        
        return pnl
    
    def calculate_pnl_pct(self, entry_price: float, current_price: float, side: str) -> float:
        """
        计算盈亏百分比
        
        Args:
            entry_price: 入场价
            current_price: 当前价
            side: 方向 (LONG/SHORT)
        
        Returns:
            盈亏百分比
        """
        if entry_price <= 0:
            return 0
        
        if side.upper() == 'LONG':
            pnl_pct = (current_price - entry_price) / entry_price * 100
        else:
            pnl_pct = (entry_price - current_price) / entry_price * 100
        
        return pnl_pct
    
    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """获取账户信息"""
        return self.accounts.get(account_id)
    
    def update_position(self, symbol: str, position_data: Dict[str, Any]):
        """更新持仓"""
        self.positions[symbol] = {
            **position_data,
            'updated_at': datetime.now().isoformat()
        }
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取持仓"""
        return self.positions.get(symbol)
