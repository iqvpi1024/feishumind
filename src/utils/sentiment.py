"""情绪检测和压力识别模块。

分析事件和文本中的压力等级，识别高压力事件。
支持关键词匹配、规则引擎、情绪分析。

Author: Claude Code
Date: 2026-02-06
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import re
from datetime import datetime
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmotionType(Enum):
    """情绪类型枚举。

    Attributes:
        JOY: 喜悦（😊）
        ANXIETY: 焦虑（😰）
        FATIGUE: 疲惫（😫）
        ANGER: 愤怒（😡）
        SADNESS: 悲伤（😢）
        CALM: 平静（😌）
        EXCITEMENT: 兴奋（🤩）
        STRESS: 压力（😣）
    """

    JOY = "joy"
    ANXIETY = "anxiety"
    FATIGUE = "fatigue"
    ANGER = "anger"
    SADNESS = "sadness"
    CALM = "calm"
    EXCITEMENT = "excitement"
    STRESS = "stress"


class StressLevel(Enum):
    """压力等级枚举。

    Attributes:
        LOW: 低压力（🟢）
        MEDIUM: 中压力（🟡）
        HIGH: 高压力（🔴）
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class EmotionAnalysisResult:
    """情绪分析结果。

    Attributes:
        emotion_type: 情绪类型
        intensity: 情绪强度（0-1）
        confidence: 置信度（0-1）
        dimension: 情绪维度（工作/健康/社交/学习）
        timestamp: 分析时间
    """

    emotion_type: EmotionType
    intensity: float
    confidence: float
    dimension: str
    timestamp: datetime


class EmotionAnalyzer:
    """精细情绪分析器。

    支持多种情绪类型的识别和强度评分。

    Attributes:
        emotion_keywords: 情绪关键词字典
        dimension_keywords: 维度关键词字典

    Examples:
        >>> analyzer = EmotionAnalyzer()
        >>> result = analyzer.analyze("今天工作很累，压力很大")
        >>> print(result.emotion_type)  # EmotionType.FATIGUE
    """

    # 情绪关键词映射
    EMOTION_KEYWORDS = {
        EmotionType.JOY: [
            "开心", "高兴", "快乐", "愉快", "欣喜", "满足",
            "不错", "很好", "太棒了", "顺利", "成功", "完成",
            "happy", "good", "great", "awesome", "joy"
        ],
        EmotionType.ANXIETY: [
            "焦虑", "担心", "紧张", "不安", "害怕", "恐慌",
            "忧虑", "忐忑", "着急", "担忧", "worry", "anxious",
            "nervous", "stress"
        ],
        EmotionType.FATIGUE: [
            "疲惫", "累", "疲劳", "困", "乏力", "精神不振",
            "精疲力尽", "累坏了", "tired", "exhausted", "fatigue"
        ],
        EmotionType.ANGER: [
            "生气", "愤怒", "恼火", "不爽", "烦躁", "气死",
            "愤怒", "angry", "mad", "annoyed", "frustrated"
        ],
        EmotionType.SADNESS: [
            "难过", "伤心", "失落", "沮丧", "郁闷", "失望",
            "sad", "upset", "disappointed", "depressed"
        ],
        EmotionType.CALM: [
            "平静", "放松", "轻松", "宁静", "安心", "舒适",
            "calm", "relaxed", "peaceful", "comfortable"
        ],
        EmotionType.EXCITEMENT: [
            "兴奋", "激动", "期待", "充满期待", "振奋", "热情",
            "excited", "thrilled", "looking forward"
        ],
        EmotionType.STRESS: [
            "压力", "压力大", "紧张", "压力山大", "喘不过气",
            "stress", "pressure", "overwhelmed"
        ],
    }

    # 情绪强度修饰词
    INTENSITY_MODIFIERS = {
        "非常": 1.5,
        "特别": 1.4,
        "超级": 1.6,
        "特别": 1.4,
        "极其": 1.8,
        "太": 1.5,
        "很": 1.3,
        "挺": 1.2,
        "有点": 0.7,
        "稍微": 0.6,
        "有点儿": 0.7,
        "一些": 0.6,
    }

    # 维度关键词
    DIMENSION_KEYWORDS = {
        "工作": ["工作", "项目", "任务", "会议", "报告", "汇报", "同事", "老板", "公司", "team", "project", "work"],
        "健康": ["身体", "健康", "生病", "感冒", "头痛", "睡眠", "休息", "锻炼", "health", "sick", "sleep"],
        "社交": ["朋友", "聚会", "约会", "家庭", "家人", "同事", "社交", "friend", "party", "family"],
        "学习": ["学习", "考试", "复习", "课程", "作业", "论文", "study", "exam", "course", "homework"],
    }

    def __init__(self) -> None:
        """初始化情绪分析器。"""
        # 编译正则表达式
        self._emotion_patterns = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            pattern = re.compile("|".join(keywords), re.IGNORECASE)
            self._emotion_patterns[emotion] = pattern

        self._intensity_pattern = re.compile(
            "|".join(self.INTENSITY_MODIFIERS.keys()), re.IGNORECASE
        )

        self._dimension_patterns = {}
        for dimension, keywords in self.DIMENSION_KEYWORDS.items():
            pattern = re.compile("|".join(keywords), re.IGNORECASE)
            self._dimension_patterns[dimension] = pattern

        logger.info("Emotion analyzer initialized")

    def analyze(self, text: str) -> EmotionAnalysisResult:
        """分析文本情绪。

        Args:
            text: 输入文本

        Returns:
            情绪分析结果

        Examples:
            >>> result = analyzer.analyze("今天工作很累，压力很大")
            >>> print(result.emotion_type, result.intensity)
        """
        if not text or not text.strip():
            return EmotionAnalysisResult(
                emotion_type=EmotionType.CALM,
                intensity=0.0,
                confidence=0.0,
                dimension="未知",
                timestamp=datetime.now()
            )

        # 1. 识别情绪类型
        emotion_type = self._detect_emotion(text)

        # 2. 计算情绪强度
        intensity = self._calculate_intensity(text, emotion_type)

        # 3. 计算置信度
        confidence = self._calculate_confidence(text, emotion_type)

        # 4. 识别情绪维度
        dimension = self._detect_dimension(text)

        logger.debug(
            f"Emotion analyzed: {emotion_type.value}, "
            f"intensity={intensity:.2f}, dimension={dimension}"
        )

        return EmotionAnalysisResult(
            emotion_type=emotion_type,
            intensity=intensity,
            confidence=confidence,
            dimension=dimension,
            timestamp=datetime.now()
        )

    def _detect_emotion(self, text: str) -> EmotionType:
        """检测情绪类型。

        Args:
            text: 输入文本

        Returns:
            情绪类型
        """
        emotion_scores = {}

        for emotion, pattern in self._emotion_patterns.items():
            matches = pattern.findall(text)
            if matches:
                emotion_scores[emotion] = len(matches)

        if not emotion_scores:
            return EmotionType.CALM

        # 返回匹配次数最多的情绪
        return max(emotion_scores, key=emotion_scores.get)

    def _calculate_intensity(self, text: str, emotion_type: EmotionType) -> float:
        """计算情绪强度。

        Args:
            text: 输入文本
            emotion_type: 情绪类型

        Returns:
            情绪强度（0-1）
        """
        base_intensity = 0.5

        # 检查强度修饰词
        modifier = self._intensity_pattern.search(text)
        if modifier:
            modifier_word = modifier.group()
            multiplier = self.INTENSITY_MODIFIERS.get(modifier_word, 1.0)
            base_intensity *= multiplier

        # 根据情绪类型调整基础强度
        if emotion_type in [EmotionType.STRESS, EmotionType.ANXIETY, EmotionType.ANGER]:
            base_intensity = min(base_intensity * 1.2, 1.0)
        elif emotion_type in [EmotionType.JOY, EmotionType.EXCITEMENT]:
            base_intensity = min(base_intensity * 1.1, 1.0)
        elif emotion_type == EmotionType.CALM:
            base_intensity = max(base_intensity * 0.5, 0.2)

        return min(base_intensity, 1.0)

    def _calculate_confidence(self, text: str, emotion_type: EmotionType) -> float:
        """计算置信度。

        Args:
            text: 输入文本
            emotion_type: 情绪类型

        Returns:
            置信度（0-1）
        """
        pattern = self._emotion_patterns.get(emotion_type)
        if not pattern:
            return 0.0

        matches = pattern.findall(text)
        if not matches:
            return 0.0

        # 匹配次数越多，置信度越高
        base_confidence = min(0.3 + len(matches) * 0.2, 1.0)

        # 如果有强度修饰词，提高置信度
        if self._intensity_pattern.search(text):
            base_confidence = min(base_confidence + 0.1, 1.0)

        return base_confidence

    def _detect_dimension(self, text: str) -> str:
        """检测情绪维度。

        Args:
            text: 输入文本

        Returns:
            情绪维度（工作/健康/社交/学习）
        """
        dimension_scores = {}

        for dimension, pattern in self._dimension_patterns.items():
            matches = pattern.findall(text)
            if matches:
                dimension_scores[dimension] = len(matches)

        if not dimension_scores:
            return "其他"

        # 返回匹配次数最多的维度
        return max(dimension_scores, key=dimension_scores.get)

    def batch_analyze(self, texts: List[str]) -> List[EmotionAnalysisResult]:
        """批量分析情绪。

        Args:
            texts: 文本列表

        Returns:
            情绪分析结果列表
        """
        return [self.analyze(text) for text in texts]


class StressEventClassifier:

    # 高压力关键词（重要且紧急）
    HIGH_STRESS_KEYWORDS = [
        "截止",
        "ddl",
        "DDL",
        "deadline",
        "deadline",
        "最后期限",
        "紧急",
        "urgent",
        "必须完成",
        "不能再拖",
        "生死攸关",
        "汇报",
        "演示",
        "演讲",
        "presentation",
        "答辩",
        "面试",
        "interview",
        "考试",
        "exam",
        "上线",
        "发布",
        "launch",
        "里程碑",
        "milestone",
    ]

    # 中压力关键词（有明确截止日期或重要性）
    MEDIUM_STRESS_KEYWORDS = [
        "会议",
        "开会",
        "meeting",
        "讨论",
        "review",
        "评审",
        "复盘",
        "周报",
        "月报",
        "总结",
        "计划",
        "目标",
        "任务",
        "安排",
        "预约",
        " deadline",
        "到期",
        "交付",
        "提交",
    ]

    # 时间压力关键词
    TIME_PRESSURE_KEYWORDS = [
        "今天",
        "明天",
        "本周",
        "下周",
        "尽快",
        "asap",
        "抓紧",
        "赶紧",
        "马上",
        "立即",
        "立即",
        "只有",
        "还剩",
        "还有",
    ]

    def __init__(self) -> None:
        """初始化压力事件分类器。"""
        # 编译正则表达式（提高性能）
        self._high_pattern = re.compile(
            "|".join(self.HIGH_STRESS_KEYWORDS), re.IGNORECASE
        )
        self._medium_pattern = re.compile(
            "|".join(self.MEDIUM_STRESS_KEYWORDS), re.IGNORECASE
        )
        self._time_pattern = re.compile(
            "|".join(self.TIME_PRESSURE_KEYWORDS), re.IGNORECASE
        )

        logger.info("Stress event classifier initialized")

    def classify(self, text: str) -> StressLevel:
        """分类事件压力等级。

        Args:
            text: 事件文本

        Returns:
            压力等级

        Examples:
            >>> level = classifier.classify("明天下午3点开会")
            >>> print(level.value)  # 'medium'
        """
        if not text or not text.strip():
            return StressLevel.LOW

        text = text.strip()
        logger.debug(f"Classifying stress level for: {text}")

        # 1. 检查高压力关键词
        if self._high_pattern.search(text):
            logger.debug("Detected HIGH stress level")
            return StressLevel.HIGH

        # 2. 检查中压力关键词
        if self._medium_pattern.search(text):
            # 如果是报告类任务（周报、月报、总结）且有时间压力，升级为高压力
            report_keywords = ["周报", "月报", "总结", "汇报", "汇报"]
            if any(kw in text for kw in report_keywords) and self._time_pattern.search(text):
                logger.debug("Detected HIGH stress level (report + time)")
                return StressLevel.HIGH

            logger.debug("Detected MEDIUM stress level")
            return StressLevel.MEDIUM

        # 3. 默认低压力
        logger.debug("Detected LOW stress level")
        return StressLevel.LOW

    def classify_with_details(
        self, text: str
    ) -> Dict[str, Any]:
        """分类事件压力等级并返回详细信息。

        Args:
            text: 事件文本

        Returns:
            包含压力等级和详细信息的字典

        Examples:
            >>> result = classifier.classify_with_details("明天要交周报")
            >>> print(result)
            {
                "level": "high",
                "matched_keywords": ["交", "周报", "明天"],
                "reason": "检测到时间压力关键词"
            }
        """
        level = self.classify(text)

        matched_keywords = []
        reason = ""

        # 提取匹配的关键词
        if self._high_pattern.search(text):
            matches = self._high_pattern.findall(text)
            matched_keywords.extend(matches)
            reason = "检测到高压力关键词"

        if self._medium_pattern.search(text):
            matches = self._medium_pattern.findall(text)
            matched_keywords.extend(matches)
            if not reason:
                reason = "检测到中压力关键词"

        if self._time_pattern.search(text):
            matches = self._time_pattern.findall(text)
            matched_keywords.extend(matches)
            if level == StressLevel.HIGH:
                reason = "检测到时间压力关键词"

        return {
            "level": level.value,
            "emoji": self._get_emoji(level),
            "matched_keywords": list(set(matched_keywords)),
            "reason": reason or "无明显压力特征",
        }

    def _get_emoji(self, level: StressLevel) -> str:
        """获取压力等级对应的表情符号。

        Args:
            level: 压力等级

        Returns:
            表情符号
        """
        emoji_map = {
            StressLevel.LOW: "🟢",
            StressLevel.MEDIUM: "🟡",
            StressLevel.HIGH: "🔴",
        }
        return emoji_map.get(level, "🟢")


class EventSentimentAnalyzer:
    """事件情绪分析器。

    分析事件中的情绪倾向和压力因素。

    Attributes:
        stress_classifier: 压力分类器实例

    Examples:
        >>> analyzer = EventSentimentAnalyzer()
        >>> result = analyzer.analyze("明天要交项目周报，压力很大")
        >>> print(result)
    """

    def __init__(self) -> None:
        """初始化情绪分析器。"""
        self.stress_classifier = StressEventClassifier()
        logger.info("Event sentiment analyzer initialized")

    def analyze(self, event_text: str) -> Dict[str, Any]:
        """分析事件情绪。

        Args:
            event_text: 事件文本

        Returns:
            情绪分析结果字典，包含：
            - stress_level: 压力等级
            - stress_score: 压力分数（0-1）
            - factors: 压力因素列表
            - suggestions: 建议措施

        Examples:
            >>> result = analyzer.analyze("明天下午3点开会讨论项目进度")
            >>> print(result["stress_level"])  # 'medium'
        """
        logger.info(f"Analyzing event sentiment: {event_text}")

        # 1. 压力等级分类
        stress_result = self.stress_classifier.classify_with_details(event_text)

        # 2. 计算压力分数
        stress_score = self._calculate_stress_score(stress_result["level"])

        # 3. 提取压力因素
        factors = self._extract_stress_factors(event_text, stress_result)

        # 4. 生成建议
        suggestions = self._generate_suggestions(stress_result["level"], factors)

        return {
            "stress_level": stress_result["level"],
            "emoji": stress_result["emoji"],
            "stress_score": stress_score,
            "matched_keywords": stress_result["matched_keywords"],
            "factors": factors,
            "suggestions": suggestions,
        }

    def _calculate_stress_score(self, level: str) -> float:
        """计算压力分数。

        Args:
            level: 压力等级

        Returns:
            压力分数（0-1）
        """
        score_map = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.9,
        }
        return score_map.get(level, 0.3)

    def _extract_stress_factors(
        self, text: str, stress_result: Dict[str, Any]
    ) -> List[str]:
        """提取压力因素。

        Args:
            text: 事件文本
            stress_result: 压力分类结果

        Returns:
            压力因素列表
        """
        factors = []

        # 根据关键词分类
        keywords = stress_result.get("matched_keywords", [])

        for keyword in keywords:
            if keyword in StressEventClassifier.HIGH_STRESS_KEYWORDS:
                factors.append(f"高重要性任务：{keyword}")
            elif keyword in StressEventClassifier.MEDIUM_STRESS_KEYWORDS:
                factors.append(f"计划性任务：{keyword}")
            elif keyword in StressEventClassifier.TIME_PRESSURE_KEYWORDS:
                factors.append(f"时间压力：{keyword}")

        return factors

    def _generate_suggestions(self, level: str, factors: List[str]) -> List[str]:
        """生成应对建议。

        Args:
            level: 压力等级
            factors: 压力因素

        Returns:
            建议列表
        """
        suggestions = []

        if level == "high":
            suggestions = [
                "建议提前准备，避免最后时刻压力",
                "可以拆解任务，分步骤完成",
                "必要时寻求团队协助",
                "确保充足的休息和睡眠",
            ]
        elif level == "medium":
            suggestions = [
                "合理安排时间，预留缓冲",
                "记录重要事项，避免遗漏",
                "保持专注，提高效率",
            ]
        else:
            suggestions = [
                "保持良好的工作节奏",
                "定期回顾和调整计划",
            ]

        return suggestions


# 便捷函数
def classify_stress_level(text: str) -> StressLevel:
    """分类压力等级（便捷函数）。

    Args:
        text: 事件文本

    Returns:
        压力等级
    """
    classifier = StressEventClassifier()
    return classifier.classify(text)


def analyze_event_sentiment(event_text: str) -> Dict[str, Any]:
    """分析事件情绪（便捷函数）。

    Args:
        event_text: 事件文本

    Returns:
        情绪分析结果
    """
    analyzer = EventSentimentAnalyzer()
    return analyzer.analyze(event_text)


def analyze_emotion(text: str) -> EmotionAnalysisResult:
    """分析情绪（便捷函数）。

    Args:
        text: 输入文本

    Returns:
        情绪分析结果
    """
    analyzer = EmotionAnalyzer()
    return analyzer.analyze(text)
