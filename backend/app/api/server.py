"""
FastAPI 应用入口 - 启动 API 服务

运行方式：
  python -m app.api.server          # 在 backend/ 目录下
  uvicorn app.api.server:app --host 0.0.0.0 --port 8000  # 等效
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.api.admin_routes import router as admin_router

app = FastAPI(
    title="LangChain Agent API",
    version="2.0.0",
    description="基于 DeepSeek 的 LLM API 服务，支持聊天、对话历史、Agent 等功能",
)

# CORS - 从环境变量读取允许的域名，逗号分隔
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:5174")
allow_origins = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（管理后台用）
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(router, prefix="")
app.include_router(admin_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
