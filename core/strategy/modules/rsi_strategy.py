#!/usr/bin/env python3
"""
📈 RSI 策略模块基类 v3.1

策略逻辑:
    - RSI > 50: 开多
    - RSI > 80: 平仓
    - 2 根 K 线确认机制

参数:
    - symbol: 交易对
    - leverage: 杠杆（默认 3x）
    - amount: 保证金（默认 100 USDT）
    - stop_loss_pct: 止损比例（None 表示使用 5% 兜底）

用法:
    from core.strategy.modules.rsi_strategy import RSIStrategy
    
    strategy = RSIStrategy(
        symbol='ETHUSDT',
        leverage=3,
        amount=100,
        stop_loss_pct=0.002  # 0.2% 止损，None 则使用 5% 兜底
    )
    
    signal = strategy.on_tick(market_data)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class RSIStrategy:
    """
    RSI 策略模块基类
    
    核心功能:
        - RSI 计算
        - 信号生成（开仓/平仓）
        - 2 根 K 线确认机制
    """
    
    def __init__(self, symbol: str, leverage: int = 3, amount: float = 100, 
                 stop_loss_pct: Optional[float] = None):
        """
        初始化 RSI 策略
        
        Args:
            symbol: 交易对（如 'ETHUSDT'）
            leverage: 杠杆（默认 3）
            amount: 保证金（默认 100 USDT）
            stop_loss_pct: 止损比例（如 0.002=0.2%, None 表示使用 5% 兜底）
        """
        self.symbol = symbol
        self.leverage = leverage
        self.amount = amount
        self.stop_loss_pct = stop_loss_pct  # None 表示使用 5% 兜底
        
        # RSI 参数
        self.rsi_period = 14
        self.rsi_buy_threshold = 50
        self.rsi_sell_threshold = 80
        
        # 状态
        self.position: Optional[str] = None  # 'LONG' / 'SHORT' / None
        self.entry_price: Decimal = Decimal('0')
        self.last_rsi: float = 0.0
        self.signal_rsi: Optional[float] = None
        self.waiting_confirmation: bool = False
        self.stable_count: int = 0
        
        # 信号统计
        self.signals_sent: int = 0
        self.signals_executed: int = 0
        
        # 策略状态
        self.is_running: bool = False
        self.start_time: Optional[datetime] = None
        
        logger.info(f"✅ RSI 策略初始化完成")
        logger.info(f"  - 交易对：{symbol}")
        logger.info(f"  - 杠杆：{leverage}x")
        logger.info(f"  - 保证金：{amount} USDT")
        logger.info(f"  - 止损：{stop_loss_pct*100 if stop_loss_pct else 5}% ({'策略止损' if stop_loss_pct else '5% 兜底'})")
        logger.info(f"  - RSI 买入阈值：>{self.rsi_buy_threshold}")
        logger.info(f"  - RSI 平仓阈值：>{self.rsi_sell_threshold}")
    
    def start(self):
        """启动策略"""
        self.is_running = True
        self.start_time = datetime.now()
        logger.info(f"🚀 RSI 策略已启动：{self.symbol}")
    
    def stop(self):
        """停止策略"""
        self.is_running = False
        logger.info(f"🛑 RSI 策略已停止：{self.symbol}")
    
    def on_tick(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        每根 K 线调用
        
        Args:
            market_data: 市场数据
                {
                    'klines': [...],  # K 线数据
                    'current_price': 2076.1,
                    'timestamp': '2026-03-14T16:45:00Z'
                }
        
        Returns:
            交易信号（如有）
                {
                    'action': 'open' / 'close',
                    'symbol': 'ETHUSDT',
                    'quantity': 0.15,
                    'stop_loss_pct': 0.002,
                    ...
                }
        """
        if not self.is_running:
            return None
        
        # 获取 K 线数据
        klines = market_data.get('klines', [])
        
        if not klines or len(klines) < self.rsi_period + 1:
            logger.debug(f"⚠️ K 线数据不足，跳过：{self.symbol}")
            return None
        
        # 计算 RSI
        rsi = self.calculate_rsi(klines)
        self.last_rsi = rsi
        
        # 检查信号（2 根 K 线确认）
        signal = self.check_signal(rsi)
        
        if signal:
            logger.info(f"📡 {self.symbol} RSI={rsi:.2f} 发出信号：{signal.get('action')}")
        
        return signal
    
    def calculate_rsi(self, klines: List[Dict[str, Any]]) -> float:
        """
        计算 RSI 指标
        
        Args:
            klines: K 线数据（按时间正序）
        
        Returns:
            RSI 值
        """
        if len(klines) < self.rsi_period + 1:
            return 50.0
        
        # 提取收盘价
        closes = [float(k['close']) for k in klines[-(self.rsi_period + 1):]]
        
        # 计算涨跌幅
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        
        # 计算平均涨跌
        avg_gain = sum(gains) / self.rsi_period
        avg_loss = sum(losses) / self.rsi_period
        
        # 计算 RSI
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def check_signal(self, rsi: float) -> Optional[Dict[str, Any]]:
        """
        检查交易信号（2 根 K 线确认）
        
        Args:
            rsi: 当前 RSI 值
        
        Returns:
            交易信号（如有）
        """
        # 如果已经在等待确认
        if self.waiting_confirmation:
            # 第二根 K 线，检查是否仍然满足条件
            if rsi > self.rsi_buy_threshold:
                # 确认！执行开仓
                self.waiting_confirmation = False
                self.signal_rsi = None
                
                # 生成开仓信号
                return self.generate_open_signal()
            else:
                # 不满足，重置
                self.waiting_confirmation = False
                self.signal_rsi = None
                return None
        
        # 第一根 K 线，检查是否触发信号
        if rsi > self.rsi_buy_threshold and not self.position:
            # 记录信号，等待下一根 K 线确认
            self.signal_rsi = rsi
            self.waiting_confirmation = True
            logger.debug(f"⏳ {self.symbol} RSI={rsi:.2f} 等待确认...")
            return None
        
        # 平仓逻辑（有持仓且 RSI>80）
        if self.position == 'LONG' and rsi > self.rsi_sell_threshold:
            return self.generate_close_signal()
        
        return None
    
    def generate_open_signal(self) -> Dict[str, Any]:
        """
        生成开仓信号
        
        Returns:
            开仓信号
        """
        # 计算开仓数量
        quantity = self.calculate_quantity()
        
        # 更新统计
        self.signals_sent += 1
        
        return {
            'action': 'open',
            'symbol': self.symbol,
            'quantity': quantity,
            'leverage': self.leverage,
            'amount': self.amount,
            'stop_loss_pct': self.stop_loss_pct,  # None 表示使用 5% 兜底
            'rsi': self.last_rsi,
            'reason': f'RSI>{self.rsi_buy_threshold} 确认'
        }
    
    def generate_close_signal(self) -> Dict[str, Any]:
        """
        生成平仓信号
        
        Returns:
            平仓信号
        """
        # 更新统计
        self.signals_executed += 1
        
        return {
            'action': 'close',
            'symbol': self.symbol,
            'reason': f'RSI>{self.rsi_sell_threshold}',
            'rsi': self.last_rsi
        }
    
    def calculate_quantity(self) -> float:
        """
        计算开仓数量
        
        Returns:
            开仓数量
        """
        # 简单估算：(保证金 × 杠杆) / 2000
        # 实际执行时会从交易所获取精确数量
        return (self.amount * self.leverage) / 2000
    
    def on_order_filled(self, order: Dict[str, Any]):
        """
        订单成交回调
        
        Args:
            order: 订单信息
                {
                    'symbol': 'ETHUSDT',
                    'side': 'BUY',
                    'quantity': 0.15,
                    'price': 2076.1,
                    ...
                }
        """
        if order['side'] == 'BUY':
            self.position = 'LONG'
            self.entry_price = Decimal(str(order['price']))
            self.signals_executed += 1
            
            logger.info(f"✅ {self.symbol} 开仓成功：{order['quantity']} @ {order['price']}")
        
        elif order['side'] == 'SELL':
            pnl = (Decimal(str(order['price'])) - self.entry_price) * Decimal(str(order['quantity']))
            
            logger.info(f"✅ {self.symbol} 平仓成功：{order['quantity']} @ {order['price']} (盈亏：{pnl:.2f} USDT)")
            
            # 重置状态
            self.position = None
            self.entry_price = Decimal('0')
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取策略状态
        
        Returns:
            策略状态信息
        """
        return {
            'name': f'{self.symbol}_RSI',
            'symbol': self.symbol,
            'status': 'running' if self.is_running else 'stopped',
            'position': self.position,
            'entry_price': float(self.entry_price) if self.entry_price > 0 else 0,
            'last_rsi': self.last_rsi,
            'signals_sent': self.signals_sent,
            'signals_executed': self.signals_executed,
            'stop_loss_pct': self.stop_loss_pct,
            'start_time': self.start_time.isoformat() if self.start_time else None
        }
    
    def save_state(self):
        """保存策略状态到文件"""
        state = {
            'symbol': self.symbol,
            'last_rsi': self.last_rsi,
            'signal_rsi': self.signal_rsi,
            'waiting_confirmation': self.waiting_confirmation,
            'stable_count': self.stable_count,
            'position': self.position,
            'entry_price': float(self.entry_price) if self.entry_price > 0 else 0,
            'signals_sent': self.signals_sent,
            'signals_executed': self.signals_executed,
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'last_update': datetime.now().isoformat()
        }
        
        state_file = f'logs/strategy_{self.symbol.replace("USDT", "")}_state.json'
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            logger.debug(f"💾 策略状态已保存：{self.symbol}")
        except Exception as e:
            logger.error(f"❌ 保存策略状态失败：{e}")
    
    def load_state(self):
        """从文件恢复策略状态"""
        state_file = f'logs/strategy_{self.symbol.replace("USDT", "")}_state.json'
        
        if not os.path.exists(state_file):
            logger.info(f"ℹ️ 无历史状态，从头开始：{self.symbol}")
            return False
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # 恢复状态
            self.last_rsi = state.get('last_rsi', 0)
            self.signal_rsi = state.get('signal_rsi')
            self.waiting_confirmation = state.get('waiting_confirmation', False)
            self.stable_count = state.get('stable_count', 0)
            self.position = state.get('position')
            self.entry_price = Decimal(str(state.get('entry_price', 0)))
            self.signals_sent = state.get('signals_sent', 0)
            self.signals_executed = state.get('signals_executed', 0)
            self.is_running = state.get('is_running', False)
            
            logger.info(f"✅ 策略状态已恢复：{self.symbol}")
            logger.info(f"  - RSI: {self.last_rsi:.2f}")
            logger.info(f"  - 等待确认：{self.waiting_confirmation}")
            logger.info(f"  - 持仓：{self.position}")
            
            return True
        except Exception as e:
            logger.error(f"❌ 恢复策略状态失败：{e}")
            return False
    
    def run(self, interval: int = 60):
        """
        运行策略（循环调用）
        
        Args:
            interval: K 线间隔（秒），默认 60 秒（1 分钟）
        """
        logger.info(f"🚀 RSI 策略启动：{self.symbol}")
        logger.info(f"  - K 线间隔：{interval}秒")
        logger.info(f"  - RSI 周期：{self.rsi_period}")
        logger.info(f"  - 买入阈值：>{self.rsi_buy_threshold}")
        logger.info(f"  - 平仓阈值：>{self.rsi_sell_threshold}")
        
        self.is_running = True
        self.start_time = datetime.now()
        
        while self.is_running:
            try:
                # 获取 K 线数据
                klines = self.get_klines()
                
                if not klines or len(klines) < self.rsi_period + 1:
                    logger.debug(f"⚠️ K 线数据不足，跳过：{self.symbol}")
                    time.sleep(interval)
                    continue
                
                # 构建市场数据
                market_data = {
                    'klines': klines,
                    'current_price': float(klines[-1]['close']),
                    'timestamp': datetime.now().isoformat()
                }
                
                # 调用 on_tick（计算 RSI + 检查信号）
                signal = self.on_tick(market_data)
                
                # 如果有信号，记录日志
                if signal:
                    logger.info(f"📡 {self.symbol} 信号：{signal.get('action')} @ {market_data['current_price']}")
                
                # 等待下一根 K 线
                logger.debug(f"⏳ 等待下一根 K 线：{self.symbol}")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info(f"🛑 策略停止：{self.symbol}")
                self.is_running = False
                self.save_state()
                break
            except Exception as e:
                logger.error(f"❌ 策略异常：{self.symbol} - {e}")
                time.sleep(10)
        
        logger.info(f"✅ RSI 策略已停止：{self.symbol}")
    
    def shutdown(self):
        """关闭策略"""
        # 关闭前保存状态
        self.save_state()
        
        self.stop()
        logger.info(f"✅ RSI 策略已关闭：{self.symbol}")
