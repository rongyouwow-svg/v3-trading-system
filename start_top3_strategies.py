#!/usr/bin/env python3
"""
🦞 启动回测最优 3 策略

策略配置:
1. ETHUSDT - BB+RSI (年化 2135%)
   - 杠杆：3x
   - 金额：300 USDT
   
2. AVAXUSDT - Breakout (年化 20.18%)
   - 杠杆：8x
   - 金额：250 USDT
   
3. UNIUSDT - RSI Reversal
   - 杠杆：5x
   - 金额：200 USDT

总仓位：750 USDT
"""

import sys
import time
import signal
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from strategies.eth_bb_rsi_strategy import ETHBBRSIStrategy
from strategies.avax_breakout_strategy import AVAXBreakoutStrategy
from strategies.uni_rsi_reversal_strategy import UNIRSIReversalStrategy

from modules.utils.logger import setup_logger

logger = setup_logger("top3_strategies", log_file="logs/top3_strategies.log")

# 全局策略列表
strategies = []

def signal_handler(sig, frame):
    """处理 Ctrl+C"""
    logger.info("⏹️ 收到停止信号，正在关闭所有策略...")
    for strategy in strategies:
        strategy.is_running = False
    sys.exit(0)

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🦞 启动回测最优 3 策略")
    logger.info("=" * 60)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建策略实例
    logger.info("\n【1】创建策略实例...")
    
    # ETH 策略
    eth_strategy = ETHBBRSIStrategy(
        symbol="ETHUSDT",
        leverage=3,
        amount=300,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.02
    )
    strategies.append(eth_strategy)
    logger.info(f"✅ ETH BB+RSI 策略已创建")
    
    # AVAX 策略
    avax_strategy = AVAXBreakoutStrategy(
        symbol="AVAXUSDT",
        leverage=8,
        amount=250,
        stop_loss_pct=0.06,
        trailing_stop_pct=0.02
    )
    strategies.append(avax_strategy)
    logger.info(f"✅ AVAX Breakout 策略已创建")
    
    # UNI 策略
    uni_strategy = UNIRSIReversalStrategy(
        symbol="UNIUSDT",
        leverage=5,
        amount=200,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.02
    )
    strategies.append(uni_strategy)
    logger.info(f"✅ UNI RSI Reversal 策略已创建")
    
    # 启动策略（多线程）
    logger.info("\n【2】启动策略...")
    
    import threading
    
    threads = []
    for strategy in strategies:
        thread = threading.Thread(target=strategy.run, daemon=True)
        thread.start()
        threads.append(thread)
        logger.info(f"✅ {strategy.symbol} 策略已启动")
        time.sleep(2)  # 避免同时启动
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 所有策略已启动！")
    logger.info("=" * 60)
    logger.info("\n策略配置:")
    logger.info("  ETHUSDT: 3x 杠杆，300 USDT, BB+RSI 策略")
    logger.info("  AVAXUSDT: 8x 杠杆，250 USDT, Breakout 策略")
    logger.info("  UNIUSDT: 5x 杠杆，200 USDT, RSI Reversal 策略")
    logger.info("\n总仓位：750 USDT")
    logger.info("\n按 Ctrl+C 停止所有策略")
    logger.info("=" * 60 + "\n")
    
    # 保持运行
    while True:
        time.sleep(60)
        
        # 检查策略状态
        for strategy in strategies:
            if not strategy.is_running:
                logger.warning(f"⚠️ {strategy.symbol} 策略已停止")

if __name__ == "__main__":
    main()
