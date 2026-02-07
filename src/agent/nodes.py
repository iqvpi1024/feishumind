"""LangGraph Agent 状态机节点实现。

本模块定义 Agent 的各个状态节点，包括意图识别、记忆检索、
工具选择、工具执行、响应生成和人类反馈。
"""

import logging
import os
from typing import Dict, Any, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from openai import OpenAI

from src.agent.state import (
    AgentState,
    AgentIntent,
    AgentAction,
    create_state_update,
)
from src.agent.tools import get_tool_registry, BaseTool
from src.memory.client import MemoryClient, get_memory_client
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 初始化 DeepSeek 客户端
DEEPSEEK_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")

if DEEPSEEK_API_KEY:
    llm_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )
    logger.info(f"DeepSeek LLM client initialized: {DEEPSEEK_MODEL}")
else:
    llm_client = None
    logger.warning("DeepSeek API key not found, LLM features disabled")


# ==================== 意图识别节点 ====================

async def intent_recognition_node(
    state: AgentState,
) -> Dict[str, Any]:
    """意图识别节点。

    分析用户消息，识别用户意图。

    Args:
        state: 当前状态

    Returns:
        Dict[str, Any]: 状态更新

    Examples:
        >>> state = AgentState.create_initial("user_123", "提醒我明天开会")
        >>> update = await intent_recognition_node(state)
        >>> assert update["intent"] == AgentIntent.REMINDER
    """
    try:
        # 获取最新消息
        latest_message = state["messages"][-1]
        user_input = latest_message.content

        logger.info(f"Recognizing intent for: {user_input[:50]}...")

        # TODO: 集成真实的意图识别模型
        # 当前使用基于规则的关键词匹配

        # 简单的关键词匹配逻辑
        intent = _classify_intent(user_input)

        logger.info(f"Intent recognized: {intent.value}")

        return create_state_update(
            state,
            intent=intent,
        )

    except Exception as e:
        logger.error(f"Intent recognition failed: {e}")
        return create_state_update(
            state,
            intent=AgentIntent.UNKNOWN,
            error=str(e),
        )


def _classify_intent(text: str) -> AgentIntent:
    """基于规则的意图分类。

    Args:
        text: 用户输入文本

    Returns:
        AgentIntent: 识别的意图
    """
    text_lower = text.lower()

    # 关键词映射
    keywords = {
        AgentIntent.REMINDER: ["提醒", "remember", "remind", "不要忘记"],
        AgentIntent.TASK_CREATE: ["创建任务", "新建任务", "todo", "任务"],
        AgentIntent.TASK_QUERY: ["查询任务", "我的任务", "任务列表", "todo list"],
        AgentIntent.CALENDAR_QUERY: ["日历", "日程", "安排", "calendar"],
        AgentIntent.NOTIFICATION: ["通知", "发送消息", "告诉"],
    }

    # 匹配关键词
    for intent, words in keywords.items():
        if any(word in text_lower for word in words):
            return intent

    return AgentIntent.CHAT


# ==================== 记忆检索节点 ====================

async def memory_retrieval_node(
    state: AgentState,
) -> Dict[str, Any]:
    """记忆检索节点。

    从记忆系统中检索相关的用户记忆。

    Args:
        state: 当前状态

    Returns:
        Dict[str, Any]: 状态更新

    Examples:
        >>> state = AgentState.create_initial("user_123", "我喜欢Python")
        >>> update = await memory_retrieval_node(state)
        >>> assert "memory_context" in update
    """
    try:
        user_id = state["user_id"]
        latest_message = state["messages"][-1]
        query = latest_message.content

        logger.info(f"Retrieving memories for {user_id[:4]}***")

        # 获取记忆客户端
        memory_client: MemoryClient = get_memory_client()

        if not memory_client.is_enabled:
            logger.warning("Memory system is disabled")
            return create_state_update(
                state,
                memory_context=None,
            )

        # 检索相关记忆
        memories = await memory_client.search_memory(
            user_id=user_id,
            query=query,
            limit=5,
        )

        # 构建记忆上下文
        memory_context = _format_memory_context(memories)

        logger.info(f"Retrieved {len(memories)} memories")

        return create_state_update(
            state,
            memory_context=memory_context,
        )

    except Exception as e:
        logger.error(f"Memory retrieval failed: {e}")
        # 记忆检索失败不是致命错误，继续处理
        return create_state_update(
            state,
            memory_context=None,
        )


def _format_memory_context(memories: List[Dict[str, Any]]) -> str:
    """格式化记忆上下文。

    Args:
        memories: 记忆列表

    Returns:
        str: 格式化的记忆上下文
    """
    if not memories:
        return "无相关记忆"

    context_parts = []
    for mem in memories[:3]:  # 只取前3条
        context_parts.append(f"- {mem['memory']} (相关度: {mem['score']:.2f})")

    return "相关记忆:\n" + "\n".join(context_parts)


# ==================== 工具选择节点 ====================

async def tool_selection_node(
    state: AgentState,
) -> Dict[str, Any]:
    """工具选择节点。

    根据意图选择合适的工具。

    Args:
        state: 当前状态

    Returns:
        Dict[str, Any]: 状态更新

    Examples:
        >>> state = AgentState.create_initial("user_123", "提醒我明天开会")
        >>> state["intent"] = AgentIntent.REMINDER
        >>> update = await tool_selection_node(state)
        >>> assert "tool_name" in update
    """
    try:
        intent = state["intent"]
        user_id = state["user_id"]

        logger.info(f"Selecting tool for intent: {intent.value}")

        # 意图到工具的映射
        intent_tool_map = {
            AgentIntent.REMINDER: "task_creation",
            AgentIntent.TASK_CREATE: "task_creation",
            AgentIntent.CALENDAR_QUERY: "calendar_query",
            AgentIntent.NOTIFICATION: "feishu_notification",
        }

        # 选择工具
        tool_name = intent_tool_map.get(intent)

        if not tool_name:
            # 不需要工具，直接生成响应
            logger.info("No tool needed, generating response")
            return create_state_update(
                state,
                next_action=AgentAction.GENERATE_RESPONSE,
                tool_name=None,
            )

        # 获取工具参数
        tool_args = _extract_tool_args(state, tool_name)

        logger.info(f"Tool selected: {tool_name}")

        return create_state_update(
            state,
            tool_name=tool_name,
            tool_args=tool_args,
            next_action=AgentAction.CALL_TOOL,
        )

    except Exception as e:
        logger.error(f"Tool selection failed: {e}")
        return create_state_update(
            state,
            next_action=AgentAction.GENERATE_RESPONSE,
            error=str(e),
        )


def _extract_tool_args(state: AgentState, tool_name: str) -> Dict[str, Any]:
    """提取工具参数。

    Args:
        state: 当前状态
        tool_name: 工具名称

    Returns:
        Dict[str, Any]: 工具参数
    """
    # 获取最新消息
    latest_message = state["messages"][-1]
    user_input = latest_message.content

    # 基础参数
    args = {
        "user_id": state["user_id"],
    }

    # TODO: 使用 LLM 提取结构化参数
    # 当前使用简单的规则提取

    if tool_name == "task_creation":
        # 提取任务标题（取前50个字符）
        args["title"] = user_input[:50]
        args["priority"] = "medium"

    elif tool_name == "calendar_query":
        args["start_date"] = None  # 使用默认

    elif tool_name == "feishu_notification":
        args["message"] = user_input
        args["msg_type"] = "text"

    return args


# ==================== 工具执行节点 ====================

async def tool_execution_node(
    state: AgentState,
) -> Dict[str, Any]:
    """工具执行节点。

    执行选定的工具。

    Args:
        state: 当前状态

    Returns:
        Dict[str, Any]: 状态更新

    Examples:
        >>> state = AgentState.create_initial("user_123", "创建任务")
        >>> state["tool_name"] = "task_creation"
        >>> state["tool_args"] = {"user_id": "user_123", "title": "测试"}
        >>> update = await tool_execution_node(state)
        >>> assert "tool_result" in update
    """
    try:
        tool_name = state["tool_name"]
        tool_args = state["tool_args"]

        if not tool_name or not tool_args:
            raise ValueError("Tool name or args missing")

        logger.info(f"Executing tool: {tool_name}")

        # 获取工具注册表
        registry = get_tool_registry()
        tool: BaseTool = registry.get(tool_name)

        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        # 执行工具
        result = await tool.execute(**tool_args)

        logger.info(f"Tool execution result: {result.get('success')}")

        return create_state_update(
            state,
            tool_result=result,
            next_action=AgentAction.GENERATE_RESPONSE,
        )

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return create_state_update(
            state,
            tool_result={"success": False, "error": str(e)},
            next_action=AgentAction.GENERATE_RESPONSE,
            error=str(e),
        )


# ==================== 响应生成节点 ====================

async def response_generation_node(
    state: AgentState,
) -> Dict[str, Any]:
    """响应生成节点。

    生成对用户的响应消息。

    Args:
        state: 当前状态

    Returns:
        Dict[str, Any]: 状态更新

    Examples:
        >>> state = AgentState.create_initial("user_123", "你好")
        >>> update = await response_generation_node(state)
        >>> assert "response" in update
    """
    try:
        intent = state["intent"]
        tool_result = state.get("tool_result")
        memory_context = state.get("memory_context")
        latest_message = state["messages"][-1]
        user_input = latest_message.content

        logger.info(f"Generating response for intent: {intent.value}")

        # 生成响应
        response = _generate_response(
            intent=intent,
            user_input=user_input,
            tool_result=tool_result,
            memory_context=memory_context,
        )

        logger.info(f"Response generated: {response[:50]}...")

        return create_state_update(
            state,
            response=response,
            next_action=AgentAction.END,
        )

    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        return create_state_update(
            state,
            response="抱歉，我遇到了一些问题，请稍后再试。",
            next_action=AgentAction.END,
            error=str(e),
        )


def _generate_response(
    intent: AgentIntent,
    user_input: str,
    tool_result: Dict[str, Any],
    memory_context: str,
) -> str:
    """生成响应内容。

    Args:
        intent: 用户意图
        user_input: 用户输入
        tool_result: 工具执行结果
        memory_context: 记忆上下文

    Returns:
        str: 响应内容
    """
    # 对于非 CHAT 意图，使用模板响应
    if intent == AgentIntent.REMINDER:
        if tool_result and tool_result.get("success"):
            return f"✅ 已为你创建提醒：{tool_result.get('title', '')}"
        else:
            return "抱歉，创建提醒失败了。"

    elif intent == AgentIntent.TASK_CREATE:
        if tool_result and tool_result.get("success"):
            return f"✅ 任务已创建：{tool_result.get('title', '')}\n任务ID: {tool_result.get('task_id', '')}"
        else:
            return "抱歉，创建任务失败了。"

    elif intent == AgentIntent.CALENDAR_QUERY:
        if tool_result and tool_result.get("success"):
            events = tool_result.get("events", [])
            if events:
                return f"📅 你的日程安排：\n" + "\n".join(
                    f"- {e['title']}: {e['start']} - {e['end']}"
                    for e in events
                )
            else:
                return "📅 你近期的日程为空。"
        else:
            return "抱歉，查询日程失败了。"

    # 对于 CHAT 意图，使用 LLM 生成响应
    if intent == AgentIntent.CHAT:
        return _generate_llm_response(user_input, memory_context)

    return f"我收到了你的消息：{user_input}"


def _generate_llm_response(user_input: str, memory_context: str) -> str:
    """使用 LLM 生成响应。

    Args:
        user_input: 用户输入
        memory_context: 记忆上下文

    Returns:
        str: LLM 生成的响应
    """
    # 如果 LLM 客户端未初始化，使用模板响应
    if not llm_client:
        if memory_context and memory_context != "无相关记忆":
            return f"根据你的记忆：\n{memory_context}\n\n关于你的问题，{user_input}"
        return f"我理解你说的是：{user_input}"

    try:
        # 构建系统提示
        system_prompt = """你是 FeishuMind，一个有情商的职场参谋 AI 助手。

你的特点：
- 友好、专业、有同理心
- 能够理解上下文并进行多轮对话
- 会根据用户的记忆提供个性化建议
- 回答简洁、直接，避免冗余

回答风格：
- 使用中文
- 语气自然、口语化
- 适当使用 emoji 增加亲和力
- 避免过度使用专业术语"""

        # 构建用户消息
        if memory_context and memory_context != "无相关记忆":
            user_message = f"""用户的相关记忆：
{memory_context}

用户的问题：{user_input}

请根据用户的记忆和问题，给出友好、有帮助的回答。"""
        else:
            user_message = user_input

        # 调用 DeepSeek API
        logger.info(f"Calling DeepSeek API: {DEEPSEEK_MODEL}")
        response = llm_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        # 提取响应内容
        ai_response = response.choices[0].message.content
        logger.info(f"DeepSeek response generated: {ai_response[:100]}...")

        return ai_response

    except Exception as e:
        logger.error(f"LLM response generation failed: {e}")
        # 降级到模板响应
        if memory_context and memory_context != "无相关记忆":
            return f"根据你的记忆：\n{memory_context}\n\n关于你的问题，{user_input}"
        return f"我理解你说的是：{user_input}"


# ==================== 记忆保存节点 ====================

async def memory_storage_node(
    state: AgentState,
) -> Dict[str, Any]:
    """记忆保存节点。

    在对话结束后，将用户消息保存到记忆系统中。

    Args:
        state: 当前状态

    Returns:
        Dict[str, Any]: 状态更新

    Examples:
        >>> state = AgentState.create_initial("user_123", "我喜欢Python")
        >>> update = await memory_storage_node(state)
        >>> assert "memory_stored" in update
    """
    try:
        user_id = state["user_id"]
        latest_message = state["messages"][-1]
        user_input = latest_message.content
        intent = state.get("intent")

        # 只对 CHAT 意图保存记忆
        if intent != AgentIntent.CHAT:
            logger.info(f"Skipping memory storage for intent: {intent}")
            return create_state_update(state, next_action=AgentAction.END)

        logger.info(f"Storing memory for {user_id[:4]}***")

        # 获取记忆客户端
        memory_client: MemoryClient = get_memory_client()

        if not memory_client.is_enabled:
            logger.warning("Memory system is disabled, skipping storage")
            return create_state_update(state, next_action=AgentAction.END)

        # 检查是否应该保存记忆
        # 简单规则：如果包含个人相关信息，则保存
        should_store = _should_store_memory(user_input)

        if not should_store:
            logger.info("Message does not contain personal info, skipping storage")
            return create_state_update(state, next_action=AgentAction.END)

        # 保存记忆
        memory_id = await memory_client.add_memory(
            user_id=user_id,
            content=user_input,
            category="preference",
        )

        logger.info(f"Memory stored: {memory_id} for user {user_id[:4]}***")

        return create_state_update(
            state,
            next_action=AgentAction.END,
        )

    except Exception as e:
        logger.error(f"Memory storage failed: {e}")
        # 记忆保存失败不影响对话流程
        return create_state_update(state, next_action=AgentAction.END)


def _should_store_memory(text: str) -> bool:
    """判断文本是否应该被保存到记忆中。

    Args:
        text: 待判断的文本

    Returns:
        bool: 是否应该保存
    """
    # 简单的关键词匹配
    keywords = [
        "我叫", "我是", "我是来自",
        "住在", "居住在", "生活在",
        "职业", "工作", "职位",
        "喜欢", "爱", "爱好",
        "记得", "记住", "别忘",
    ]

    return any(keyword in text for keyword in keywords)


# ==================== 人类反馈节点 ====================

async def human_feedback_node(
    state: AgentState,
) -> Dict[str, Any]:
    """人类反馈节点。

    处理用户的反馈，决定是否需要重新执行工具。

    Args:
        state: 当前状态

    Returns:
        Dict[str, Any]: 状态更新

    Examples:
        >>> state = AgentState.create_initial("user_123", "重新执行")
        >>> update = await human_feedback_node(state)
        >>> assert "next_action" in update
    """
    try:
        # TODO: 实现人类反馈逻辑
        # 当前直接结束

        logger.info("Processing human feedback")

        return create_state_update(
            state,
            next_action=AgentAction.END,
        )

    except Exception as e:
        logger.error(f"Human feedback processing failed: {e}")
        return create_state_update(
            state,
            next_action=AgentAction.END,
            error=str(e),
        )
