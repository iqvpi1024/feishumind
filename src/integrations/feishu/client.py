"""飞书 API 客户端封装模块。

本模块封装飞书开放平台的 API 调用，包括消息发送、用户信息获取等。
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FeishuAPIError(Exception):
    """飞书 API 错误。

    Attributes:
        message: 错误消息
        code: 错误码
    """

    def __init__(self, message: str, code: int = 0):
        """初始化错误。

        Args:
            message: 错误消息
            code: 错误码
        """
        self.message = message
        self.code = code
        super().__init__(f"[{code}] {message}")


class FeishuClient:
    """飞书 API 客户端。

    封装飞书开放平台的 API 调用，支持自动重试和错误处理。

    Attributes:
        app_id: 飞书应用 ID
        app_secret: 飞书应用密钥
        access_token: 访问令牌
        base_url: API 基础 URL

    Examples:
        >>> client = FeishuClient(
        ...     app_id="cli_xxx",
        ...     app_secret="xxx"
        ... )
        >>> await client.send_message(
        ...     receive_id="ou_xxx",
        ...     content="Hello"
        ... )
    """

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        base_url: str = "https://open.feishu.cn/open-apis",
    ):
        """初始化飞书客户端。

        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            base_url: API 基础 URL
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        # 创建 HTTP 客户端
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_keepalive_connections=5),
        )

        logger.info("Feishu client initialized")

    async def __aenter__(self):
        """异步上下文管理器入口。"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出。"""
        await self.close()

    async def close(self):
        """关闭 HTTP 客户端。"""
        await self._http_client.aclose()
        logger.debug("Feishu client closed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_access_token(self) -> str:
        """获取访问令牌。

        Returns:
            str: 访问令牌

        Raises:
            FeishuAPIError: 获取令牌失败

        Examples:
            >>> token = await client.get_access_token()
            >>> print(token)
        """
        # 检查令牌是否有效
        if self.access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self.access_token

        # 获取新令牌
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"

        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }

        try:
            response = await self._http_client.post(
                url,
                json=payload,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("code") != 0:
                raise FeishuAPIError(
                    data.get("msg", "Failed to get access token"),
                    data.get("code", -1),
                )

            self.access_token = data.get("tenant_access_token")
            expires_in = data.get("expire", 7200)

            # 提前 5 分钟过期
            self._token_expires_at = datetime.fromtimestamp(
                datetime.now().timestamp() + expires_in - 300
            )

            logger.info("Access token refreshed")

            return self.access_token

        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting access token: {e}")
            raise FeishuAPIError(f"HTTP error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def send_message(
        self,
        receive_id: str,
        content: str,
        msg_type: str = "text",
        receive_id_type: str = "open_id",
    ) -> Dict[str, Any]:
        """发送消息。

        Args:
            receive_id: 接收者 ID
            content: 消息内容
            msg_type: 消息类型 (text|post|interactive)
            receive_id_type: 接收者 ID 类型 (open_id|user_id|union_id|chat_id)

        Returns:
            Dict[str, Any]: 发送结果

        Raises:
            FeishuAPIError: 发送失败

        Examples:
            >>> result = await client.send_message(
            ...     receive_id="ou_xxx",
            ...     content="Hello, world!"
            ... )
            >>> print(result["msg_id"])
        """
        token = await self.get_access_token()

        url = f"{self.base_url}/message/v4/send"

        # 构建消息体
        # 飞书 API 要求 content 字段是 JSON 字符串
        if msg_type == "text":
            message_content = {"text": content}
        elif msg_type == "post":
            message_content = {
                "post": {
                    "zh_cn": {
                        "title": "消息",
                        "content": [
                            [{"tag": "text", "text": content}],
                        ]
                    }
                }
            }
        else:
            message_content = {"text": content}

        # 将 content 转换为 JSON 字符串（飞书 API 要求）
        import json
        content_json = json.dumps(message_content, ensure_ascii=False)

        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "receive_id_type": receive_id_type,
            "content": content_json,
        }

        headers = {
            "Authorization": f"Bearer {token}",
        }

        logger.info(f"Send message payload: {payload}")

        try:
            response = await self._http_client.post(
                url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Send message API response: {data}")

            if data.get("code") != 0:
                logger.error(f"Send message failed: code={data.get('code')}, msg={data.get('msg')}")
                raise FeishuAPIError(
                    data.get("msg", "Failed to send message"),
                    data.get("code", -1),
                )

            logger.info(
                f"Message sent successfully to {receive_id[:4]}***: "
                f"{content[:30]}..."
            )

            return {
                "success": True,
                "msg_id": data.get("data", {}).get("msg_id"),
                "code": data.get("code"),
            }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending message: {e}")
            raise FeishuAPIError(f"HTTP error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_user_info(
        self,
        user_id: str,
        user_id_type: str = "open_id",
    ) -> Optional[Dict[str, Any]]:
        """获取用户信息。

        Args:
            user_id: 用户 ID
            user_id_type: 用户 ID 类型

        Returns:
            Optional[Dict[str, Any]]: 用户信息，失败返回 None

        Examples:
            >>> info = await client.get_user_info("ou_xxx")
            >>> if info:
            ...     print(info["name"])
        """
        token = await self.get_access_token()

        url = f"{self.base_url}/contact/v3/users/{user_id}"

        headers = {
            "Authorization": f"Bearer {token}",
        }

        params = {
            "user_id_type": user_id_type,
        }

        try:
            response = await self._http_client.get(
                url,
                headers=headers,
                params=params,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("code") != 0:
                logger.warning(f"Failed to get user info: {data.get('msg')}")
                return None

            user_data = data.get("data", {}).get("user", {})
            logger.info(f"User info retrieved: {user_data.get('name', 'Unknown')}")

            return user_data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting user info: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_tenant_info(self) -> Optional[Dict[str, Any]]:
        """获取租户信息。

        Returns:
            Optional[Dict[str, Any]]: 租户信息，失败返回 None

        Examples:
            >>> info = await client.get_tenant_info()
            >>> if info:
            ...     print(info["name"])
        """
        token = await self.get_access_token()

        url = f"{self.base_url}/tenant/v2/tenant/query"

        headers = {
            "Authorization": f"Bearer {token}",
        }

        try:
            response = await self._http_client.get(
                url,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("code") != 0:
                logger.warning(f"Failed to get tenant info: {data.get('msg')}")
                return None

            tenant_data = data.get("data", {}).get("tenant", {})
            logger.info(f"Tenant info retrieved: {tenant_data.get('name', 'Unknown')}")

            return tenant_data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting tenant info: {e}")
            return None


def get_feishu_client() -> Optional[FeishuClient]:
    """获取飞书客户端实例（从环境变量）。

    Returns:
        Optional[FeishuClient]: 飞书客户端实例，配置缺失时返回 None

    Examples:
        >>> client = get_feishu_client()
        >>> if client:
        ...     await client.send_message(...)
    """
    import os

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if not app_id or not app_secret:
        logger.warning(
            "Feishu API credentials not configured. "
            "Set FEISHU_APP_ID and FEISHU_APP_SECRET"
        )
        return None

    return FeishuClient(
        app_id=app_id,
        app_secret=app_secret,
    )
