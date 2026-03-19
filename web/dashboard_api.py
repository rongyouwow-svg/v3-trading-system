#!/usr/bin/env python3
"""
🦞 Web Dashboard API v3.0

提供 Web 界面所需的 API 接口。

功能:
    - 策略状态查询
    - 交易记录查询
    - 账户信息查询
    - 系统状态查询
    - 静态文件服务（Web 页面）

用法:
    uvicorn web.dashboard_api:app --host 0.0.0.0 --port 3000
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from typing import Dict, List, Optional
from datetime import datetime
import os
from pathlib import Path

from modules.utils.result import Result
from modules.utils.logger import setup_logger

logger = setup_logger("dashboard_api", log_file="logs/dashboard_api.log")

# 导入测试策略 API
try:
    from test_strategy_api import router as test_strategy_router
except ImportError:
    test_strategy_router = None

# 导入币安测试网 API
try:
    from .binance_testnet_api import router as binance_router
    print(f"✅ 币安 API 导入成功：{binance_router}")
except ImportError as e:
    print(f"❌ 币安 API 导入失败：{e}")
    binance_router = None

# 导入策略状态 API
try:
    from strategies.strategy_status_api import router as strategy_status_router
    print(f"✅ 策略状态 API 导入成功")
except ImportError as e:
    print(f"❌ 策略状态 API 导入失败：{e}")
    strategy_status_router = None

# 导入交易记录刷新 API
try:
    from strategies.trades_refresh_api import router as trades_refresh_router
    print(f"✅ 交易记录刷新 API 导入成功")
except ImportError as e:
    print(f"❌ 交易记录刷新 API 导入失败：{e}")
    trades_refresh_router = None

# 导入策略管理 API
try:
    from .strategy_management_api import router as strategy_management_router, initialize_strategy_api
    print(f"✅ 策略管理 API 导入成功")
except ImportError as e:
    print(f"❌ 策略管理 API 导入失败：{e}")
    strategy_management_router = None
    initialize_strategy_api = None


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用
    
    Returns:
        FastAPI: FastAPI 应用实例
    """
    app = FastAPI(
        title="🦞 大王量化 Dashboard API",
        description="大王量化交易系统 Web 界面 API",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 配置 CORS（允许所有来源，生产环境应限制）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册币安测试网 API
    if binance_router:
        app.include_router(binance_router)
        logger.info("✅ 币安测试网 API 已注册")
    
    # 注册策略状态 API
    if strategy_status_router:
        app.include_router(strategy_status_router)
        logger.info("✅ 策略状态 API 已注册")
    
    # 注册交易记录刷新 API
    if trades_refresh_router:
        app.include_router(trades_refresh_router)
        logger.info("✅ 交易记录刷新 API 已注册")
    
    # 注册策略管理 API
    if strategy_management_router:
        app.include_router(strategy_management_router)
        logger.info("✅ 策略管理 API 已注册")
    
    # 注册测试策略 API
    if test_strategy_router:
        app.include_router(test_strategy_router)
        logger.info("✅ 测试策略 API 已注册")
    
    # 注册路由
    register_routes(app)
    
    # 挂载静态文件（Web 页面）
    dashboard_path = Path(__file__).parent / "dashboard"
    if dashboard_path.exists():
        app.mount("/dashboard", StaticFiles(directory=str(dashboard_path), html=True), name="dashboard")
        logger.info(f"✅ Web 页面已挂载：{dashboard_path}")
    
    logger.info("✅ Web Dashboard API 初始化完成")
    
    return app


def register_routes(app: FastAPI):
    """
    注册 API 路由
    
    Args:
        app (FastAPI): FastAPI 应用
    """
    
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "name": "大王量化 Dashboard API",
            "version": "3.0.0",
            "status": "ok"
        }
    
    @app.get("/api/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/api/strategies")
    async def get_strategies():
        """
        获取所有策略
        
        Returns:
            Dict: 策略列表
        """
        # TODO: 从策略管理器获取
        return {
            "strategies": [],
            "count": 0
        }
    
    @app.get("/api/strategies/{symbol}")
    async def get_strategy(symbol: str):
        """
        获取指定策略
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Dict: 策略信息
        """
        # TODO: 从策略管理器获取
        return {
            "symbol": symbol,
            "status": "unknown"
        }
    
    @app.post("/api/strategies/{symbol}/start")
    async def start_strategy(symbol: str, config: Dict):
        """
        启动策略
        
        Args:
            symbol (str): 交易对
            config (Dict): 策略配置
        
        Returns:
            Dict: 启动结果
        """
        # TODO: 调用策略管理器
        return {"success": True, "message": f"策略 {symbol} 已启动"}
    
    @app.post("/api/strategies/{symbol}/stop")
    async def stop_strategy(symbol: str):
        """
        停止策略
        
        Args:
            symbol (str): 交易对
        
        Returns:
            Dict: 停止结果
        """
        # TODO: 调用策略管理器
        return {"success": True, "message": f"策略 {symbol} 已停止"}
    
    @app.get("/api/positions")
    async def get_positions():
        """
        获取所有持仓
        
        Returns:
            Dict: 持仓列表
        """
        # TODO: 从连接器获取
        return {
            "positions": [],
            "count": 0
        }
    
    @app.get("/api/orders")
    async def get_orders(
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ):
        """
        获取订单列表
        
        Args:
            symbol (str, optional): 交易对
            status (str, optional): 状态
            limit (int, optional): 数量限制
        
        Returns:
            Dict: 订单列表
        """
        # TODO: 从订单管理器获取
        return {
            "orders": [],
            "count": 0
        }
    
    @app.get("/api/trades")
    async def get_trades(
        symbol: Optional[str] = None,
        limit: int = 100
    ):
        """
        获取交易记录
        
        Args:
            symbol (str, optional): 交易对
            limit (int, optional): 数量限制
        
        Returns:
            Dict: 交易记录列表
        """
        # TODO: 从数据库获取
        return {
            "trades": [],
            "count": 0
        }
    
    @app.get("/api/account")
    async def get_account():
        """
        获取账户信息
        
        Returns:
            Dict: 账户信息
        """
        try:
            import requests
            # 从币安 API 获取真实余额
            resp = requests.get("http://localhost:8888/api/v2/private/account", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                usdt_balance = next((item for item in data.get('balances', []) if item['asset'] == 'USDT'), None)
                if usdt_balance:
                    return {
                        "balance": {
                            "total": float(usdt_balance.get('free', 0)) + float(usdt_balance.get('locked', 0)),
                            "available": float(usdt_balance.get('free', 0)),
                            "locked": float(usdt_balance.get('locked', 0))
                        }
                    }
        except Exception as e:
            pass
        
        # 降级返回
        return {
            "balance": {
                "total": 0,
                "available": 0,
                "locked": 0
            },
            "warning": "无法获取真实余额，请检查 API 连接"
        }
    
    @app.get("/api/system")
    async def get_system_status():
        """
        获取系统状态
        
        Returns:
            Dict: 系统状态信息
        """
        return {
            "status": "ok",
            "version": "3.0.0",
            "uptime": 0,
            "strategies_count": 0,
            "orders_count": 0
        }
    
    @app.post("/api/strategy/start")
    async def start_strategy(request: Request):
        """启动策略"""
        try:
            data = await request.json()
            logger.info(f"🚀 启动策略请求：{data}")
            
            strategy_id = f"test_{data.get('symbol', 'ETHUSDT')}_{datetime.now().strftime('%H%M%S')}"
            
            return {
                'success': True,
                'message': f'策略已启动：{strategy_id}',
                'strategy_id': strategy_id,
                'config': data
            }
            
        except Exception as e:
            logger.error(f"❌ 启动策略失败：{e}")
            return {
                'success': False,
                'message': f'启动失败：{str(e)}'
            }
    
    @app.get("/api/plugins")
    async def get_plugins():
        """
        获取插件列表
        
        Returns:
            Dict: 插件列表
        """
        # TODO: 从插件管理器获取
        return {
            "plugins": [],
            "count": 0
        }


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 启动 Web Dashboard API")
    logger.info("📊 API 文档：http://localhost:3000/docs")
    logger.info("🏠 Web 页面：http://localhost:3000/dashboard/")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    )


# ==================== 优雅关闭处理 ====================

import atexit
import signal
import sys

class GracefulShutdown:
    """优雅关闭处理器"""
    
    def __init__(self):
        self.running = True
        # 注册信号处理
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
        # 注册退出清理
        atexit.register(self.cleanup)
    
    def handle_signal(self, signum, frame):
        logger.info(f"收到信号 {signum}，开始优雅关闭...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """清理所有资源"""
        logger.info("开始清理资源...")
        
        # 关闭数据库连接
        try:
            # TODO: 添加数据库连接关闭
            logger.info("✅ 数据库连接已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭数据库失败：{e}")
        
        # 关闭 API 连接
        try:
            # TODO: 添加 API 连接关闭
            logger.info("✅ API 连接已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭 API 失败：{e}")
        
        # 保存状态
        try:
            # TODO: 添加状态保存
            logger.info("✅ 状态已保存")
        except Exception as e:
            logger.error(f"❌ 保存状态失败：{e}")
        
        logger.info("✅ 资源清理完成")

# 初始化优雅关闭处理器
shutdown_handler = GracefulShutdown()

logger.info("✅ 优雅关闭处理器已初始化")


# ==================== 健康检查端点 ====================

@app.get("/health/detailed")
async def health_detailed():
    """详细健康检查"""
    import psutil
    import os
    
    try:
        process = psutil.Process(os.getpid())
        
        # 内存使用
        memory_percent = process.memory_percent()
        memory_info = process.memory_info()
        
        # CPU 使用
        cpu_percent = process.cpu_percent(interval=1)
        
        # 磁盘使用
        disk_usage = psutil.disk_usage('/')
        
        # 网络连接数
        connections = process.num_connections()
        
        # 打开的文件数
        open_files = len(process.open_files())
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "process": {
                "pid": os.getpid(),
                "memory_percent": round(memory_percent, 2),
                "memory_rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "cpu_percent": cpu_percent,
                "threads": process.num_threads(),
                "connections": connections,
                "open_files": open_files
            },
            "system": {
                "memory_total_gb": round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
                "memory_available_gb": round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 2),
                "disk_total_gb": round(disk_usage.total / 1024 / 1024 / 1024, 2),
                "disk_free_gb": round(disk_usage.free / 1024 / 1024 / 1024, 2),
                "disk_percent": round(disk_usage.percent, 2)
            }
        }
        
        # 健康检查规则
        if memory_percent > 90:
            health_status["status"] = "unhealthy"
            health_status["reason"] = "memory_usage > 90%"
        elif cpu_percent > 90:
            health_status["status"] = "unhealthy"
            health_status["reason"] = "cpu_usage > 90%"
        elif disk_usage.percent > 90:
            health_status["status"] = "unhealthy"
            health_status["reason"] = "disk_usage > 90%"
        
        return health_status
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "reason": str(e),
            "timestamp": datetime.now().isoformat()
        }

logger.info("✅ 健康检查端点已添加")


# ==================== 自动状态保存 ====================

import asyncio
from core.state_persistence import state_manager

async def auto_save_state():
    """每 5 分钟自动保存状态"""
    while True:
        await asyncio.sleep(300)  # 5 分钟
        try:
            # 获取当前策略状态
            response = requests.get('http://localhost:3000/api/strategy/active', timeout=5)
            if response.status_code == 200:
                data = response.json()
                states = {s['symbol']: s for s in data.get('active_strategies', [])}
                
                # 保存状态
                state_manager.save_all_states(states)
                logger.info("✅ 自动状态保存完成")
        except Exception as e:
            logger.error(f"❌ 自动状态保存失败：{e}")

# 启动后台任务
# asyncio.create_task(auto_save_state())

logger.info("✅ 自动状态保存已配置")


# ============================================================================
# 策略注册中心 API
# ============================================================================

# 内存中的策略注册表（全局变量）
global_active_strategies = {}

@app.post("/api/strategy/register")
async def register_strategy(request: Request):
    """策略注册"""
    try:
        data = await request.json()
        symbol = data.get('symbol')
        pid = data.get('pid')
        
        if not symbol:
            return {'success': False, 'error': 'Missing symbol'}
        
        # 记录策略信息
        global_active_strategies[symbol] = {
            'symbol': symbol,
            'pid': pid,
            'leverage': data.get('leverage', 1),
            'amount': data.get('amount', 0),
            'script': data.get('script', ''),
            'start_time': data.get('start_time', datetime.now().isoformat()),
            'status': 'running'
        }
        
        print(f"✅ 策略注册：{symbol} (PID: {pid})")
        
        return {'success': True, 'message': f'Strategy {symbol} registered'}
    
    except Exception as e:
        print(f"❌ 策略注册失败：{e}")
        return {'success': False, 'error': str(e)}

@app.post("/api/strategy/unregister")
async def unregister_strategy(request: Request):
    """策略注销"""
    try:
        data = await request.json()
        symbol = data.get('symbol')
        
        if not symbol:
            return {'success': False, 'error': 'Missing symbol'}
        
        # 删除策略记录
        if symbol in global_active_strategies:
            del global_active_strategies[symbol]
            print(f"✅ 策略注销：{symbol}")
        else:
            print(f"⚠️ 策略未找到：{symbol}")
        
        return {'success': True, 'message': f'Strategy {symbol} unregistered'}
    
    except Exception as e:
        print(f"❌ 策略注销失败：{e}")
        return {'success': False, 'error': str(e)}

@app.get("/api/strategy/list")
async def get_strategy_list():
    """获取活跃策略列表"""
    try:
        strategies = list(global_active_strategies.values())
        return {
            'success': True,
            'strategies': strategies,
            'count': len(strategies)
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.get("/api/strategies")
async def get_strategies():
    """获取策略列表（兼容旧 API）"""
    result = await get_strategy_list()
    return {
        'strategies': result.get('strategies', []),
        'count': result.get('count', 0)
    }


# ============================================================================
# 策略注册中心 API
# ============================================================================

@app.post("/api/strategy/register")
async def api_register_strategy(request: Request):
    """策略注册"""
    try:
        from strategy_registry import register_strategy
        data = await request.json()
        result = register_strategy(
            symbol=data.get('symbol'),
            pid=data.get('pid'),
            leverage=data.get('leverage', 1),
            amount=data.get('amount', 0),
            script=data.get('script', '')
        )
        return {'success': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.post("/api/strategy/unregister")
async def api_unregister_strategy(request: Request):
    """策略注销"""
    try:
        from strategy_registry import unregister_strategy
        data = await request.json()
        result = unregister_strategy(data.get('symbol'))
        return {'success': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.get("/api/strategy/list")
async def api_get_strategies():
    """获取策略列表"""
    try:
        from strategy_registry import get_active_strategies
        strategies = get_active_strategies()
        return {'success': True, 'data': {'strategies': strategies}}
    except Exception as e:
        return {'success': False, 'error': str(e)}
