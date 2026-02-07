"""日志工具模块。

提供统一的日志记录接口，基于 loguru 实现。
"""

import sys
from pathlib import Path
from loguru import logger as _logger
from typing import Optional

# 移除默认的 handler
_logger.remove()

# 添加控制台输出
_logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# 添加文件输出 (可选，仅在非Docker环境或有权限时启用)
import os
log_path = Path("logs")

# 检查是否应该启用文件日志（不在Docker中或明确启用）
if os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true":
    try:
        log_path.mkdir(exist_ok=True)
        _logger.add(
            log_path / "feishumind_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="00:00",  # 每天午夜轮换
            retention="7 days",  # 保留7天
            compression="zip",  # 压缩旧日志
        )
    except (PermissionError, OSError) as e:
        # 如果无法创建文件日志，忽略错误
        pass


def get_logger(name: Optional[str] = None) -> "logger":
    """获取 logger 实例。

    Args:
        name: Logger 名称，通常使用 __name__

    Returns:
        Logger 实例

    Examples:
        >>> from src.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello, FeishuMind!")
    """
    if name:
        return _logger.bind(name=name)
    return _logger


# 导出 logger
__all__ = ["get_logger", "logger"]

logger = get_logger(__name__)
