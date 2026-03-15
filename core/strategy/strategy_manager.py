#!/usr/bin/env python3
"""
📊 策略管理器 v3.1

职责:
    - 策略模块动态加载（热插拔）
    - 策略生命周期管理（启动/停止/重启）
    - 策略健康检查
    - 并行执行（线程池）

特性:
    - 热插拔（动态加载/卸载策略）
    - 线程池并行执行（默认 10 个线程）
    - 崩溃隔离（单个策略崩溃不影响其他）
    - 自动重启（策略无响应时）

用法:
    from core.strategy.strategy_manager import StrategyManager
    
    manager = StrategyManager()
    manager.load_strategy('ETH_RSI', config)
    manager.start_strategy('ETH_RSI')
    manager.run_tick()
"""

import importlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, Future
import time

logger = logging.getLogger(__name__)


class StrategyManager:
    """
    策略管理器
    
    核心功能:
        - 策略模块动态加载（热插拔）
        - 策略生命周期管理
        - 并行执行（线程池）
        - 健康检查
    """
    
    def __init__(self, max_workers: int = 10, health_check_interval: int = 300):
        """
        初始化策略管理器
        
        Args:
            max_workers: 线程池大小（默认 10）
            health_check_interval: 健康检查间隔（秒，默认 300 秒=5 分钟）
        """
        self.strategies: Dict[str, Any] = {}
        self.strategy_configs: Dict[str, Dict[str, Any]] = {}
        self.strategy_health: Dict[str, Dict[str, Any]] = {}
        
        # 线程池（并行执行）
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 健康检查配置
        self.health_check_interval = health_check_interval
        self.last_health_check = datetime.now()
        
        logger.info(f"✅ 策略管理器初始化完成 (线程池大小：{max_workers})")
    
    def load_strategy(self, name: str, config: Dict[str, Any]) -> bool:
        """
        动态加载策略模块（热插拔）
        
        Args:
            name: 策略名称（如 'ETH_RSI'）
            config: 策略配置（symbol/leverage/amount/stop_loss_pct 等）
        
        Returns:
            是否加载成功
        """
        try:
            # 检查策略是否已存在
            if name in self.strategies:
                logger.warning(f"⚠️ 策略 {name} 已存在，先卸载")
                self.unload_strategy(name)
            
            # 动态导入策略模块
            strategy_type = config.get('type', 'rsi_strategy')
            
            if strategy_type == 'rsi_strategy':
                from core.strategy.modules.rsi_1min_strategy import Strategy as RSIStrategy
                strategy = RSIStrategy(
                    symbol=config['symbol'],
                    leverage=config.get('leverage', 3),
                    amount=config.get('amount', 100),
                    stop_loss_pct=config.get('stop_loss_pct')
                )
            elif strategy_type == 'rsi_scale_in_strategy':
                from core.strategy.modules.rsi_scale_in_strategy import Strategy as RSIScaleInStrategy
                strategy = RSIScaleInStrategy(
                    symbol=config['symbol'],
                    leverage=config.get('leverage', 3),
                    total_amount=config.get('amount', 200),
                    stop_loss_pct=config.get('stop_loss_pct')
                )
            else:
                logger.error(f"未知策略类型：{strategy_type}")
                return False
            
            # 注册策略
            self.strategies[name] = strategy
            self.strategy_configs[name] = config
            self.strategy_health[name] = {
                'last_tick': datetime.now(),
                'status': 'loaded',
                'error_count': 0,
                'config': config
            }
            
            logger.info(f"✅ 策略 {name} 加载成功 (类型：{strategy_type})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 策略 {name} 加载失败：{e}")
            return False
    
    def unload_strategy(self, name: str) -> bool:
        """
        动态卸载策略模块（热插拔）
        
        Args:
            name: 策略名称
        
        Returns:
            是否卸载成功
        """
        try:
            if name not in self.strategies:
                logger.warning(f"⚠️ 策略 {name} 不存在，无法卸载")
                return False
            
            # 停止策略
            strategy = self.strategies[name]
            if hasattr(strategy, 'stop'):
                strategy.stop()
            
            # 删除策略
            del self.strategies[name]
            if name in self.strategy_configs:
                del self.strategy_configs[name]
            if name in self.strategy_health:
                del self.strategy_health[name]
            
            logger.info(f"✅ 策略 {name} 卸载成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 策略 {name} 卸载失败：{e}")
            return False
    
    def start_strategy(self, name: str, restore_state: bool = True) -> bool:
        """
        启动策略
        
        Args:
            name: 策略名称
            restore_state: 是否恢复历史状态
        
        Returns:
            是否启动成功
        """
        try:
            if name not in self.strategies:
                logger.error(f"❌ 策略 {name} 不存在，无法启动")
                return False
            
            strategy = self.strategies[name]
            
            # 恢复历史状态
            if restore_state and hasattr(strategy, 'load_state'):
                logger.info(f"🔄 恢复策略状态：{name}")
                strategy.load_state()
            
            # 启动策略
            if hasattr(strategy, 'start'):
                strategy.start()
            
            self.strategy_health[name]['status'] = 'running'
            self.strategy_health[name]['start_time'] = datetime.now()
            
            logger.info(f"✅ 策略 {name} 启动成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 策略 {name} 启动失败：{e}")
            return False
    
    def stop_strategy(self, name: str) -> bool:
        """
        停止策略
        
        Args:
            name: 策略名称
        
        Returns:
            是否停止成功
        """
        try:
            if name not in self.strategies:
                logger.error(f"❌ 策略 {name} 不存在，无法停止")
                return False
            
            strategy = self.strategies[name]
            if hasattr(strategy, 'stop'):
                strategy.stop()
            
            self.strategy_health[name]['status'] = 'stopped'
            
            logger.info(f"✅ 策略 {name} 停止成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 策略 {name} 停止失败：{e}")
            return False
    
    def run_strategy_tick(self, name: str, strategy: Any, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        执行单个策略的 tick（带异常处理）
        
        Args:
            name: 策略名称
            strategy: 策略实例
            market_data: 市场数据
        
        Returns:
            交易信号（如有）
        """
        try:
            # 调用策略的 on_tick 方法
            if hasattr(strategy, 'on_tick'):
                signal = strategy.on_tick(market_data)
                
                # 更新健康状态
                self.strategy_health[name]['last_tick'] = datetime.now()
                self.strategy_health[name]['error_count'] = 0
                
                if signal:
                    logger.info(f"📡 策略 {name} 发出信号：{signal.get('action')}")
                
                return signal
            else:
                logger.warning(f"⚠️ 策略 {name} 没有 on_tick 方法")
                return None
                
        except Exception as e:
            logger.error(f"❌ 策略 {name} 执行失败：{e}")
            self.strategy_health[name]['error_count'] = self.strategy_health[name].get('error_count', 0) + 1
            return None
    
    def run_tick(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        并行执行所有策略的 tick
        
        Args:
            market_data: 市场数据
        
        Returns:
            所有策略发出的信号列表
        """
        signals = []
        
        if not self.strategies:
            logger.debug("ℹ️ 无活跃策略，跳过 tick 执行")
            return signals
        
        # 提交所有策略到线程池（并行执行）
        futures: List[Future] = []
        for name, strategy in self.strategies.items():
            future = self.executor.submit(self.run_strategy_tick, name, strategy, market_data)
            futures.append((name, future))
        
        # 收集所有策略的结果
        for name, future in futures:
            try:
                signal = future.result(timeout=10)  # 超时 10 秒
                if signal:
                    signals.append({
                        'strategy': name,
                        'signal': signal
                    })
            except Exception as e:
                logger.error(f"❌ 策略 {name} 结果收集失败：{e}")
        
        # 健康检查（定期执行）
        self._check_health()
        
        return signals
    
    def _check_health(self):
        """
        健康检查（自动重启无响应的策略）
        """
        now = datetime.now()
        
        # 检查是否到了健康检查时间
        if (now - self.last_health_check).total_seconds() < self.health_check_interval:
            return
        
        logger.info("🏥 执行策略健康检查")
        
        for name, health in self.strategy_health.items():
            last_tick = health.get('last_tick', now)
            
            # 策略 5 分钟无响应
            if (now - last_tick).total_seconds() > self.health_check_interval:
                logger.warning(f"⚠️ 策略 {name} 无响应（最后响应：{last_tick}），尝试自动重启")
                
                # 获取配置
                config = health.get('config', {})
                
                # 重启策略
                self.unload_strategy(name)
                time.sleep(1)  # 等待 1 秒
                self.load_strategy(name, config)
                self.start_strategy(name)
        
        self.last_health_check = now
    
    def get_strategy_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取策略状态
        
        Args:
            name: 策略名称
        
        Returns:
            策略状态信息
        """
        if name not in self.strategies:
            return None
        
        strategy = self.strategies[name]
        health = self.strategy_health.get(name, {})
        
        status = {
            'name': name,
            'status': health.get('status', 'unknown'),
            'symbol': strategy.symbol if hasattr(strategy, 'symbol') else 'N/A',
            'leverage': strategy.leverage if hasattr(strategy, 'leverage') else 'N/A',
            'amount': strategy.amount if hasattr(strategy, 'amount') else 'N/A',
            'stop_loss_pct': strategy.stop_loss_pct if hasattr(strategy, 'stop_loss_pct') else '5% (兜底)',
            'last_tick': health.get('last_tick', 'N/A'),
            'error_count': health.get('error_count', 0),
            'start_time': health.get('start_time', 'N/A')
        }
        
        return status
    
    def get_all_status(self) -> List[Dict[str, Any]]:
        """
        获取所有策略状态
        
        Returns:
            所有策略状态列表
        """
        status_list = []
        for name in self.strategies:
            status = self.get_strategy_status(name)
            if status:
                status_list.append(status)
        return status_list
    
    def shutdown(self):
        """
        关闭策略管理器（停止所有策略）
        """
        logger.info("🛑 关闭策略管理器")
        
        # 停止所有策略
        for name in list(self.strategies.keys()):
            self.stop_strategy(name)
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("✅ 策略管理器已关闭")
