#!/usr/bin/env python3
"""
🔍 错误自动检测和修复机制

功能:
- 自动检测 API 错误
- 自动记录错误日志
- 自动尝试修复
- 发送错误报告
"""

import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List

LOG_FILE = "/home/admin/.openclaw/workspace/quant/v3-architecture/logs/error_detection.log"
ERROR_REPORT_FILE = "/home/admin/.openclaw/workspace/quant/v3-architecture/logs/error_report.json"

class ErrorDetector:
    """错误检测器"""
    
    def __init__(self):
        self.api_base = "http://localhost:3000"
        self.errors = []
        self.load_errors()
    
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except Exception as e:
            print(f"❌ 日志写入失败：{e}")
    
    def load_errors(self):
        """加载错误记录"""
        try:
            with open(ERROR_REPORT_FILE, 'r', encoding='utf-8') as f:
                self.errors = json.load(f)
        except:
            self.errors = []
    
    def save_errors(self):
        """保存错误记录"""
        try:
            with open(ERROR_REPORT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"❌ 错误记录保存失败：{e}")
    
    def check_api(self, endpoint: str, expected_status: str = "success") -> bool:
        """检查 API 是否正常"""
        try:
            response = requests.get(f"{self.api_base}{endpoint}", timeout=5)
            data = response.json()
            
            if data.get('success') or data.get('status') == 'ok':
                self.log(f"✅ {endpoint} 正常")
                return True
            else:
                error_msg = f"❌ {endpoint} 异常：{data}"
                self.log(error_msg)
                self.add_error(endpoint, error_msg)
                return False
        except Exception as e:
            error_msg = f"❌ {endpoint} 错误：{e}"
            self.log(error_msg)
            self.add_error(endpoint, error_msg)
            return False
    
    def add_error(self, endpoint: str, error_msg: str):
        """添加错误记录"""
        self.errors.append({
            'time': datetime.now().isoformat(),
            'endpoint': endpoint,
            'error': error_msg,
            'fixed': False
        })
        self.save_errors()
    
    def check_all_apis(self):
        """检查所有 API"""
        self.log("\n" + "="*60)
        self.log("🔍 开始 API 健康检查")
        self.log("="*60)
        
        apis = [
            '/api/binance/klines?symbol=ETHUSDT&interval=1m&limit=1',
            '/api/binance/account-info',
            '/api/strategy/active',
            '/api/trades/refresh?symbol=ETHUSDT&limit=1'
        ]
        
        results = {}
        for api in apis:
            results[api] = self.check_api(api)
        
        # 生成报告
        self.generate_report(results)
        
        # 尝试修复
        self.try_fix()
        
        return all(results.values())
    
    def generate_report(self, results: Dict):
        """生成检查报告"""
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        
        self.log(f"\n📊 检查结果：{passed}/{total} 通过")
        
        for api, result in results.items():
            status = "✅" if result else "❌"
            self.log(f"  {status} {api}")
    
    def try_fix(self):
        """尝试修复错误"""
        self.log("\n🔧 开始尝试修复")
        
        fixed_count = 0
        for error in self.errors:
            if not error.get('fixed'):
                if self.fix_error(error):
                    error['fixed'] = True
                    fixed_count += 1
        
        self.save_errors()
        self.log(f"✅ 修复了 {fixed_count} 个错误")
    
    def fix_error(self, error: Dict) -> bool:
        """修复错误"""
        endpoint = error.get('endpoint', '')
        
        # 检测常见错误并尝试修复
        if 'datetime' in error.get('error', '') and 'not defined' in error.get('error', ''):
            self.log(f"🔧 检测到导入错误，尝试修复...")
            return self.fix_import_error(endpoint, 'datetime')
        
        return False
    
    def fix_import_error(self, endpoint: str, module: str) -> bool:
        """修复导入错误"""
        try:
            # 找到对应的文件
            file_path = self.get_file_from_endpoint(endpoint)
            if not file_path:
                return False
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已导入
            if f'from {module} import' in content or f'import {module}' in content:
                self.log(f"✅ {module} 已导入")
                return True
            
            # 添加导入
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    continue
                else:
                    # 在最后一个导入后添加
                    lines.insert(i, f'import {module}')
                    break
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            self.log(f"✅ 已添加 import {module} 到 {file_path}")
            
            # 重启服务
            self.restart_service()
            
            return True
        except Exception as e:
            self.log(f"❌ 修复失败：{e}")
            return False
    
    def get_file_from_endpoint(self, endpoint: str) -> str:
        """从端点获取文件路径"""
        if 'trades' in endpoint:
            return '/home/admin/.openclaw/workspace/quant/v3-architecture/strategies/trades_refresh_api.py'
        elif 'strategy' in endpoint:
            return '/home/admin/.openclaw/workspace/quant/v3-architecture/strategies/strategy_status_api.py'
        return ''
    
    def restart_service(self):
        """重启服务"""
        try:
            self.log("🔄 重启 Web 服务...")
            os.system("pkill -f 'uvicorn web.dashboard_api:app'")
            time.sleep(2)
            os.system("cd /home/admin/.openclaw/workspace/quant/v3-architecture && nohup uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000 > logs/web_dashboard.log 2>&1 &")
            time.sleep(5)
            self.log("✅ Web 服务已重启")
        except Exception as e:
            self.log(f"❌ 重启失败：{e}")
    
    def run(self, interval: int = 300):
        """运行错误检测（默认 5 分钟一次）"""
        self.log(f"\n🚀 错误检测启动（间隔：{interval}秒）")
        
        while True:
            try:
                self.check_all_apis()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.log("\n🛑 错误检测停止")
                break
            except Exception as e:
                self.log(f"❌ 检测异常：{e}")
                time.sleep(interval)


if __name__ == "__main__":
    detector = ErrorDetector()
    
    # 立即检查一次
    detector.check_all_apis()
    
    # 持续监控
    # detector.run(interval=300)  # 5 分钟一次
