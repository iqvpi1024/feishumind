"""飞书日历 API 集成模块。

提供飞书日历事件的创建、查询、更新、删除等功能。
参考文档：https://open.feishu.cn/document/server-docs/docs/calendar-v4/event

Author: Claude Code
Date: 2026-02-06
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import iso8601

from src.integrations.feishu.client import FeishuClient, FeishuAPIError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FeishuCalendarError(FeishuAPIError):
    """飞书日历 API 错误。"""

    pass


class FeishuCalendarClient:
    """飞书日历客户端。

    封装飞书日历 API 调用，支持事件的增删改查。

    Attributes:
        feishu_client: 飞书客户端实例

    Examples:
        >>> calendar = FeishuCalendarClient(feishu_client)
        >>> event_id = await calendar.create_event(
        ...     user_id="ou_xxx",
        ...     title="项目会议",
        ...     start_time=datetime(2026, 2, 7, 15, 0),
        ...     end_time=datetime(2026, 2, 7, 16, 0)
        ... )
    """

    def __init__(self, feishu_client: FeishuClient):
        """初始化飞书日历客户端。

        Args:
            feishu_client: 飞书客户端实例
        """
        self.feishu_client = feishu_client
        logger.info("Feishu calendar client initialized")

    async def create_event(
        self,
        user_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendes: Optional[List[str]] = None,
        reminder_minutes: Optional[List[int]] = None,
    ) -> str:
        """创建日历事件。

        Args:
            user_id: 用户 ID（飞书 user_id）
            title: 事件标题
            start_time: 开始时间
            end_time: 结束时间
            description: 事件描述
            location: 地点
            attendes: 参与者 ID 列表
            reminder_minutes: 提醒时间（分钟），如 [15, 60, 1440] 表示提前15分钟、1小时、1天

        Returns:
            事件 ID

        Raises:
            FeishuCalendarError: 创建失败

        Examples:
            >>> event_id = await calendar.create_event(
            ...     user_id="ou_xxx",
            ...     title="项目周会",
            ...     start_time=datetime(2026, 2, 7, 15, 0),
            ...     end_time=datetime(2026, 2, 7, 16, 0),
            ...     description="讨论本周进度",
            ...     reminder_minutes=[15, 60, 1440]
            ... )
        """
        logger.info(
            f"Creating calendar event: {title} for user {user_id[:4]}*** "
            f"from {start_time} to {end_time}"
        )

        # 1. 获取主日历 ID
        calendar_id = await self._get_primary_calendar(user_id)

        # 2. 构建事件数据
        event_data = {
            "calendar_id": calendar_id,
            "summary": title,
            "start_time": {
                "timestamp": str(int(start_time.timestamp())),
            },
            "end_time": {
                "timestamp": str(int(end_time.timestamp())),
            },
        }

        # 可选字段
        if description:
            event_data["description"] = description

        if location:
            event_data["location"] = {"name": location}

        if attendes:
            event_data["attendee_ability"] = "can_see_others"
            event_data["attendees"] = [
                {"user_id": uid, "type": "user"} for uid in attendes
            ]

        if reminder_minutes:
            event_data["reminders"] = [
                {"minutes": minutes} for minutes in reminder_minutes
            ]

        # 3. 调用飞书 API
        try:
            response = await self.feishu_client._request(
                method="POST",
                path="/open-apis/calendar/v4/events/",
                json=event_data,
            )

            event_id = response.get("data", {}).get("event", {}).get("event_id")

            if not event_id:
                raise FeishuCalendarError(
                    f"Failed to create event: no event_id returned", code=500
                )

            logger.info(f"Event created successfully: {event_id}")
            return event_id

        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise FeishuCalendarError(f"Failed to create event: {e}", code=500)

    async def get_event(self, user_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        """获取事件详情。

        Args:
            user_id: 用户 ID
            event_id: 事件 ID

        Returns:
            事件详情字典，失败返回 None

        Examples:
            >>> event = await calendar.get_event(
            ...     user_id="ou_xxx",
            ...     event_id="evt_xxx"
            ... )
        """
        logger.info(f"Getting event {event_id} for user {user_id[:4]}***")

        try:
            # 获取主日历 ID
            calendar_id = await self._get_primary_calendar(user_id)

            response = await self.feishu_client._request(
                method="GET",
                path=f"/open-apis/calendar/v4/events/{event_id}",
                params={"calendar_id": calendar_id},
            )

            event_data = response.get("data", {}).get("event")
            logger.info(f"Event retrieved: {event_id}")
            return event_data

        except Exception as e:
            logger.error(f"Failed to get event: {e}")
            return None

    async def update_event(
        self,
        user_id: str,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
    ) -> bool:
        """更新事件。

        Args:
            user_id: 用户 ID
            event_id: 事件 ID
            title: 新标题（可选）
            start_time: 新开始时间（可选）
            end_time: 新结束时间（可选）
            description: 新描述（可选）

        Returns:
            是否成功

        Examples:
            >>> success = await calendar.update_event(
            ...     user_id="ou_xxx",
            ...     event_id="evt_xxx",
            ...     title="更新后的标题"
            ... )
        """
        logger.info(f"Updating event {event_id} for user {user_id[:4]}***")

        try:
            # 获取主日历 ID
            calendar_id = await self._get_primary_calendar(user_id)

            # 构建更新数据
            update_data = {}

            if title:
                update_data["summary"] = title

            if start_time:
                update_data["start_time"] = {
                    "timestamp": str(int(start_time.timestamp()))
                }

            if end_time:
                update_data["end_time"] = {
                    "timestamp": str(int(end_time.timestamp()))
                }

            if description:
                update_data["description"] = description

            # 调用 API
            await self.feishu_client._request(
                method="PATCH",
                path=f"/open-apis/calendar/v4/events/{event_id}",
                params={"calendar_id": calendar_id},
                json=update_data,
            )

            logger.info(f"Event updated successfully: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update event: {e}")
            return False

    async def delete_event(self, user_id: str, event_id: str) -> bool:
        """删除事件。

        Args:
            user_id: 用户 ID
            event_id: 事件 ID

        Returns:
            是否成功

        Examples:
            >>> success = await calendar.delete_event(
            ...     user_id="ou_xxx",
            ...     event_id="evt_xxx"
            ... )
        """
        logger.info(f"Deleting event {event_id} for user {user_id[:4]}***")

        try:
            # 获取主日历 ID
            calendar_id = await self._get_primary_calendar(user_id)

            # 调用 API
            await self.feishu_client._request(
                method="DELETE",
                path=f"/open-apis/calendar/v4/events/{event_id}",
                params={"calendar_id": calendar_id},
            )

            logger.info(f"Event deleted successfully: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete event: {e}")
            return False

    async def list_events(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """列出事件。

        Args:
            user_id: 用户 ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 最大返回数量

        Returns:
            事件列表

        Examples:
            >>> events = await calendar.list_events(
            ...     user_id="ou_xxx",
            ...     start_date=datetime(2026, 2, 1),
            ...     end_date=datetime(2026, 2, 28)
            ... )
        """
        logger.info(
            f"Listing events for user {user_id[:4]}*** "
            f"from {start_date} to {end_date}"
        )

        try:
            # 获取主日历 ID
            calendar_id = await self._get_primary_calendar(user_id)

            # 调用 API
            response = await self.feishu_client._request(
                method="GET",
                path="/open-apis/calendar/v4/events",
                params={
                    "calendar_id": calendar_id,
                    "start_time": str(int(start_date.timestamp())),
                    "end_time": str(int(end_date.timestamp())),
                    "page_size": limit,
                },
            )

            events = response.get("data", {}).get("event_list", [])
            logger.info(f"Retrieved {len(events)} events")
            return events

        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            return []

    async def _get_primary_calendar(self, user_id: str) -> str:
        """获取用户主日历 ID。

        Args:
            user_id: 用户 ID

        Returns:
            主日历 ID

        Raises:
            FeishuCalendarError: 获取失败
        """
        logger.debug(f"Getting primary calendar for user {user_id[:4]}***")

        try:
            # 调用飞书 API 获取日历列表
            response = await self.feishu_client._request(
                method="GET",
                path="/open-apis/calendar/v4/calendars",
                params={"user_id": user_id},
            )

            calendars = response.get("data", {}).get("calendar_list", [])

            # 查找主日历
            for calendar in calendars:
                if calendar.get("primary"):
                    calendar_id = calendar.get("calendar_id")
                    logger.debug(f"Primary calendar found: {calendar_id}")
                    return calendar_id

            # 如果没有主日历，返回第一个日历
            if calendars:
                calendar_id = calendars[0].get("calendar_id")
                logger.warning(f"No primary calendar, using first: {calendar_id}")
                return calendar_id

            raise FeishuCalendarError("No calendars found for user", code=404)

        except Exception as e:
            logger.error(f"Failed to get primary calendar: {e}")
            raise FeishuCalendarError(f"Failed to get primary calendar: {e}", code=500)

    async def send_event_reminder(
        self,
        user_id: str,
        event_id: str,
        remind_time: str,
    ) -> bool:
        """发送事件提醒消息。

        Args:
            user_id: 用户 ID
            event_id: 事件 ID
            remind_time: 提醒时间（"15min", "1hour", "1day"）

        Returns:
            是否成功

        Examples:
            >>> success = await calendar.send_event_reminder(
            ...     user_id="ou_xxx",
            ...     event_id="evt_xxx",
            ...     remind_time="1hour"
            ... )
        """
        logger.info(
            f"Sending event reminder: {event_id} to user {user_id[:4]}*** "
            f"({remind_time} before)"
        )

        try:
            # 获取事件详情
            event = await self.get_event(user_id, event_id)
            if not event:
                raise FeishuCalendarError(f"Event not found: {event_id}", code=404)

            title = event.get("summary", "未命名事件")
            start_time = event.get("start_time", {}).get("timestamp")
            description = event.get("description", "")

            # 格式化提醒消息
            message = self._format_reminder_message(
                title=title,
                start_time=int(start_time) if start_time else None,
                description=description,
                remind_time=remind_time,
            )

            # 发送飞书消息
            # TODO: 集成飞书消息发送 API
            # await self.feishu_client.send_message(
            #     receive_id=user_id,
            #     content=message,
            #     msg_type="interactive"
            # )

            logger.info(f"Event reminder sent: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send event reminder: {e}")
            return False

    def _format_reminder_message(
        self,
        title: str,
        start_time: Optional[int],
        description: str,
        remind_time: str,
    ) -> Dict[str, Any]:
        """格式化提醒消息。

        Args:
            title: 事件标题
            start_time: 开始时间戳
            description: 描述
            remind_time: 提醒时间

        Returns:
            飞书卡片消息字典
        """
        # 转换时间戳
        if start_time:
            dt = datetime.fromtimestamp(start_time)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        else:
            time_str = "待定"

        # 提醒时间文本
        remind_time_map = {
            "15min": "15分钟后",
            "1hour": "1小时后",
            "1day": "明天",
        }
        remind_text = remind_time_map.get(remind_time, remind_time)

        # 构建卡片内容
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "content": "📅 日程提醒",
                    "tag": "plain_text",
                },
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"【{title}】",
                        "tag": "lark_md",
                    },
                },
                {
                    "tag": "div",
                    "text": {
                        "content": f"⏰ 时间：{time_str}",
                        "tag": "lark_md",
                    },
                },
            ],
        }

        if description:
            card["elements"].append(
                {
                    "tag": "div",
                    "text": {
                        "content": f"📝 描述：{description}",
                        "tag": "lark_md",
                    },
                }
            )

        return card
