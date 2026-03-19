#!/usr/bin/env python3
"""
🦞 资金管理引擎 v3.0

职责:
    - 仓位计算
    - PnL 计算
    - 手续费统计
    - 风险控制

特性:
    - 多种仓位计算模式
    - 实时 PnL 跟踪
    - 手续费累计
    - 风险指标监控

用法:
    from core.capital.capital_manager import CapitalManager
    
    manager = CapitalManager()
    position_size = manager.calculate_position_size(100, 2000, 5)
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
import json
import os

from modules.utils.logger import setup_logger
from modules.utils.decorators import handle_exceptions
from modules.utils.result import Result
from modules.utils.precision import PrecisionUtils

logger = setup_logger("capital_manager", log_file="logs/capital_manager.log")


class CapitalManager:
    """
    资金管理引擎
    
    核心功能:
        - 仓位计算
        - PnL 计算
        - 手续费统计
        - 风险控制
    """
    
    # 仓位计算模式
    POSITION_MODE_FIXED = "fixed"  # 固定比例
    POSITION_MODE_KELLY = "kelly"  # 凯利公式
    POSITION_MODE_MARTINGALE = "martingale"  # 马丁格尔
    
    def __init__(self):
        """初始化资金管理引擎"""
        # 账户信息
        self.total_capital: Decimal = Decimal('0')
        self.available_capital: Decimal = Decimal('0')
        self.used_capital: Decimal = Decimal('0')
        
        # 仓位信息
        self.positions: Dict[str, Dict] = {}
        
        # PnL 统计
        self.realized_pnl: Decimal = Decimal('0')
        self.unrealized_pnl: Decimal = Decimal('0')
        self.total_pnl: Decimal = Decimal('0')
        
        # 手续费统计
        self.total_commission: Decimal = Decimal('0')
        self.commission_by_asset: Dict[str, Decimal] = {}
        
        # 交易统计
        self.trade_count: int = 0
        self.win_count: int = 0
        self.lose_count: int = 0
        
        # 风险指标
        self.max_drawdown: Decimal = Decimal('0')
        self.current_drawdown: Decimal = Decimal('0')
        self.peak_capital: Decimal = Decimal('0')
        
        # 持久化文件
        self.persistence_file = "/root/.openclaw/workspace/quant/v3-architecture/data/capital_manager.json"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
        
        # 加载数据
        self._load_data()
        
        logger.info("资金管理引擎初始化完成")
    
    # ==================== 仓位计算 ====================
    
    def calculate_position_size(
        self,
        amount: Decimal,
        price: Decimal,
        leverage: int = 1,
        mode: str = POSITION_MODE_FIXED,
        win_rate: Optional[float] = None,
        profit_loss_ratio: Optional[float] = None
    ) -> Decimal:
        """
        计算仓位大小
        
        Args:
            amount (Decimal): 可用资金
            price (Decimal): 价格
            leverage (int): 杠杆
            mode (str): 计算模式
            win_rate (float, optional): 胜率（凯利公式用）
            profit_loss_ratio (float, optional): 盈亏比（凯利公式用）
        
        Returns:
            Decimal: 仓位大小（币种数量）
        """
        if mode == self.POSITION_MODE_FIXED:
            return self._calculate_fixed_position(amount, price, leverage)
        elif mode == self.POSITION_MODE_KELLY:
            return self._calculate_kelly_position(amount, price, win_rate, profit_loss_ratio)
        elif mode == self.POSITION_MODE_MARTINGALE:
            return self._calculate_martingale_position(amount, price, leverage)
        else:
            return self._calculate_fixed_position(amount, price, leverage)
    
    def _calculate_fixed_position(
        self,
        amount: Decimal,
        price: Decimal,
        leverage: int = 1
    ) -> Decimal:
        """
        固定比例仓位计算
        
        公式：仓位 = (资金 * 杠杆) / 价格
        
        Args:
            amount (Decimal): 可用资金
            price (Decimal): 价格
            leverage (int): 杠杆
        
        Returns:
            Decimal: 仓位大小
        """
        if price <= 0:
            return Decimal('0')
        
        position_value = amount * leverage
        position_size = position_value / price
        
        return position_size
    
    def _calculate_kelly_position(
        self,
        amount: Decimal,
        price: Decimal,
        win_rate: Optional[float] = None,
        profit_loss_ratio: Optional[float] = None
    ) -> Decimal:
        """
        凯利公式仓位计算
        
        公式：f* = (p * b - q) / b
        其中：
            f* = 仓位比例
            p = 胜率
            q = 败率 (1 - p)
            b = 盈亏比
        
        Args:
            amount (Decimal): 可用资金
            price (Decimal): 价格
            win_rate (float, optional): 胜率
            profit_loss_ratio (float, optional): 盈亏比
        
        Returns:
            Decimal: 仓位大小
        """
        # 默认参数
        if win_rate is None:
            win_rate = 0.5
        if profit_loss_ratio is None:
            profit_loss_ratio = 2.0
        
        # 凯利公式
        p = Decimal(str(win_rate))
        q = Decimal('1') - p
        b = Decimal(str(profit_loss_ratio))
        
        # f* = (p * b - q) / b
        kelly_fraction = (p * b - q) / b
        
        # 限制在 0-100%
        kelly_fraction = max(Decimal('0'), min(kelly_fraction, Decimal('1')))
        
        # 计算仓位
        position_value = amount * kelly_fraction
        position_size = position_value / price if price > 0 else Decimal('0')
        
        return position_size
    
    def _calculate_martingale_position(
        self,
        amount: Decimal,
        price: Decimal,
        leverage: int = 1,
        base_amount: Optional[Decimal] = None
    ) -> Decimal:
        """
        马丁格尔仓位计算（加倍下注）
        
        Args:
            amount (Decimal): 可用资金
            price (Decimal): 价格
            leverage (int): 杠杆
            base_amount (Decimal, optional): 基础金额
        
        Returns:
            Decimal: 仓位大小
        """
        # 基础金额（默认使用可用资金的 10%）
        if base_amount is None:
            base_amount = amount * Decimal('0.1')
        
        # 如果有连续亏损，加倍
        if self.lose_count > 0:
            base_amount = base_amount * (Decimal('2') ** self.lose_count)
        
        # 限制最大仓位（不超过可用资金的 50%）
        max_amount = amount * Decimal('0.5')
        base_amount = min(base_amount, max_amount)
        
        return self._calculate_fixed_position(base_amount, price, leverage)
    
    # ==================== PnL 计算 ====================
    
    def calculate_pnl(
        self,
        entry_price: Decimal,
        current_price: Decimal,
        quantity: Decimal,
        side: str
    ) -> Decimal:
        """
        计算盈亏
        
        Args:
            entry_price (Decimal): 入场价
            current_price (Decimal): 当前价
            quantity (Decimal): 数量
            side (str): 方向（LONG/SHORT）
        
        Returns:
            Decimal: 盈亏
        """
        if side.upper() == 'LONG':
            pnl = (current_price - entry_price) * quantity
        else:  # SHORT
            pnl = (entry_price - current_price) * quantity
        
        return pnl
    
    def calculate_pnl_pct(
        self,
        entry_price: Decimal,
        current_price: Decimal,
        side: str
    ) -> Decimal:
        """
        计算盈亏百分比
        
        Args:
            entry_price (Decimal): 入场价
            current_price (Decimal): 当前价
            side (str): 方向（LONG/SHORT）
        
        Returns:
            Decimal: 盈亏百分比
        """
        if entry_price <= 0:
            return Decimal('0')
        
        if side.upper() == 'LONG':
            pnl_pct = (current_price - entry_price) / entry_price
        else:  # SHORT
            pnl_pct = (entry_price - current_price) / entry_price
        
        return pnl_pct
    
    def update_unrealized_pnl(self):
        """更新未实现盈亏"""
        total_unrealized = Decimal('0')
        
        for symbol, position in self.positions.items():
            if position.get('size', Decimal('0')) != 0:
                entry_price = Decimal(position.get('entry_price', '0'))
                current_price = Decimal(position.get('current_price', '0'))
                size = Decimal(position.get('size', '0'))
                side = position.get('side', 'LONG')
                
                pnl = self.calculate_pnl(entry_price, current_price, size, side)
                total_unrealized += pnl
        
        self.unrealized_pnl = total_unrealized
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
        
        # 更新最大回撤
        self._update_drawdown()
    
    def _update_drawdown(self):
        """更新回撤"""
        # 更新峰值资金
        total_value = self.total_capital + self.total_pnl
        if total_value > self.peak_capital:
            self.peak_capital = total_value
        
        # 计算当前回撤
        if self.peak_capital > 0:
            self.current_drawdown = (self.peak_capital - total_value) / self.peak_capital
            
            # 更新最大回撤
            if self.current_drawdown > self.max_drawdown:
                self.max_drawdown = self.current_drawdown
    
    # ==================== 手续费统计 ====================
    
    def add_commission(self, commission: Decimal, asset: str = 'USDT'):
        """
        添加手续费记录
        
        Args:
            commission (Decimal): 手续费金额
            asset (str): 手续费币种
        """
        self.total_commission += commission
        
        if asset not in self.commission_by_asset:
            self.commission_by_asset[asset] = Decimal('0')
        
        self.commission_by_asset[asset] += commission
        
        logger.debug(f"📝 手续费：{commission} {asset}")
    
    # ==================== 交易统计 ====================
    
    def add_trade(self, pnl: Decimal, is_win: bool):
        """
        添加交易记录
        
        Args:
            pnl (Decimal): 盈亏
            is_win (bool): 是否盈利
        """
        self.trade_count += 1
        self.realized_pnl += pnl
        
        if is_win:
            self.win_count += 1
        else:
            self.lose_count += 1
        
        # 重置连亏计数
        if is_win:
            self.lose_count = 0
        
        logger.info(f"💰 交易记录：PnL={pnl}, 胜={self.win_count}, 负={self.lose_count}")
    
    # ==================== 风险控制 ====================
    
    def check_risk_limits(
        self,
        position_size: Decimal,
        price: Decimal,
        symbol: str
    ) -> Result:
        """
        检查风险限制
        
        Args:
            position_size (Decimal): 仓位大小
            price (Decimal): 价格
            symbol (str): 交易对
        
        Returns:
            Result: 检查结果
        """
        # 1. 检查可用资金
        position_value = position_size * price
        if position_value > self.available_capital:
            return Result.fail(
                error_code="INSUFFICIENT_CAPITAL",
                message=f"可用资金不足：需要{position_value}, 可用{self.available_capital}"
            )
        
        # 2. 检查单一仓位限制（不超过总资金的 20%）
        if position_value > self.total_capital * Decimal('0.2'):
            return Result.fail(
                error_code="POSITION_LIMIT_EXCEEDED",
                message=f"单一仓位超限：不超过总资金的 20%"
            )
        
        # 3. 检查最大回撤（不超过 10%）
        if self.current_drawdown > Decimal('0.1'):
            return Result.fail(
                error_code="DRAWDOWN_LIMIT_EXCEEDED",
                message=f"最大回撤超限：当前{self.current_drawdown:.2%}"
            )
        
        return Result.ok(message="风险检查通过")
    
    # ==================== 持久化 ====================
    
    def _load_data(self):
        """从持久化文件加载数据"""
        if not os.path.exists(self.persistence_file):
            logger.debug("持久化文件不存在，使用默认数据")
            return
        
        try:
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.total_capital = Decimal(data.get('total_capital', '0'))
            self.available_capital = Decimal(data.get('available_capital', '0'))
            self.realized_pnl = Decimal(data.get('realized_pnl', '0'))
            self.trade_count = data.get('trade_count', 0)
            self.win_count = data.get('win_count', 0)
            self.lose_count = data.get('lose_count', 0)
            
            logger.info(f"📊 加载数据成功（总资金：{self.total_capital}）")
            
        except Exception as e:
            logger.error(f"⚠️ 加载数据失败：{e}")
    
    def _save_data(self):
        """保存数据到持久化文件"""
        try:
            data = {
                'total_capital': str(self.total_capital),
                'available_capital': str(self.available_capital),
                'realized_pnl': str(self.realized_pnl),
                'trade_count': self.trade_count,
                'win_count': self.win_count,
                'lose_count': self.lose_count,
                'update_time': datetime.now().isoformat()
            }
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("📝 已保存数据")
            
        except Exception as e:
            logger.error(f"❌ 保存数据失败：{e}")
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        win_rate = self.win_count / self.trade_count * 100 if self.trade_count > 0 else 0
        
        return {
            'total_capital': str(self.total_capital),
            'available_capital': str(self.available_capital),
            'used_capital': str(self.used_capital),
            'realized_pnl': str(self.realized_pnl),
            'unrealized_pnl': str(self.unrealized_pnl),
            'total_pnl': str(self.total_pnl),
            'total_commission': str(self.total_commission),
            'trade_count': self.trade_count,
            'win_count': self.win_count,
            'lose_count': self.lose_count,
            'win_rate': f"{win_rate:.2f}%",
            'max_drawdown': f"{self.max_drawdown:.2f}%",
            'current_drawdown': f"{self.current_drawdown:.2f}%"
        }


# 全局实例
_capital_manager: Optional[CapitalManager] = None


def get_capital_manager() -> CapitalManager:
    """获取全局资金管理引擎实例"""
    global _capital_manager
    if _capital_manager is None:
        _capital_manager = CapitalManager()
    return _capital_manager


def reset_capital_manager():
    """重置资金管理引擎（测试用）"""
    global _capital_manager
    _capital_manager = None
