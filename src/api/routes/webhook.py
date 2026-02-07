"""飞书 Webhook API 路由模块。

提供飞书事件接收的 Webhook 端点。
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, status, Header
from pydantic import BaseModel, Field

from src.integrations.feishu.crypto import get_feishu_crypto
from src.integrations.feishu.client import get_feishu_client
from src.agent.graph import run_agent
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/webhook",
    tags=["webhook"],
    responses={404: {"description": "Not found"}},
)


# ==================== Request Models ====================


class FeishuEvent(BaseModel):
    """飞书事件模型。

    Attributes:
        event_schema: 事件版本
        header: 事件头信息
        event: 事件数据
    """

    event_schema: str = Field(default="2.0", description="事件版本", alias="schema")
    header: Dict[str, Any] = Field(default={}, description="事件头")
    event: Dict[str, Any] = Field(default={}, description="事件内容")


# ==================== Webhook Endpoints ====================


@router.post(
    "/feishu",
    summary="飞书 Webhook",
    description="接收飞书开放平台的事件推送",
)
async def feishu_webhook(
    request: Request,
    x_feishu_timestamp: Optional[str] = Header(None, alias="X-Feishu-Timestamp"),
    x_feishu_nonce: Optional[str] = Header(None, alias="X-Feishu-Nonce"),
    x_feishu_signature: Optional[str] = Header(None, alias="X-Feishu-Signature"),
):
    """飞书 Webhook 端点。

    处理飞书开放平台的事件推送，包括消息接收、成员加入等。

    Args:
        request: FastAPI 请求对象
        x_feishu_timestamp: 飞书时间戳
        x_feishu_nonce: 飞书随机字符串
        x_feishu_signature: 飞书签名

    Returns:
        dict: 响应数据

    Raises:
        HTTPException: 处理失败时
    """
    try:
        # 读取请求体
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8")

        logger.info(
            f"Received Feishu webhook: "
            f"timestamp={x_feishu_timestamp}, "
            f"nonce={x_feishu_nonce}, "
            f"body_length={len(body_str)}"
        )

        # 先解析 JSON 检查是否是 URL 验证
        import json
        try:
            request_data = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON body: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON body",
            )

        # 处理 URL 验证挑战（在签名验证之前）
        # 飞书的 URL 验证请求是明文的，不加密，也不需要签名验证
        if request_data.get("type") == "url_verification":
            challenge = request_data.get("challenge")
            logger.info(f"URL verification request received, challenge: {challenge}")
            # URL 验证直接返回 challenge，不需要任何验证
            return {"challenge": challenge}

        # 对于非 URL 验证请求，必须有加密配置
        crypto = get_feishu_crypto()
        if not crypto:
            logger.error("Feishu crypto not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Feishu crypto not configured. Please set FEISHU_ENCRYPT_KEY and FEISHU_VERIFICATION_TOKEN",
            )

        # 记录原始请求体用于调试
        logger.info(f"Raw request body (first 200 chars): {body_str[:200]}")
        logger.info(f"Request headers - timestamp: {x_feishu_timestamp}, nonce: {x_feishu_nonce}, signature: {x_feishu_signature[:20] if x_feishu_signature else None}...")

        # 验证签名（如果存在）
        if all([x_feishu_timestamp, x_feishu_nonce, x_feishu_signature]):
            is_valid = crypto.verify_signature(
                timestamp=x_feishu_timestamp,
                nonce=x_feishu_nonce,
                body=body_str,
                signature=x_feishu_signature,
            )

            if not is_valid:
                logger.error("Feishu signature verification failed")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid signature",
                )
            logger.info("Signature verification passed")
        else:
            # 开发环境：如果没有签名头，记录警告但继续处理
            logger.warning(
                "Missing Feishu signature headers. "
                "This is unexpected in production. Continuing for debugging..."
            )
            # 注意：在生产环境中，应该在这里返回 401 错误

        # 解密事件数据
        encrypt_key = request_data.get("encrypt")
        if not encrypt_key:
            logger.error("Missing encrypt key in request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing encrypt key",
            )

        # 解密事件
        event_data = crypto.decrypt(encrypt_key)

        if not event_data:
            logger.error("Failed to decrypt event data")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to decrypt event",
            )

        # 提取事件类型（飞书事件结构：header.event_type）
        header = event_data.get("header", {})
        event_type = header.get("event_type", "unknown")

        logger.info(f"Event decrypted: {event_type}")

        # 处理加密后的 URL 验证挑战
        if event_type == "url_verification":
            challenge = event_data.get("challenge")
            logger.info(f"URL verification challenge extracted from decrypted event: {challenge}")
            return {"challenge": challenge}

        # 处理其他类型的事件
        await _handle_feishu_event(event_data)

        # 返回成功响应
        return {
            "code": 0,
            "msg": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


async def _handle_feishu_event(event_data: Dict[str, Any]) -> None:
    """处理飞书事件。

    Args:
        event_data: 事件数据

    Raises:
        Exception: 处理失败时
    """
    # 飞书事件结构：header.event_type
    header = event_data.get("header", {})
    event_type = header.get("event_type")

    if event_type == "im.message.receive_v1":
        # 接收消息事件
        await _handle_message_event(event_data)
    elif event_type == "im.chat.member_user.add_v1":
        # 成员加入事件
        await _handle_member_add_event(event_data)
    else:
        logger.warning(f"Unhandled event type: {event_type}")


async def _handle_message_event(event_data: Dict[str, Any]) -> None:
    """处理消息事件。

    Args:
        event_data: 事件数据

    Raises:
        Exception: 处理失败时
    """
    try:
        # 提取消息信息
        event = event_data.get("event", {})
        message = event.get("message", {})
        sender = event.get("sender", {})

        sender_id = sender.get("sender_id", {}).get("open_id", "")
        message_id = message.get("message_id", "")
        chat_id = message.get("chat_id", "")
        message_type = message.get("message_type", "")

        # 提取消息内容
        content = message.get("content", "")

        # 解析内容（JSON 字符串）
        import json
        try:
            content_data = json.loads(content)
            text_content = content_data.get("text", "")
        except json.JSONDecodeError:
            text_content = content

        logger.info(
            f"Received message from {sender_id[:4]}***: "
            f"{text_content[:50]}..."
        )

        # TODO: 调用 Agent 处理消息
        # 当前为简单回复
        await _send_agent_response(
            sender_id=sender_id,
            chat_id=chat_id,
            user_message=text_content,
        )

    except Exception as e:
        logger.error(f"Error handling message event: {e}")
        raise


async def _handle_member_add_event(event_data: Dict[str, Any]) -> None:
    """处理成员加入事件。

    Args:
        event_data: 事件数据
    """
    try:
        event = event_data.get("event", {})
        user_list = event.get("user_list", [])

        logger.info(f"New members added: {len(user_list)} users")

        # 发送欢迎消息
        for user_info in user_list:
            user_id = user_info.get("open_id", "")
            await _send_welcome_message(user_id)

    except Exception as e:
        logger.error(f"Error handling member add event: {e}")


async def _send_agent_response(
    sender_id: str,
    chat_id: str,
    user_message: str,
) -> None:
    """发送 Agent 响应。

    Args:
        sender_id: 发送者 ID
        chat_id: 聊天 ID
        user_message: 用户消息

    Raises:
        Exception: 发送失败时
    """
    try:
        # 获取飞书客户端
        client = get_feishu_client()

        if not client:
            logger.error("Feishu client not configured")
            return

        # 调用 Agent 获取响应
        logger.info(f"Calling agent for user {sender_id[:4]}***")
        agent_result = await run_agent(
            user_id=sender_id,
            message=user_message,
        )

        # 提取响应内容
        if "error" in agent_result:
            response_text = f"抱歉，处理时遇到错误：{agent_result['error']}"
        else:
            response_text = agent_result.get("response", "我收到了你的消息")

        # 发送消息
        # 优先发送到私聊，如果没有则发送到群聊
        receive_id = sender_id if sender_id else chat_id
        receive_id_type = "open_id" if sender_id else "chat_id"

        logger.info(f"Sending message: receive_id={receive_id}, receive_id_type={receive_id_type}, sender_id={sender_id}, chat_id={chat_id}")

        await client.send_message(
            receive_id=receive_id,
            content=response_text,
            msg_type="text",
            receive_id_type=receive_id_type,
        )

        logger.info(f"Agent response sent to {receive_id[:4]}***")

    except Exception as e:
        logger.error(f"Error sending agent response: {e}")
        raise


async def _send_welcome_message(user_id: str) -> None:
    """发送欢迎消息。

    Args:
        user_id: 用户 ID

    Raises:
        Exception: 发送失败时
    """
    try:
        client = get_feishu_client()

        if not client:
            logger.error("Feishu client not configured")
            return

        welcome_text = (
            "👋 欢迎使用飞书灵犀！\n\n"
            "我是你的智能职场参谋，可以帮你：\n"
            "• 设置提醒\n"
            "• 管理任务\n"
            "• 查询日历\n"
            "• 发送通知\n\n"
            "直接发送消息试试吧！"
        )

        await client.send_message(
            receive_id=user_id,
            content=welcome_text,
            msg_type="text",
            receive_id_type="open_id",
        )

        logger.info(f"Welcome message sent to {user_id[:4]}***")

    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")


# ==================== Health Check ====================

@router.get(
    "/feishu/health",
    summary="Webhook 健康检查",
    description="检查 Webhook 服务状态",
)
async def webhook_health():
    """Webhook 健康检查端点。

    Returns:
        dict: 服务状态
    """
    crypto = get_feishu_crypto()
    client = get_feishu_client()

    return {
        "status": "healthy",
        "crypto_configured": crypto is not None,
        "client_configured": client is not None,
    }
