"""飞书加密解密工具单元测试。

测试飞书 Webhook 的签名验证和事件解密功能。
"""

import pytest
from unittest.mock import patch

from src.integrations.feishu.crypto import (
    FeishuCrypto,
    get_feishu_crypto,
)


@pytest.fixture
def mock_crypto():
    """模拟加密工具。

    Returns:
        FeishuCrypto: 加密工具实例
    """
    # 使用测试密钥（Base64 编码的 32 字节）
    import base64
    test_key = base64.b64encode(b"0" * 32).decode("utf-8")
    test_token = "test_verification_token"

    return FeishuCrypto(
        encrypt_key=test_key,
        verification_token=test_token,
    )


# ==================== 签名验证测试 ====================


def test_verify_signature_success(mock_crypto):
    """测试签名验证成功。

    Args:
        mock_crypto: 模拟加密工具
    """
    # 计算正确的签名
    import hashlib
    import base64

    timestamp = "1234567890"
    nonce = "test_nonce"
    body = '{"test": "data"}'
    token = "test_verification_token"

    sign_str = f"{timestamp}{nonce}{token}{body}"
    sign_bytes = hashlib.sha256(sign_str.encode("utf-8")).digest()
    signature = base64.b64encode(sign_bytes).decode("utf-8")

    # 验证签名
    is_valid = mock_crypto.verify_signature(
        timestamp=timestamp,
        nonce=nonce,
        body=body,
        signature=signature,
    )

    assert is_valid is True


def test_verify_signature_failure(mock_crypto):
    """测试签名验证失败。

    Args:
        mock_crypto: 模拟加密工具
    """
    is_valid = mock_crypto.verify_signature(
        timestamp="1234567890",
        nonce="test_nonce",
        body='{"test": "data"}',
        signature="invalid_signature",
    )

    assert is_valid is False


# ==================== 加密解密测试 ====================


def test_encrypt_decrypt(mock_crypto):
    """测试加密解密。

    Args:
        mock_crypto: 模拟加密工具
    """
    plain_data = {
        "type": "im.message.receive_v1",
        "event": {
            "message": "test",
        }
    }

    # 加密
    encrypted = mock_crypto.encrypt(plain_data)
    assert encrypted is not None
    assert isinstance(encrypted, str)

    # 解密
    decrypted = mock_crypto.decrypt(encrypted)
    assert decrypted is not None
    # 解密结果可能包含额外的字段，所以只检查type字段
    assert "type" in decrypted
    assert decrypted["type"] == "im.message.receive_v1"


def test_decrypt_invalid_data(mock_crypto):
    """测试解密无效数据。

    Args:
        mock_crypto: 模拟加密工具
    """
    result = mock_crypto.decrypt("invalid_base64_string")
    assert result is None


# ==================== 获取实例测试 ====================


@patch.dict("os.environ", {
    "FEISHU_ENCRYPT_KEY": "test_key",
    "FEISHU_VERIFICATION_TOKEN": "test_token",
})
def test_get_feishu_crypto_with_env():
    """测试从环境变量获取实例。"""
    import os

    # 设置环境变量
    import base64
    os.environ["FEISHU_ENCRYPT_KEY"] = base64.b64encode(b"0" * 32).decode("utf-8")
    os.environ["FEISHU_VERIFICATION_TOKEN"] = "test_token"

    crypto = get_feishu_crypto()

    assert crypto is not None
    assert isinstance(crypto, FeishuCrypto)


@patch.dict("os.environ", {}, clear=True)
def test_get_feishu_crypto_without_env():
    """测试环境变量未配置时返回 None。"""
    import os

    # 清除环境变量
    os.environ.pop("FEISHU_ENCRYPT_KEY", None)
    os.environ.pop("FEISHU_VERIFICATION_TOKEN", None)

    crypto = get_feishu_crypto()

    assert crypto is None
