"""飞书加密解密工具模块。

本模块实现飞书 Webhook 的签名验证和事件解密功能。
遵循飞书开放平台的加密规范。
"""

import base64
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FeishuCrypto:
    """飞书加密解密工具类。

    负责验证 Webhook 签名和加解密事件数据。

    Attributes:
        encrypt_key: 飞书提供的加密 Key
        verification_token: 飞书提供的验证 Token

    Examples:
        >>> crypto = FeishuCrypto(
        ...     encrypt_key="your_encrypt_key",
        ...     verification_token="your_token"
        ... )
        >>> is_valid = crypto.verify_signature("timestamp", "nonce", "body", "signature")
        >>> event = crypto.decrypt("encrypted_data")
    """

    def __init__(
        self,
        encrypt_key: str,
        verification_token: str,
    ):
        """初始化加密工具。

        Args:
            encrypt_key: 飞书提供的加密 Key (Base64 编码)
            verification_token: 飞书提供的验证 Token
        """
        self.encrypt_key = encrypt_key
        self.verification_token = verification_token

        # 解码加密 Key
        self._key = base64.b64decode(encrypt_key)

        logger.info("Feishu crypto initialized")

    def verify_signature(
        self,
        timestamp: str,
        nonce: str,
        body: str,
        signature: str,
    ) -> bool:
        """验证飞书 Webhook 签名。

        Args:
            timestamp: 请求时间戳
            nonce: 随机字符串
            body: 请求体（原始字符串）
            signature: 飞书签名

        Returns:
            bool: 签名是否有效

        Examples:
            >>> is_valid = crypto.verify_signature(
            ...     timestamp="1234567890",
            ...     nonce="random_nonce",
            ...     body='{"challenge":"test"}',
            ...     signature="abc123..."
            ... )
        """
        try:
            # 拼接签名原文
            sign_str = f"{timestamp}{nonce}{self.verification_token}{body}"

            # 计算 SHA-256 签名
            sign_bytes = hashlib.sha256(sign_str.encode("utf-8")).digest()

            # Base64 编码
            computed_signature = base64.b64encode(sign_bytes).decode("utf-8")

            # 比对签名
            is_valid = computed_signature == signature

            if not is_valid:
                logger.warning("Feishu signature verification failed")

            return is_valid

        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

    def decrypt(self, encrypted_data: str) -> Optional[Dict[str, Any]]:
        """解密飞书事件数据。

        Args:
            encrypted_data: 加密的事件数据（Base64 编码）

        Returns:
            Optional[Dict[str, Any]]: 解密后的事件数据，失败返回 None

        Examples:
            >>> event = crypto.decrypt("encrypted_base64_string")
            >>> if event:
            ...     print(event["type"])
        """
        try:
            # Base64 解码
            encrypted_bytes = base64.b64decode(encrypted_data)

            # 提取 IV（前 16 字节）
            iv = encrypted_bytes[:16]

            # 提取密文（16 字节之后）
            ciphertext = encrypted_bytes[16:]

            # 创建解密器 (AES-256-CFB)
            cipher = Cipher(
                algorithms.AES(self._key),
                modes.CFB(iv),
                backend=default_backend(),
            )
            decryptor = cipher.decryptor()

            # 解密
            decrypted_bytes = decryptor.update(ciphertext) + decryptor.finalize()

            # 去除 PKCS7 填充
            padding_length = decrypted_bytes[-1]
            decrypted_bytes = decrypted_bytes[:-padding_length]

            # 解析 JSON
            decrypted_str = decrypted_bytes.decode("utf-8")
            event_data = json.loads(decrypted_str)

            logger.info(f"Event decrypted successfully: {event_data.get('type', 'unknown')}")

            return event_data

        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None

    def encrypt(self, plain_data: Dict[str, Any]) -> Optional[str]:
        """加密数据（用于响应）。

        Args:
            plain_data: 要加密的明文数据

        Returns:
            Optional[str]: 加密后的 Base64 字符串，失败返回 None

        Examples:
            >>> encrypted = crypto.encrypt({"msg": "hello"})
            >>> if encrypted:
            ...     print(encrypted)
        """
        try:
            # 序列化为 JSON
            plain_str = json.dumps(plain_data, separators=(",", ":"))
            plain_bytes = plain_str.encode("utf-8")

            # PKCS7 填充
            block_size = 32
            padding_length = block_size - (len(plain_bytes) % block_size)
            plain_bytes += bytes([padding_length]) * padding_length

            # 生成随机 IV (16 字节)
            import os
            iv = os.urandom(16)

            # 创建加密器 (AES-256-CFB)
            cipher = Cipher(
                algorithms.AES(self._key),
                modes.CFB(iv),
                backend=default_backend(),
            )
            encryptor = cipher.encryptor()

            # 加密
            encrypted_bytes = encryptor.update(plain_bytes) + encryptor.finalize()

            # 拼接 IV 和密文
            result_bytes = iv + encrypted_bytes

            # Base64 编码
            encrypted_str = base64.b64encode(result_bytes).decode("utf-8")

            logger.debug("Data encrypted successfully")

            return encrypted_str

        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return None


def get_feishu_crypto() -> Optional[FeishuCrypto]:
    """获取飞书加密工具实例（从环境变量）。

    Returns:
        Optional[FeishuCrypto]: 加密工具实例，配置缺失时返回 None

    Examples:
        >>> crypto = get_feishu_crypto()
        >>> if crypto:
        ...     # 使用加密工具
        ...     pass
    """
    import os

    encrypt_key = os.getenv("FEISHU_ENCRYPT_KEY")
    verification_token = os.getenv("FEISHU_VERIFICATION_TOKEN")

    if not encrypt_key or not verification_token:
        logger.warning(
            "Feishu encryption keys not configured. "
            "Set FEISHU_ENCRYPT_KEY and FEISHU_VERIFICATION_TOKEN"
        )
        return None

    return FeishuCrypto(
        encrypt_key=encrypt_key,
        verification_token=verification_token,
    )
