"""
FeishuMind FastAPI 主应用模块

本模块定义了 FastAPI 应用的核心配置和中间件设置。
遵循 PEP 8 编码规范，使用类型注解和异步编程模式。

功能：
- FastAPI 应用实例初始化
- CORS 中间件配置（支持飞书域名）
- 健康检查端点
- 全局异常处理
- 请求日志中间件

Author: FeishuMind Team
Created: 2026-02-06
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn

from src.api.middleware.logging import LoggingMiddleware
from src.api.routes import memory, agent, webhook, github, resilience, calendar


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理

    在应用启动和关闭时执行初始化和清理操作。

    Args:
        app: FastAPI 应用实例

    Yields:
        None
    """
    # 启动时执行
    logger.info("🚀 FeishuMind 启动中...")
    logger.info("📚 版本: 1.0.0")
    logger.info("🔧 环境: development")
    yield
    # 关闭时执行
    logger.info("👋 FeishuMind 关闭中...")


# 创建 FastAPI 应用实例
app = FastAPI(
    title="FeishuMind API",
    description="飞书灵犀 - 半自主AI代理系统，有情商的职场参谋",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ============ CORS 中间件配置 ============
# 允许的源（飞书域名 + 本地开发）
ALLOWED_ORIGINS: list[str] = [
    "https://open.feishu.cn",  # 飞书官方域名
    "http://localhost:3000",   # 本地开发前端
    "http://localhost:8000",   # 本地API服务
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# ============ 自定义中间件 ============
# 请求日志中间件（必须在CORS之后添加）
app.add_middleware(LoggingMiddleware)

# ============ API 路由注册 ============
# 记忆管理路由
app.include_router(memory.router, prefix="/api/v1")
logger.info("✅ Memory routes registered")

# Agent 路由
app.include_router(agent.router, prefix="/api/v1")
logger.info("✅ Agent routes registered")

# Webhook 路由
app.include_router(webhook.router, prefix="/api/v1")
logger.info("✅ Webhook routes registered")

# GitHub 路由
app.include_router(github.router, prefix="")
logger.info("✅ GitHub routes registered")

# 韧性辅导路由
app.include_router(resilience.router, prefix="")
logger.info("✅ Resilience routes registered")

# 日历路由
app.include_router(calendar.router, prefix="/api/v1")
logger.info("✅ Calendar routes registered")


# ============ 健康检查端点 ============
@app.get(
    "/health",
    tags=["Health"],
    summary="健康检查",
    description="检查API服务是否正常运行",
    responses={
        200: {
            "description": "服务正常",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "FeishuMind",
                        "version": "1.0.0",
                    }
                }
            },
        }
    },
)
async def health_check() -> dict[str, str]:
    """
    健康检查端点

    用于负载均衡器、容器编排系统等服务健康检查。
    返回服务的状态和基本信息。

    Returns:
        dict[str, str]: 包含服务状态的字典
            - status: 服务状态（healthy/unhealthy）
            - service: 服务名称
            - version: 服务版本
    """
    return {
        "status": "healthy",
        "service": "FeishuMind",
        "version": "1.0.0",
    }


@app.get(
    "/",
    tags=["Root"],
    summary="根路径",
    description="API 服务根路径，返回欢迎信息",
)
async def root() -> dict[str, str]:
    """
    根路径端点

    返回API的基本信息和文档链接。

    Returns:
        dict[str, str]: 欢迎信息和文档链接
    """
    return {
        "message": "Welcome to FeishuMind API",
        "docs": "/docs",
        "health": "/health",
    }


# ============ 全局异常处理器 ============
class FeishuMindException(Exception):
    """FeishuMind 自定义异常基类"""

    def __init__(self, message: str, code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        """
        初始化自定义异常

        Args:
            message: 错误信息
            code: HTTP状态码
        """
        self.message = message
        self.code = code
        super().__init__(self.message)


@app.exception_handler(FeishuMindException)
async def feishumind_exception_handler(
    request: Request, exc: FeishuMindException
) -> JSONResponse:
    """
    自定义异常处理器

    处理 FeishuMindException 及其子类异常，返回统一的错误响应格式。

    Args:
        request: 请求对象
        exc: 异常实例

    Returns:
        JSONResponse: 格式化的错误响应
    """
    logger.error(f"❌ 自定义异常: {exc.message} | 路径: {request.url.path}")
    return JSONResponse(
        status_code=exc.code,
        content={
            "error": True,
            "message": exc.message,
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器

    捕获所有未被其他处理器处理的异常，防止敏感信息泄露。

    Args:
        request: 请求对象
        exc: 异常实例

    Returns:
        JSONResponse: 通用错误响应
    """
    # 在生产环境中，不应该暴露详细的错误信息
    logger.error(f"💥 未处理的异常: {str(exc)} | 路径: {request.url.path}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "path": request.url.path,
        },
    )


# ============ 启动命令 ============
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式：自动重载
        log_level="info",
    )
