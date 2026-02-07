"""
安全中间件

提供认证、授权、输入验证和安全响应头功能。
"""

import re
import hashlib
import secrets
from typing import Callable, Optional, List
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from jose import JWTError, jwt
from loguru import logger

from src.utils.config import settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件。

    添加安全响应头和实施安全策略。
    """

    # 安全响应头
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并添加安全头。

        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器

        Returns:
            HTTP响应
        """
        response = await call_next(request)

        # 添加安全响应头
        for header_name, header_value in self.SECURITY_HEADERS.items():
            response.headers[header_name] = header_value

        # 移除服务器信息
        response.headers.pop("Server", None)

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """输入验证中间件。

    验证和清理用户输入，防止注入攻击。
    """

    # SQL注入模式
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(\bexec\b|\bexecute\b)",
        r"(;.*\bexec\b)",
        r"('.*--)",
        r"(\/\*.*\*\/)",
    ]

    # XSS模式
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
    ]

    def __init__(self, app: ASGIApp, enable_strict: bool = True) -> None:
        """初始化输入验证中间件。

        Args:
            app: ASGI应用
            enable_strict: 是否启用严格模式
        """
        super().__init__(app)
        self.enable_strict = enable_strict

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并验证输入。

        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器

        Returns:
            HTTP响应或400错误

        Raises:
            HTTPException: 如果输入验证失败
        """
        # 验证查询参数
        if request.query_params:
            for key, value in request.query_params.items():
                if not self._is_safe_input(value):
                    logger.warning(f"可疑查询参数: {key}={value}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="输入包含非法字符",
                    )

        # 验证请求体（仅对JSON请求）
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.json()
                    if not self._is_safe_dict(body):
                        logger.warning(f"可疑请求体: {body}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="请求包含非法内容",
                        )
                except Exception as e:
                    if "非法" not in str(e):
                        logger.error(f"JSON解析失败: {e}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="无效的JSON格式",
                        )

        return await call_next(request)

    def _is_safe_input(self, value: str) -> bool:
        """检查输入是否安全。

        Args:
            value: 输入值

        Returns:
            是否安全
        """
        if not isinstance(value, str):
            return True

        # 检查SQL注入
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return False

        # 检查XSS
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return False

        return True

    def _is_safe_dict(self, data: dict, max_depth: int = 10) -> bool:
        """递归检查字典是否安全。

        Args:
            data: 字典数据
            max_depth: 最大递归深度

        Returns:
            是否安全
        """
        if max_depth <= 0:
            return False

        for key, value in data.items():
            if isinstance(value, str):
                if not self._is_safe_input(value):
                    return False
            elif isinstance(value, dict):
                if not self._is_safe_dict(value, max_depth - 1):
                    return False
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, (str, dict)):
                        if isinstance(item, str) and not self._is_safe_input(item):
                            return False
                        elif isinstance(item, dict) and not self._is_safe_dict(item, max_depth - 1):
                            return False

        return True


class JWTAuthMiddleware:
    """JWT认证中间件。

    验证JWT令牌并提供认证功能。
    """

    def __init__(self) -> None:
        """初始化JWT认证中间件。"""
        self.security = HTTPBearer(auto_error=False)
        self.algorithm = settings.JWT_ALGORITHM
        self.secret_key = settings.SECRET_KEY

    async def __call__(
        self,
        request: Request,
    ) -> Optional[HTTPAuthorizationCredentials]:
        """验证JWT令牌。

        Args:
            request: HTTP请求

        Returns:
            认证凭据或None

        Raises:
            HTTPException: 如果令牌无效
        """
        credentials: Optional[HTTPAuthorizationCredentials] = await self.security(request)

        if credentials is None:
            return None

        try:
            # 验证JWT令牌
            payload = jwt.decode(
                credentials.credentials,
                self.secret_key,
                algorithms=[self.algorithm],
            )

            # 检查过期时间
            import time
            if payload.get("exp", 0) < time.time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌已过期",
                )

            # 将用户信息存储在请求状态中
            request.state.user_id = payload.get("sub")
            request.state.payload = payload

            return credentials

        except JWTError as e:
            logger.warning(f"JWT验证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
            )

    @staticmethod
    def create_token(
        user_id: str,
        payload: dict,
        expiration_seconds: int = 3600,
    ) -> str:
        """创建JWT令牌。

        Args:
            user_id: 用户ID
            payload: 额外的载荷数据
            expiration_seconds: 过期时间（秒）

        Returns:
            JWT令牌字符串
        """
        import time

        # 合并载荷
        token_payload = {
            "sub": user_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + expiration_seconds,
            **payload,
        }

        # 生成令牌
        token = jwt.encode(
            token_payload,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        return token


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API密钥中间件。

    验证API密钥用于服务间通信。
    """

    def __init__(
        self,
        app: ASGIApp,
        api_keys: Optional[List[str]] = None,
    ) -> None:
        """初始化API密钥中间件。

        Args:
            app: ASGI应用
            api_keys: 有效的API密钥列表
        """
        super().__init__(app)
        self.api_keys = set(api_keys or [])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并验证API密钥。

        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器

        Returns:
            HTTP响应或401错误

        Raises:
            HTTPException: 如果API密钥无效
        """
        # 跳过健康检查和公开端点
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # 获取API密钥
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            # 如果没有API密钥，尝试JWT认证
            return await call_next(request)

        # 验证API密钥
        if self.api_keys and api_key not in self.api_keys:
            logger.warning(f"无效的API密钥: {api_key[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的API密钥",
            )

        return await call_next(request)


class RateLimitByUserMiddleware(BaseHTTPMiddleware):
    """基于用户的速率限制中间件。

    为每个用户实施独立的速率限制。
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
        self.user_requests: dict = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并实施速率限制。

        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器

        Returns:
            HTTP响应或429错误
        """
        import time

        # 获取用户ID
        user_id = request.state.user_id if hasattr(request.state, "user_id") else None
        if not user_id:
            # 使用客户端IP作为用户标识
            user_id = request.client.host if request.client else "unknown"

        # 清理过期的请求记录
        current_time = time.time()
        if user_id in self.user_requests:
            self.user_requests[user_id] = [
                req_time
                for req_time in self.user_requests[user_id]
                if current_time - req_time < 60
            ]

        # 检查速率限制
        request_count = len(self.user_requests.get(user_id, []))
        if request_count >= self.requests_per_minute:
            logger.warning(f"用户速率限制触发: {user_id} ({request_count} requests/min)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"每分钟最多{self.requests_per_minute}个请求",
            )

        # 记录此次请求
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        self.user_requests[user_id].append(current_time)

        return await call_next(request)


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """CORS安全中间件。

    严格配置CORS策略。
    """

    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: List[str] = None,
        allowed_methods: List[str] = None,
        allowed_headers: List[str] = None,
    ) -> None:
        """初始化CORS中间件。

        Args:
            app: ASGI应用
            allowed_origins: 允许的源列表
            allowed_methods: 允许的HTTP方法
            allowed_headers: 允许的请求头
        """
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["https://open.feishu.cn"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE"]
        self.allowed_headers = allowed_headers or ["Content-Type", "Authorization"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并添加CORS头。

        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器

        Returns:
            HTTP响应
        """
        origin = request.headers.get("origin")

        # 验证源
        if origin in self.allowed_origins:
            # 预检请求
            if request.method == "OPTIONS":
                response = Response()
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
                response.headers["Access-Control-Max-Age"] = "600"
                return response

        response = await call_next(request)

        # 添加CORS头
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


def setup_security_middleware(app) -> None:
    """设置所有安全中间件。

    Args:
        app: FastAPI应用实例
    """
    # 安全响应头
    app.add_middleware(SecurityMiddleware)

    # 输入验证
    app.add_middleware(InputValidationMiddleware, enable_strict=True)

    # CORS安全配置
    app.add_middleware(
        CORSSecurityMiddleware,
        allowed_origins=settings.ALLOWED_ORIGINS,
    )

    # API密钥验证（如果配置了密钥）
    api_keys = settings.API_KEYS if hasattr(settings, "API_KEYS") else None
    if api_keys:
        app.add_middleware(APIKeyMiddleware, api_keys=api_keys)

    logger.info("安全中间件已启用")
