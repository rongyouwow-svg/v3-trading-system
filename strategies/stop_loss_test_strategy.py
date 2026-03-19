#!/usr/bin/env python3
"""
🦞 止损单测试策略 v2
设计逻辑：
1. 开单 50% → 创建第一个止损单
2. 间隔 15 秒
3. 追加 50% → 更新止损单（基于新持仓均价）
4. 等待手动关闭
5. 平仓 → 等待持仓归零 → 取消止损单
"""

from strategies.base_strategy import BaseStrategy
import asyncio

class StopLossTestStrategy(BaseStrategy):
    """止损单测试策略 v2"""
    
    async def start(self):
        """启动止损单测试策略"""
        self.status = 'running'
        self.log(f"🚀 止损单测试策略 v2 启动：{self.symbol}")
        self.log(f"杠杆：{self.leverage}x, 保证金：${self.amount}")
        
        try:
            # 第 1 步：开单 50%
            self.log("⏱️ T+0 秒：准备开单 50%")
            self.emit_signal({
                'type': 'OPEN',
                'side': 'BUY',
                'percentage': 0.5,
                'stop_loss_pct': 0.05  # 5% 止损
            })
            self.log("✅ 开单 50% 完成，等待创建第一个止损单...")
            
            # 等待 15 秒
            self.log("⏱️ 等待 15 秒...")
            await asyncio.sleep(15)
            
            # 第 2 步：追加 50%
            self.log("⏱️ T+15 秒：准备追加 50%")
            self.emit_signal({
                'type': 'ADD',
                'side': 'BUY',
                'percentage': 0.5,
                'stop_loss_pct': 0.05  # 5% 止损
            })
            self.log("✅ 追加 50% 完成，等待更新止损单...")
            
            # 等待手动关闭
            self.log("✅ 开仓完成，等待手动关闭策略...")
            self.log("📊 预期：持仓 100%，止损单基于均价计算")
            
            # 保持运行状态，等待用户手动停止
            while self.status == 'running':
                await asyncio.sleep(5)
            
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
        self.log("📤 发送平仓信号...")
        await super().stop()
    
    def get_status(self) -> dict:
        """获取策略状态"""
        status = super().get_status()
        status['strategy_name'] = 'stop_loss_test_v2'
        status['description'] = '止损单测试策略 v2 - 开单 50% → 15 秒 → 追加 50%'
        return status
