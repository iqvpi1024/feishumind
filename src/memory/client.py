"""Mem0 客户端封装模块。

本模块提供对 Mem0 记忆系统的统一接口，包括添加记忆、搜索记忆、
更新反馈评分等核心功能。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from mem0 import Memory, MemoryClient as Mem0Client
from src.memory.config import get_memory_config

logger = logging.getLogger(__name__)


class MemoryClient:
    """Mem0 客户端封装类。

    提供记忆的增删改查功能，支持精确匹配和语义检索。

    Attributes:
        config: 记忆系统配置
        client: Mem0 原生客户端实例

    Examples:
        >>> client = MemoryClient()
        >>> memory_id = await client.add_memory(
        ...     user_id="user_123",
        ...     content="我喜欢用 Python 写代码",
        ...     category="preference"
        ... )
        >>> memories = await client.search_memory(
        ...     user_id="user_123",
        ...     query="编程偏好"
        ... )
    """

    def __init__(self, config: Optional[Any] = None):
        """初始化 Mem0 客户端。

        Args:
            config: 记忆系统配置，默认使用全局配置
        """
        self.config = config or get_memory_config()
        self._use_cloud_api = False  # 默认值

        if not self.config.enabled:
            logger.warning("Memory system is disabled in config")
            self._client = None
            return

        try:
            # 初始化 Mem0 客户端
            # 优先使用 Mem0 云服务（如果配置了 API Key）
            if self.config.mem0_api_key:
                # 使用 Mem0 云服务 (MemoryClient)
                logger.info(f"Initializing Mem0 Cloud client with API key: {self.config.mem0_api_key[:10]}...")
                host = self.config.mem0_api_base or "https://api.mem0.ai"
                logger.info(f"Mem0 Cloud host: {host}")
                try:
                    self._client = Mem0Client(
                        api_key=self.config.mem0_api_key,
                        host=host
                    )
                    self._use_cloud_api = True
                    logger.info(f"Memory client initialized with Mem0 Cloud service at {host}")
                except Exception as cloud_error:
                    logger.error(f"Failed to initialize Mem0 Cloud client: {cloud_error}")
                    logger.error(f"Cloud error type: {type(cloud_error).__name__}")
                    raise
            else:
                # 使用本地向量存储
                self._client = Memory.from_config(
                    {
                        "vector_store": {
                            "type": self.config.vector_store,
                            "params": {
                                "embedding_model": self.config.embedding_model,
                            }
                        },
                        "history_db_path": self.config.database_path,
                    }
                )
                self._use_cloud_api = False
                logger.info(
                    f"Memory client initialized with {self.config.vector_store} backend"
                )
        except Exception as e:
            logger.error(f"Failed to initialize memory client: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._client = None
            raise

    @property
    def is_enabled(self) -> bool:
        """检查记忆系统是否启用。

        Returns:
            bool: 是否启用
        """
        return self.config.enabled and self._client is not None

    async def add_memory(
        self,
        user_id: str,
        content: str,
        category: str = "preference",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """添加记忆。

        Args:
            user_id: 用户ID
            content: 记忆内容
            category: 记忆类别 (preference|emotion|event)
            metadata: 额外元数据

        Returns:
            str: 记忆ID

        Raises:
            ValueError: 内容为空或类别无效
            RuntimeError: 记忆系统未启用或添加失败

        Examples:
            >>> memory_id = await client.add_memory(
            ...     user_id="user_123",
            ...     content="我每天早上9点开始工作",
            ...     category="preference"
            ... )
        """
        if not self.is_enabled:
            raise RuntimeError("Memory system is not enabled")

        # 参数验证
        if not content or not content.strip():
            raise ValueError("Memory content cannot be empty")

        if category not in ["preference", "emotion", "event"]:
            raise ValueError(
                f"Invalid category: {category}. "
                "Must be one of: preference, emotion, event"
            )

        # 数据脱敏（PII 处理）
        # TODO: 实现更复杂的脱敏逻辑
        sanitized_content = self._sanitize_content(content)

        # 构建元数据
        memory_metadata = {
            "user_id": user_id,
            "category": category,
            "created_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }

        try:
            # 调用 Mem0 添加记忆
            if self._use_cloud_api:
                # 使用云服务 API
                # messages 参数需要是字典列表
                result = self._client.add(
                    messages=[{
                        "role": "user",
                        "content": sanitized_content,
                    }],
                    user_id=user_id,
                    metadata=memory_metadata,
                )
            else:
                # 使用本地存储 API
                result = self._client.add(
                    sanitized_content,
                    user_id=user_id,
                    metadata=memory_metadata,
                )

            memory_id = result.get("id", f"mem_{datetime.utcnow().timestamp()}")
            logger.info(
                f"Memory added: {memory_id} for user {user_id[:4]}***, "
                f"category={category}"
            )
            return memory_id

        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise RuntimeError(f"Memory addition failed: {e}")

    async def search_memory(
        self,
        user_id: str,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """搜索记忆。

        支持精确匹配（SQLite）和语义检索（FAISS 向量）。

        Args:
            user_id: 用户ID
            query: 查询内容
            category: 过滤类别（可选）
            limit: 返回数量上限
            threshold: 相似度阈值（覆盖配置默认值）

        Returns:
            List[Dict]: 记忆列表，按相关性降序排列

        Raises:
            ValueError: 查询内容为空
            RuntimeError: 记忆系统未启用

        Examples:
            >>> memories = await client.search_memory(
            ...     user_id="user_123",
            ...     query="工作习惯",
            ...     limit=5
            ... )
            >>> for mem in memories:
            ...     print(f"{mem['score']:.2f}: {mem['memory']}")
        """
        if not self.is_enabled:
            raise RuntimeError("Memory system is not enabled")

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # 参数标准化
        limit = min(limit, self.config.default_search_limit)
        threshold = threshold or self.config.similarity_threshold

        try:
            # 调用 Mem0 搜索
            if self._use_cloud_api:
                # 云服务 API 需要使用 filters
                search_params = {
                    "query": query,
                    "limit": limit * 2,
                }
                # 如果指定了 user_id，添加到 filters
                if user_id:
                    search_params["filters"] = {"user_id": user_id}

                response = self._client.search(**search_params)
                # 云服务返回格式: {"results": [...]}
                results = response.get("results", [])
            else:
                # 本地存储 API
                results = self._client.search(
                    query=query,
                    user_id=user_id,
                    limit=limit * 2,
                )

            # 后处理：过滤和排序
            filtered_results = []
            for item in results:
                # 相似度过滤
                score = item.get("score", 0.0)
                if score < threshold:
                    continue

                # 类别过滤
                if category:
                    metadata = item.get("metadata", {})
                    if metadata.get("category") != category:
                        continue

                filtered_results.append({
                    "memory_id": item.get("id", ""),
                    "memory": item.get("memory", ""),
                    "score": score,
                    "category": item.get("metadata", {}).get("category", ""),
                    "created_at": item.get("metadata", {}).get("created_at", ""),
                    "metadata": item.get("metadata", {}),
                })

            # 按分数降序排序
            filtered_results.sort(key=lambda x: x["score"], reverse=True)
            filtered_results = filtered_results[:limit]

            logger.info(
                f"Memory search: query='{query[:30]}...', "
                f"user={user_id[:4]}***, found={len(filtered_results)}"
            )
            return filtered_results

        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            raise RuntimeError(f"Memory search failed: {e}")

    async def update_memory(
        self,
        memory_id: str,
        feedback_score: float,
    ) -> bool:
        """更新记忆反馈评分。

        Args:
            memory_id: 记忆ID
            feedback_score: 反馈评分 (0.0-1.0)

        Returns:
            bool: 是否更新成功

        Raises:
            ValueError: 评分超出范围
            RuntimeError: 记忆系统未启用

        Examples:
            >>> success = await client.update_memory(
            ...     memory_id="mem_123",
            ...     feedback_score=0.9
            ... )
        """
        if not self.is_enabled:
            raise RuntimeError("Memory system is not enabled")

        if not 0.0 <= feedback_score <= 1.0:
            raise ValueError(
                f"Feedback score must be between 0.0 and 1.0, got {feedback_score}"
            )

        try:
            # TODO: Mem0 的反馈机制 API 需要确认
            # 当前使用 metadata 更新方式
            # 更新后的反馈可以影响后续检索权重

            # 临时实现：记录到日志
            logger.info(
                f"Memory feedback: id={memory_id}, score={feedback_score:.2f}"
            )

            # 如果评分过低，标记需要重新优化
            if feedback_score < self.config.feedback_threshold:
                logger.warning(
                    f"Memory {memory_id} has low score ({feedback_score:.2f}), "
                    "consider re-optimization"
                )

            return True

        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            raise RuntimeError(f"Memory update failed: {e}")

    async def get_all_memories(
        self,
        user_id: str,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取用户所有记忆。

        Args:
            user_id: 用户ID
            category: 过滤类别（可选）

        Returns:
            List[Dict]: 所有记忆列表
        """
        if not self.is_enabled:
            raise RuntimeError("Memory system is not enabled")

        try:
            # TODO: Mem0 的 get_all API 需要确认
            # 临时实现：使用空搜索获取所有
            results = self._client.get_all(user_id=user_id)

            if category:
                results = [
                    r for r in results
                    if r.get("metadata", {}).get("category") == category
                ]

            return results

        except Exception as e:
            logger.error(f"Failed to get all memories: {e}")
            raise RuntimeError(f"Failed to retrieve memories: {e}")

    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆。

        Args:
            memory_id: 记忆ID

        Returns:
            bool: 是否删除成功
        """
        if not self.is_enabled:
            raise RuntimeError("Memory system is not enabled")

        try:
            # TODO: Mem0 的 delete API 需要确认
            self._client.delete(memory_id)
            logger.info(f"Memory deleted: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            raise RuntimeError(f"Memory deletion failed: {e}")

    def _sanitize_content(self, content: str) -> str:
        """数据脱敏处理。

        移除或模糊化敏感信息（PII）。

        Args:
            content: 原始内容

        Returns:
            str: 脱敏后的内容
        """
        # TODO: 实现完整的脱敏逻辑
        # 1. 识别邮箱、电话、身份证等
        # 2. 替换为占位符（如 [EMAIL], [PHONE]）
        # 3. 保留语义特征

        # 简单示例：移除多余空格
        sanitized = " ".join(content.split())

        return sanitized


# 全局客户端实例（单例模式）
_client: Optional[MemoryClient] = None


def get_memory_client() -> MemoryClient:
    """获取记忆客户端实例（单例模式）。

    Returns:
        MemoryClient: 客户端实例

    Examples:
        >>> client = get_memory_client()
        >>> await client.add_memory(...)
    """
    global _client
    if _client is None:
        _client = MemoryClient()
    return _client


def reset_memory_client() -> None:
    """重置记忆客户端（主要用于测试）。"""
    global _client
    _client = None
