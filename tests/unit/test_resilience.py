"""韧性辅导系统单元测试。

测试情绪分析、压力曲线生成、韧性评分等功能。

Author: Claude Code
Date: 2026-02-06
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.utils.sentiment import (
    EmotionAnalyzer,
    EmotionType,
    StressLevel,
    EmotionAnalysisResult,
)
from src.utils.resilience import (
    PressureCurveGenerator,
    ResilienceAdvisor,
    ResilienceScorer,
    PressureCurve,
    ResilienceScore,
    ResilienceLevel,
)


# ============ 情绪分析器测试 ============


class TestEmotionAnalyzer:
    """情绪分析器测试类。"""

    @pytest.fixture
    def analyzer(self) -> EmotionAnalyzer:
        """创建情绪分析器实例。"""
        return EmotionAnalyzer()

    def test_analyze_joy_emotion(self, analyzer: EmotionAnalyzer) -> None:
        """测试喜悦情绪分析。"""
        result = analyzer.analyze("今天很开心，工作完成得很顺利")

        assert result.emotion_type == EmotionType.JOY
        assert result.intensity > 0.5
        assert result.dimension == "工作"
        assert result.confidence > 0.3

    def test_analyze_anxiety_emotion(self, analyzer: EmotionAnalyzer) -> None:
        """测试焦虑情绪分析。"""
        result = analyzer.analyze("明天要考试，非常担心考不好")

        assert result.emotion_type == EmotionType.ANXIETY
        assert result.intensity > 0.5
        assert result.dimension == "学习"
        assert result.confidence > 0.3

    def test_analyze_fatigue_emotion(self, analyzer: EmotionAnalyzer) -> None:
        """测试疲惫情绪分析。"""
        result = analyzer.analyze("今天工作特别累，精疲力尽")

        assert result.emotion_type == EmotionType.FATIGUE
        assert result.intensity > 0.5
        assert result.confidence > 0.3

    def test_analyze_anger_emotion(self, analyzer: EmotionAnalyzer) -> None:
        """测试愤怒情绪分析。"""
        result = analyzer.analyze("客户的要求非常不合理，很生气")

        assert result.emotion_type == EmotionType.ANGER
        assert result.intensity > 0.5
        assert result.confidence > 0.3

    def test_analyze_calm_emotion(self, analyzer: EmotionAnalyzer) -> None:
        """测试平静情绪分析。"""
        result = analyzer.analyze("今天状态不错，心情很平静")

        assert result.emotion_type == EmotionType.CALM
        assert result.intensity > 0.0
        assert result.confidence > 0.3

    def test_analyze_empty_text(self, analyzer: EmotionAnalyzer) -> None:
        """测试空文本分析。"""
        result = analyzer.analyze("")

        assert result.emotion_type == EmotionType.CALM
        assert result.intensity == 0.0
        assert result.confidence == 0.0

    def test_batch_analyze(self, analyzer: EmotionAnalyzer) -> None:
        """测试批量分析。"""
        texts = [
            "今天很开心",
            "压力很大",
            "感觉很累",
        ]

        results = analyzer.batch_analyze(texts)

        assert len(results) == 3
        assert results[0].emotion_type == EmotionType.JOY
        assert results[1].emotion_type in [EmotionType.STRESS, EmotionType.ANXIETY]
        assert results[2].emotion_type == EmotionType.FATIGUE

    def test_intensity_with_modifier(self, analyzer: EmotionAnalyzer) -> None:
        """测试强度修饰词。"""
        result1 = analyzer.analyze("很开心")
        result2 = analyzer.analyze("非常开心")

        # "非常"应该增加强度
        assert result2.intensity > result1.intensity

    def test_dimension_detection(self, analyzer: EmotionAnalyzer) -> None:
        """测试维度检测。"""
        result1 = analyzer.analyze("工作压力很大")
        result2 = analyzer.analyze("身体不舒服")
        result3 = analyzer.analyze("朋友聚会很开心")

        assert result1.dimension == "工作"
        assert result2.dimension == "健康"
        assert result3.dimension == "社交"


# ============ 压力曲线生成器测试 ============


class TestPressureCurveGenerator:
    """压力曲线生成器测试类。"""

    @pytest.fixture
    def generator(self) -> PressureCurveGenerator:
        """创建压力曲线生成器实例。"""
        return PressureCurveGenerator()

    @pytest.fixture
    def sample_events(self) -> List[Dict[str, Any]]:
        """创建示例事件列表。"""
        base_time = datetime.now()

        events = [
            {
                "description": "完成项目报告",
                "timestamp": base_time - timedelta(days=4),
                "stress_level": "high",
                "stress_score": 0.9,
            },
            {
                "description": "团队会议",
                "timestamp": base_time - timedelta(days=3),
                "stress_level": "medium",
                "stress_score": 0.6,
            },
            {
                "description": "代码审查",
                "timestamp": base_time - timedelta(days=2),
                "stress_level": "medium",
                "stress_score": 0.5,
            },
            {
                "description": "休息一天",
                "timestamp": base_time - timedelta(days=1),
                "stress_level": "low",
                "stress_score": 0.2,
            },
            {
                "description": "客户演示",
                "timestamp": base_time,
                "stress_level": "high",
                "stress_score": 0.95,
            },
        ]

        return events

    def test_add_data_point(self, generator: PressureCurveGenerator) -> None:
        """测试添加数据点。"""
        point = generator.add_data_point(
            event_description="测试事件",
            stress_level=StressLevel.HIGH,
            stress_score=0.8,
        )

        assert point.event_description == "测试事件"
        assert point.stress_level == StressLevel.HIGH
        assert point.stress_score == 0.8
        assert len(generator.data_points) == 1

    def test_generate_curve_from_events(
        self, generator: PressureCurveGenerator, sample_events: List[Dict[str, Any]]
    ) -> None:
        """测试从事件生成曲线。"""
        curve = generator.generate_from_events(sample_events)

        assert isinstance(curve, PressureCurve)
        assert len(curve.data_points) == 5
        assert curve.average_stress > 0.0
        assert curve.peak_stress > 0.0

    def test_average_stress_calculation(
        self, generator: PressureCurveGenerator, sample_events: List[Dict[str, Any]]
    ) -> None:
        """测试平均压力计算。"""
        curve = generator.generate_from_events(sample_events)

        # 平均压力应该是 (0.9 + 0.6 + 0.5 + 0.2 + 0.95) / 5 = 0.63
        expected_avg = (0.9 + 0.6 + 0.5 + 0.2 + 0.95) / 5
        assert abs(curve.average_stress - expected_avg) < 0.01

    def test_peak_stress_detection(
        self, generator: PressureCurveGenerator, sample_events: List[Dict[str, Any]]
    ) -> None:
        """测试峰值压力检测。"""
        curve = generator.generate_from_events(sample_events)

        # 峰值应该是 0.95
        assert curve.peak_stress == 0.95

    def test_trend_analysis_rising(self, generator: PressureCurveGenerator) -> None:
        """测试上升趋势分析。"""
        base_time = datetime.now()
        events = [
            {
                "description": "事件1",
                "timestamp": base_time - timedelta(days=3),
                "stress_level": "low",
                "stress_score": 0.3,
            },
            {
                "description": "事件2",
                "timestamp": base_time - timedelta(days=2),
                "stress_level": "medium",
                "stress_score": 0.5,
            },
            {
                "description": "事件3",
                "timestamp": base_time - timedelta(days=1),
                "stress_level": "high",
                "stress_score": 0.8,
            },
            {
                "description": "事件4",
                "timestamp": base_time,
                "stress_level": "high",
                "stress_score": 0.9,
            },
        ]

        curve = generator.generate_from_events(events)
        assert curve.trend == "rising"

    def test_trend_analysis_falling(self, generator: PressureCurveGenerator) -> None:
        """测试下降趋势分析。"""
        base_time = datetime.now()
        events = [
            {
                "description": "事件1",
                "timestamp": base_time - timedelta(days=3),
                "stress_level": "high",
                "stress_score": 0.9,
            },
            {
                "description": "事件2",
                "timestamp": base_time - timedelta(days=2),
                "stress_level": "high",
                "stress_score": 0.8,
            },
            {
                "description": "事件3",
                "timestamp": base_time - timedelta(days=1),
                "stress_level": "medium",
                "stress_score": 0.5,
            },
            {
                "description": "事件4",
                "timestamp": base_time,
                "stress_level": "low",
                "stress_score": 0.3,
            },
        ]

        curve = generator.generate_from_events(events)
        assert curve.trend == "falling"

    def test_future_predictions(
        self, generator: PressureCurveGenerator, sample_events: List[Dict[str, Any]]
    ) -> None:
        """测试未来预测。"""
        curve = generator.generate_from_events(sample_events)

        assert len(curve.predictions) == 3
        assert all(0.0 <= p <= 1.0 for p in curve.predictions)

    def test_get_peaks_and_valleys(
        self, generator: PressureCurveGenerator, sample_events: List[Dict[str, Any]]
    ) -> None:
        """测试获取峰值和低谷。"""
        curve = generator.generate_from_events(sample_events)
        peaks_and_valleys = generator.get_peaks_and_valleys(curve)

        assert "peaks" in peaks_and_valleys
        assert "valleys" in peaks_and_valleys
        assert isinstance(peaks_and_valleys["peaks"], list)
        assert isinstance(peaks_and_valleys["valleys"], list)

    def test_get_summary(
        self, generator: PressureCurveGenerator, sample_events: List[Dict[str, Any]]
    ) -> None:
        """测试获取摘要。"""
        curve = generator.generate_from_events(sample_events)
        summary = generator.get_summary(curve)

        assert "total_data_points" in summary
        assert "average_stress" in summary
        assert "peak_stress" in summary
        assert "trend" in summary
        assert "status" in summary
        assert summary["total_data_points"] == 5


# ============ 韧性建议系统测试 ============


class TestResilienceAdvisor:
    """韧性建议系统测试类。"""

    @pytest.fixture
    def advisor(self) -> ResilienceAdvisor:
        """创建韧性建议系统实例。"""
        return ResilienceAdvisor()

    def test_get_suggestions_high_stress(self, advisor: ResilienceAdvisor) -> None:
        """测试高压力建议。"""
        suggestions = advisor.get_suggestions(
            stress_level="high",
            dimension="工作",
            emotion_type="anxiety",
        )

        assert len(suggestions) > 0
        assert all("category" in s and "suggestion" in s for s in suggestions)

        # 检查是否包含放松建议
        categories = [s["category"] for s in suggestions]
        assert "放松技巧" in categories or "工作调整" in categories

    def test_get_suggestions_medium_stress(self, advisor: ResilienceAdvisor) -> None:
        """测试中等压力建议。"""
        suggestions = advisor.get_suggestions(
            stress_level="medium",
            dimension="工作",
            emotion_type="calm",
        )

        assert len(suggestions) > 0
        assert all("category" in s and "suggestion" in s for s in suggestions)

    def test_get_suggestions_low_stress(self, advisor: ResilienceAdvisor) -> None:
        """测试低压力建议。"""
        suggestions = advisor.get_suggestions(
            stress_level="low",
            dimension="学习",
            emotion_type="joy",
        )

        assert len(suggestions) > 0

    def test_get_suggestions_health_dimension(self, advisor: ResilienceAdvisor) -> None:
        """测试健康维度建议。"""
        suggestions = advisor.get_suggestions(
            stress_level="high",
            dimension="健康",
            emotion_type="fatigue",
        )

        categories = [s["category"] for s in suggestions]
        assert "睡眠改善" in categories or "运动建议" in categories

    def test_get_action_plan(self, advisor: ResilienceAdvisor) -> None:
        """测试获取行动计划。"""
        plan = advisor.get_action_plan(
            stress_level="high",
            dimension="工作",
            emotion_type="anxiety",
        )

        assert "immediate" in plan
        assert "short_term" in plan
        assert "long_term" in plan
        assert "total_count" in plan
        assert plan["total_count"] > 0
        assert len(plan["immediate"]) >= 2


# ============ 韧性评分系统测试 ============


class TestResilienceScorer:
    """韧性评分系统测试类。"""

    @pytest.fixture
    def scorer(self) -> ResilienceScorer:
        """创建韧性评分系统实例。"""
        return ResilienceScorer()

    @pytest.fixture
    def sample_events(self) -> List[Dict[str, Any]]:
        """创建示例事件列表。"""
        base_time = datetime.now()

        events = [
            {
                "description": "完成项目报告",
                "timestamp": base_time - timedelta(days=4),
                "stress_level": "high",
                "stress_score": 0.9,
                "dimension": "工作",
            },
            {
                "description": "团队会议",
                "timestamp": base_time - timedelta(days=3),
                "stress_level": "medium",
                "stress_score": 0.6,
                "dimension": "工作",
            },
            {
                "description": "休息一天",
                "timestamp": base_time - timedelta(days=2),
                "stress_level": "low",
                "stress_score": 0.2,
                "dimension": "健康",
            },
            {
                "description": "朋友聚会",
                "timestamp": base_time - timedelta(days=1),
                "stress_level": "low",
                "stress_score": 0.3,
                "dimension": "社交",
            },
            {
                "description": "客户演示",
                "timestamp": base_time,
                "stress_level": "high",
                "stress_score": 0.85,
                "dimension": "工作",
            },
        ]

        return events

    def test_calculate_score(self, scorer: ResilienceScorer, sample_events: List[Dict[str, Any]]) -> None:
        """测试计算韧性评分。"""
        score = scorer.calculate_score(sample_events)

        assert isinstance(score, ResilienceScore)
        assert 0.0 <= score.overall_score <= 100.0
        assert isinstance(score.level, ResilienceLevel)
        assert isinstance(score.dimension_scores, dict)
        assert isinstance(score.suggestions, list)

    def test_score_with_low_stress(self, scorer: ResilienceScorer) -> None:
        """测试低压力评分。"""
        base_time = datetime.now()
        events = [
            {
                "description": "轻松工作",
                "timestamp": base_time - timedelta(days=1),
                "stress_level": "low",
                "stress_score": 0.2,
                "dimension": "工作",
            },
            {
                "description": "休息放松",
                "timestamp": base_time,
                "stress_level": "low",
                "stress_score": 0.1,
                "dimension": "健康",
            },
        ]

        score = scorer.calculate_score(events)

        # 低压力应该得到较高的韧性评分
        assert score.overall_score > 60.0
        assert score.level in [ResilienceLevel.GOOD, ResilienceLevel.EXCELLENT, ResilienceLevel.NORMAL]

    def test_score_with_high_stress(self, scorer: ResilienceScorer) -> None:
        """测试高压力评分。"""
        base_time = datetime.now()
        events = [
            {
                "description": "紧急项目",
                "timestamp": base_time - timedelta(days=1),
                "stress_level": "high",
                "stress_score": 0.95,
                "dimension": "工作",
            },
            {
                "description": "客户投诉",
                "timestamp": base_time,
                "stress_level": "high",
                "stress_score": 0.9,
                "dimension": "工作",
            },
        ]

        score = scorer.calculate_score(events)

        # 高压力应该得到较低的韧性评分
        assert score.overall_score < 40.0
        assert score.level in [ResilienceLevel.CRITICAL, ResilienceLevel.WARNING]

    def test_dimension_scores(self, scorer: ResilienceScorer, sample_events: List[Dict[str, Any]]) -> None:
        """测试维度评分。"""
        score = scorer.calculate_score(sample_events)

        assert "工作" in score.dimension_scores
        assert 0.0 <= score.dimension_scores["工作"] <= 100.0

    def test_suggestions_generation(self, scorer: ResilienceScorer, sample_events: List[Dict[str, Any]]) -> None:
        """测试建议生成。"""
        score = scorer.calculate_score(sample_events)

        assert len(score.suggestions) > 0
        assert all(isinstance(s, str) for s in score.suggestions)

    def test_score_with_falling_trend(self, scorer: ResilienceScorer) -> None:
        """测试下降趋势的加分。"""
        base_time = datetime.now()
        events = [
            {
                "description": "高压力事件1",
                "timestamp": base_time - timedelta(days=3),
                "stress_level": "high",
                "stress_score": 0.9,
                "dimension": "工作",
            },
            {
                "description": "中等压力",
                "timestamp": base_time - timedelta(days=2),
                "stress_level": "medium",
                "stress_score": 0.6,
                "dimension": "工作",
            },
            {
                "description": "低压力事件",
                "timestamp": base_time - timedelta(days=1),
                "stress_level": "low",
                "stress_score": 0.3,
                "dimension": "工作",
            },
            {
                "description": "轻松状态",
                "timestamp": base_time,
                "stress_level": "low",
                "stress_score": 0.2,
                "dimension": "工作",
            },
        ]

        score1 = scorer.calculate_score(events)

        # 下降趋势应该加分
        assert score1.overall_score > 40.0  # 基础分 + 趋势加分
