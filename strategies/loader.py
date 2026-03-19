#!/usr/bin/env python3
"""
🦞 策略加载器 v2.0
支持热插拔的动态导入机制（参考 Freqtrade/OctoBot 设计）

核心特性：
1. 动态扫描 strategies/ 文件夹
2. 自动识别继承 BaseStrategy 的类
3. 支持运行时热插拔（添加新策略无需重启）
4. 模块缓存管理（避免重复加载）
5. 详细的错误日志和诊断信息
"""

import os
import sys
import importlib
import importlib.util
from datetime import datetime
from typing import Dict, List, Optional, Type


class StrategyLoader:
    """策略加载器 - 支持热插拔"""
    
    # 策略文件缓存（避免重复扫描）
    _file_cache: Dict[str, float] = {}  # {filename: mtime}
    _module_cache: Dict[str, object] = {}  # {module_name: module}
    
    def __init__(self, strategies_folder: Optional[str] = None):
        """
        初始化加载器
        
        Args:
            strategies_folder: 策略文件夹路径（默认当前文件所在目录）
        """
        if strategies_folder is None:
            strategies_folder = os.path.dirname(os.path.abspath(__file__))
        
        self.folder = strategies_folder
        self.strategies: Dict[str, Type] = {}  # {strategy_id: StrategyClass}
        self.last_reload: Optional[datetime] = None
        self._base_strategy_class: Optional[Type] = None
    
    def _get_base_strategy(self) -> Type:
        """获取策略基类（带缓存）"""
        if self._base_strategy_class is None:
            try:
                from strategies.base_strategy import BaseStrategy
                self._base_strategy_class = BaseStrategy
            except ImportError as e:
                # 尝试多种导入路径
                sys.path.insert(0, os.path.dirname(self.folder))
                try:
                    from strategies.base_strategy import BaseStrategy
                    self._base_strategy_class = BaseStrategy
                except ImportError:
                    raise ImportError(f"无法导入 BaseStrategy: {e}")
        
        return self._base_strategy_class
    
    def _is_strategy_class(self, obj) -> bool:
        """检查是否是有效的策略类"""
        try:
            BaseStrategy = self._get_base_strategy()
            return (
                isinstance(obj, type) and
                issubclass(obj, BaseStrategy) and
                obj.__name__ != 'BaseStrategy'
            )
        except Exception:
            return False
    
    def _file_has_changed(self, filename: str) -> bool:
        """检查文件是否发生变化（用于热插拔）"""
        filepath = os.path.join(self.folder, filename)
        if not os.path.exists(filepath):
            return False
        
        current_mtime = os.path.getmtime(filepath)
        cached_mtime = self._file_cache.get(filename)
        
        if cached_mtime is None or current_mtime != cached_mtime:
            self._file_cache[filename] = current_mtime
            return True
        
        return False
    
    def reload(self, force: bool = False) -> Dict[str, Type]:
        """
        重新加载所有策略（热插拔核心）
        
        Args:
            force: 强制重新加载（忽略缓存）
        
        Returns:
            策略字典 {strategy_id: StrategyClass}
        """
        if force:
            self._file_cache.clear()
            self._module_cache.clear()
        
        old_strategies = self.strategies.copy()
        self.strategies = {}
        self.strategy_aliases = {}  # {alias: primary_id} 新增：别名映射
        new_count = 0
        unchanged_count = 0
        
        # 扫描策略文件夹
        try:
            files = os.listdir(self.folder)
        except OSError as e:
            print(f"❌ 无法读取策略文件夹 {self.folder}: {e}")
            return old_strategies
        
        for filename in files:
            # 只加载 .py 文件，跳过 _ 开头的文件和特殊文件
            if not (filename.endswith('.py') and not filename.startswith('_')):
                continue
            
            # 跳过已知不变的文件（热插拔优化）
            if not force and not self._file_has_changed(filename):
                unchanged_count += 1
                continue
            
            module_name = filename[:-3]  # 去掉 .py
            module_path = os.path.join(self.folder, filename)
            
            try:
                # 检查模块是否已缓存
                if module_name in self._module_cache and not force:
                    # 从缓存加载
                    module = self._module_cache[module_name]
                else:
                    # 动态导入模块
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if not spec or not spec.loader:
                        print(f"⚠️ 无法加载模块 {filename}: spec 为空")
                        continue
                    
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module  # 注册到 sys.modules
                    spec.loader.exec_module(module)
                    self._module_cache[module_name] = module
                
                # 找到模块中的策略类
                for name in dir(module):
                    obj = getattr(module, name)
                    
                    if self._is_strategy_class(obj):
                        # 使用类名作为策略 ID（小写）- 这是主 ID
                        primary_id = obj.__name__.lower()
                        self.strategies[primary_id] = obj
                        new_count += 1
                        
                        # 生成别名（支持多种命名风格）
                        alias = self._camel_to_snake(obj.__name__)
                        if alias != primary_id:
                            # 存储别名映射（不直接存储策略类，避免重复）
                            self.strategy_aliases[alias] = primary_id
                            print(f"   ↳ 别名：{alias} → {primary_id}")
                
            except Exception as e:
                print(f"❌ 加载策略失败 {filename}: {e}")
                import traceback
                traceback.print_exc()
        
        self.last_reload = datetime.now()
        
        # 打印加载结果
        if new_count > 0:
            print(f"✅ 策略加载完成：{new_count} 个策略 (缓存命中：{unchanged_count}, 别名：{len(self.strategy_aliases)})")
        else:
            print(f"ℹ️  策略无变化 (缓存命中：{unchanged_count})")
        
        return self.strategies
    
    def _camel_to_snake(self, name: str) -> str:
        """将驼峰命名转换为蛇形命名"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def get_strategy(self, strategy_id: str) -> Optional[Type]:
        """
        获取策略类（如果不存在则重新加载）
        
        Args:
            strategy_id: 策略 ID（可以是主 ID 或别名）
        
        Returns:
            策略类
        """
        # 直接查找（主 ID）
        if strategy_id in self.strategies:
            return self.strategies[strategy_id]
        
        # 查找别名映射
        if strategy_id in self.strategy_aliases:
            primary_id = self.strategy_aliases[strategy_id]
            print(f"✅ 找到别名映射：{strategy_id} → {primary_id}")
            return self.strategies.get(primary_id)
        
        # 尝试重新加载
        print(f"🔄 策略 '{strategy_id}' 不存在，重新加载...")
        self.reload()
        
        # 再次查找主 ID
        if strategy_id in self.strategies:
            return self.strategies[strategy_id]
        
        # 再次查找别名
        if strategy_id in self.strategy_aliases:
            primary_id = self.strategy_aliases[strategy_id]
            print(f"✅ 找到别名映射：{strategy_id} → {primary_id}")
            return self.strategies.get(primary_id)
        
        # 尝试模糊匹配（去掉下划线）
        normalized_id = strategy_id.replace('_', '').lower()
        for sid, sclass in self.strategies.items():
            if sid.replace('_', '').lower() == normalized_id:
                print(f"✅ 找到模糊匹配：{strategy_id} → {sid}")
                return sclass
        
        return None
    
    def list_strategies(self) -> List[Dict]:
        """
        获取策略列表（只返回主策略，不返回别名）
        
        Returns:
            策略信息列表
        """
        if not self.strategies:
            self.reload()
        
        strategies = []
        for strategy_id, strategy_class in sorted(self.strategies.items()):
            # 只返回主策略（strategy_id 就是类名小写）
            # 别名不会出现在 strategies 字典中，只存在于 strategy_aliases
            strategies.append({
                'id': strategy_id,
                'name': strategy_class.__name__,
                'description': getattr(strategy_class, '__doc__', '自动交易策略').strip().split('\n')[0],
                'module': strategy_class.__module__,
                'file': f"{strategy_class.__module__}.py"
            })
        
        return strategies
    
    def get_strategy_info(self, strategy_id: str) -> Optional[Dict]:
        """获取策略详细信息"""
        strategy_class = self.get_strategy(strategy_id)
        if strategy_class is None:
            return None
        
        return {
            'id': strategy_id,
            'name': strategy_class.__name__,
            'description': getattr(strategy_class, '__doc__', '自动交易策略'),
            'module': strategy_class.__module__,
            'file': f"{strategy_class.__module__}.py",
            'last_reload': self.last_reload.isoformat() if self.last_reload else None
        }


# 全局加载器实例（单例模式）
_loader: Optional[StrategyLoader] = None

def get_loader() -> StrategyLoader:
    """获取全局加载器实例（单例模式）"""
    global _loader
    if _loader is None:
        _loader = StrategyLoader()
    return _loader

def reload_all_strategies() -> Dict[str, Type]:
    """便捷函数：强制重新加载所有策略"""
    loader = get_loader()
    return loader.reload(force=True)
