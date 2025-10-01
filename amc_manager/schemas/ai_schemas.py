"""Pydantic schemas for AI API endpoints"""

from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


class InsightCategoryEnum(str, Enum):
    """Categories for data insights"""
    TREND = "trend"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    PERFORMANCE = "performance"
    OPTIMIZATION = "optimization"
    PATTERN = "pattern"
    FORECAST = "forecast"


class ChartTypeEnum(str, Enum):
    """Supported chart types"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    TABLE = "table"
    METRIC_CARD = "metric_card"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"


# Request Schemas

class AnalyzeDataRequest(BaseModel):
    """Request schema for data analysis endpoint"""
    data: Dict[str, Any] = Field(..., description="AMC query results with columns and rows")
    analysis_type: str = Field(
        default="comprehensive",
        description="Type of analysis: comprehensive, trends_only, anomalies_only"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for insights"
    )
    max_insights: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of insights to return"
    )
    include_forecasting: bool = Field(
        default=False,
        description="Include forecasting in analysis"
    )

    @validator('data')
    def validate_data_structure(cls, v):
        """Validate data has required structure"""
        if not isinstance(v, dict):
            raise ValueError("Data must be a dictionary")
        if 'columns' not in v or 'rows' not in v:
            raise ValueError("Data must contain 'columns' and 'rows' keys")
        if not isinstance(v['columns'], list):
            raise ValueError("Columns must be a list")
        if not isinstance(v['rows'], list):
            raise ValueError("Rows must be a list")
        return v

    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "columns": ["date", "impressions", "clicks"],
                    "rows": [
                        ["2025-01-01", 1000, 50],
                        ["2025-01-02", 1200, 60]
                    ]
                },
                "analysis_type": "comprehensive",
                "confidence_threshold": 0.7,
                "max_insights": 10
            }
        }


class RecommendChartsRequest(BaseModel):
    """Request schema for chart recommendations endpoint"""
    data: Dict[str, Any] = Field(..., description="AMC query results with columns and rows")
    max_recommendations: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of chart recommendations"
    )
    min_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score for recommendations"
    )

    @validator('data')
    def validate_data_structure(cls, v):
        """Validate data has required structure"""
        if not isinstance(v, dict):
            raise ValueError("Data must be a dictionary")
        if 'columns' not in v or 'rows' not in v:
            raise ValueError("Data must contain 'columns' and 'rows' keys")
        if not isinstance(v['columns'], list):
            raise ValueError("Columns must be a list")
        if not isinstance(v['rows'], list):
            raise ValueError("Rows must be a list")
        return v

    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "columns": ["date", "metric"],
                    "rows": [["2025-01-01", 100]]
                },
                "max_recommendations": 5,
                "min_confidence": 0.5
            }
        }


class GenerateInsightsRequest(BaseModel):
    """Request schema for combined insights generation"""
    data: Dict[str, Any] = Field(..., description="AMC query results")
    include_charts: bool = Field(default=True, description="Include chart recommendations")
    include_analysis: bool = Field(default=True, description="Include data analysis")
    max_insights: int = Field(default=10, ge=1, le=50)
    max_chart_recommendations: int = Field(default=5, ge=1, le=10)

    @validator('data')
    def validate_data_structure(cls, v):
        """Validate data structure"""
        if not isinstance(v, dict):
            raise ValueError("Data must be a dictionary")
        if 'columns' not in v or 'rows' not in v:
            raise ValueError("Data must contain 'columns' and 'rows' keys")
        return v


# Response Schemas

class ChartConfigResponse(BaseModel):
    """Chart configuration response"""
    x_axis: Optional[str] = None
    y_axis: Optional[List[str]] = None
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    color_palette: List[str] = Field(default_factory=list)
    enable_tooltips: bool = True
    enable_zoom: bool = False
    enable_legend: bool = True
    stacked: bool = False
    show_grid: bool = True
    animation_enabled: bool = True


class ChartRecommendationResponse(BaseModel):
    """Chart recommendation response"""
    chart_type: ChartTypeEnum
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    suggested_title: str
    config: ChartConfigResponse
    optimization_tips: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    data_requirements: Optional[Dict[str, Any]] = None


class DataInsightResponse(BaseModel):
    """Data insight response"""
    category: InsightCategoryEnum
    title: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    impact: str = Field(description="Impact level: low, medium, high")
    recommendation: Optional[str] = None
    supporting_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator('impact')
    def validate_impact(cls, v):
        """Validate impact is one of the allowed values"""
        if v not in ['low', 'medium', 'high']:
            raise ValueError("Impact must be 'low', 'medium', or 'high'")
        return v


class StatisticalSummaryResponse(BaseModel):
    """Statistical summary response"""
    metrics: Dict[str, Dict[str, float]]
    correlations: Dict[str, float] = Field(
        default_factory=dict,
        description="Correlation pairs as 'col1_col2': correlation_value"
    )
    outliers: Dict[str, List[int]] = Field(default_factory=dict)
    trends: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class AnalyzeDataResponse(BaseModel):
    """Response schema for data analysis"""
    insights: List[DataInsightResponse]
    statistical_summary: StatisticalSummaryResponse
    recommendations: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "insights": [
                    {
                        "category": "trend",
                        "title": "Upward trend in clicks",
                        "description": "Clicks show a 20% increase",
                        "confidence": 0.85,
                        "impact": "high",
                        "recommendation": "Continue current strategy"
                    }
                ],
                "statistical_summary": {
                    "metrics": {
                        "clicks": {
                            "mean": 150.5,
                            "std": 25.3,
                            "min": 100,
                            "max": 200
                        }
                    },
                    "correlations": {},
                    "outliers": {},
                    "trends": {}
                },
                "recommendations": ["Continue current strategy"],
                "metadata": {"analysis_type": "comprehensive"}
            }
        }


class RecommendChartsResponse(BaseModel):
    """Response schema for chart recommendations"""
    recommendations: List[ChartRecommendationResponse]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "recommendations": [
                    {
                        "chart_type": "line",
                        "confidence_score": 0.9,
                        "reasoning": "Best for time series data",
                        "suggested_title": "Metrics Over Time",
                        "config": {
                            "x_axis": "date",
                            "y_axis": ["clicks", "impressions"],
                            "enable_zoom": True
                        },
                        "optimization_tips": ["Aggregate by week"]
                    }
                ],
                "metadata": {"total_recommendations": 1}
            }
        }


class GenerateInsightsResponse(BaseModel):
    """Combined insights response"""
    data_analysis: Optional[AnalyzeDataResponse] = None
    chart_recommendations: Optional[List[ChartRecommendationResponse]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class RateLimitResponse(BaseModel):
    """Rate limit error response"""
    detail: str = "Rate limit exceeded"
    retry_after: int = Field(description="Seconds until retry is allowed")
    limit: int = Field(description="Rate limit threshold")
    window: str = Field(description="Rate limit window duration")
