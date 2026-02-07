"""
飞书卡片消息生成器

生成各种飞书卡片消息格式。

Author: FeishuMind Team
Created: 2026-02-06
"""

from typing import List

from src.integrations.github.models import GitHubRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FeishuCardBuilder:
    """飞书卡片构建器"""

    @staticmethod
    def create_github_trending_card(repos: List[GitHubRepo], period: str = "daily") -> dict:
        """创建 GitHub Trending 卡片

        生成符合飞书卡片格式的 GitHub Trending 推送消息。

        Args:
            repos: 仓库列表
            period: 时间周期 (daily, weekly, monthly)

        Returns:
            飞书卡片消息字典
        """
        # 中文周期映射
        period_map = {
            "daily": "今日",
            "weekly": "本周",
            "monthly": "本月",
        }
        period_text = period_map.get(period, "今日")

        # 构建卡片元素
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**📅 {period_text}热门仓库推荐**\n\n为您精选以下热门项目",
                },
            },
            {"tag": "hr"},
        ]

        # 添加每个仓库的信息
        for idx, repo in enumerate(repos, 1):
            repo_element = {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**{idx}. {repo.full_name}**\n"
                            f"⭐ {repo.stars} stars | 🍴 {repo.forks} forks\n"
                            f"💻 {repo.language or 'Unknown'}\n\n"
                            f"{repo.description or '暂无描述'}",
                        },
                    }
                ],
            }
            elements.append(repo_element)

            # 添加查看按钮
            if idx < len(repos):  # 最后一个不加分隔线
                elements.append({"tag": "hr"})

        # 添加底部按钮
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "查看 GitHub Trending"},
                        "type": "default",
                        "url": "https://github.com/trending",
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "修改偏好设置"},
                        "type": "primary",
                        "value": {"action": "edit_github_prefs"},
                    },
                ],
            }
        )

        # 构建完整卡片
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🔥 GitHub {period_text}热门推荐",
                    },
                    "template": "orange",
                },
                "elements": elements,
            },
        }

        return card

    @staticmethod
    def create_simple_text_card(title: str, content: str) -> dict:
        """创建简单文本卡片

        Args:
            title: 卡片标题
            content: 文本内容

        Returns:
            飞书卡片消息字典
        """
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "blue",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": content},
                    }
                ],
            },
        }

        return card

    @staticmethod
    def create_error_card(error_message: str) -> dict:
        """创建错误提示卡片

        Args:
            error_message: 错误信息

        Returns:
            飞书卡片消息字典
        """
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": "❌ 操作失败"},
                    "template": "red",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": f"**错误信息:** {error_message}"},
                    }
                ],
            },
        }

        return card

    @staticmethod
    def create_success_card(message: str) -> dict:
        """创建成功提示卡片

        Args:
            message: 成功信息

        Returns:
            飞书卡片消息字典
        """
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": "✅ 操作成功"},
                    "template": "green",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": message},
                    }
                ],
            },
        }

        return card

    @staticmethod
    def format_repo_summary(repo: GitHubRepo) -> str:
        """格式化单个仓库摘要

        Args:
            repo: 仓库对象

        Returns:
            Markdown 格式的摘要文本
        """
        lines = [
            f"**{repo.full_name}**",
            f"⭐ {repo.stars} | 🍴 {repo.forks} | 💻 {repo.language or 'N/A'}",
            "",
            repo.description or "暂无描述",
            "",
            f"🔗 [查看仓库]({repo.url})",
        ]

        return "\n".join(lines)
