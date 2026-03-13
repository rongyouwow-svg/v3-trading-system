#!/usr/bin/env python3
"""
测试止损单查重机制
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock

from connectors.binance.usdt_futures import BinanceUSDTFuturesConnector


class TestStopLossCheck:
    """测试止损单查重机制"""
    
    @pytest.fixture
    def connector(self):
        """创建连接器实例"""
        return BinanceUSDTFuturesConnector(
            api_key="test_key",
            secret_key="test_secret",
            testnet=True
        )
    
    def test_check_stop_loss_exists_no_orders(self, connector, monkeypatch):
        """测试没有止损单的情况"""
        # Mock get_algo_orders 返回空列表
        def mock_get_algo_orders(symbol, limit):
            from modules.utils.result import Result
            return Result.ok(data={"orders": [], "count": 0})
        
        monkeypatch.setattr(connector, "get_algo_orders", mock_get_algo_orders)
        
        result = connector.check_stop_loss_exists("ETHUSDT", "SELL")
        
        assert result.is_success
        assert result.data["exists"] is False
        assert result.data["count"] == 0
    
    def test_check_stop_loss_exists_with_orders(self, connector, monkeypatch):
        """测试有止损单的情况"""
        # Mock get_algo_orders 返回有止损单
        def mock_get_algo_orders(symbol, limit):
            from modules.utils.result import Result
            return Result.ok(data={
                "orders": [
                    {
                        "algo_id": "123",
                        "symbol": "ETHUSDT",
                        "side": "SELL",
                        "type": "STOP_MARKET",
                        "status": "NEW",
                        "trigger_price": "2000",
                        "quantity": "0.01"
                    }
                ],
                "count": 1
            })
        
        monkeypatch.setattr(connector, "get_algo_orders", mock_get_algo_orders)
        
        result = connector.check_stop_loss_exists("ETHUSDT", "SELL")
        
        assert result.is_success
        assert result.data["exists"] is True
        assert result.data["count"] == 1
        assert len(result.data["orders"]) == 1
    
    def test_check_stop_loss_exists_filter_by_side(self, connector, monkeypatch):
        """测试按方向筛选止损单"""
        # Mock get_algo_orders 返回多个止损单
        def mock_get_algo_orders(symbol, limit):
            from modules.utils.result import Result
            return Result.ok(data={
                "orders": [
                    {
                        "algo_id": "123",
                        "symbol": "ETHUSDT",
                        "side": "SELL",
                        "type": "STOP_MARKET",
                        "status": "NEW"
                    },
                    {
                        "algo_id": "456",
                        "symbol": "ETHUSDT",
                        "side": "BUY",
                        "type": "STOP_MARKET",
                        "status": "NEW"
                    }
                ],
                "count": 2
            })
        
        monkeypatch.setattr(connector, "get_algo_orders", mock_get_algo_orders)
        
        # 只筛选 SELL 方向的止损单
        result = connector.check_stop_loss_exists("ETHUSDT", "SELL")
        
        assert result.is_success
        assert result.data["exists"] is True
        assert result.data["count"] == 1  # 只有 1 个 SELL 方向的
        assert result.data["orders"][0]["side"] == "SELL"
    
    def test_check_stop_loss_exists_filter_completed_orders(self, connector, monkeypatch):
        """测试过滤已完成的止损单"""
        # Mock get_algo_orders 返回已完成和活跃的止损单
        def mock_get_algo_orders(symbol, limit):
            from modules.utils.result import Result
            return Result.ok(data={
                "orders": [
                    {
                        "algo_id": "123",
                        "symbol": "ETHUSDT",
                        "side": "SELL",
                        "type": "STOP_MARKET",
                        "status": "FILLED"  # 已完成
                    },
                    {
                        "algo_id": "456",
                        "symbol": "ETHUSDT",
                        "side": "SELL",
                        "type": "STOP_MARKET",
                        "status": "NEW"  # 活跃
                    }
                ],
                "count": 2
            })
        
        monkeypatch.setattr(connector, "get_algo_orders", mock_get_algo_orders)
        
        result = connector.check_stop_loss_exists("ETHUSDT", "SELL")
        
        assert result.is_success
        assert result.data["exists"] is True
        assert result.data["count"] == 1  # 只有 1 个活跃的
        assert result.data["orders"][0]["status"] == "NEW"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
