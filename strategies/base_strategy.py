#!/usr/bin/env python3
"""
🦞 策略基类
所有策略必须继承此类
"""

from datetime import datetime

class BaseStrategy:
    """策略基类"""
    
    def __init__(self, gateway, symbol: str, leverage: int, amount: float):
        """
        初始化策略
        
        Args:
            gateway: 网关联例（用于发送信号和调用 API）
            symbol: 交易对（如 ETHUSDT）
            leverage: 杠杆倍数
            amount: 保证金（USDT）
        """
        self.gateway = gateway
        self.symbol = symbol
        self.leverage = leverage
        self.amount = amount
        
        # 策略状态
        self.status = 'initializing'  # initializing/running/stopped/failed
        self.position_size = 0  # 当前持仓数量
        self.position_price = 0  # 平均持仓价格
        self.logs = []  # 日志列表
        
        # 定时器
        self.timers = []
    
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def emit_signal(self, signal: dict):
        """
        发送交易信号给网关
        
        Args:
            signal: 信号字典
                    {
                      "type": "OPEN"|"ADD"|"CLOSE"|"EMERGENCY_CLOSE",
                      "side": "BUY"|"SELL",
                      "percentage": 0.5,  # 仓位百分比
                      "stop_loss_pct": 0.1  # 止损百分比（可选）
                    }
        """
        self.log(f"发送信号：{signal}")
        
        # 网关执行信号
        if hasattr(self.gateway, 'execute_signal'):
            result = self.gateway.execute_signal(self.symbol, signal)
            self.log(f"信号执行结果：{result}")
        else:
            self.log("❌ 网关没有 execute_signal 方法")
    
    async def start(self):
        """
        启动策略（默认实现，调用 on_start）
        子类可以重写此方法，或实现 on_start()
        """
        self.log("🚀 策略启动中...")
        
        # 调用子类的 on_start（如果实现了）
        if hasattr(self, 'on_start'):
            result = self.on_start()
            if result is False:
                self.status = 'failed'
                return
        
        self.status = 'running'
        self.log("✅ 策略已启动")
    
    async def stop(self):
        """
        停止策略（默认实现，调用 on_stop）
        子类可以重写此方法，或实现 on_stop()
        """
        self.log("🛑 策略停止中...")
        
        # 调用子类的 on_stop（如果实现了）
        if hasattr(self, 'on_stop'):
            result = self.on_stop()
            if result is False:
                self.log("⚠️ 停止失败")
        
        self.status = 'stopped'
        
        # 清除所有定时器
        for timer in self.timers:
            if hasattr(timer, 'cancel'):
                timer.cancel()
        self.timers.clear()
        
        self.log("✅ 策略已停止")
    
    def get_status(self) -> dict:
        """
        获取策略状态
        子类必须实现此方法
        """
        return {
            'symbol': self.symbol,
            'status': self.status,
            'leverage': self.leverage,
            'amount': self.amount,
            'position_size': self.position_size,
            'position_price': self.position_price,
            'logs': self.logs[-20:]  # 最近 20 条日志
        }
