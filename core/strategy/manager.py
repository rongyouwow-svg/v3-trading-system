#!/usr/bin/env python3
"""
🦞 策略管理器 v3.0

职责：
    - 策略加载（热插拔）
    - 策略启动/停止
    - 策略状态管理
    - 策略持久化

特性：
    - 支持多策略同时运行
    - 策略独立线程，持续信号计算
    - stop_flag 安全停止机制
    - 策略状态持久化（JSON + 数据库）

用法:
    from core.strategy.manager import StrategyManager
    
    manager = StrategyManager()
    result = manager.start_strategy('ETHUSDT', 'breakout', leverage=5, amount=100)
"""

import json
import os
import threading
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from modules.interfaces.strategy import IStrategyEngine
from modules.models.strategy import Strategy
from modules.utils.result import Result, ok, fail
from modules.utils.exceptions import (
    StrategyNotFoundException,
    StrategyExistsException,
    TradingException
)
from modules.utils.logger import setup_logger
from modules.utils.decorators import handle_exceptions, log_execution
from modules.health.heartbeat import get_heartbeat_monitor, HealthStatus
from connectors.binance.usdt_futures import BinanceUSDTFuturesConnector
from core.capital.capital_manager import CapitalManager
from core.exception.exception_handler import ExceptionManager
from core.sync.state_sync import StateSync

logger = setup_logger("strategy_manager", log_file="logs/strategy_manager.log")

# 获取心跳检测器
heartbeat_monitor = get_heartbeat_monitor()

# 获取连接器（用于止损单查重）
connector: Optional[BinanceUSDTFuturesConnector] = None

# Phase 2 模块实例
capital_manager: Optional[CapitalManager] = None
exception_manager: Optional[ExceptionManager] = None
state_sync: Optional[StateSync] = None


class StrategyManager(IStrategyEngine):
    """
    策略管理器（支持热插拔）
    
    核心功能:
        - 策略加载（动态导入）
        - 策略启动（独立线程）
        - 策略停止（安全停止）
        - 状态持久化（JSON + 数据库）
    """
    
    # 持久化文件路径
    PERSISTENCE_FILE = "/home/admin/.openclaw/workspace/quant/v3-architecture/data/plugin_strategies.json"
    
    def __init__(self, connector=None, execution_engine=None):
        """
        初始化策略管理器
        
        Args:
            connector: 交易所连接器
            execution_engine: 执行引擎
        """
        self.connector = connector
        self.execution_engine = execution_engine
        
        # 策略实例存储 {symbol: strategy_instance}
        self.strategies: Dict[str, Strategy] = {}
        
        # 线程管理 {symbol: thread}
        self.threads: Dict[str, threading.Thread] = {}
        
        # 停止标志 {symbol: bool}
        self.stop_flags: Dict[str, bool] = {}
        
        # 止损单 ID 存储 {symbol: algo_id}
        self.stop_loss_ids: Dict[str, str] = {}
        
        # Phase 2 模块初始化
        self.capital_manager = CapitalManager() if connector else None
        self.exception_manager = ExceptionManager() if connector else None
        self.state_sync = StateSync(connector) if connector else None
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.PERSISTENCE_FILE), exist_ok=True)
        
        # 加载已有策略（热插拔）
        self._load_strategies()
        
        # 启动状态同步（如果有连接器）
        if self.state_sync:
            self.state_sync.start()
            logger.info("✅ 状态同步已启动")
        
        logger.info("策略管理器初始化完成")
    
    def _load_strategies(self):
        """
        从持久化文件加载策略（热插拔恢复）
        
        说明:
            - 读取 plugin_strategies.json
            - 恢复运行中的策略状态
            - 不自动重启策略线程（需要手动启动）
        """
        if not os.path.exists(self.PERSISTENCE_FILE):
            logger.debug("持久化文件不存在，跳过加载")
            return
        
        try:
            with open(self.PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for symbol, strategy_data in data.items():
                if strategy_data.get("status") == "running":
                    logger.info(f"🔌 [热插拔] 发现运行中策略：{symbol} - {strategy_data.get('strategy_id')}")
                    
                    # 创建策略对象
                    strategy = Strategy(
                        symbol=symbol,
                        strategy_id=strategy_data.get("strategy_id", "unknown"),
                        strategy_name=strategy_data.get("strategy_name", "未知策略"),
                        side=strategy_data.get("side", "LONG"),
                        leverage=strategy_data.get("leverage", 1),
                        amount=Decimal(strategy_data.get("amount", "0")),
                        status="running",
                        start_time=datetime.fromisoformat(strategy_data["start_time"])
                        if strategy_data.get("start_time")
                        else None,
                        is_hot_plug=True,
                    )
                    
                    # 添加到内存
                    self.strategies[symbol] = strategy
                    
                    logger.info(f"✅ 已恢复策略：{symbol}")
            
            logger.info(f"📊 加载了 {len(self.strategies)} 个策略")
            
        except Exception as e:
            logger.error(f"⚠️ 加载策略文件失败：{e}")
    
    def _save_strategies(self):
        """保存策略到持久化文件"""
        try:
            data = {}
            for symbol, strategy in self.strategies.items():
                data[symbol] = {
                    "symbol": strategy.symbol,
                    "strategy_id": strategy.strategy_id,
                    "strategy_name": strategy.strategy_name,
                    "side": strategy.side,
                    "leverage": strategy.leverage,
                    "amount": str(strategy.amount),
                    "status": strategy.status,
                    "start_time": strategy.start_time.isoformat()
                    if strategy.start_time
                    else None,
                    "stop_time": strategy.stop_time.isoformat()
                    if strategy.stop_time
                    else None,
                    "is_hot_plug": strategy.is_hot_plug,
                }
            
            # 同时保存止损单 ID
            if self.stop_loss_ids:
                data["_stop_loss_ids"] = self.stop_loss_ids
            
            with open(self.PERSISTENCE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"📝 已保存 {len(data)} 个策略")
            
        except Exception as e:
            logger.error(f"❌ 保存策略失败：{e}")
    
    def _create_stop_loss_with_check(self, symbol: str, strategy: Strategy):
        """
        创建止损单（带查重机制 + Phase 2 异常处理）
        
        Args:
            symbol (str): 交易对
            strategy (Strategy): 策略实例
        """
        if not self.connector:
            logger.warning(f"⚠️ 连接器未设置，跳过止损单创建")
            return
        
        # Phase 2 集成：使用异常处理引擎
        if self.exception_manager:
            try:
                self.exception_manager.handle_exception(
                    lambda: self._do_create_stop_loss(symbol, strategy)
                )
            except Exception as e:
                logger.error(f"❌ 止损单创建异常：{e}")
        else:
            self._do_create_stop_loss(symbol, strategy)
    
    def _do_create_stop_loss(self, symbol: str, strategy: Strategy):
        """
        实际创建止损单的逻辑
        
        Args:
            symbol (str): 交易对
            strategy (Strategy): 策略实例
        """
        try:
            # 1. 查重：检查是否已有止损单
            check_result = self.connector.check_stop_loss_exists(
                symbol=symbol,
                side="SELL" if strategy.side == "LONG" else "BUY"
            )
            
            if not check_result.is_success:
                logger.warning(f"⚠️ 止损单查重失败：{check_result.message}")
                return
            
            if check_result.data.get("exists"):
                count = check_result.data.get("count", 0)
                logger.warning(f"⚠️ {symbol} 已有 {count} 个活跃止损单，跳过创建")
                # 保存已有的止损单 ID
                orders = check_result.data.get("orders", [])
                if orders:
                    self.stop_loss_ids[symbol] = orders[0].get("algo_id", "")
                return
            
            # 2. 计算止损价格（示例：入场价的 95%）
            entry_price = strategy.entry_price or Decimal("2000")
            stop_price = entry_price * Decimal("0.95")
            
            # 3. 计算止损单数量
            quantity = strategy.position_size or Decimal("0.01")
            
            # 4. 创建止损单
            result = self.connector.create_stop_loss_order(
                symbol=symbol,
                side="SELL" if strategy.side == "LONG" else "BUY",
                quantity=quantity,
                stop_price=stop_price
            )
            
            if result.is_success:
                algo_id = result.data.get("algo_id", "")
                self.stop_loss_ids[symbol] = algo_id
                logger.info(f"✅ {symbol} 止损单已创建：{algo_id} @ {stop_price}")
            else:
                logger.error(f"❌ {symbol} 止损单创建失败：{result.message}")
            
        except Exception as e:
            logger.error(f"❌ 创建止损单异常：{e}")
    
    @handle_exceptions()
    @log_execution()
    def start_strategy(self, symbol: str, strategy_id: str, **kwargs) -> Result:
        """
        启动策略
        
        Args:
            symbol (str): 交易对
            strategy_id (str): 策略 ID
            **kwargs: 策略参数（leverage, amount, side 等）
        
        Returns:
            Result: 操作结果
        
        Example:
            >>> manager.start_strategy('ETHUSDT', 'breakout', leverage=5, amount=100)
            Result.ok(data={'symbol': 'ETHUSDT', 'strategy_id': 'breakout'})
        """
        # 检查是否已有策略
        if symbol in self.strategies:
            existing = self.strategies[symbol]
            if existing.is_running():
                return fail(
                    error_code="STRATEGY_EXISTS",
                    message=f"{symbol} 已有活跃策略 ({existing.strategy_id})"
                )
        
        # 提取参数
        side = kwargs.get("side", "LONG")
        leverage = kwargs.get("leverage", 1)
        amount = Decimal(str(kwargs.get("amount", 100)))
        strategy_name = kwargs.get("strategy_name", strategy_id)
        
        # 创建策略对象
        strategy = Strategy(
            symbol=symbol,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            side=side,
            leverage=leverage,
            amount=amount,
            status="running",
            start_time=datetime.now(),
            is_hot_plug=True,
        )
        
        # 添加到内存
        self.strategies[symbol] = strategy
        
        # 启动信号计算线程
        stop_flag = False
        self.stop_flags[symbol] = stop_flag
        
        thread = threading.Thread(
            target=self._signal_calculation_loop,
            args=(symbol, stop_flag),
            daemon=True,
            name=f"strategy-{symbol}"
        )
        thread.start()
        self.threads[symbol] = thread
        
        # 持久化
        self._save_strategies()
        
        # Phase 2 集成：使用资金管理计算仓位
        if self.capital_manager and self.connector:
            try:
                # 获取当前价格（示例）
                current_price = Decimal("2000")  # 实际应从行情获取
                
                # 计算仓位大小
                position_size = self.capital_manager.calculate_position_size(
                    amount=strategy.amount,
                    price=current_price,
                    leverage=strategy.leverage,
                    mode=CapitalManager.POSITION_MODE_FIXED
                )
                
                # 更新策略的仓位大小
                strategy.position_size = position_size
                
                logger.info(f"💰 仓位计算完成：{symbol} {position_size}")
                
            except Exception as e:
                logger.warning(f"⚠️ 仓位计算失败：{e}")
        
        # 创建止损单（带查重机制）
        if self.connector:
            self._create_stop_loss_with_check(symbol, strategy)
        
        logger.info(f"🚀 策略已启动：{symbol} - {strategy_id}")
        
        return ok(
            data={
                "symbol": symbol,
                "strategy_id": strategy_id,
                "thread_name": thread.name,
                "position_size": str(strategy.position_size) if strategy.position_size else None
            },
            message=f"{symbol} 策略已启动"
        )
    
    @handle_exceptions()
    @log_execution()
    def stop_strategy(self, symbol: str) -> Result:
        """
        停止策略
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Result: 操作结果
        """
        if symbol not in self.strategies:
            return fail(
                error_code="STRATEGY_NOT_FOUND",
                message=f"{symbol} 没有活跃策略"
            )
        
        # 设置停止标志
        self.stop_flags[symbol] = True
        
        # 等待线程安全退出（最多 10 秒）
        if symbol in self.threads:
            thread = self.threads[symbol]
            thread.join(timeout=10)
            
            if thread.is_alive():
                logger.warning(f"⚠️ 策略线程 {thread.name} 未在 10 秒内退出")
            
            del self.threads[symbol]
        
        # 取消止损单
        if self.connector and symbol in self.stop_loss_ids:
            algo_id = self.stop_loss_ids[symbol]
            result = self.connector.cancel_algo_order(symbol, algo_id)
            if result.is_success:
                logger.info(f"✅ {symbol} 止损单已取消：{algo_id}")
            else:
                logger.warning(f"⚠️ {symbol} 止损单取消失败：{result.message}")
            del self.stop_loss_ids[symbol]
        
        # 从内存移除（先移除再保存）
        del self.strategies[symbol]
        
        # 持久化（保存剩余策略）
        self._save_strategies()
        
        logger.info(f"🛑 策略已停止：{symbol}")
        
        return ok(data={"symbol": symbol}, message=f"{symbol} 策略已停止")
    
    def _signal_calculation_loop(self, symbol: str, stop_flag: bool):
        """
        持续计算交易信号（热插拔核心）
        
        Args:
            symbol (str): 交易对
            stop_flag (bool): 停止标志
        
        说明:
            - 这是策略的核心循环
            - 每分钟计算一次信号
            - 检测到 stop_flag 立即退出
            - 异常后自动重试
        """
        logger.info(f"🔄 {symbol} 信号计算线程已启动")
        
        while not stop_flag:
            try:
                # 1. 获取策略实例
                strategy = self.strategies.get(symbol)
                if not strategy:
                    logger.warning(f"⚠️ {symbol} 策略实例不存在，退出线程")
                    break
                
                # 2. 获取最新 K 线（这里简化，实际应该从数据源获取）
                # kline = self._get_latest_kline(symbol)
                
                # 3. 计算指标
                # indicators = self._calculate_indicators(kline)
                
                # 4. 生成信号
                # signal = self._generate_signal(strategy, indicators)
                
                # 5. 执行信号
                # if signal:
                #     self._execute_signal(symbol, signal)
                
                # 6. 更新策略 PnL
                # self._update_strategy_pnl(strategy)
                
                # 7. 更新心跳（每 30 秒）
                heartbeat_monitor.update_heartbeat(symbol)
                
                # 8. 等待下一个 K 线（1 分钟）
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ {symbol} 信号计算异常：{e}")
                time.sleep(10)  # 异常后等待 10 秒
        
        logger.info(f"🛑 {symbol} 信号计算线程已停止")
    
    def get_active_strategies(self) -> List[Strategy]:
        """
        获取活跃策略列表
        
        Returns:
            List[Strategy]: 策略列表
        """
        return [s for s in self.strategies.values() if s.is_running()]
    
    def get_strategy_status(self, symbol: str) -> Optional[Strategy]:
        """
        获取策略状态
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Optional[Strategy]: 策略状态，不存在返回 None
        """
        return self.strategies.get(symbol)
    
    def get_strategy_health(self, symbol: str) -> Dict:
        """
        获取策略健康状态（包含心跳检测）
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Dict: 健康状态信息
        """
        strategy = self.strategies.get(symbol)
        health_status = heartbeat_monitor.check_health(symbol)
        heartbeat_age = heartbeat_monitor.get_heartbeat_age(symbol)
        
        return {
            "symbol": symbol,
            "strategy": strategy.to_dict() if strategy else None,
            "health_status": health_status.value,
            "heartbeat_age_seconds": heartbeat_age,
            "is_healthy": health_status == HealthStatus.HEALTHY,
            "last_heartbeat": heartbeat_monitor.get_last_heartbeat(symbol).isoformat() if heartbeat_monitor.get_last_heartbeat(symbol) else None
        }
    
    def get_all_health_status(self) -> Dict:
        """
        获取所有策略健康状态
        
        Returns:
            Dict: 所有策略的健康状态报告
        """
        return heartbeat_monitor.get_health_report()
    
    @handle_exceptions()
    def reload_strategies(self) -> Result:
        """
        重新加载策略（热插拔）
        
        Returns:
            Result: 操作结果
        """
        # 清除内存中的策略
        self.strategies.clear()
        self.threads.clear()
        self.stop_flags.clear()
        
        # 重新加载
        self._load_strategies()
        
        return ok(
            data={"count": len(self.strategies)},
            message=f"已重新加载 {len(self.strategies)} 个策略"
        )
    
    # ==================== 辅助方法 ====================
    
    def _get_latest_kline(self, symbol: str) -> dict:
        """获取最新 K 线（待实现）"""
        # TODO: 从行情数据层获取
        return {}
    
    def _calculate_indicators(self, kline: dict) -> dict:
        """计算技术指标（待实现）"""
        # TODO: 实现指标计算
        return {}
    
    def _generate_signal(self, strategy: Strategy, indicators: dict) -> Optional[str]:
        """生成交易信号（待实现）"""
        # TODO: 根据策略逻辑生成信号
        return None
    
    def _execute_signal(self, symbol: str, signal: str):
        """执行交易信号（待实现）"""
        # TODO: 调用执行引擎
        pass
    
    def _update_strategy_pnl(self, strategy: Strategy):
        """更新策略 PnL（待实现）"""
        # TODO: 从连接器获取实时价格
        pass


# 全局实例
_strategy_manager: Optional[StrategyManager] = None


def get_strategy_manager() -> StrategyManager:
    """获取全局策略管理器实例"""
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
    return _strategy_manager
