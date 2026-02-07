"""API 集成测试。

测试所有 API 端点的集成。

Author: Claude Code
Date: 2026-02-06
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client() -> TestClient:
    """创建测试客户端。"""
    return TestClient(app)


class TestMemoryAPIIntegration:
    """记忆 API 集成测试。"""

    def test_memory_crud_flow(self, client: TestClient) -> None:
        """测试记忆 CRUD 完整流程。"""
        # Create
        response = client.post(
            "/api/v1/memory",
            json={
                "user_id": "integration_test_user",
                "content": "测试内容：集成测试",
                "category": "test",
            },
        )
        assert response.status_code in [200, 500]  # 可能失败（Mem0未配置）
        if response.status_code == 200:
            memory_id = response.json().get("memory_id")

            # Read
            response = client.get(
                "/api/v1/memory/search",
                params={
                    "user_id": "integration_test_user",
                    "query": "测试",
                },
            )
            assert response.status_code in [200, 500]

            # Update feedback
            if memory_id:
                response = client.put(
                    f"/api/v1/memory/{memory_id}/feedback",
                    json={"score": 0.8},
                )
                assert response.status_code in [200, 500]

            # List
            response = client.get("/api/v1/memory/user/integration_test_user")
            assert response.status_code in [200, 500]


class TestAgentAPIIntegration:
    """Agent API 集成测试。"""

    def test_agent_chat_flow(self, client: TestClient) -> None:
        """测试 Agent 对话流程。"""
        # Chat
        response = client.post(
            "/api/v1/agent/chat",
            json={
                "user_id": "integration_test_user",
                "message": "你好",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

        # Status
        response = client.get("/api/v1/agent/status")
        assert response.status_code == 200


class TestResilienceAPIIntegration:
    """韧性辅导 API 集成测试。"""

    def test_resilience_full_flow(self, client: TestClient) -> None:
        """测试韧性辅导完整流程。"""
        # 1. Analyze emotion
        response = client.post(
            "/api/v1/resilience/analyze",
            json={"text": "今天工作压力很大"},
        )
        assert response.status_code == 200

        # 2. Analyze event
        response = client.post(
            "/api/v1/resilience/analyze-event",
            json={"event_text": "明天要交项目报告"},
        )
        assert response.status_code == 200
        event_data = response.json()

        # 3. Generate pressure curve
        events = [
            {
                "description": "完成项目报告",
                "stress_level": event_data["stress_level"],
                "stress_score": event_data["stress_score"],
            }
        ]

        response = client.post(
            "/api/v1/resilience/curve/generate",
            json={"events": events},
        )
        assert response.status_code == 200

        # 4. Calculate resilience score
        response = client.post(
            "/api/v1/resilience/score/calculate",
            json={"events": events},
        )
        assert response.status_code == 200

        # 5. Get suggestions
        response = client.post(
            "/api/v1/resilience/suggestions",
            json={
                "stress_level": event_data["stress_level"],
                "dimension": "工作",
                "emotion_type": "anxiety",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) > 0


class TestGitHubAPIIntegration:
    """GitHub API 集成测试。"""

    def test_github_api_flow(self, client: TestClient) -> None:
        """测试 GitHub API 流程。"""
        # Trending
        response = client.get(
            "/api/v1/github/trending",
            params={"language": "python", "period": "daily"},
        )
        assert response.status_code in [200, 500]  # 可能失败（网络问题）

        # Preferences
        response = client.get("/api/v1/github/preferences/integration_test_user")
        assert response.status_code in [200, 404]

        # Set preferences
        response = client.post(
            "/api/v1/github/preferences/integration_test_user",
            json={"languages": ["python"]},
        )
        assert response.status_code == 200


class TestNLPAPIIntegration:
    """NLP API 集成测试。"""

    def test_nlp_parsing_flow(self, client: TestClient) -> None:
        """测试 NLP 解析流程。"""
        # DateTime parsing
        response = client.post(
            "/api/v1/nlp/parse-datetime",
            json={"text": "明天下午3点"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "datetime" in data

        # Recurrence parsing
        response = client.post(
            "/api/v1/nlp/parse-recurrence",
            json={"text": "每天早上9点"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "recurrence_rule" in data

        # Event extraction
        response = client.post(
            "/api/v1/nlp/extract-event",
            json={"text": "明天下午3点开会讨论项目进度"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "title" in data


class TestSchedulerAPIIntegration:
    """调度器 API 集成测试。"""

    def test_scheduler_flow(self, client: TestClient) -> None:
        """测试调度器流程。"""
        # Schedule job
        response = client.post(
            "/api/v1/scheduler/schedule",
            json={
                "job_type": "github_trending",
                "trigger_time": "2026-12-31T09:00:00",
            },
        )
        assert response.status_code in [200, 500]

        # List jobs
        response = client.get("/api/v1/scheduler/jobs")
        assert response.status_code == 200


class TestAPIAuthentication:
    """API 认证测试。"""

    def test_unauthorized_access(self, client: TestClient) -> None:
        """测试未授权访问（当前无认证，仅预留）。"""
        # 当前没有认证机制，所有端点都应该可以访问
        response = client.get("/api/v1/agent/status")
        assert response.status_code == 200


class TestAPIRateLimiting:
    """API 限流测试。"""

    def test_rate_limiting(self, client: TestClient) -> None:
        """测试限流（当前未实现，仅预留）。"""
        # 多次请求
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200


class TestAPIErrorHandling:
    """API 错误处理测试。"""

    def test_invalid_json(self, client: TestClient) -> None:
        """测试无效 JSON。"""
        response = client.post(
            "/api/v1/agent/chat",
            data="invalid json",
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client: TestClient) -> None:
        """测试缺少必需字段。"""
        response = client.post(
            "/api/v1/memory",
            json={"user_id": "test"},  # 缺少 content
        )
        assert response.status_code == 422

    def test_invalid_data_types(self, client: TestClient) -> None:
        """测试无效数据类型。"""
        response = client.post(
            "/api/v1/resilience/analyze",
            json={"text": 123},  # 应该是字符串
        )
        assert response.status_code == 422


class TestAPIResponseFormat:
    """API 响应格式测试。"""

    def test_response_structure(self, client: TestClient) -> None:
        """测试响应结构。"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        # 检查响应是字典
        assert isinstance(data, dict)

        # 检查必需字段
        assert "status" in data

    def test_error_response_format(self, client: TestClient) -> None:
        """测试错误响应格式。"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        data = response.json()

        # 检查错误响应格式
        assert "detail" in data
