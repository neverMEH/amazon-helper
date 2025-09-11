"""Report Dashboard Service - Manages collection report dashboard data and operations"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime, date, timedelta
import json
import uuid
from decimal import Decimal
from collections import defaultdict

from ..core.logger_simple import get_logger
from .db_service import DatabaseService, with_connection_retry, db_service

logger = get_logger(__name__)


class ReportDashboardService(DatabaseService):
    """Service for managing collection report dashboard operations"""
    
    def __init__(self):
        super().__init__()
        self.db = db_service
        
        # Chart color palette
        self.default_colors = [
            '#3B82F6',  # Blue
            '#10B981',  # Green
            '#F59E0B',  # Yellow
            '#EF4444',  # Red
            '#8B5CF6',  # Purple
            '#EC4899',  # Pink
            '#14B8A6',  # Teal
            '#F97316',  # Orange
        ]
    
    @with_connection_retry
    def get_dashboard_data(
        self,
        collection_id: str,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        weeks: Optional[List[str]] = None,
        aggregation: str = 'none'
    ) -> Dict[str, Any]:
        """
        Get dashboard data for a collection with optional filtering
        
        Args:
            collection_id: UUID of the collection
            user_id: User ID for access control
            start_date: Optional start date filter
            end_date: Optional end date filter
            weeks: Optional list of specific week start dates
            aggregation: Aggregation type ('none', 'sum', 'avg', 'min', 'max')
            
        Returns:
            Dashboard data with metadata and metrics
        """
        try:
            # Fetch collection details
            collection_response = self.client.table('report_data_collections')\
                .select('*')\
                .eq('id', collection_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not collection_response.data:
                raise ValueError(f"Collection not found or access denied: {collection_id}")
            
            collection = collection_response.data[0]
            
            # Build query for weeks
            weeks_query = self.client.table('report_data_weeks')\
                .select('*, workflow_executions!workflow_execution_id(*)')\
                .eq('collection_id', collection_id)\
                .eq('status', 'succeeded')
            
            # Apply filters
            if start_date:
                weeks_query = weeks_query.gte('week_start_date', start_date.isoformat())
            if end_date:
                weeks_query = weeks_query.lte('week_end_date', end_date.isoformat())
            if weeks:
                weeks_query = weeks_query.in_('week_start_date', weeks)
            
            # Execute query
            weeks_response = weeks_query.order('week_start_date').execute()
            week_data = weeks_response.data or []
            
            # Extract metadata
            metadata = self._extract_metadata(collection, week_data)
            
            # Process and transform data
            processed_data = self._process_week_data(week_data, aggregation)
            
            # Calculate summary statistics
            summary = self._calculate_summary(processed_data)
            
            # Return data structure matching frontend expectations
            return {
                'collection': {
                    'id': collection_id,
                    'name': collection.get('collection_id', 'Unknown'),
                    'workflow_id': collection.get('workflow_id', ''),
                    'instance_id': collection.get('instance_id', ''),
                    'status': collection.get('status', 'unknown'),
                    'created_at': collection.get('created_at', ''),
                    'weeks_completed': metadata.get('successful_weeks', 0),
                    'weeks_failed': metadata.get('total_weeks', 0) - metadata.get('successful_weeks', 0),
                    'weeks_pending': 0
                },
                'weeks': processed_data,  # Changed from 'data' to 'weeks'
                'summary': summary,
                'chartData': None  # Will be populated by frontend
            }
            
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            raise
    
    def _extract_metadata(self, collection: Dict, week_data: List[Dict]) -> Dict[str, Any]:
        """Extract metadata from collection and week data"""
        # Get available KPIs from first successful execution
        available_kpis = []
        if week_data and week_data[0].get('workflow_executions'):
            execution = week_data[0]['workflow_executions']
            if execution.get('result_columns'):
                available_kpis = [col['name'] for col in execution['result_columns']]
        
        # Use cached metadata if available
        if collection.get('report_metadata'):
            available_kpis = collection['report_metadata'].get('available_kpis', available_kpis)
        
        return {
            'total_weeks': len(week_data),
            'successful_weeks': len([w for w in week_data if w['status'] == 'succeeded']),
            'date_range': {
                'start': min([w['week_start_date'] for w in week_data]) if week_data else None,
                'end': max([w['week_end_date'] for w in week_data]) if week_data else None
            },
            'available_kpis': available_kpis
        }
    
    def _process_week_data(self, week_data: List[Dict], aggregation: str) -> List[Dict]:
        """Process week data and apply aggregation if needed"""
        processed = []
        
        for week in week_data:
            week_metrics = {}
            
            # Use summary stats if available
            if week.get('summary_stats'):
                week_metrics = week['summary_stats']
            # Otherwise extract from execution results
            elif week.get('workflow_executions') and week['workflow_executions'].get('result_rows'):
                week_metrics = self._extract_metrics_from_results(
                    week['workflow_executions']['result_rows']
                )
            
            # Match the WeekData interface expected by frontend
            processed.append({
                'id': week.get('id', f"week_{week.get('week_number', 0)}"),
                'week_number': week.get('week_number', 0),
                'week_start': week['week_start_date'],
                'week_end': week['week_end_date'],
                'status': week.get('status', 'unknown'),
                'execution_results': {
                    'metrics': week_metrics
                } if week_metrics else None
            })
        
        # Apply aggregation if requested
        if aggregation != 'none' and processed:
            return [self._aggregate_periods(processed, aggregation)]
        
        return processed
    
    def _extract_metrics_from_results(self, result_rows: List[Dict]) -> Dict[str, Any]:
        """Extract and aggregate metrics from execution result rows"""
        if not result_rows:
            return {}
        
        metrics = defaultdict(float)
        count = len(result_rows)
        
        for row in result_rows:
            for key, value in row.items():
                if isinstance(value, (int, float, Decimal)):
                    metrics[f'total_{key}'] += float(value)
        
        # Calculate averages
        for key in list(metrics.keys()):
            if key.startswith('total_'):
                base_key = key.replace('total_', '')
                metrics[f'avg_{base_key}'] = metrics[key] / count if count > 0 else 0
        
        return dict(metrics)
    
    def _aggregate_periods(self, periods: List[Dict], aggregation_type: str) -> Dict[str, Any]:
        """Aggregate multiple periods into a single result"""
        if not periods:
            return {}
        
        all_metrics = defaultdict(list)
        
        # Collect all metric values
        for period in periods:
            for metric, value in period.get('metrics', {}).items():
                if isinstance(value, (int, float, Decimal)):
                    all_metrics[metric].append(float(value))
        
        # Apply aggregation
        aggregated = {}
        for metric, values in all_metrics.items():
            if aggregation_type == 'sum':
                aggregated[metric] = sum(values)
            elif aggregation_type == 'avg':
                aggregated[metric] = sum(values) / len(values) if values else 0
            elif aggregation_type == 'min':
                aggregated[metric] = min(values) if values else 0
            elif aggregation_type == 'max':
                aggregated[metric] = max(values) if values else 0
        
        return {
            'week_start': periods[0]['week_start'],
            'week_end': periods[-1]['week_end'],
            'metrics': aggregated,
            'periods_aggregated': len(periods)
        }
    
    def _calculate_summary(self, data: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics across all data"""
        if not data:
            return {}
        
        summary_metrics = defaultdict(float)
        total_rows = 0
        
        for item in data:
            metrics = item.get('metrics', {})
            for key, value in metrics.items():
                if isinstance(value, (int, float, Decimal)):
                    if 'total_' in key or 'sum_' in key:
                        summary_metrics[key] = summary_metrics.get(key, 0) + float(value)
                    elif 'avg_' in key:
                        # For averages, we'll recalculate at the end
                        pass
            
            total_rows += item.get('row_count', 0)
        
        # Calculate overall averages
        for key in list(summary_metrics.keys()):
            if key.startswith('total_'):
                avg_key = key.replace('total_', 'avg_')
                if len(data) > 0:
                    summary_metrics[avg_key] = summary_metrics[key] / len(data)
        
        summary_metrics['total_rows'] = total_rows
        summary_metrics['weeks_included'] = len(data)
        
        return dict(summary_metrics)
    
    @with_connection_retry
    def calculate_comparison(
        self,
        period1_data: List[Dict],
        period2_data: List[Dict],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate comparison between two periods
        
        Args:
            period1_data: Data for first period
            period2_data: Data for second period
            metrics: List of metrics to compare
            
        Returns:
            Comparison results with deltas and percentages
        """
        period1_metrics = self._aggregate_metrics(period1_data, metrics)
        period2_metrics = self._aggregate_metrics(period2_data, metrics)
        
        delta = {}
        for metric in metrics:
            val1 = period1_metrics.get(metric, 0)
            val2 = period2_metrics.get(metric, 0)
            
            delta[metric] = {
                'value': val2 - val1,
                'percent': ((val2 - val1) / val1 * 100) if val1 != 0 else 0
            }
        
        return {
            'period1': period1_metrics,
            'period2': period2_metrics,
            'delta': delta
        }
    
    def _aggregate_metrics(self, data: List[Dict], metrics: List[str]) -> Dict[str, float]:
        """Aggregate specific metrics from data"""
        aggregated = {metric: 0 for metric in metrics}
        
        for item in data:
            for metric in metrics:
                if metric in item:
                    aggregated[metric] += float(item[metric])
        
        return aggregated
    
    def aggregate_data(
        self,
        data: List[Dict],
        aggregation_type: str = 'sum'
    ) -> Dict[str, Any]:
        """
        Aggregate data using specified method
        
        Args:
            data: List of data dictionaries
            aggregation_type: 'sum', 'avg', 'min', or 'max'
            
        Returns:
            Aggregated results
        """
        if not data:
            return {}
        
        # Collect all numeric values by key
        metrics = defaultdict(list)
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float, Decimal)):
                    metrics[key].append(float(value))
        
        # Apply aggregation
        result = {}
        for key, values in metrics.items():
            if aggregation_type == 'sum':
                result[key] = sum(values)
            elif aggregation_type == 'avg':
                result[key] = sum(values) / len(values) if values else 0
            elif aggregation_type == 'min':
                result[key] = min(values) if values else 0
            elif aggregation_type == 'max':
                result[key] = max(values) if values else 0
        
        return result
    
    def transform_for_chart(
        self,
        data: List[Dict],
        chart_type: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Transform data into Chart.js format
        
        Args:
            data: Raw data to transform
            chart_type: Type of chart ('line', 'bar', 'area', etc.)
            metrics: List of metrics to include
            
        Returns:
            Chart.js formatted data
        """
        labels = []
        datasets = []
        
        # Extract labels (dates)
        for item in data:
            if 'week_start' in item:
                labels.append(item['week_start'])
            elif 'week_start_date' in item:
                labels.append(item['week_start_date'])
        
        # Create dataset for each metric
        for i, metric in enumerate(metrics):
            dataset_data = []
            
            for item in data:
                # Look for metric in different possible locations
                value = None
                if 'metrics' in item and metric in item['metrics']:
                    value = item['metrics'][metric]
                elif 'summary_stats' in item and f'total_{metric}' in item['summary_stats']:
                    value = item['summary_stats'][f'total_{metric}']
                elif 'summary_stats' in item and metric in item['summary_stats']:
                    value = item['summary_stats'][metric]
                elif metric in item:
                    value = item[metric]
                
                dataset_data.append(float(value) if value is not None else 0)
            
            color = self.default_colors[i % len(self.default_colors)]
            
            dataset = {
                'label': metric,
                'data': dataset_data,
                'borderColor': color,
                'backgroundColor': self._get_background_color(color, chart_type),
                'tension': 0.1 if chart_type == 'line' else 0
            }
            
            # Add specific properties based on chart type
            if chart_type == 'area':
                dataset['fill'] = True
            elif chart_type == 'bar':
                dataset['backgroundColor'] = color
            
            datasets.append(dataset)
        
        return {
            'labels': labels,
            'datasets': datasets
        }
    
    def _get_background_color(self, color: str, chart_type: str) -> str:
        """Get appropriate background color based on chart type"""
        if chart_type in ['area', 'line']:
            # Create semi-transparent version for area fills
            # This is a simple approach - in production you might want to use a proper color library
            return color + '20'  # Add alpha channel
        return color
    
    @with_connection_retry
    def save_report_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a report configuration"""
        try:
            response = self.client.table('collection_report_configs')\
                .insert(config_data)\
                .execute()
            
            if response.data:
                logger.info(f"Saved report config: {response.data[0].get('id')}")
                return response.data[0]
            
            raise ValueError("Failed to save report configuration")
            
        except Exception as e:
            logger.error(f"Error saving report config: {e}")
            raise
    
    @with_connection_retry
    def get_report_configs(
        self,
        collection_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get saved report configurations for a collection"""
        try:
            response = self.client.table('collection_report_configs')\
                .select('*')\
                .eq('collection_id', collection_id)\
                .eq('user_id', user_id)\
                .order('updated_at', desc=True)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error fetching report configs: {e}")
            return []
    
    @with_connection_retry
    def create_snapshot(self, snapshot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a report snapshot"""
        try:
            # Generate snapshot ID if not provided
            if 'snapshot_id' not in snapshot_data:
                snapshot_data['snapshot_id'] = f"snap_{uuid.uuid4().hex[:8]}"
            
            response = self.client.table('collection_report_snapshots')\
                .insert(snapshot_data)\
                .execute()
            
            if response.data:
                logger.info(f"Created snapshot: {response.data[0].get('snapshot_id')}")
                return response.data[0]
            
            raise ValueError("Failed to create snapshot")
            
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            raise
    
    @with_connection_retry
    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Get a report snapshot by ID"""
        try:
            response = self.client.table('collection_report_snapshots')\
                .select('*')\
                .eq('snapshot_id', snapshot_id)\
                .execute()
            
            if response.data:
                # Increment access count
                self.client.table('collection_report_snapshots')\
                    .update({'access_count': response.data[0]['access_count'] + 1})\
                    .eq('snapshot_id', snapshot_id)\
                    .execute()
                
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching snapshot: {e}")
            return None
    
    @with_connection_retry
    def update_summary_stats(self, week_id: str, stats: Dict[str, Any]) -> bool:
        """Update summary statistics for a week"""
        try:
            response = self.client.table('report_data_weeks')\
                .update({'summary_stats': stats})\
                .eq('id', week_id)\
                .execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error updating summary stats: {e}")
            return False
    
    def calculate_summary_stats(self, week_data: List[Dict]) -> Dict[str, float]:
        """Calculate summary statistics from week data"""
        if not week_data:
            return {}
        
        total_impressions = 0
        total_clicks = 0
        total_spend = 0
        
        for week in week_data:
            if 'summary_stats' in week:
                stats = week['summary_stats']
                total_impressions += stats.get('total_impressions', 0)
                total_clicks += stats.get('total_clicks', 0)
                total_spend += stats.get('total_spend', 0)
        
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        
        return {
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'total_spend': total_spend,
            'avg_ctr': round(avg_ctr, 4)
        }


# Create singleton instance
report_dashboard_service = ReportDashboardService()