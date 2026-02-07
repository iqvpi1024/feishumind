"""Agent-to-Agent (A2A) 通信模块。

支持不同 Agent 之间的相互调用和协作。

Author: Claude Code
Date: 2026-02-06
"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import asyncio
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)


class AgentType(Enum):
    """Agent 类型枚举。

    Attributes:
        CALENDAR: 日历 Agent
        RESILIENCE: 韧性辅导 Agent
        GITHUB: GitHub Agent
        MEMORY: 记忆 Agent
        NOTIFICATION: 通知 Agent
    """

    CALENDAR = "calendar"
    RESILIENCE = "resilience"
    GITHUB = "github"
    MEMORY = "memory"
    NOTIFICATION = "notification"


class A2AMessage:
    """A2A 通信消息。

    Attributes:
        sender: 发送者 Agent 类型
        receiver: 接收者 Agent 类型
        action: 动作类型
        data: 数据载荷
        timestamp: 时间戳
        message_id: 消息 ID
    """

    def __init__(
        self,
        sender: AgentType,
        receiver: AgentType,
        action: str,
        data: Dict[str, Any],
        message_id: Optional[str] = None,
    ):
        """初始化 A2A 消息。

        Args:
            sender: 发送者
            receiver: 接收者
            action: 动作
            data: 数据
            message_id: 消息 ID（可选）
        """
        self.sender = sender
        self.receiver = receiver
        self.action = action
        self.data = data
        self.timestamp = datetime.now()
        self.message_id = message_id or f"{sender.value}_{receiver.value}_{int(self.timestamp.timestamp())}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。

        Returns:
            字典表示
        """
        return {
            "message_id": self.message_id,
            "sender": self.sender.value,
            "receiver": self.receiver.value,
            "action": self.action,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class A2AClient:
    """Agent-to-Agent 通信客户端。

    管理不同 Agent 之间的通信。

    Attributes:
        agent_registry: Agent 注册表
        message_history: 消息历史

    Examples:
        >>> client = A2AClient()
        >>> client.register_agent(AgentType.CALENDAR, calendar_handler)
        >>> response = await client.send_message(
        ...     AgentType.CALENDAR,
        ...     "get_events",
        ...     {"user_id": "123"}
        ... )
    """

    def __init__(self) -> None:
        """初始化 A2A 客户端。"""
        self.agent_registry: Dict[AgentType, Callable] = {}
        self.message_history: List[A2AMessage] = []
        logger.info("A2A client initialized")

    def register_agent(
        self,
        agent_type: AgentType,
        handler: Callable,
    ) -> None:
        """注册 Agent 处理器。

        Args:
            agent_type: Agent 类型
            handler: 处理函数（异步函数）

        Examples:
            >>> async def calendar_handler(action, data):
            ...     return {"events": []}
            >>> client.register_agent(AgentType.CALENDAR, calendar_handler)
        """
        self.agent_registry[agent_type] = handler
        logger.info(f"Registered agent: {agent_type.value}")

    async def send_message(
        self,
        receiver: AgentType,
        action: str,
        data: Dict[str, Any],
        sender: AgentType = AgentType.MEMORY,
    ) -> Dict[str, Any]:
        """发送消息到指定 Agent。

        Args:
            receiver: 接收者 Agent 类型
            action: 动作类型
            data: 数据载荷
            sender: 发送者 Agent 类型

        Returns:
            响应数据

        Raises:
            ValueError: 如果 Agent 未注册

        Examples:
            >>> response = await client.send_message(
            ...     AgentType.CALENDAR,
            ...     "get_events",
            ...     {"user_id": "123"}
            ... )
        """
        if receiver not in self.agent_registry:
            logger.error(f"Agent not registered: {receiver.value}")
            raise ValueError(f"Agent not registered: {receiver.value}")

        # 创建消息
        message = A2AMessage(
            sender=sender,
            receiver=receiver,
            action=action,
            data=data,
        )

        # 记录消息历史
        self.message_history.append(message)

        logger.info(
            f"Sending A2A message: {sender.value} -> {receiver.value}, "
            f"action={action}"
        )

        try:
            # 调用目标 Agent 的处理器
            handler = self.agent_registry[receiver]
            response = await handler(action, data)

            logger.info(f"A2A message succeeded: {message.message_id}")
            return response

        except Exception as e:
            logger.error(f"A2A message failed: {message.message_id}, error={e}")
            return {
                "success": False,
                "error": str(e),
                "message_id": message.message_id,
            }

    async def broadcast_message(
        self,
        action: str,
        data: Dict[str, Any],
        sender: AgentType = AgentType.MEMORY,
        exclude: Optional[List[AgentType]] = None,
    ) -> Dict[AgentType, Dict[str, Any]]:
        """广播消息到所有 Agent。

        Args:
            action: 动作类型
            data: 数据载荷
            sender: 发送者 Agent 类型
            exclude: 排除的 Agent 列表

        Returns:
            所有 Agent 的响应字典

        Examples:
            >>> responses = await client.broadcast_message(
            ...     "update_context",
            ...     {"user_id": "123"}
            ... )
        """
        exclude = exclude or []
        responses = {}

        for agent_type in self.agent_registry:
            if agent_type in exclude or agent_type == sender:
                continue

            try:
                response = await self.send_message(
                    receiver=agent_type,
                    action=action,
                    data=data,
                    sender=sender,
                )
                responses[agent_type] = response

            except Exception as e:
                logger.error(f"Broadcast to {agent_type.value} failed: {e}")
                responses[agent_type] = {
                    "success": False,
                    "error": str(e),
                }

        return responses

    def get_message_history(
        self,
        sender: Optional[AgentType] = None,
        receiver: Optional[AgentType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取消息历史。

        Args:
            sender: 过滤发送者
            receiver: 过滤接收者
            limit: 限制数量

        Returns:
            消息历史列表
        """
        messages = self.message_history

        # 过滤
        if sender:
            messages = [m for m in messages if m.sender == sender]
        if receiver:
            messages = [m for m in messages if m.receiver == receiver]

        # 限制数量
        messages = messages[-limit:]

        # 转换为字典
        return [m.to_dict() for m in messages]

    def clear_history(self) -> None:
        """清空消息历史。"""
        self.message_history.clear()
        logger.info("A2A message history cleared")


class CalendarAgentClient:
    """日历 Agent 客户端。

    提供日历相关功能的封装。

    Attributes:
        a2a_client: A2A 通信客户端

    Examples:
        >>> client = CalendarAgentClient(a2a_client)
        >>> events = await client.get_events(user_id="123")
    """

    def __init__(self, a2a_client: A2AClient) -> None:
        """初始化日历 Agent 客户端。

        Args:
            a2a_client: A2A 通信客户端
        """
        self.a2a_client = a2a_client
        logger.info("Calendar agent client initialized")

    async def get_events(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取用户的日历事件。

        Args:
            user_id: 用户 ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            事件列表

        Examples:
            >>> events = await client.get_events("123", "2026-02-06", "2026-02-13")
        """
        response = await self.a2a_client.send_message(
            receiver=AgentType.CALENDAR,
            action="get_events",
            data={
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
            },
            sender=AgentType.RESILIENCE,
        )

        return response.get("events", [])

    async def create_event(
        self,
        user_id: str,
        title: str,
        start_time: str,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建日历事件。

        Args:
            user_id: 用户 ID
            title: 事件标题
            start_time: 开始时间
            end_time: 结束时间（可选）
            description: 描述（可选）

        Returns:
            创建结果

        Examples:
            >>> result = await client.create_event(
            ...     "123",
            ...     "团队会议",
            ...     "2026-02-07T14:00:00"
            ... )
        """
        response = await self.a2a_client.send_message(
            receiver=AgentType.CALENDAR,
            action="create_event",
            data={
                "user_id": user_id,
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "description": description,
            },
            sender=AgentType.RESILIENCE,
        )

        return response

    async def get_upcoming_events(
        self,
        user_id: str,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """获取未来几天的日程。

        Args:
            user_id: 用户 ID
            days: 天数

        Returns:
            事件列表

        Examples:
            >>> events = await client.get_upcoming_events("123", days=7)
        """
        response = await self.a2a_client.send_message(
            receiver=AgentType.CALENDAR,
            action="get_upcoming_events",
            data={
                "user_id": user_id,
                "days": days,
            },
            sender=AgentType.RESILIENCE,
        )

        return response.get("events", [])


class ResilienceAgentClient:
    """韧性辅导 Agent 客户端。

    提供韧性辅导功能的封装。

    Attributes:
        a2a_client: A2A 通信客户端

    Examples:
        >>> client = ResilienceAgentClient(a2a_client)
        >>> score = await client.analyze_emotion("今天压力很大")
    """

    def __init__(self, a2a_client: A2AClient) -> None:
        """初始化韧性辅导 Agent 客户端。

        Args:
            a2a_client: A2A 通信客户端
        """
        self.a2a_client = a2a_client
        logger.info("Resilience agent client initialized")

    async def analyze_emotion(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """分析情绪。

        Args:
            text: 输入文本

        Returns:
            情绪分析结果

        Examples:
            >>> result = await client.analyze_emotion("今天压力很大")
            >>> print(result["emotion_type"])
        """
        response = await self.a2a_client.send_message(
            receiver=AgentType.RESILIENCE,
            action="analyze_emotion",
            data={"text": text},
            sender=AgentType.MEMORY,
        )

        return response

    async def get_resilience_score(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """获取韧性评分。

        Args:
            user_id: 用户 ID

        Returns:
            韧性评分

        Examples:
            >>> score = await client.get_resilience_score("123")
        """
        response = await self.a2a_client.send_message(
            receiver=AgentType.RESILIENCE,
            action="get_score",
            data={"user_id": user_id},
            sender=AgentType.MEMORY,
        )

        return response

    async def get_suggestions(
        self,
        stress_level: str,
        dimension: str,
        emotion_type: str,
    ) -> List[Dict[str, str]]:
        """获取韧性建议。

        Args:
            stress_level: 压力等级
            dimension: 情绪维度
            emotion_type: 情绪类型

        Returns:
            建议列表

        Examples:
            >>> suggestions = await client.get_suggestions("high", "工作", "anxiety")
        """
        response = await self.a2a_client.send_message(
            receiver=AgentType.RESILIENCE,
            action="get_suggestions",
            data={
                "stress_level": stress_level,
                "dimension": dimension,
                "emotion_type": emotion_type,
            },
            sender=AgentType.MEMORY,
        )

        return response.get("suggestions", [])


# 全局 A2A 客户端实例
_global_a2a_client: Optional[A2AClient] = None


def get_a2a_client() -> A2AClient:
    """获取全局 A2A 客户端实例。

    Returns:
        A2A 客户端实例

    Examples:
        >>> client = get_a2a_client()
        >>> response = await client.send_message(...)
    """
    global _global_a2a_client
    if _global_a2a_client is None:
        _global_a2a_client = A2AClient()
    return _global_a2a_client


def set_a2a_client(client: A2AClient) -> None:
    """设置全局 A2A 客户端实例。

    Args:
        client: A2A 客户端实例

    Examples:
        >>> client = A2AClient()
        >>> set_a2a_client(client)
    """
    global _global_a2a_client
    _global_a2a_client = client
