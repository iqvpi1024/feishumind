"""韧性辅导 API 路由测试。

测试韧性辅导相关的 API 端点。

Author: Claude Code
Date: 2026-02-06
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.api.main import app
from src.utils.sentiment import StressLevel


# ============ 测试客户端 ============


@pytest.fixture
def client() -> TestClient:
    """创建测试客户端。"""
    return TestClient(app)


# ============ 情绪分析 API 测试 ============


class TestAnalyzeEmotionAPI:
    """情绪分析 API 测试类。"""

    def test_analyze_emotion_success(self, client: TestClient) -> None:
        """测试成功分析情绪。"""
        response = client.post(
            "/api/v1/resilience/analyze",
            json={"text": "今天很开心，工作完成得很顺利"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "emotion_type" in data
        assert "intensity" in data
        assert "confidence" in data
        assert "dimension" in data
        assert "timestamp" in data
        assert 0.0 <= data["intensity"] <= 1.0
        assert 0.0 <= data["confidence"] <= 1.0

    def test_analyze_emotion_empty_text(self, client: TestClient) -> None:
        """测试空文本分析。"""
        response = client.post(
            "/api/v1/resilience/analyze",
            json={"text": ""},
        )

        assert response.status_code == 422  # Validation error

    def test_analyze_emotion_long_text(self, client: TestClient) -> None:
        """测试长文本分析。"""
        long_text = "今天很开心，" * 100  # 约 800 字符

        response = client.post(
            "/api/v1/resilience/analyze",
            json={"text": long_text},
        )

        assert response.status_code == 200


# ============ 事件情绪分析 API 测试 ============


class TestAnalyzeEventAPI:
    """事件情绪分析 API 测试类。"""

    def test_analyze_event_success(self, client: TestClient) -> None:
        """测试成功分析事件情绪。"""
        response = client.post(
            "/api/v1/resilience/analyze-event",
            json={"event_text": "明天要交项目周报，压力很大"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "stress_level" in data
        assert "emoji" in data
        assert "stress_score" in data
        assert "matched_keywords" in data
        assert "factors" in data
        assert "suggestions" in data
        assert 0.0 <= data["stress_score"] <= 1.0

    def test_analyze_event_low_stress(self, client: TestClient) -> None:
        """测试低压力事件分析。"""
        response = client.post(
            "/api/v1/resilience/analyze-event",
            json={"event_text": "今天天气很好，心情不错"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stress_level"] == "low"

    def test_analyze_event_high_stress(self, client: TestClient) -> None:
        """测试高压力事件分析。"""
        response = client.post(
            "/api/v1/resilience/analyze-event",
            json={"event_text": "明天是项目截止日期，必须完成"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stress_level"] == "high"


# ============ 压力曲线 API 测试 ============


class TestPressureCurveAPI:
    """压力曲线 API 测试类。"""

    @pytest.fixture
    def sample_events(self) -> List[Dict[str, Any]]:
        """创建示例事件列表。"""
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
                "description": "团队会议",
                "timestamp": (base_time - timedelta(days=3)).isoformat(),
                "stress_level": "medium",
                "stress_score": 0.6,
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
                "description": "朋友聚会",
                "timestamp": (base_time - timedelta(days=1)).isoformat(),
                "stress_level": "low",
                "stress_score": 0.3,
                "dimension": "社交",
            },
            {
                "description": "客户演示",
                "timestamp": base_time.isoformat(),
                "stress_level": "high",
                "stress_score": 0.95,
                "dimension": "工作",
            },
        ]

        return events

    def test_generate_pressure_curve_success(self, client: TestClient, sample_events: List[Dict[str, Any]]) -> None:
        """测试成功生成压力曲线。"""
        response = client.post(
            "/api/v1/resilience/curve/generate",
            json={"events": sample_events},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data_points" in data
        assert "average_stress" in data
        assert "peak_stress" in data
        assert "trend" in data
        assert "predictions" in data
        assert "summary" in data
        assert len(data["data_points"]) == 5
        assert 0.0 <= data["average_stress"] <= 1.0
        assert 0.0 <= data["peak_stress"] <= 1.0
        assert len(data["predictions"]) == 3

    def test_generate_pressure_curve_auto_analyze(self, client: TestClient) -> None:
        """测试自动分析压力等级。"""
        events = [
            {
                "description": "明天要交项目周报",
            },
            {
                "description": "今天天气很好",
            },
            {
                "description": "客户会议",
            },
        ]

        response = client.post(
            "/api/v1/resilience/curve/generate",
            json={"events": events},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data_points"]) == 3

    def test_generate_pressure_curve_empty_events(self, client: TestClient) -> None:
        """测试空事件列表。"""
        response = client.post(
            "/api/v1/resilience/curve/generate",
            json={"events": []},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data_points"]) == 0


# ============ 韧性评分 API 测试 ============


class TestResilienceScoreAPI:
    """韧性评分 API 测试类。"""

    @pytest.fixture
    def sample_events(self) -> List[Dict[str, Any]]:
        """创建示例事件列表。"""
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

        return events

    def test_calculate_resilience_score_success(self, client: TestClient, sample_events: List[Dict[str, Any]]) -> None:
        """测试成功计算韧性评分。"""
        response = client.post(
            "/api/v1/resilience/score/calculate",
            json={"events": sample_events},
        )

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "level" in data
        assert "dimension_scores" in data
        assert "suggestions" in data
        assert "timestamp" in data
        assert 0.0 <= data["overall_score"] <= 100.0

    def test_calculate_resilience_score_low_stress(self, client: TestClient) -> None:
        """测试低压力韧性评分。"""
        events = [
            {
                "description": "轻松工作",
                "stress_level": "low",
                "stress_score": 0.2,
                "dimension": "工作",
            },
            {
                "description": "休息放松",
                "stress_level": "low",
                "stress_score": 0.1,
                "dimension": "健康",
            },
        ]

        response = client.post(
            "/api/v1/resilience/score/calculate",
            json={"events": events},
        )

        assert response.status_code == 200
        data = response.json()
        # 低压力应该得到较高的韧性评分
        assert data["overall_score"] > 60.0

    def test_calculate_resilience_score_high_stress(self, client: TestClient) -> None:
        """测试高压力韧性评分。"""
        events = [
            {
                "description": "紧急项目",
                "stress_level": "high",
                "stress_score": 0.95,
                "dimension": "工作",
            },
            {
                "description": "客户投诉",
                "stress_level": "high",
                "stress_score": 0.9,
                "dimension": "工作",
            },
        ]

        response = client.post(
            "/api/v1/resilience/score/calculate",
            json={"events": events},
        )

        assert response.status_code == 200
        data = response.json()
        # 高压力应该得到较低的韧性评分
        assert data["overall_score"] < 40.0


# ============ 建议获取 API 测试 ============


class TestSuggestionsAPI:
    """建议获取 API 测试类。"""

    def test_get_suggestions_success(self, client: TestClient) -> None:
        """测试成功获取建议。"""
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
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
        assert all("category" in s and "suggestion" in s for s in data["suggestions"])

    def test_get_suggestions_medium_stress(self, client: TestClient) -> None:
        """测试中等压力建议。"""
        response = client.post(
            "/api/v1/resilience/suggestions",
            json={
                "stress_level": "medium",
                "dimension": "学习",
                "emotion_type": "calm",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) > 0

    def test_get_action_plan_success(self, client: TestClient) -> None:
        """测试成功获取行动计划。"""
        response = client.post(
            "/api/v1/resilience/action-plan",
            json={
                "stress_level": "high",
                "dimension": "工作",
                "emotion_type": "anxiety",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "immediate" in data
        assert "short_term" in data
        assert "long_term" in data
        assert "total_count" in data
        assert data["total_count"] > 0
        assert len(data["immediate"]) >= 2


# ============ 健康检查 API 测试 ============


class TestHealthCheckAPI:
    """健康检查 API 测试类。"""

    def test_health_check(self, client: TestClient) -> None:
        """测试健康检查。"""
        response = client.get("/api/v1/resilience/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
