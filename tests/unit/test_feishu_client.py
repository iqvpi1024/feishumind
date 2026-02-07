"""飞书客户端单元测试。

测试飞书 API 客户端的功能。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.integrations.feishu.client import (
    FeishuClient,
    FeishuAPIError,
    get_feishu_client,
)


@pytest.fixture
def mock_http_client():
    """模拟 HTTP 客户端。

    Returns:
        Mock: HTTP 客户端 mock
    """
    mock = Mock()
    mock.post = AsyncMock()
    mock.get = AsyncMock()
    mock.aclose = AsyncMock()
    return mock


@pytest.fixture
def feishu_client(mock_http_client):
    """飞书客户端测试夹具。

    Args:
        mock_http_client: 模拟 HTTP 客户端

    Returns:
        FeishuClient: 飞书客户端实例
    """
    client = FeishuClient(
        app_id="cli_test",
        app_secret="test_secret",
    )
    client._http_client = mock_http_client
    return client


# ==================== 访问令牌测试 ====================


@pytest.mark.asyncio
async def test_get_access_token_success(feishu_client, mock_http_client):
    """测试成功获取访问令牌。

    Args:
        feishu_client: 飞书客户端
        mock_http_client: 模拟 HTTP 客户端
    """
    # 模拟响应
    mock_response = Mock()
    mock_response.json.return_value = {
        "code": 0,
        "tenant_access_token": "test_token",
        "expire": 7200,
    }
    mock_http_client.post.return_value = mock_response

    token = await feishu_client.get_access_token()

    assert token == "test_token"
    assert feishu_client.access_token == "test_token"


@pytest.mark.asyncio
async def test_get_access_token_error(feishu_client, mock_http_client):
    """测试获取令牌失败。

    Args:
        feishu_client: 飞书客户端
        mock_http_client: 模拟 HTTP 客户端
    """
    mock_response = Mock()
    mock_response.json.return_value = {
        "code": -1,
        "msg": "Invalid credentials",
    }
    mock_http_client.post.return_value = mock_response

    with pytest.raises(FeishuAPIError):
        await feishu_client.get_access_token()


# ==================== 发送消息测试 ====================


@pytest.mark.asyncio
async def test_send_message_success(feishu_client, mock_http_client):
    """测试成功发送消息。

    Args:
        feishu_client: 飞书客户端
        mock_http_client: 模拟 HTTP 客户端
    """
    # 模拟令牌响应
    feishu_client.access_token = "test_token"

    # 模拟发送响应
    mock_response = Mock()
    mock_response.json.return_value = {
        "code": 0,
        "data": {
            "msg_id": "msg_test",
        }
    }
    mock_http_client.post.return_value = mock_response

    result = await feishu_client.send_message(
        receive_id="ou_test",
        content="Hello, world!",
    )

    assert result["success"] is True
    assert result["msg_id"] == "msg_test"


@pytest.mark.asyncio
async def test_send_message_with_token_refresh(feishu_client, mock_http_client):
    """测试发送消息时自动刷新令牌。

    Args:
        feishu_client: 飞书客户端
        mock_http_client: 模拟 HTTP 客户端
    """
    # 第一次调用：获取令牌
    token_response = Mock()
    token_response.json.return_value = {
        "code": 0,
        "tenant_access_token": "new_token",
        "expire": 7200,
    }

    # 第二次调用：发送消息
    send_response = Mock()
    send_response.json.return_value = {
        "code": 0,
        "data": {"msg_id": "msg_test"},
    }

    mock_http_client.post.side_effect = [token_response, send_response]

    result = await feishu_client.send_message(
        receive_id="ou_test",
        content="Test",
    )

    assert result["success"] is True
    assert feishu_client.access_token == "new_token"


# ==================== 获取用户信息测试 ====================


@pytest.mark.asyncio
async def test_get_user_info_success(feishu_client, mock_http_client):
    """测试成功获取用户信息。

    Args:
        feishu_client: 飞书客户端
        mock_http_client: 模拟 HTTP 客户端
    """
    feishu_client.access_token = "test_token"

    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "code": 0,
        "data": {
            "user": {
                "name": "Test User",
                "open_id": "ou_test",
            }
        }
    }
    mock_response.raise_for_status = Mock()
    mock_http_client.get.return_value = mock_response

    user_info = await feishu_client.get_user_info("ou_test")

    assert user_info is not None
    assert user_info["name"] == "Test User"
    assert user_info["open_id"] == "ou_test"


@pytest.mark.asyncio
async def test_get_user_info_not_found(feishu_client, mock_http_client):
    """测试用户不存在。

    Args:
        feishu_client: 飞书客户端
        mock_http_client: 模拟 HTTP 客户端
    """
    feishu_client.access_token = "test_token"

    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "code": -1,
        "msg": "User not found",
    }
    mock_response.raise_for_status = Mock()
    mock_http_client.get.return_value = mock_response

    user_info = await feishu_client.get_user_info("ou_invalid")

    assert user_info is None


# ==================== 获取租户信息测试 ====================


@pytest.mark.asyncio
async def test_get_tenant_info_success(feishu_client, mock_http_client):
    """测试成功获取租户信息。

    Args:
        feishu_client: 飞书客户端
        mock_http_client: 模拟 HTTP 客户端
    """
    feishu_client.access_token = "test_token"

    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "code": 0,
        "data": {
            "tenant": {
                "name": "Test Tenant",
                "tenant_id": "12345",
            }
        }
    }
    mock_response.raise_for_status = Mock()
    mock_http_client.get.return_value = mock_response

    tenant_info = await feishu_client.get_tenant_info()

    assert tenant_info is not None
    assert tenant_info["name"] == "Test Tenant"


# ==================== 获取实例测试 ====================


@patch.dict("os.environ", {
    "FEISHU_APP_ID": "cli_test",
    "FEISHU_APP_SECRET": "test_secret",
})
def test_get_feishu_client_with_env():
    """测试从环境变量获取客户端。"""
    import os

    os.environ["FEISHU_APP_ID"] = "cli_test"
    os.environ["FEISHU_APP_SECRET"] = "test_secret"

    client = get_feishu_client()

    assert client is not None
    assert isinstance(client, FeishuClient)


@patch.dict("os.environ", {}, clear=True)
def test_get_feishu_client_without_env():
    """测试环境变量未配置时返回 None。"""
    import os

    os.environ.pop("FEISHU_APP_ID", None)
    os.environ.pop("FEISHU_APP_SECRET", None)

    client = get_feishu_client()

    assert client is None
