"""Chart Recommendations AI Service for AMC Query Results"""

import os
import json
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import stats

from amc_manager.services.data_analysis_service import DataAnalysisService

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
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


@dataclass
class ChartConfig:
    """Configuration parameters for a chart"""
    x_axis: Optional[str] = None
    y_axis: Optional[List[str]] = None
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    color_palette: List[str] = field(default_factory=list)
    enable_tooltips: bool = True
    enable_zoom: bool = False
    enable_legend: bool = True
    stacked: bool = False
    show_grid: bool = True
    animation_enabled: bool = True


@dataclass
class DataCharacteristics:
    """Characteristics of the dataset"""
    numeric_columns: List[str]
    categorical_columns: List[str]
    temporal_columns: List[str]
    row_count: int
    column_count: int
    has_time_series: bool
    has_categories: bool
    has_correlations: bool
    cardinality: Dict[str, int]  # column -> unique value count
    data_distribution: Dict[str, str]  # column -> "normal", "skewed", etc.


@dataclass
class ChartRecommendation:
    """A chart type recommendation with configuration"""
    chart_type: ChartType
    confidence_score: float  # 0.0 to 1.0
    reasoning: str
    suggested_title: str
    config: ChartConfig
    optimization_tips: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data_requirements: Optional[Dict[str, Any]] = None


class ChartRecommendationError(Exception):
    """Custom exception for chart recommendation errors"""
    pass


class VisualizationBestPractices:
    """Encapsulates visualization best practices"""

    max_pie_chart_categories = 7
    max_bar_chart_categories = 20
    min_data_points_for_line_chart = 3
    max_data_points_before_aggregation = 100
    min_data_points_for_scatter = 5

    default_color_palette = [
        "#3B82F6",  # Blue
        "#10B981",  # Green
        "#F59E0B",  # Amber
        "#EF4444",  # Red
        "#8B5CF6",  # Purple
        "#EC4899",  # Pink
        "#06B6D4",  # Cyan
        "#F97316",  # Orange
    ]


class ChartRecommendationsAI:
    """AI service for recommending chart types and configurations"""

    def __init__(self):
        """Initialize Chart Recommendations AI service"""
        self.data_analysis_service = DataAnalysisService()
        self.best_practices = VisualizationBestPractices()
        self._cache = {}

    async def recommend_charts(
        self,
        data: Dict[str, Any],
        max_recommendations: int = 5,
        min_confidence: float = 0.5
    ) -> List[ChartRecommendation]:
        """
        Recommend chart types for the given data

        Args:
            data: Query results with columns and rows
            max_recommendations: Maximum number of recommendations to return
            min_confidence: Minimum confidence score threshold

        Returns:
            List of chart recommendations sorted by confidence
        """
        if not data or not data.get("rows") or not data.get("columns"):
            raise ChartRecommendationError("No data to analyze")

        if not isinstance(data.get("rows"), list):
            raise ChartRecommendationError("Invalid data structure: rows must be a list")

        # Check cache
        cache_key = self._generate_cache_key(data)
        if cache_key in self._cache:
            logger.info("Using cached chart recommendations")
            return self._cache[cache_key]

        # Analyze data characteristics
        characteristics = self._analyze_data_characteristics(data)

        # Generate recommendations
        recommendations = []

        # Add recommendations based on data characteristics
        recommendations.extend(self._recommend_for_time_series(data, characteristics))
        recommendations.extend(self._recommend_for_categorical(data, characteristics))
        recommendations.extend(self._recommend_for_correlations(data, characteristics))
        recommendations.extend(self._recommend_for_single_values(data, characteristics))
        recommendations.extend(self._recommend_for_matrices(data, characteristics))
        recommendations.extend(self._recommend_for_funnels(data, characteristics))
        recommendations.extend(self._recommend_table(data, characteristics))

        # Filter by confidence threshold
        recommendations = [r for r in recommendations if r.confidence_score >= min_confidence]

        # Sort by confidence score
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)

        # Apply best practices validation
        recommendations = self._validate_best_practices(recommendations, characteristics)

        # Limit results
        recommendations = recommendations[:max_recommendations]

        # Cache results
        self._cache[cache_key] = recommendations

        return recommendations

    def _analyze_data_characteristics(self, data: Dict[str, Any]) -> DataCharacteristics:
        """Analyze characteristics of the dataset"""
        columns = data.get("columns", [])
        rows = data.get("rows", [])

        if not rows:
            return DataCharacteristics(
                numeric_columns=[],
                categorical_columns=[],
                temporal_columns=[],
                row_count=0,
                column_count=len(columns),
                has_time_series=False,
                has_categories=False,
                has_correlations=False,
                cardinality={},
                data_distribution={}
            )

        # Convert to list of dicts for analysis
        data_dicts = []
        for row in rows:
            data_dicts.append(dict(zip(columns, row)))

        # Use DataAnalysisService to analyze column types
        analysis = self.data_analysis_service.analyze_data(data_dicts)
        column_stats = analysis.get("column_stats", {})

        numeric_columns = []
        categorical_columns = []
        temporal_columns = []
        cardinality = {}
        data_distribution = {}

        for column, stats in column_stats.items():
            col_type = stats.get("type", "unknown")

            if col_type == "numeric":
                numeric_columns.append(column)
                # Determine distribution
                if "std_dev" in stats and "mean" in stats:
                    cv = stats["std_dev"] / stats["mean"] if stats["mean"] != 0 else 0
                    data_distribution[column] = "skewed" if cv > 1 else "normal"
            elif col_type == "datetime":
                temporal_columns.append(column)
            elif col_type == "categorical":
                categorical_columns.append(column)

            cardinality[column] = stats.get("unique_count", 0)

        has_time_series = len(temporal_columns) > 0 and len(numeric_columns) > 0
        has_categories = len(categorical_columns) > 0
        has_correlations = len(numeric_columns) >= 2

        return DataCharacteristics(
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            temporal_columns=temporal_columns,
            row_count=len(rows),
            column_count=len(columns),
            has_time_series=has_time_series,
            has_categories=has_categories,
            has_correlations=has_correlations,
            cardinality=cardinality,
            data_distribution=data_distribution
        )

    def _recommend_for_time_series(
        self,
        data: Dict[str, Any],
        characteristics: DataCharacteristics
    ) -> List[ChartRecommendation]:
        """Recommend charts for time series data"""
        recommendations = []

        if not characteristics.has_time_series:
            return recommendations

        if len(characteristics.numeric_columns) == 0:
            return recommendations

        # Line chart recommendation
        if characteristics.row_count >= self.best_practices.min_data_points_for_line_chart:
            for time_col in characteristics.temporal_columns:
                config = ChartConfig(
                    x_axis=time_col,
                    y_axis=characteristics.numeric_columns[:3],  # Limit to 3 metrics
                    x_axis_label=time_col.replace("_", " ").title(),
                    y_axis_label="Value",
                    color_palette=self.best_practices.default_color_palette,
                    enable_zoom=True,
                    enable_tooltips=True
                )

                optimization_tips = []
                if characteristics.row_count > self.best_practices.max_data_points_before_aggregation:
                    optimization_tips.append("Consider aggregating data by hour/day/week for better performance")

                recommendations.append(ChartRecommendation(
                    chart_type=ChartType.LINE,
                    confidence_score=0.9,
                    reasoning="Line chart is best for visualizing trends over time",
                    suggested_title=f"{', '.join(characteristics.numeric_columns[:3])} Over Time",
                    config=config,
                    optimization_tips=optimization_tips
                ))

        # Area chart recommendation
        if len(characteristics.numeric_columns) > 0:
            config = ChartConfig(
                x_axis=characteristics.temporal_columns[0],
                y_axis=characteristics.numeric_columns[:2],
                x_axis_label=characteristics.temporal_columns[0].replace("_", " ").title(),
                y_axis_label="Value",
                color_palette=self.best_practices.default_color_palette,
                stacked=True
            )

            recommendations.append(ChartRecommendation(
                chart_type=ChartType.AREA,
                confidence_score=0.75,
                reasoning="Area chart works well for showing cumulative trends over time",
                suggested_title=f"Cumulative {', '.join(characteristics.numeric_columns[:2])}",
                config=config,
                optimization_tips=["Use stacked area for multiple metrics to show composition"]
            ))

        return recommendations

    def _recommend_for_categorical(
        self,
        data: Dict[str, Any],
        characteristics: DataCharacteristics
    ) -> List[ChartRecommendation]:
        """Recommend charts for categorical data"""
        recommendations = []

        if not characteristics.has_categories or len(characteristics.numeric_columns) == 0:
            return recommendations

        cat_col = characteristics.categorical_columns[0]
        cat_cardinality = characteristics.cardinality.get(cat_col, 0)

        # Bar chart recommendation
        if cat_cardinality <= self.best_practices.max_bar_chart_categories:
            config = ChartConfig(
                x_axis=cat_col,
                y_axis=characteristics.numeric_columns[:1],
                x_axis_label=cat_col.replace("_", " ").title(),
                y_axis_label=characteristics.numeric_columns[0].replace("_", " ").title(),
                color_palette=self.best_practices.default_color_palette
            )

            confidence = 0.85 if cat_cardinality <= 10 else 0.70

            recommendations.append(ChartRecommendation(
                chart_type=ChartType.BAR,
                confidence_score=confidence,
                reasoning="Bar chart is ideal for comparing values across categories",
                suggested_title=f"{characteristics.numeric_columns[0]} by {cat_col}",
                config=config,
                optimization_tips=["Sort bars by value for easier comparison"]
            ))

        # Pie chart recommendation
        if cat_cardinality <= self.best_practices.max_pie_chart_categories:
            config = ChartConfig(
                x_axis=cat_col,
                y_axis=[characteristics.numeric_columns[0]],
                color_palette=self.best_practices.default_color_palette,
                enable_legend=True
            )

            warnings = []
            confidence = 0.75

            if cat_cardinality > 5:
                warnings.append("Pie charts work best with 5 or fewer categories")
                confidence = 0.60

            recommendations.append(ChartRecommendation(
                chart_type=ChartType.PIE,
                confidence_score=confidence,
                reasoning="Pie chart shows proportional distribution across categories",
                suggested_title=f"Distribution of {characteristics.numeric_columns[0]}",
                config=config,
                warnings=warnings,
                optimization_tips=["Consider using a donut chart for better readability"]
            ))

        return recommendations

    def _recommend_for_correlations(
        self,
        data: Dict[str, Any],
        characteristics: DataCharacteristics
    ) -> List[ChartRecommendation]:
        """Recommend charts for correlation analysis"""
        recommendations = []

        if not characteristics.has_correlations:
            return recommendations

        if characteristics.row_count < self.best_practices.min_data_points_for_scatter:
            return recommendations

        # Scatter plot recommendation
        if len(characteristics.numeric_columns) >= 2:
            config = ChartConfig(
                x_axis=characteristics.numeric_columns[0],
                y_axis=[characteristics.numeric_columns[1]],
                x_axis_label=characteristics.numeric_columns[0].replace("_", " ").title(),
                y_axis_label=characteristics.numeric_columns[1].replace("_", " ").title(),
                color_palette=self.best_practices.default_color_palette,
                enable_tooltips=True
            )

            recommendations.append(ChartRecommendation(
                chart_type=ChartType.SCATTER,
                confidence_score=0.80,
                reasoning="Scatter plot reveals correlations and patterns between two numeric variables",
                suggested_title=f"{characteristics.numeric_columns[0]} vs {characteristics.numeric_columns[1]}",
                config=config,
                optimization_tips=["Add trendline to show correlation strength"]
            ))

        return recommendations

    def _recommend_for_single_values(
        self,
        data: Dict[str, Any],
        characteristics: DataCharacteristics
    ) -> List[ChartRecommendation]:
        """Recommend charts for single value displays"""
        recommendations = []

        # Metric card for single row or single aggregated value
        if characteristics.row_count == 1 or characteristics.column_count <= 3:
            for num_col in characteristics.numeric_columns[:3]:
                config = ChartConfig(
                    y_axis=[num_col],
                    enable_legend=False
                )

                recommendations.append(ChartRecommendation(
                    chart_type=ChartType.METRIC_CARD,
                    confidence_score=0.85,
                    reasoning="Metric card effectively displays key performance indicators",
                    suggested_title=num_col.replace("_", " ").title(),
                    config=config,
                    optimization_tips=["Add comparison to previous period", "Include trend indicator"]
                ))

        return recommendations

    def _recommend_for_matrices(
        self,
        data: Dict[str, Any],
        characteristics: DataCharacteristics
    ) -> List[ChartRecommendation]:
        """Recommend heatmap for matrix-style data"""
        recommendations = []

        # Heatmap recommendation for 2+ categorical columns and 1+ numeric
        if len(characteristics.categorical_columns) >= 2 and len(characteristics.numeric_columns) >= 1:
            config = ChartConfig(
                x_axis=characteristics.categorical_columns[0],
                y_axis=[characteristics.categorical_columns[1]],
                color_palette=self.best_practices.default_color_palette,
                enable_tooltips=True
            )

            recommendations.append(ChartRecommendation(
                chart_type=ChartType.HEATMAP,
                confidence_score=0.75,
                reasoning="Heatmap visualizes intensity across two categorical dimensions",
                suggested_title=f"{characteristics.numeric_columns[0]} Heatmap",
                config=config,
                optimization_tips=["Use diverging color scale for better contrast"]
            ))

        return recommendations

    def _recommend_for_funnels(
        self,
        data: Dict[str, Any],
        characteristics: DataCharacteristics
    ) -> List[ChartRecommendation]:
        """Recommend funnel chart for conversion data"""
        recommendations = []

        # Funnel chart for sequential categorical data with decreasing values
        if len(characteristics.categorical_columns) >= 1 and len(characteristics.numeric_columns) >= 1:
            # Check if data looks like a funnel (decreasing values)
            rows = data.get("rows", [])
            if len(rows) >= 3:
                columns = data.get("columns", [])
                numeric_col_idx = columns.index(characteristics.numeric_columns[0])

                values = [row[numeric_col_idx] for row in rows if len(row) > numeric_col_idx]

                # Check if values are generally decreasing
                decreasing_count = sum(1 for i in range(len(values) - 1) if values[i] > values[i + 1])
                if decreasing_count >= len(values) - 2:  # Allow 1 exception
                    config = ChartConfig(
                        x_axis=characteristics.categorical_columns[0],
                        y_axis=[characteristics.numeric_columns[0]],
                        color_palette=self.best_practices.default_color_palette,
                        enable_legend=False
                    )

                    recommendations.append(ChartRecommendation(
                        chart_type=ChartType.FUNNEL,
                        confidence_score=0.85,
                        reasoning="Funnel chart is ideal for visualizing conversion stages",
                        suggested_title="Conversion Funnel",
                        config=config,
                        optimization_tips=["Show conversion rates between stages", "Highlight drop-off points"]
                    ))

        return recommendations

    def _recommend_table(
        self,
        data: Dict[str, Any],
        characteristics: DataCharacteristics
    ) -> List[ChartRecommendation]:
        """Recommend table for detailed data display"""
        recommendations = []

        # Table is always a fallback option
        config = ChartConfig(
            enable_legend=False
        )

        confidence = 0.65
        optimization_tips = ["Add sorting and filtering", "Highlight important values"]

        # Higher confidence for many columns
        if characteristics.column_count > 5:
            confidence = 0.75
            optimization_tips.append("Consider column visibility toggles")

        recommendations.append(ChartRecommendation(
            chart_type=ChartType.TABLE,
            confidence_score=confidence,
            reasoning="Table provides detailed view of all data points",
            suggested_title="Data Table",
            config=config,
            optimization_tips=optimization_tips
        ))

        return recommendations

    def _validate_best_practices(
        self,
        recommendations: List[ChartRecommendation],
        characteristics: DataCharacteristics
    ) -> List[ChartRecommendation]:
        """Validate recommendations against best practices"""
        for rec in recommendations:
            # Add warnings for pie charts with many categories
            if rec.chart_type == ChartType.PIE:
                if characteristics.categorical_columns:
                    cat_col = rec.config.x_axis or characteristics.categorical_columns[0]
                    cardinality = characteristics.cardinality.get(cat_col, 0)
                    if cardinality > self.best_practices.max_pie_chart_categories:
                        rec.warnings.append(
                            f"Pie chart has {cardinality} categories. Consider using bar chart instead."
                        )
                        rec.confidence_score *= 0.7

            # Add warnings for bar charts with too many categories
            if rec.chart_type == ChartType.BAR:
                if characteristics.categorical_columns:
                    cat_col = rec.config.x_axis or characteristics.categorical_columns[0]
                    cardinality = characteristics.cardinality.get(cat_col, 0)
                    if cardinality > self.best_practices.max_bar_chart_categories:
                        rec.warnings.append(
                            f"Bar chart has {cardinality} categories. Consider grouping or filtering."
                        )
                        rec.confidence_score *= 0.8

        return recommendations

    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key from data"""
        # Create a hash of the data structure (columns and row count)
        key_data = {
            "columns": data.get("columns", []),
            "row_count": len(data.get("rows", []))
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_best_practices_validator(self) -> VisualizationBestPractices:
        """Get the best practices validator"""
        return self.best_practices


# Global instance
chart_recommendations_ai = ChartRecommendationsAI()
