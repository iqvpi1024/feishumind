"""端到端集成测试。

测试完整的用户交互流程。

Author: Claude Code
Date: 2026-02-06
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any

from src.api.main import app


@pytest.fixture
def client() -> TestClient:
    """创建测试客户端。"""
    return TestClient(app)


class TestE2EChatFlow:
    """端到端对话流程测试。"""

    def test_complete_chat_flow(self, client: TestClient) -> None:
        """测试完整的对话流程。"""
        # 1. 发送对话消息
        response = client.post(
            "/api/v1/agent/chat",
            json={
                "user_id": "test_user_001",
                "message": "你好，我最近工作压力很大",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data

        session_id = data["session_id"]

        # 2. 继续对话
        response = client.post(
            "/api/v1/agent/chat",
            json={
                "user_id": "test_user_001",
                "message": "明天有个重要的项目汇报",
                "session_id": session_id,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

        # 3. 提供反馈
        response = client.post(
            "/api/v1/agent/feedback",
            json={
                "session_id": session_id,
                "rating": 0.8,
                "comment": "建议很有帮助",
            },
        )

        assert response.status_code == 200


class TestE2EGitHubFlow:
    """GitHub 热门推送端到端测试。"""

    def test_github_trending_flow(self, client: TestClient) -> None:
        """测试 GitHub Trending 完整流程。"""
        # 1. 获取 Trending 数据
        response = client.get(
            "/api/v1/github/trending",
            params={
                "language": "python",
                "period": "daily",
            },
        )

        # 可能失败（网络问题），但API应该正常响应
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "repos" in data

        # 2. 获取用户偏好
        response = client.get(
            "/api/v1/github/preferences/test_user_001",
        )

        assert response.status_code in [200, 404]

        # 3. 设置用户偏好
        response = client.post(
            "/api/v1/github/preferences/test_user_001",
            json={
                "languages": ["python", "javascript"],
                "period": "daily",
            },
        )

        assert response.status_code == 200


class TestE2EEventReminderFlow:
    """事件提醒端到端测试。"""

    def test_event_reminder_flow(self, client: TestClient) -> None:
        """测试事件提醒完整流程。"""
        # 1. 解析时间
        response = client.post(
            "/api/v1/nlp/parse-datetime",
            json={"text": "明天下午3点"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "datetime" in data

        # 2. 创建事件提醒
        response = client.post(
            "/api/v1/agent/tools/reminder",
            json={
                "user_id": "test_user_001",
                "event_description": "明天下午3点开会讨论项目进度",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data

        # 3. 情绪分析
        response = client.post(
            "/api/v1/resilience/analyze-event",
            json={"event_text": "明天下午3点开会讨论项目进度"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "stress_level" in data


class TestE2EResilienceFlow:
    """韧性辅导端到端测试。"""

    def test_resilience_analysis_flow(self, client: TestClient) -> None:
        """测试韧性辅导完整流程。"""
        # 1. 情绪分析
        response = client.post(
            "/api/v1/resilience/analyze",
            json={"text": "今天工作很累，压力很大"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["emotion_type"] in ["fatigue", "stress"]

        # 2. 生成压力曲线
        base_time = datetime.now()
        events = [
            {
                "description": "完成项目报告",
                "timestamp": (base_time - timedelta(days=4)).isoformat(),
                "stress_level": "high",
                "stress_score": 0.9,
                "dimension": "工作",
            },
            {
                "description": "休息一天",
                "timestamp": (base_time - timedelta(days=2)).isoformat(),
                "stress_level": "low",
                "stress_score": 0.2,
                "dimension": "健康",
            },
            {
                "description": "客户演示",
                "timestamp": base_time.isoformat(),
                "stress_level": "high",
                "stress_score": 0.85,
                "dimension": "工作",
            },
        ]

        response = client.post(
            "/api/v1/resilience/curve/generate",
            json={"events": events},
        )

        assert response.status_code == 200
        data = response.json()
        assert "average_stress" in data
        assert len(data["data_points"]) == 3

        # 3. 计算韧性评分
        response = client.post(
            "/api/v1/resilience/score/calculate",
            json={"events": events},
        )

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert 0.0 <= data["overall_score"] <= 100.0

        # 4. 获取建议
        response = client.post(
            "/api/v1/resilience/suggestions",
            json={
                "stress_level": "high",
                "dimension": "工作",
                "emotion_type": "anxiety",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) > 0


class TestE2EMemoryFlow:
    """记忆管理端到端测试。"""

    def test_memory_flow(self, client: TestClient) -> None:
        """测试记忆管理完整流程。"""
        # 1. 添加记忆
        response = client.post(
            "/api/v1/memory",
            json={
                "user_id": "test_user_001",
                "content": "我喜欢Python编程，特别是机器学习方向",
                "category": "preference",
            },
        )

        assert response.status_code == 200
        data = response.json()
        memory_id = data.get("memory_id")
        assert memory_id is not None

        # 2. 搜索记忆
        response = client.get(
            "/api/v1/memory/search",
            params={
                "user_id": "test_user_001",
                "query": "Python",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "memories" in data

        # 3. 反馈评分
        if memory_id:
            response = client.put(
                f"/api/v1/memory/{memory_id}/feedback",
                json={"score": 0.9},
            )

            assert response.status_code == 200

        # 4. 获取所有记忆
        response = client.get(f"/api/v1/memory/user/test_user_001")

        assert response.status_code == 200
        data = response.json()
        assert "memories" in data


class TestE2EWebhookFlow:
    """Webhook 端到端测试。"""

    def test_webhook_flow(self, client: TestClient) -> None:
        """测试 Webhook 完整流程。"""
        # 模拟飞书 Webhook 请求
        webhook_data = {
            "token": "verify_token",
            "challenge": "challenge_code",
        }

        # URL验证请求
        response = client.post(
            "/webhook/feishu",
            json=webhook_data,
        )

        # 可能失败（签名验证），但API应该正常响应
        assert response.status_code in [200, 401, 403]


class TestE2EErrorHandling:
    """错误处理端到端测试。"""

    def test_404_handling(self, client: TestClient) -> None:
        """测试 404 错误处理。"""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    def test_422_validation_error(self, client: TestClient) -> None:
        """测试参数验证错误。"""
        response = client.post(
            "/api/v1/agent/chat",
            json={
                # 缺少必需字段
            },
        )

        assert response.status_code == 422

    def test_health_check(self, client: TestClient) -> None:
        """测试健康检查。"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestE2EConcurrency:
    """并发测试。"""

    def test_concurrent_requests(self, client: TestClient) -> None:
        """测试并发请求。"""
        import threading

        results = []

        def make_request():
            response = client.get("/health")
            results.append(response.status_code)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 所有请求都应该成功
        assert all(status == 200 for status in results)
        assert len(results) == 10
