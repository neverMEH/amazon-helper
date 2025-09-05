"""Data Aggregation Service - Pre-computes metrics for fast dashboard queries"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
import json
from ..core.logger_simple import get_logger
from .reporting_database_service import reporting_db_service
from .db_service import db_service

logger = get_logger(__name__)


class DataAggregationService:
    """Service for computing and managing aggregated reporting data"""
    
    def __init__(self):
        self.db = db_service
        self.reporting_db = reporting_db_service
        
        # Common AMC metrics for aggregation
        self.STANDARD_METRICS = [
            'impressions',
            'clicks', 
            'conversions',
            'spend',
            'sales',
            'units_sold',
            'new_to_brand',
            'new_to_brand_sales',
            'view_through_conversions',
            'click_through_conversions'
        ]
        
        # Calculated metrics
        self.CALCULATED_METRICS = {
            'ctr': 'clicks / NULLIF(impressions, 0)',  # Click-through rate
            'cvr': 'conversions / NULLIF(clicks, 0)',  # Conversion rate
            'acos': 'spend / NULLIF(sales, 0)',  # Advertising cost of sales
            'roas': 'sales / NULLIF(spend, 0)',  # Return on ad spend
            'cpc': 'spend / NULLIF(clicks, 0)',  # Cost per click
            'cpm': '(spend / NULLIF(impressions, 0)) * 1000',  # Cost per mille
            'units_per_order': 'units_sold / NULLIF(conversions, 0)'
        }
    
    async def compute_weekly_aggregates(
        self,
        workflow_execution_id: str,
        execution_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute weekly aggregates from workflow execution results
        
        Args:
            workflow_execution_id: Execution UUID
            execution_results: Raw results from AMC execution
            
        Returns:
            Aggregated metrics for the week
        """
        try:
            # Get execution details
            execution = self.db.client.table('workflow_executions')\
                .select('*, workflows(*)')\
                .eq('id', workflow_execution_id)\
                .single()\
                .execute()
            
            if not execution.data:
                logger.error(f"Execution {workflow_execution_id} not found")
                return {}
            
            execution_data = execution.data
            workflow = execution_data.get('workflows', {})
            
            # Determine date range from execution parameters
            params = execution_data.get('execution_parameters', {})
            start_date = self._parse_date(params.get('startDate'))
            end_date = self._parse_date(params.get('endDate'))
            
            if not start_date or not end_date:
                logger.warning("Could not determine date range for aggregation")
                return {}
            
            # Compute base metrics
            base_metrics = self._compute_base_metrics(execution_results)
            
            # Compute calculated metrics
            calculated_metrics = self._compute_calculated_metrics(base_metrics)
            
            # Combine all metrics
            all_metrics = {**base_metrics, **calculated_metrics}
            
            # Extract dimensions (campaigns, ASINs, etc.)
            dimensions = self._extract_dimensions(execution_results)
            
            # Create aggregation record
            aggregate_data = {
                'workflow_id': workflow['id'],
                'instance_id': execution_data['instance_id'],
                'aggregation_type': 'weekly',
                'aggregation_key': f"{start_date}_{end_date}",
                'metrics': all_metrics,
                'dimensions': dimensions,
                'data_date': end_date,
                'row_count': len(execution_results)
            }
            
            # Store in database
            stored = self.reporting_db.create_or_update_aggregate(aggregate_data)
            
            if stored:
                logger.info(f"Stored weekly aggregate for {start_date} to {end_date}")
                return all_metrics
            else:
                logger.error("Failed to store aggregate")
                return {}
                
        except Exception as e:
            logger.error(f"Error computing weekly aggregates: {e}")
            return {}
    
    async def compute_monthly_aggregates(
        self,
        workflow_id: str,
        instance_id: str,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        Compute monthly aggregates from weekly data
        
        Args:
            workflow_id: Workflow UUID
            instance_id: Instance UUID
            year: Year for aggregation
            month: Month for aggregation
            
        Returns:
            Aggregated metrics for the month
        """
        try:
            # Get all weekly aggregates for the month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            weekly_aggregates = self.reporting_db.get_aggregates_for_dashboard(
                workflow_id,
                instance_id,
                'weekly',
                start_date,
                end_date
            )
            
            if not weekly_aggregates:
                logger.warning(f"No weekly data found for {year}-{month:02d}")
                return {}
            
            # Combine weekly metrics
            combined_metrics = self._combine_aggregates(weekly_aggregates)
            
            # Create monthly aggregate record
            aggregate_data = {
                'workflow_id': workflow_id,
                'instance_id': instance_id,
                'aggregation_type': 'monthly',
                'aggregation_key': f"{year}-{month:02d}",
                'metrics': combined_metrics,
                'dimensions': self._combine_dimensions(weekly_aggregates),
                'data_date': end_date,
                'row_count': sum(agg.get('row_count', 0) for agg in weekly_aggregates)
            }
            
            # Store in database
            stored = self.reporting_db.create_or_update_aggregate(aggregate_data)
            
            if stored:
                logger.info(f"Stored monthly aggregate for {year}-{month:02d}")
                return combined_metrics
            else:
                logger.error("Failed to store monthly aggregate")
                return {}
                
        except Exception as e:
            logger.error(f"Error computing monthly aggregates: {e}")
            return {}
    
    def _compute_base_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute base metrics from raw results"""
        metrics = {}
        
        for metric in self.STANDARD_METRICS:
            total = 0
            count = 0
            
            for row in results:
                if metric in row:
                    value = row[metric]
                    if value is not None:
                        try:
                            total += float(value)
                            count += 1
                        except (ValueError, TypeError):
                            continue
            
            if count > 0:
                metrics[metric] = round(total, 2)
            else:
                metrics[metric] = 0
        
        return metrics
    
    def _compute_calculated_metrics(self, base_metrics: Dict[str, float]) -> Dict[str, float]:
        """Compute calculated metrics like ROAS, ACOS, CTR"""
        calculated = {}
        
        # Click-through rate
        if base_metrics.get('impressions', 0) > 0:
            calculated['ctr'] = round(
                (base_metrics.get('clicks', 0) / base_metrics['impressions']) * 100, 
                2
            )
        else:
            calculated['ctr'] = 0
        
        # Conversion rate
        if base_metrics.get('clicks', 0) > 0:
            calculated['cvr'] = round(
                (base_metrics.get('conversions', 0) / base_metrics['clicks']) * 100,
                2
            )
        else:
            calculated['cvr'] = 0
        
        # ACOS (Advertising Cost of Sales)
        if base_metrics.get('sales', 0) > 0:
            calculated['acos'] = round(
                (base_metrics.get('spend', 0) / base_metrics['sales']) * 100,
                2
            )
        else:
            calculated['acos'] = 0
        
        # ROAS (Return on Ad Spend)
        if base_metrics.get('spend', 0) > 0:
            calculated['roas'] = round(
                base_metrics.get('sales', 0) / base_metrics['spend'],
                2
            )
        else:
            calculated['roas'] = 0
        
        # Cost per click
        if base_metrics.get('clicks', 0) > 0:
            calculated['cpc'] = round(
                base_metrics.get('spend', 0) / base_metrics['clicks'],
                2
            )
        else:
            calculated['cpc'] = 0
        
        # Cost per mille (CPM)
        if base_metrics.get('impressions', 0) > 0:
            calculated['cpm'] = round(
                (base_metrics.get('spend', 0) / base_metrics['impressions']) * 1000,
                2
            )
        else:
            calculated['cpm'] = 0
        
        # Units per order
        if base_metrics.get('conversions', 0) > 0:
            calculated['units_per_order'] = round(
                base_metrics.get('units_sold', 0) / base_metrics['conversions'],
                2
            )
        else:
            calculated['units_per_order'] = 0
        
        # New to brand percentage
        if base_metrics.get('conversions', 0) > 0:
            calculated['ntb_percentage'] = round(
                (base_metrics.get('new_to_brand', 0) / base_metrics['conversions']) * 100,
                2
            )
        else:
            calculated['ntb_percentage'] = 0
        
        return calculated
    
    def _extract_dimensions(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract dimension values from results (campaigns, ASINs, etc.)"""
        dimensions = {
            'campaigns': set(),
            'asins': set(),
            'keywords': set(),
            'placements': set(),
            'audiences': set()
        }
        
        for row in results:
            # Extract campaign IDs
            if 'campaign_id' in row and row['campaign_id']:
                dimensions['campaigns'].add(str(row['campaign_id']))
            
            # Extract ASINs
            if 'asin' in row and row['asin']:
                dimensions['asins'].add(row['asin'])
            elif 'product_asin' in row and row['product_asin']:
                dimensions['asins'].add(row['product_asin'])
            
            # Extract keywords
            if 'keyword' in row and row['keyword']:
                dimensions['keywords'].add(row['keyword'])
            
            # Extract placements
            if 'placement' in row and row['placement']:
                dimensions['placements'].add(row['placement'])
            
            # Extract audiences
            if 'audience_id' in row and row['audience_id']:
                dimensions['audiences'].add(str(row['audience_id']))
        
        # Convert sets to lists for JSON storage
        return {
            'campaigns': list(dimensions['campaigns'])[:100],  # Limit to 100
            'asins': list(dimensions['asins'])[:100],
            'keywords': list(dimensions['keywords'])[:100],
            'placements': list(dimensions['placements'])[:50],
            'audiences': list(dimensions['audiences'])[:50],
            'total_campaigns': len(dimensions['campaigns']),
            'total_asins': len(dimensions['asins']),
            'total_keywords': len(dimensions['keywords'])
        }
    
    def _combine_aggregates(self, aggregates: List[Dict[str, Any]]) -> Dict[str, float]:
        """Combine multiple aggregates (e.g., weekly into monthly)"""
        combined = {}
        
        # Sum up base metrics
        for metric in self.STANDARD_METRICS:
            total = 0
            for agg in aggregates:
                metrics = agg.get('metrics', {})
                if metric in metrics:
                    total += metrics[metric]
            combined[metric] = round(total, 2)
        
        # Recalculate derived metrics
        combined.update(self._compute_calculated_metrics(combined))
        
        return combined
    
    def _combine_dimensions(self, aggregates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine dimensions from multiple aggregates"""
        combined_dims = {
            'campaigns': set(),
            'asins': set(),
            'keywords': set(),
            'placements': set(),
            'audiences': set()
        }
        
        for agg in aggregates:
            dims = agg.get('dimensions', {})
            for key in combined_dims:
                if key in dims and isinstance(dims[key], list):
                    combined_dims[key].update(dims[key])
        
        # Convert to lists and limit size
        return {
            'campaigns': list(combined_dims['campaigns'])[:200],
            'asins': list(combined_dims['asins'])[:200],
            'keywords': list(combined_dims['keywords'])[:200],
            'placements': list(combined_dims['placements'])[:100],
            'audiences': list(combined_dims['audiences'])[:100],
            'total_campaigns': len(combined_dims['campaigns']),
            'total_asins': len(combined_dims['asins']),
            'total_keywords': len(combined_dims['keywords'])
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y/%m/%d']:
                try:
                    return datetime.strptime(date_str[:10], fmt[:10]).date()
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return None
    
    async def update_incremental_aggregates(
        self,
        workflow_id: str,
        instance_id: str,
        new_execution_id: str
    ) -> bool:
        """
        Update aggregates incrementally when new data arrives
        
        Args:
            workflow_id: Workflow UUID
            instance_id: Instance UUID
            new_execution_id: New execution to incorporate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the new execution data
            execution = self.db.client.table('workflow_executions')\
                .select('*')\
                .eq('id', new_execution_id)\
                .single()\
                .execute()
            
            if not execution.data:
                logger.error(f"Execution {new_execution_id} not found")
                return False
            
            # Get the results
            results = execution.data.get('result_data', {}).get('results', [])
            if not results:
                logger.warning("No results to aggregate")
                return True  # Not an error, just no data
            
            # Compute aggregates for this execution
            aggregates = await self.compute_weekly_aggregates(
                new_execution_id,
                results
            )
            
            return bool(aggregates)
            
        except Exception as e:
            logger.error(f"Error updating incremental aggregates: {e}")
            return False
    
    async def get_metric_trends(
        self,
        workflow_id: str,
        instance_id: str,
        metric_name: str,
        start_date: date,
        end_date: date,
        aggregation_type: str = 'weekly'
    ) -> List[Tuple[date, float]]:
        """
        Get trend data for a specific metric
        
        Args:
            workflow_id: Workflow UUID
            instance_id: Instance UUID
            metric_name: Name of the metric (e.g., 'roas', 'acos')
            start_date: Start date for trend
            end_date: End date for trend
            aggregation_type: Type of aggregation ('weekly' or 'monthly')
            
        Returns:
            List of (date, value) tuples
        """
        try:
            aggregates = self.reporting_db.get_aggregates_for_dashboard(
                workflow_id,
                instance_id,
                aggregation_type,
                start_date,
                end_date
            )
            
            trends = []
            for agg in aggregates:
                metrics = agg.get('metrics', {})
                if metric_name in metrics:
                    data_date = datetime.fromisoformat(agg['data_date']).date()
                    value = metrics[metric_name]
                    trends.append((data_date, value))
            
            # Sort by date
            trends.sort(key=lambda x: x[0])
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting metric trends: {e}")
            return []
    
    async def cleanup_stale_aggregates(self, days_to_keep: int = 365) -> int:
        """
        Clean up old aggregated data
        
        Args:
            days_to_keep: Keep aggregates from last N days
            
        Returns:
            Number of records cleaned up
        """
        try:
            return self.reporting_db.cleanup_old_aggregates(days_to_keep)
        except Exception as e:
            logger.error(f"Error cleaning up aggregates: {e}")
            return 0


# Create singleton instance
data_aggregation_service = DataAggregationService()