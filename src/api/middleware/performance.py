"""
性能优化中间件

提供响应压缩、缓存控制等性能优化功能。
"""

import time
import gzip
import json
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件。

    记录每个请求的处理时间，识别慢查询。
    """

    def __init__(
        self,
        app: ASGIApp,
        slow_query_threshold_ms: float = 1000.0,
    ) -> None:
        """初始化性能中间件。

        Args:
            app: ASGI应用
            slow_query_threshold_ms: 慢查询阈值（毫秒）
        """
        super().__init__(app)
        self.slow_query_threshold_ms = slow_query_threshold_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录性能指标。

        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器

        Returns:
            HTTP响应
        """
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time_ms = (time.time() - start_time) * 1000

        # 添加响应头
        response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"

        # 记录慢查询
        if process_time_ms > self.slow_query_threshold_ms:
            logger.warning(
                f"慢查询检测: {request.method} {request.url.path} "
                f"耗时 {process_time_ms:.2f}ms"
            )

        # 记录性能日志
        logger.info(
            f"{request.method} {request.url.path} "
            f"状态码:{response.status_code} "
            f"耗时:{process_time_ms:.2f}ms"
        )

        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """缓存控制中间件。

    为静态资源添加缓存头。
    """

    # 静态资源缓存时间（秒）
    STATIC_CACHE_MAX_AGE = 86400  # 1天

    # API响应缓存时间（秒）
    API_CACHE_MAX_AGE = 300  # 5分钟

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并添加缓存头。

        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器

        Returns:
            HTTP响应
        """
        response = await call_next(request)

        # 静态资源添加长期缓存
        if request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = f"public, max-age={self.STATIC_CACHE_MAX_AGE}"

        # API响应添加短期缓存
        elif request.url.path.startswith("/api/v1/github/trending"):
            # GitHub Trending 可以缓存1小时
            response.headers["Cache-Control"] = f"public, max-age=3600"

        elif request.url.path.startswith("/api/v1/"):
            # 其他API响应缓存5分钟
            response.headers["Cache-Control"] = f"public, max-age={self.API_CACHE_MAX_AGE}"

        # 添加ETag（基于响应内容）
        if hasattr(response, "body"):
            etag = self._generate_etag(response.body)
            response.headers["ETag"] = etag

        return response

    def _generate_etag(self, body: bytes) -> str:
        """生成ETag。

        Args:
            body: 响应体

        Returns:
            ETag字符串
        """
        import hashlib
        return hashlib.md5(body).hexdigest()


class CompressionMiddleware:
    """响应压缩中间件。

    使用GZip压缩响应体，减少带宽使用。
    """

    def __init__(self, minimum_size: int = 1000) -> None:
        """初始化压缩中间件。

        Args:
            minimum_size: 最小压缩大小（字节）
        """
        self.minimum_size = minimum_size

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """处理请求并压缩响应。

        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器

        Returns:
            HTTP响应
        """
        response = await call_next(request)

        # 检查是否需要压缩
        if (
            "gzip" in request.headers.get("accept-encoding", "")
            and response.headers.get("content-type", "").startswith("application/json")
            and int(response.headers.get("content-length", 0)) > self.minimum_size
        ):
            # 压缩响应体
            compressed_body = gzip.compress(response.body)
            response.body = compressed_body
            response.headers["content-encoding"] = "gzip"
            response.headers["content-length"] = str(len(compressed_body))

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件。

    防止API滥用，保护服务稳定性。
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 30,
    ) -> None:
        """初始化速率限制中间件。

        Args:
            app: ASGI应用
            requests_per_minute: 每分钟请求数限制
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并实施速率限制。

        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器

        Returns:
            HTTP响应或429错误
        """
        # 获取客户端标识
        client_id = request.client.host if request.client else "unknown"

        # 清理过期的请求记录
        current_time = time.time()
        if client_id in self.request_counts:
            # 移除1分钟前的请求
            self.request_counts[client_id] = [
                req_time
                for req_time in self.request_counts[client_id]
                if current_time - req_time < 60
            ]

        # 检查速率限制
        request_count = len(self.request_counts.get(client_id, []))
        if request_count >= self.requests_per_minute:
            logger.warning(f"速率限制触发: {client_id} ({request_count} requests/min)")
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "message": f"每分钟最多{self.requests_per_minute}个请求",
                }),
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + 60)),
                },
            )

        # 记录此次请求
        if client_id not in self.request_counts:
            self.request_counts[client_id] = []
        self.request_counts[client_id].append(current_time)

        # 处理请求
        response = await call_next(request)

        # 添加速率限制头
        remaining = self.requests_per_minute - len(self.request_counts[client_id])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response


def setup_performance_middleware(app) -> None:
    """设置所有性能优化中间件。

    Args:
        app: FastAPI应用实例
    """
    # GZip压缩
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 性能监控
    app.add_middleware(PerformanceMiddleware, slow_query_threshold_ms=1000.0)

    # 缓存控制
    app.add_middleware(CacheControlMiddleware)

    # 速率限制
    app.add_middleware(RateLimitMiddleware, requests_per_minute=30)

    logger.info("性能优化中间件已启用")
