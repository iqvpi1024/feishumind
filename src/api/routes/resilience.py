"""韧性辅导 API 路由。

提供情绪分析、韧性评分、压力曲线等 API 端点。

Author: Claude Code
Date: 2026-02-06
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.utils.logger import get_logger
from src.utils.sentiment import (
    EmotionAnalyzer,
    EventSentimentAnalyzer,
    EmotionAnalysisResult,
)
from src.utils.resilience import (
    PressureCurveGenerator,
    ResilienceScorer,
    ResilienceAdvisor,
    PressureCurve,
    ResilienceScore,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/resilience",
    tags=["resilience"],
)

# ============ 请求/响应模型 ============


class AnalyzeEmotionRequest(BaseModel):
    """情绪分析请求。

    Attributes:
        text: 输入文本
    """

    text: str = Field(..., description="输入文本", min_length=1, max_length=5000)


class AnalyzeEmotionResponse(BaseModel):
    """情绪分析响应。

    Attributes:
        emotion_type: 情绪类型
        intensity: 情绪强度（0-1）
        confidence: 置信度（0-1）
        dimension: 情绪维度
        timestamp: 分析时间
    """

    emotion_type: str = Field(..., description="情绪类型")
    intensity: float = Field(..., description="情绪强度（0-1）", ge=0.0, le=1.0)
    confidence: float = Field(..., description="置信度（0-1）", ge=0.0, le=1.0)
    dimension: str = Field(..., description="情绪维度")
    timestamp: str = Field(..., description="分析时间")


class AnalyzeEventRequest(BaseModel):
    """事件情绪分析请求。

    Attributes:
        event_text: 事件文本
    """

    event_text: str = Field(..., description="事件文本", min_length=1, max_length=5000)


class AnalyzeEventResponse(BaseModel):
    """事件情绪分析响应。

    Attributes:
        stress_level: 压力等级
        emoji: 表情符号
        stress_score: 压力分数（0-1）
        matched_keywords: 匹配的关键词
        factors: 压力因素
        suggestions: 建议
    """

    stress_level: str = Field(..., description="压力等级")
    emoji: str = Field(..., description="表情符号")
    stress_score: float = Field(..., description="压力分数（0-1）", ge=0.0, le=1.0)
    matched_keywords: List[str] = Field(..., description="匹配的关键词")
    factors: List[str] = Field(..., description="压力因素")
    suggestions: List[str] = Field(..., description="建议")


class EventData(BaseModel):
    """事件数据。

    Attributes:
        description: 事件描述
        timestamp: 时间戳（可选）
        stress_level: 压力等级（可选）
        stress_score: 压力分数（可选）
        dimension: 维度（可选）
    """

    description: str = Field(..., description="事件描述")
    timestamp: Optional[str] = Field(None, description="时间戳")
    stress_level: Optional[str] = Field(None, description="压力等级")
    stress_score: Optional[float] = Field(None, description="压力分数", ge=0.0, le=1.0)
    dimension: Optional[str] = Field(None, description="情绪维度")


class GenerateCurveRequest(BaseModel):
    """生成压力曲线请求。

    Attributes:
        events: 事件列表
    """

    events: List[EventData] = Field(..., description="事件列表")


class CurveDataPoint(BaseModel):
    """曲线数据点。

    Attributes:
        timestamp: 时间戳
        stress_level: 压力等级
        stress_score: 压力分数
        emotion_type: 情绪类型
        dimension: 维度
    """

    timestamp: str = Field(..., description="时间戳")
    stress_level: str = Field(..., description="压力等级")
    stress_score: float = Field(..., description="压力分数")
    emotion_type: str = Field(..., description="情绪类型")
    dimension: str = Field(..., description="维度")


class PressureCurveResponse(BaseModel):
    """压力曲线响应。

    Attributes:
        data_points: 数据点列表
        average_stress: 平均压力分数
        peak_stress: 峰值压力
        trend: 趋势
        predictions: 未来预测
        summary: 摘要信息
    """

    data_points: List[CurveDataPoint] = Field(..., description="数据点列表")
    average_stress: float = Field(..., description="平均压力分数")
    peak_stress: float = Field(..., description="峰值压力")
    trend: str = Field(..., description="趋势")
    predictions: List[float] = Field(..., description="未来预测")
    summary: Dict[str, Any] = Field(..., description="摘要信息")


class ResilienceScoreResponse(BaseModel):
    """韧性评分响应。

    Attributes:
        overall_score: 总体评分（0-100）
        level: 韧性等级
        dimension_scores: 维度评分
        suggestions: 改进建议
        timestamp: 评分时间
    """

    overall_score: float = Field(..., description="总体评分（0-100）", ge=0.0, le=100.0)
    level: str = Field(..., description="韧性等级")
    dimension_scores: Dict[str, float] = Field(..., description="维度评分")
    suggestions: List[str] = Field(..., description="改进建议")
    timestamp: str = Field(..., description="评分时间")


class GetSuggestionsRequest(BaseModel):
    """获取建议请求。

    Attributes:
        stress_level: 压力等级
        dimension: 情绪维度
        emotion_type: 情绪类型
    """

    stress_level: str = Field(..., description="压力等级")
    dimension: str = Field(..., description="情绪维度")
    emotion_type: str = Field(..., description="情绪类型")


class SuggestionItem(BaseModel):
    """建议项。

    Attributes:
        category: 类别
        suggestion: 建议
    """

    category: str = Field(..., description="类别")
    suggestion: str = Field(..., description="建议")


class GetSuggestionsResponse(BaseModel):
    """获取建议响应。

    Attributes:
        suggestions: 建议列表
    """

    suggestions: List[SuggestionItem] = Field(..., description="建议列表")


class ActionPlanResponse(BaseModel):
    """行动计划响应。

    Attributes:
        immediate: 立即行动
        short_term: 短期行动
        long_term: 长期行动
        total_count: 总数量
    """

    immediate: List[SuggestionItem] = Field(..., description="立即行动")
    short_term: List[SuggestionItem] = Field(..., description="短期行动")
    long_term: List[SuggestionItem] = Field(..., description="长期行动")
    total_count: int = Field(..., description="总数量")


# ============ API 端点 ============


@router.post(
    "/analyze",
    response_model=AnalyzeEmotionResponse,
    summary="分析情绪",
    description="分析输入文本的情绪类型、强度和维度",
)
async def analyze_emotion(request: AnalyzeEmotionRequest) -> AnalyzeEmotionResponse:
    """分析情绪。

    Args:
        request: 情绪分析请求

    Returns:
        情绪分析结果

    Raises:
        HTTPException: 分析失败时抛出
    """
    try:
        logger.info(f"Analyzing emotion for text: {request.text[:100]}...")

        analyzer = EmotionAnalyzer()
        result: EmotionAnalysisResult = analyzer.analyze(request.text)

        return AnalyzeEmotionResponse(
            emotion_type=result.emotion_type.value,
            intensity=result.intensity,
            confidence=result.confidence,
            dimension=result.dimension,
            timestamp=result.timestamp.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to analyze emotion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"情绪分析失败: {str(e)}",
        )


@router.post(
    "/analyze-event",
    response_model=AnalyzeEventResponse,
    summary="分析事件情绪",
    description="分析事件的压力等级、压力因素和建议",
)
async def analyze_event(request: AnalyzeEventRequest) -> AnalyzeEventResponse:
    """分析事件情绪。

    Args:
        request: 事件情绪分析请求

    Returns:
        事件情绪分析结果

    Raises:
        HTTPException: 分析失败时抛出
    """
    try:
        logger.info(f"Analyzing event: {request.event_text[:100]}...")

        analyzer = EventSentimentAnalyzer()
        result = analyzer.analyze(request.event_text)

        return AnalyzeEventResponse(
            stress_level=result["stress_level"],
            emoji=result["emoji"],
            stress_score=result["stress_score"],
            matched_keywords=result["matched_keywords"],
            factors=result["factors"],
            suggestions=result["suggestions"],
        )

    except Exception as e:
        logger.error(f"Failed to analyze event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"事件分析失败: {str(e)}",
        )


@router.post(
    "/curve/generate",
    response_model=PressureCurveResponse,
    summary="生成压力曲线",
    description="基于事件列表生成压力曲线",
)
async def generate_pressure_curve(request: GenerateCurveRequest) -> PressureCurveResponse:
    """生成压力曲线。

    Args:
        request: 生成压力曲线请求

    Returns:
        压力曲线

    Raises:
        HTTPException: 生成失败时抛出
    """
    try:
        logger.info(f"Generating pressure curve from {len(request.events)} events")

        # 转换事件数据
        events = []
        for event in request.events:
            event_dict = {
                "description": event.description,
                "stress_level": event.stress_level,
                "stress_score": event.stress_score,
                "dimension": event.dimension,
            }

            if event.timestamp:
                event_dict["timestamp"] = datetime.fromisoformat(event.timestamp)

            events.append(event_dict)

        # 如果没有提供压力等级，自动分析
        if not any(e.get("stress_level") for e in events):
            event_analyzer = EventSentimentAnalyzer()
            for event in events:
                if not event.get("stress_level"):
                    result = event_analyzer.analyze(event["description"])
                    event["stress_level"] = result["stress_level"]
                    event["stress_score"] = result["stress_score"]
                    event["dimension"] = result.get("dimension", "其他")

        # 生成压力曲线
        generator = PressureCurveGenerator()
        curve: PressureCurve = generator.generate_from_events(events)

        # 生成摘要
        summary = generator.get_summary(curve)

        # 转换数据点
        data_points = []
        for point in curve.data_points:
            data_points.append(
                CurveDataPoint(
                    timestamp=point.timestamp.isoformat(),
                    stress_level=point.stress_level.value,
                    stress_score=point.stress_score,
                    emotion_type=point.emotion_type.value,
                    dimension=point.dimension,
                )
            )

        return PressureCurveResponse(
            data_points=data_points,
            average_stress=curve.average_stress,
            peak_stress=curve.peak_stress,
            trend=curve.trend,
            predictions=curve.predictions,
            summary=summary,
        )

    except Exception as e:
        logger.error(f"Failed to generate pressure curve: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"压力曲线生成失败: {str(e)}",
        )


@router.post(
    "/score/calculate",
    response_model=ResilienceScoreResponse,
    summary="计算韧性评分",
    description="基于事件列表计算韧性评分",
)
async def calculate_resilience_score(request: GenerateCurveRequest) -> ResilienceScoreResponse:
    """计算韧性评分。

    Args:
        request: 事件列表

    Returns:
        韧性评分

    Raises:
        HTTPException: 计算失败时抛出
    """
    try:
        logger.info(f"Calculating resilience score from {len(request.events)} events")

        # 转换事件数据
        events = []
        for event in request.events:
            event_dict = {
                "description": event.description,
                "stress_level": event.stress_level,
                "stress_score": event.stress_score,
                "dimension": event.dimension,
            }

            if event.timestamp:
                event_dict["timestamp"] = datetime.fromisoformat(event.timestamp)

            events.append(event_dict)

        # 如果没有提供压力等级，自动分析
        if not any(e.get("stress_level") for e in events):
            event_analyzer = EventSentimentAnalyzer()
            for event in events:
                if not event.get("stress_level"):
                    result = event_analyzer.analyze(event["description"])
                    event["stress_level"] = result["stress_level"]
                    event["stress_score"] = result["stress_score"]
                    event["dimension"] = result.get("dimension", "其他")

        # 计算韧性评分
        scorer = ResilienceScorer()
        score: ResilienceScore = scorer.calculate_score(events)

        return ResilienceScoreResponse(
            overall_score=score.overall_score,
            level=score.level.value,
            dimension_scores=score.dimension_scores,
            suggestions=score.suggestions,
            timestamp=score.timestamp.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to calculate resilience score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"韧性评分计算失败: {str(e)}",
        )


@router.post(
    "/suggestions",
    response_model=GetSuggestionsResponse,
    summary="获取韧性建议",
    description="根据压力等级、维度和情绪类型获取个性化建议",
)
async def get_suggestions(request: GetSuggestionsRequest) -> GetSuggestionsResponse:
    """获取韧性建议。

    Args:
        request: 获取建议请求

    Returns:
        建议列表

    Raises:
        HTTPException: 获取失败时抛出
    """
    try:
        logger.info(
            f"Getting suggestions: stress_level={request.stress_level}, "
            f"dimension={request.dimension}, emotion_type={request.emotion_type}"
        )

        advisor = ResilienceAdvisor()
        suggestions = advisor.get_suggestions(
            stress_level=request.stress_level,
            dimension=request.dimension,
            emotion_type=request.emotion_type,
        )

        return GetSuggestionsResponse(
            suggestions=[
                SuggestionItem(
                    category=s["category"],
                    suggestion=s["suggestion"],
                )
                for s in suggestions
            ]
        )

    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取建议失败: {str(e)}",
        )


@router.post(
    "/action-plan",
    response_model=ActionPlanResponse,
    summary="获取行动计划",
    description="根据压力等级、维度和情绪类型获取行动计划",
)
async def get_action_plan(request: GetSuggestionsRequest) -> ActionPlanResponse:
    """获取行动计划。

    Args:
        request: 获取行动计划请求

    Returns:
        行动计划

    Raises:
        HTTPException: 获取失败时抛出
    """
    try:
        logger.info(
            f"Getting action plan: stress_level={request.stress_level}, "
            f"dimension={request.dimension}, emotion_type={request.emotion_type}"
        )

        advisor = ResilienceAdvisor()
        plan = advisor.get_action_plan(
            stress_level=request.stress_level,
            dimension=request.dimension,
            emotion_type=request.emotion_type,
        )

        def to_suggestion_items(items: List[Dict[str, str]]) -> List[SuggestionItem]:
            return [
                SuggestionItem(
                    category=item["category"],
                    suggestion=item["suggestion"],
                )
                for item in items
            ]

        return ActionPlanResponse(
            immediate=to_suggestion_items(plan["immediate"]),
            short_term=to_suggestion_items(plan["short_term"]),
            long_term=to_suggestion_items(plan["long_term"]),
            total_count=plan["total_count"],
        )

    except Exception as e:
        logger.error(f"Failed to get action plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取行动计划失败: {str(e)}",
        )


@router.get(
    "/health",
    summary="健康检查",
    description="检查韧性辅导模块的健康状态",
)
async def health_check() -> Dict[str, str]:
    """健康检查。

    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "service": "FeishuMind Resilience Service",
        "version": "1.0.0",
    }
