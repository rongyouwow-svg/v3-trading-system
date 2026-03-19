# 🦞 策略插件注册

"""
策略注册机制（动态热插拔 v2.0）：
1. 所有策略文件放在 strategies/ 文件夹
2. 策略类必须继承 BaseStrategy
3. 策略类名必须与文件名一致（驼峰命名）
4. 网关启动时自动扫描并注册所有策略
5. 支持运行时热插拔（添加新策略无需重启）

策略命名规范：
- 文件名：snake_case (如 rsi_1min_reversal.py)
- 类名：PascalCase (如 Rsi1minReversal)
- 策略 ID：小写无下划线 (如 rsi1minreversal)
"""

from strategies.loader import get_loader

# 动态获取策略注册表（只读引用）
def _get_available_strategies():
    """获取可用策略字典（动态加载）"""
    loader = get_loader()
    return loader.strategies

# 兼容旧代码的 AVAILABLE_STRATEGIES（动态属性）
class _AvailableStrategiesProxy:
    """AVAILABLE_STRATEGIES 代理类（保持向后兼容）"""
    
    def __getitem__(self, key):
        loader = get_loader()
        if key not in loader.strategies:
            # 尝试别名映射
            if key in loader.strategy_aliases:
                key = loader.strategy_aliases[key]
            else:
                loader.reload()
        return loader.strategies.get(key)
    
    def __contains__(self, key):
        loader = get_loader()
        return key in loader.strategies or key in loader.strategy_aliases
    
    def get(self, key, default=None):
        loader = get_loader()
        if key in loader.strategies:
            return loader.strategies[key]
        if key in loader.strategy_aliases:
            return loader.strategies.get(loader.strategy_aliases[key], default)
        loader.reload()
        if key in loader.strategies:
            return loader.strategies[key]
        if key in loader.strategy_aliases:
            return loader.strategies.get(loader.strategy_aliases[key], default)
        return default
    
    def keys(self):
        loader = get_loader()
        # 返回主 ID + 别名（保持向后兼容）
        all_keys = set(loader.strategies.keys())
        all_keys.update(loader.strategy_aliases.keys())
        return all_keys
    
    def items(self):
        loader = get_loader()
        # 返回所有主策略和别名的映射
        result = {}
        for key, value in loader.strategies.items():
            result[key] = value
        for alias, primary_id in loader.strategy_aliases.items():
            result[alias] = loader.strategies[primary_id]
        return result.items()
    
    def __repr__(self):
        loader = get_loader()
        all_keys = list(loader.strategies.keys()) + list(loader.strategy_aliases.keys())
        return f"AvailableStrategies({all_keys})"

# 动态策略注册表（代理对象）
AVAILABLE_STRATEGIES = _AvailableStrategiesProxy()

# 策略注册表（动态生成，保持向后兼容）
def _build_strategy_registry():
    """构建策略注册表（包含所有别名）"""
    loader = get_loader()
    strategies = loader.strategies.copy()
    
    # 添加别名（兼容旧代码）
    aliases = {
        'test_strategy': 'teststrategy',
        'auto_sim': 'autosimstrategy',
        'stop_loss_test': 'stoplossteststrategy',
        'rsi_1min_reversal': 'rsi1minreversal',
    }
    
    for alias, real_id in aliases.items():
        if real_id in strategies:
            strategies[alias] = strategies[real_id]
    
    return strategies

def load_strategy(strategy_id: str, gateway, symbol: str, leverage: int, amount: float):
    """
    加载策略实例（动态加载）
    
    Args:
        strategy_id: 策略 ID
        gateway: 网关包装器
        symbol: 交易对
        leverage: 杠杆
        amount: 保证金
    
    Returns:
        策略实例
    """
    loader = get_loader()
    strategy_class = loader.get_strategy(strategy_id)
    
    if strategy_class is None:
        # 尝试重新加载
        loader.reload()
        strategy_class = loader.get_strategy(strategy_id)
    
    if strategy_class is None:
        raise ValueError(f"未知策略：{strategy_id} (可用策略：{list(loader.strategies.keys())})")
    
    return strategy_class(gateway, symbol, leverage, amount)

def get_strategy_list() -> list:
    """获取可用策略列表（动态加载）"""
    loader = get_loader()
    return loader.list_strategies()

def reload_strategies():
    """手动触发策略重新加载（热插拔 API）"""
    loader = get_loader()
    return loader.reload()

# 初始化时打印策略列表
def _print_loaded_strategies():
    """打印已加载的策略列表"""
    loader = get_loader()
    strategies = loader.strategies
    print(f"\n🦞 策略注册表初始化完成")
    print(f"✅ 已加载 {len(strategies)} 个策略:")
    for strategy_id in sorted(strategies.keys()):
        print(f"   - {strategy_id}")
    print()

# 延迟加载（避免循环导入）
import atexit
atexit.register(_print_loaded_strategies)
