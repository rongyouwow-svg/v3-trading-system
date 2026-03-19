#!/usr/bin/env python3
"""
🦞 仓位计算器

功能:
    - 根据投资金额和杠杆计算开仓数量
    - 考虑交易精度
    - 严格控制在策略配置范围内
"""

from decimal import Decimal, ROUND_DOWN
from typing import Dict


class PositionCalculator:
    """仓位计算器"""
    
    def __init__(self, connector=None):
        """
        初始化计算器
        
        Args:
            connector: 币安连接器（用于获取精度）
        """
        self.connector = connector
    
    def calculate_position_size(
        self,
        amount_usd: Decimal,
        leverage: int,
        price: Decimal,
        symbol: str
    ) -> Decimal:
        """
        计算开仓数量
        
        Args:
            amount_usd: 投资金额 (USDT)
            leverage: 杠杆倍数
            price: 当前价格
            symbol: 币种名称
            
        Returns:
            Decimal: 开仓数量（币种单位）
        """
        # 计算仓位价值
        position_value = amount_usd * leverage
        
        # 计算理论数量
        quantity = position_value / price
        
        # 应用精度限制
        quantity = self._apply_precision(quantity, symbol)
        
        return quantity
    
    def calculate_position_value(
        self,
        quantity: Decimal,
        price: Decimal,
        leverage: int
    ) -> Decimal:
        """
        计算仓位价值
        
        Args:
            quantity: 数量
            price: 价格
            leverage: 杠杆
            
        Returns:
            Decimal: 仓位价值 (USDT)
        """
        return quantity * price
    
    def calculate_required_margin(
        self,
        quantity: Decimal,
        price: Decimal,
        leverage: int
    ) -> Decimal:
        """
        计算所需保证金
        
        Args:
            quantity: 数量
            price: 价格
            leverage: 杠杆
            
        Returns:
            Decimal: 保证金 (USDT)
        """
        position_value = quantity * price
        margin = position_value / leverage
        return margin
    
    def _apply_precision(self, quantity: Decimal, symbol: str) -> Decimal:
        """
        应用精度限制
        
        Args:
            quantity: 理论数量
            symbol: 币种名称
            
        Returns:
            Decimal: 精确后的数量
        """
        # 默认精度
        precision = 3
        
        # 从连接器获取精度（如果有）
        if self.connector:
            precision = self.connector.get_quantity_precision(symbol)
        
        # 向下取整到指定精度
        quantize_str = '0.' + '0' * precision
        return quantity.quantize(Decimal(quantize_str), rounding=ROUND_DOWN)
    
    def validate_position(
        self,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        leverage: int,
        max_position_usd: Decimal
    ) -> Dict:
        """
        验证仓位是否合规
        
        Args:
            symbol: 币种
            quantity: 数量
            price: 价格
            leverage: 杠杆
            max_position_usd: 最大仓位限制
            
        Returns:
            dict: 验证结果
        """
        position_value = self.calculate_position_value(quantity, price, leverage)
        margin = self.calculate_required_margin(quantity, price, leverage)
        
        result = {
            'valid': True,
            'position_value': position_value,
            'margin': margin,
            'leverage': leverage,
            'warnings': []
        }
        
        # 检查是否超过最大仓位
        if position_value > max_position_usd:
            result['valid'] = False
            result['warnings'].append(
                f"仓位价值 {position_value:.2f} USDT 超过限制 {max_position_usd:.2f} USDT"
            )
        
        # 检查杠杆是否过高
        if leverage > 20:
            result['warnings'].append(f"高杠杆 {leverage}x，注意风险")
        
        return result


# 全局单例
_calculator = None

def get_calculator(connector=None) -> PositionCalculator:
    """获取计算器单例"""
    global _calculator
    if _calculator is None:
        _calculator = PositionCalculator(connector)
    return _calculator


def calculate_position(
    amount_usd: float,
    leverage: int,
    price: float,
    symbol: str
) -> float:
    """
    便捷函数：计算开仓数量
    
    Args:
        amount_usd: 投资金额
        leverage: 杠杆
        price: 价格
        symbol: 币种
        
    Returns:
        float: 开仓数量
    """
    calc = get_calculator()
    result = calc.calculate_position_size(
        Decimal(str(amount_usd)),
        leverage,
        Decimal(str(price)),
        symbol
    )
    return float(result)


if __name__ == "__main__":
    # 测试
    calc = PositionCalculator()
    
    print("=== 测试仓位计算器 ===\n")
    
    # 测试配置
    test_cases = [
        {'symbol': 'ETHUSDT', 'amount': 300, 'leverage': 3, 'price': 2275},
        {'symbol': 'UNIUSDT', 'amount': 200, 'leverage': 5, 'price': 7.5},
        {'symbol': 'AVAXUSDT', 'amount': 250, 'leverage': 8, 'price': 10.0},
    ]
    
    for test in test_cases:
        quantity = calc.calculate_position_size(
            Decimal(str(test['amount'])),
            test['leverage'],
            Decimal(str(test['price'])),
            test['symbol']
        )
        
        position_value = Decimal(str(test['amount'])) * test['leverage']
        margin = Decimal(str(test['amount']))
        
        print(f"{test['symbol']}:")
        print(f"  投资金额：{test['amount']} USDT")
        print(f"  杠杆倍数：{test['leverage']}x")
        print(f"  当前价格：${test['price']}")
        print(f"  仓位价值：{position_value} USDT")
        print(f"  开仓数量：{quantity}")
        print(f"  所需保证金：{margin} USDT")
        print()
