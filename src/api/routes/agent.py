"""Agent API 路由模块。

提供 Agent 对话和反馈的 REST API 接口。
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.agent.graph import run_agent
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["agent"],
    responses={404: {"description": "Not found"}},
)


# ==================== Request Models ====================


class ChatRequest(BaseModel):
    """对话请求模型。

    Attributes:
        user_id: 用户ID
        message: 用户消息
        config: 配置参数（可选）
    """

    user_id: str = Field(..., description="飞书用户ID")
    message: str = Field(..., min_length=1, max_length=5000, description="用户消息")
    config: Optional[dict] = Field(default=None, description="配置参数")


class FeedbackRequest(BaseModel):
    """反馈请求模型。

    Attributes:
        conversation_id: 对话ID
        feedback: 反馈内容
        score: 反馈评分
    """

    conversation_id: str = Field(..., description="对话ID")
    feedback: str = Field(..., description="反馈内容")
    score: float = Field(..., ge=0.0, le=1.0, description="反馈评分")


# ==================== Response Models ====================


class ChatResponse(BaseModel):
    """对话响应模型。

    Attributes:
        code: 状态码
        message: 响应消息
        data: 响应数据
    """

    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: dict = Field(default={}, description="响应数据")


class AgentResponse(BaseModel):
    """Agent 响应数据模型。

    Attributes:
        response: 响应内容
        intent: 识别的意图
        tool_used: 使用的工具
        tool_result: 工具执行结果
        memory_context: 记忆上下文
    """

    response: str = Field(..., description="响应内容")
    intent: str = Field(default="", description="识别的意图")
    tool_used: Optional[str] = Field(default=None, description="使用的工具")
    tool_result: Optional[dict] = Field(default=None, description="工具执行结果")
    memory_context: Optional[str] = Field(default=None, description="记忆上下文")


# ==================== API Endpoints ====================


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Agent 对话",
    description="与 Agent 进行对话，自动识别意图并执行相应操作。",
)
async def chat(request: ChatRequest):
    """Agent 对话端点。

    处理用户消息，通过 Agent 工作流生成响应。

    Args:
        request: 对话请求

    Returns:
        ChatResponse: 包含响应内容的响应

    Raises:
        HTTPException: 处理失败时
    """
    try:
        logger.info(
            f"Chat request from {request.user_id[:4]}***: "
            f"{request.message[:50]}..."
        )

        # 运行 Agent
        result = await run_agent(
            user_id=request.user_id,
            message=request.message,
            config=request.config,
        )

        # 检查错误
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        # 构建响应数据
        response_data = AgentResponse(
            response=result.get("response", ""),
            intent=str(result.get("intent", "")),
            tool_used=result.get("tool_name"),
            tool_result=result.get("tool_result"),
            memory_context=result.get("memory_context"),
        )

        logger.info(
            f"Chat response for {request.user_id[:4]}***: "
            f"{response_data.response[:50]}..."
        )

        return ChatResponse(
            code=0,
            message="Success",
            data=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post(
    "/feedback",
    response_model=ChatResponse,
    summary="Agent 反馈",
    description="提交对 Agent 响应的反馈，用于优化后续对话。",
)
async def feedback(request: FeedbackRequest):
    """Agent 反馈端点。

    处理用户对 Agent 响应的反馈。

    Args:
        request: 反馈请求

    Returns:
        ChatResponse: 操作结果

    Raises:
        HTTPException: 处理失败时
    """
    try:
        logger.info(
            f"Feedback for conversation {request.conversation_id}: "
            f"score={request.score:.2f}"
        )

        # TODO: 存储反馈到数据库或记忆系统
        # 当前为模拟实现

        return ChatResponse(
            code=0,
            message="Feedback received",
            data={
                "conversation_id": request.conversation,
                "score": request.score,
            },
        )

    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get(
    "/status",
    summary="Agent 状态",
    description="获取 Agent 系统状态。",
)
async def get_status():
    """获取 Agent 状态。

    Returns:
        dict: Agent 系统状态
    """
    return {
        "code": 0,
        "message": "Agent is running",
        "data": {
            "status": "healthy",
            "tools_enabled": True,
            "memory_enabled": True,
        },
    }
