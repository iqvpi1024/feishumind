"""记忆管理 API 路由测试模块。

测试记忆管理相关的 FastAPI 端点。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.memory.client import MemoryClient, reset_memory_client


@pytest.fixture
def test_client():
    """测试客户端夹具。

    Returns:
        TestClient: FastAPI 测试客户端
    """
    return TestClient(app)


@pytest.fixture
def mock_memory_client():
    """模拟记忆客户端夹具。

    Returns:
        Mock: 模拟的记忆客户端
    """
    mock = Mock(spec=MemoryClient)
    mock.is_enabled = True

    # 模拟异步方法
    mock.add_memory = AsyncMock(return_value="mem_123")
    mock.search_memory = AsyncMock(return_value=[
        {
            "memory_id": "mem_123",
            "memory": "Test memory",
            "score": 0.95,
            "category": "preference",
            "created_at": "2026-02-06T10:00:00",
            "metadata": {}
        }
    ])
    mock.update_memory = AsyncMock(return_value=True)
    mock.get_all_memories = AsyncMock(return_value=[
        {
            "id": "mem_123",
            "memory": "Test memory",
            "metadata": {
                "category": "preference",
                "created_at": "2026-02-06T10:00:00"
            }
        }
    ])
    mock.delete_memory = AsyncMock(return_value=True)

    return mock


@pytest.fixture(autouse=True)
def override_dependency(mock_memory_client):
    """覆盖依赖注入。

    Args:
        mock_memory_client: 模拟记忆客户端
    """
    from src.api.routes import memory
    original_override = memory.get_memory_client

    def override():
        return mock_memory_client

    app.dependency_overrides[memory.get_memory_client] = override

    yield

    app.dependency_overrides = {}


def test_add_memory_success(test_client, mock_memory_client):
    """测试成功添加记忆。

    Args:
        test_client: 测试客户端
        mock_memory_client: 模拟记忆客户端
    """
    response = test_client.post(
        "/api/v1/memory",
        json={
            "user_id": "user_123",
            "content": "我喜欢用 Python 写代码",
            "category": "preference"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["memory_id"] == "mem_123"
    mock_memory_client.add_memory.assert_called_once()


def test_add_memory_invalid_category(test_client):
    """测试添加记忆时无效类别。

    Args:
        test_client: 测试客户端
    """
    response = test_client.post(
        "/api/v1/memory",
        json={
            "user_id": "user_123",
            "content": "Test content",
            "category": "invalid"
        }
    )

    assert response.status_code == 422  # Validation error


def test_add_memory_empty_content(test_client):
    """测试添加空内容。

    Args:
        test_client: 测试客户端
    """
    response = test_client.post(
        "/api/v1/memory",
        json={
            "user_id": "user_123",
            "content": "",
            "category": "preference"
        }
    )

    assert response.status_code == 422  # Validation error


def test_search_memory_success(test_client, mock_memory_client):
    """测试成功搜索记忆。

    Args:
        test_client: 测试客户端
        mock_memory_client: 模拟记忆客户端
    """
    response = test_client.get(
        "/api/v1/memory/search",
        params={
            "user_id": "user_123",
            "query": "编程偏好",
            "limit": 10
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert len(data["data"]) == 1
    assert data["data"][0]["memory_id"] == "mem_123"
    mock_memory_client.search_memory.assert_called_once()


def test_search_memory_with_category(test_client, mock_memory_client):
    """测试带类别过滤的搜索。

    Args:
        test_client: 测试客户端
        mock_memory_client: 模拟记忆客户端
    """
    response = test_client.get(
        "/api/v1/memory/search",
        params={
            "user_id": "user_123",
            "query": "test",
            "category": "preference"
        }
    )

    assert response.status_code == 200


def test_update_feedback_success(test_client, mock_memory_client):
    """测试成功更新反馈。

    Args:
        test_client: 测试客户端
        mock_memory_client: 模拟记忆客户端
    """
    response = test_client.put(
        "/api/v1/memory/mem_123/feedback",
        json={"feedback_score": 0.9}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["feedback_score"] == 0.9
    mock_memory_client.update_memory.assert_called_once_with(
        memory_id="mem_123",
        feedback_score=0.9
    )


def test_update_feedback_invalid_score(test_client):
    """测试无效反馈评分。

    Args:
        test_client: 测试客户端
    """
    response = test_client.put(
        "/api/v1/memory/mem_123/feedback",
        json={"feedback_score": 1.5}
    )

    assert response.status_code == 422  # Validation error


def test_get_all_memories(test_client, mock_memory_client):
    """测试获取所有记忆。

    Args:
        test_client: 测试客户端
        mock_memory_client: 模拟记忆客户端
    """
    response = test_client.get(
        "/api/v1/memory/user/user_123"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert len(data["data"]) == 1
    mock_memory_client.get_all_memories.assert_called_once()


def test_delete_memory(test_client, mock_memory_client):
    """测试删除记忆。

    Args:
        test_client: 测试客户端
        mock_memory_client: 模拟记忆客户端
    """
    response = test_client.delete("/api/v1/memory/mem_123")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    mock_memory_client.delete_memory.assert_called_once_with("mem_123")


def test_health_check(test_client):
    """测试健康检查端点。

    Args:
        test_client: 测试客户端
    """
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "FeishuMind"


def test_root_endpoint(test_client):
    """测试根路径端点。

    Args:
        test_client: 测试客户端
    """
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["docs"] == "/docs"
