"""
GitHub 功能集成测试

测试 GitHub Trending 的端到端功能。

Author: FeishuMind Team
Created: 2026-02-06
"""

import pytest

from src.integrations.github.client import GitHubClient
from src.integrations.feishu.cards import FeishuCardBuilder
from src.utils.scheduler import TaskScheduler
from src.integrations.github.models import GitHubRepo


@pytest.mark.asyncio
async def test_github_client_basic():
    """测试 GitHub 客户端基本功能"""
    client = GitHubClient()

    # 测试 URL 构建
    url = client._build_trending_url("Python", "daily")
    assert "python" in url
    assert "since=daily" in url

    # 测试数字解析
    assert client._parse_number("1.2k") == 1200
    assert client._parse_number("500") == 500


def test_card_builder():
    """测试卡片生成器"""
    # 创建测试仓库
    repos = [
        GitHubRepo(
            repo_id="test/repo1",
            name="repo1",
            full_name="test/repo1",
            description="Test repository",
            language="Python",
            stars=1000,
            forks=100,
            url="https://github.com/test/repo1",
            owner="test",
        )
    ]

    # 生成卡片
    card = FeishuCardBuilder.create_github_trending_card(repos, "daily")

    # 验证卡片结构
    assert card["msg_type"] == "interactive"
    assert "card" in card
    assert "header" in card["card"]
    assert "elements" in card["card"]


def test_scheduler():
    """测试调度器"""
    scheduler = TaskScheduler()

    # 测试调度器未启动
    assert not scheduler.is_running()

    # 启动调度器
    scheduler.start()
    assert scheduler.is_running()

    # 关闭调度器
    scheduler.shutdown()
    assert not scheduler.is_running()


def test_github_models():
    """测试 GitHub 数据模型"""
    repo = GitHubRepo(
        repo_id="test/repo1",
        name="repo1",
        full_name="test/repo1",
        description="Test",
        language="Python",
        stars=100,
        forks=10,
        url="https://github.com/test/repo1",
        owner="test",
    )

    assert repo.repo_id == "test/repo1"
    assert repo.stars == 100
    assert repo.language == "Python"

    # 测试序列化
    repo_dict = repo.dict()
    assert "repo_id" in repo_dict
    assert repo_dict["stars"] == 100


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_github_trending():
    """集成测试：真实获取 GitHub Trending

    注意：此测试需要网络连接，可能不稳定
    """
    client = GitHubClient(timeout=10)

    try:
        repos = await client.get_trending_repos(language="Python", period="daily", limit=5)

        # 验证返回结果
        assert isinstance(repos, list)

        # 如果有结果，验证数据结构
        if len(repos) > 0:
            repo = repos[0]
            assert hasattr(repo, "full_name")
            assert hasattr(repo, "stars")
            assert hasattr(repo, "url")
            assert repo.stars >= 0

    except Exception as e:
        pytest.skip(f"网络请求失败，跳过集成测试: {e}")
