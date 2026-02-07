"""情绪检测和压力识别模块单元测试。

测试 StressEventClassifier 和 EventSentimentAnalyzer 的功能。

Author: Claude Code
Date: 2026-02-06
"""

import pytest

from src.utils.sentiment import (
    StressLevel,
    StressEventClassifier,
    EventSentimentAnalyzer,
    classify_stress_level,
    analyze_event_sentiment,
)


class TestStressEventClassifier:
    """StressEventClassifier 测试类。"""

    def setup_method(self):
        """测试前设置。"""
        self.classifier = StressEventClassifier()

    def test_classify_high_stress(self):
        """测试分类高压力事件。"""
        result = self.classifier.classify("明天要交项目周报")
        assert result == StressLevel.HIGH

    def test_classify_medium_stress(self):
        """测试分类中压力事件。"""
        result = self.classifier.classify("明天下午3点开会")
        assert result == StressLevel.MEDIUM

    def test_classify_low_stress(self):
        """测试分类低压力事件。"""
        result = self.classifier.classify("明天下午3点去喝咖啡")
        assert result == StressLevel.LOW

    def test_classify_with_deadline(self):
        """测试包含截止日期的高压力。"""
        result = self.classifier.classify("项目截止日期是明天")
        assert result == StressLevel.HIGH

    def test_classify_with_presentation(self):
        """测试包含演示的高压力。"""
        result = self.classifier.classify("下周要进行项目演示")
        assert result == StressLevel.HIGH

    def test_classify_with_meeting(self):
        """测试包含会议的中压力。"""
        result = self.classifier.classify("明天上午10点开会")
        assert result == StressLevel.MEDIUM

    def test_classify_empty_input(self):
        """测试空输入。"""
        result = self.classifier.classify("")
        assert result == StressLevel.LOW

    def test_classify_with_details(self):
        """测试带详细信息的分类。"""
        result = self.classifier.classify_with_details("明天要交项目周报")
        assert result["level"] == "high"
        assert result["emoji"] == "🔴"
        assert "matched_keywords" in result
        assert len(result["matched_keywords"]) > 0


class TestEventSentimentAnalyzer:
    """EventSentimentAnalyzer 测试类。"""

    def setup_method(self):
        """测试前设置。"""
        self.analyzer = EventSentimentAnalyzer()

    def test_analyze_high_stress_event(self):
        """测试分析高压力事件。"""
        result = self.analyzer.analyze("明天要交项目周报")
        assert result["stress_level"] == "high"
        assert result["emoji"] == "🔴"
        assert result["stress_score"] >= 0.7

    def test_analyze_medium_stress_event(self):
        """测试分析中压力事件。"""
        result = self.analyzer.analyze("明天下午3点开会")
        assert result["stress_level"] == "medium"
        assert result["emoji"] == "🟡"

    def test_analyze_low_stress_event(self):
        """测试分析低压力事件。"""
        result = self.analyzer.analyze("明天下午3点去喝咖啡")
        assert result["stress_level"] == "low"
        assert result["emoji"] == "🟢"

    def test_stress_factors_extraction(self):
        """测试压力因素提取。"""
        result = self.analyzer.analyze("明天项目截止，需要汇报")
        assert "factors" in result
        assert len(result["factors"]) > 0

    def test_suggestions_generation(self):
        """测试建议生成。"""
        result = self.analyzer.analyze("明天要交项目周报")
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0
        # 高压力事件应该有4条建议
        assert len(result["suggestions"]) == 4


class TestConvenienceFunctions:
    """便捷函数测试类。"""

    def test_classify_stress_level_convenience(self):
        """测试 classify_stress_level 便捷函数。"""
        result = classify_stress_level("明天要交项目周报")
        assert result == StressLevel.HIGH

    def test_analyze_event_sentiment_convenience(self):
        """测试 analyze_event_sentiment 便捷函数。"""
        result = analyze_event_sentiment("明天下午3点开会")
        assert "stress_level" in result
        assert "stress_score" in result


class TestStressLevelEnum:
    """StressLevel 枚举测试类。"""

    def test_enum_values(self):
        """测试枚举值。"""
        assert StressLevel.LOW.value == "low"
        assert StressLevel.MEDIUM.value == "medium"
        assert StressLevel.HIGH.value == "high"

    def test_enum_comparison(self):
        """测试枚举比较。"""
        assert StressLevel.HIGH == StressLevel.HIGH
        assert StressLevel.HIGH != StressLevel.MEDIUM
