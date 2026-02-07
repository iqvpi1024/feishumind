"""记忆管理 API 路由模块。

提供记忆的增删改查 REST API 接口。
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from src.memory.client import MemoryClient, get_memory_client
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/memory",
    tags=["memory"],
    responses={404: {"description": "Not found"}},
)


# ==================== Request Models ====================


class AddMemoryRequest(BaseModel):
    """添加记忆请求模型。

    Attributes:
        user_id: 用户ID
        content: 记忆内容
        category: 记忆类别 (preference|emotion|event)
        metadata: 额外元数据
    """

    user_id: str = Field(..., description="飞书用户ID")
    content: str = Field(..., min_length=1, max_length=5000, description="记忆内容")
    category: str = Field(
        default="preference",
        description="记忆类别: preference, emotion, event",
    )
    metadata: Optional[dict] = Field(default=None, description="额外元数据")

    @field_validator('category')
    @classmethod
    def category_valid(cls, v: str) -> str:
        """验证类别有效。

        Args:
            v: 类别字符串

        Returns:
            验证后的类别

        Raises:
            ValueError: 类别无效
        """
        allowed = ['preference', 'emotion', 'event']
        if v not in allowed:
            raise ValueError(f'Category must be one of {allowed}')
        return v


class SearchMemoryRequest(BaseModel):
    """搜索记忆请求模型。

    Attributes:
        user_id: 用户ID
        query: 查询内容
        category: 过滤类别（可选）
        limit: 返回数量上限
        threshold: 相似度阈值
    """

    user_id: str = Field(..., description="飞书用户ID")
    query: str = Field(..., min_length=1, max_length=500, description="查询内容")
    category: Optional[str] = Field(
        default=None,
        description="过滤类别: preference, emotion, event",
    )
    limit: int = Field(default=10, ge=1, le=50, description="返回数量上限")
    threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="相似度阈值",
    )


class FeedbackRequest(BaseModel):
    """反馈评分请求模型。

    Attributes:
        feedback_score: 反馈评分 (0.0-1.0)
    """

    feedback_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="反馈评分",
    )


# ==================== Response Models ====================


class AddMemoryResponse(BaseModel):
    """添加记忆响应模型。

    Attributes:
        code: 状态码
        message: 响应消息
        data: 响应数据
    """

    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: dict = Field(default={"memory_id": ""}, description="记忆ID")


class MemoryItem(BaseModel):
    """记忆项模型。

    Attributes:
        memory_id: 记忆ID
        memory: 记忆内容
        score: 相似度分数
        category: 记忆类别
        created_at: 创建时间
        metadata: 元数据
    """

    memory_id: str = Field(..., description="记忆ID")
    memory: str = Field(..., description="记忆内容")
    score: float = Field(..., description="相似度分数")
    category: str = Field(..., description="记忆类别")
    created_at: str = Field(..., description="创建时间")
    metadata: dict = Field(default={}, description="元数据")


class SearchMemoryResponse(BaseModel):
    """搜索记忆响应模型。

    Attributes:
        code: 状态码
        message: 响应消息
        data: 记忆列表
    """

    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: List[MemoryItem] = Field(default=[], description="记忆列表")


class FeedbackResponse(BaseModel):
    """反馈评分响应模型。

    Attributes:
        code: 状态码
        message: 响应消息
        data: 响应数据
    """

    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: dict = Field(default={}, description="响应数据")


# ==================== API Endpoints ====================


@router.post(
    "",
    response_model=AddMemoryResponse,
    summary="添加记忆",
    description="添加一条新的用户记忆，支持偏好、情绪、事件三类。",
)
async def add_memory(
    request: AddMemoryRequest,
    client: MemoryClient = Depends(get_memory_client),
):
    """添加记忆。

    Args:
        request: 添加记忆请求
        client: 记忆客户端（依赖注入）

    Returns:
        AddMemoryResponse: 包含记忆ID的响应

    Raises:
        HTTPException: 添加失败时
    """
    try:
        memory_id = await client.add_memory(
            user_id=request.user_id,
            content=request.content,
            category=request.category,
            metadata=request.metadata,
        )

        return AddMemoryResponse(
            code=0,
            message="Memory added successfully",
            data={"memory_id": memory_id},
        )

    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get(
    "/search",
    response_model=SearchMemoryResponse,
    summary="搜索记忆",
    description="根据查询内容搜索用户记忆，支持语义检索。",
)
async def search_memory(
    user_id: str,
    query: str,
    category: Optional[str] = None,
    limit: int = 10,
    threshold: Optional[float] = None,
    client: MemoryClient = Depends(get_memory_client),
):
    """搜索记忆。

    Args:
        user_id: 用户ID
        query: 查询内容
        category: 过滤类别（可选）
        limit: 返回数量上限
        threshold: 相似度阈值
        client: 记忆客户端（依赖注入）

    Returns:
        SearchMemoryResponse: 包含记忆列表的响应

    Raises:
        HTTPException: 搜索失败时
    """
    try:
        memories = await client.search_memory(
            user_id=user_id,
            query=query,
            category=category,
            limit=limit,
            threshold=threshold,
        )

        # 转换为响应模型
        memory_items = [
            MemoryItem(**mem) for mem in memories
        ]

        return SearchMemoryResponse(
            code=0,
            message=f"Found {len(memory_items)} memories",
            data=memory_items,
        )

    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to search memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.put(
    "/{memory_id}/feedback",
    response_model=FeedbackResponse,
    summary="反馈评分",
    description="对记忆进行反馈评分，影响后续检索权重。",
)
async def update_feedback(
    memory_id: str,
    request: FeedbackRequest,
    client: MemoryClient = Depends(get_memory_client),
):
    """更新记忆反馈评分。

    Args:
        memory_id: 记忆ID
        request: 反馈评分请求
        client: 记忆客户端（依赖注入）

    Returns:
        FeedbackResponse: 操作结果

    Raises:
        HTTPException: 更新失败时
    """
    try:
        success = await client.update_memory(
            memory_id=memory_id,
            feedback_score=request.feedback_score,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory {memory_id} not found",
            )

        return FeedbackResponse(
            code=0,
            message="Feedback updated successfully",
            data={
                "memory_id": memory_id,
                "feedback_score": request.feedback_score,
            },
        )

    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to update feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get(
    "/user/{user_id}",
    response_model=SearchMemoryResponse,
    summary="获取用户所有记忆",
    description="获取指定用户的所有记忆记录。",
)
async def get_all_memories(
    user_id: str,
    category: Optional[str] = None,
    client: MemoryClient = Depends(get_memory_client),
):
    """获取用户所有记忆。

    Args:
        user_id: 用户ID
        category: 过滤类别（可选）
        client: 记忆客户端（依赖注入）

    Returns:
        SearchMemoryResponse: 所有记忆列表

    Raises:
        HTTPException: 获取失败时
    """
    try:
        memories = await client.get_all_memories(
            user_id=user_id,
            category=category,
        )

        # 转换为响应模型（添加默认分数）
        memory_items = [
            MemoryItem(
                memory_id=mem.get("id", ""),
                memory=mem.get("memory", ""),
                score=1.0,  # 默认分数
                category=mem.get("metadata", {}).get("category", ""),
                created_at=mem.get("metadata", {}).get("created_at", ""),
                metadata=mem.get("metadata", {}),
            )
            for mem in memories
        ]

        return SearchMemoryResponse(
            code=0,
            message=f"Retrieved {len(memory_items)} memories",
            data=memory_items,
        )

    except Exception as e:
        logger.error(f"Failed to get memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.delete(
    "/{memory_id}",
    summary="删除记忆",
    description="删除指定的记忆记录。",
)
async def delete_memory(
    memory_id: str,
    client: MemoryClient = Depends(get_memory_client),
):
    """删除记忆。

    Args:
        memory_id: 记忆ID
        client: 记忆客户端（依赖注入）

    Returns:
        dict: 操作结果

    Raises:
        HTTPException: 删除失败时
    """
    try:
        success = await client.delete_memory(memory_id=memory_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory {memory_id} not found",
            )

        return {
            "code": 0,
            "message": "Memory deleted successfully",
            "data": {"memory_id": memory_id},
        }

    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
