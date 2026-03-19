#!/usr/bin/env python3
"""
📊 v3 系统 30 分钟测试报告生成脚本

在策略重启 30 分钟后自动生成完整测试报告
"""

import requests
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"
REPORTS_DIR = "/root/.openclaw/workspace/quant/v3-architecture/logs/reports"

os.makedirs(REPORTS_DIR, exist_ok=True)

def get_strategy_status():
    """获取策略状态"""
    try:
        response = requests.get(f"{BASE_URL}/api/strategy/active", timeout=10)
        return response.json()
    except:
        return None

def get_account_info():
    """获取账户信息"""
    try:
        response = requests.get(f"{BASE_URL}/api/binance/account-info", timeout=10)
        return response.json()
    except:
        return None

def get_positions():
    """获取持仓"""
    try:
        response = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
        return response.json()
    except:
        return None

def get_trades():
    """获取交易记录"""
    try:
        response = requests.get(f"{BASE_URL}/api/binance/trades?limit=50", timeout=10)
        return response.json()
    except:
        return None

def generate_report():
    """生成测试报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    strategy_data = get_strategy_status()
    account_data = get_account_info()
    positions_data = get_positions()
    trades_data = get_trades()
    
    report = []
    report.append("# 🧪 v3 系统 30 分钟测试报告")
    report.append("")
    report.append(f"**测试时间**: {timestamp}")
    report.append(f"**测试周期**: 30 分钟")
    report.append(f"**测试版本**: v3.1.0")
    report.append("")
    
    # 系统状态
    report.append("## 📊 系统状态")
    report.append("")
    report.append("| 组件 | 状态 |")
    report.append("|------|------|")
    report.append(f"| Web 服务 | {'✅ 运行中' if strategy_data else '❌ 已停止'} |")
    report.append(f"| 策略进程 | {'✅ 运行中' if strategy_data and strategy_data.get('count', 0) > 0 else '❌ 已停止'} |")
    report.append("")
    
    # 策略状态
    report.append("## 🤖 策略状态")
    report.append("")
    if strategy_data and strategy_data.get('success'):
        strategies = strategy_data.get('active_strategies', [])
        report.append("| 策略 | RSI | 持仓 | 信号 | 状态 |")
        report.append("|------|-----|------|------|------|")
        for s in strategies:
            report.append(f"| {s['symbol']} | {s.get('rsi', 0):.2f} | {s.get('position') or '无'} | {s.get('signals_sent', 0)}/{s.get('signals_executed', 0)} | {s.get('status', 'N/A')} |")
    else:
        report.append("策略已停止或无法获取状态")
    report.append("")
    
    # 账户信息
    report.append("## 💰 账户信息")
    report.append("")
    if account_data and account_data.get('success'):
        account = account_data.get('account', {})
        report.append(f"- **总余额**: {account.get('balance', 0):.2f} USDT")
        report.append(f"- **可用余额**: {account.get('available', 0):.2f} USDT")
    else:
        report.append("无法获取账户信息")
    report.append("")
    
    # 持仓信息
    report.append("## 📈 持仓信息")
    report.append("")
    if positions_data and positions_data.get('success'):
        positions = positions_data.get('positions', [])
        if positions:
            for pos in positions:
                report.append(f"- **{pos['symbol']}** {pos['side']} {pos['size']} @ {pos['entry_price']}")
                report.append(f"  - 当前价：{pos['current_price']}")
                report.append(f"  - 未实现盈亏：{pos['unrealized_pnl']:.2f} USDT ({pos['unrealized_pnl_pct']:.2f}%)")
        else:
            report.append("✅ 无持仓（空仓状态）")
    else:
        report.append("无法获取持仓信息")
    report.append("")
    
    # 交易记录
    report.append("## 💹 交易记录")
    report.append("")
    if trades_data and trades_data.get('success'):
        trades = trades_data.get('trades', [])
        report.append(f"**总成交数**: {len(trades)} 条")
        report.append("")
        report.append("### 最近 5 笔成交")
        report.append("")
        report.append("| 时间 | 交易对 | 方向 | 类型 | 价格 | 数量 |")
        report.append("|------|--------|------|------|------|------|")
        for t in trades[:5]:
            report.append(f"| {t.get('trade_time', 'N/A')} | {t.get('symbol', 'N/A')} | {t.get('side', 'N/A')} | {t.get('order_type', 'N/A')} | {t.get('price', 0)} | {t.get('quantity', 0)} |")
    else:
        report.append("无法获取交易记录")
    report.append("")
    
    # 测试总结
    report.append("## ✅ 测试总结")
    report.append("")
    report.append("### 已完成测试项")
    report.append("")
    report.append("- [ ] 策略启动/停止")
    report.append("- [ ] RSI 计算准确性")
    report.append("- [ ] 信号生成逻辑")
    report.append("- [ ] 订单创建执行")
    report.append("- [ ] 仓位控制")
    report.append("- [ ] 止损管理")
    report.append("- [ ] 前端功能")
    report.append("")
    
    report.append("### 问题汇总")
    report.append("")
    report.append("1. 止损单页面路由问题（已修复）")
    report.append("2. Web 服务稳定性问题（待调查）")
    report.append("")
    
    report.append("### 下一步计划")
    report.append("")
    report.append("1. 重启策略，观察开仓情况")
    report.append("2. 测试止损触发功能")
    report.append("3. 验证仓位控制逻辑")
    report.append("4. 生成完整测试报告")
    report.append("")
    
    report.append("---")
    report.append("")
    report.append(f"**报告生成时间**: {timestamp}")
    report.append(f"**下次报告**: 60 分钟后")
    
    return "\n".join(report)

if __name__ == "__main__":
    report = generate_report()
    
    # 保存报告
    filename = f"v3_test_report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.md"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 同时更新最新报告
    latest_path = os.path.join(REPORTS_DIR, "LATEST_TEST_REPORT.md")
    with open(latest_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 测试报告已生成：{filepath}")
    print("")
    print(report)
