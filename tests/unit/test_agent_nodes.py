"""Agent 节点单元测试模块。

测试 Agent 状态机的各个节点功能。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from langchain_core.messages import HumanMessage

from src.agent.state import AgentState, AgentIntent
from src.agent.nodes import (
    intent_recognition_node,
    memory_retrieval_node,
    tool_selection_node,
    tool_execution_node,
    response_generation_node,
    _classify_intent,
)


@pytest.fixture
def sample_state():
    """创建测试用的状态。

    Returns:
        AgentState: 测试状态
    """
    return AgentState.create_initial(
        user_id="user_123",
        message="测试消息",
    )


# ==================== 意图识别节点测试 ====================


@pytest.mark.asyncio
async def test_intent_recognition_reminder(sample_state):
    """测试识别提醒意图。

    Args:
        sample_state: 测试状态
    """
    # 修改消息为提醒
    sample_state["messages"] = [HumanMessage(content="提醒我明天开会")]

    result = await intent_recognition_node(sample_state)

    assert result["intent"] == AgentIntent.REMINDER


@pytest.mark.asyncio
async def test_intent_recognition_task_create(sample_state):
    """测试识别任务创建意图。

    Args:
        sample_state: 测试状态
    """
    sample_state["messages"] = [HumanMessage(content="创建一个新任务")]

    result = await intent_recognition_node(sample_state)

    assert result["intent"] == AgentIntent.TASK_CREATE


@pytest.mark.asyncio
async def test_intent_recognition_chat(sample_state):
    """测试识别普通对话意图。

    Args:
        sample_state: 测试状态
    """
    sample_state["messages"] = [HumanMessage(content="你好")]

    result = await intent_recognition_node(sample_state)

    assert result["intent"] == AgentIntent.CHAT


@pytest.mark.asyncio
async def test_intent_recognition_error(sample_state):
    """测试意图识别错误处理。

    Args:
        sample_state: 测试状态
    """
    # 空消息列表
    sample_state["messages"] = []

    result = await intent_recognition_node(sample_state)

    assert result["intent"] == AgentIntent.UNKNOWN
    assert "error" in result


def test_classify_intent_reminder():
    """测试提醒意图分类。"""
    intent = _classify_intent("提醒我明天下午开会")
    assert intent == AgentIntent.REMINDER


def test_classify_intent_task():
    """测试任务创建意图分类。"""
    intent = _classify_intent("创建一个新任务")
    assert intent == AgentIntent.TASK_CREATE


def test_classify_intent_calendar():
    """测试日历查询意图分类。"""
    intent = _classify_intent("查询我的日历")
    assert intent == AgentIntent.CALENDAR_QUERY


def test_classify_intent_chat():
    """测试普通对话分类。"""
    intent = _classify_intent("你好，今天天气不错")
    assert intent == AgentIntent.CHAT


# ==================== 记忆检索节点测试 ====================


@pytest.mark.asyncio
async def test_memory_retrieval_success(sample_state):
    """测试记忆检索成功。

    Args:
        sample_state: 测试状态
    """
    with patch('src.agent.nodes.get_memory_client') as mock_get_client:
        mock_client = Mock()
        mock_client.is_enabled = True
        mock_client.search_memory = AsyncMock(return_value=[
            {
                "memory": "用户喜欢Python",
                "score": 0.95,
                "memory_id": "mem_1",
                "category": "preference",
                "created_at": "2026-02-06",
                "metadata": {}
            }
        ])
        mock_get_client.return_value = mock_client

        result = await memory_retrieval_node(sample_state)

        assert "memory_context" in result
        assert "用户喜欢Python" in result["memory_context"]


@pytest.mark.asyncio
async def test_memory_retrieval_disabled(sample_state):
    """测试记忆系统禁用时的行为。

    Args:
        sample_state: 测试状态
    """
    with patch('src.agent.nodes.get_memory_client') as mock_get_client:
        mock_client = Mock()
        mock_client.is_enabled = False
        mock_get_client.return_value = mock_client

        result = await memory_retrieval_node(sample_state)

        assert result["memory_context"] is None


@pytest.mark.asyncio
async def test_memory_retrieval_error(sample_state):
    """测试记忆检索错误处理。

    Args:
        sample_state: 测试状态
    """
    with patch('src.agent.nodes.get_memory_client') as mock_get_client:
        mock_client = Mock()
        mock_client.is_enabled = True
        mock_client.search_memory = AsyncMock(side_effect=Exception("DB error"))
        mock_get_client.return_value = mock_client

        result = await memory_retrieval_node(sample_state)

        assert result["memory_context"] is None
        assert "error" in result


# ==================== 工具选择节点测试 ====================


@pytest.mark.asyncio
async def test_tool_selection_reminder(sample_state):
    """测试为提醒意图选择工具。

    Args:
        sample_state: 测试状态
    """
    sample_state["intent"] = AgentIntent.REMINDER

    result = await tool_selection_node(sample_state)

    assert result["tool_name"] == "task_creation"
    assert result["next_action"] == "call_tool"


@pytest.mark.asyncio
async def test_tool_selection_chat(sample_state):
    """测试对话意图不选择工具。

    Args:
        sample_state: 测试状态
    """
    sample_state["intent"] = AgentIntent.CHAT

    result = await tool_selection_node(sample_state)

    assert result["tool_name"] is None
    assert result["next_action"] == "generate_response"


@pytest.mark.asyncio
async def test_tool_selection_calendar(sample_state):
    """测试日历查询工具选择。

    Args:
        sample_state: 测试状态
    """
    sample_state["intent"] = AgentIntent.CALENDAR_QUERY

    result = await tool_selection_node(sample_state)

    assert result["tool_name"] == "calendar_query"


# ==================== 工具执行节点测试 ====================


@pytest.mark.asyncio
async def test_tool_execution_success(sample_state):
    """测试工具执行成功。

    Args:
        sample_state: 测试状态
    """
    sample_state["tool_name"] = "task_creation"
    sample_state["tool_args"] = {
        "user_id": "user_123",
        "title": "测试任务",
    }

    with patch('src.agent.nodes.get_tool_registry') as mock_get_registry:
        mock_tool = Mock()
        mock_tool.execute = AsyncMock(return_value={
            "success": True,
            "task_id": "task_123",
        })

        mock_registry = Mock()
        mock_registry.get.return_value = mock_tool
        mock_get_registry.return_value = mock_registry

        result = await tool_execution_node(sample_state)

        assert result["tool_result"]["success"] is True
        assert result["next_action"] == "generate_response"


@pytest.mark.asyncio
async def test_tool_execution_not_found(sample_state):
    """测试工具未找到。

    Args:
        sample_state: 测试状态
    """
    sample_state["tool_name"] = "nonexistent_tool"
    sample_state["tool_args"] = {}

    with patch('src.agent.nodes.get_tool_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.get.return_value = None
        mock_get_registry.return_value = mock_registry

        result = await tool_execution_node(sample_state)

        assert result["tool_result"]["success"] is False
        assert "error" in result["tool_result"]


# ==================== 响应生成节点测试 ====================


@pytest.mark.asyncio
async def test_response_generation_chat(sample_state):
    """测试生成对话响应。

    Args:
        sample_state: 测试状态
    """
    sample_state["intent"] = AgentIntent.CHAT
    sample_state["memory_context"] = None
    sample_state["tool_result"] = None

    result = await response_generation_node(sample_state)

    assert "response" in result
    assert result["next_action"] == "end"


@pytest.mark.asyncio
async def test_response_generation_reminder_success(sample_state):
    """测试生成提醒成功响应。

    Args:
        sample_state: 测试状态
    """
    sample_state["intent"] = AgentIntent.REMINDER
    sample_state["tool_result"] = {
        "success": True,
        "title": "开会提醒",
    }
    sample_state["memory_context"] = None

    result = await response_generation_node(sample_state)

    assert "✅" in result["response"]
    assert "开会提醒" in result["response"]


@pytest.mark.asyncio
async def test_response_generation_reminder_failure(sample_state):
    """测试生成提醒失败响应。

    Args:
        sample_state: 测试状态
    """
    sample_state["intent"] = AgentIntent.REMINDER
    sample_state["tool_result"] = {
        "success": False,
    }
    sample_state["memory_context"] = None

    result = await response_generation_node(sample_state)

    assert "抱歉" in result["response"]


@pytest.mark.asyncio
async def test_response_generation_with_memory(sample_state):
    """测试带记忆上下文的响应生成。

    Args:
        sample_state: 测试状态
    """
    sample_state["intent"] = AgentIntent.CHAT
    sample_state["memory_context"] = "相关记忆:\n- 用户喜欢Python"
    sample_state["tool_result"] = None

    result = await response_generation_node(sample_state)

    assert "记忆" in result["response"]
