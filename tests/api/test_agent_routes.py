"""Agent API 路由测试模块。

测试 Agent 相关的 FastAPI 端点。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def test_client():
    """测试客户端夹具。

    Returns:
        TestClient: FastAPI 测试客户端
    """
    return TestClient(app)


@pytest.fixture
def mock_agent_result():
    """模拟 Agent 执行结果。

    Returns:
        dict: 模拟的结果
    """
    return {
        "response": "✅ 已为你创建提醒：开会",
        "intent": "reminder",
        "tool_name": "task_creation",
        "tool_result": {
            "success": True,
            "title": "开会",
        },
        "memory_context": None,
        "next_action": "end",
    }


# ==================== 对话端点测试 ====================


def test_chat_success(test_client, mock_agent_result):
    """测试成功对话。

    Args:
        test_client: 测试客户端
        mock_agent_result: 模拟的 Agent 结果
    """
    with patch('src.api.routes.agent.run_agent') as mock_run:
        mock_run = AsyncMock(return_value=mock_agent_result)

        # 由于 fastapi.testclient 不支持 async，需要使用同步包装
        def sync_run(*args, **kwargs):
            import asyncio
            return asyncio.run(mock_run(*args, **kwargs))

        with patch('src.api.routes.agent.run_agent', side_effect=sync_run):
            response = test_client.post(
                "/api/v1/agent/chat",
                json={
                    "user_id": "user_123",
                    "message": "提醒我明天开会",
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "response" in data["data"]
        assert data["data"]["response"] == "✅ 已为你创建提醒：开会"


def test_chat_empty_message(test_client):
    """测试空消息应失败。

    Args:
        test_client: 测试客户端
    """
    response = test_client.post(
        "/api/v1/agent/chat",
        json={
            "user_id": "user_123",
            "message": "",
        }
    )

    assert response.status_code == 422  # Validation error


def test_chat_missing_user_id(test_client):
    """测试缺少用户ID应失败。

    Args:
        test_client: 测试客户端
    """
    response = test_client.post(
        "/api/v1/agent/chat",
        json={
            "message": "你好",
        }
    )

    assert response.status_code == 422  # Validation error


def test_chat_with_config(test_client, mock_agent_result):
    """测试带配置的对话。

    Args:
        test_client: 测试客户端
        mock_agent_result: 模拟的 Agent 结果
    """
    with patch('src.api.routes.agent.run_agent') as mock_run:
        def sync_run(*args, **kwargs):
            import asyncio
            return asyncio.run(mock_run(*args, **kwargs))

        with patch('src.api.routes.agent.run_agent', side_effect=sync_run):
            response = test_client.post(
                "/api/v1/agent/chat",
                json={
                    "user_id": "user_123",
                    "message": "查询日历",
                    "config": {
                        "temperature": 0.7,
                    }
                }
            )

        assert response.status_code == 200


def test_chat_agent_error(test_client):
    """测试 Agent 执行错误。

    Args:
        test_client: 测试客户端
    """
    with patch('src.api.routes.agent.run_agent') as mock_run:
        # 模拟返回错误
        error_result = {
            "error": "Agent execution failed",
        }

        def sync_run(*args, **kwargs):
            import asyncio
            return asyncio.run(mock_run(*args, **kwargs))

        with patch('src.api.routes.agent.run_agent', return_value=error_result, side_effect=sync_run):
            response = test_client.post(
                "/api/v1/agent/chat",
                json={
                    "user_id": "user_123",
                    "message": "测试",
                }
            )

        assert response.status_code == 500


# ==================== 反馈端点测试 ====================


def test_feedback_success(test_client):
    """测试成功提交反馈。

    Args:
        test_client: 测试客户端
    """
    response = test_client.post(
        "/api/v1/agent/feedback",
        json={
            "conversation_id": "conv_123",
            "feedback": "回答很有帮助",
            "score": 0.9,
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["message"] == "Feedback received"


def test_feedback_invalid_score(test_client):
    """测试无效评分。

    Args:
        test_client: 测试客户端
    """
    response = test_client.post(
        "/api/v1/agent/feedback",
        json={
            "conversation_id": "conv_123",
            "feedback": "测试",
            "score": 1.5,  # 超出范围
        }
    )

    assert response.status_code == 422  # Validation error


def test_feedback_missing_fields(test_client):
    """测试缺少必需字段。

    Args:
        test_client: 测试客户端
    """
    response = test_client.post(
        "/api/v1/agent/feedback",
        json={
            "conversation_id": "conv_123",
            "feedback": "测试",
            # 缺少 score
        }
    )

    assert response.status_code == 422  # Validation error


# ==================== 状态端点测试 ====================


def test_get_status(test_client):
    """测试获取状态。

    Args:
        test_client: 测试客户端
    """
    response = test_client.get("/api/v1/agent/status")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["status"] == "healthy"
    assert data["data"]["tools_enabled"] is True
    assert data["data"]["memory_enabled"] is True


# ==================== 集成测试 ====================


def test_full_conversation_flow(test_client, mock_agent_result):
    """测试完整对话流程。

    Args:
        test_client: 测试客户端
        mock_agent_result: 模拟的 Agent 结果
    """
    # 1. 发送消息
    with patch('src.api.routes.agent.run_agent') as mock_run:
        def sync_run(*args, **kwargs):
            import asyncio
            return asyncio.run(mock_run(*args, **kwargs))

        with patch('src.api.routes.agent.run_agent', side_effect=sync_run):
            response = test_client.post(
                "/api/v1/agent/chat",
                json={
                    "user_id": "user_123",
                    "message": "创建任务：完成报告",
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert "✅" in data["data"]["response"]

    # 2. 提交反馈
    feedback_response = test_client.post(
        "/api/v1/agent/feedback",
        json={
            "conversation_id": "conv_123",
            "feedback": "很有帮助",
            "score": 0.95,
        }
    )

    assert feedback_response.status_code == 200

    # 3. 检查状态
    status_response = test_client.get("/api/v1/agent/status")
    assert status_response.status_code == 200
