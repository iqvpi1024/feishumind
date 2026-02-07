"""事件提醒工具模块。

提供事件提醒的 Agent 工具，集成 NLP 解析、飞书日历 API、调度器和情绪检测。

Author: Claude Code
Date: 2026-02-06
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from src.agent.tools import BaseTool
from src.utils.nlp import extract_event_info, parse_datetime
from src.utils.sentiment import analyze_event_sentiment, StressLevel
from src.utils.logger import get_logger
from src.integrations.feishu.calendar import FeishuCalendarClient
from src.integrations.feishu.client import FeishuClient
from src.utils.scheduler import TaskScheduler

logger = get_logger(__name__)


class EventReminderTool(BaseTool):
    """事件提醒工具。

    从自然语言输入创建事件，设置飞书日历和提醒。

    Attributes:
        name: 工具名称
        description: 工具描述

    Examples:
        >>> tool = EventReminderTool(
        ...     feishu_client=feishu_client,
        ...     scheduler=scheduler
        ... )
        >>> result = await tool.execute(
        ...     user_id="ou_xxx",
        ...     message="提醒我明天下午3点开会"
        ... )
    """

    name = "event_reminder"
    description = (
        "创建事件提醒。支持自然语言时间解析，如'明天下午3点开会'、"
        "'下周一上午10点汇报'。将自动创建飞书日历事件并设置多个提醒时间点。"
    )

    def __init__(
        self,
        feishu_client: FeishuClient,
        scheduler: TaskScheduler,
        reminder_minutes: Optional[List[int]] = None,
    ):
        """初始化事件提醒工具。

        Args:
            feishu_client: 飞书客户端
            scheduler: 任务调度器
            reminder_minutes: 提前提醒时间列表（分钟），默认 [15, 60, 1440]
        """
        self.feishu_client = feishu_client
        self.scheduler = scheduler
        self.calendar_client = FeishuCalendarClient(feishu_client)
        self.reminder_minutes = reminder_minutes or [15, 60, 1440]

        logger.info("Event reminder tool initialized")

    @property
    def parameters(self) -> Dict[str, Any]:
        """获取工具参数定义。"""
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户 ID（飞书 user_id）",
                },
                "message": {
                    "type": "string",
                    "description": "事件描述，如'提醒我明天下午3点开会'",
                },
                "description": {
                    "type": "string",
                    "description": "事件详细描述（可选）",
                },
                "location": {
                    "type": "string",
                    "description": "事件地点（可选）",
                },
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "参与者 ID 列表（可选）",
                },
                "reminder_minutes": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "提前提醒时间（分钟），如 [15, 60, 1440]",
                },
            },
            "required": ["user_id", "message"],
        }

    async def execute(
        self,
        user_id: str,
        message: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        reminder_minutes: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """执行事件提醒创建。

        工作流程：
        1. 使用 NLP 解析用户输入，提取事件信息
        2. 情绪检测，识别压力等级
        3. 创建飞书日历事件
        4. 设置多个提醒时间点
        5. 返回确认消息

        Args:
            user_id: 用户 ID
            message: 事件描述
            description: 详细描述
            location: 地点
            attendees: 参与者
            reminder_minutes: 提前提醒时间

        Returns:
            执行结果字典，包含：
            - success: 是否成功
            - event_id: 事件 ID
            - event_info: 事件信息
            - stress_analysis: 压力分析
            - reminders: 提醒时间列表
        """
        logger.info(
            f"Executing event reminder for user {user_id[:4]}***: {message}"
        )

        try:
            # 1. NLP 解析事件信息
            event_info = self._parse_event(message)
            if not event_info:
                return {
                    "success": False,
                    "error": "无法解析事件信息，请提供更清晰的时间描述",
                }

            # 2. 情绪检测
            stress_analysis = analyze_event_sentiment(message)

            # 3. 创建飞书日历事件
            event_id = await self._create_feishu_event(
                user_id=user_id,
                event_info=event_info,
                description=description,
                location=location,
                attendees=attendees,
                reminder_minutes=reminder_minutes or self.reminder_minutes,
            )

            if not event_id:
                return {
                    "success": False,
                    "error": "创建飞书日历事件失败",
                }

            # 4. 设置提醒任务
            reminder_jobs = self._schedule_reminders(
                user_id=user_id,
                event_id=event_id,
                event_info=event_info,
                reminder_minutes=reminder_minutes or self.reminder_minutes,
            )

            # 5. 构建响应
            response = {
                "success": True,
                "event_id": event_id,
                "event_info": {
                    "title": event_info.get("title"),
                    "start_time": event_info.get("start_time").isoformat(),
                    "end_time": event_info.get("end_time").isoformat(),
                },
                "stress_analysis": stress_analysis,
                "reminders": reminder_jobs,
                "message": self._format_success_message(
                    event_info, stress_analysis, reminder_jobs
                ),
            }

            logger.info(f"Event reminder created successfully: {event_id}")
            return response

        except Exception as e:
            logger.error(f"Failed to execute event reminder: {e}")
            return {
                "success": False,
                "error": f"创建事件提醒失败: {str(e)}",
            }

    def _parse_event(self, message: str) -> Optional[Dict[str, Any]]:
        """解析事件信息。

        Args:
            message: 用户消息

        Returns:
            事件信息字典，失败返回 None
        """
        logger.debug(f"Parsing event from message: {message}")

        # 使用 NLP 提取事件信息
        event_info = extract_event_info(message)

        if not event_info:
            return None

        # 计算结束时间（默认1小时）
        start_time = event_info.get("start_time")
        if start_time:
            event_info["end_time"] = start_time + timedelta(hours=1)
        else:
            logger.error("No start_time found in event_info")
            return None

        return event_info

    async def _create_feishu_event(
        self,
        user_id: str,
        event_info: Dict[str, Any],
        description: Optional[str],
        location: Optional[str],
        attendees: Optional[List[str]],
        reminder_minutes: List[int],
    ) -> Optional[str]:
        """创建飞书日历事件。

        Args:
            user_id: 用户 ID
            event_info: 事件信息
            description: 描述
            location: 地点
            attendees: 参与者
            reminder_minutes: 提前提醒时间

        Returns:
            事件 ID，失败返回 None
        """
        try:
            event_id = await self.calendar_client.create_event(
                user_id=user_id,
                title=event_info.get("title", "未命名事件"),
                start_time=event_info["start_time"],
                end_time=event_info["end_time"],
                description=description,
                location=location,
                attendes=attendees,
                reminder_minutes=reminder_minutes,
            )

            return event_id

        except Exception as e:
            logger.error(f"Failed to create Feishu event: {e}")
            return None

    def _schedule_reminders(
        self,
        user_id: str,
        event_id: str,
        event_info: Dict[str, Any],
        reminder_minutes: List[int],
    ) -> List[Dict[str, Any]]:
        """设置提醒任务。

        Args:
            user_id: 用户 ID
            event_id: 事件 ID
            event_info: 事件信息
            reminder_minutes: 提前提醒时间

        Returns:
            提醒任务列表
        """
        logger.debug(
            f"Scheduling reminders for event {event_id[:8]}***: {reminder_minutes}"
        )

        reminder_jobs = []

        # 创建异步回调函数
        async def reminder_callback(event_id: str):
            """提醒回调函数。"""
            try:
                await self.calendar_client.send_event_reminder(
                    user_id=user_id,
                    event_id=event_id,
                    remind_time="",  # 由调度器自动确定
                )
            except Exception as e:
                logger.error(f"Failed to send reminder: {e}")

        # 调度多个提醒
        job_ids = self.scheduler.schedule_event_reminders(
            event_id=event_id,
            event_start_time=event_info["start_time"],
            callback=reminder_callback,
            reminder_minutes=reminder_minutes,
        )

        # 构建提醒任务信息
        for i, job_id in enumerate(job_ids):
            reminder_jobs.append(
                {
                    "job_id": job_id,
                    "minutes_before": reminder_minutes[i],
                }
            )

        logger.info(f"Scheduled {len(reminder_jobs)} reminder jobs")
        return reminder_jobs

    def _format_success_message(
        self,
        event_info: Dict[str, Any],
        stress_analysis: Dict[str, Any],
        reminders: List[Dict[str, Any]],
    ) -> str:
        """格式化成功消息。

        Args:
            event_info: 事件信息
            stress_analysis: 压力分析
            reminders: 提醒任务列表

        Returns:
            格式化的消息
        """
        title = event_info.get("title", "未命名事件")
        start_time = event_info.get("start_time").strftime("%Y-%m-%d %H:%M")
        stress_emoji = stress_analysis.get("emoji", "🟢")
        stress_level = stress_analysis.get("stress_level", "low")

        reminder_text = "、".join(
            [f"{r['minutes_before']}分钟前" for r in reminders]
        )

        message = (
            f"✅ 已创建事件提醒\n\n"
            f"【{title}】\n"
            f"⏰ 时间：{start_time}\n"
            f"{stress_emoji} 压力等级：{stress_level}\n"
            f"🔔 提醒：{reminder_text}前会通知您\n"
        )

        # 如果有建议，添加到消息中
        suggestions = stress_analysis.get("suggestions", [])
        if suggestions:
            message += f"\n💡 建议：{suggestions[0]}"

        return message


# 便捷函数
def create_event_reminder_tool(
    feishu_client: FeishuClient,
    scheduler: TaskScheduler,
    reminder_minutes: Optional[List[int]] = None,
) -> EventReminderTool:
    """创建事件提醒工具（便捷函数）。

    Args:
        feishu_client: 飞书客户端
        scheduler: 任务调度器
        reminder_minutes: 提前提醒时间

    Returns:
        EventReminderTool 实例
    """
    return EventReminderTool(
        feishu_client=feishu_client,
        scheduler=scheduler,
        reminder_minutes=reminder_minutes,
    )
