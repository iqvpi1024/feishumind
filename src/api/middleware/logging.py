"""
请求日志中间件

本模块提供请求/响应日志记录功能，用于调试和监控API性能。

功能：
- 记录所有HTTP请求的基本信息（方法、路径、状态码）
- 计算请求处理时间
- 记录请求头和响应头（可选）
- 支持排除特定路径（如 /health）

Author: FeishuMind Team
Created: 2026-02-06
"""

import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件

    记录所有传入的HTTP请求和响应，包括请求方法、路径、
    状态码和处理时间。用于调试、性能监控和审计日志。

    Example:
        ```python
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
        ```
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        exclude_paths: list[str] | None = None,
        log_headers: bool = False,
    ) -> None:
        """
        初始化日志中间件

        Args:
            app: ASGI应用实例
            exclude_paths: 要排除记录的路径列表（如 ['/health']）
            log_headers: 是否记录请求/响应头（默认False，避免日志过大）
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self.log_headers = log_headers

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        处理请求并记录日志

        Args:
            request: 传入的HTTP请求
            call_next: 下一个中间件或路由处理器

        Returns:
            Response: HTTP响应对象
        """
        # 检查是否需要排除此路径
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # 记录请求开始时间
        start_time = time.time()

        # 提取请求信息
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # 记录请求头（可选）
        if self.log_headers:
            headers = dict(request.headers)
            logger.debug(f"📤 请求头: {headers}")

        # 调用下一个中间件或路由处理器
        try:
            response = await call_next(request)
        except Exception as e:
            # 记录异常
            process_time = time.time() - start_time
            logger.error(
                f"❌ 请求异常 | "
                f"{method} {path} | "
                f"客户端: {client_host} | "
                f"耗时: {process_time:.3f}s | "
                f"错误: {str(e)}"
            )
            raise

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录响应信息
        status_code = response.status_code
        logger.info(
            f"✅ API请求 | "
            f"{method} {path} | "
            f"状态码: {status_code} | "
            f"客户端: {client_host} | "
            f"耗时: {process_time:.3f}s"
        )

        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response
