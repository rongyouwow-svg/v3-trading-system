#!/usr/bin/env python3
"""
📊 策略管理 API v3.1

功能:
    - 策略启动
    - 策略停止
    - 策略列表查询
    - 策略状态查询

用法:
    from web.strategy_management_api import router
    app.include_router(router)
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategy", tags=["策略管理"])

# 全局策略管理器（由主应用初始化）
_strategy_manager = None
_execution_engine = None


def initialize_strategy_api(strategy_manager, execution_engine):
    """
    初始化策略 API
    
    Args:
        strategy_manager: 策略管理器实例
        execution_engine: 执行引擎实例
    """
    global _strategy_manager, _execution_engine
    _strategy_manager = strategy_manager
    _execution_engine = execution_engine
    logger.info("✅ 策略管理 API 初始化完成")


@router.post("/start")
async def start_strategy(request: Request):
    """
    启动策略
    
    请求示例:
    ```json
    {
        "name": "ETH_RSI",
        "symbol": "ETHUSDT",
        "type": "rsi_strategy",
        "leverage": 3,
        "amount": 100,
        "stop_loss_pct": 0.002
    }
    ```
    """
    try:
        data = await request.json()
        
        # 验证必需参数
        required_fields = ['name', 'symbol']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"缺少必需参数：{field}")
        
        # 检查策略是否已存在
        if _strategy_manager and data['name'] in _strategy_manager.strategies:
            raise HTTPException(status_code=400, detail=f"策略 {data['name']} 已存在")
        
        # 构建策略配置
        config = {
            'symbol': data['symbol'],
            'type': data.get('type', 'rsi_strategy'),
            'leverage': data.get('leverage', 3),
            'amount': data.get('amount', 100),
            'stop_loss_pct': data.get('stop_loss_pct'),  # None 表示使用 5% 兜底
            'module': data.get('module')
        }
        
        # 加载策略
        if _strategy_manager:
            success = _strategy_manager.load_strategy(data['name'], config)
            
            if not success:
                raise HTTPException(status_code=500, detail="策略加载失败")
            
            # 启动策略
            _strategy_manager.start_strategy(data['name'])
            
            # 注册到执行引擎
            if _execution_engine:
                _execution_engine.register_strategy(
                    data['name'],
                    _strategy_manager.strategies[data['name']]
                )
            
            logger.info(f"✅ 策略 {data['name']} 启动成功")
            
            return JSONResponse(content={
                'success': True,
                'data': {
                    'name': data['name'],
                    'status': 'running',
                    'symbol': config['symbol'],
                    'leverage': config['leverage'],
                    'amount': config['amount'],
                    'stop_loss_pct': config['stop_loss_pct'],
                    'message': f"策略已启动，止损配置：{config['stop_loss_pct']*100 if config['stop_loss_pct'] else 5}%"
                }
            })
        else:
            raise HTTPException(status_code=500, detail="策略管理器未初始化")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 启动策略失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_strategy(request: Request):
    """
    停止策略
    
    请求示例:
    ```json
    {
        "name": "ETH_RSI",
        "close_position": true,
        "cancel_stop_loss": true
    }
    ```
    """
    try:
        data = await request.json()
        
        # 验证必需参数
        if 'name' not in data:
            raise HTTPException(status_code=400, detail="缺少必需参数：name")
        
        # 检查策略是否存在
        if not _strategy_manager or data['name'] not in _strategy_manager.strategies:
            raise HTTPException(status_code=404, detail=f"策略 {data['name']} 不存在")
        
        # 平仓（可选）
        if data.get('close_position', True):
            strategy = _strategy_manager.strategies[data['name']]
            if strategy.position:
                # 执行平仓
                close_signal = {
                    'symbol': strategy.symbol,
                    'quantity': None  # 全平
                }
                _execution_engine.execute_close_signal(close_signal)
                logger.info(f"✅ 策略 {data['name']} 持仓已平仓")
        
        # 取消止损单（可选）
        if data.get('cancel_stop_loss', True):
            strategy = _strategy_manager.strategies[data['name']]
            if _execution_engine:
                _execution_engine.stop_loss_manager.cancel_stop_loss_by_symbol(strategy.symbol)
                logger.info(f"✅ 策略 {data['name']} 止损单已取消")
        
        # 停止策略
        _strategy_manager.stop_strategy(data['name'])
        
        # 从执行引擎注销
        if _execution_engine:
            _execution_engine.unregister_strategy(data['name'])
        
        logger.info(f"✅ 策略 {data['name']} 已停止")
        
        return JSONResponse(content={
            'success': True,
            'data': {
                'name': data['name'],
                'status': 'stopped',
                'position_closed': data.get('close_position', True),
                'stop_loss_cancelled': data.get('cancel_stop_loss', True),
                'message': '策略已停止'
            }
        })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 停止策略失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_strategy_list():
    """
    获取策略列表
    
    返回:
    ```json
    {
        "success": true,
        "data": {
            "strategies": [
                {
                    "name": "ETH_RSI",
                    "status": "running",
                    "symbol": "ETHUSDT",
                    "leverage": 3,
                    "amount": 100,
                    "stop_loss_pct": 0.002,
                    "last_tick": "2026-03-14T17:04:00Z"
                }
            ]
        }
    }
    ```
    """
    try:
        if not _strategy_manager:
            return JSONResponse(content={
                'success': True,
                'data': {'strategies': []}
            })
        
        strategies = _strategy_manager.get_all_status()
        
        # 添加策略管理器状态
        response_data = {
            'strategies': strategies,
            'manager_status': {
                'total_strategies': len(_strategy_manager.strategies),
                'running_strategies': sum(1 for s in strategies if s.get('status') == 'running'),
                'max_workers': _strategy_manager.executor._max_workers
            }
        }
        
        return JSONResponse(content={
            'success': True,
            'data': response_data
        })
            
    except Exception as e:
        logger.error(f"❌ 获取策略列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/status")
async def get_strategy_status(name: str):
    """
    获取策略状态
    
    返回:
    ```json
    {
        "success": true,
        "data": {
            "name": "ETH_RSI",
            "status": "running",
            "symbol": "ETHUSDT",
            "leverage": 3,
            "amount": 100,
            "stop_loss_pct": 0.002,
            "last_tick": "2026-03-14T17:04:00Z"
        }
    }
    ```
    """
    try:
        if not _strategy_manager or name not in _strategy_manager.strategies:
            raise HTTPException(status_code=404, detail=f"策略 {name} 不存在")
        
        status = _strategy_manager.get_strategy_status(name)
        
        return JSONResponse(content={
            'success': True,
            'data': status
        })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取策略状态失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    健康检查端点
    
    返回:
    ```json
    {
        "success": true,
        "data": {
            "web": "ok",
            "strategies": 3,
            "monitor": "ok",
            "timestamp": "2026-03-14T18:32:00Z"
        }
    }
    ```
    """
    try:
        strategy_count = 0
        if _strategy_manager:
            strategy_count = len(_strategy_manager.strategies)
        
        return JSONResponse(content={
            'success': True,
            'data': {
                'web': 'ok',
                'strategies': strategy_count,
                'monitor': 'ok',
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"❌ 健康检查失败：{e}")
        return JSONResponse(content={
            'success': False,
            'data': {
                'web': 'error',
                'error': str(e)
            }
        }, status_code=500)


@router.post("/restart")
async def restart_strategy(request: Request):
    """
    重启策略（停止后重新启动）
    
    请求示例:
    ```json
    {
        "name": "ETH_RSI",
        "close_position": false
    }
    ```
    """
    try:
        data = await request.json()
        
        if 'name' not in data:
            raise HTTPException(status_code=400, detail="缺少必需参数：name")
        
        # 获取策略配置
        if not _strategy_manager or data['name'] not in _strategy_manager.strategy_configs:
            raise HTTPException(status_code=404, detail=f"策略 {data['name']} 不存在")
        
        config = _strategy_manager.strategy_configs[data['name']]
        
        # 停止策略（不平仓）
        _strategy_manager.stop_strategy(data['name'])
        
        # 等待 1 秒
        import time
        time.sleep(1)
        
        # 重新启动策略
        _strategy_manager.start_strategy(data['name'])
        
        logger.info(f"✅ 策略 {data['name']} 已重启")
        
        return JSONResponse(content={
            'success': True,
            'data': {
                'name': data['name'],
                'status': 'running',
                'message': '策略已重启'
            }
        })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 重启策略失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
