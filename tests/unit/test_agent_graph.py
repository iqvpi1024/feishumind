"""Agent 工作流单元测试模块。

测试 LangGraph 工作流的构建和执行。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.agent.state import AgentState, AgentAction
from src.agent.graph import (
    create_agent_graph,
    compile_agent_graph,
    run_agent,
    should_call_tool,
    should_request_feedback,
)


# ==================== 工作流构建测试 ====================


def test_create_agent_graph():
    """测试创建 Agent 工作流。"""
    graph = create_agent_graph()

    assert graph is not None
    # 验证节点已添加
    nodes = graph.nodes
    assert "intent_recognition" in nodes
    assert "memory_retrieval" in nodes
    assert "tool_selection" in nodes
    assert "tool_execution" in nodes
    assert "response_generation" in nodes
    assert "human_feedback" in nodes


def test_compile_agent_graph():
    """测试编译工作流。"""
    compiled = compile_agent_graph(use_checkpointer=False)

    assert compiled is not None


def test_compile_agent_graph_with_checkpointer():
    """测试编译带检查点的工作流。"""
    compiled = compile_agent_graph(use_checkpointer=True)

    assert compiled is not None


# ==================== 条件边测试 ====================


def test_should_call_tool_true():
    """测试需要调用工具的情况。"""
    state = AgentState.create_initial("user_123", "创建任务")
    state["next_action"] = AgentAction.CALL_TOOL

    result = should_call_tool(state)

    assert result == "tool_execution"


def test_should_call_tool_false():
    """测试不需要调用工具的情况。"""
    state = AgentState.create_initial("user_123", "你好")
    state["next_action"] = AgentAction.GENERATE_RESPONSE

    result = should_call_tool(state)

    assert result == "response_generation"


def test_should_request_feedback():
    """测试是否需要反馈（当前直接结束）。"""
    state = AgentState.create_initial("user_123", "你好")

    result = should_request_feedback(state)

    assert result == "end"


# ==================== 工作流执行测试 ====================


@pytest.mark.asyncio
async def test_run_agent_chat():
    """测试运行 Agent（对话场景）。"""
    with patch('src.agent.graph.compile_agent_graph') as mock_compile:
        # 创建模拟的编译图
        mock_graph = Mock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "response": "你好！有什么我可以帮助你的吗？",
            "intent": "chat",
            "next_action": "end",
        })
        mock_compile.return_value = mock_graph

        result = await run_agent(
            user_id="user_123",
            message="你好",
        )

        assert result["response"] == "你好！有什么我可以帮助你的吗？"
        mock_graph.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_run_agent_reminder():
    """测试运行 Agent（提醒场景）。"""
    with patch('src.agent.graph.compile_agent_graph') as mock_compile:
        mock_graph = Mock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "response": "✅ 已为你创建提醒：开会",
            "intent": "reminder",
            "tool_name": "task_creation",
            "tool_result": {
                "success": True,
                "title": "开会",
            },
            "next_action": "end",
        })
        mock_compile.return_value = mock_graph

        result = await run_agent(
            user_id="user_123",
            message="提醒我明天开会",
        )

        assert "✅" in result["response"]
        assert result["tool_name"] == "task_creation"


@pytest.mark.asyncio
async def test_run_agent_error():
    """测试运行 Agent（错误处理）。"""
    with patch('src.agent.graph.compile_agent_graph') as mock_compile:
        mock_graph = Mock()
        mock_graph.ainvoke = AsyncMock(side_effect=Exception("Graph execution failed"))
        mock_compile.return_value = mock_graph

        result = await run_agent(
            user_id="user_123",
            message="测试",
        )

        assert "error" in result
        assert "抱歉" in result["response"]


# ==================== 状态转换测试 ====================


@pytest.mark.asyncio
async def test_full_workflow_simulation():
    """测试完整工作流模拟。"""
    # 模拟完整的状态转换
    state = AgentState.create_initial("user_123", "创建任务：完成代码审查")

    # 1. 意图识别
    from src.agent.nodes import intent_recognition_node
    state.update(await intent_recognition_node(state))
    assert state["intent"] == "task_create"

    # 2. 记忆检索
    from src.agent.nodes import memory_retrieval_node
    with patch('src.agent.nodes.get_memory_client') as mock_get_client:
        mock_client = Mock()
        mock_client.is_enabled = True
        mock_client.search_memory = AsyncMock(return_value=[])
        mock_get_client.return_value = mock_client

        state.update(await memory_retrieval_node(state))
        assert "memory_context" in state

    # 3. 工具选择
    from src.agent.nodes import tool_selection_node
    state.update(await tool_selection_node(state))
    assert state["tool_name"] == "task_creation"
    assert state["next_action"] == "call_tool"

    # 4. 工具执行
    from src.agent.nodes import tool_execution_node
    with patch('src.agent.nodes.get_tool_registry') as mock_get_registry:
        mock_tool = Mock()
        mock_tool.execute = AsyncMock(return_value={
            "success": True,
            "task_id": "task_123",
            "title": "完成代码审查",
        })

        mock_registry = Mock()
        mock_registry.get.return_value = mock_tool
        mock_get_registry.return_value = mock_registry

        state.update(await tool_execution_node(state))
        assert state["tool_result"]["success"] is True

    # 5. 响应生成
    from src.agent.nodes import response_generation_node
    state.update(await response_generation_node(state))
    assert "response" in state
    assert "✅" in state["response"]
    assert state["next_action"] == "end"


# ==================== 集成测试 ====================


@pytest.mark.asyncio
async def test_agent_with_memory_integration():
    """测试 Agent 与记忆系统的集成。"""
    from src.agent.graph import run_agent
    from src.agent.nodes import memory_retrieval_node

    with patch('src.agent.graph.compile_agent_graph') as mock_compile:
        mock_graph = Mock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "response": "根据你的记忆，你喜欢Python",
            "intent": "chat",
            "memory_context": "相关记忆:\n- 用户喜欢Python (相关度: 0.95)",
            "next_action": "end",
        })
        mock_compile.return_value = mock_graph

        result = await run_agent(
            user_id="user_123",
            message="我喜欢什么编程语言？",
        )

        assert "记忆" in result["response"]


@pytest.mark.asyncio
async def test_agent_with_tool_integration():
    """测试 Agent 与工具系统的集成。"""
    from src.agent.graph import run_agent

    with patch('src.agent.graph.compile_agent_graph') as mock_compile:
        mock_graph = Mock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "response": "✅ 任务已创建：查询日历",
            "intent": "calendar_query",
            "tool_name": "calendar_query",
            "tool_result": {
                "success": True,
                "events": [
                    {"title": "周会", "start": "10:00", "end": "11:00"}
                ]
            },
            "next_action": "end",
        })
        mock_compile.return_value = mock_graph

        result = await run_agent(
            user_id="user_123",
            message="查询我的日历",
        )

        assert result["tool_name"] == "calendar_query"
        assert result["tool_result"]["success"] is True
