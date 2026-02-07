"""
GitHub API 路由单元测试

测试 GitHub 相关的 API 端点。

Author: FeishuMind Team
Created: 2026-02-06
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.api.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.mark.asyncio
async def test_get_trending_success(client):
    """测试成功获取 Trending"""
    with patch("src.integrations.github.client.GitHubClient.get_trending_repos") as mock_get:
        mock_get.return_value = []

        response = client.get("/api/v1/github/trending?language=Python&period=daily&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data


@pytest.mark.asyncio
async def test_get_trending_invalid_period(client):
    """测试无效的时间周期"""
    with patch("src.integrations.github.client.GitHubClient.get_trending_repos") as mock_get:
        mock_get.side_effect = ValueError("Invalid period")

        response = client.get("/api/v1/github/trending?period=invalid")

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_test_card_endpoint(client):
    """测试卡片生成端点"""
    response = client.post(
        "/api/v1/github/test-card",
        params={"language": "Python", "period": "daily"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "card" in data["data"]


@pytest.mark.asyncio
async def test_set_preferences(client):
    """测试设置偏好"""
    with patch("src.api.routes.github._save_user_preferences") as mock_save:
        mock_save.return_value = "mem_123"

        response = client.post(
            "/api/v1/github/preferences",
            json={
                "user_id": "test_user",
                "languages": ["Python", "JavaScript"],
                "push_time": "09:00",
                "push_enabled": True,
                "frequency": "daily",
                "min_stars": 100,
                "limit": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["memory_id"] == "mem_123"


@pytest.mark.asyncio
async def test_get_status(client):
    """测试获取状态"""
    with patch("src.api.routes.github._get_user_preferences") as mock_get:
        from src.integrations.github.models import GitHubPreferences

        mock_get.return_value = GitHubPreferences(
            user_id="test_user",
            languages=["Python"],
            push_time="09:00",
            push_enabled=True,
            frequency="daily",
            min_stars=100,
            limit=5,
        )

        response = client.get("/api/v1/github/status/test_user")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["user_id"] == "test_user"
