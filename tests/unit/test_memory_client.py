"""记忆客户端单元测试模块。

测试 MemoryClient 的核心功能，包括添加记忆、搜索记忆、
更新反馈评分等。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.memory.client import MemoryClient, get_memory_client, reset_memory_client
from src.memory.config import MemoryConfig


@pytest.fixture
def mock_config():
    """模拟配置对象。

    Returns:
        MemoryConfig: 测试配置
    """
    config = MemoryConfig(
        enabled=True,
        vector_store="faiss",
        storage_path="./test_data/memory",
        database_path="./test_data/memory/test.db",
        # 添加缺失的必填字段以避免Pydantic验证错误
        embedding_model="BAAI/bge-small-en-v1.5",
        embedding_dimension=384,
    )
    return config


@pytest.fixture
def memory_client(mock_config):
    """记忆客户端测试夹具。

    Args:
        mock_config: 模拟配置

    Returns:
        MemoryClient: 测试客户端
    """
    # 使用 patch 模拟 Mem0 初始化
    with patch('src.memory.client.Memory.from_config') as mock_mem0:
        mock_client_instance = Mock()
        mock_mem0.return_value = mock_client_instance

        client = MemoryClient(config=mock_config)
        client._client = mock_client_instance

        yield client, mock_client_instance


@pytest.mark.asyncio
async def test_add_memory_success(memory_client):
    """测试成功添加记忆。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, mock_mem0_client = memory_client

    # 模拟 Mem0 返回值
    mock_mem0_client.add.return_value = {
        "id": "mem_123",
        "memory": "Test content",
        "metadata": {}
    }

    # 执行添加
    memory_id = await client.add_memory(
        user_id="user_123",
        content="我喜欢用 Python 写代码",
        category="preference"
    )

    # 验证
    assert memory_id == "mem_123"
    mock_mem0_client.add.assert_called_once()


@pytest.mark.asyncio
async def test_add_memory_empty_content(memory_client):
    """测试添加空记忆应抛出异常。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, _ = memory_client

    with pytest.raises(ValueError, match="content cannot be empty"):
        await client.add_memory(
            user_id="user_123",
            content="",
            category="preference"
        )


@pytest.mark.asyncio
async def test_add_memory_invalid_category(memory_client):
    """测试添加无效类别应抛出异常。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, _ = memory_client

    with pytest.raises(ValueError, match="Invalid category"):
        await client.add_memory(
            user_id="user_123",
            content="Test content",
            category="invalid_category"
        )


@pytest.mark.asyncio
async def test_add_memory_with_metadata(memory_client):
    """测试添加带元数据的记忆。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, mock_mem0_client = memory_client

    mock_mem0_client.add.return_value = {
        "id": "mem_456",
        "memory": "Test content",
        "metadata": {}
    }

    metadata = {"source": "feishu", "timestamp": "2026-02-06"}
    memory_id = await client.add_memory(
        user_id="user_123",
        content="测试记忆",
        category="event",
        metadata=metadata
    )

    assert memory_id == "mem_456"
    # 验证元数据被合并
    call_args = mock_mem0_client.add.call_args
    assert "source" in call_args[1]["metadata"]


@pytest.mark.asyncio
async def test_search_memory_success(memory_client):
    """测试成功搜索记忆。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, mock_mem0_client = memory_client

    # 模拟搜索结果
    mock_mem0_client.search.return_value = [
        {
            "id": "mem_123",
            "memory": "我喜欢 Python",
            "score": 0.95,
            "metadata": {
                "category": "preference",
                "created_at": "2026-02-06T10:00:00"
            }
        },
        {
            "id": "mem_124",
            "memory": "我喜欢写代码",
            "score": 0.85,
            "metadata": {
                "category": "preference",
                "created_at": "2026-02-06T11:00:00"
            }
        }
    ]

    results = await client.search_memory(
        user_id="user_123",
        query="编程偏好",
        limit=10
    )

    # 验证
    assert len(results) == 2
    assert results[0]["score"] >= results[1]["score"]  # 按分数降序
    assert results[0]["memory_id"] == "mem_123"


@pytest.mark.asyncio
async def test_search_memory_with_threshold(memory_client):
    """测试带阈值的搜索。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, mock_mem0_client = memory_client

    mock_mem0_client.search.return_value = [
        {"id": "mem_1", "memory": "Low score", "score": 0.5, "metadata": {}},
        {"id": "mem_2", "memory": "High score", "score": 0.9, "metadata": {}}
    ]

    results = await client.search_memory(
        user_id="user_123",
        query="test",
        threshold=0.7
    )

    # 只有分数 >= 0.7 的结果
    assert len(results) == 1
    assert results[0]["memory_id"] == "mem_2"


@pytest.mark.asyncio
async def test_search_memory_with_category_filter(memory_client):
    """测试类别过滤。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, mock_mem0_client = memory_client

    mock_mem0_client.search.return_value = [
        {
            "id": "mem_1",
            "memory": "Preference",
            "score": 0.9,
            "metadata": {"category": "preference"}
        },
        {
            "id": "mem_2",
            "memory": "Emotion",
            "score": 0.8,
            "metadata": {"category": "emotion"}
        }
    ]

    results = await client.search_memory(
        user_id="user_123",
        query="test",
        category="preference"
    )

    # 只返回 preference 类别
    assert len(results) == 1
    assert results[0]["category"] == "preference"


@pytest.mark.asyncio
async def test_update_feedback_success(memory_client):
    """测试成功更新反馈。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, _ = memory_client

    success = await client.update_memory(
        memory_id="mem_123",
        feedback_score=0.9
    )

    assert success is True


@pytest.mark.asyncio
async def test_update_feedback_invalid_score(memory_client):
    """测试无效反馈评分。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, _ = memory_client

    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        await client.update_memory(
            memory_id="mem_123",
            feedback_score=1.5
        )


@pytest.mark.asyncio
async def test_update_feedback_low_score(memory_client):
    """测试低分反馈（应触发警告）。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, _ = memory_client

    # 低分不应抛异常，但应记录警告
    success = await client.update_memory(
        memory_id="mem_123",
        feedback_score=0.5
    )

    assert success is True


@pytest.mark.asyncio
async def test_get_all_memories(memory_client):
    """测试获取所有记忆。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, mock_mem0_client = memory_client

    mock_mem0_client.get_all.return_value = [
        {
            "id": "mem_1",
            "memory": "Memory 1",
            "metadata": {"category": "preference"}
        },
        {
            "id": "mem_2",
            "memory": "Memory 2",
            "metadata": {"category": "emotion"}
        }
    ]

    memories = await client.get_all_memories(user_id="user_123")

    assert len(memories) == 2


@pytest.mark.asyncio
async def test_delete_memory(memory_client):
    """测试删除记忆。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, mock_mem0_client = memory_client

    mock_mem0_client.delete.return_value = None

    success = await client.delete_memory(memory_id="mem_123")

    assert success is True
    mock_mem0_client.delete.assert_called_once_with("mem_123")


def test_sanitize_content(memory_client):
    """测试内容脱敏。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, _ = memory_client

    # 测试空格标准化
    sanitized = client._sanitize_content("  Test   content  ")
    assert sanitized == "Test content"


def test_is_enabled_property(memory_client):
    """测试启用状态属性。

    Args:
        memory_client: 记忆客户端夹具
    """
    client, _ = memory_client
    assert client.is_enabled is True


@patch('src.memory.client.Memory.from_config')
def test_memory_disabled(mock_mem0):
    """测试记忆系统禁用时的行为。"""
    config = MemoryConfig(enabled=False)
    client = MemoryClient(config=config)

    assert client.is_enabled is False


@patch('src.memory.client.Memory.from_config')
def test_get_memory_client_singleton(mock_mem0):
    """测试单例模式。"""
    mock_instance = Mock()
    mock_mem0.return_value = mock_instance

    reset_memory_client()

    client1 = get_memory_client()
    client2 = get_memory_client()

    assert client1 is client2


@patch('src.memory.client.Memory.from_config')
def test_reset_memory_client(mock_mem0):
    """测试重置客户端。"""
    mock_instance = Mock()
    mock_mem0.return_value = mock_instance

    client1 = get_memory_client()
    reset_memory_client()
    client2 = get_memory_client()

    assert client1 is not client2
