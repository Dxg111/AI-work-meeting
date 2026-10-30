"""
FastAPI 主入口文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import os
import sys

# 中文 Windows 默认控制台为 GBK，强制 UTF-8 输出，避免 emoji/特殊字符导致启动失败
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from config import settings
from core.database import engine
from core.exceptions import (
    BusinessException,
    business_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)

# 导入所有模型（确保 SQLAlchemy 识别表关系）
import models

# 导入路由
from api import auth, meetings

# 确保上传目录存在（在应用创建前）
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("[启动] 应用启动中...")

    # 启动 APScheduler 调度器
    from core.scheduler import start_scheduler, shutdown_scheduler
    start_scheduler()

    yield

    # 关闭时执行
    print("[关闭] 应用关闭中...")
    shutdown_scheduler()
    await engine.dispose()


# 创建 FastAPI 应用
app = FastAPI(
    title="智能会议纪要助手系统",
    description="基于 LangChain 的 AI 会议纪要生成系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 挂载静态文件目录（上传的音视频文件）
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册异常处理器
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(meetings.router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """根路径"""
    return {"message": "智能会议纪要助手系统 API"}


@app.get(f"{settings.API_PREFIX}/health")
async def health_check():
    """健康检查"""
    return {
        "code": 200,
        "message": "服务运行正常",
        "data": {
            "status": "healthy",
            "version": "1.0.0"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
