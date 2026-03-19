#!/usr/bin/env python3
"""
📈 策略状态 API

提供策略状态查询功能
"""

from fastapi import APIRouter, Query, Body
from typing import Dict, List
import requests
import os
import json

router = APIRouter(prefix="/api/strategy", tags=["策略状态"])

# 策略进程文件
STRATEGY_PID_FILE = "/root/.openclaw/workspace/quant/v3-architecture/logs/strategy_pids.json"


def get_strategy_status_from_file() -> Dict:
    """从文件获取策略状态"""
    import json
    
    try:
        with open(STRATEGY_PID_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 如果是字符串，解析为字典
            if isinstance(data, str):
                return json.loads(data)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"⚠️ 读取策略状态失败：{e}")
        return {}


def save_strategy_status(status: Dict):
    """保存策略状态"""
    import json
    
    try:
        with open(STRATEGY_PID_FILE, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ 保存策略状态失败：{e}")


@router.get("/status")
async def get_strategy_status():
    """获取策略状态"""
    status = get_strategy_status_from_file()
    
    return {
        'success': True,
        'strategies': status
    }


@router.get("/active")
async def get_active_strategies():
    """获取活跃策略"""
    status = get_strategy_status_from_file()
    
    active = []
    for symbol, data in status.items():
        # 跳过非字典数据
        if not isinstance(data, dict):
            continue
        
        if data.get('status') == 'running':
            active.append({
                'symbol': symbol,
                'status': data.get('status', 'unknown'),
                'rsi': data.get('last_rsi', 0),
                'stable_count': data.get('stable_count', 0),
                'position': data.get('position', None),
                'entry_price': data.get('entry_price', 0),
                'signals_sent': data.get('signals_sent', 0),
                'signals_executed': data.get('signals_executed', 0)
            })
    
    return {
        'success': True,
        'active_strategies': active,
        'count': len(active)
    }


@router.post("/update")
async def update_strategy_status(request: dict = Body(...)):
    """更新策略状态"""
    symbol = request.get('symbol')
    status_data = request.get('status_data')
    
    if not symbol:
        return {'success': False, 'error': 'symbol is required'}
    
    status = get_strategy_status_from_file()
    status[symbol] = status_data
    save_strategy_status(status)
    
    return {
        'success': True,
        'message': f'{symbol} 策略状态已更新'
    }
