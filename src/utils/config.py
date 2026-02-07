"""
配置管理模块

本模块负责从环境变量和配置文件中加载应用配置。

使用 Pydantic Settings 进行类型安全的配置管理。
所有配置项都有默认值，可通过环境变量覆盖。

Author: FeishuMind Team
Created: 2026-02-06
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类

    所有配置项都通过环境变量加载，使用 Pydantic 进行类型验证。
    如果环境变量未设置，使用默认值。

    Attributes:
        model_config: Pydantic 配置
        APP_NAME: 应用名称
        DEBUG: 调试模式
        VERSION: 应用版本
        ENVIRONMENT: 运行环境
        HOST: 服务器主机地址
        PORT: 服务器端口
        ALLOWED_ORIGINS: CORS 允许的源列表
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # 忽略未定义的环境变量
    )

    # ============ 应用基础配置 ============
    APP_NAME: str = Field(default="FeishuMind", description="应用名称")
    DEBUG: bool = Field(default=False, description="调试模式")
    VERSION: str = Field(default="1.0.0", description="应用版本")
    ENVIRONMENT: str = Field(default="development", description="运行环境")

    # ============ 服务器配置 ============
    HOST: str = Field(default="0.0.0.0", description="服务器主机地址")
    PORT: int = Field(default=8000, description="服务器端口")

    # ============ 飞书配置 ============
    FEISHU_APP_ID: str = Field(default="", description="飞书应用ID")
    FEISHU_APP_SECRET: str = Field(default="", description="飞书应用密钥")
    FEISHU_VERIFICATION_TOKEN: str = Field(default="", description="飞书验证令牌")
    FEISHU_ENCRYPT_KEY: str = Field(default="", description="飞书加密密钥")
    FEISHU_API_BASE_URL: str = Field(
        default="https://open.feishu.cn", description="飞书API基础URL"
    )

    # ============ AI 模型配置 ============
    CLAUDE_API_KEY: str = Field(default="", description="Claude API密钥")
    CLAUDE_MODEL: str = Field(
        default="claude-3-5-sonnet-20241022", description="Claude模型名称"
    )
    MAX_TOKENS_PER_USER: int = Field(default=5000, description="每用户最大Token数")

    # ============ 记忆层配置 ============
    MEM0_API_KEY: str = Field(default="", description="Mem0 API密钥")
    MEM0_BASE_URL: str = Field(
        default="https://api.mem0.ai", description="Mem0 API基础URL"
    )
    VECTOR_DB: str = Field(default="faiss", description="向量数据库类型")
    EMBEDDING_MODEL: str = Field(
        default="BAAI/bge-small-zh-v1.5", description="嵌入模型"
    )

    # ============ 数据库配置 ============
    DATABASE_URL: str = Field(
        default="sqlite:///./feishumind.db", description="数据库连接URL"
    )

    # ============ Redis 配置 ============
    REDIS_HOST: str = Field(default="localhost", description="Redis主机")
    REDIS_PORT: int = Field(default=6379, description="Redis端口")
    REDIS_PASSWORD: str = Field(default="", description="Redis密码")
    REDIS_DB: int = Field(default=0, description="Redis数据库编号")

    # ============ 安全配置 ============
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-this-in-production",
        description="JWT密钥"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT算法")
    JWT_EXPIRATION: int = Field(default=3600, description="JWT过期时间（秒）")

    # ============ CORS 配置 ============
    ALLOWED_ORIGINS: List[str] = Field(
        default=["https://open.feishu.cn", "http://localhost:3000"],
        description="允许的CORS源"
    )

    # ============ 日志配置 ============
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="logs/feishumind.log", description="日志文件路径")

    # ============ 功能开关 ============
    ENABLE_PROACTIVE_MODE: bool = Field(default=True, description="启用主动模式")
    ENABLE_HUMAN_APPROVAL: bool = Field(default=True, description="启用人工确认")
    ENABLE_EMOTION_TRACKING: bool = Field(default=True, description="启用情绪追踪")


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例

    使用 lru_cache 确保配置只加载一次。
    后续调用返回缓存的配置对象。

    Returns:
        Settings: 应用配置对象
    """
    return Settings()


# 导出配置实例
settings = get_settings()
