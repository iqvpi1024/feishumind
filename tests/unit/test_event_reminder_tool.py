"""事件提醒工具单元测试。

测试 EventReminderTool 的功能。

Author: Claude Code
Date: 2026-02-06
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.agent.tool_modules.event_reminder import EventReminderTool, create_event_reminder_tool
from src.integrations.feishu.client import FeishuClient
from src.utils.scheduler import TaskScheduler


@pytest.fixture
def mock_feishu_client():
    """模拟飞书客户端。"""
    client = Mock(spec=FeishuClient)
    return client


@pytest.fixture
def mock_scheduler():
    """模拟任务调度器。"""
    scheduler = Mock(spec=TaskScheduler)
    scheduler.schedule_event_reminders = Mock(return_value=["job_1", "job_2"])
    return scheduler


@pytest.fixture
def event_reminder_tool(mock_feishu_client, mock_scheduler):
    """事件提醒工具实例。"""
    return EventReminderTool(
        feishu_client=mock_feishu_client,
        scheduler=mock_scheduler,
    )


class TestEventReminderTool:
    """EventReminderTool 测试类。"""

    def test_tool_name_and_description(self, event_reminder_tool):
        """测试工具名称和描述。"""
        assert event_reminder_tool.name == "event_reminder"
        assert event_reminder_tool.description is not None
        assert "自然语言" in event_reminder_tool.description

    def test_parameters_definition(self, event_reminder_tool):
        """测试参数定义。"""
        params = event_reminder_tool.parameters
        assert params["type"] == "object"
        assert "user_id" in params["properties"]
        assert "message" in params["properties"]
        assert "user_id" in params["required"]
        assert "message" in params["required"]

    @pytest.mark.asyncio
    async def test_execute_success(self, event_reminder_tool, mock_feishu_client):
        """测试成功执行。"""
        # Mock 飞书日历客户端
        with patch.object(
            event_reminder_tool,
            "calendar_client",
        ) as mock_calendar:
            mock_calendar.create_event = AsyncMock(return_value="evt_123")
            mock_calendar.send_event_reminder = AsyncMock(return_value=True)

            # 执行
            result = await event_reminder_tool.execute(
                user_id="ou_test",
                message="提醒我明天下午3点开会",
            )

            # 验证
            assert result["success"] is True
            assert result["event_id"] == "evt_123"
            assert "event_info" in result
            assert "stress_analysis" in result
            assert "reminders" in result

    @pytest.mark.asyncio
    async def test_execute_parse_failure(self, event_reminder_tool):
        """测试解析失败。"""
        result = await event_reminder_tool.execute(
            user_id="ou_test",
            message="这是一个没有时间的消息",
        )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_with_custom_reminders(
        self, event_reminder_tool, mock_feishu_client
    ):
        """测试自定义提醒时间。"""
        with patch.object(
            event_reminder_tool,
            "calendar_client",
        ) as mock_calendar:
            mock_calendar.create_event = AsyncMock(return_value="evt_123")

            result = await event_reminder_tool.execute(
                user_id="ou_test",
                message="提醒我明天下午3点开会",
                reminder_minutes=[30, 60],
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_parse_event(self, event_reminder_tool):
        """测试事件解析。"""
        event_info = event_reminder_tool._parse_event("提醒我明天下午3点开会")

        assert event_info is not None
        assert "title" in event_info
        assert "start_time" in event_info
        assert "end_time" in event_info

    def test_format_success_message(self, event_reminder_tool):
        """测试成功消息格式化。"""
        event_info = {
            "title": "测试会议",
            "start_time": datetime.now() + timedelta(days=1),
        }
        stress_analysis = {
            "emoji": "🟡",
            "stress_level": "medium",
            "suggestions": ["建议提前准备"],
        }
        reminders = [
            {"job_id": "job_1", "minutes_before": 15},
            {"job_id": "job_2", "minutes_before": 60},
        ]

        message = event_reminder_tool._format_success_message(
            event_info, stress_analysis, reminders
        )

        assert "测试会议" in message
        assert "🟡" in message
        assert "medium" in message
        assert "15分钟前" in message
        assert "60分钟前" in message


class TestConvenienceFunction:
    """便捷函数测试类。"""

    def test_create_event_reminder_tool(self, mock_feishu_client, mock_scheduler):
        """测试 create_event_reminder_tool 便捷函数。"""
        tool = create_event_reminder_tool(
            feishu_client=mock_feishu_client,
            scheduler=mock_scheduler,
            reminder_minutes=[15, 60],
        )

        assert isinstance(tool, EventReminderTool)
        assert tool.reminder_minutes == [15, 60]
