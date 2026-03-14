#!/usr/bin/env python3
"""
⏰ 策略定时停止脚本

在中午 12:00 自动停止所有 RSI 策略
"""

import subprocess
import sys
from datetime import datetime

def stop_strategy(process_name: str):
    """停止策略进程"""
    try:
        # 查找进程
        result = subprocess.run(
            f"ps aux | grep '{process_name}' | grep -v grep | awk '{{print $2}}'",
            shell=True,
            capture_output=True,
            text=True
        )
        
        pids = result.stdout.strip().split('\n')
        
        if pids and pids[0]:
            for pid in pids:
                print(f"🛑 停止进程：{pid}")
                subprocess.run(f"kill {pid}", shell=True)
            
            print(f"✅ {process_name} 已停止")
            return True
        else:
            print(f"⚠️ {process_name} 未找到")
            return False
    except Exception as e:
        print(f"❌ 停止失败：{e}")
        return False

def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"⏰ 策略定时停止")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 停止 ETH 策略
    print("1. 停止 ETH RSI 策略...")
    stop_strategy("rsi_1min_strategy.py")
    
    # 停止 LINK 策略
    print("\n2. 停止 LINK RSI 策略...")
    stop_strategy("link_rsi_detailed_strategy.py")
    
    print(f"\n{'='*60}")
    print(f"✅ 所有策略已停止")
    print(f"{'='*60}\n")
    
    print("📝 请手动生成测试报告:")
    print("   - ETH 策略报告：logs/ETH_RSI_STRATEGY_REPORT.md")
    print("   - LINK 策略报告：logs/LINK_RSI_STRATEGY_REPORT.md")
    print("   - v3 系统评测：logs/V3_SYSTEM_EVALUATION.md")

if __name__ == "__main__":
    main()
