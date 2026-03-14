#!/usr/bin/env python3
"""
🛡️ 风控引擎

职责:
    - 仓位监控
    - 资金监控
    - 异常检测
    - 告警管理
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskEngine:
    """风控引擎"""
    
    def __init__(self):
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.alerts: List[Dict[str, Any]] = []
        
        # 风控配置
        self.config = {
            'max_position_size': 1000,  # 最大仓位
            'max_drawdown': 0.1,  # 最大回撤 10%
            'max_daily_loss': 500  # 最大日亏损
        }
    
    def update_position(self, symbol: str, position_data: Dict[str, Any]):
        """更新持仓"""
        self.positions[symbol] = {
            **position_data,
            'updated_at': datetime.now().isoformat()
        }
        logger.debug(f"📊 持仓已更新：{symbol}")
    
    def check_position_limit(self, symbol: str, size: float) -> Dict[str, Any]:
        """
        检查仓位限制
        
        Args:
            symbol: 交易对
            size: 仓位大小
        
        Returns:
            检查结果
        """
        if size > self.config['max_position_size']:
            return {
                'success': False,
                'error': f'仓位超限：{size} > {self.config["max_position_size"]}'
            }
        
        return {'success': True}
    
    def check_drawdown(self, current_pnl: float, peak_pnl: float) -> Dict[str, Any]:
        """
        检查回撤
        
        Args:
            current_pnl: 当前盈亏
            peak_pnl: 峰值盈亏
        
        Returns:
            检查结果
        """
        if peak_pnl <= 0:
            return {'success': True}
        
        drawdown = (peak_pnl - current_pnl) / peak_pnl
        
        if drawdown > self.config['max_drawdown']:
            return {
                'success': False,
                'error': f'回撤超限：{drawdown:.2%} > {self.config["max_drawdown"]:.0%}'
            }
        
        return {'success': True}
    
    def create_alert(self, alert_type: str, message: str, level: str = 'warning'):
        """
        创建告警
        
        Args:
            alert_type: 告警类型
            message: 告警消息
            level: 告警级别 (info/warning/error)
        """
        alert = {
            'type': alert_type,
            'message': message,
            'level': level,
            'created_at': datetime.now().isoformat()
        }
        
        self.alerts.append(alert)
        logger.warning(f"⚠️ 告警：{message}")
    
    def get_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取告警列表"""
        return self.alerts[-limit:]
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取持仓"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """获取所有持仓"""
        return list(self.positions.values())
