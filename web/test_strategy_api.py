#!/usr/bin/env python3
"""
🦞 测试策略 API

用于测试策略执行、止损单跟随、平仓等功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

router = APIRouter(prefix="/api/test-strategy", tags=["测试策略"])


class TestStrategyConfig(BaseModel):
    """测试策略配置"""
    symbol: str
    leverage: int = 5
    amount: float = 100
    use_stop_loss: bool = True
    stop_loss_pct: float = 5.0


class TestStrategyStatus(BaseModel):
    """测试策略状态"""
    strategy_id: str
    symbol: str
    status: str  # running, stopped, error
    entry_price: Optional[float] = None
    current_price: Optional[float] = None
    position_size: Optional[float] = None
    pnl: Optional[float] = None
    stop_loss_price: Optional[float] = None
    message: str


# 模拟策略状态存储
test_strategies = {}


@router.post("/start", response_model=dict)
async def start_test_strategy(config: TestStrategyConfig):
    """
    启动测试策略
    
    流程:
    1. 开仓 50%
    2. 等待加仓 50%
    3. 创建止损单
    4. 监控策略执行
    """
    strategy_id = f"test_{config.symbol}_{len(test_strategies) + 1}"
    
    # 创建策略状态
    test_strategies[strategy_id] = {
        'strategy_id': strategy_id,
        'symbol': config.symbol,
        'status': 'running',
        'leverage': config.leverage,
        'amount': config.amount,
        'use_stop_loss': config.use_stop_loss,
        'stop_loss_pct': config.stop_loss_pct,
        'entry_price': None,
        'current_price': None,
        'position_size': None,
        'pnl': 0,
        'stop_loss_price': None,
        'stages': {
            'entry_50pct': False,
            'add_50pct': False,
            'stop_loss_created': False
        }
    }
    
    # 模拟策略执行（实际应该调用真实 API）
    asyncio.create_task(execute_test_strategy(strategy_id, config))
    
    return {
        'success': True,
        'message': f'测试策略已启动：{strategy_id}',
        'strategy_id': strategy_id
    }


async def execute_test_strategy(strategy_id: str, config: TestStrategyConfig):
    """
    执行测试策略
    
    流程:
    1. 开仓 50%
    2. 等待价格变动，加仓 50%
    3. 创建止损单
    4. 监控止损
    """
    import asyncio
    
    strategy = test_strategies.get(strategy_id)
    if not strategy:
        return
    
    try:
        # 阶段 1: 开仓 50%
        print(f"📊 {strategy_id}: 开仓 50%...")
        await asyncio.sleep(2)  # 模拟开仓
        strategy['stages']['entry_50pct'] = True
        strategy['entry_price'] = 2000.0  # 模拟价格
        strategy['position_size'] = (config.amount * 0.5) / strategy['entry_price'] * config.leverage
        print(f"✅ {strategy_id}: 开仓 50% 完成")
        
        # 阶段 2: 加仓 50%
        print(f"📊 {strategy_id}: 等待加仓条件...")
        await asyncio.sleep(3)  # 模拟等待
        strategy['stages']['add_50pct'] = True
        strategy['position_size'] *= 2  # 加仓后翻倍
        print(f"✅ {strategy_id}: 加仓 50% 完成")
        
        # 阶段 3: 创建止损单
        if config.use_stop_loss:
            print(f"📊 {strategy_id}: 创建止损单...")
            await asyncio.sleep(1)
            strategy['stages']['stop_loss_created'] = True
            strategy['stop_loss_price'] = strategy['entry_price'] * (1 - config.stop_loss_pct / 100)
            print(f"✅ {strategy_id}: 止损单已创建 @ {strategy['stop_loss_price']}")
        
        # 阶段 4: 监控策略
        print(f"📊 {strategy_id}: 监控策略执行...")
        while strategy['status'] == 'running':
            await asyncio.sleep(5)
            # 模拟价格变动
            strategy['current_price'] = strategy['entry_price'] * (1 + (hash(strategy_id) % 100 - 50) / 1000)
            strategy['pnl'] = (strategy['current_price'] - strategy['entry_price']) * strategy['position_size']
            
            # 检查止损
            if config.use_stop_loss and strategy['current_price'] <= strategy['stop_loss_price']:
                print(f"🛑 {strategy_id}: 触发止损，平仓...")
                await stop_test_strategy(strategy_id)
                break
    
    except Exception as e:
        print(f"❌ {strategy_id}: 策略执行失败 - {e}")
        strategy['status'] = 'error'


@router.post("/stop/{strategy_id}", response_model=dict)
async def stop_test_strategy(strategy_id: str):
    """
    停止测试策略
    
    流程:
    1. 平仓
    2. 取消止损单
    3. 更新状态
    """
    strategy = test_strategies.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    strategy['status'] = 'stopped'
    
    return {
        'success': True,
        'message': f'策略已停止：{strategy_id}',
        'final_pnl': strategy['pnl']
    }


@router.get("/status/{strategy_id}", response_model=TestStrategyStatus)
async def get_strategy_status(strategy_id: str):
    """获取策略状态"""
    strategy = test_strategies.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    return TestStrategyStatus(
        strategy_id=strategy['strategy_id'],
        symbol=strategy['symbol'],
        status=strategy['status'],
        entry_price=strategy['entry_price'],
        current_price=strategy['current_price'],
        position_size=strategy['position_size'],
        pnl=strategy['pnl'],
        stop_loss_price=strategy['stop_loss_price'],
        message=f"阶段：开仓 50%={strategy['stages']['entry_50pct']}, 加仓 50%={strategy['stages']['add_50pct']}, 止损单={strategy['stages']['stop_loss_created']}"
    )


@router.get("/list", response_model=list)
async def list_test_strategies():
    """列出所有测试策略"""
    return list(test_strategies.values())
