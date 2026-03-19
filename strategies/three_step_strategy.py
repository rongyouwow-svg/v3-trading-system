#!/usr/bin/env python3
"""
🦞 三步交易策略
完整的交易流程：开仓 50% → 加仓 30% → 平仓 100%
用于验证交易记录完整性和加仓功能
"""

from strategies.base_strategy import BaseStrategy
import asyncio

class ThreeStepStrategy(BaseStrategy):
    """三步交易策略 - 开仓 50% → 加仓 30% → 平仓 100%"""
    
    async def start(self):
        """启动三步交易策略"""
        self.status = 'running'
        self.log(f"🚀 三步交易策略启动：{self.symbol}")
        self.log(f"杠杆：{self.leverage}x, 保证金：${self.amount}")
        
        try:
            # === 第 1 步：开仓 50% ===
            self.log("⏱️ T+0 秒：准备开仓 50%")
            self.emit_signal({
                'type': 'OPEN',
                'side': 'BUY',
                'percentage': 0.5,  # 50% 仓位
                'stop_loss_pct': 0.05  # 5% 止损
            })
            self.log("✅ 第 1 步完成：开仓 50%")
            
            # 等待 5 秒
            await asyncio.sleep(5)
            
            # === 第 2 步：加仓 30% ===
            self.log("⏱️ T+5 秒：准备加仓 30%")
            self.emit_signal({
                'type': 'ADD',
                'side': 'BUY',
                'percentage': 0.3,  # 30% 加仓
                'stop_loss_pct': 0.05  # 5% 止损
            })
            self.log("✅ 第 2 步完成：加仓 30%（总仓位 80%）")
            
            # 等待 5 秒
            await asyncio.sleep(5)
            
            # === 第 3 步：平仓 100% ===
            self.log("⏱️ T+10 秒：准备平仓 100%")
            self.emit_signal({
                'type': 'CLOSE',
                'side': 'SELL',
                'percentage': 1.0  # 100% 平仓
            })
            self.log("✅ 第 3 步完成：平仓 100%")
            
            self.log("🎉 三步交易策略执行完成")
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
        status['strategy_name'] = 'three_step_strategy'
        status['description'] = '三步交易策略 - 开仓 50% → 加仓 30% → 平仓 100%'
        return status
