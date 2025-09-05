"""Dashboard Data Service - Queries and formats data for dashboard widgets"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, date
from enum import Enum
import json
from ..core.logger_simple import get_logger
from .reporting_database_service import reporting_db_service
from .data_aggregation_service import data_aggregation_service
from .db_service import db_service

logger = get_logger(__name__)


class ChartType(Enum):
    """Supported chart types for dashboard widgets"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    TABLE = "table"
    METRIC_CARD = "metric_card"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"


class AggregationLevel(Enum):
    """Data aggregation levels"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class DashboardDataService:
    """Service for querying and formatting dashboard data"""
    
    def __init__(self):
        self.db = db_service
        self.reporting_db = reporting_db_service
        self.aggregation_service = data_aggregation_service
        
        # Cache configuration
        self.cache_ttl_seconds = 300  # 5 minutes
        self.cache = {}  # Simple in-memory cache
        
        # Data formatting configurations
        self.MAX_DATA_POINTS = 365  # Maximum data points for time series
        self.MAX_TABLE_ROWS = 1000  # Maximum rows for table widgets
    
    async def get_widget_data(
        self,
        widget_config: Dict[str, Any],
        date_range: Optional[Tuple[date, date]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get formatted data for a dashboard widget
        
        Args:
            widget_config: Widget configuration including type and data source
            date_range: Optional date range filter
            filters: Optional additional filters (instances, campaigns, etc.)
            
        Returns:
            Formatted data ready for visualization
        """
        try:
            widget_type = widget_config.get('widget_type', 'chart')
            chart_type = widget_config.get('chart_type', 'line')
            data_source = widget_config.get('data_source', {})
            
            # Extract data source parameters
            workflow_id = data_source.get('workflow_id')
            instance_id = data_source.get('instance_id')
            metrics = data_source.get('metrics', [])
            dimensions = data_source.get('dimensions', [])
            aggregation_level = data_source.get('aggregation_level', 'weekly')
            
            if not workflow_id or not instance_id:
                logger.error("Missing workflow_id or instance_id in data source")
                return {'error': 'Invalid data source configuration'}
            
            # Apply date range
            if not date_range:
                # Default to last 30 days
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)
            
            # Check cache
            cache_key = self._generate_cache_key(
                widget_config, date_range, filters
            )
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                logger.info(f"Returning cached data for widget")
                return cached_data
            
            # Fetch data based on widget type
            if widget_type == 'metric_card':
                data = await self._get_metric_card_data(
                    workflow_id, instance_id, metrics, date_range, filters
                )
            elif widget_type == 'table':
                data = await self._get_table_data(
                    workflow_id, instance_id, metrics, dimensions, 
                    date_range, filters
                )
            elif chart_type == ChartType.LINE.value:
                data = await self._get_line_chart_data(
                    workflow_id, instance_id, metrics, 
                    aggregation_level, date_range, filters
                )
            elif chart_type == ChartType.BAR.value:
                data = await self._get_bar_chart_data(
                    workflow_id, instance_id, metrics, dimensions,
                    date_range, filters
                )
            elif chart_type == ChartType.PIE.value:
                data = await self._get_pie_chart_data(
                    workflow_id, instance_id, metrics[0] if metrics else 'impressions',
                    dimensions[0] if dimensions else 'campaign',
                    date_range, filters
                )
            elif chart_type == ChartType.AREA.value:
                data = await self._get_area_chart_data(
                    workflow_id, instance_id, metrics,
                    aggregation_level, date_range, filters
                )
            else:
                # Default to line chart
                data = await self._get_line_chart_data(
                    workflow_id, instance_id, metrics,
                    aggregation_level, date_range, filters
                )
            
            # Cache the result
            self._cache_data(cache_key, data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting widget data: {e}")
            return {'error': str(e)}
    
    async def _get_metric_card_data(
        self,
        workflow_id: str,
        instance_id: str,
        metrics: List[str],
        date_range: Tuple[date, date],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get data for metric card widgets (KPIs with comparison)"""
        try:
            metric_name = metrics[0] if metrics else 'impressions'
            
            # Get current period data
            current_aggregates = self.reporting_db.get_aggregates_for_dashboard(
                workflow_id, instance_id, 'weekly',
                date_range[0], date_range[1]
            )
            
            # Calculate current value
            current_value = 0
            for agg in current_aggregates:
                if metric_name in agg.get('metrics', {}):
                    current_value += agg['metrics'][metric_name]
            
            # Get previous period for comparison
            period_length = (date_range[1] - date_range[0]).days
            prev_end = date_range[0] - timedelta(days=1)
            prev_start = prev_end - timedelta(days=period_length)
            
            prev_aggregates = self.reporting_db.get_aggregates_for_dashboard(
                workflow_id, instance_id, 'weekly',
                prev_start, prev_end
            )
            
            # Calculate previous value
            prev_value = 0
            for agg in prev_aggregates:
                if metric_name in agg.get('metrics', {}):
                    prev_value += agg['metrics'][metric_name]
            
            # Calculate change
            change = 0
            change_percent = 0
            if prev_value > 0:
                change = current_value - prev_value
                change_percent = (change / prev_value) * 100
            
            return {
                'type': 'metric_card',
                'metric': metric_name,
                'current_value': round(current_value, 2),
                'previous_value': round(prev_value, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'trend': 'up' if change > 0 else 'down' if change < 0 else 'neutral',
                'period': f"{date_range[0]} to {date_range[1]}"
            }
            
        except Exception as e:
            logger.error(f"Error getting metric card data: {e}")
            return {'error': str(e)}
    
    async def _get_line_chart_data(
        self,
        workflow_id: str,
        instance_id: str,
        metrics: List[str],
        aggregation_level: str,
        date_range: Tuple[date, date],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get time-series data for line charts"""
        try:
            # Get aggregated data
            aggregates = self.reporting_db.get_aggregates_for_dashboard(
                workflow_id, instance_id, aggregation_level,
                date_range[0], date_range[1]
            )
            
            if not aggregates:
                return {
                    'type': 'line_chart',
                    'labels': [],
                    'datasets': []
                }
            
            # Extract dates and organize by metric
            dates = []
            metric_data = {metric: [] for metric in metrics}
            
            for agg in aggregates:
                data_date = agg['data_date']
                dates.append(data_date)
                
                agg_metrics = agg.get('metrics', {})
                for metric in metrics:
                    value = agg_metrics.get(metric, 0)
                    metric_data[metric].append(value)
            
            # Format for Chart.js
            datasets = []
            colors = self._get_chart_colors(len(metrics))
            
            for i, metric in enumerate(metrics):
                datasets.append({
                    'label': self._format_metric_label(metric),
                    'data': metric_data[metric],
                    'borderColor': colors[i],
                    'backgroundColor': colors[i] + '20',  # Add transparency
                    'tension': 0.4,  # Smooth lines
                    'fill': False
                })
            
            return {
                'type': 'line_chart',
                'labels': [d.strftime('%Y-%m-%d') for d in dates],
                'datasets': datasets,
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {'position': 'top'},
                        'title': {'display': True, 'text': 'Metrics Over Time'}
                    },
                    'scales': {
                        'y': {'beginAtZero': True}
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting line chart data: {e}")
            return {'error': str(e)}
    
    async def _get_bar_chart_data(
        self,
        workflow_id: str,
        instance_id: str,
        metrics: List[str],
        dimensions: List[str],
        date_range: Tuple[date, date],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get categorical data for bar charts"""
        try:
            # Get aggregated data
            aggregates = self.reporting_db.get_aggregates_for_dashboard(
                workflow_id, instance_id, 'weekly',
                date_range[0], date_range[1]
            )
            
            if not aggregates:
                return {
                    'type': 'bar_chart',
                    'labels': [],
                    'datasets': []
                }
            
            # Aggregate by dimension (e.g., by campaign)
            dimension = dimensions[0] if dimensions else 'campaigns'
            dimension_totals = {}
            
            for agg in aggregates:
                agg_dimensions = agg.get('dimensions', {})
                dimension_values = agg_dimensions.get(dimension, [])
                agg_metrics = agg.get('metrics', {})
                
                for dim_value in dimension_values[:10]:  # Limit to top 10
                    if dim_value not in dimension_totals:
                        dimension_totals[dim_value] = {m: 0 for m in metrics}
                    
                    for metric in metrics:
                        if metric in agg_metrics:
                            dimension_totals[dim_value][metric] += agg_metrics[metric]
            
            # Sort by first metric and take top items
            if dimension_totals and metrics:
                sorted_dims = sorted(
                    dimension_totals.items(),
                    key=lambda x: x[1][metrics[0]],
                    reverse=True
                )[:20]  # Top 20 items
            else:
                sorted_dims = []
            
            # Format for Chart.js
            labels = [dim[0] for dim in sorted_dims]
            datasets = []
            colors = self._get_chart_colors(len(metrics))
            
            for i, metric in enumerate(metrics):
                datasets.append({
                    'label': self._format_metric_label(metric),
                    'data': [dim[1][metric] for dim in sorted_dims],
                    'backgroundColor': colors[i]
                })
            
            return {
                'type': 'bar_chart',
                'labels': labels,
                'datasets': datasets,
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {'position': 'top'},
                        'title': {'display': True, 'text': f'Metrics by {dimension.title()}'}
                    },
                    'scales': {
                        'y': {'beginAtZero': True}
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting bar chart data: {e}")
            return {'error': str(e)}
    
    async def _get_pie_chart_data(
        self,
        workflow_id: str,
        instance_id: str,
        metric: str,
        dimension: str,
        date_range: Tuple[date, date],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get composition data for pie charts"""
        try:
            # Get aggregated data
            aggregates = self.reporting_db.get_aggregates_for_dashboard(
                workflow_id, instance_id, 'weekly',
                date_range[0], date_range[1]
            )
            
            if not aggregates:
                return {
                    'type': 'pie_chart',
                    'labels': [],
                    'data': [],
                    'backgroundColor': []
                }
            
            # Aggregate by dimension
            dimension_totals = {}
            
            for agg in aggregates:
                agg_dimensions = agg.get('dimensions', {})
                dimension_values = agg_dimensions.get(dimension, [])
                agg_metrics = agg.get('metrics', {})
                
                for dim_value in dimension_values:
                    if dim_value not in dimension_totals:
                        dimension_totals[dim_value] = 0
                    
                    if metric in agg_metrics:
                        dimension_totals[dim_value] += agg_metrics[metric]
            
            # Sort and take top items
            sorted_dims = sorted(
                dimension_totals.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]  # Top 10 for pie chart
            
            # Add "Others" category if there are more items
            if len(dimension_totals) > 10:
                others_total = sum(
                    val for key, val in dimension_totals.items()
                    if key not in [d[0] for d in sorted_dims]
                )
                if others_total > 0:
                    sorted_dims.append(('Others', others_total))
            
            # Format for Chart.js
            labels = [dim[0] for dim in sorted_dims]
            data = [dim[1] for dim in sorted_dims]
            colors = self._get_chart_colors(len(labels))
            
            return {
                'type': 'pie_chart',
                'labels': labels,
                'datasets': [{
                    'data': data,
                    'backgroundColor': colors,
                    'borderWidth': 1
                }],
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {'position': 'right'},
                        'title': {
                            'display': True,
                            'text': f'{self._format_metric_label(metric)} by {dimension.title()}'
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting pie chart data: {e}")
            return {'error': str(e)}
    
    async def _get_area_chart_data(
        self,
        workflow_id: str,
        instance_id: str,
        metrics: List[str],
        aggregation_level: str,
        date_range: Tuple[date, date],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get stacked area chart data"""
        try:
            # Similar to line chart but with fill
            line_data = await self._get_line_chart_data(
                workflow_id, instance_id, metrics,
                aggregation_level, date_range, filters
            )
            
            # Modify datasets for area chart
            if 'datasets' in line_data:
                for dataset in line_data['datasets']:
                    dataset['fill'] = True
                    
                line_data['type'] = 'area_chart'
            
            return line_data
            
        except Exception as e:
            logger.error(f"Error getting area chart data: {e}")
            return {'error': str(e)}
    
    async def _get_table_data(
        self,
        workflow_id: str,
        instance_id: str,
        metrics: List[str],
        dimensions: List[str],
        date_range: Tuple[date, date],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get tabular data for table widgets"""
        try:
            # Get raw execution data for tables
            executions = self.db.get_workflow_executions_sync(
                workflow_id,
                limit=10,
                instance_id=instance_id
            )
            
            # Find executions within date range
            relevant_executions = []
            for exec in executions:
                exec_date = datetime.fromisoformat(exec['created_at']).date()
                if date_range[0] <= exec_date <= date_range[1]:
                    relevant_executions.append(exec)
            
            # Extract table data
            rows = []
            columns = ['Date'] + [self._format_metric_label(m) for m in metrics]
            
            for exec in relevant_executions[:self.MAX_TABLE_ROWS]:
                result_data = exec.get('result_data', {})
                results = result_data.get('results', [])
                
                if results:
                    # Aggregate results
                    totals = {m: 0 for m in metrics}
                    for row in results:
                        for metric in metrics:
                            if metric in row:
                                totals[metric] += float(row[metric] or 0)
                    
                    row_data = [exec['created_at'][:10]]  # Date only
                    row_data.extend([round(totals[m], 2) for m in metrics])
                    rows.append(row_data)
            
            return {
                'type': 'table',
                'columns': columns,
                'rows': rows,
                'total_rows': len(rows)
            }
            
        except Exception as e:
            logger.error(f"Error getting table data: {e}")
            return {'error': str(e)}
    
    async def export_widget_data(
        self,
        widget_config: Dict[str, Any],
        format: str = 'csv',
        date_range: Optional[Tuple[date, date]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Export widget data in specified format
        
        Args:
            widget_config: Widget configuration
            format: Export format ('csv' or 'json')
            date_range: Optional date range
            filters: Optional filters
            
        Returns:
            Exported data as bytes
        """
        try:
            # Get widget data
            data = await self.get_widget_data(widget_config, date_range, filters)
            
            if format == 'csv':
                return self._export_to_csv(data)
            elif format == 'json':
                return json.dumps(data, default=str, indent=2).encode('utf-8')
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting widget data: {e}")
            raise
    
    def _export_to_csv(self, data: Dict[str, Any]) -> bytes:
        """Export data to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        
        if data.get('type') == 'table':
            writer = csv.writer(output)
            writer.writerow(data['columns'])
            writer.writerows(data['rows'])
        elif 'datasets' in data:
            # Time-series data
            writer = csv.writer(output)
            headers = ['Date']
            for dataset in data['datasets']:
                headers.append(dataset['label'])
            writer.writerow(headers)
            
            # Write data rows
            for i, label in enumerate(data.get('labels', [])):
                row = [label]
                for dataset in data['datasets']:
                    if i < len(dataset['data']):
                        row.append(dataset['data'][i])
                    else:
                        row.append('')
                writer.writerow(row)
        
        return output.getvalue().encode('utf-8')
    
    def _format_metric_label(self, metric: str) -> str:
        """Format metric name for display"""
        labels = {
            'impressions': 'Impressions',
            'clicks': 'Clicks',
            'conversions': 'Conversions',
            'spend': 'Spend',
            'sales': 'Sales',
            'units_sold': 'Units Sold',
            'new_to_brand': 'New to Brand',
            'ctr': 'CTR (%)',
            'cvr': 'CVR (%)',
            'acos': 'ACOS (%)',
            'roas': 'ROAS',
            'cpc': 'CPC',
            'cpm': 'CPM',
            'ntb_percentage': 'NTB %'
        }
        return labels.get(metric, metric.replace('_', ' ').title())
    
    def _get_chart_colors(self, count: int) -> List[str]:
        """Get chart colors for datasets"""
        colors = [
            '#3B82F6',  # Blue
            '#10B981',  # Green
            '#F59E0B',  # Amber
            '#EF4444',  # Red
            '#8B5CF6',  # Purple
            '#EC4899',  # Pink
            '#14B8A6',  # Teal
            '#F97316',  # Orange
            '#6366F1',  # Indigo
            '#84CC16',  # Lime
        ]
        
        # Repeat colors if needed
        while len(colors) < count:
            colors.extend(colors)
        
        return colors[:count]
    
    def _generate_cache_key(
        self,
        widget_config: Dict[str, Any],
        date_range: Tuple[date, date],
        filters: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key for widget data"""
        key_parts = [
            widget_config.get('widget_id', ''),
            str(date_range[0]),
            str(date_range[1]),
            json.dumps(filters or {}, sort_keys=True)
        ]
        return '_'.join(key_parts)
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if available and not expired"""
        if cache_key in self.cache:
            cached_entry = self.cache[cache_key]
            if datetime.now() - cached_entry['timestamp'] < timedelta(seconds=self.cache_ttl_seconds):
                return cached_entry['data']
            else:
                # Remove expired entry
                del self.cache[cache_key]
        return None
    
    def _cache_data(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Cache widget data"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        
        # Simple cache size management (keep last 100 entries)
        if len(self.cache) > 100:
            # Remove oldest entries
            sorted_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k]['timestamp']
            )
            for key in sorted_keys[:20]:  # Remove oldest 20
                del self.cache[key]


# Create singleton instance
dashboard_data_service = DashboardDataService()