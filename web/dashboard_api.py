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
        # TODO: 从连接器获取
        return {
            "balance": {
                "total": 0,
                "available": 0,
                "locked": 0
            }
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
