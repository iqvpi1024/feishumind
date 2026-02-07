"""
GitHub 路由

提供 GitHub Trending 相关的 API 端点。

Author: FeishuMind Team
Created: 2026-02-06
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.integrations.feishu.cards import FeishuCardBuilder
from src.integrations.github.client import GitHubClient
from src.integrations.github.models import GitHubPreferences, GitHubRepo, GitHubTrendingRequest
from src.memory.client import MemoryClient, get_memory_client
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/github", tags=["GitHub"])


# ============ 请求/响应模型 ============


class SetPreferencesRequest(BaseModel):
    """设置偏好请求"""

    user_id: str = Field(..., description="用户ID")
    languages: List[str] = Field(default_factory=list, description="关注的语言列表")
    push_time: str = Field("09:00", description="推送时间 (HH:MM)")
    push_enabled: bool = Field(True, description="是否启用推送")
    frequency: str = Field("daily", description="推送频率 (daily|weekly)")
    min_stars: int = Field(100, ge=0, description="最小星标数")
    limit: int = Field(5, ge=1, le=20, description="每次推送数量")


class ScheduleRequest(BaseModel):
    """定时任务请求"""

    user_id: str = Field(..., description="用户ID")
    enabled: bool = Field(..., description="是否启用")
    time: str = Field("09:00", description="推送时间 (HH:MM)")


class TrendingResponse(BaseModel):
    """Trending 响应"""

    repos: List[GitHubRepo]
    total: int
    period: str
    language: str | None = None


class PreferencesResponse(BaseModel):
    """偏好响应"""

    user_id: str
    languages: List[str]
    push_time: str
    push_enabled: bool
    frequency: str
    min_stars: int
    limit: int


# ============ 辅助函数 ============


async def _get_user_preferences(memory_client: MemoryClient, user_id: str) -> GitHubPreferences:
    """获取用户偏好

    Args:
        memory_client: 记忆客户端
        user_id: 用户ID

    Returns:
        用户偏好对象
    """
    try:
        # 从记忆中获取偏好
        memories = await memory_client.search_memory(
            query=f"github preferences {user_id}",
            limit=1,
            filters={"category": "github_pref"},
        )

        if memories and memories[0].get("metadata"):
            pref_data = memories[0]["metadata"]
            return GitHubPreferences(**pref_data)

        # 返回默认偏好
        return GitHubPreferences(user_id=user_id)

    except Exception as e:
        logger.warning(f"Failed to get user preferences: {e}, using defaults")
        return GitHubPreferences(user_id=user_id)


async def _save_user_preferences(
    memory_client: MemoryClient, preferences: GitHubPreferences
) -> str:
    """保存用户偏好

    Args:
        memory_client: 记忆客户端
        preferences: 偏好对象

    Returns:
        记忆ID
    """
    # 删除旧偏好
    try:
        old_memories = await memory_client.search_memory(
            query=f"github preferences {preferences.user_id}",
            limit=10,
            filters={"category": "github_pref"},
        )
        for mem in old_memories:
            await memory_client.delete_memory(mem["id"])
    except Exception as e:
        logger.warning(f"Failed to delete old preferences: {e}")

    # 保存新偏好
    memory_id = await memory_client.add_memory(
        content=f"GitHub trending preferences for {preferences.user_id}",
        category="github_pref",
        metadata=preferences.model_dump(),
    )

    return memory_id


# ============ API 端点 ============


@router.post("/preferences", response_model=dict, status_code=status.HTTP_200_OK)
async def set_preferences(
    request: SetPreferencesRequest,
    memory_client: MemoryClient = Depends(get_memory_client),
):
    """设置 GitHub Trending 偏好

    设置用户的 GitHub Trending 推送偏好，包括:
    - 关注的编程语言
    - 推送时间
    - 推送频率
    - 最小星标数过滤

    Args:
        request: 偏好设置请求
        memory_client: 记忆客户端

    Returns:
        设置结果
    """
    try:
        # 构建偏好对象
        preferences = GitHubPreferences(
            user_id=request.user_id,
            languages=request.languages,
            push_time=request.push_time,
            push_enabled=request.push_enabled,
            frequency=request.frequency,
            min_stars=request.min_stars,
            limit=request.limit,
        )

        # 保存到记忆系统
        memory_id = await _save_user_preferences(memory_client, preferences)

        logger.info(f"Saved GitHub preferences for user {request.user_id}")

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "memory_id": memory_id,
                "preferences": preferences.model_dump(),
            },
        }

    except Exception as e:
        logger.error(f"Failed to set preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set preferences: {str(e)}",
        )


@router.get("/preferences/{user_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def get_preferences(
    user_id: str,
    memory_client: MemoryClient = Depends(get_memory_client),
):
    """获取用户偏好

    获取用户的 GitHub Trending 推送偏好设置。

    Args:
        user_id: 用户ID
        memory_client: 记忆客户端

    Returns:
        用户偏好
    """
    try:
        preferences = await _get_user_preferences(memory_client, user_id)

        return {
            "code": 0,
            "msg": "success",
            "data": preferences.model_dump(),
        }

    except Exception as e:
        logger.error(f"Failed to get preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}",
        )


@router.get("/trending", response_model=dict, status_code=status.HTTP_200_OK)
async def get_trending(
    language: str | None = None,
    period: str = "daily",
    limit: int = 10,
    min_stars: int = 0,
):
    """获取 GitHub Trending

    获取 GitHub Trending 仓库列表，支持语言和时间周期过滤。

    Args:
        language: 编程语言过滤 (如: Python, JavaScript)
        period: 时间周期 (daily, weekly, monthly)
        limit: 返回数量限制 (1-50)
        min_stars: 最小星标数过滤

    Returns:
        Trending 仓库列表
    """
    try:
        # 创建请求对象
        request = GitHubTrendingRequest(
            language=language,
            period=period,
            limit=limit,
            min_stars=min_stars,
        )

        # 获取 Trending 数据
        client = GitHubClient()
        repos = await client.get_trending_repos(
            language=request.language,
            period=request.period,
            limit=request.limit,
        )

        # 过滤星标数
        if request.min_stars > 0:
            repos = [r for r in repos if r.stars >= request.min_stars]

        logger.info(f"Retrieved {len(repos)} trending repos")

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "repos": [r.model_dump() for r in repos],
                "total": len(repos),
                "period": period,
                "language": language,
            },
        }

    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get trending: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trending: {str(e)}",
        )


@router.post("/schedule", response_model=dict, status_code=status.HTTP_200_OK)
async def set_schedule(request: ScheduleRequest):
    """配置定时推送

    启用或禁用 GitHub Trending 定时推送。

    Args:
        request: 定时任务请求

    Returns:
        配置结果
    """
    try:
        # TODO: 实现实际的定时任务配置
        # 这里需要集成 TaskScheduler

        logger.info(
            f"User {request.user_id} set schedule: enabled={request.enabled}, time={request.time}"
        )

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "enabled": request.enabled,
                "time": request.time,
                "message": "定时任务配置成功（功能待完善）",
            },
        }

    except Exception as e:
        logger.error(f"Failed to set schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set schedule: {str(e)}",
        )


@router.get("/status/{user_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def get_status(
    user_id: str,
    memory_client: MemoryClient = Depends(get_memory_client),
):
    """获取推送状态

    获取用户的 GitHub Trending 推送状态。

    Args:
        user_id: 用户ID
        memory_client: 记忆客户端

    Returns:
        推送状态信息
    """
    try:
        # 获取用户偏好
        preferences = await _get_user_preferences(memory_client, user_id)

        # TODO: 获取下次推送时间 (需要从 scheduler 获取)

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "user_id": user_id,
                "push_enabled": preferences.push_enabled,
                "push_time": preferences.push_time,
                "frequency": preferences.frequency,
                "languages": preferences.languages,
                "next_push_time": f"每日 {preferences.push_time}",  # 简化版
            },
        }

    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}",
        )


@router.post("/test-card", response_model=dict, status_code=status.HTTP_200_OK)
async def test_card(language: str = "Python", period: str = "daily"):
    """测试卡片生成

    生成测试用的飞书卡片消息，用于调试卡片格式。

    Args:
        language: 测试语言
        period: 测试周期

    Returns:
        飞书卡片消息
    """
    try:
        # 创建模拟仓库数据
        mock_repos = [
            GitHubRepo(
                repo_id="test/repo1",
                name="repo1",
                full_name="test/repo1",
                description="这是一个测试仓库",
                language=language,
                stars=1000,
                forks=100,
                url="https://github.com/test/repo1",
                owner="test",
            ),
            GitHubRepo(
                repo_id="test/repo2",
                name="repo2",
                full_name="test/repo2",
                description="这是另一个测试仓库",
                language=language,
                stars=500,
                forks=50,
                url="https://github.com/test/repo2",
                owner="test",
            ),
        ]

        # 生成卡片
        card = FeishuCardBuilder.create_github_trending_card(mock_repos, period)

        return {
            "code": 0,
            "msg": "success",
            "data": card,
        }

    except Exception as e:
        logger.error(f"Failed to generate test card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test card: {str(e)}",
        )
