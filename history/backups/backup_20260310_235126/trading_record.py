#!/usr/bin/env python3
"""
🦞 交易记录模块
负责交易记录的生成、存储、查询
"""

import json
import os
from datetime import datetime
from typing import Dict, List

TRADES_FILE = '/tmp/trading_records.json'

class TradingRecord:
    """交易记录管理器"""
    
    def __init__(self):
        self.trades_file = TRADES_FILE
        self.trades = self.load_trades()
    
    def load_trades(self) -> List[Dict]:
        """加载交易记录"""
        if os.path.exists(self.trades_file):
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_trades(self):
        """保存交易记录"""
        with open(self.trades_file, 'w', encoding='utf-8') as f:
            json.dump(self.trades, f, indent=2, ensure_ascii=False)
    
    def add_trade(self, trade: Dict):
        """
        添加交易记录
        
        Args:
            trade: 交易记录字典
        """
        self.trades.append(trade)
        self.save_trades()
    
    def create_trade_record(self, symbol: str, side: str, action: str,
                           quantity: float, price: float, 
                           strategy: str, signal_reason: str,
                           pnl: float = 0, pnl_pct: float = 0,
                           status: str = 'pending',
                           stop_loss_price: float = None,
                           stop_order_id: int = None,
                           trade_type: str = None,
                           details: Dict = None) -> Dict:
        """
        创建交易记录（优化版）
        
        Args:
            symbol: 交易对
            side: LONG/SHORT
            action: OPEN/CLOSE
            quantity: 数量
            price: 价格
            strategy: 策略名称
            signal_reason: 信号原因
            pnl: 盈亏（平仓时）
            pnl_pct: 盈亏百分比（平仓时）
            status: pending/executed/failed
            stop_loss_price: 止损价格（开仓时）
            stop_order_id: 止损单 ID（开仓时）
            trade_type: 交易类型（strategy_open/strategy_add/strategy_close/manual_open/manual_close）
            details: 详细信息（杠杆、保证金、仓位价值等）
            
        Returns:
            交易记录
        """
        # 自动判断交易类型
        if trade_type is None:
            if strategy and strategy != 'manual':
                if action == 'OPEN':
                    trade_type = 'strategy_open'
                elif action == 'ADD':
                    trade_type = 'strategy_add'
                else:
                    trade_type = 'strategy_close'
            else:
                trade_type = 'manual_open' if action == 'OPEN' else 'manual_close'
        
        # 构建详细信息
        if details is None:
            details = {}
        
        trade = {
            'id': len(self.trades) + 1,
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'action': action,
            'quantity': quantity,
            'price': price,
            'amount': quantity * price,
            'strategy': strategy,
            'signal_reason': signal_reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'status': status,
            'exchange': 'binance_testnet',
            'notes': '',
            'stop_loss_price': stop_loss_price,
            'stop_order_id': stop_order_id,
            'trade_type': trade_type,  # 交易类型（策略/手动）
            'details': details  # 详细信息
        }
        
        self.add_trade(trade)
        return trade
    
    def update_trade_status(self, trade_id: int, status: str, 
                           exchange_order_id: str = None,
                           notes: str = None) -> Dict:
        """
        更新交易状态
        
        Args:
            trade_id: 交易 ID
            status: executed/failed
            exchange_order_id: 交易所订单 ID
            notes: 备注
            
        Returns:
            更新后的交易记录
        """
        for trade in self.trades:
            if trade['id'] == trade_id:
                trade['status'] = status
                if exchange_order_id:
                    trade['exchange_order_id'] = exchange_order_id
                if notes:
                    trade['notes'] = notes
                self.save_trades()
                return trade
        
        return None
    
    def get_trades(self, limit: int = 50, symbol: str = None, 
                   status: str = None) -> List[Dict]:
        """
        获取交易记录
        
        Args:
            limit: 限制数量
            symbol: 交易对筛选
            status: 状态筛选
            
        Returns:
            交易记录列表
        """
        trades = self.trades.copy()
        
        # 筛选
        if symbol:
            trades = [t for t in trades if t['symbol'] == symbol]
        if status:
            trades = [t for t in trades if t['status'] == status]
        
        # 排序（最新的在前）
        trades.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 限制数量
        return trades[:limit]
    
    def get_trade_stats(self, symbol: str = None) -> Dict:
        """
        获取交易统计
        
        Args:
            symbol: 交易对
            
        Returns:
            统计数据
        """
        trades = self.get_trades(limit=1000, symbol=symbol, status='executed')
        
        if not trades:
            return {
                'total_trades': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'win_trades': 0,
                'loss_trades': 0,
                'avg_pnl': 0
            }
        
        total_pnl = sum(t['pnl'] for t in trades)
        win_trades = [t for t in trades if t['pnl'] > 0]
        loss_trades = [t for t in trades if t['pnl'] <= 0]
        
        return {
            'total_trades': len(trades),
            'total_pnl': total_pnl,
            'win_rate': len(win_trades) / len(trades) * 100,
            'win_trades': len(win_trades),
            'loss_trades': len(loss_trades),
            'avg_pnl': total_pnl / len(trades),
            'best_trade': max(trades, key=lambda x: x['pnl'])['pnl'],
            'worst_trade': min(trades, key=lambda x: x['pnl'])['pnl']
        }
    
    def clear_trades(self):
        """清空交易记录"""
        self.trades = []
        self.save_trades()


# 全局实例
trading_record = TradingRecord()
