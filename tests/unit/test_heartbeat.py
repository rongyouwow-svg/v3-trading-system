#!/usr/bin/env python3
"""
测试心跳检测模块
"""

import pytest
import time
from datetime import datetime, timedelta
from modules.health.heartbeat import (
    HeartbeatMonitor,
    HealthStatus,
    get_heartbeat_monitor,
    reset_heartbeat_monitor
)


class TestHeartbeatMonitor:
    """测试心跳检测器"""
    
    @pytest.fixture
    def monitor(self):
        """创建心跳检测器实例"""
        reset_heartbeat_monitor()
        return HeartbeatMonitor()
    
    def test_update_heartbeat(self, monitor):
        """测试更新心跳"""
        monitor.update_heartbeat("ETHUSDT")
        
        assert "ETHUSDT" in monitor.heartbeats
        assert monitor.statuses["ETHUSDT"] == HealthStatus.HEALTHY
        assert monitor.counters["ETHUSDT"] == 1
    
    def test_check_health_healthy(self, monitor):
        """测试检查健康状态（健康）"""
        monitor.update_heartbeat("ETHUSDT")
        status = monitor.check_health("ETHUSDT")
        
        assert status == HealthStatus.HEALTHY
    
    def test_check_health_unknown(self, monitor):
        """测试检查健康状态（未知）"""
        status = monitor.check_health("NONEXISTENT")
        
        assert status == HealthStatus.UNKNOWN
    
    def test_check_health_unhealthy(self, monitor):
        """测试检查健康状态（不健康）"""
        # 手动设置一个旧的心跳时间
        monitor.heartbeats["ETHUSDT"] = datetime.now() - timedelta(seconds=400)
        status = monitor.check_health("ETHUSDT")
        
        assert status == HealthStatus.UNHEALTHY
    
    def test_get_healthy_strategies(self, monitor):
        """测试获取健康策略列表"""
        monitor.update_heartbeat("ETHUSDT")
        monitor.update_heartbeat("BTCUSDT")
        
        healthy = monitor.get_healthy_strategies()
        
        assert "ETHUSDT" in healthy
        assert "BTCUSDT" in healthy
        assert len(healthy) == 2
    
    def test_get_unhealthy_strategies(self, monitor):
        """测试获取不健康策略列表"""
        monitor.update_heartbeat("ETHUSDT")
        monitor.heartbeats["BTCUSDT"] = datetime.now() - timedelta(seconds=400)
        
        # 刷新状态
        monitor.check_health("BTCUSDT")
        
        unhealthy = monitor.get_unhealthy_strategies()
        
        assert "BTCUSDT" in unhealthy
        assert "ETHUSDT" not in unhealthy
    
    def test_get_last_heartbeat(self, monitor):
        """测试获取最后心跳时间"""
        before = datetime.now()
        monitor.update_heartbeat("ETHUSDT")
        after = datetime.now()
        
        last_beat = monitor.get_last_heartbeat("ETHUSDT")
        
        assert last_beat is not None
        assert before <= last_beat <= after
    
    def test_get_heartbeat_age(self, monitor):
        """测试获取心跳年龄"""
        monitor.update_heartbeat("ETHUSDT")
        time.sleep(0.1)
        
        age = monitor.get_heartbeat_age("ETHUSDT")
        
        assert age is not None
        assert 0.1 <= age < 1.0
    
    def test_get_health_report(self, monitor):
        """测试获取健康报告"""
        monitor.update_heartbeat("ETHUSDT")
        monitor.update_heartbeat("BTCUSDT")
        
        report = monitor.get_health_report()
        
        assert "timestamp" in report
        assert report["total_strategies"] == 2
        assert report["healthy_count"] == 2
        assert report["unhealthy_count"] == 0
        assert "ETHUSDT" in report["strategies"]
        assert "BTCUSDT" in report["strategies"]
    
    def test_set_status(self, monitor):
        """测试手动设置状态"""
        monitor.update_heartbeat("ETHUSDT")
        monitor.set_status("ETHUSDT", HealthStatus.UNHEALTHY)
        
        assert monitor.statuses["ETHUSDT"] == HealthStatus.UNHEALTHY
    
    def test_remove_strategy(self, monitor):
        """测试移除策略"""
        monitor.update_heartbeat("ETHUSDT")
        monitor.remove_strategy("ETHUSDT")
        
        assert "ETHUSDT" not in monitor.heartbeats
        assert "ETHUSDT" not in monitor.statuses
        assert "ETHUSDT" not in monitor.counters
    
    def test_clear(self, monitor):
        """测试清空所有记录"""
        monitor.update_heartbeat("ETHUSDT")
        monitor.update_heartbeat("BTCUSDT")
        monitor.clear()
        
        assert len(monitor.heartbeats) == 0
        assert len(monitor.statuses) == 0
        assert len(monitor.counters) == 0
    
    def test_heartbeat_counter(self, monitor):
        """测试心跳计数器"""
        monitor.update_heartbeat("ETHUSDT")
        monitor.update_heartbeat("ETHUSDT")
        monitor.update_heartbeat("ETHUSDT")
        
        assert monitor.counters["ETHUSDT"] == 3
    
    def test_check_all_health(self, monitor):
        """测试检查所有策略健康状态"""
        monitor.update_heartbeat("ETHUSDT")
        monitor.update_heartbeat("BTCUSDT")
        
        all_status = monitor.check_all_health()
        
        assert len(all_status) == 2
        assert all_status["ETHUSDT"] == HealthStatus.HEALTHY
        assert all_status["BTCUSDT"] == HealthStatus.HEALTHY


class TestGlobalMonitor:
    """测试全局心跳检测器"""
    
    def test_get_heartbeat_monitor(self):
        """测试获取全局实例"""
        reset_heartbeat_monitor()
        
        monitor1 = get_heartbeat_monitor()
        monitor2 = get_heartbeat_monitor()
        
        assert monitor1 is monitor2  # 同一个实例
    
    def test_reset_heartbeat_monitor(self):
        """测试重置全局实例"""
        monitor1 = get_heartbeat_monitor()
        reset_heartbeat_monitor()
        monitor2 = get_heartbeat_monitor()
        
        assert monitor1 is not monitor2  # 不同实例
