"""
GitHub 集成模块

本模块提供 GitHub Trending 数据获取和用户偏好管理功能。

主要功能:
- 获取 GitHub Trending 仓库
- 支持语言和时间段过滤
- 用户偏好管理
- 定时推送

Author: FeishuMind Team
Created: 2026-02-06
"""

from src.integrations.github.client import GitHubClient
from src.integrations.github.models import GitHubRepo, GitHubTrendingRequest

__all__ = ["GitHubClient", "GitHubRepo", "GitHubTrendingRequest"]
