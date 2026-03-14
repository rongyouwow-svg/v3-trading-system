#!/usr/bin/env python3
"""
🔍 v3 系统 30 分钟定期检查脚本

检查项目:
1. Web 服务状态
2. 策略进程状态
3. 账户余额变化
4. 当前持仓
5. 最新交易记录
6. 策略状态
7. 止损单状态
8. 错误检测状态

输出: 监测报告到 logs/v3_monitor_YYYY-MM-DD_HH-MM.md
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List

BASE_URL = "http://localhost:3000"
LOGS_DIR = "/home/admin/.openclaw/workspace/quant/v3-architecture/logs"
MONITOR_DIR = os.path.join(LOGS_DIR, "monitoring")

os.makedirs(MONITOR_DIR, exist_ok=True)


class V3Monitor:
    """v3 系统监测器"""
    
    def __init__(self):
        self.timestamp = datetime.now()
        self.issues = []
        self.data = {}
        
    def log_issue(self, level: str, message: str):
        """记录问题"""
        self.issues.append({
            'level': level,  # INFO, WARNING, ERROR
            'message': message,
            'time': self.timestamp.strftime('%H:%M:%S')
        })
    
    def check_web_service(self) -> bool:
        """1. 检查 Web 服务"""
        try:
            response = requests.get(f"{BASE_URL}/api/strategy/active", timeout=5)
            data = response.json()
            
            if data.get('success'):
                self.data['web_service'] = 'OK'
                self.data['active_strategies_count'] = data.get('count', 0)
                return True
            else:
                self.log_issue('ERROR', 'Web 服务 API 返回失败')
                self.data['web_service'] = 'ERROR'
                return False
        except Exception as e:
            self.log_issue('ERROR', f'Web 服务无法访问：{e}')
            self.data['web_service'] = 'DOWN'
            return False
    
    def check_account(self) -> bool:
        """2. 检查账户余额"""
        try:
            response = requests.get(f"{BASE_URL}/api/binance/account-info", timeout=10)
            data = response.json()
            
            if data.get('success'):
                account = data.get('account', {})
                self.data['account_balance'] = account.get('balance', 0)
                self.data['account_available'] = account.get('available', 0)
                return True
            else:
                self.log_issue('WARNING', f'账户查询返回异常：{data}')
                self.data['account_balance'] = None
                return False
        except Exception as e:
            self.log_issue('ERROR', f'账户查询失败：{e}')
            self.data['account_balance'] = None
            return False
    
    def check_positions(self) -> bool:
        """3. 检查持仓"""
        try:
            response = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
            data = response.json()
            
            positions = data.get('positions', [])
            self.data['positions'] = positions
            self.data['positions_count'] = len(positions)
            
            if positions:
                for pos in positions:
                    self.log_issue('INFO', f"持仓：{pos['symbol']} {pos['side']} {pos['size']} @ {pos['entry_price']}")
            
            return True
        except Exception as e:
            self.log_issue('ERROR', f'持仓查询失败：{e}')
            self.data['positions'] = []
            return False
    
    def check_trades(self) -> bool:
        """4. 检查最新交易记录"""
        try:
            response = requests.get(f"{BASE_URL}/api/binance/trades?limit=5", timeout=10)
            data = response.json()
            
            if data.get('success'):
                trades = data.get('trades', [])
                self.data['recent_trades'] = trades[:5]
                
                if trades:
                    latest = trades[0]
                    self.data['latest_trade_time'] = latest.get('trade_time', 'N/A')
                    self.data['latest_trade_type'] = latest.get('order_type', 'N/A')
                    self.data['latest_trade_price'] = latest.get('price', 0)
            else:
                self.log_issue('WARNING', '交易记录查询返回异常')
                self.data['recent_trades'] = []
            
            return True
        except Exception as e:
            self.log_issue('ERROR', f'交易记录查询失败：{e}')
            self.data['recent_trades'] = []
            return False
    
    def check_strategy_status(self) -> bool:
        """5. 检查策略状态"""
        try:
            response = requests.get(f"{BASE_URL}/api/strategy/active", timeout=10)
            data = response.json()
            
            if data.get('success'):
                strategies = data.get('active_strategies', [])
                self.data['strategies'] = strategies
                
                for s in strategies:
                    rsi = s.get('rsi', 0)
                    position = s.get('position', '无')
                    symbol = s.get('symbol', 'UNKNOWN')
                    
                    # 检查 RSI 是否异常
                    if rsi < 20 or rsi > 80:
                        self.log_issue('WARNING', f'{symbol} RSI 极端值：{rsi:.2f}')
                    
                    self.log_issue('INFO', f"策略：{symbol} RSI={rsi:.2f} 持仓={position or '无'}")
            else:
                self.log_issue('WARNING', '策略状态查询返回异常')
                self.data['strategies'] = []
            
            return True
        except Exception as e:
            self.log_issue('ERROR', f'策略状态查询失败：{e}')
            self.data['strategies'] = []
            return False
    
    def check_stop_loss(self) -> bool:
        """6. 检查止损单"""
        try:
            response = requests.get(f"{BASE_URL}/api/binance/stop-loss", timeout=10)
            data = response.json()
            
            if data.get('success'):
                orders = data.get('orders', [])
                self.data['stop_loss_count'] = len(orders)
                
                if orders:
                    for order in orders:
                        self.log_issue('INFO', f"止损单：{order['symbol']} {order['side']} @ {order['trigger_price']}")
            else:
                self.log_issue('WARNING', '止损单查询返回异常')
                self.data['stop_loss_count'] = 0
            
            return True
        except Exception as e:
            self.log_issue('ERROR', f'止损单查询失败：{e}')
            self.data['stop_loss_count'] = 0
            return False
    
    def check_error_detection(self) -> bool:
        """7. 检查错误检测日志"""
        try:
            error_log = os.path.join(LOGS_DIR, "error_detection.log")
            if os.path.exists(error_log):
                # 读取最后 10 行
                with open(error_log, 'r') as f:
                    lines = f.readlines()[-10:]
                
                # 检查是否有最新错误
                for line in lines:
                    if 'ERROR' in line or '❌' in line:
                        # 检查是否是最近 30 分钟内的
                        self.log_issue('WARNING', f'错误检测日志发现异常：{line.strip()[:100]}')
                
                self.data['error_detection'] = 'OK'
            else:
                self.data['error_detection'] = 'NO_LOG'
            
            return True
        except Exception as e:
            self.log_issue('WARNING', f'错误检测检查失败：{e}')
            self.data['error_detection'] = 'UNKNOWN'
            return False
    
    def generate_report(self) -> str:
        """生成监测报告"""
        report = []
        report.append("# 🔍 v3 系统监测报告")
        report.append("")
        report.append(f"**检查时间**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**检查周期**: 30 分钟")
        report.append("")
        
        # 问题汇总
        report.append("## ⚠️ 问题汇总")
        report.append("")
        
        if not self.issues:
            report.append("✅ 无问题，系统运行正常！")
        else:
            errors = [i for i in self.issues if i['level'] == 'ERROR']
            warnings = [i for i in self.issues if i['level'] == 'WARNING']
            infos = [i for i in self.issues if i['level'] == 'INFO']
            
            report.append(f"- ❌ 错误：{len(errors)} 个")
            report.append(f"- ⚠️ 警告：{len(warnings)} 个")
            report.append(f"- ℹ️ 信息：{len(infos)} 条")
            report.append("")
            
            if errors:
                report.append("### 错误")
                for issue in errors:
                    report.append(f"- [{issue['time']}] {issue['message']}")
                report.append("")
            
            if warnings:
                report.append("### 警告")
                for issue in warnings:
                    report.append(f"- [{issue['time']}] {issue['message']}")
                report.append("")
        
        # 系统状态
        report.append("## 📊 系统状态")
        report.append("")
        report.append("| 组件 | 状态 |")
        report.append("|------|------|")
        report.append(f"| Web 服务 | {'✅' if self.data.get('web_service') == 'OK' else '❌'} {self.data.get('web_service', 'UNKNOWN')} |")
        report.append(f"| 账户余额 | {'✅' if self.data.get('account_balance') else '❌'} {self.data.get('account_balance', 'N/A')} USDT |")
        report.append(f"| 当前持仓 | {'✅' if 'positions' in self.data else '❌'} {self.data.get('positions_count', 0)} 个 |")
        report.append(f"| 活跃策略 | {'✅' if 'strategies' in self.data else '❌'} {self.data.get('active_strategies_count', 0)} 个 |")
        report.append(f"| 止损单 | {'✅' if 'stop_loss_count' in self.data else '❌'} {self.data.get('stop_loss_count', 0)} 个 |")
        report.append(f"| 错误检测 | {'✅' if self.data.get('error_detection') == 'OK' else '⚠️'} {self.data.get('error_detection', 'UNKNOWN')} |")
        report.append("")
        
        # 持仓详情
        if self.data.get('positions'):
            report.append("## 📈 持仓详情")
            report.append("")
            for pos in self.data['positions']:
                report.append(f"- **{pos['symbol']}** {pos['side']} {pos['size']} @ {pos['entry_price']} (未实现盈亏：{pos.get('unrealized_pnl', 'N/A')})")
            report.append("")
        
        # 策略详情
        if self.data.get('strategies'):
            report.append("## 🤖 策略详情")
            report.append("")
            for s in self.data['strategies']:
                report.append(f"- **{s['symbol']}**: RSI={s.get('rsi', 0):.2f}, 持仓={s.get('position') or '无'}, 状态={s.get('status', 'N/A')}")
            report.append("")
        
        # 最新交易
        if self.data.get('recent_trades'):
            report.append("## 💰 最新交易")
            report.append("")
            for t in self.data['recent_trades'][:3]:
                report.append(f"- {t.get('trade_time', 'N/A')}: {t['symbol']} {t['side']} **{t.get('order_type', 'N/A')}** @ {t['price']}")
            report.append("")
        
        # 结论
        report.append("## ✅ 结论")
        report.append("")
        
        error_count = len([i for i in self.issues if i['level'] == 'ERROR'])
        if error_count == 0:
            report.append("✅ **系统运行正常，无需干预！**")
        else:
            report.append(f"❌ **发现 {error_count} 个错误，需要立即处理！**")
        
        report.append("")
        report.append("---")
        report.append("")
        report.append("*下次检查：30 分钟后*")
        
        return "\n".join(report)
    
    def save_report(self):
        """保存报告到文件"""
        report = self.generate_report()
        filename = f"v3_monitor_{self.timestamp.strftime('%Y-%m-%d_%H-%M')}.md"
        filepath = os.path.join(MONITOR_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 同时更新最新报告
        latest_path = os.path.join(MONITOR_DIR, "LATEST.md")
        with open(latest_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存 JSON 数据
        json_path = os.path.join(MONITOR_DIR, f"v3_monitor_{self.timestamp.strftime('%Y-%m-%d_%H-%M')}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': self.timestamp.isoformat(),
                'issues': self.issues,
                'data': self.data
            }, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def run_all_checks(self):
        """运行所有检查"""
        print(f"\n🔍 v3 系统监测开始 - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        self.check_web_service()
        self.check_account()
        self.check_positions()
        self.check_trades()
        self.check_strategy_status()
        self.check_stop_loss()
        self.check_error_detection()
        
        # 保存报告
        filepath = self.save_report()
        
        # 输出摘要
        print(f"\n📊 监测完成！")
        print(f"  - Web 服务：{self.data.get('web_service', 'UNKNOWN')}")
        print(f"  - 账户余额：{self.data.get('account_balance', 'N/A')} USDT")
        print(f"  - 当前持仓：{self.data.get('positions_count', 0)} 个")
        print(f"  - 活跃策略：{self.data.get('active_strategies_count', 0)} 个")
        print(f"  - 发现问题：{len(self.issues)} 个")
        print(f"\n📄 报告已保存：{filepath}")
        print("="*60)
        
        # 如果有严重问题，打印警告
        errors = [i for i in self.issues if i['level'] == 'ERROR']
        if errors:
            print("\n❌ 发现严重错误，需要立即处理:")
            for e in errors:
                print(f"  - [{e['time']}] {e['message']}")
        
        return len(errors) == 0


if __name__ == "__main__":
    monitor = V3Monitor()
    success = monitor.run_all_checks()
    
    # 返回退出码（0=正常，1=有错误）
    exit(0 if success else 1)
