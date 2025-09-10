"""Unit tests for Report Dashboard Service - testing logic without database"""

import pytest
from datetime import date
from uuid import uuid4

# Import the service to test
from amc_manager.services.report_dashboard_service import ReportDashboardService


class TestReportDashboardServiceUnit:
    """Unit tests for ReportDashboardService focusing on business logic"""
    
    def test_aggregate_data_sum(self):
        """Test sum aggregation"""
        service = ReportDashboardService()
        data = [
            {'impressions': 1000, 'clicks': 100, 'spend': 50.5},
            {'impressions': 2000, 'clicks': 200, 'spend': 100.5},
            {'impressions': 3000, 'clicks': 300, 'spend': 150.5}
        ]
        
        result = service.aggregate_data(data, 'sum')
        
        assert result['impressions'] == 6000
        assert result['clicks'] == 600
        assert result['spend'] == 301.5
    
    def test_aggregate_data_avg(self):
        """Test average aggregation"""
        service = ReportDashboardService()
        data = [
            {'impressions': 1000, 'clicks': 100},
            {'impressions': 2000, 'clicks': 200},
            {'impressions': 3000, 'clicks': 300}
        ]
        
        result = service.aggregate_data(data, 'avg')
        
        assert result['impressions'] == 2000
        assert result['clicks'] == 200
    
    def test_aggregate_data_min_max(self):
        """Test min and max aggregation"""
        service = ReportDashboardService()
        data = [
            {'impressions': 1000, 'clicks': 100},
            {'impressions': 2000, 'clicks': 200},
            {'impressions': 3000, 'clicks': 300}
        ]
        
        min_result = service.aggregate_data(data, 'min')
        assert min_result['impressions'] == 1000
        assert min_result['clicks'] == 100
        
        max_result = service.aggregate_data(data, 'max')
        assert max_result['impressions'] == 3000
        assert max_result['clicks'] == 300
    
    def test_calculate_comparison(self):
        """Test period comparison calculations"""
        service = ReportDashboardService()
        
        period1 = [
            {'impressions': 1000, 'clicks': 100, 'spend': 50},
            {'impressions': 2000, 'clicks': 200, 'spend': 100}
        ]
        
        period2 = [
            {'impressions': 1500, 'clicks': 150, 'spend': 75},
            {'impressions': 2500, 'clicks': 250, 'spend': 125}
        ]
        
        result = service.calculate_comparison(
            period1_data=period1,
            period2_data=period2,
            metrics=['impressions', 'clicks', 'spend']
        )
        
        # Check structure
        assert 'period1' in result
        assert 'period2' in result
        assert 'delta' in result
        
        # Check period1 totals
        assert result['period1']['impressions'] == 3000
        assert result['period1']['clicks'] == 300
        assert result['period1']['spend'] == 150
        
        # Check period2 totals
        assert result['period2']['impressions'] == 4000
        assert result['period2']['clicks'] == 400
        assert result['period2']['spend'] == 200
        
        # Check deltas
        assert result['delta']['impressions']['value'] == 1000
        assert result['delta']['impressions']['percent'] == pytest.approx(33.33, 0.01)
        assert result['delta']['clicks']['value'] == 100
        assert result['delta']['spend']['value'] == 50
    
    def test_transform_for_chart_line(self):
        """Test Chart.js transformation for line charts"""
        service = ReportDashboardService()
        
        data = [
            {
                'week_start': '2025-01-01',
                'metrics': {
                    'impressions': 1000,
                    'clicks': 100
                }
            },
            {
                'week_start': '2025-01-08',
                'metrics': {
                    'impressions': 2000,
                    'clicks': 200
                }
            }
        ]
        
        result = service.transform_for_chart(
            data=data,
            chart_type='line',
            metrics=['impressions', 'clicks']
        )
        
        # Check structure
        assert 'labels' in result
        assert 'datasets' in result
        
        # Check labels
        assert len(result['labels']) == 2
        assert result['labels'][0] == '2025-01-01'
        assert result['labels'][1] == '2025-01-08'
        
        # Check datasets
        assert len(result['datasets']) == 2
        
        # Check impressions dataset
        impressions_ds = result['datasets'][0]
        assert impressions_ds['label'] == 'impressions'
        assert impressions_ds['data'] == [1000, 2000]
        assert 'borderColor' in impressions_ds
        
        # Check clicks dataset
        clicks_ds = result['datasets'][1]
        assert clicks_ds['label'] == 'clicks'
        assert clicks_ds['data'] == [100, 200]
    
    def test_calculate_summary_stats(self):
        """Test summary statistics calculation"""
        service = ReportDashboardService()
        
        week_data = [
            {
                'summary_stats': {
                    'total_impressions': 1000000,
                    'total_clicks': 15000,
                    'total_spend': 3000
                }
            },
            {
                'summary_stats': {
                    'total_impressions': 2000000,
                    'total_clicks': 30000,
                    'total_spend': 6000
                }
            }
        ]
        
        result = service.calculate_summary_stats(week_data)
        
        assert result['total_impressions'] == 3000000
        assert result['total_clicks'] == 45000
        assert result['total_spend'] == 9000
        assert result['avg_ctr'] == pytest.approx(1.5, 0.01)  # (45000/3000000)*100
    
    def test_extract_metrics_from_results(self):
        """Test extracting metrics from execution results"""
        service = ReportDashboardService()
        
        result_rows = [
            {'impressions': 1000, 'clicks': 100, 'spend': 50.5},
            {'impressions': 2000, 'clicks': 200, 'spend': 100.5},
            {'impressions': 3000, 'clicks': 300, 'spend': 150.5}
        ]
        
        metrics = service._extract_metrics_from_results(result_rows)
        
        # Check totals
        assert metrics['total_impressions'] == 6000
        assert metrics['total_clicks'] == 600
        assert metrics['total_spend'] == 301.5
        
        # Check averages
        assert metrics['avg_impressions'] == 2000
        assert metrics['avg_clicks'] == 200
        assert metrics['avg_spend'] == pytest.approx(100.5, 0.01)
    
    def test_aggregate_periods(self):
        """Test aggregating multiple periods"""
        service = ReportDashboardService()
        
        periods = [
            {
                'week_start': '2025-01-01',
                'week_end': '2025-01-07',
                'metrics': {'impressions': 1000, 'clicks': 100}
            },
            {
                'week_start': '2025-01-08',
                'week_end': '2025-01-14',
                'metrics': {'impressions': 2000, 'clicks': 200}
            },
            {
                'week_start': '2025-01-15',
                'week_end': '2025-01-21',
                'metrics': {'impressions': 3000, 'clicks': 300}
            }
        ]
        
        # Test sum aggregation
        result = service._aggregate_periods(periods, 'sum')
        
        assert result['week_start'] == '2025-01-01'
        assert result['week_end'] == '2025-01-21'
        assert result['metrics']['impressions'] == 6000
        assert result['metrics']['clicks'] == 600
        assert result['periods_aggregated'] == 3
        
        # Test average aggregation
        result_avg = service._aggregate_periods(periods, 'avg')
        assert result_avg['metrics']['impressions'] == 2000
        assert result_avg['metrics']['clicks'] == 200
    
    def test_process_week_data_with_summary_stats(self):
        """Test processing week data when summary stats are available"""
        service = ReportDashboardService()
        
        week_data = [
            {
                'week_start_date': '2025-01-01',
                'week_end_date': '2025-01-07',
                'summary_stats': {
                    'total_impressions': 1000000,
                    'total_clicks': 15000
                },
                'workflow_execution_id': str(uuid4()),
                'record_count': 1500
            }
        ]
        
        result = service._process_week_data(week_data, 'none')
        
        assert len(result) == 1
        assert result[0]['week_start'] == '2025-01-01'
        assert result[0]['week_end'] == '2025-01-07'
        assert result[0]['metrics']['total_impressions'] == 1000000
        assert result[0]['metrics']['total_clicks'] == 15000
        assert result[0]['row_count'] == 1500
    
    def test_get_background_color(self):
        """Test background color generation for different chart types"""
        service = ReportDashboardService()
        
        color = '#3B82F6'
        
        # For area/line charts, should add transparency
        bg_color = service._get_background_color(color, 'area')
        assert bg_color == '#3B82F620'
        
        bg_color = service._get_background_color(color, 'line')
        assert bg_color == '#3B82F620'
        
        # For bar charts, should return same color
        bg_color = service._get_background_color(color, 'bar')
        assert bg_color == '#3B82F6'
    
    def test_empty_data_handling(self):
        """Test handling of empty data"""
        service = ReportDashboardService()
        
        # Test empty aggregation
        result = service.aggregate_data([], 'sum')
        assert result == {}
        
        # Test empty comparison
        result = service.calculate_comparison([], [], [])
        assert result['period1'] == {}
        assert result['period2'] == {}
        
        # Test empty transform
        result = service.transform_for_chart([], 'line', [])
        assert result['labels'] == []
        assert result['datasets'] == []
        
        # Test empty summary stats
        result = service.calculate_summary_stats([])
        assert result == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])