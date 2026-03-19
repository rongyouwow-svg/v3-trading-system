#!/usr/bin/env python3
"""V3 量化交易系统启动脚本"""

import uvicorn
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🦞 启动 V3 量化交易系统...")
    print(f"工作目录：{os.getcwd()}")
    print(f"Python: {sys.version}")
    
    # 启动 FastAPI 服务器
    uvicorn.run(
        "web.dashboard_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
