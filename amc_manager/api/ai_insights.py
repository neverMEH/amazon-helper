"""AI Insights API Router"""

import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import logging

from amc_manager.schemas.ai_schemas import (
    AnalyzeDataRequest,
    AnalyzeDataResponse,
    RecommendChartsRequest,
    RecommendChartsResponse,
    GenerateInsightsRequest,
    GenerateInsightsResponse,
    DataInsightResponse,
    ChartRecommendationResponse,
    ChartConfigResponse,
    StatisticalSummaryResponse,
    RateLimitResponse,
    ErrorResponse
)
from amc_manager.services.data_analysis_ai import (
    DataAnalysisAI,
    DataAnalysisRequest as ServiceAnalysisRequest,
    DataAnalysisError
)
from amc_manager.services.chart_recommendations_ai import (
    chart_recommendations_ai,
    ChartRecommendationError
)
from amc_manager.api.dependencies import get_current_user
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI Insights"])

# Rate limiting state (in-memory, per-user)
rate_limit_state = {}
RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW_SECONDS = 60


def check_rate_limit(user_id: str) -> bool:
    """
    Check if user is within rate limit
    Returns True if allowed, raises HTTPException if rate limited
    """
    now = datetime.now()

    # Initialize user state if not exists
    if user_id not in rate_limit_state:
        rate_limit_state[user_id] = {
            "requests": [],
            "window_start": now
        }

    user_state = rate_limit_state[user_id]

    # Remove requests outside the window
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
    user_state["requests"] = [
        req_time for req_time in user_state["requests"]
        if req_time > window_start
    ]

    # Check if limit exceeded
    if len(user_state["requests"]) >= RATE_LIMIT_REQUESTS:
        # Calculate retry_after
        oldest_request = min(user_state["requests"])
        retry_after = int((oldest_request + timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS) - now).total_seconds())

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "detail": "Rate limit exceeded. Please try again later.",
                "retry_after": max(retry_after, 1),
                "limit": RATE_LIMIT_REQUESTS,
                "window": f"{RATE_LIMIT_WINDOW_SECONDS} seconds"
            }
        )

    # Add current request
    user_state["requests"].append(now)
    return True


@router.post(
    "/analyze-data",
    response_model=AnalyzeDataResponse,
    responses={
        200: {"description": "Data analysis completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"description": "Unauthorized"},
        429: {"model": RateLimitResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Analyze AMC Query Data",
    description="Analyze AMC query results to generate insights, detect trends, and identify anomalies"
)
async def analyze_data(
    request: AnalyzeDataRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AnalyzeDataResponse:
    """
    Analyze AMC query data and generate insights

    This endpoint performs comprehensive data analysis including:
    - Trend detection
    - Anomaly identification
    - Correlation analysis
    - Statistical summaries
    - Actionable recommendations
    """
    try:
        # Check rate limit
        user_id = current_user.get("id", "unknown")
        check_rate_limit(user_id)

        # Initialize service
        data_analysis_service = DataAnalysisAI()

        # Create service request
        service_request = ServiceAnalysisRequest(
            data=request.data,
            analysis_type=request.analysis_type,
            confidence_threshold=request.confidence_threshold,
            max_insights=request.max_insights,
            include_forecasting=request.include_forecasting
        )

        # Perform analysis
        logger.info(f"Analyzing data for user {user_id}, analysis_type={request.analysis_type}")
        analysis_result = await data_analysis_service.analyze(service_request)

        # Convert to response format
        insights_response = [
            DataInsightResponse(
                category=insight.category,
                title=insight.title,
                description=insight.description,
                confidence=insight.confidence,
                impact=insight.impact,
                recommendation=insight.recommendation,
                supporting_data=insight.supporting_data,
                timestamp=insight.timestamp
            )
            for insight in analysis_result.insights
        ]

        # Convert correlations tuple keys to string keys for JSON serialization
        correlations_dict = {
            f"{k[0]}__{k[1]}": v
            for k, v in analysis_result.statistical_summary.correlations.items()
        }

        statistical_summary = StatisticalSummaryResponse(
            metrics=analysis_result.statistical_summary.metrics,
            correlations=correlations_dict,
            outliers=analysis_result.statistical_summary.outliers,
            trends=analysis_result.statistical_summary.trends
        )

        response = AnalyzeDataResponse(
            insights=insights_response,
            statistical_summary=statistical_summary,
            recommendations=analysis_result.recommendations,
            metadata={
                **analysis_result.metadata,
                "user_id": user_id,
                "request_timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Data analysis completed successfully for user {user_id}, {len(insights_response)} insights generated")
        return response

    except DataAnalysisError as e:
        logger.error(f"Data analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during data analysis"
        )


@router.post(
    "/recommend-charts",
    response_model=RecommendChartsResponse,
    responses={
        200: {"description": "Chart recommendations generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"description": "Unauthorized"},
        429: {"model": RateLimitResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get Chart Recommendations",
    description="Recommend optimal chart types and configurations for AMC query results"
)
async def recommend_charts(
    request: RecommendChartsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> RecommendChartsResponse:
    """
    Generate chart type recommendations for data

    Analyzes data characteristics and recommends:
    - Optimal chart types (line, bar, pie, scatter, etc.)
    - Chart configurations (axes, colors, tooltips)
    - Visualization best practices
    - Optimization tips
    """
    try:
        # Check rate limit
        user_id = current_user.get("id", "unknown")
        check_rate_limit(user_id)

        # Get recommendations
        logger.info(f"Generating chart recommendations for user {user_id}")
        recommendations = await chart_recommendations_ai.recommend_charts(
            data=request.data,
            max_recommendations=request.max_recommendations,
            min_confidence=request.min_confidence
        )

        # Convert to response format
        recommendations_response = [
            ChartRecommendationResponse(
                chart_type=rec.chart_type,
                confidence_score=rec.confidence_score,
                reasoning=rec.reasoning,
                suggested_title=rec.suggested_title,
                config=ChartConfigResponse(
                    x_axis=rec.config.x_axis,
                    y_axis=rec.config.y_axis,
                    x_axis_label=rec.config.x_axis_label,
                    y_axis_label=rec.config.y_axis_label,
                    color_palette=rec.config.color_palette,
                    enable_tooltips=rec.config.enable_tooltips,
                    enable_zoom=rec.config.enable_zoom,
                    enable_legend=rec.config.enable_legend,
                    stacked=rec.config.stacked,
                    show_grid=rec.config.show_grid,
                    animation_enabled=rec.config.animation_enabled
                ),
                optimization_tips=rec.optimization_tips,
                warnings=rec.warnings,
                data_requirements=rec.data_requirements
            )
            for rec in recommendations
        ]

        response = RecommendChartsResponse(
            recommendations=recommendations_response,
            metadata={
                "total_recommendations": len(recommendations_response),
                "user_id": user_id,
                "request_timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Chart recommendations completed for user {user_id}, {len(recommendations_response)} recommendations generated")
        return response

    except ChartRecommendationError as e:
        logger.error(f"Chart recommendation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in recommend_charts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during chart recommendation"
        )


@router.post(
    "/generate-insights",
    response_model=GenerateInsightsResponse,
    responses={
        200: {"description": "Insights generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"description": "Unauthorized"},
        429: {"model": RateLimitResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Generate Comprehensive Insights",
    description="Generate both data analysis insights and chart recommendations in a single request"
)
async def generate_insights(
    request: GenerateInsightsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> GenerateInsightsResponse:
    """
    Generate comprehensive insights combining data analysis and chart recommendations

    This endpoint provides a complete AI-powered analysis including:
    - Data insights and trends
    - Chart recommendations
    - Statistical summaries
    - Actionable recommendations
    """
    try:
        # Check rate limit
        user_id = current_user.get("id", "unknown")
        check_rate_limit(user_id)

        logger.info(f"Generating comprehensive insights for user {user_id}")

        # Initialize response
        response_data = {}

        # Parallel execution of analysis and chart recommendations
        tasks = []

        if request.include_analysis:
            # Data analysis task
            data_analysis_service = DataAnalysisAI()
            service_request = ServiceAnalysisRequest(
                data=request.data,
                analysis_type="comprehensive",
                confidence_threshold=0.7,
                max_insights=request.max_insights
            )
            tasks.append(data_analysis_service.analyze(service_request))
        else:
            tasks.append(None)

        if request.include_charts:
            # Chart recommendations task
            tasks.append(chart_recommendations_ai.recommend_charts(
                data=request.data,
                max_recommendations=request.max_chart_recommendations,
                min_confidence=0.5
            ))
        else:
            tasks.append(None)

        # Execute tasks
        results = await asyncio.gather(*[t for t in tasks if t is not None], return_exceptions=True)

        # Process results
        analysis_result = None
        chart_recommendations = None

        if request.include_analysis and len(results) > 0 and not isinstance(results[0], Exception):
            analysis_result = results[0]

            # Convert to response format
            insights_response = [
                DataInsightResponse(
                    category=insight.category,
                    title=insight.title,
                    description=insight.description,
                    confidence=insight.confidence,
                    impact=insight.impact,
                    recommendation=insight.recommendation,
                    supporting_data=insight.supporting_data,
                    timestamp=insight.timestamp
                )
                for insight in analysis_result.insights
            ]

            correlations_dict = {
                f"{k[0]}__{k[1]}": v
                for k, v in analysis_result.statistical_summary.correlations.items()
            }

            statistical_summary = StatisticalSummaryResponse(
                metrics=analysis_result.statistical_summary.metrics,
                correlations=correlations_dict,
                outliers=analysis_result.statistical_summary.outliers,
                trends=analysis_result.statistical_summary.trends
            )

            response_data["data_analysis"] = AnalyzeDataResponse(
                insights=insights_response,
                statistical_summary=statistical_summary,
                recommendations=analysis_result.recommendations,
                metadata=analysis_result.metadata
            )

        if request.include_charts:
            chart_result_index = 1 if request.include_analysis else 0
            if len(results) > chart_result_index and not isinstance(results[chart_result_index], Exception):
                chart_recs = results[chart_result_index]

                chart_recommendations = [
                    ChartRecommendationResponse(
                        chart_type=rec.chart_type,
                        confidence_score=rec.confidence_score,
                        reasoning=rec.reasoning,
                        suggested_title=rec.suggested_title,
                        config=ChartConfigResponse(
                            x_axis=rec.config.x_axis,
                            y_axis=rec.config.y_axis,
                            x_axis_label=rec.config.x_axis_label,
                            y_axis_label=rec.config.y_axis_label,
                            color_palette=rec.config.color_palette,
                            enable_tooltips=rec.config.enable_tooltips,
                            enable_zoom=rec.config.enable_zoom,
                            enable_legend=rec.config.enable_legend,
                            stacked=rec.config.stacked,
                            show_grid=rec.config.show_grid,
                            animation_enabled=rec.config.animation_enabled
                        ),
                        optimization_tips=rec.optimization_tips,
                        warnings=rec.warnings,
                        data_requirements=rec.data_requirements
                    )
                    for rec in chart_recs
                ]

                response_data["chart_recommendations"] = chart_recommendations

        response = GenerateInsightsResponse(
            **response_data,
            metadata={
                "user_id": user_id,
                "request_timestamp": datetime.now().isoformat(),
                "included_analysis": request.include_analysis,
                "included_charts": request.include_charts
            }
        )

        logger.info(f"Comprehensive insights generated successfully for user {user_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during insights generation"
        )
