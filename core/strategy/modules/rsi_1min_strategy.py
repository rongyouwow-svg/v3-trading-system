#!/usr/bin/env python3
"""
📈 1 分钟 RSI 策略模块 v3.1

策略逻辑:
    - RSI > 50: 开多（2 根 K 线确认）
    - RSI > 80: 平仓
    - 止损：0.2% 策略止损 + 5% 硬止损兜底

参数:
    - symbol: 交易对（ETHUSDT / LINKUSDT）
    - leverage: 杠杆（默认 3x）
    - amount: 保证金（默认 100 USDT）
    - stop_loss_pct: 0.002（0.2% 策略止损）

用法:
    from core.strategy.modules.rsi_1min_strategy import RSIStrategy
    
    strategy = RSIStrategy(
        symbol='ETHUSDT',
        leverage=3,
        amount=100,
        stop_loss_pct=0.002  # 0.2% 策略止损
    )
"""

import logging
from typing import Dict, Any, Optional
from core.strategy.modules.rsi_strategy import RSIStrategy

logger = logging.getLogger(__name__)


class Strategy(RSIStrategy):
    """
    1 分钟 RSI 策略（ETH/LINK）
    
    继承自 RSIStrategy 基类
    """
    
    def __init__(self, symbol: str, leverage: int = 3, amount: float = 100, 
                 stop_loss_pct: Optional[float] = 0.002):
        """
        初始化策略
        
        Args:
            symbol: 交易对（'ETHUSDT' / 'LINKUSDT'）
            leverage: 杠杆（默认 3）
            amount: 保证金（默认 100 USDT）
            stop_loss_pct: 止损比例（默认 0.002=0.2%，None 则使用 5% 兜底）
        """
        super().__init__(
            symbol=symbol,
            leverage=leverage,
            amount=amount,
            stop_loss_pct=stop_loss_pct
        )
        
        logger.info(f"✅ 1 分钟 RSI 策略初始化完成：{symbol}")
        logger.info(f"  - 止损：{stop_loss_pct*100}% (策略止损)")
