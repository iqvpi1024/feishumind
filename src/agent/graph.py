"""LangGraph 工作流构建模块。

本模块定义 Agent 的状态转换图和执行流程。
"""

import logging
from typing import Literal, Dict, Any, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agent.state import AgentState, AgentAction
from src.agent.nodes import (
    intent_recognition_node,
    memory_retrieval_node,
    tool_selection_node,
    tool_execution_node,
    response_generation_node,
    human_feedback_node,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ==================== 条件边函数 ====================

def should_call_tool(state: AgentState) -> Literal["tool_execution", "response_generation"]:
    """判断是否需要调用工具。

    Args:
        state: 当前状态

    Returns:
        Literal["tool_execution", "response_generation"]: 下一个节点
    """
    next_action = state.get("next_action")

    if next_action == AgentAction.CALL_TOOL:
        logger.info("Routing to tool_execution")
        return "tool_execution"
    else:
        logger.info("Routing to response_generation")
        return "response_generation"


def should_request_feedback(state: AgentState) -> Literal["human_feedback", "end"]:
    """判断是否需要请求人类反馈。

    Args:
        state: 当前状态

    Returns:
        Literal["human_feedback", "end"]: 下一个节点
    """
    # TODO: 实现反馈逻辑
    # 当前直接结束
    logger.info("Routing to end")
    return "end"


# ==================== 工作流构建 ====================

def create_agent_graph() -> StateGraph:
    """创建 Agent 状态转换图。

    构建完整的状态机，包含所有节点和转换边。

    Returns:
        StateGraph: LangGraph 状态转换图

    Examples:
        >>> graph = create_agent_graph()
        >>> assert graph is not None
    """
    logger.info("Creating Agent state graph")

    # 创建状态图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent_recognition", intent_recognition_node)
    workflow.add_node("memory_retrieval", memory_retrieval_node)
    workflow.add_node("tool_selection", tool_selection_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("response_generation", response_generation_node)
    workflow.add_node("human_feedback", human_feedback_node)

    # 设置入口点
    workflow.set_entry_point("intent_recognition")

    # 添加边（固定转换）
    workflow.add_edge("intent_recognition", "memory_retrieval")
    workflow.add_edge("memory_retrieval", "tool_selection")

    # 添加条件边（动态转换）
    workflow.add_conditional_edges(
        "tool_selection",
        should_call_tool,
        {
            "tool_execution": "tool_execution",
            "response_generation": "response_generation",
        },
    )

    workflow.add_edge("tool_execution", "response_generation")

    workflow.add_conditional_edges(
        "response_generation",
        should_request_feedback,
        {
            "human_feedback": "human_feedback",
            "end": END,
        },
    )

    workflow.add_edge("human_feedback", END)

    logger.info("Agent state graph created successfully")

    return workflow


def compile_agent_graph(
    use_checkpointer: bool = True,
) -> Any:
    """编译 Agent 图为可执行的工作流。

    Args:
        use_checkpointer: 是否使用检查点（支持中断和恢复）

    Returns:
        CompiledGraph: 编译后的工作流

    Examples:
        >>> graph = compile_agent_graph()
        >>> result = await graph.ainvoke(state)
    """
    # 创建工作流
    workflow = create_agent_graph()

    # 配置检查点（可选）
    if use_checkpointer:
        checkpointer = MemorySaver()
        logger.info("Using checkpointer for state persistence")
    else:
        checkpointer = None
        logger.info("Checkpointer disabled")

    # 编译工作流
    compiled_graph = workflow.compile(
        checkpointer=checkpointer,
    )

    logger.info("Agent graph compiled successfully")

    return compiled_graph


# ==================== 工作流执行 ====================

async def run_agent(
    user_id: str,
    message: str,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """运行 Agent 工作流。

    Args:
        user_id: 用户ID
        message: 用户消息
        config: 配置参数

    Returns:
        Dict[str, Any]: 执行结果

    Examples:
        >>> result = await run_agent(
        ...     user_id="user_123",
        ...     message="提醒我明天开会"
        ... )
        >>> assert result["response"]
    """
    try:
        # 创建初始状态
        initial_state = AgentState.create_initial(
            user_id=user_id,
            message=message,
        )

        logger.info(
            f"Running agent for {user_id[:4]}***: "
            f"{message[:50]}..."
        )

        # 编译工作流
        graph = compile_agent_graph()

        # 配置执行参数
        run_config = {
            "configurable": {
                "thread_id": user_id,
            },
        }

        if config:
            run_config.update(config)

        # 执行工作流
        result = await graph.ainvoke(initial_state, run_config)

        logger.info(
            f"Agent execution completed for {user_id[:4]}***"
        )

        return result

    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return {
            "error": str(e),
            "response": "抱歉，处理你的请求时遇到了错误。",
        }


# ==================== 工作流可视化 ====================

def print_graph_structure() -> None:
    """打印工作流结构（用于调试）。

    Examples:
        >>> print_graph_structure()
    """
    logger.info("Agent Graph Structure:")
    logger.info("START")
    logger.info("  ↓")
    logger.info("intent_recognition")
    logger.info("  ↓")
    logger.info("memory_retrieval")
    logger.info("  ↓")
    logger.info("tool_selection")
    logger.info("  ↓ (conditional)")
    logger.info("  ├─ tool_execution ──┐")
    logger.info("  │                   │")
    logger.info("  └─ response_generation ←─┘")
    logger.info("           ↓ (conditional)")
    logger.info("       ├─ human_feedback ──┐")
    logger.info("       │                   │")
    logger.info("       └─ END ←────────────┘")
