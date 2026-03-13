#!/usr/bin/env python3
"""
测试心跳检测集成
"""

import pytest
import time
from core.strategy.manager import StrategyManager
from modules.health.heartbeat import get_heartbeat_monitor, reset_heartbeat_monitor, HealthStatus


class TestHeartbeatIntegration:
    """测试心跳检测集成"""
    
    @pytest.fixture
    def manager(self, tmp_path, monkeypatch):
        """创建策略管理器实例"""
        reset_heartbeat_monitor()
        persistence_file = tmp_path / "test_strategies.json"
        monkeypatch.setattr(StrategyManager, "PERSISTENCE_FILE", str(persistence_file))
        return StrategyManager()
    
    def test_heartbeat_update_on_start(self, manager):
        """测试启动策略时更新心跳"""
        manager.start_strategy("ETHUSDT", "breakout", leverage=5, amount=100)
        
        # 等待心跳更新
        time.sleep(0.1)
        
        health = manager.get_strategy_health("ETHUSDT")
        
        assert health["strategy"] is not None
        assert health["health_status"] == HealthStatus.HEALTHY.value
        assert health["is_healthy"] is True
        assert health["heartbeat_age_seconds"] is not None
    
    def test_heartbeat_timeout_detection(self, manager):
        """测试心跳超时检测"""
        # 直接测试心跳检测器（不通过策略管理器，避免后台线程干扰）
        monitor = get_heartbeat_monitor()
        from datetime import datetime, timedelta
        
        # 设置旧的心跳时间
        monitor.heartbeats["TESTUSDT"] = datetime.now() - timedelta(seconds=400)
        monitor.statuses["TESTUSDT"] = HealthStatus.HEALTHY
        
        # 检查健康状态
        status = monitor.check_health("TESTUSDT")
        
        # 心跳超时，应该是不健康
        assert status == HealthStatus.UNHEALTHY
    
    def test_get_all_health_status(self, manager):
        """测试获取所有策略健康状态"""
        manager.start_strategy("ETHUSDT", "breakout")
        manager.start_strategy("BTCUSDT", "rsi")
        
        report = manager.get_all_health_status()
        
        assert report["total_strategies"] == 2
        assert "ETHUSDT" in report["strategies"]
        assert "BTCUSDT" in report["strategies"]
        assert report["healthy_count"] == 2
    
    def test_heartbeat_counter_increases(self, manager):
        """测试心跳计数器增加"""
        manager.start_strategy("ETHUSDT", "breakout")
        
        monitor = get_heartbeat_monitor()
        initial_count = monitor.counters.get("ETHUSDT", 0)
        
        # 等待心跳更新（策略线程每 60 秒更新一次，这里手动更新）
        monitor.update_heartbeat("ETHUSDT")
        
        assert monitor.counters["ETHUSDT"] > initial_count
    
    def test_health_status_after_stop(self, manager):
        """测试停止策略后健康状态"""
        manager.start_strategy("ETHUSDT", "breakout")
        manager.stop_strategy("ETHUSDT")
        
        health = manager.get_strategy_health("ETHUSDT")
        
        # 策略已停止，但心跳记录还在
        assert health["strategy"] is None  # 策略已从内存移除
        assert health["last_heartbeat"] is not None  # 但有心跳记录
