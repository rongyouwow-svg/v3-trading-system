#!/usr/bin/env python3
"""
🦞 模拟账户模块
实现模拟交易功能
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

class SimulatedAccount:
    """模拟交易账户"""
    
    def __init__(self, initial_capital: float = 100.0):
        """
        初始化模拟账户
        
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: Dict[str, Dict] = {}
        self.trades: List[Dict] = []
        self.trade_id = 0
        self.notifications = deque(maxlen=100)
        self.state_file = '/tmp/sim_state_v6.json'
        self.load()
    
    def load(self):
        """从文件加载状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.initial_capital = data.get('icap', self.initial_capital)
                    self.capital = data.get('cap', self.initial_capital)
                    self.positions = data.get('pos', {})
                    self.trades = data.get('trades', [])
                    self.trade_id = data.get('tid', 0)
                    notifs = data.get('notifs', [])
                    self.notifications = deque(notifs, 100)
            except Exception as e:
                print(f"加载状态失败：{e}")
    
    def save(self):
        """保存状态到文件"""
        data = {
            'icap': self.initial_capital,
            'cap': self.capital,
            'pos': self.positions,
            'trades': self.trades,
            'tid': self.trade_id,
            'notifs': list(self.notifications)
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def notify(self, title: str, message: str = None):
        """添加通知"""
        notif = {
            'time': datetime.now().isoformat(),
            'title': title,
            'message': message
        }
        self.notifications.append(notif)
        print(f"📢 {title}: {message}")
        self.save()
    
    def open(self, symbol: str, side: str, quantity: float, price: float,
             stop_loss: float = 0, take_profit: float = 0, 
             grade: str = 'C', leverage: int = 1) -> Dict:
        """
        开仓
        
        Args:
            symbol: 交易对
            side: long/short
            quantity: 数量
            price: 价格
            stop_loss: 止损价
            take_profit: 止盈价
            grade: 信号等级
            leverage: 杠杆
            
        Returns:
            开仓结果
        """
        required = quantity * price / leverage
        
        if required > self.capital:
            self.notify('❌ 开仓失败', f'资金不足 ${required:.2f}')
            return {'success': False, 'error': f'资金不足，需要${required:.2f}'}
        
        self.capital -= required
        
        self.positions[symbol] = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'grade': grade,
            'leverage': leverage,
            'time': datetime.now().isoformat()
        }
        
        self.notify('🔓 开仓', f"{grade}级 {side.upper()} {symbol} {quantity:.4f} @ ${price} ({leverage}x)")
        self.save()
        
        return {
            'success': True,
            'position': self.positions[symbol]
        }
    
    def close(self, symbol: str, price: float) -> Dict:
        """
        平仓
        
        Args:
            symbol: 交易对
            price: 平仓价格
            
        Returns:
            平仓结果
        """
        if symbol not in self.positions:
            return {'success': False, 'error': '无此持仓'}
        
        pos = self.positions[symbol]
        pnl = (price - pos['price']) * pos['quantity']
        if pos['side'] == 'short':
            pnl = (pos['price'] - price) * pos['quantity']
        
        pnl_pct = (pnl / (pos['price'] * pos['quantity'])) * 100
        
        # 返还保证金 + 盈亏
        required = pos['quantity'] * pos['price'] / pos['leverage']
        self.capital += required + pnl
        
        self.trade_id += 1
        self.trades.append({
            'id': self.trade_id,
            'symbol': symbol,
            'side': pos['side'],
            'quantity': pos['quantity'],
            'entry': pos['price'],
            'exit': price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'grade': pos.get('grade', ''),
            'time': datetime.now().isoformat()
        })
        
        del self.positions[symbol]
        
        self.notify('🔒 平仓', f"{'✅' if pnl >= 0 else '❌'} {symbol} | 盈亏：${pnl:.2f} ({pnl_pct:+.2f}%)")
        self.save()
        
        return {
            'success': True,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'trade': self.trades[-1]
        }
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        position_value = sum(
            p['quantity'] * p['price'] / p.get('leverage', 1)
            for p in self.positions.values()
        )
        
        return {
            'initial_capital': self.initial_capital,
            'available_capital': self.capital,
            'position_value': position_value,
            'total_value': self.capital + position_value,
            'positions_count': len(self.positions),
            'total_trades': len(self.trades),
            'unrealized_pnl': 0  # 简化处理
        }
    
    def get_positions(self) -> List[Dict]:
        """获取持仓列表"""
        return list(self.positions.values())
    
    def get_trades(self, limit: int = 50) -> List[Dict]:
        """获取交易历史"""
        return self.trades[-limit:]
    
    def get_notifications(self, limit: int = 20) -> List[Dict]:
        """获取通知列表"""
        return list(self.notifications)[-limit:]
    
    def reset(self, new_capital: float = 100.0):
        """重置账户"""
        self.initial_capital = new_capital
        self.capital = new_capital
        self.positions = {}
        self.trades = []
        self.trade_id = 0
        self.notifications.clear()
        self.save()
        self.notify('🔄 账户已重置', f'初始资金：${new_capital}')
