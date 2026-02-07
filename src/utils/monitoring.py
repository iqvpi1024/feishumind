"""监控和追踪系统。

提供性能监控、请求追踪、指标收集等功能。

Author: Claude Code
Date: 2026-02-06
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import time
import threading
from contextlib import contextmanager
from functools import wraps
import uuid

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RequestMetrics:
    """请求指标。

    Attributes:
        endpoint: 端点路径
        method: 请求方法
        status_code: 状态码
        duration: 响应时间（毫秒）
        timestamp: 时间戳
    """

    def __init__(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """初始化请求指标。

        Args:
            endpoint: 端点路径
            method: 请求方法
            status_code: 状态码
            duration: 响应时间（毫秒）
            timestamp: 时间戳
        """
        self.endpoint = endpoint
        self.method = method
        self.status_code = status_code
        self.duration = duration
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。

        Returns:
            字典表示
        """
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "duration_ms": self.duration,
            "timestamp": self.timestamp.isoformat(),
        }


class MetricsCollector:
    """指标收集器。

    收集和统计请求指标。

    Attributes:
        metrics: 指标列表
        lock: 线程锁

    Examples:
        >>> collector = MetricsCollector()
        >>> collector.record("/health", "GET", 200, 50.5)
    """

    def __init__(self, max_metrics: int = 10000) -> None:
        """初始化指标收集器。

        Args:
            max_metrics: 最大保留指标数
        """
        self.metrics: List[RequestMetrics] = []
        self.max_metrics = max_metrics
        self.lock = threading.RLock()
        logger.info(f"Metrics collector initialized with max_metrics={max_metrics}")

    def record(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
    ) -> None:
        """记录请求指标。

        Args:
            endpoint: 端点路径
            method: 请求方法
            status_code: 状态码
            duration: 响应时间（毫秒）
        """
        with self.lock:
            # 如果超过最大数量，删除最旧的
            if len(self.metrics) >= self.max_metrics:
                self.metrics.pop(0)

            metric = RequestMetrics(endpoint, method, status_code, duration)
            self.metrics.append(metric)

    def get_stats(
        self,
        endpoint: Optional[str] = None,
        minutes: int = 60,
    ) -> Dict[str, Any]:
        """获取统计信息。

        Args:
            endpoint: 端点路径（可选）
            minutes: 时间范围（分钟）

        Returns:
            统计信息字典
        """
        with self.lock:
            # 过滤指标
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            filtered_metrics = [
                m for m in self.metrics
                if m.timestamp > cutoff_time
                and (endpoint is None or m.endpoint == endpoint)
            ]

            if not filtered_metrics:
                return {
                    "total_requests": 0,
                    "avg_duration_ms": 0,
                    "p50_duration_ms": 0,
                    "p95_duration_ms": 0,
                    "p99_duration_ms": 0,
                    "error_rate": 0,
                }

            # 计算统计数据
            durations = [m.duration for m in filtered_metrics]
            error_count = sum(1 for m in filtered_metrics if m.status_code >= 400)

            durations.sort()

            return {
                "total_requests": len(filtered_metrics),
                "avg_duration_ms": sum(durations) / len(durations),
                "p50_duration_ms": durations[len(durations) // 2],
                "p95_duration_ms": durations[int(len(durations) * 0.95)],
                "p99_duration_ms": durations[int(len(durations) * 0.99)],
                "error_rate": error_count / len(filtered_metrics),
            }

    def get_recent_metrics(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取最近的指标。

        Args:
            limit: 限制数量

        Returns:
            指标列表
        """
        with self.lock:
            recent = self.metrics[-limit:]
            return [m.to_dict() for m in recent]

    def clear(self) -> None:
        """清空指标。"""
        with self.lock:
            self.metrics.clear()


# 全局指标收集器实例
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器实例。

    Returns:
        指标收集器实例
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


class RequestContext:
    """请求上下文。

    追踪单个请求的生命周期。

    Attributes:
        request_id: 请求 ID
        start_time: 开始时间
        endpoint: 端点路径
        method: 请求方法
        metadata: 元数据
    """

    def __init__(
        self,
        request_id: str,
        endpoint: str,
        method: str,
    ) -> None:
        """初始化请求上下文。

        Args:
            request_id: 请求 ID
            endpoint: 端点路径
            method: 请求方法
        """
        self.request_id = request_id
        self.start_time = time.time()
        self.endpoint = endpoint
        self.method = method
        self.metadata: Dict[str, Any] = {}

    def get_duration_ms(self) -> float:
        """获取已用时间（毫秒）。

        Returns:
            已用时间（毫秒）
        """
        return (time.time() - self.start_time) * 1000


@contextmanager
def track_request(endpoint: str, method: str = "GET"):
    """追踪请求上下文管理器。

    Args:
        endpoint: 端点路径
        method: 请求方法

    Yields:
        请求上下文

    Examples:
        >>> with track_request("/health", "GET") as ctx:
        ...     # ... 处理请求 ...
        ...     pass
        >>> # 自动记录指标
    """
    request_id = str(uuid.uuid4())
    ctx = RequestContext(request_id, endpoint, method)

    logger.info(f"[{request_id}] Started: {method} {endpoint}")

    try:
        yield ctx

        duration = ctx.get_duration_ms()
        logger.info(f"[{request_id}] Completed: {method} {endpoint} - {duration:.2f}ms")

        # 记录指标
        collector = get_metrics_collector()
        collector.record(endpoint, method, 200, duration)

    except Exception as e:
        duration = ctx.get_duration_ms()
        logger.error(f"[{request_id}] Failed: {method} {endpoint} - {str(e)}")

        # 记录错误指标
        collector = get_metrics_collector()
        collector.record(endpoint, method, 500, duration)

        raise


def tracked(endpoint: str, method: str = "GET"):
    """追踪装饰器。

    Args:
        endpoint: 端点路径
        method: 请求方法

    Returns:
        装饰器函数

    Examples:
        >>> @tracked("/api/func", "POST")
        ... def my_function():
        ...     return {"success": True}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with track_request(endpoint, method):
                return func(*args, **kwargs)

        return wrapper
    return decorator


class PerformanceTimer:
    """性能计时器。

    用于测量代码执行时间。

    Attributes:
        name: 计时器名称
        start_time: 开始时间

    Examples:
        >>> with PerformanceTimer("database_query"):
        ...     # ... 执行查询 ...
        ...     pass
        >>> # 自动打印耗时
    """

    def __init__(self, name: str) -> None:
        """初始化计时器。

        Args:
            name: 计时器名称
        """
        self.name = name
        self.start_time: Optional[float] = None

    def __enter__(self):
        """进入上下文。"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文。"""
        if self.start_time is not None:
            duration = (time.time() - self.start_time) * 1000
            logger.info(f"[Performance] {self.name}: {duration:.2f}ms")

            # 如果执行时间过长，发出警告
            if duration > 1000:
                logger.warning(
                    f"[Performance Warning] {self.name} took {duration:.2f}ms"
                )

    def get_duration_ms(self) -> float:
        """获取已用时间（毫秒）。

        Returns:
            已用时间（毫秒）
        """
        if self.start_time is None:
            return 0.0
        return (time.time() - self.start_time) * 1000


def log_execution_time(func: Callable) -> Callable:
    """记录函数执行时间的装饰器。

    Args:
        func: 函数

    Returns:
        装饰后的函数

    Examples:
        >>> @log_execution_time
        ... def my_function():
        ...     time.sleep(1)
        ...     return "done"
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            return result

        finally:
            duration = (time.time() - start_time) * 1000
            logger.debug(f"[Execution Time] {func_name}: {duration:.2f}ms")

    return wrapper


def slow_query_threshold(threshold_ms: float = 500):
    """慢查询检测装饰器。

    Args:
        threshold_ms: 阈值（毫秒）

    Returns:
        装饰器函数

    Examples:
        >>> @slow_query_threshold(threshold_ms=200)
        ... def query_database():
        ...     # ... 查询操作 ...
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result

            finally:
                duration = (time.time() - start_time) * 1000
                if duration > threshold_ms:
                    logger.warning(
                        f"[Slow Query] {func.__name__} took {duration:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )

        return wrapper
    return decorator
