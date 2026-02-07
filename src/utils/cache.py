"""简单缓存系统。

提供内存缓存和TTL支持。

Author: Claude Code
Date: 2026-02-06
"""

from typing import Dict, Any, Optional, Callable, TypeVar
from datetime import datetime, timedelta
import threading
from functools import wraps
import hashlib
import json

from src.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CacheEntry:
    """缓存条目。

    Attributes:
        value: 缓存值
        expiry: 过期时间
    """

    def __init__(self, value: Any, ttl: int = 300) -> None:
        """初始化缓存条目。

        Args:
            value: 缓存值
            ttl: 过期时间（秒），默认5分钟
        """
        self.value = value
        self.expiry = datetime.now() + timedelta(seconds=ttl)
        self.created_at = datetime.now()

    def is_expired(self) -> bool:
        """检查是否过期。

        Returns:
            是否过期
        """
        return datetime.now() > self.expiry


class SimpleCache:
    """简单内存缓存。

    线程安全的LRU缓存实现。

    Attributes:
        cache: 缓存字典
        max_size: 最大缓存条目数
        lock: 线程锁

    Examples:
        >>> cache = SimpleCache(max_size=1000)
        >>> cache.set("key", "value", ttl=60)
        >>> value = cache.get("key")
    """

    def __init__(self, max_size: int = 1000) -> None:
        """初始化缓存。

        Args:
            max_size: 最大缓存条目数
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

        logger.info(f"Cache initialized with max_size={max_size}")

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值。

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        with self.lock:
            entry = self.cache.get(key)

            if entry is None:
                self.misses += 1
                return None

            if entry.is_expired():
                # 清理过期条目
                del self.cache[key]
                self.misses += 1
                return None

            self.hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """设置缓存值。

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认5分钟
        """
        with self.lock:
            # 如果缓存已满，删除最旧的条目
            if len(self.cache) >= self.max_size and key not in self.cache:
                # 找到最老的条目
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k].created_at,
                )
                del self.cache[oldest_key]

            self.cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str) -> bool:
        """删除缓存值。

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> None:
        """清空缓存。"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息。

        Returns:
            统计信息字典
        """
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
            }

    def cleanup_expired(self) -> int:
        """清理过期条目。

        Returns:
            清理的条目数
        """
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self.cache[key]

            return len(expired_keys)


# 全局缓存实例
_global_cache: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """获取全局缓存实例。

    Returns:
        缓存实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = SimpleCache(max_size=1000)
    return _global_cache


def cached(ttl: int = 300, key_prefix: str = "") -> Callable:
    """缓存装饰器。

    Args:
        ttl: 过期时间（秒）
        key_prefix: 缓存键前缀

    Returns:
        装饰器函数

    Examples:
        >>> @cached(ttl=60, key_prefix="user_info")
        ... def get_user_info(user_id: str):
        ...     # ... 数据库查询 ...
        ...     return user_data
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 生成缓存键
            cache_key = _generate_cache_key(
                key_prefix or func.__name__,
                args,
                kwargs,
            )

            # 尝试从缓存获取
            cache = get_cache()
            cached_value = cache.get(cache_key)

            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # 缓存未命中，调用函数
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


def _generate_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """生成缓存键。

    Args:
        prefix: 键前缀
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        缓存键
    """
    # 将参数序列化为字符串
    args_str = json.dumps(args, default=str, sort_keys=True)
    kwargs_str = json.dumps(kwargs, default=str, sort_keys=True)

    # 计算哈希
    combined = f"{prefix}:{args_str}:{kwargs_str}"
    hash_value = hashlib.md5(combined.encode()).hexdigest()[:16]

    return f"{prefix}:{hash_value}"


class CacheDecorator:
    """缓存装饰器类（提供更灵活的配置）。"""

    def __init__(
        self,
        ttl: int = 300,
        key_prefix: str = "",
        skip_cache: Callable[..., bool] = None,
    ) -> None:
        """初始化缓存装饰器。

        Args:
            ttl: 过期时间（秒）
            key_prefix: 缓存键前缀
            skip_cache: 跳过缓存的判断函数
        """
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.skip_cache = skip_cache

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 检查是否跳过缓存
            if self.skip_cache and self.skip_cache(*args, **kwargs):
                return func(*args, **kwargs)

            # 生成缓存键
            cache_key = _generate_cache_key(
                self.key_prefix or func.__name__,
                args,
                kwargs,
            )

            # 尝试从缓存获取
            cache = get_cache()
            cached_value = cache.get(cache_key)

            if cached_value is not None:
                return cached_value

            # 缓存未命中，调用函数
            result = func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, result, self.ttl)

            return result

        return wrapper
