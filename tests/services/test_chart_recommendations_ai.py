"""Tests for Chart Recommendations AI Service"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import pandas as pd
import numpy as np

from amc_manager.services.chart_recommendations_ai import (
    ChartRecommendationsAI,
    ChartRecommendation,
    ChartType,
    ChartConfig,
    DataCharacteristics,
    VisualizationBestPractices,
    ChartRecommendationError
)


class TestChartRecommendationsAI:
    """Test suite for Chart Recommendations AI functionality"""

    @pytest.fixture
    def sample_numeric_data(self):
        """Sample data with numeric values for testing"""
        return {
            "columns": ["date", "impressions", "clicks", "spend"],
            "rows": [
                ["2025-01-01", 1000, 50, 100.00],
                ["2025-01-02", 1200, 60, 120.00],
                ["2025-01-03", 1100, 55, 110.00],
                ["2025-01-04", 1300, 70, 130.00],
                ["2025-01-05", 1500, 85, 150.00]
            ]
        }

    @pytest.fixture
    def sample_categorical_data(self):
        """Sample data with categorical values"""
        return {
            "columns": ["campaign", "impressions", "clicks"],
            "rows": [
                ["Campaign A", 5000, 250],
                ["Campaign B", 3500, 175],
                ["Campaign C", 4200, 210],
                ["Campaign D", 2800, 140],
                ["Campaign E", 3900, 195]
            ]
        }

    @pytest.fixture
    def sample_mixed_data(self):
        """Sample data with mixed data types"""
        return {
            "columns": ["date", "category", "value", "percentage"],
            "rows": [
                ["2025-01-01", "A", 100, 0.25],
                ["2025-01-01", "B", 150, 0.35],
                ["2025-01-01", "C", 120, 0.40],
                ["2025-01-02", "A", 110, 0.27],
                ["2025-01-02", "B", 160, 0.38],
                ["2025-01-02", "C", 115, 0.35]
            ]
        }

    @pytest.fixture
    def chart_recommendations_ai(self):
        """Create ChartRecommendationsAI instance for testing"""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-openai-key'
        }):
            return ChartRecommendationsAI()

    @pytest.mark.asyncio
    async def test_data_type_detection_numeric(self, chart_recommendations_ai, sample_numeric_data):
        """Test detection of numeric data types"""
        characteristics = chart_recommendations_ai._analyze_data_characteristics(sample_numeric_data)

        assert "impressions" in characteristics.numeric_columns
        assert "clicks" in characteristics.numeric_columns
        assert "spend" in characteristics.numeric_columns
        assert len(characteristics.numeric_columns) == 3

    @pytest.mark.asyncio
    async def test_data_type_detection_categorical(self, chart_recommendations_ai, sample_categorical_data):
        """Test detection of categorical data types"""
        characteristics = chart_recommendations_ai._analyze_data_characteristics(sample_categorical_data)

        assert "campaign" in characteristics.categorical_columns
        assert len(characteristics.categorical_columns) == 1

    @pytest.mark.asyncio
    async def test_data_type_detection_temporal(self, chart_recommendations_ai, sample_numeric_data):
        """Test detection of temporal/date data types"""
        characteristics = chart_recommendations_ai._analyze_data_characteristics(sample_numeric_data)

        assert "date" in characteristics.temporal_columns
        assert len(characteristics.temporal_columns) == 1

    @pytest.mark.asyncio
    async def test_line_chart_recommendation_time_series(self, chart_recommendations_ai, sample_numeric_data):
        """Test line chart recommendation for time series data"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_numeric_data)

        # Should recommend line chart for time series data
        assert any(rec.chart_type == ChartType.LINE for rec in recommendations)

        # Line chart should have high confidence for time series
        line_chart = next(rec for rec in recommendations if rec.chart_type == ChartType.LINE)
        assert line_chart.confidence_score >= 0.8

    @pytest.mark.asyncio
    async def test_bar_chart_recommendation_categorical(self, chart_recommendations_ai, sample_categorical_data):
        """Test bar chart recommendation for categorical data"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_categorical_data)

        # Should recommend bar chart for categorical comparisons
        assert any(rec.chart_type == ChartType.BAR for rec in recommendations)

        # Bar chart should have high confidence for categorical data
        bar_chart = next(rec for rec in recommendations if rec.chart_type == ChartType.BAR)
        assert bar_chart.confidence_score >= 0.8

    @pytest.mark.asyncio
    async def test_pie_chart_recommendation_proportions(self, chart_recommendations_ai):
        """Test pie chart recommendation for proportional data"""
        # Data with few categories suitable for pie chart
        data = {
            "columns": ["segment", "percentage"],
            "rows": [
                ["Desktop", 45],
                ["Mobile", 35],
                ["Tablet", 20]
            ]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(data)

        # Should recommend pie chart for proportional data
        assert any(rec.chart_type == ChartType.PIE for rec in recommendations)

    @pytest.mark.asyncio
    async def test_scatter_chart_recommendation_correlation(self, chart_recommendations_ai):
        """Test scatter chart recommendation for correlation analysis"""
        # Data with two numeric variables
        data = {
            "columns": ["spend", "conversions"],
            "rows": [
                [100, 5],
                [150, 8],
                [120, 6],
                [180, 10],
                [140, 7]
            ]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(data)

        # Should recommend scatter chart for correlation
        assert any(rec.chart_type == ChartType.SCATTER for rec in recommendations)

    @pytest.mark.asyncio
    async def test_area_chart_recommendation_cumulative(self, chart_recommendations_ai):
        """Test area chart recommendation for cumulative trends"""
        # Time series data suitable for area chart
        data = {
            "columns": ["date", "total_conversions"],
            "rows": [
                ["2025-01-01", 10],
                ["2025-01-02", 25],
                ["2025-01-03", 42],
                ["2025-01-04", 65],
                ["2025-01-05", 85]
            ]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(data)

        # Should recommend area chart for cumulative data
        assert any(rec.chart_type == ChartType.AREA for rec in recommendations)

    @pytest.mark.asyncio
    async def test_table_recommendation_many_columns(self, chart_recommendations_ai):
        """Test table recommendation for data with many columns"""
        # Data with many columns
        data = {
            "columns": ["col1", "col2", "col3", "col4", "col5", "col6", "col7", "col8"],
            "rows": [
                [1, 2, 3, 4, 5, 6, 7, 8],
                [9, 10, 11, 12, 13, 14, 15, 16]
            ]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(data)

        # Should recommend table for data with many columns
        assert any(rec.chart_type == ChartType.TABLE for rec in recommendations)

    @pytest.mark.asyncio
    async def test_metric_card_recommendation_single_value(self, chart_recommendations_ai):
        """Test metric card recommendation for single value"""
        # Single aggregated value
        data = {
            "columns": ["total_conversions"],
            "rows": [[450]]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(data)

        # Should recommend metric card for single value
        assert any(rec.chart_type == ChartType.METRIC_CARD for rec in recommendations)

    @pytest.mark.asyncio
    async def test_heatmap_recommendation_matrix_data(self, chart_recommendations_ai):
        """Test heatmap recommendation for matrix data"""
        # Matrix-style data
        data = {
            "columns": ["hour", "day", "clicks"],
            "rows": [
                ["00:00", "Monday", 10],
                ["01:00", "Monday", 5],
                ["00:00", "Tuesday", 12],
                ["01:00", "Tuesday", 8]
            ]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(data)

        # Should recommend heatmap for matrix data
        assert any(rec.chart_type == ChartType.HEATMAP for rec in recommendations)

    @pytest.mark.asyncio
    async def test_funnel_recommendation_conversion_data(self, chart_recommendations_ai):
        """Test funnel chart recommendation for conversion funnel data"""
        # Conversion funnel data
        data = {
            "columns": ["stage", "count"],
            "rows": [
                ["Impressions", 10000],
                ["Clicks", 500],
                ["Add to Cart", 100],
                ["Purchases", 25]
            ]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(data)

        # Should recommend funnel for conversion data
        assert any(rec.chart_type == ChartType.FUNNEL for rec in recommendations)

    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self, chart_recommendations_ai, sample_numeric_data):
        """Test confidence score calculation for recommendations"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_numeric_data)

        # All recommendations should have confidence scores
        for rec in recommendations:
            assert 0.0 <= rec.confidence_score <= 1.0

        # Recommendations should be sorted by confidence
        for i in range(len(recommendations) - 1):
            assert recommendations[i].confidence_score >= recommendations[i + 1].confidence_score

    @pytest.mark.asyncio
    async def test_chart_configuration_suggestions(self, chart_recommendations_ai, sample_numeric_data):
        """Test configuration parameter suggestions for charts"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_numeric_data)

        # Each recommendation should have configuration suggestions
        for rec in recommendations:
            assert rec.config is not None
            assert rec.config.x_axis is not None
            assert rec.config.y_axis is not None or rec.chart_type == ChartType.PIE

    @pytest.mark.asyncio
    async def test_visualization_best_practices_validation(self, chart_recommendations_ai):
        """Test validation against visualization best practices"""
        # Too many categories for pie chart
        data = {
            "columns": ["category", "value"],
            "rows": [[f"Cat{i}", i * 10] for i in range(15)]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(data)

        # Pie chart should have lower confidence or warnings for too many categories
        pie_charts = [rec for rec in recommendations if rec.chart_type == ChartType.PIE]
        if pie_charts:
            assert len(pie_charts[0].warnings) > 0 or pie_charts[0].confidence_score < 0.5

    @pytest.mark.asyncio
    async def test_color_palette_suggestions(self, chart_recommendations_ai, sample_categorical_data):
        """Test color palette suggestions"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_categorical_data)

        # Should provide color palette suggestions
        for rec in recommendations:
            if rec.config and hasattr(rec.config, 'color_palette'):
                assert len(rec.config.color_palette) > 0

    @pytest.mark.asyncio
    async def test_axis_label_suggestions(self, chart_recommendations_ai, sample_numeric_data):
        """Test axis label suggestions"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_numeric_data)

        # Should suggest appropriate axis labels
        for rec in recommendations:
            if rec.chart_type in [ChartType.LINE, ChartType.BAR, ChartType.SCATTER]:
                assert rec.config.x_axis_label is not None
                assert rec.config.y_axis_label is not None

    @pytest.mark.asyncio
    async def test_chart_title_suggestions(self, chart_recommendations_ai, sample_numeric_data):
        """Test chart title suggestions"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_numeric_data)

        # Should suggest meaningful chart titles
        for rec in recommendations:
            assert rec.suggested_title is not None
            assert len(rec.suggested_title) > 0

    @pytest.mark.asyncio
    async def test_optimization_recommendations(self, chart_recommendations_ai, sample_numeric_data):
        """Test chart optimization recommendations"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_numeric_data)

        # Should provide optimization tips
        for rec in recommendations:
            assert hasattr(rec, 'optimization_tips')
            if rec.chart_type != ChartType.TABLE:
                assert len(rec.optimization_tips) > 0

    @pytest.mark.asyncio
    async def test_multiple_chart_recommendations(self, chart_recommendations_ai, sample_mixed_data):
        """Test that multiple valid chart types are recommended"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_mixed_data)

        # Should recommend multiple chart types
        assert len(recommendations) >= 2

        # Should have different chart types
        chart_types = [rec.chart_type for rec in recommendations]
        assert len(set(chart_types)) >= 2

    @pytest.mark.asyncio
    async def test_recommendation_reasoning(self, chart_recommendations_ai, sample_numeric_data):
        """Test that recommendations include reasoning"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_numeric_data)

        # Each recommendation should have reasoning
        for rec in recommendations:
            assert rec.reasoning is not None
            assert len(rec.reasoning) > 0
            assert "because" in rec.reasoning.lower() or "best" in rec.reasoning.lower()

    @pytest.mark.asyncio
    async def test_empty_data_handling(self, chart_recommendations_ai):
        """Test handling of empty data"""
        empty_data = {
            "columns": [],
            "rows": []
        }

        with pytest.raises(ChartRecommendationError, match="No data to analyze"):
            await chart_recommendations_ai.recommend_charts(empty_data)

    @pytest.mark.asyncio
    async def test_invalid_data_handling(self, chart_recommendations_ai):
        """Test handling of invalid data structures"""
        invalid_data = {
            "columns": ["col1", "col2"],
            "rows": "not a list"
        }

        with pytest.raises(ChartRecommendationError):
            await chart_recommendations_ai.recommend_charts(invalid_data)

    @pytest.mark.asyncio
    async def test_single_row_data(self, chart_recommendations_ai):
        """Test recommendations for single row data"""
        single_row = {
            "columns": ["metric1", "metric2", "metric3"],
            "rows": [[100, 200, 300]]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(single_row)

        # Should recommend metric cards or bar chart for single row
        assert any(rec.chart_type in [ChartType.METRIC_CARD, ChartType.BAR] for rec in recommendations)

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, chart_recommendations_ai):
        """Test handling of large datasets"""
        # Create large dataset
        large_data = {
            "columns": ["date", "value"],
            "rows": [[f"2025-01-{i:02d}", i * 100] for i in range(1, 101)]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(large_data)

        # Should provide recommendations with data sampling warnings
        assert len(recommendations) > 0
        # Line chart should be recommended for large time series
        assert any(rec.chart_type == ChartType.LINE for rec in recommendations)

    @pytest.mark.asyncio
    async def test_data_aggregation_suggestions(self, chart_recommendations_ai):
        """Test suggestions for data aggregation"""
        # Detailed data that could benefit from aggregation
        detailed_data = {
            "columns": ["timestamp", "value"],
            "rows": [[f"2025-01-01 {h:02d}:00:00", h * 10] for h in range(24)]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(detailed_data)

        # Should suggest aggregation in optimization tips
        for rec in recommendations:
            if rec.chart_type == ChartType.LINE:
                assert any("aggregate" in tip.lower() for tip in rec.optimization_tips)

    @pytest.mark.asyncio
    async def test_chart_type_exclusions(self, chart_recommendations_ai):
        """Test that inappropriate chart types are excluded"""
        # Continuous numeric data - pie chart should not be recommended
        continuous_data = {
            "columns": ["value1", "value2"],
            "rows": [[i * 1.5, i * 2.3] for i in range(20)]
        }

        recommendations = await chart_recommendations_ai.recommend_charts(continuous_data)

        # Pie chart should not be in recommendations
        chart_types = [rec.chart_type for rec in recommendations]
        assert ChartType.PIE not in chart_types

    @pytest.mark.asyncio
    async def test_caching_mechanism(self, chart_recommendations_ai, sample_numeric_data):
        """Test that recommendations are cached"""
        # First call
        recommendations1 = await chart_recommendations_ai.recommend_charts(sample_numeric_data)

        # Second call with same data
        with patch.object(chart_recommendations_ai, '_analyze_data_characteristics') as mock_analyze:
            recommendations2 = await chart_recommendations_ai.recommend_charts(sample_numeric_data)
            # Should use cache, not reanalyze
            mock_analyze.assert_not_called()

        assert len(recommendations1) == len(recommendations2)

    @pytest.mark.asyncio
    async def test_custom_parameters(self, chart_recommendations_ai, sample_numeric_data):
        """Test custom recommendation parameters"""
        recommendations = await chart_recommendations_ai.recommend_charts(
            sample_numeric_data,
            max_recommendations=3,
            min_confidence=0.7
        )

        # Should respect max recommendations
        assert len(recommendations) <= 3

        # Should respect min confidence
        for rec in recommendations:
            assert rec.confidence_score >= 0.7

    @pytest.mark.asyncio
    async def test_chart_interactivity_suggestions(self, chart_recommendations_ai, sample_numeric_data):
        """Test suggestions for chart interactivity"""
        recommendations = await chart_recommendations_ai.recommend_charts(sample_numeric_data)

        # Should suggest interactivity options
        for rec in recommendations:
            if rec.chart_type in [ChartType.LINE, ChartType.BAR, ChartType.SCATTER]:
                assert hasattr(rec.config, 'enable_tooltips')
                assert hasattr(rec.config, 'enable_zoom')

    def test_data_characteristics_analysis(self, chart_recommendations_ai, sample_mixed_data):
        """Test data characteristics analysis"""
        characteristics = chart_recommendations_ai._analyze_data_characteristics(sample_mixed_data)

        assert isinstance(characteristics, DataCharacteristics)
        assert len(characteristics.numeric_columns) > 0
        assert len(characteristics.categorical_columns) > 0
        assert len(characteristics.temporal_columns) > 0
        assert characteristics.row_count > 0
        assert characteristics.column_count > 0

    def test_best_practices_validator(self, chart_recommendations_ai):
        """Test visualization best practices validator"""
        validator = chart_recommendations_ai._get_best_practices_validator()

        assert isinstance(validator, VisualizationBestPractices)

        # Test pie chart category limit
        assert validator.max_pie_chart_categories <= 7

        # Test color palette size
        assert len(validator.default_color_palette) >= 5
