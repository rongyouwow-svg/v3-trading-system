#!/usr/bin/env python3
"""
🦞 测试策略
简单的信号触发测试
"""

from strategies.base_strategy import BaseStrategy
import asyncio

class TestStrategy(BaseStrategy):
    """测试策略 - 简单的开平仓测试"""
    
    async def start(self):
        """启动测试策略"""
        self.status = 'running'
        self.log(f"🚀 测试策略启动：{self.symbol}")
        self.log(f"杠杆：{self.leverage}x, 保证金：${self.amount}")
        
        try:
            # T+0 秒：开仓
            self.log("⏱️ T+0 秒：准备开仓")
            self.emit_signal({
                'type': 'OPEN',
                'side': 'BUY',
                'percentage': 1.0,  # 100% 仓位
                'stop_loss_pct': 0.05  # 5% 止损
            })
            
            # 等待 10 秒
            await asyncio.sleep(10)
            
            # T+10 秒：平仓
            self.log("⏱️ T+10 秒：准备平仓")
            self.emit_signal({
                'type': 'CLOSE',
                'side': 'SELL',
                'percentage': 1.0  # 100% 平仓
            })
            
            self.log("✅ 测试策略完成")
            self.status = 'completed'
            
        except Exception as e:
            self.log(f"❌ 策略执行失败：{e}")
            self.status = 'failed'
            # 紧急平仓
            self.emit_signal({
                'type': 'EMERGENCY_CLOSE',
                'side': 'SELL',
                'percentage': 1.0
            })
    
    async def stop(self):
        """停止策略"""
        self.log("⚠️ 策略被手动停止")
        await super().stop()
    
    def get_status(self) -> dict:
        """获取策略状态"""
        status = super().get_status()
        status['strategy_name'] = 'test_strategy'
        status['description'] = '测试策略 - 简单开平仓测试'
        return status
