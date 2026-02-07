"""
GitHub 数据模型

定义 GitHub Trending 相关的数据结构。

Author: FeishuMind Team
Created: 2026-02-06
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_serializer


class GitHubRepo(BaseModel):
    """
    GitHub 仓库模型

    表示一个 GitHub 仓库的详细信息。

    Attributes:
        repo_id: 仓库唯一标识
        name: 仓库名称 (owner/repo)
        full_name: 完整仓库名称
        description: 仓库描述
        language: 主要编程语言
        stars: 星标数
        forks: 分支数
        url: 仓库 URL
        owner: 所有者名称
        avatar_url: 所有者头像 URL
        created_at: 创建时间
        updated_at: 更新时间
    """

    repo_id: str = Field(..., description="仓库唯一标识")
    name: str = Field(..., description="仓库名称")
    full_name: str = Field(..., description="完整仓库名称")
    description: Optional[str] = Field(None, description="仓库描述")
    language: Optional[str] = Field(None, description="主要编程语言")
    stars: int = Field(0, description="星标数")
    forks: int = Field(0, description="分支数")
    url: str = Field(..., description="仓库 URL")
    owner: str = Field(..., description="所有者名称")
    avatar_url: Optional[str] = Field(None, description="所有者头像 URL")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """序列化日期时间为 ISO 格式。

        Args:
            dt: 日期时间对象

        Returns:
            ISO 格式的日期时间字符串，如果为 None 则返回 None
        """
        return dt.isoformat() if dt else None


class GitHubTrendingRequest(BaseModel):
    """
    GitHub Trending 请求模型

    用于获取 Trending 仓库的请求参数。

    Attributes:
        language: 编程语言过滤 (如: Python, JavaScript)
        period: 时间周期 (daily, weekly, monthly)
        limit: 返回数量限制
        min_stars: 最小星标数过滤
    """

    language: Optional[str] = Field(None, description="编程语言过滤")
    period: str = Field("daily", description="时间周期 (daily|weekly|monthly)")
    limit: int = Field(10, ge=1, le=50, description="返回数量限制")
    min_stars: int = Field(0, ge=0, description="最小星标数过滤")


class GitHubPreferences(BaseModel):
    """
    GitHub 用户偏好模型

    存储用户的 GitHub 推送偏好设置。

    Attributes:
        user_id: 用户 ID
        languages: 关注的语言列表
        push_time: 推送时间 (HH:MM 格式)
        push_enabled: 是否启用推送
        frequency: 推送频率 (daily, weekly)
        min_stars: 最小星标数
        limit: 每次推送数量
    """

    user_id: str = Field(..., description="用户 ID")
    languages: List[str] = Field(default_factory=list, description="关注的语言列表")
    push_time: str = Field("09:00", description="推送时间 (HH:MM)")
    push_enabled: bool = Field(True, description="是否启用推送")
    frequency: str = Field("daily", description="推送频率 (daily|weekly)")
    min_stars: int = Field(100, ge=0, description="最小星标数")
    limit: int = Field(5, ge=1, le=20, description="每次推送数量")
