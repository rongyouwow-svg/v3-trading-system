#!/usr/bin/env python3
"""
🦞 自动交易模拟策略
经典的三步交易：开仓 50% → 加仓 30% → 平仓 100%
"""

from strategies.base_strategy import BaseStrategy
import asyncio

class AutoSimStrategy(BaseStrategy):
    """自动交易模拟策略 - 三步交易"""
    
    async def start(self):
        """启动自动交易模拟策略"""
        self.status = 'running'
        self.log(f"🚀 自动交易模拟启动：{self.symbol}")
        self.log(f"杠杆：{self.leverage}x, 保证金：${self.amount}")
        
        try:
            # 第 1 步：开仓 50%
            self.log("⏱️ T+0 秒：准备开仓 50%")
            self.emit_signal({
                'type': 'OPEN',
                'side': 'BUY',
                'percentage': 0.5,
                'stop_loss_pct': 0.05
            })
            await asyncio.sleep(5)
            
            # 第 2 步：加仓 30%
            self.log("⏱️ T+5 秒：准备加仓 30%")
            self.emit_signal({
                'type': 'ADD',
                'side': 'BUY',
                'percentage': 0.3,
                'stop_loss_pct': 0.05
            })
            await asyncio.sleep(5)
            
            # 第 3 步：← 注释掉自动平仓，让持仓保持以便测试止损单
            # self.log("⏱️ T+10 秒：准备平仓 100%")
            # self.emit_signal({
            #     'type': 'CLOSE',
            #     'side': 'SELL',
            #     'percentage': 1.0
            # })
            
            self.log("✅ 开仓 + 加仓完成，持仓保持，等待止损单测试")
            self.status = 'running'  # ← 保持运行状态，不自动完成
            
        except Exception as e:
            self.log(f"❌ 策略执行失败：{e}")
            self.status = 'failed'
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
        status['strategy_name'] = 'auto_sim'
        status['description'] = '自动交易模拟 - 开仓 50% → 加仓 30% → 平仓 100%'
        return status
