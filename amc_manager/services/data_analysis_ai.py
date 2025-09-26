"""Data Analysis AI Service for AMC Query Results"""

import os
import json
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

from amc_manager.services.ai_service import AIService, AIServiceError
from amc_manager.services.db_service import DatabaseService

logger = logging.getLogger(__name__)


class InsightCategory(str, Enum):
    """Categories for data insights"""
    TREND = "trend"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    PERFORMANCE = "performance"
    OPTIMIZATION = "optimization"
    PATTERN = "pattern"
    FORECAST = "forecast"


class TrendType(str, Enum):
    """Types of trends detected in data"""
    UPWARD = "upward"
    DOWNWARD = "downward"
    STABLE = "stable"
    VOLATILE = "volatile"
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"


@dataclass
class DataInsight:
    """Represents a single data insight"""
    category: InsightCategory
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    impact: str  # "low", "medium", "high"
    recommendation: Optional[str] = None
    supporting_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StatisticalSummary:
    """Statistical summary of metrics"""
    metrics: Dict[str, Dict[str, float]]  # metric_name -> {mean, median, std, min, max, etc.}
    correlations: Dict[Tuple[str, str], float]
    outliers: Dict[str, List[int]]  # metric_name -> list of row indices
    trends: Dict[str, Dict[str, Any]]  # metric_name -> trend info


@dataclass
class DataAnalysisRequest:
    """Request for data analysis"""
    data: Dict[str, Any]  # AMC query result
    analysis_type: str = "comprehensive"  # "comprehensive", "trends_only", "anomalies_only", etc.
    confidence_threshold: float = 0.7
    max_insights: int = 10
    include_forecasting: bool = False
    custom_prompts: Optional[List[str]] = None


@dataclass
class DataAnalysisResponse:
    """Response from data analysis"""
    insights: List[DataInsight]
    statistical_summary: StatisticalSummary
    recommendations: List[str]
    metadata: Dict[str, Any]


class DataAnalysisError(Exception):
    """Custom exception for data analysis errors"""
    pass


class DataPreprocessor:
    """Handles data preprocessing for analysis"""

    def preprocess(self, query_results: Dict[str, Any], sample_size: Optional[int] = None) -> Dict[str, Any]:
        """Preprocess AMC query results for analysis"""
        if not query_results.get("rows") or not query_results.get("columns"):
            raise DataAnalysisError("No data to analyze")

        # Convert to DataFrame
        df = pd.DataFrame(query_results["rows"], columns=query_results["columns"])

        # Sample if needed
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)

        # Identify column types
        numeric_columns = []
        date_columns = []
        categorical_columns = []

        for col in df.columns:
            # Try to convert to numeric
            try:
                df[col] = pd.to_numeric(df[col])
                numeric_columns.append(col)
            except (ValueError, TypeError):
                # Try to parse as date
                try:
                    df[col] = pd.to_datetime(df[col])
                    date_columns.append(col)
                except (ValueError, TypeError):
                    # Treat as categorical
                    categorical_columns.append(col)

        return {
            "dataframe": df,
            "numeric_columns": numeric_columns,
            "date_columns": date_columns,
            "categorical_columns": categorical_columns,
            "original_metadata": query_results.get("metadata", {})
        }

    def normalize_data(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Normalize specified columns"""
        scaler = StandardScaler()
        df_normalized = df.copy()

        if columns:
            df_normalized[columns] = scaler.fit_transform(df[columns])

        return df_normalized


class TrendDetector:
    """Detects trends and patterns in data"""

    def detect_trend(self, series: pd.Series, check_seasonality: bool = False) -> Dict[str, Any]:
        """Detect trend in a time series"""
        if len(series) < 3:
            return {"type": TrendType.STABLE, "strength": 0, "confidence": 0}

        # Remove NaN values
        series = series.dropna()

        if len(series) < 3:
            return {"type": TrendType.STABLE, "strength": 0, "confidence": 0}

        # Linear regression for trend
        X = np.arange(len(series)).reshape(-1, 1)
        y = series.values

        model = LinearRegression()
        model.fit(X, y)

        slope = model.coef_[0]
        r_squared = model.score(X, y)

        # Calculate trend strength
        y_range = np.max(y) - np.min(y)
        if y_range > 0:
            normalized_slope = abs(slope) / y_range
        else:
            normalized_slope = 0

        # Detect seasonality if requested
        if check_seasonality and len(series) >= 12:
            seasonal_result = self._detect_seasonality(series)
            if seasonal_result["is_seasonal"]:
                return {
                    "type": TrendType.SEASONAL,
                    "period": seasonal_result["period"],
                    "strength": seasonal_result["strength"],
                    "confidence": seasonal_result["confidence"],
                    "underlying_trend": slope
                }

        # Determine trend type
        if abs(normalized_slope) < 0.1:
            # Check for volatility
            cv = series.std() / series.mean() if series.mean() != 0 else 0
            if cv > 0.3:
                return {
                    "type": TrendType.VOLATILE,
                    "strength": cv,
                    "confidence": 0.5 + r_squared * 0.5
                }
            else:
                return {
                    "type": TrendType.STABLE,
                    "strength": 1 - abs(normalized_slope),
                    "confidence": r_squared
                }
        elif slope > 0:
            return {
                "type": TrendType.UPWARD,
                "strength": min(normalized_slope * 10, 1),
                "confidence": r_squared
            }
        else:
            return {
                "type": TrendType.DOWNWARD,
                "strength": min(abs(normalized_slope) * 10, 1),
                "confidence": r_squared
            }

    def _detect_seasonality(self, series: pd.Series) -> Dict[str, Any]:
        """Detect seasonal patterns"""
        # Simple autocorrelation approach
        max_lag = min(len(series) // 2, 52)  # Max 52 weeks
        best_correlation = 0
        best_period = 0

        for lag in range(2, max_lag):
            if len(series) > lag:
                correlation = series.autocorr(lag=lag)
                if abs(correlation) > abs(best_correlation):
                    best_correlation = correlation
                    best_period = lag

        is_seasonal = abs(best_correlation) > 0.6

        return {
            "is_seasonal": is_seasonal,
            "period": best_period if is_seasonal else None,
            "strength": abs(best_correlation),
            "confidence": abs(best_correlation)
        }

    def detect_anomalies(self, series: pd.Series, sensitivity: float = 2.5) -> Dict[int, Dict[str, Any]]:
        """Detect anomalies using statistical methods"""
        anomalies = {}

        if len(series) < 3:
            return anomalies

        # Remove NaN values but keep track of original indices
        clean_series = series.dropna()

        if len(clean_series) < 3:
            return anomalies

        # Z-score method
        mean = clean_series.mean()
        std = clean_series.std()

        if std > 0:
            z_scores = np.abs((clean_series - mean) / std)

            for idx in clean_series.index:
                z_score = z_scores[idx]
                if z_score > sensitivity:
                    severity = "high" if z_score > sensitivity * 1.1 else "medium"
                    anomalies[idx] = {
                        "value": clean_series[idx],
                        "z_score": z_score,
                        "severity": severity,
                        "expected_range": (mean - sensitivity * std, mean + sensitivity * std)
                    }

        return anomalies

    def find_change_points(self, series: pd.Series) -> List[int]:
        """Find significant change points in the data"""
        if len(series) < 5:
            return []

        # Use first derivative to find peaks
        diff = series.diff().fillna(0)
        abs_diff = abs(diff)

        # Find peaks in the absolute difference
        peaks, properties = find_peaks(abs_diff, prominence=abs_diff.std())

        return list(peaks)


class InsightGenerator:
    """Generates insights from analyzed data"""

    def categorize_insights(self, insights: List[Dict[str, Any]]) -> Dict[InsightCategory, List[Dict[str, Any]]]:
        """Categorize insights by type"""
        categorized = {category: [] for category in InsightCategory}

        for insight in insights:
            insight_type = insight.get("type", "").lower()

            if "trend" in insight_type:
                categorized[InsightCategory.TREND].append(insight)
            elif "anomaly" in insight_type or "outlier" in insight_type:
                categorized[InsightCategory.ANOMALY].append(insight)
            elif "correlation" in insight_type:
                categorized[InsightCategory.CORRELATION].append(insight)
            elif "performance" in insight_type or "metric" in insight_type:
                categorized[InsightCategory.PERFORMANCE].append(insight)
            elif "optimization" in insight_type or "opportunity" in insight_type:
                categorized[InsightCategory.OPTIMIZATION].append(insight)
            elif "pattern" in insight_type:
                categorized[InsightCategory.PATTERN].append(insight)
            elif "forecast" in insight_type or "prediction" in insight_type:
                categorized[InsightCategory.FORECAST].append(insight)

        return categorized

    def generate_recommendations(self, insights: List[DataInsight]) -> List[str]:
        """Generate actionable recommendations from insights"""
        recommendations = []

        for insight in insights:
            if insight.impact == "high" and insight.confidence > 0.8:
                if insight.recommendation:
                    recommendations.append(insight.recommendation)
                else:
                    # Generate generic recommendation based on category
                    if insight.category == InsightCategory.TREND:
                        if "upward" in insight.description.lower():
                            recommendations.append(f"Continue monitoring the positive trend in {insight.title}")
                        elif "downward" in insight.description.lower():
                            recommendations.append(f"Investigate and address the declining trend in {insight.title}")

                    elif insight.category == InsightCategory.ANOMALY:
                        recommendations.append(f"Review the anomaly detected: {insight.title}")

                    elif insight.category == InsightCategory.OPTIMIZATION:
                        recommendations.append(f"Consider optimization opportunity: {insight.title}")

        return list(set(recommendations))[:5]  # Return top 5 unique recommendations


class DataAnalysisAI(DatabaseService):
    """Main service for AI-powered data analysis"""

    def __init__(self):
        super().__init__()
        self.ai_service = AIService()
        self.preprocessor = DataPreprocessor()
        self.trend_detector = TrendDetector()
        self.insight_generator = InsightGenerator()
        self._cache = {}  # Simple in-memory cache

    async def analyze(self, request: DataAnalysisRequest) -> DataAnalysisResponse:
        """Analyze AMC query results"""
        try:
            # Check cache
            cache_key = self._get_cache_key(request.data)
            if cache_key in self._cache:
                cached_result = self._cache[cache_key]
                # Cache expires after 1 hour
                if (datetime.now() - cached_result["timestamp"]).seconds < 3600:
                    return cached_result["response"]

            # Preprocess data
            processed = self.preprocessor.preprocess(
                request.data,
                sample_size=10000 if self._should_sample(request.data) else None
            )

            df = processed["dataframe"]

            # Generate statistical summary
            statistical_summary = self._generate_statistical_summary(df)

            # Analyze trends
            trends = self._analyze_trends(df, processed["numeric_columns"])

            # Detect anomalies
            anomalies = self._detect_anomalies(df, processed["numeric_columns"])

            # Analyze correlations
            correlations = self._analyze_correlations(df)

            # Generate AI insights
            try:
                ai_insights = await self._generate_ai_insights(
                    request, processed, trends, anomalies, correlations
                )
            except Exception as e:
                logger.warning(f"AI insight generation failed, using fallback: {e}")
                ai_insights = self._generate_fallback_insights(
                    processed, trends, anomalies, correlations
                )

            # Rank and filter insights
            filtered_insights = self._rank_insights(ai_insights)[:request.max_insights]

            # Remove duplicates
            unique_insights = self._deduplicate_insights(filtered_insights)

            # Generate recommendations
            recommendations = self.insight_generator.generate_recommendations(unique_insights)

            response = DataAnalysisResponse(
                insights=unique_insights,
                statistical_summary=statistical_summary,
                recommendations=recommendations,
                metadata={
                    "analysis_type": request.analysis_type,
                    "total_rows_analyzed": len(df),
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Cache the response
            self._cache[cache_key] = {
                "response": response,
                "timestamp": datetime.now()
            }

            return response

        except Exception as e:
            logger.error(f"Data analysis failed: {e}")
            raise DataAnalysisError(f"Failed to analyze data: {str(e)}")

    async def analyze_time_series(self, data: Dict[str, Any], date_column: str,
                                 metric_columns: List[str]) -> Dict[str, Any]:
        """Specialized time series analysis"""
        processed = self.preprocessor.preprocess(data)
        df = processed["dataframe"]

        if date_column not in df.columns:
            raise DataAnalysisError(f"Date column '{date_column}' not found")

        # Sort by date
        df = df.sort_values(date_column)

        results = {}
        for metric in metric_columns:
            if metric in df.columns:
                series = df[metric]

                # Detect trend
                trend = self.trend_detector.detect_trend(series, check_seasonality=True)

                # Simple forecasting (last value + trend)
                if len(series) > 1:
                    recent_change = series.iloc[-1] - series.iloc[-2]
                    forecast = series.iloc[-1] + recent_change
                else:
                    forecast = series.iloc[-1] if len(series) > 0 else None

                results[metric] = {
                    "has_trend": trend["type"] != TrendType.STABLE,
                    "trend_type": trend["type"],
                    "trend_strength": trend["strength"],
                    "forecast": forecast,
                    "confidence": trend["confidence"]
                }

        return results

    async def compare_metrics(self, data: Dict[str, Any], metrics: List[str],
                             comparison_type: str = "growth_rate") -> Dict[str, Any]:
        """Compare multiple metrics"""
        processed = self.preprocessor.preprocess(data)
        df = processed["dataframe"]

        comparison = {}
        growth_rates = {}

        for metric in metrics:
            if metric in df.columns:
                series = df[metric]

                if comparison_type == "growth_rate" and len(series) > 1:
                    # Calculate overall growth rate
                    growth_rate = ((series.iloc[-1] - series.iloc[0]) / series.iloc[0] * 100
                                 if series.iloc[0] != 0 else 0)
                    growth_rates[metric] = growth_rate

                    comparison[metric] = {
                        "growth_rate": growth_rate,
                        "volatility": series.std() / series.mean() if series.mean() != 0 else 0,
                        "trend": self.trend_detector.detect_trend(series)
                    }

        if growth_rates:
            comparison["fastest_growing"] = max(growth_rates, key=growth_rates.get)
            comparison["slowest_growing"] = min(growth_rates, key=growth_rates.get)

            # Find most stable metric (lowest volatility)
            volatilities = {m: comparison[m]["volatility"] for m in comparison
                          if isinstance(comparison[m], dict) and "volatility" in comparison[m]}
            if volatilities:
                comparison["most_stable"] = min(volatilities, key=volatilities.get)

        return comparison

    def _generate_statistical_summary(self, df: pd.DataFrame) -> StatisticalSummary:
        """Generate statistical summary of the data"""
        metrics = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) > 0:
                metrics[col] = {
                    "mean": float(series.mean()),
                    "median": float(series.median()),
                    "std": float(series.std()),
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "q25": float(series.quantile(0.25)),
                    "q75": float(series.quantile(0.75)),
                    "count": len(series)
                }

        # Calculate correlations
        correlations = {}
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            for i, col1 in enumerate(numeric_cols):
                for j, col2 in enumerate(numeric_cols):
                    if i < j:  # Only store upper triangle
                        corr_value = corr_matrix.loc[col1, col2]
                        if not pd.isna(corr_value) and abs(corr_value) > 0.3:
                            correlations[(col1, col2)] = float(corr_value)

        # Detect outliers
        outliers = {}
        for col in numeric_cols:
            anomalies = self.trend_detector.detect_anomalies(df[col])
            if anomalies:
                outliers[col] = list(anomalies.keys())

        # Analyze trends
        trends = {}
        for col in numeric_cols:
            trend = self.trend_detector.detect_trend(df[col])
            trends[col] = trend

        return StatisticalSummary(
            metrics=metrics,
            correlations=correlations,
            outliers=outliers,
            trends=trends
        )

    def _analyze_trends(self, df: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Analyze trends in numeric columns"""
        trends = {}
        for col in numeric_columns:
            if col in df.columns:
                trend = self.trend_detector.detect_trend(df[col], check_seasonality=True)
                trends[col] = trend
        return trends

    def _detect_anomalies(self, df: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Detect anomalies in numeric columns"""
        anomalies = {}
        for col in numeric_columns:
            if col in df.columns:
                col_anomalies = self.trend_detector.detect_anomalies(df[col])
                if col_anomalies:
                    anomalies[col] = col_anomalies
        return anomalies

    def _analyze_correlations(self, df: pd.DataFrame) -> Dict[Tuple[str, str], float]:
        """Analyze correlations between numeric columns"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        correlations = {}

        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()

            for i, col1 in enumerate(numeric_cols):
                for j, col2 in enumerate(numeric_cols):
                    if i < j:  # Only upper triangle
                        corr_value = corr_matrix.loc[col1, col2]
                        if not pd.isna(corr_value) and abs(corr_value) > 0.3:
                            correlations[(col1, col2)] = float(corr_value)

        return correlations

    def _calculate_performance_metrics(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate derived performance metrics"""
        metrics = {}

        # Common e-commerce/advertising metrics
        if "clicks" in df.columns and "impressions" in df.columns:
            df["ctr"] = df["clicks"] / df["impressions"]
            metrics["ctr"] = {
                "average": float(df["ctr"].mean()),
                "trend": self.trend_detector.detect_trend(df["ctr"])["type"]
            }

        if "spend" in df.columns and "clicks" in df.columns:
            df["cpc"] = df["spend"] / df["clicks"].replace(0, np.nan)
            metrics["cpc"] = {
                "average": float(df["cpc"].mean()),
                "trend": self.trend_detector.detect_trend(df["cpc"].dropna())["type"]
            }

        if "conversions" in df.columns and "clicks" in df.columns:
            df["conversion_rate"] = df["conversions"] / df["clicks"].replace(0, np.nan)
            metrics["conversion_rate"] = {
                "average": float(df["conversion_rate"].mean()),
                "trend": self.trend_detector.detect_trend(df["conversion_rate"].dropna())["type"]
            }

        return metrics

    async def _generate_ai_insights(self, request: DataAnalysisRequest, processed: Dict[str, Any],
                                   trends: Dict[str, Any], anomalies: Dict[str, Any],
                                   correlations: Dict[Tuple[str, str], float]) -> List[DataInsight]:
        """Generate insights using AI"""
        prompt = self._generate_analysis_prompt(request.data)

        # Add context about detected patterns
        context = {
            "trends": trends,
            "anomalies": anomalies,
            "correlations": correlations,
            "row_count": len(processed["dataframe"]),
            "columns": list(processed["dataframe"].columns)
        }

        prompt += f"\n\nDetected patterns: {json.dumps(context, indent=2)}"
        prompt += "\n\nProvide insights in JSON format with fields: category, title, description, confidence, impact, recommendation"

        # Call AI service
        ai_response = await self.ai_service.generate_completion(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.3
        )

        # Parse AI response
        insights = []
        try:
            ai_insights = json.loads(ai_response.content)
            if isinstance(ai_insights, list):
                for item in ai_insights:
                    insights.append(DataInsight(
                        category=InsightCategory(item.get("category", "pattern")),
                        title=item.get("title", "Insight"),
                        description=item.get("description", ""),
                        confidence=float(item.get("confidence", 0.5)),
                        impact=item.get("impact", "medium"),
                        recommendation=item.get("recommendation")
                    ))
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse AI insights: {e}")
            # Fallback to pattern-based insights
            insights = self._generate_fallback_insights(processed, trends, anomalies, correlations)

        return insights

    def _generate_fallback_insights(self, processed: Dict[str, Any], trends: Dict[str, Any],
                                   anomalies: Dict[str, Any], correlations: Dict[Tuple[str, str], float]) -> List[DataInsight]:
        """Generate insights without AI (fallback)"""
        insights = []

        # Trend insights
        for col, trend in trends.items():
            if trend["confidence"] > 0.7:
                insights.append(DataInsight(
                    category=InsightCategory.TREND,
                    title=f"{trend['type'].value.capitalize()} trend in {col}",
                    description=f"{col} shows a {trend['type'].value} trend with {trend['strength']:.1%} strength",
                    confidence=trend["confidence"],
                    impact="high" if trend["strength"] > 0.5 else "medium"
                ))

        # Anomaly insights
        for col, col_anomalies in anomalies.items():
            if col_anomalies:
                insights.append(DataInsight(
                    category=InsightCategory.ANOMALY,
                    title=f"Anomalies detected in {col}",
                    description=f"{len(col_anomalies)} anomalous values detected in {col}",
                    confidence=0.8,
                    impact="high" if any(a["severity"] == "high" for a in col_anomalies.values()) else "medium",
                    recommendation=f"Review the {len(col_anomalies)} anomalous values in {col}"
                ))

        # Correlation insights
        for (col1, col2), corr in correlations.items():
            if abs(corr) > 0.7:
                insights.append(DataInsight(
                    category=InsightCategory.CORRELATION,
                    title=f"Strong correlation between {col1} and {col2}",
                    description=f"{col1} and {col2} have a correlation of {corr:.2f}",
                    confidence=abs(corr),
                    impact="medium" if abs(corr) < 0.85 else "high"
                ))

        return insights

    def _generate_analysis_prompt(self, query_results: Dict[str, Any]) -> str:
        """Generate prompt for AI analysis"""
        columns = query_results.get("columns", [])
        sample_rows = query_results.get("rows", [])[:5]  # First 5 rows as sample

        prompt = f"""Analyze the following AMC query results and provide actionable insights:

Columns: {', '.join(columns)}
Sample data (first 5 rows):
{json.dumps(sample_rows, indent=2)}

Total rows: {len(query_results.get('rows', []))}

Please analyze this data for:
1. Trends and patterns
2. Anomalies or outliers
3. Correlations between metrics
4. Performance insights
5. Optimization opportunities

Focus on actionable insights that would help improve campaign performance."""

        return prompt

    def _rank_insights(self, insights: List[DataInsight]) -> List[DataInsight]:
        """Rank insights by importance"""
        # Score based on confidence and impact
        def insight_score(insight: DataInsight) -> float:
            impact_scores = {"low": 0.3, "medium": 0.6, "high": 1.0}
            return insight.confidence * impact_scores.get(insight.impact, 0.5)

        return sorted(insights, key=insight_score, reverse=True)

    def _deduplicate_insights(self, insights: List[DataInsight]) -> List[DataInsight]:
        """Remove duplicate insights"""
        seen_keys = set()
        unique_insights = []

        for insight in insights:
            # Create a key from title and category
            key = f"{insight.category}:{insight.title}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_insights.append(insight)

        return unique_insights

    def _should_sample(self, data: Dict[str, Any]) -> bool:
        """Determine if data should be sampled"""
        row_count = len(data.get("rows", []))
        return row_count > 10000

    def _get_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key for data"""
        # Use hash of columns and first/last rows
        columns = str(data.get("columns", []))
        rows = data.get("rows", [])

        if rows:
            sample = str(rows[0]) + str(rows[-1]) + str(len(rows))
        else:
            sample = "empty"

        key_string = f"{columns}:{sample}"
        return hashlib.md5(key_string.encode()).hexdigest()
