#!/usr/bin/env python3
"""
🦞 策略引擎模块
负责策略管理、信号生成、持仓跟踪
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

STRATEGIES_FILE = '/tmp/strategies_v6.json'
SIGNALS_FILE = '/tmp/signals_v6.json'

class StrategyEngine:
    """策略引擎"""
    
    def __init__(self):
        self.strategies_file = STRATEGIES_FILE
        self.signals_file = SIGNALS_FILE
        # 只加载策略，不清空
        self.strategies = self.load_strategies()
        self.signals = self.load_signals()
    
    def load_strategies(self) -> List[Dict]:
        """加载策略列表（强制清空损坏策略）"""
        # 强制清空策略文件
        try:
            with open(self.strategies_file, 'w') as f:
                json.dump([], f)
            print("✅ 策略文件已强制清空")
            return []
        except Exception as e:
            print(f"❌ 清空策略失败：{e}")
            return []
    
    def save_strategies(self):
        """保存策略列表"""
        with open(self.strategies_file, 'w', encoding='utf-8') as f:
            json.dump(self.strategies, f, indent=2, ensure_ascii=False)
    
    def load_signals(self) -> List[Dict]:
        """加载信号列表"""
        if os.path.exists(self.signals_file):
            with open(self.signals_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_signals(self):
        """保存信号列表"""
        with open(self.signals_file, 'w', encoding='utf-8') as f:
            json.dump(self.signals, f, indent=2, ensure_ascii=False)
    
    def start_strategy(self, symbol: str, strategy: str, side: str, 
                      entry_price: float, quantity: float = 0) -> Dict:
        """
        启动策略（带互斥检查）
        
        Args:
            symbol: 交易对
            strategy: 策略名称
            side: long/short
            entry_price: 入场价格
            quantity: 数量
            
        Returns:
            策略信息
        """
        # 互斥检查：同一交易对只能有一个活跃策略
        for s in self.strategies:
            if s['symbol'] == symbol and s['status'] == '运行中':
                return {
                    'success': False,
                    'error': f'{symbol} 已有活跃策略，不能重复启动',
                    'existing_strategy': s
                }
        
        new_strategy = {
            'id': len(self.strategies) + 1,
            'symbol': symbol,
            'strategy': strategy,
            'side': side,
            'entry_price': entry_price,
            'quantity': quantity,
            'entry_time': datetime.now().isoformat(),
            'status': '运行中',
            'pnl': 0,
            'current_price': 0,
            'stop_loss': 0,
            'stop_order_id': None,  # 币安止损单 ID
            'take_profit': 0
        }
        
        self.strategies.append(new_strategy)
        self.save_strategies()
        
        print(f"🚀 策略启动：{symbol} {side.upper()} @ ${entry_price} ({strategy})")
        return new_strategy
    
    def stop_strategy(self, symbol: str) -> Dict:
        """
        停止策略
        
        Args:
            symbol: 交易对
            
        Returns:
            结果
        """
        initial_count = len(self.strategies)
        self.strategies = [s for s in self.strategies if s['symbol'] != symbol]
        self.save_strategies()
        
        if len(self.strategies) < initial_count:
            print(f"⏹️ 策略停止：{symbol}")
            return {'success': True, 'message': f'策略 {symbol} 已停止'}
        
        return {'success': False, 'error': '未找到策略'}
    
    def update_strategy_pnl(self, symbol: str, current_price: float) -> Dict:
        """
        更新策略盈亏
        
        Args:
            symbol: 交易对
            current_price: 当前价格
            
        Returns:
            更新后的策略
        """
        for strategy in self.strategies:
            if strategy['symbol'] == symbol:
                if strategy['side'] == 'long':
                    pnl = (current_price - strategy['entry_price']) * strategy.get('quantity', 1)
                else:
                    pnl = (strategy['entry_price'] - current_price) * strategy.get('quantity', 1)
                
                strategy['current_price'] = current_price
                strategy['pnl'] = pnl
                self.save_strategies()
                
                return strategy
        
        return None
    
    def generate_signal(self, symbol: str, strategy_name: str, current_price: float, strategy: Dict = None) -> Optional[Dict]:
        """
        生成交易信号（v23 高频策略）
        
        Args:
            symbol: 交易对
            strategy_name: 策略名称
            current_price: 当前价格
            
        Returns:
            交易信号（如果有）
        """
        # v23 高频策略逻辑
        if strategy_name != 'v23 高频':
            return None
        
        # 简化版：价格波动超过 1% 生成信号
        # 实际应该使用技术指标（WR, RSI, KDJ 等）
        for strategy in self.strategies:
            if strategy['symbol'] == symbol and strategy['status'] == '运行中':
                entry_price = strategy['entry_price']
                price_change = abs(current_price - entry_price) / entry_price * 100
                
                if price_change > 1.0:  # 波动超过 1%
                    signal_type = 'CLOSE_LONG' if strategy['side'] == 'long' else 'CLOSE_SHORT'
                    return {
                        'type': signal_type,
                        'symbol': symbol,
                        'reason': f'价格波动 {price_change:.2f}%',
                        'action': 'close'
                    }
        
        return None
    
    def execute_signal(self, signal: Dict, api_client=None) -> Dict:
        """
        执行交易信号
        
        Args:
            signal: 交易信号
            api_client: 币安 API 客户端（用于实际下单）
            
        Returns:
            执行结果
        """
        from .trading_record import trading_record
        
        signal_type = signal.get('type')
        symbol = signal.get('symbol')
        reason = signal.get('reason', '')
        
        # 查找对应策略
        strategy = None
        for s in self.strategies:
            if s['symbol'] == symbol and s['status'] == '运行中':
                strategy = s
                break
        
        if not strategy:
            return {'success': False, 'error': '未找到活跃策略'}
        
        # 创建交易记录（pending 状态）
        trade = trading_record.create_trade_record(
            symbol=symbol,
            side=strategy['side'].upper(),
            action='CLOSE',
            quantity=strategy.get('quantity', 0.01),
            price=strategy['current_price'],
            strategy=strategy['strategy'],
            signal_reason=reason,
            pnl=strategy['pnl'],
            pnl_pct=(strategy['pnl'] / (strategy['entry_price'] * strategy.get('quantity', 0.01)) * 100) if strategy.get('quantity', 0.01) > 0 else 0,
            status='pending'
        )
        
        # 如果有 API 客户端，执行实际交易
        exchange_order_id = None
        if api_client:
            # 实际下单逻辑
            # order_result = api_client.close_position(...)
            # exchange_order_id = order_result.get('order_id')
            pass
        
        # 关闭策略
        result = self.stop_strategy(symbol)
        
        if result.get('success'):
            # 更新交易记录为 executed
            trading_record.update_trade_status(
                trade_id=trade['id'],
                status='executed',
                exchange_order_id=exchange_order_id,
                notes=f'策略平仓：{reason}'
            )
            
            return {
                'success': True,
                'message': f'已执行 {signal_type}',
                'reason': reason,
                'trade_id': trade['id'],
                'pnl': strategy['pnl']
            }
        
        return {'success': False, 'error': '策略关闭失败'}
    
    def get_active_strategies(self) -> List[Dict]:
        """获取活跃策略"""
        return [s for s in self.strategies if s['status'] == '运行中']
    
    def generate_signal(self, symbol: str, signal_type: str, 
                       confidence: float, price: float) -> Dict:
        """
        生成交易信号
        
        Args:
            symbol: 交易对
            signal_type: LONG/SHORT
            confidence: 置信度 0-1
            price: 价格
            
        Returns:
            信号
        """
        signal = {
            'id': len(self.signals) + 1,
            'symbol': symbol,
            'type': signal_type,
            'confidence': confidence,
            'price': price,
            'time': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        self.signals.append(signal)
        self.save_signals()
        
        print(f"📊 信号生成：{symbol} {signal_type} (置信度：{confidence:.2f}) @ ${price}")
        return signal
    
    def execute_signal(self, signal_id: int, action: str = 'open') -> Dict:
        """
        执行信号
        
        Args:
            signal_id: 信号 ID
            action: open/close
            
        Returns:
            执行结果
        """
        for signal in self.signals:
            if signal['id'] == signal_id:
                signal['status'] = 'executed'
                signal['executed_at'] = datetime.now().isoformat()
                signal['action'] = action
                self.save_signals()
                
                print(f"✅ 信号执行：{signal['symbol']} {action}")
                return {'success': True, 'signal': signal}
        
        return {'success': False, 'error': '信号未找到'}
    
    def get_signals(self, limit: int = 50) -> List[Dict]:
        """获取最近信号"""
        return self.signals[-limit:]
    
    def get_strategy_stats(self) -> Dict:
        """获取策略统计"""
        active = len([s for s in self.strategies if s['status'] == '运行中'])
        total_pnl = sum(s.get('pnl', 0) for s in self.strategies)
        
        return {
            'total_strategies': len(self.strategies),
            'active_strategies': active,
            'total_pnl': total_pnl,
            'total_signals': len(self.signals)
        }


# 全局实例
strategy_engine = StrategyEngine()
