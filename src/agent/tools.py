"""Agent 工具注册和管理模块。

本模块定义工具基类、工具注册表和内置工具实现。
"""

import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from src.agent.state import ToolDefinition, validate_tool_args
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseTool(ABC):
    """工具基类。

    所有工具必须继承此类并实现 execute 方法。

    Attributes:
        name: 工具名称
        description: 工具描述

    Examples:
        >>> class MyTool(BaseTool):
        ...     name = "my_tool"
        ...     description = "My custom tool"
        ...
        ...     async def execute(self, **kwargs):
        ...         return {"success": True, "result": "done"}
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行工具逻辑。

        Args:
            **kwargs: 工具参数

        Returns:
            Dict[str, Any]: 执行结果，必须包含 success 字段

        Raises:
            Exception: 执行失败时
        """
        pass

    @property
    def parameters(self) -> Dict[str, Any]:
        """获取工具参数定义（JSON Schema）。

        Returns:
            Dict[str, Any]: JSON Schema 格式的参数定义
        """
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def to_definition(self) -> ToolDefinition:
        """转换为工具定义。

        Returns:
            ToolDefinition: 工具定义字典
        """
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            function=self.execute,
        )


class FeishuNotificationTool(BaseTool):
    """飞书通知工具。

    用于发送飞书消息通知。

    Attributes:
        name: 工具名称
        description: 工具描述
    """

    name = "feishu_notification"
    description = "发送飞书消息通知"

    @property
    def parameters(self) -> Dict[str, Any]:
        """参数定义。"""
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "飞书用户ID",
                },
                "message": {
                    "type": "string",
                    "description": "通知内容",
                },
                "msg_type": {
                    "type": "string",
                    "enum": ["text", "post"],
                    "description": "消息类型",
                },
            },
            "required": ["user_id", "message"],
        }

    async def execute(
        self,
        user_id: str,
        message: str,
        msg_type: str = "text",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """发送飞书通知。

        Args:
            user_id: 飞书用户ID
            message: 通知内容
            msg_type: 消息类型
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 发送结果

        Examples:
            >>> tool = FeishuNotificationTool()
            >>> result = await tool.execute(
            ...     user_id="ou_xxx",
            ...     message="明天上午9点开会"
            ... )
            >>> assert result["success"]
        """
        try:
            # TODO: 集成真实的飞书 API
            # 当前为模拟实现

            logger.info(
                f"Sending Feishu notification to {user_id[:4]}***: "
                f"{message[:50]}..."
            )

            # 模拟发送
            return {
                "success": True,
                "message_id": f"msg_{datetime.utcnow().timestamp()}",
                "result": "Notification sent",
                "user_id": user_id,
                "content": message,
            }

        except Exception as e:
            logger.error(f"Failed to send Feishu notification: {e}")
            return {
                "success": False,
                "error": str(e),
            }


class CalendarQueryTool(BaseTool):
    """日历查询工具。

    用于查询用户的日历安排。

    Attributes:
        name: 工具名称
        description: 工具描述
    """

    name = "calendar_query"
    description = "查询用户日历安排"

    @property
    def parameters(self) -> Dict[str, Any]:
        """参数定义。"""
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID",
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期 (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期 (YYYY-MM-DD)",
                },
            },
            "required": ["user_id"],
        }

    async def execute(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """查询日历。

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 查询结果

        Examples:
            >>> tool = CalendarQueryTool()
            >>> result = await tool.execute(
            ...     user_id="user_123",
            ...     start_date="2026-02-06"
            ... )
            >>> assert result["success"]
        """
        try:
            # TODO: 集成真实的日历 API
            # 当前为模拟实现

            # 默认查询今天
            if not start_date:
                start_date = datetime.now().strftime("%Y-%m-%d")

            logger.info(
                f"Querying calendar for {user_id[:4]}*** "
                f"from {start_date} to {end_date}"
            )

            # 模拟返回数据
            events = [
                {
                    "title": "团队周会",
                    "start": f"{start_date} 10:00",
                    "end": f"{start_date} 11:00",
                    "location": "会议室A",
                }
            ]

            return {
                "success": True,
                "events": events,
                "count": len(events),
            }

        except Exception as e:
            logger.error(f"Failed to query calendar: {e}")
            return {
                "success": False,
                "error": str(e),
            }


class TaskCreationTool(BaseTool):
    """任务创建工具。

    用于创建待办任务。

    Attributes:
        name: 工具名称
        description: 工具描述
    """

    name = "task_creation"
    description = "创建待办任务"

    @property
    def parameters(self) -> Dict[str, Any]:
        """参数定义。"""
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户ID",
                },
                "title": {
                    "type": "string",
                    "description": "任务标题",
                },
                "description": {
                    "type": "string",
                    "description": "任务描述",
                },
                "due_date": {
                    "type": "string",
                    "description": "截止日期 (YYYY-MM-DD)",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "优先级",
                },
            },
            "required": ["user_id", "title"],
        }

    async def execute(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: str = "medium",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """创建任务。

        Args:
            user_id: 用户ID
            title: 任务标题
            description: 任务描述
            due_date: 截止日期
            priority: 优先级
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 创建结果

        Examples:
            >>> tool = TaskCreationTool()
            >>> result = await tool.execute(
            ...     user_id="user_123",
            ...     title="完成代码审查",
            ...     priority="high"
            ... )
            >>> assert result["success"]
        """
        try:
            # TODO: 集成真实的任务管理 API
            # 当前为模拟实现

            logger.info(
                f"Creating task for {user_id[:4]}***: "
                f"{title[:50]}..."
            )

            task_id = f"task_{datetime.utcnow().timestamp()}"

            return {
                "success": True,
                "task_id": task_id,
                "title": title,
                "description": description,
                "due_date": due_date,
                "priority": priority,
                "status": "pending",
            }

        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return {
                "success": False,
                "error": str(e),
            }


class ToolRegistry:
    """工具注册表。

    管理所有可用的工具。

    Attributes:
        _tools: 工具字典

    Examples:
        >>> registry = ToolRegistry()
        >>> registry.register(FeishuNotificationTool())
        >>> tool = registry.get("feishu_notification")
        >>> assert tool is not None
    """

    def __init__(self) -> None:
        """初始化工具注册表。"""
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具。

        Args:
            tool: 工具实例

        Raises:
            ValueError: 工具名称已存在

        Examples:
            >>> registry = ToolRegistry()
            >>> registry.register(FeishuNotificationTool())
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")

        self._tools[tool.name] = tool
        logger.info(f"Tool registered: {tool.name}")

    def unregister(self, tool_name: str) -> None:
        """注销工具。

        Args:
            tool_name: 工具名称

        Examples:
            >>> registry = ToolRegistry()
            >>> registry.unregister("feishu_notification")
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"Tool unregistered: {tool_name}")

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具。

        Args:
            tool_name: 工具名称

        Returns:
            Optional[BaseTool]: 工具实例，不存在则返回 None

        Examples:
            >>> registry = ToolRegistry()
            >>> tool = registry.get("feishu_notification")
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """列出所有工具名称。

        Returns:
            List[str]: 工具名称列表

        Examples:
            >>> registry = ToolRegistry()
            >>> tools = registry.list_tools()
            >>> assert "feishu_notification" in tools
        """
        return list(self._tools.keys())

    def get_all_definitions(self) -> List[ToolDefinition]:
        """获取所有工具定义。

        Returns:
            List[ToolDefinition]: 工具定义列表

        Examples:
            >>> registry = ToolRegistry()
            >>> definitions = registry.get_all_definitions()
        """
        return [tool.to_definition() for tool in self._tools.values()]


# 全局工具注册表（单例模式）
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表（单例模式）。

    Returns:
        ToolRegistry: 工具注册表实例

    Examples:
        >>> registry = get_tool_registry()
        >>> assert registry is not None
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        # 注册默认工具
        _registry.register(FeishuNotificationTool())
        _registry.register(CalendarQueryTool())
        _registry.register(TaskCreationTool())
        logger.info("Default tools registered")
    return _registry


def reset_tool_registry() -> None:
    """重置工具注册表（主要用于测试）。"""
    global _registry
    _registry = None
