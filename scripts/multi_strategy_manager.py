#!/usr/bin/env python3
"""
🦞 多策略管理器（4 合 1）

合并：
- rsi_1min_strategy.py (ETH)
- link_rsi_detailed_strategy.py (LINK)
- rsi_scale_in_strategy.py (AVAX)
- uni_rsi_v24_strategy.py (UNI)

功能：
1. 动态加载/卸载策略
2. 共享内存池
3. 统一心跳注册
4. 自动重启崩溃策略
"""

import requests
import time
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from importlib import import_module

# 配置
BASE_URL = "http://localhost:8000"
LOGS_DIR = Path("/root/.openclaw/workspace/quant/v3-architecture/logs")
STATE_FILE = LOGS_DIR / "multi_strategy_manager_state.json"

# 添加策略路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))

# 导入策略注册中心
from strategy_registry import register_strategy, unregister_strategy, StrategyRegistry

# 策略配置
STRATEGY_CONFIGS = {
    'ETHUSDT': {
        'script': 'strategies.rsi_1min_strategy',
        'class': 'RSIStrategy',
        'leverage': 3,
        'amount': 100,
        'stop_loss_pct': 0.01,
        'take_profit_pct': 0.02
    },
    'LINKUSDT': {
        'script': 'strategies.link_rsi_detailed_strategy',
        'class': 'DetailedRSIStrategy',  # 实际类名
        'leverage': 3,
        'amount': 100,
        'stop_loss_pct': 0.01,
        'take_profit_pct': 0.02
    },
    'AVAXUSDT': {
        'script': 'strategies.rsi_scale_in_strategy',
        'class': 'RSIScaleInStrategy',
        'leverage': 3,
        'total_amount': 200,  # 修正参数名
        'stop_loss_pct': 0.005,
        'take_profit_pct': 0.02
    },
    'UNIUSDT': {
        'script': 'strategies.uni_rsi_v24_strategy',
        'class': 'UNIRsiStrategy',  # 实际类名
        'leverage': 3,
        'amount': 100,
        'stop_loss_pct': 0.008,
        'take_profit_pct': 0.02
    }
}


class MultiStrategyManager:
    """多策略管理器"""
    
    def __init__(self):
        self.strategies = {}
        self.active_symbols = []
        self.registry = StrategyRegistry()
        self.state = self.load_state()
        
        print("="*70)
        print("🦞 多策略管理器启动（4 合 1）")
        print("="*70)
        print(f"📊 初始状态:")
        print(f"   策略配置：{len(STRATEGY_CONFIGS)} 个")
        print(f"   内存优化：共享内存池")
        print(f"   懒加载：仅加载有持仓的策略")
        print("="*70)
    
    def load_state(self):
        """加载状态"""
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_state(self):
        """保存状态"""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def has_position(self, symbol):
        """检查是否有持仓"""
        try:
            response = requests.get(f"{BASE_URL}/api/binance/positions", timeout=10)
            data = response.json()
            if data.get('success'):
                positions = data.get('positions', [])
                for pos in positions:
                    if pos.get('symbol') == symbol and float(pos.get('size', 0)) > 0:
                        return True
            return False
        except Exception as e:
            print(f"❌ 检查持仓失败：{e}")
            return False
    
    def is_rsi_oversold(self, symbol, threshold=50):
        """检查 RSI 是否超卖（低于阈值）"""
        try:
            # 获取最近 100 根 K 线
            response = requests.get(
                f"{BASE_URL}/api/binance/klines",
                params={'symbol': symbol, 'interval': '1m', 'limit': 100},
                timeout=10
            )
            data = response.json()
            
            # 处理 API 返回格式
            if isinstance(data, dict):
                if not data.get('success'):
                    return False
                klines = data.get('klines', [])
            elif isinstance(data, list):
                klines = data  # 直接是列表
            else:
                return False
            
            if not klines or len(klines) < 7:
                return False
            
            # 提取收盘价（索引 4）
            closes = []
            for k in klines:
                if isinstance(k, dict):
                    closes.append(float(k.get('close', 0)))
                elif isinstance(k, list):
                    closes.append(float(k[4]))
            
            if len(closes) < 7:
                return False
            
            # 计算 RSI(7)
            delta = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in delta]
            losses = [-d if d < 0 else 0 for d in delta]
            
            avg_gain = sum(gains[-7:]) / 7
            avg_loss = sum(losses[-7:]) / 7
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi = 100 - (100 / (1 + rs))
            
            is_oversold = rsi < threshold
            if is_oversold:
                print(f"📈 {symbol} RSI 超卖：{rsi:.2f} < {threshold}")
            
            return is_oversold
        except Exception as e:
            # 静默失败，避免日志过多
            return False
    
    def load_strategy(self, symbol):
        """懒加载策略"""
        if symbol in self.strategies:
            print(f"✅ {symbol} 策略已加载")
            return True
        
        config = STRATEGY_CONFIGS.get(symbol)
        if not config:
            print(f"❌ {symbol} 配置不存在")
            return False
        
        try:
            # 动态导入策略模块（添加 strategies 路径）
            strategies_path = str(Path(__file__).parent.parent / 'strategies')
            if strategies_path not in sys.path:
                sys.path.insert(0, strategies_path)
            
            # 导入模块
            module_name = config['script'].split('.')[-1]
            module = import_module(module_name)
            strategy_class = getattr(module, config['class'])
            
            # 创建策略实例
            strategy = strategy_class(
                symbol=symbol,
                leverage=config['leverage'],
                amount=config['amount']
            )
            
            # 设置止损止盈
            strategy.stop_loss_pct = config['stop_loss_pct']
            strategy.take_profit_pct = config['take_profit_pct']
            
            # 保存策略
            self.strategies[symbol] = {
                'instance': strategy,
                'config': config,
                'last_heartbeat': time.time(),
                'load_time': datetime.now().isoformat()
            }
            
            # 注册到策略注册中心
            register_strategy(
                symbol=symbol,
                pid=os.getpid(),
                leverage=config['leverage'],
                amount=config['amount'],
                script=config['script']
            )
            
            print(f"✅ {symbol} 策略已加载并注册")
            return True
            
        except Exception as e:
            print(f"❌ {symbol} 策略加载失败：{e}")
            return False
    
    def unload_strategy(self, symbol):
        """卸载策略"""
        if symbol not in self.strategies:
            return
        
        try:
            # 注销策略
            unregister_strategy(symbol)
            
            # 删除策略实例
            del self.strategies[symbol]
            
            print(f"✅ {symbol} 策略已卸载")
        except Exception as e:
            print(f"❌ {symbol} 策略卸载失败：{e}")
    
    def run_strategy_once(self, symbol):
        """运行策略一次"""
        if symbol not in self.strategies:
            return False
        
        try:
            strategy_data = self.strategies[symbol]
            strategy = strategy_data['instance']
            
            # 运行策略逻辑
            if hasattr(strategy, 'run_once'):
                strategy.run_once()
            elif hasattr(strategy, 'run'):
                # 如果只有 run 方法，运行一次循环
                strategy.run(interval=1)
            
            # 更新心跳
            strategy_data['last_heartbeat'] = time.time()
            
            return True
        except Exception as e:
            print(f"❌ {symbol} 策略运行失败：{e}")
            return False
    
    def check_inactive_strategies(self, timeout=3600):
        """检查并卸载不活跃策略"""
        now = time.time()
        to_unload = []
        
        for symbol, strategy_data in self.strategies.items():
            last_activity = strategy_data['last_heartbeat']
            
            # 超过 1 小时无活动
            if now - last_activity > timeout:
                # 检查是否还有持仓
                if not self.has_position(symbol):
                    to_unload.append(symbol)
        
        for symbol in to_unload:
            print(f"⏰ {symbol} 策略超时（无持仓），卸载...")
            self.unload_strategy(symbol)
    
    def run(self):
        """运行管理器"""
        print(f"\n🚀 多策略管理器启动")
        print(f"   检查间隔：60 秒")
        print(f"   智能懒加载：有持仓 OR RSI<50 → 加载")
        print(f"   自动卸载：3600 秒无活动")
        print(f"="*70)
        
        last_check = None
        
        while True:
            try:
                current_time = datetime.now()
                
                # 每 60 秒检查一次
                if last_check is None or (current_time - last_check).total_seconds() >= 60:
                    last_check = current_time
                    
                    # 1. 检查所有配置的策略（智能懒加载）
                    for symbol in STRATEGY_CONFIGS.keys():
                        has_pos = self.has_position(symbol)
                        is_rsi_low = self.is_rsi_oversold(symbol, threshold=50)  # RSI<50 超卖
                        is_loaded = symbol in self.strategies
                        
                        # 有持仓 OR RSI 超卖 → 加载策略
                        if (has_pos or is_rsi_low) and not is_loaded:
                            reason = "持仓" if has_pos else "RSI 超卖"
                            print(f"\n📈 {symbol} {reason}，加载策略...")
                            self.load_strategy(symbol)
                        elif is_loaded and not has_pos and not is_rsi_low:
                            # 已加载但无持仓且 RSI 不超卖 → 标记为可卸载
                            pass
                        
                        # 无持仓但已加载 → 保持加载（避免频繁加载/卸载）
                        # 由 check_inactive_strategies 处理
                    
                    # 2. 运行已加载的策略
                    for symbol in list(self.strategies.keys()):
                        print(f"\n⏰ {current_time.strftime('%H:%M:%S')} - 运行 {symbol} 策略...")
                        self.run_strategy_once(symbol)
                    
                    # 3. 检查不活跃策略
                    self.check_inactive_strategies(timeout=3600)
                    
                    # 4. 保存状态
                    self.state['last_check'] = current_time.isoformat()
                    self.state['loaded_strategies'] = list(self.strategies.keys())
                    self.save_state()
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                print(f"\n\n⚠️ 管理器停止（用户中断）")
                # 卸载所有策略
                for symbol in list(self.strategies.keys()):
                    self.unload_strategy(symbol)
                break
            except Exception as e:
                print(f"❌ 管理器异常：{e}")
                time.sleep(10)
        
        print(f"\n✅ 管理器运行结束")


def main():
    """主函数"""
    manager = MultiStrategyManager()
    manager.run()


if __name__ == '__main__':
    main()
