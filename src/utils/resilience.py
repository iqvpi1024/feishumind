"""韧性辅导系统模块。

提供压力曲线生成、韧性评分、个性化建议等功能。

Author: Claude Code
Date: 2026-02-06
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict

from src.utils.logger import get_logger
from src.utils.sentiment import (
    StressLevel,
    EmotionType,
    EmotionAnalyzer,
    EmotionAnalysisResult,
)

logger = get_logger(__name__)


class ResilienceLevel(Enum):
    """韧性等级枚举。

    Attributes:
        EXCELLENT: 优秀（🌟）
        GOOD: 良好（✅）
        NORMAL: 正常（📍）
        WARNING: 需关注（⚠️）
        CRITICAL: 危险（🚨）
    """

    EXCELLENT = "excellent"
    GOOD = "good"
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class StressDataPoint:
    """压力数据点。

    Attributes:
        timestamp: 时间戳
        stress_level: 压力等级
        stress_score: 压力分数（0-1）
        emotion_type: 情绪类型
        intensity: 情绪强度
        dimension: 情绪维度
        event_description: 事件描述
    """

    timestamp: datetime
    stress_level: StressLevel
    stress_score: float
    emotion_type: EmotionType
    intensity: float
    dimension: str
    event_description: str


@dataclass
class PressureCurve:
    """压力曲线。

    Attributes:
        data_points: 数据点列表
        average_stress: 平均压力分数
        peak_stress: 峰值压力
        trend: 趋势（上升/下降/稳定）
        predictions: 未来预测
    """

    data_points: List[StressDataPoint] = field(default_factory=list)
    average_stress: float = 0.0
    peak_stress: float = 0.0
    trend: str = "stable"
    predictions: List[float] = field(default_factory=list)


@dataclass
class ResilienceScore:
    """韧性评分。

    Attributes:
        overall_score: 总体评分（0-100）
        level: 韧性等级
        dimension_scores: 维度评分
        suggestions: 改进建议
        timestamp: 评分时间
    """

    overall_score: float
    level: ResilienceLevel
    dimension_scores: Dict[str, float]
    suggestions: List[str]
    timestamp: datetime


class PressureCurveGenerator:
    """压力曲线生成器。

    基于历史事件数据生成压力曲线。

    Attributes:
        emotion_analyzer: 情绪分析器
        data_points: 历史数据点

    Examples:
        >>> generator = PressureCurveGenerator()
        >>> curve = generator.generate_from_events(events)
        >>> print(curve.average_stress)
    """

    def __init__(self) -> None:
        """初始化压力曲线生成器。"""
        self.emotion_analyzer = EmotionAnalyzer()
        self.data_points: List[StressDataPoint] = []
        logger.info("Pressure curve generator initialized")

    def add_data_point(
        self,
        event_description: str,
        stress_level: StressLevel | str,
        stress_score: float,
        timestamp: Optional[datetime] = None,
    ) -> StressDataPoint:
        """添加数据点。

        Args:
            event_description: 事件描述
            stress_level: 压力等级（StressLevel枚举或字符串）
            stress_score: 压力分数
            timestamp: 时间戳（默认为当前时间）

        Returns:
            添加的数据点
        """
        if timestamp is None:
            timestamp = datetime.now()

        # 如果stress_level是字符串，转换为枚举
        if isinstance(stress_level, str):
            stress_level_map = {
                "low": StressLevel.LOW,
                "medium": StressLevel.MEDIUM,
                "high": StressLevel.HIGH,
            }
            stress_level = stress_level_map.get(stress_level.lower(), StressLevel.LOW)

        # 分析情绪
        emotion_result = self.emotion_analyzer.analyze(event_description)

        data_point = StressDataPoint(
            timestamp=timestamp,
            stress_level=stress_level,
            stress_score=stress_score,
            emotion_type=emotion_result.emotion_type,
            intensity=emotion_result.intensity,
            dimension=emotion_result.dimension,
            event_description=event_description,
        )

        self.data_points.append(data_point)
        logger.debug(f"Added data point: {stress_level.value}, score={stress_score:.2f}")

        return data_point

    def generate_from_events(
        self, events: List[Dict[str, Any]]
    ) -> PressureCurve:
        """从事件列表生成压力曲线。

        Args:
            events: 事件列表，每个事件包含：
                - description: 事件描述
                - timestamp: 时间戳
                - stress_level: 压力等级

        Returns:
            压力曲线对象
        """
        self.data_points.clear()

        for event in events:
            self.add_data_point(
                event_description=event.get("description", ""),
                stress_level=event.get("stress_level", StressLevel.LOW),
                stress_score=event.get("stress_score", 0.3),
                timestamp=event.get("timestamp"),
            )

        return self.generate_curve()

    def generate_curve(self) -> PressureCurve:
        """生成压力曲线。

        Returns:
            压力曲线对象
        """
        if not self.data_points:
            logger.warning("No data points available")
            return PressureCurve()

        # 按时间排序
        sorted_points = sorted(self.data_points, key=lambda x: x.timestamp)

        # 计算平均压力
        stress_scores = [point.stress_score for point in sorted_points]
        average_stress = statistics.mean(stress_scores)

        # 找到峰值
        peak_stress = max(stress_scores)

        # 分析趋势
        trend = self._analyze_trend(stress_scores)

        # 生成预测
        predictions = self._predict_future(stress_scores)

        logger.info(
            f"Generated pressure curve: avg={average_stress:.2f}, "
            f"peak={peak_stress:.2f}, trend={trend}"
        )

        return PressureCurve(
            data_points=sorted_points,
            average_stress=average_stress,
            peak_stress=peak_stress,
            trend=trend,
            predictions=predictions,
        )

    def _analyze_trend(self, scores: List[float]) -> str:
        """分析压力趋势。

        Args:
            scores: 压力分数列表

        Returns:
            趋势（rising/falling/stable）
        """
        if len(scores) < 2:
            return "stable"

        # 计算最近一半数据的平均
        mid = len(scores) // 2
        early_avg = statistics.mean(scores[:mid]) if mid > 0 else scores[0]
        late_avg = statistics.mean(scores[mid:]) if mid < len(scores) else scores[-1]

        diff = late_avg - early_avg

        if diff > 0.1:
            return "rising"
        elif diff < -0.1:
            return "falling"
        else:
            return "stable"

    def _predict_future(self, scores: List[float]) -> List[float]:
        """预测未来压力。

        Args:
            scores: 历史压力分数

        Returns:
            未来预测值（3个数据点）
        """
        if len(scores) < 3:
            return [scores[-1]] * 3 if scores else [0.3] * 3

        # 简单移动平均预测
        window = min(5, len(scores))
        recent_avg = statistics.mean(scores[-window:])

        # 根据趋势调整
        trend_factor = 0.0
        if len(scores) >= window * 2:  # 确保有足够的数据点
            earlier_scores = scores[-(window * 2):-window]
            if earlier_scores:  # 额外检查确保列表不为空
                earlier_avg = statistics.mean(earlier_scores)
                trend_factor = (recent_avg - earlier_avg) * 0.3

        predictions = []
        for i in range(3):
            predicted = recent_avg + trend_factor * (i + 1)
            predicted = max(0.0, min(1.0, predicted))  # 限制在 [0, 1]
            predictions.append(predicted)

        return predictions

    def get_peaks_and_valleys(self, curve: PressureCurve) -> Dict[str, List[StressDataPoint]]:
        """获取峰值和低谷。

        Args:
            curve: 压力曲线

        Returns:
            包含峰值和低谷的字典
        """
        if len(curve.data_points) < 3:
            return {"peaks": [], "valleys": []}

        scores = [point.stress_score for point in curve.data_points]
        peaks = []
        valleys = []

        for i in range(1, len(scores) - 1):
            if scores[i] > scores[i - 1] and scores[i] > scores[i + 1]:
                # 局部峰值
                if scores[i] > curve.average_stress:
                    peaks.append(curve.data_points[i])
            elif scores[i] < scores[i - 1] and scores[i] < scores[i + 1]:
                # 局部低谷
                if scores[i] < curve.average_stress:
                    valleys.append(curve.data_points[i])

        return {"peaks": peaks, "valleys": valleys}

    def get_summary(self, curve: PressureCurve) -> Dict[str, Any]:
        """获取曲线摘要。

        Args:
            curve: 压力曲线

        Returns:
            摘要信息
        """
        peaks_and_valleys = self.get_peaks_and_valleys(curve)

        return {
            "total_data_points": len(curve.data_points),
            "average_stress": curve.average_stress,
            "peak_stress": curve.peak_stress,
            "trend": curve.trend,
            "peaks_count": len(peaks_and_valleys["peaks"]),
            "valleys_count": len(peaks_and_valleys["valleys"]),
            "predictions": curve.predictions,
            "status": self._get_status(curve),
        }

    def _get_status(self, curve: PressureCurve) -> str:
        """获取曲线状态。

        Args:
            curve: 压力曲线

        Returns:
            状态描述
        """
        if curve.average_stress >= 0.8:
            return "高压力状态，需要关注"
        elif curve.average_stress >= 0.6:
            return "中等压力，建议调整"
        elif curve.trend == "rising":
            return "压力上升趋势，注意调节"
        elif curve.trend == "falling":
            return "压力下降趋势，状态良好"
        else:
            return "压力稳定，保持现状"


class ResilienceAdvisor:
    """韧性建议系统。

    基于情绪和压力等级生成个性化建议。

    Attributes:
        suggestion_library: 建议库

    Examples:
        >>> advisor = ResilienceAdvisor()
        >>> suggestions = advisor.get_suggestions("high", "工作")
        >>> print(suggestions)
    """

    # 建议库
    SUGGESTION_LIBRARY = {
        "relaxation": {
            "title": "放松技巧",
            "suggestions": [
                "尝试深呼吸练习：吸气4秒，屏息4秒，呼气6秒",
                "进行5-10分钟的正念冥想",
                "听舒缓的音乐，放松身心",
                "做简单的伸展运动，缓解肌肉紧张",
                "离开工作环境，到户外散步10分钟",
            ],
        },
        "exercise": {
            "title": "运动建议",
            "suggestions": [
                "进行30分钟的有氧运动（慢跑、快走、游泳）",
                "尝试瑜伽或普拉提，提高身体柔韧性",
                "做一些简单的办公室拉伸运动",
                "下班后散步20-30分钟",
                "尝试高强度间歇训练（HIIT），释放压力",
            ],
        },
        "social": {
            "title": "社交支持",
            "suggestions": [
                "与信任的朋友或家人交流你的感受",
                "参加兴趣小组或社区活动",
                "寻求专业的心理咨询师帮助",
                "与同事分享工作经验，获得支持",
                "避免孤立自己，保持社交联系",
            ],
        },
        "learning": {
            "title": "学习成长",
            "suggestions": [
                "学习新的技能或知识，提升自信心",
                "阅读正面心理学或自助类书籍",
                "参加时间管理或压力管理培训",
                "学习设定合理的目标和期望",
                "培养新的兴趣爱好，转移注意力",
            ],
        },
        "work": {
            "title": "工作调整",
            "suggestions": [
                "使用番茄工作法，提高专注力",
                "学会优先级管理，先完成重要任务",
                "合理安排休息时间，避免过度工作",
                "与上级沟通，调整不合理的工作安排",
                '学会说"不"，避免承担过多责任',
            ],
        },
        "sleep": {
            "title": "睡眠改善",
            "suggestions": [
                "建立规律的睡眠时间表",
                "睡前1小时避免使用电子设备",
                "保持卧室安静、黑暗、凉爽",
                "避免睡前摄入咖啡因和大量食物",
                "尝试放松技巧，如温水澡或阅读",
            ],
        },
    }

    def __init__(self) -> None:
        """初始化韧性建议系统。"""
        logger.info("Resilience advisor initialized")

    def get_suggestions(
        self,
        stress_level: str,
        dimension: str,
        emotion_type: str,
    ) -> List[Dict[str, str]]:
        """获取个性化建议。

        Args:
            stress_level: 压力等级
            dimension: 情绪维度
            emotion_type: 情绪类型

        Returns:
            建议列表

        Examples:
            >>> suggestions = advisor.get_suggestions("high", "工作", "anxiety")
            >>> print(len(suggestions))  # 3-5 个建议
        """
        suggestions = []

        # 根据压力等级选择建议类别
        if stress_level == "high":
            categories = ["relaxation", "exercise", "social", "work"]
        elif stress_level == "medium":
            categories = ["work", "learning", "exercise"]
        else:
            categories = ["learning", "social"]

        # 根据维度调整
        if dimension == "工作" and stress_level in ["high", "medium"]:
            categories.insert(0, "work")
        elif dimension == "健康" and stress_level == "high":
            categories.insert(0, "sleep")
            categories.insert(1, "exercise")

        # 根据情绪类型调整
        if emotion_type in ["fatigue", "exhausted"]:
            categories.insert(0, "sleep")
        elif emotion_type in ["anxiety", "stress"]:
            categories.insert(0, "relaxation")

        # 从建议库中提取建议
        for category in categories[:3]:  # 限制为3个类别
            if category in self.SUGGESTION_LIBRARY:
                library = self.SUGGESTION_LIBRARY[category]
                # 从每个类别中选择2-3个建议
                category_suggestions = library["suggestions"][:3]
                for suggestion in category_suggestions:
                    suggestions.append({
                        "category": library["title"],
                        "suggestion": suggestion,
                    })

        logger.debug(f"Generated {len(suggestions)} suggestions")
        return suggestions

    def get_action_plan(
        self,
        stress_level: str,
        dimension: str,
        emotion_type: str,
    ) -> Dict[str, Any]:
        """获取行动计划。

        Args:
            stress_level: 压力等级
            dimension: 情绪维度
            emotion_type: 情绪类型

        Returns:
            行动计划
        """
        suggestions = self.get_suggestions(stress_level, dimension, emotion_type)

        # 生成优先级行动计划
        immediate_actions = []
        short_term_actions = []
        long_term_actions = []

        for i, suggestion in enumerate(suggestions):
            if i < 2:
                immediate_actions.append(suggestion)
            elif i < 4:
                short_term_actions.append(suggestion)
            else:
                long_term_actions.append(suggestion)

        return {
            "immediate": immediate_actions,  # 立即行动
            "short_term": short_term_actions,  # 短期（1-2天）
            "long_term": long_term_actions,  # 长期（1周+）
            "total_count": len(suggestions),
        }


class ResilienceScorer:
    """韧性评分系统。

    基于历史数据计算韧性评分。

    Attributes:
        curve_generator: 压力曲线生成器
        advisor: 韧性建议系统

    Examples:
        >>> scorer = ResilienceScorer()
        >>> score = scorer.calculate_score(events)
        >>> print(score.overall_score)  # 0-100
    """

    def __init__(self) -> None:
        """初始化韧性评分系统。"""
        self.curve_generator = PressureCurveGenerator()
        self.advisor = ResilienceAdvisor()
        logger.info("Resilience scorer initialized")

    def calculate_score(
        self,
        events: List[Dict[str, Any]],
    ) -> ResilienceScore:
        """计算韧性评分。

        Args:
            events: 事件列表

        Returns:
            韧性评分对象
        """
        # 生成压力曲线
        curve = self.curve_generator.generate_from_events(events)

        # 计算总分
        overall_score = self._calculate_overall_score(curve)

        # 确定韧性等级
        level = self._determine_level(overall_score)

        # 计算维度分数
        dimension_scores = self._calculate_dimension_scores(events)

        # 生成建议
        suggestions = self._generate_suggestions(overall_score, level, curve)

        logger.info(
            f"Calculated resilience score: {overall_score:.1f}, level={level.value}"
        )

        return ResilienceScore(
            overall_score=overall_score,
            level=level,
            dimension_scores=dimension_scores,
            suggestions=suggestions,
            timestamp=datetime.now(),
        )

    def _calculate_overall_score(self, curve: PressureCurve) -> float:
        """计算总体评分。

        Args:
            curve: 压力曲线

        Returns:
            总体评分（0-100）
        """
        # 基础分：100 - 平均压力分数 * 100
        base_score = 100 - curve.average_stress * 100

        # 趋势调整
        trend_bonus = 0.0
        if curve.trend == "falling":
            trend_bonus = 10.0  # 压力下降加分
        elif curve.trend == "rising":
            trend_bonus = -10.0  # 压力上升减分

        # 峰值惩罚
        peak_penalty = 0.0
        if curve.peak_stress > 0.8:
            peak_penalty = -15.0

        # 数据点数量奖励（数据越多越可信）
        data_bonus = min(len(curve.data_points) * 0.5, 10.0)

        score = base_score + trend_bonus + peak_penalty + data_bonus
        return max(0.0, min(100.0, score))  # 限制在 [0, 100]

    def _determine_level(self, score: float) -> ResilienceLevel:
        """确定韧性等级。

        Args:
            score: 总体评分

        Returns:
            韧性等级
        """
        if score >= 85:
            return ResilienceLevel.EXCELLENT
        elif score >= 70:
            return ResilienceLevel.GOOD
        elif score >= 50:
            return ResilienceLevel.NORMAL
        elif score >= 30:
            return ResilienceLevel.WARNING
        else:
            return ResilienceLevel.CRITICAL

    def _calculate_dimension_scores(self, events: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算维度分数。

        Args:
            events: 事件列表

        Returns:
            维度分数字典
        """
        dimension_data = defaultdict(list)

        # 按维度分组
        for event in events:
            dimension = event.get("dimension", "其他")
            stress_score = event.get("stress_score", 0.5)
            dimension_data[dimension].append(stress_score)

        # 计算每个维度的分数
        dimension_scores = {}
        for dimension, scores in dimension_data.items():
            if scores:
                avg_stress = statistics.mean(scores)
                # 转换为韧性分数（压力越小分数越高）
                resilience_score = (1 - avg_stress) * 100
                dimension_scores[dimension] = resilience_score

        return dimension_scores

    def _generate_suggestions(
        self,
        score: float,
        level: ResilienceLevel,
        curve: PressureCurve,
    ) -> List[str]:
        """生成改进建议。

        Args:
            score: 总体评分
            level: 韧性等级
            curve: 压力曲线

        Returns:
            建议列表
        """
        suggestions = []

        if level == ResilienceLevel.CRITICAL:
            suggestions = [
                "🚨 韧性状态危险，建议立即寻求专业帮助",
                "考虑请假休息，调整工作和生活节奏",
                "与信任的人交流，不要独自承受",
            ]
        elif level == ResilienceLevel.WARNING:
            suggestions = [
                "⚠️ 韧性状态需要关注，建议采取行动",
                "识别压力来源，制定应对计划",
                "增加休息和放松时间",
            ]
        elif level == ResilienceLevel.NORMAL:
            suggestions = [
                "📍 韧性状态正常，继续保持",
                "关注压力趋势，提前预防",
                "培养更多应对压力的技巧",
            ]
        elif level == ResilienceLevel.GOOD:
            suggestions = [
                "✅ 韧性状态良好，继续保持",
                "可以尝试挑战更多目标",
                "帮助他人建立韧性",
            ]
        else:  # EXCELLENT
            suggestions = [
                "🌟 韧性状态优秀，非常出色",
                "保持现有习惯，持续优化",
                "分享你的经验给他人",
            ]

        # 根据趋势添加建议
        if curve.trend == "rising":
            suggestions.append("⚠️ 压力呈上升趋势，需要警惕")
        elif curve.trend == "falling":
            suggestions.append("✅ 压力呈下降趋势，状态改善")

        return suggestions


# 便捷函数
def generate_pressure_curve(events: List[Dict[str, Any]]) -> PressureCurve:
    """生成压力曲线（便捷函数）。

    Args:
        events: 事件列表

    Returns:
        压力曲线
    """
    generator = PressureCurveGenerator()
    return generator.generate_from_events(events)


def calculate_resilience_score(events: List[Dict[str, Any]]) -> ResilienceScore:
    """计算韧性评分（便捷函数）。

    Args:
        events: 事件列表

    Returns:
        韧性评分
    """
    scorer = ResilienceScorer()
    return scorer.calculate_score(events)


def get_resilience_suggestions(
    stress_level: str,
    dimension: str,
    emotion_type: str,
) -> List[Dict[str, str]]:
    """获取韧性建议（便捷函数）。

    Args:
        stress_level: 压力等级
        dimension: 情绪维度
        emotion_type: 情绪类型

    Returns:
        建议列表
    """
    advisor = ResilienceAdvisor()
    return advisor.get_suggestions(stress_level, dimension, emotion_type)
