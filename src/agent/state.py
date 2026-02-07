"""LangGraph Agent 状态管理模块。

本模块定义 Agent 的状态结构，用于在状态机的各个节点之间传递数据。
遵循 PEP 8 规范，使用类型注解和完整文档。
"""

from typing import List, Optional, Dict, Any, TypedDict, Callable
from langchain_core.messages import BaseMessage
from enum import Enum


class AgentIntent(str, Enum):
    """Agent 意图枚举。

    定义 Agent 可以识别的用户意图类型。
    """

    CHAT = "chat"  # 普通对话
    REMINDER = "reminder"  # 设置提醒
    TASK_CREATE = "task_create"  # 创建任务
    TASK_QUERY = "task_query"  # 查询任务
    CALENDAR_QUERY = "calendar_query"  # 查询日历
    NOTIFICATION = "notification"  # 发送通知
    UNKNOWN = "unknown"  # 未知意图


class AgentAction(str, Enum):
    """Agent 动作枚举。

    定义 Agent 可以执行的动作类型。
    """

    GENERATE_RESPONSE = "generate_response"  # 生成响应
    CALL_TOOL = "call_tool"  # 调用工具
    REQUEST_FEEDBACK = "request_feedback"  # 请求反馈
    END = "end"  # 结束对话


class AgentState(TypedDict):
    """LangGraph Agent 状态类。

    定义 Agent 状态机的完整状态结构，包含对话历史、用户信息、
    识别的意图、可用工具、记忆上下文等。

    Attributes:
        messages: 对话历史消息列表
        user_id: 用户ID（飞书用户ID）
        intent: 识别的用户意图
        tools: 可用工具列表
        memory_context: 检索到的记忆上下文
        next_action: 下一个要执行的动作
        tool_name: 选择的工具名称
        tool_args: 工具调用参数
        tool_result: 工具执行结果
        response: 生成的响应内容
        metadata: 额外的元数据
        error: 错误信息（如果有）
    """

    # 对话历史
    messages: List[BaseMessage]

    # 用户信息
    user_id: str

    # 意图识别
    intent: AgentIntent

    # 工具相关
    tools: List[str]
    tool_name: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]

    # 记忆上下文
    memory_context: Optional[str]

    # 动作控制
    next_action: AgentAction

    # 响应生成
    response: Optional[str]

    # 元数据和错误处理
    metadata: Dict[str, Any]
    error: Optional[str]

    def validate(self) -> bool:
        """验证状态的有效性。

        检查必需字段是否存在，以及数据类型是否正确。

        Returns:
            bool: 状态是否有效

        Examples:
            >>> state = AgentState(
            ...     messages=[],
            ...     user_id="user_123",
            ...     intent=AgentIntent.CHAT,
            ...     tools=[],
            ...     tool_name=None,
            ...     tool_args=None,
            ...     tool_result=None,
            ...     memory_context=None,
            ...     next_action=AgentAction.GENERATE_RESPONSE,
            ...     response=None,
            ...     metadata={},
            ...     error=None
            ... )
            >>> assert state.validate()
        """
        # 检查必需字段
        if not self.user_id:
            return False

        if not isinstance(self.messages, list):
            return False

        # 检查枚举类型
        if not isinstance(self.intent, AgentIntent):
            return False

        if not isinstance(self.next_action, AgentAction):
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """将状态转换为字典。

        用于序列化和日志记录。

        Returns:
            Dict[str, Any]: 状态字典
        """
        return {
            "user_id": self.user_id,
            "intent": self.intent.value if isinstance(self.intent, AgentIntent) else self.intent,
            "next_action": self.next_action.value if isinstance(self.next_action, AgentAction) else self.next_action,
            "tools": self.tools,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "memory_context": self.memory_context,
            "response": self.response,
            "error": self.error,
            "message_count": len(self.messages),
            "metadata": self.metadata,
        }

    @classmethod
    def create_initial(
        cls,
        user_id: str,
        message: str,
    ) -> "AgentState":
        """创建初始状态。

        用于开始新的对话。

        Args:
            user_id: 用户ID
            message: 用户消息

        Returns:
            AgentState: 初始状态

        Examples:
            >>> from langchain_core.messages import HumanMessage
            >>> state = AgentState.create_initial(
            ...     user_id="user_123",
            ...     message="你好，帮我提醒明天开会"
            ... )
            >>> assert state["user_id"] == "user_123"
            >>> assert state["intent"] == AgentIntent.UNKNOWN
        """
        from langchain_core.messages import HumanMessage

        return cls(
            messages=[HumanMessage(content=message)],
            user_id=user_id,
            intent=AgentIntent.UNKNOWN,
            tools=[],
            tool_name=None,
            tool_args=None,
            tool_result=None,
            memory_context=None,
            next_action=AgentAction.GENERATE_RESPONSE,
            response=None,
            metadata={},
            error=None,
        )


def create_state_update(
    current_state: AgentState,
    **updates: Any,
) -> Dict[str, Any]:
    """创建状态更新字典。

    辅助函数，用于生成状态更新。

    Args:
        current_state: 当前状态
        **updates: 要更新的字段

    Returns:
        Dict[str, Any]: 状态更新字典

    Examples:
        >>> update = create_state_update(
        ...     state,
        ...     intent=AgentIntent.REMINDER,
        ...     next_action=AgentAction.CALL_TOOL
        ... )
    """
    return updates


# 工具类型定义
ToolFunction = Callable[..., Dict[str, Any]]


class ToolDefinition(TypedDict):
    """工具定义类型。

    定义工具的元数据结构。

    Attributes:
        name: 工具名称
        description: 工具描述
        parameters: 参数定义（JSON Schema）
        function: 工具函数
    """

    name: str
    description: str
    parameters: Dict[str, Any]
    function: ToolFunction


def validate_tool_args(
    tool_def: ToolDefinition,
    args: Dict[str, Any],
) -> bool:
    """验证工具参数。

    检查工具调用参数是否符合工具定义。

    Args:
        tool_def: 工具定义
        args: 工具参数

    Returns:
        bool: 参数是否有效

    Examples:
        >>> tool_def = ToolDefinition(
        ...     name="test_tool",
        ...     description="Test",
        ...     parameters={"required": ["arg1"]},
        ...     function=lambda x: x
        ... )
        >>> validate_tool_args(tool_def, {"arg1": "value"})
        True
        >>> validate_tool_args(tool_def, {})
        False
    """
    required = tool_def["parameters"].get("required", [])

    for param in required:
        if param not in args:
            return False

    return True
