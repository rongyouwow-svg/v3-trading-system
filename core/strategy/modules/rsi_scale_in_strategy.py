#!/usr/bin/env python3
"""
📈 RSI 分批建仓策略模块 v3.1 (AVAX)

策略逻辑:
    - RSI > 50: 分批开多（30%/50%/20%）
    - RSI > 80: 全部平仓
    - 止损：0.5% 策略止损 + 5% 硬止损兜底

分批计划:
    - 第 1 批：30% (60 USDT) - RSI>50 第 1 次确认
    - 第 2 批：50% (100 USDT) - RSI>50 第 2 次确认
    - 第 3 批：20% (40 USDT) - RSI>50 第 3 次确认
    - 累计：200 USDT

参数:
    - symbol: AVAXUSDT
    - leverage: 3x
    - total_amount: 200 USDT
    - stop_loss_pct: 0.005 (0.5% 策略止损)

用法:
    from core.strategy.modules.rsi_scale_in_strategy import RSIScaleInStrategy
    
    strategy = RSIScaleInStrategy(
        symbol='AVAXUSDT',
        leverage=3,
        total_amount=200,
        stop_loss_pct=0.005  # 0.5% 策略止损
    )
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal

# 延迟导入父类，避免循环依赖
def get_rsi_strategy_class():
    from core.strategy.modules.rsi_strategy import RSIStrategy
    return RSIStrategy

# 使用父类的 logger
logger = logging.getLogger(__name__.replace('.modules.', '.'))


# 延迟获取父类
RSIStrategy = get_rsi_strategy_class()

class Strategy(RSIStrategy):
    """
    RSI 分批建仓策略（AVAX）
    
    继承自 RSIStrategy 基类，增加分批建仓逻辑
    """
    
    def __init__(self, symbol: str = 'AVAXUSDT', leverage: int = 3, 
                 total_amount: float = 200, stop_loss_pct: Optional[float] = 0.005):
        """
        初始化策略
        
        Args:
            symbol: 交易对（默认 'AVAXUSDT'）
            leverage: 杠杆（默认 3）
            total_amount: 总保证金（默认 200 USDT）
            stop_loss_pct: 止损比例（默认 0.005=0.5%，None 则使用 5% 兜底）
        """
        super().__init__(
            symbol=symbol,
            leverage=leverage,
            amount=total_amount,
            stop_loss_pct=stop_loss_pct
        )
        
        # 分批建仓配置
        self.scale_in_ratios: List[float] = [0.30, 0.50, 0.20]  # 30%/50%/20%
        self.current_scale_index: int = 0  # 当前建仓批次
        self.scale_in_amounts: List[float] = [
            total_amount * ratio for ratio in self.scale_in_ratios
        ]  # [60, 100, 40]
        
        # 分批状态
        self.scale_in_count: int = 0  # 已完成批次数
        self.total_invested: float = 0.0  # 累计投入
        
        logger.info(f"✅ RSI 分批建仓策略初始化完成：{symbol}")
        logger.info(f"  - 总保证金：{total_amount} USDT")
        logger.info(f"  - 分批计划：30% ({self.scale_in_amounts[0]:.0f}U) → 50% ({self.scale_in_amounts[1]:.0f}U) → 20% ({self.scale_in_amounts[2]:.0f}U)")
        logger.info(f"  - 止损：{stop_loss_pct*100 if stop_loss_pct else 5}% ({'策略止损' if stop_loss_pct else '5% 兜底'})")
    
    def check_signal(self, rsi: float) -> Optional[Dict[str, Any]]:
        """
        检查交易信号（分批建仓特殊逻辑）
        
        逻辑:
            - 第 1 批：2 根 K 线确认（避免误触发）
            - 第 2 批及以后：单 K 线确认（快速建仓）
        
        Args:
            rsi: 当前 RSI 值
        
        Returns:
            交易信号（如有）
        """
        # 第 1 批需要 2 根 K 线确认
        if self.current_scale_index == 0:
            return super().check_signal(rsi)
        
        # 第 2 批及以后，单 K 线确认（快速建仓）
        if rsi > self.rsi_buy_threshold and self.current_scale_index < len(self.scale_in_ratios):
            logger.info(f"📡 {self.symbol} 第{self.current_scale_index + 1}批：单 K 线确认开仓 (RSI={rsi:.2f})")
            return self.generate_open_signal()
        
        # 平仓逻辑
        if self.position == 'LONG' and rsi > self.rsi_sell_threshold:
            return self.generate_close_signal()
        
        return None
    
    def generate_open_signal(self) -> Dict[str, Any]:
        """
        生成开仓信号（分批建仓）
        
        Returns:
            开仓信号
        """
        # 检查是否已完成所有批次
        if self.current_scale_index >= len(self.scale_in_ratios):
            logger.warning(f"⚠️ {self.symbol} 已完成所有分批建仓，跳过开仓")
            return None
        
        # 计算本批次开仓数量
        quantity = self.calculate_scale_in_quantity()
        
        # 更新统计
        self.signals_sent += 1
        
        signal = {
            'action': 'open',
            'symbol': self.symbol,
            'quantity': quantity,
            'leverage': self.leverage,
            'amount': self.scale_in_amounts[self.current_scale_index],
            'stop_loss_pct': self.stop_loss_pct,
            'rsi': self.last_rsi,
            'reason': f'RSI>{self.rsi_buy_threshold} 确认 (第{self.current_scale_index + 1}/{len(self.scale_in_ratios)}批)',
            'scale_in': {
                'batch': self.current_scale_index + 1,
                'total_batches': len(self.scale_in_ratios),
                'ratio': self.scale_in_ratios[self.current_scale_index],
                'amount': self.scale_in_amounts[self.current_scale_index]
            }
        }
        
        logger.info(f"📡 {self.symbol} 生成开仓信号：第{self.current_scale_index + 1}批 {quantity} @ ~市价")
        
        return signal
    
    def calculate_scale_in_quantity(self) -> float:
        """
        计算本批次开仓数量
        
        Returns:
            开仓数量
        """
        batch_amount = self.scale_in_amounts[self.current_scale_index]
        # 简单估算：(本批次保证金 × 杠杆) / 2000
        return (batch_amount * self.leverage) / 2000
    
    def on_order_filled(self, order: Dict[str, Any]):
        """
        订单成交回调（分批建仓）
        
        Args:
            order: 订单信息
        """
        if order['side'] == 'BUY':
            # 更新分批状态
            batch_amount = self.scale_in_amounts[self.current_scale_index]
            self.total_invested += batch_amount
            self.current_scale_index += 1
            self.scale_in_count += 1
            
            self.position = 'LONG'
            self.entry_price = Decimal(str(order['price']))
            self.signals_executed += 1
            
            logger.info(f"✅ {self.symbol} 第{self.current_scale_index}批开仓成功：{order['quantity']} @ {order['price']}")
            logger.info(f"  - 本批次：{batch_amount} USDT")
            logger.info(f"  - 累计投入：{self.total_invested} USDT / {self.amount} USDT")
            
            if self.current_scale_index >= len(self.scale_in_ratios):
                logger.info(f"✅ {self.symbol} 已完成所有分批建仓")
        
        elif order['side'] == 'SELL':
            # 平仓
            pnl = (Decimal(str(order['price'])) - self.entry_price) * Decimal(str(order['quantity']))
            
            logger.info(f"✅ {self.symbol} 平仓成功：{order['quantity']} @ {order['price']} (盈亏：{pnl:.2f} USDT)")
            
            # 重置分批状态
            self.position = None
            self.entry_price = Decimal('0')
            self.current_scale_index = 0
            self.scale_in_count = 0
            self.total_invested = 0.0
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取策略状态（包含分批信息）
        
        Returns:
            策略状态信息
        """
        status = super().get_status()
        
        # 添加分批信息
        status.update({
            'scale_in': {
                'current_batch': self.current_scale_index + 1,
                'total_batches': len(self.scale_in_ratios),
                'completed_batches': self.scale_in_count,
                'total_invested': self.total_invested,
                'total_amount': self.amount
            }
        })
        
        return status
    
    def save_state(self):
        """保存分批建仓策略状态（扩展基类）"""
        # 先调用基类保存
        super().save_state()
        
        # 添加分批建仓特有状态
        state_file = f'logs/strategy_{self.symbol.replace("USDT", "")}_state.json'
        try:
            with open(state_file, 'r+', encoding='utf-8') as f:
                state = json.load(f)
                state['scale_in'] = {
                    'current_scale_index': self.current_scale_index,
                    'scale_in_count': self.scale_in_count,
                    'total_invested': self.total_invested,
                    'scale_in_ratios': self.scale_in_ratios,
                    'scale_in_amounts': self.scale_in_amounts
                }
                f.seek(0)
                json.dump(state, f, indent=2, ensure_ascii=False)
            logger.debug(f"💾 分批建仓状态已保存：{self.symbol}")
        except Exception as e:
            logger.error(f"❌ 保存分批建仓状态失败：{e}")
    
    def load_state(self):
        """从文件恢复分批建仓策略状态（扩展基类）"""
        # 先调用基类恢复
        success = super().load_state()
        
        if success:
            # 恢复分批建仓特有状态
            state_file = f'logs/strategy_{self.symbol.replace("USDT", "")}_state.json'
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                if 'scale_in' in state:
                    scale_in = state['scale_in']
                    self.current_scale_index = scale_in.get('current_scale_index', 0)
                    self.scale_in_count = scale_in.get('scale_in_count', 0)
                    self.total_invested = scale_in.get('total_invested', 0.0)
                    
                    logger.info(f"  - 分批进度：第{self.current_scale_index + 1}/{len(self.scale_in_ratios)}批")
                    logger.info(f"  - 已投入：{self.total_invested} USDT")
            except Exception as e:
                logger.error(f"❌ 恢复分批建仓状态失败：{e}")
        
        return success
    
    def generate_close_signal(self) -> Dict[str, Any]:
        """
        生成平仓信号（全部平仓）
        
        Returns:
            平仓信号
        """
        # 更新统计
        self.signals_executed += 1
        
        signal = {
            'action': 'close',
            'symbol': self.symbol,
            'reason': f'RSI>{self.rsi_sell_threshold}',
            'rsi': self.last_rsi,
            'close_all': True,  # 标记为全部平仓
            'scale_in': {
                'total_invested': self.total_invested,
                'batches': self.scale_in_count
            }
        }
        
        logger.info(f"📡 {self.symbol} 生成平仓信号：全部平仓")
        
        return signal
