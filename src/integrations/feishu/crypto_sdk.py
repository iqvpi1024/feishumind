"""飞书加密解密工具模块（使用飞书官方 SDK）。

本模块使用飞书官方 SDK 提供的加密解密功能。
"""

import logging
from typing import Optional, Dict, Any

try:
    from lark_oapi.api.auth.v3 import *
    from lark_oapi import JSON
except ImportError:
    # 如果 SDK 未安装，回退到手动实现
    JSON = dict

from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_feishu_crypto_sdk():
    """获取飞书加密工具（使用 SDK）。

    Returns:
        可用的加密工具实例，SDK 未安装时返回 None
    """
    import os
    from lark_oapi.api.auth.v3 import app_ticket_internal_app

    encrypt_key = os.getenv("FEISHU_ENCRYPT_KEY")
    verification_token = os.getenv("FEISHU_VERIFICATION_TOKEN")

    if not encrypt_key or not verification_token:
        logger.warning("Feishu encryption keys not configured")
        return None

    try:
        # 使用飞书 SDK 的加密解密功能
        from lark_oapi.event import EventDispatcher

        dispatcher = EventDispatcher(
            encrypt_key=encrypt_key,
            verification_token=verification_token,
        )

        logger.info("Feishu SDK crypto initialized")
        return dispatcher

    except ImportError:
        logger.error("lark-oapi SDK not installed, falling back to manual implementation")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Feishu SDK crypto: {e}")
        return None


class FeishuCryptoSDK:
    """使用飞书 SDK 的加密解密工具。

    如果 SDK 可用则使用 SDK，否则回退到手动实现。
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

        # 尝试使用飞书 SDK
        try:
            from lark_oapi.event import EventDispatcher

            self._dispatcher = EventDispatcher(
                encrypt_key=encrypt_key,
                verification_token=verification_token,
            )
            self._use_sdk = True
            logger.info("Feishu crypto initialized (using SDK)")

        except ImportError:
            # SDK 未安装，回退到手动实现
            from src.integrations.feishu.crypto import FeishuCrypto
            self._crypto = FeishuCrypto(encrypt_key, verification_token)
            self._use_sdk = False
            logger.info("Feishu crypto initialized (using fallback)")

    def verify_signature(
        self,
        timestamp: str,
        nonce: str,
        body: str,
        signature: str,
    ) -> bool:
        """验证飞书 Webhook 签名。"""
        if self._use_sdk and hasattr(self._dispatcher, 'verify_signature'):
            # 使用 SDK 的签名验证
            return self._dispatcher.verify_signature(
                timestamp=timestamp,
                nonce=nonce,
                body=body,
                signature=signature,
            )
        else:
            # 使用手动实现
            return self._crypto.verify_signature(timestamp, nonce, body, signature)

    def decrypt(self, encrypted_data: str) -> Optional[Dict[str, Any]]:
        """解密飞书事件数据。"""
        if self._use_sdk:
            # 使用 SDK 解密
            try:
                # 飞书 SDK 的解密接口
                result = self._dispatcher.decrypt(encrypted_data)
                if result:
                    import json
                    return json.loads(result)
                return None
            except Exception as e:
                logger.error(f"SDK decryption error: {e}")
                # 回退到手动实现
                return self._crypto.decrypt(encrypted_data)
        else:
            # 使用手动实现
            return self._crypto.decrypt(encrypted_data)

    def encrypt(self, plain_data: Dict[str, Any]) -> Optional[str]:
        """加密数据（用于响应）。"""
        if self._use_sdk and hasattr(self._dispatcher, 'encrypt'):
            # 使用 SDK 加密
            try:
                import json
                plain_str = json.dumps(plain_data)
                return self._dispatcher.encrypt(plain_str)
            except Exception as e:
                logger.error(f"SDK encryption error: {e}")
                # 回退到手动实现
                return self._crypto.encrypt(plain_data)
        else:
            # 使用手动实现
            return self._crypto.encrypt(plain_data)


def get_feishu_crypto() -> Optional[FeishuCryptoSDK]:
    """获取飞书加密工具实例（从环境变量）。

    Returns:
        Optional[FeishuCryptoSDK]: 加密工具实例，配置缺失时返回 None
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

    return FeishuCryptoSDK(
        encrypt_key=encrypt_key,
        verification_token=verification_token,
    )
