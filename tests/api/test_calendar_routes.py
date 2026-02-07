"""日历 API 路由测试模块。

测试飞书日历相关的 FastAPI 端点。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from src.api.main import app
from src.api.routes.calendar import set_feishu_client
from src.integrations.feishu.client import FeishuClient


@pytest.fixture
def test_client():
    """测试客户端夹具。

    Returns:
        TestClient: FastAPI 测试客户端
    """
    return TestClient(app)


@pytest.fixture
def mock_feishu_client():
    """模拟飞书客户端。

    Returns:
        Mock: 模拟的飞书客户端
    """
    client = Mock(spec=FeishuClient)
    set_feishu_client(client)
    return client


@pytest.fixture
def sample_event_data():
    """示例事件数据。

    Returns:
        dict: 示例事件数据
    """
    return {
        "user_id": "ou_123456",
        "title": "项目周会",
        "start_time": "2026-02-07T15:00:00+08:00",
        "end_time": "2026-02-07T16:00:00+08:00",
        "description": "讨论本周进度和下周计划",
        "location": "会议室 A",
        "attendees": ["ou_yyy", "ou_zzz"],
        "reminder_minutes": [15, 60, 1440],
    }


# ==================== 创建事件测试 ====================


def test_create_event_success(test_client, mock_feishu_client, sample_event_data):
    """测试成功创建事件。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
        sample_event_data: 示例事件数据
    """
    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.create_event.return_value = "event_123"
        mock_calendar_class.return_value = mock_calendar

        response = test_client.post("/api/v1/calendar/events", json=sample_event_data)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["event_id"] == "event_123"
        assert "created successfully" in data["message"].lower()


def test_create_event_missing_title(test_client, mock_feishu_client):
    """测试缺少标题应失败。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    event_data = {
        "user_id": "ou_123",
        "start_time": "2026-02-07T15:00:00+08:00",
        "end_time": "2026-02-07T16:00:00+08:00",
    }

    response = test_client.post("/api/v1/calendar/events", json=event_data)

    assert response.status_code == 422  # Validation error


def test_create_event_invalid_datetime(test_client, mock_feishu_client, sample_event_data):
    """测试无效日期时间格式应失败。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
        sample_event_data: 示例事件数据
    """
    sample_event_data["start_time"] = "invalid-datetime"

    response = test_client.post("/api/v1/calendar/events", json=sample_event_data)

    assert response.status_code == 400


def test_create_event_feishu_api_error(test_client, mock_feishu_client, sample_event_data):
    """测试飞书API失败。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
        sample_event_data: 示例事件数据
    """
    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.create_event.side_effect = Exception("Feishu API error")
        mock_calendar_class.return_value = mock_calendar

        response = test_client.post("/api/v1/calendar/events", json=sample_event_data)

        assert response.status_code == 500


def test_create_event_with_optional_fields(test_client, mock_feishu_client):
    """测试带可选字段的创建。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    event_data = {
        "user_id": "ou_123",
        "title": "简单会议",
        "start_time": "2026-02-07T15:00:00+08:00",
        "end_time": "2026-02-07T16:00:00+08:00",
        # 不提供可选字段
    }

    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.create_event.return_value = "event_456"
        mock_calendar_class.return_value = mock_calendar

        response = test_client.post("/api/v1/calendar/events", json=event_data)

        assert response.status_code == 201


# ==================== 获取事件测试 ====================


def test_get_event_success(test_client, mock_feishu_client):
    """测试成功获取事件。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    event_id = "event_123"
    mock_event = {
        "event_id": event_id,
        "title": "项目周会",
        "start_time": "2026-02-07T15:00:00+08:00",
    }

    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.get_event.return_value = mock_event
        mock_calendar_class.return_value = mock_calendar

        response = test_client.get(f"/api/v1/calendar/events/{event_id}?user_id=ou_123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event"]["event_id"] == event_id


def test_get_event_not_found(test_client, mock_feishu_client):
    """测试事件不存在。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    event_id = "nonexistent_event"

    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.get_event.return_value = None
        mock_calendar_class.return_value = mock_calendar

        response = test_client.get(f"/api/v1/calendar/events/{event_id}?user_id=ou_123")

        assert response.status_code == 404


def test_get_event_missing_user_id(test_client, mock_feishu_client):
    """测试缺少用户ID应失败。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    response = test_client.get("/api/v1/calendar/events/event_123")

    assert response.status_code == 422  # Validation error


# ==================== 更新事件测试 ====================


def test_update_event_success(test_client, mock_feishu_client):
    """测试成功更新事件。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    event_id = "event_123"
    update_data = {
        "user_id": "ou_123",
        "title": "更新后的标题",
        "description": "更新后的描述",
    }

    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.update_event.return_value = True
        mock_calendar_class.return_value = mock_calendar

        response = test_client.put(f"/api/v1/calendar/events/{event_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event_id"] == event_id


def test_update_event_invalid_datetime(test_client, mock_feishu_client):
    """测试更新时使用无效日期时间。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    event_id = "event_123"
    update_data = {
        "user_id": "ou_123",
        "start_time": "invalid-datetime",
    }

    response = test_client.put(f"/api/v1/calendar/events/{event_id}", json=update_data)

    assert response.status_code == 400


def test_update_event_feishu_error(test_client, mock_feishu_client):
    """测试飞书API更新失败。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    event_id = "event_123"
    update_data = {
        "user_id": "ou_123",
        "title": "新标题",
    }

    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.update_event.return_value = False
        mock_calendar_class.return_value = mock_calendar

        response = test_client.put(f"/api/v1/calendar/events/{event_id}", json=update_data)

        assert response.status_code == 500


# ==================== 删除事件测试 ====================


def test_delete_event_success(test_client, mock_feishu_client):
    """测试成功删除事件。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    event_id = "event_123"

    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.delete_event.return_value = True
        mock_calendar_class.return_value = mock_calendar

        response = test_client.delete(f"/api/v1/calendar/events/{event_id}?user_id=ou_123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event_id"] == event_id


def test_delete_event_not_found(test_client, mock_feishu_client):
    """测试删除不存在的事件。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    event_id = "nonexistent_event"

    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.delete_event.return_value = False
        mock_calendar_class.return_value = mock_calendar

        response = test_client.delete(f"/api/v1/calendar/events/{event_id}?user_id=ou_123")

        assert response.status_code == 500


# ==================== 列出事件测试 ====================


def test_list_events_success(test_client, mock_feishu_client):
    """测试成功列出事件。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    mock_events = [
        {"event_id": "event_1", "title": "会议1"},
        {"event_id": "event_2", "title": "会议2"},
    ]

    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.list_events.return_value = mock_events
        mock_calendar_class.return_value = mock_calendar

        response = test_client.get(
            "/api/v1/calendar/events"
            "?user_id=ou_123"
            "&start_date=2026-02-01T00:00:00+08:00"
            "&end_date=2026-02-07T23:59:59+08:00"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["events"]) == 2


def test_list_events_empty(test_client, mock_feishu_client):
    """测试列出事件（空列表）。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.list_events.return_value = []
        mock_calendar_class.return_value = mock_calendar

        response = test_client.get(
            "/api/v1/calendar/events"
            "?user_id=ou_123"
            "&start_date=2026-02-01T00:00:00+08:00"
            "&end_date=2026-02-07T23:59:59+08:00"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["events"] == []


def test_list_events_with_date_filter(test_client, mock_feishu_client):
    """测试带日期过滤的列出。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar.list_events.return_value = []
        mock_calendar_class.return_value = mock_calendar

        response = test_client.get(
            "/api/v1/calendar/events"
            "?user_id=ou_123"
            "&start_date=2026-02-01T00:00:00+08:00"
            "&end_date=2026-02-07T23:59:59+08:00"
            "&limit=50"
        )

        assert response.status_code == 200


def test_list_events_invalid_date_format(test_client, mock_feishu_client):
    """测试无效日期格式。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    response = test_client.get(
        "/api/v1/calendar/events"
        "?user_id=ou_123"
        "&start_date=invalid-date"
        "&end_date=2026-02-07T23:59:59+08:00"
    )

    assert response.status_code == 400


def test_list_events_limit_validation(test_client, mock_feishu_client):
    """测试限制参数验证。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
    """
    # 测试超出最大限制
    response = test_client.get(
        "/api/v1/calendar/events"
        "?user_id=ou_123"
        "&start_date=2026-02-01T00:00:00+08:00"
        "&end_date=2026-02-07T23:59:59+08:00"
        "&limit=2000"  # 超过最大值 1000
    )

    assert response.status_code == 422  # Validation error


# ==================== 集成测试 ====================


def test_full_event_lifecycle(test_client, mock_feishu_client, sample_event_data):
    """测试完整事件生命周期。

    Args:
        test_client: 测试客户端
        mock_feishu_client: 模拟的飞书客户端
        sample_event_data: 示例事件数据
    """
    event_id = "event_123"

    with patch('src.api.routes.calendar.FeishuCalendarClient') as mock_calendar_class:
        mock_calendar = AsyncMock()
        mock_calendar_class.return_value = mock_calendar

        # 1. 创建事件
        mock_calendar.create_event.return_value = event_id
        create_response = test_client.post("/api/v1/calendar/events", json=sample_event_data)
        assert create_response.status_code == 201

        # 2. 获取事件
        mock_calendar.get_event.return_value = {
            "event_id": event_id,
            "title": sample_event_data["title"],
        }
        get_response = test_client.get(
            f"/api/v1/calendar/events/{event_id}?user_id={sample_event_data['user_id']}"
        )
        assert get_response.status_code == 200

        # 3. 更新事件
        mock_calendar.update_event.return_value = True
        update_response = test_client.put(
            f"/api/v1/calendar/events/{event_id}",
            json={
                "user_id": sample_event_data["user_id"],
                "title": "更新后的标题",
            }
        )
        assert update_response.status_code == 200

        # 4. 删除事件
        mock_calendar.delete_event.return_value = True
        delete_response = test_client.delete(
            f"/api/v1/calendar/events/{event_id}?user_id={sample_event_data['user_id']}"
        )
        assert delete_response.status_code == 200
