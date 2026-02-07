"""
飞书日历 API 路由模块

提供日历事件的 REST API 接口，支持创建、查询、更新、删除事件。
所有端点都需要用户认证（通过 user_id）。

Author: Claude Code
Date: 2026-02-06
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field, ConfigDict
from loguru import logger

from src.integrations.feishu.calendar import FeishuCalendarClient, FeishuCalendarError
from src.integrations.feishu.client import FeishuClient


# ============ Pydantic 模型 ============
class CalendarEventCreate(BaseModel):
    """创建日历事件请求模型"""

    user_id: str = Field(..., description="用户 ID（飞书 user_id）")
    title: str = Field(..., min_length=1, max_length=200, description="事件标题")
    start_time: str = Field(..., description="开始时间（ISO 8601 格式）")
    end_time: str = Field(..., description="结束时间（ISO 8601 格式）")
    description: Optional[str] = Field(None, max_length=5000, description="事件描述")
    location: Optional[str] = Field(None, max_length=200, description="地点")
    attendees: Optional[List[str]] = Field(None, description="参与者 ID 列表")
    reminder_minutes: Optional[List[int]] = Field(
        None, description="提醒时间（分钟），如 [15, 60, 1440]"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "ou_xxx",
                "title": "项目周会",
                "start_time": "2026-02-07T15:00:00+08:00",
                "end_time": "2026-02-07T16:00:00+08:00",
                "description": "讨论本周进度和下周计划",
                "location": "会议室 A",
                "attendees": ["ou_yyy", "ou_zzz"],
                "reminder_minutes": [15, 60, 1440],
            }
        }
    )


class CalendarEventUpdate(BaseModel):
    """更新日历事件请求模型"""

    user_id: str = Field(..., description="用户 ID")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="新标题")
    start_time: Optional[str] = Field(None, description="新开始时间（ISO 8601 格式）")
    end_time: Optional[str] = Field(None, description="新结束时间（ISO 8601 格式）")
    description: Optional[str] = Field(None, max_length=5000, description="新描述")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "ou_xxx",
                "title": "更新后的标题",
                "description": "更新后的描述",
            }
        }
    )


class CalendarEventResponse(BaseModel):
    """日历事件响应模型"""

    success: bool = Field(..., description="是否成功")
    event_id: Optional[str] = Field(None, description="事件 ID")
    message: str = Field(..., description="响应消息")


class CalendarEventListParams(BaseModel):
    """列出事件查询参数"""

    user_id: str = Field(..., description="用户 ID")
    start_date: str = Field(..., description="开始日期（ISO 8601 格式）")
    end_date: str = Field(..., description="结束日期（ISO 8601 格式）")
    limit: int = Field(100, ge=1, le=1000, description="最大返回数量")


# ============ 路由定义 ============
router = APIRouter(prefix="/calendar", tags=["Calendar"])

# 全局飞书客户端实例（从依赖注入获取，这里暂时使用全局实例）
_feishu_client: Optional[FeishuClient] = None


def set_feishu_client(client: FeishuClient):
    """设置飞书客户端实例"""
    global _feishu_client
    _feishu_client = client
    logger.info("Feishu client initialized for calendar routes")


def _get_calendar_client() -> FeishuCalendarClient:
    """获取日历客户端实例"""
    if _feishu_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feishu client not initialized",
        )
    return FeishuCalendarClient(_feishu_client)


def _parse_datetime(dt_str: str) -> datetime:
    """解析 ISO 8601 时间字符串"""
    try:
        # 移除时区信息并解析
        if "T" in dt_str:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        else:
            return datetime.fromisoformat(dt_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid datetime format: {dt_str}. Expected ISO 8601 format.",
        )


# ============ API 端点 ============
@router.post(
    "/events",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建日历事件",
    description="在用户的主日历中创建新事件",
    responses={
        201: {"description": "事件创建成功"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"},
    },
)
async def create_event(event_data: CalendarEventCreate) -> CalendarEventResponse:
    """
    创建日历事件

    在用户的主日历中创建一个新事件，支持设置标题、时间、描述、地点、参与者和提醒。

    Args:
        event_data: 事件数据

    Returns:
        CalendarEventResponse: 创建结果，包含事件 ID

    Raises:
        HTTPException: 创建失败时抛出
    """
    try:
        logger.info(f"Creating calendar event: {event_data.title}")

        # 解析时间
        start_time = _parse_datetime(event_data.start_time)
        end_time = _parse_datetime(event_data.end_time)

        # 获取日历客户端
        calendar_client = _get_calendar_client()

        # 创建事件
        event_id = await calendar_client.create_event(
            user_id=event_data.user_id,
            title=event_data.title,
            start_time=start_time,
            end_time=end_time,
            description=event_data.description,
            location=event_data.location,
            attendes=event_data.attendees,
            reminder_minutes=event_data.reminder_minutes,
        )

        logger.info(f"Event created successfully: {event_id}")

        return CalendarEventResponse(
            success=True,
            event_id=event_id,
            message=f"Event '{event_data.title}' created successfully",
        )

    except FeishuCalendarError as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error creating event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/events/{event_id}",
    summary="获取日历事件",
    description="根据事件 ID 获取事件详情",
    responses={
        200: {"description": "获取成功"},
        404: {"description": "事件不存在"},
        500: {"description": "服务器内部错误"},
    },
)
async def get_event(
    event_id: str,
    user_id: str = Query(..., description="用户 ID"),
) -> dict:
    """
    获取日历事件

    根据事件 ID 获取事件的详细信息。

    Args:
        event_id: 事件 ID
        user_id: 用户 ID

    Returns:
        dict: 事件详情

    Raises:
        HTTPException: 获取失败时抛出
    """
    try:
        logger.info(f"Getting event: {event_id}")

        # 获取日历客户端
        calendar_client = _get_calendar_client()

        # 获取事件
        event = await calendar_client.get_event(user_id=user_id, event_id=event_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event not found: {event_id}",
            )

        logger.info(f"Event retrieved: {event_id}")

        return {
            "success": True,
            "event": event,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put(
    "/events/{event_id}",
    response_model=CalendarEventResponse,
    summary="更新日历事件",
    description="更新现有事件的部分字段",
    responses={
        200: {"description": "更新成功"},
        404: {"description": "事件不存在"},
        500: {"description": "服务器内部错误"},
    },
)
async def update_event(
    event_id: str,
    event_data: CalendarEventUpdate,
) -> CalendarEventResponse:
    """
    更新日历事件

    更新现有事件的标题、时间或描述。只更新提供的字段，未提供的字段保持不变。

    Args:
        event_id: 事件 ID
        event_data: 更新数据

    Returns:
        CalendarEventResponse: 更新结果

    Raises:
        HTTPException: 更新失败时抛出
    """
    try:
        logger.info(f"Updating event: {event_id}")

        # 获取日历客户端
        calendar_client = _get_calendar_client()

        # 解析时间（如果提供）
        start_time = (
            _parse_datetime(event_data.start_time) if event_data.start_time else None
        )
        end_time = (
            _parse_datetime(event_data.end_time) if event_data.end_time else None
        )

        # 更新事件
        success = await calendar_client.update_event(
            user_id=event_data.user_id,
            event_id=event_id,
            title=event_data.title,
            start_time=start_time,
            end_time=end_time,
            description=event_data.description,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update event",
            )

        logger.info(f"Event updated successfully: {event_id}")

        return CalendarEventResponse(
            success=True,
            event_id=event_id,
            message="Event updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete(
    "/events/{event_id}",
    response_model=CalendarEventResponse,
    summary="删除日历事件",
    description="删除指定的日历事件",
    responses={
        200: {"description": "删除成功"},
        404: {"description": "事件不存在"},
        500: {"description": "服务器内部错误"},
    },
)
async def delete_event(
    event_id: str,
    user_id: str = Query(..., description="用户 ID"),
) -> CalendarEventResponse:
    """
    删除日历事件

    根据事件 ID 删除事件。

    Args:
        event_id: 事件 ID
        user_id: 用户 ID

    Returns:
        CalendarEventResponse: 删除结果

    Raises:
        HTTPException: 删除失败时抛出
    """
    try:
        logger.info(f"Deleting event: {event_id}")

        # 获取日历客户端
        calendar_client = _get_calendar_client()

        # 删除事件
        success = await calendar_client.delete_event(
            user_id=user_id,
            event_id=event_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete event",
            )

        logger.info(f"Event deleted successfully: {event_id}")

        return CalendarEventResponse(
            success=True,
            event_id=event_id,
            message="Event deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/events",
    summary="列出日历事件",
    description="列出指定日期范围内的所有事件",
    responses={
        200: {"description": "获取成功"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"},
    },
)
async def list_events(
    user_id: str = Query(..., description="用户 ID"),
    start_date: str = Query(..., description="开始日期（ISO 8601 格式）"),
    end_date: str = Query(..., description="结束日期（ISO 8601 格式）"),
    limit: int = Query(100, ge=1, le=1000, description="最大返回数量"),
) -> dict:
    """
    列出日历事件

    查询指定日期范围内的所有事件，按开始时间排序。

    Args:
        user_id: 用户 ID
        start_date: 开始日期
        end_date: 结束日期
        limit: 最大返回数量

    Returns:
        dict: 事件列表

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        logger.info(f"Listing events for user {user_id[:4]}*** from {start_date} to {end_date}")

        # 解析日期
        start_dt = _parse_datetime(start_date)
        end_dt = _parse_datetime(end_date)

        # 获取日历客户端
        calendar_client = _get_calendar_client()

        # 列出事件
        events = await calendar_client.list_events(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
        )

        logger.info(f"Retrieved {len(events)} events")

        return {
            "success": True,
            "count": len(events),
            "events": events,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
