"""Mem0 记忆系统配置模块。

本模块负责配置 Mem0 客户端，包括向量数据库、Embedding 模型
和存储策略的设置。
"""

import os
from typing import Optional
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MemoryConfig(BaseSettings):
    """Mem0 记忆系统配置类。

    负责管理记忆系统的所有配置参数，包括向量数据库选择、
    Embedding 模型配置和存储路径。

    Attributes:
        enabled: 是否启用记忆系统
        vector_store: 向量存储类型 (faiss|pinecone|weaviate)
        embedding_model: Embedding 模型名称
        storage_path: 本地存储路径
        user_id: 当前用户ID（用于多用户隔离）

    Raises:
        ValueError: 配置参数无效时
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MEMORY_",
        case_sensitive=False,
        extra='ignore',  # 忽略额外的字段，避免与.env中的其他配置冲突
    )

    # 记忆系统开关
    enabled: bool = True

    # 向量存储配置
    vector_store: str = Field(
        default="faiss",
        description="向量存储类型: faiss, pinecone, weaviate",
    )

    # Embedding 模型配置
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="HuggingFace Embedding 模型",
    )
    embedding_dimension: int = Field(
        default=384,
        description="向量维度 (bge-small-en-v1.5 为 384)",
    )

    # 存储路径配置
    storage_path: str = Field(
        default="./data/memory",
        description="记忆数据存储路径",
    )
    database_path: str = Field(
        default="./data/memory/memories.db",
        description="SQLite 数据库路径",
    )

    # Mem0 API 配置（可选，用于云端版本）
    mem0_api_key: Optional[str] = Field(
        default=None,
        description="Mem0 Cloud API Key（可选）",
    )
    mem0_api_base: Optional[str] = Field(
        default=None,
        description="Mem0 Cloud API Base URL",
    )

    # 检索配置
    default_search_limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="默认检索数量上限",
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="相似度阈值（低于此值的检索结果将被过滤）",
    )

    # 反馈配置
    feedback_enabled: bool = True
    feedback_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="反馈评分阈值（Score < 0.8 触发重新优化）",
    )

    @field_validator('vector_store')
    @classmethod
    def validate_vector_store(cls, v: str) -> str:
        """验证向量存储类型。

        Args:
            v: 向量存储类型

        Returns:
            验证后的向量存储类型

        Raises:
            ValueError: 不支持的向量存储类型
        """
        allowed_stores = ['faiss', 'pinecone', 'weaviate', 'chroma']
        v_lower = v.lower()
        if v_lower not in allowed_stores:
            raise ValueError(
                f"Unsupported vector store: {v}. "
                f"Must be one of {allowed_stores}"
            )
        return v_lower

    @field_validator('storage_path', 'database_path')
    @classmethod
    def create_storage_dirs(cls, v: str) -> str:
        """创建存储目录。

        Args:
            v: 路径字符串

        Returns:
            绝对路径
        """
        path = Path(v).expanduser().absolute()
        if v.endswith('.db'):
            # 数据库文件，创建父目录
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # 存储目录，直接创建
            path.mkdir(parents=True, exist_ok=True)
        return str(path)


# 全局配置实例（单例模式）
_config: Optional[MemoryConfig] = None


def get_memory_config() -> MemoryConfig:
    """获取记忆系统配置实例（单例模式）。

    Returns:
        MemoryConfig: 配置实例

    Examples:
        >>> config = get_memory_config()
        >>> print(config.vector_store)
        'faiss'
    """
    global _config
    if _config is None:
        _config = MemoryConfig()
    return _config


def reset_memory_config() -> None:
    """重置记忆系统配置（主要用于测试）。"""
    global _config
    _config = None
