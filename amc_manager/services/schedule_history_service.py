"""Service for managing schedule execution history"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..core.logger_simple import get_logger
from .db_service import DatabaseService

logger = get_logger(__name__)


class ScheduleHistoryService(DatabaseService):
    """Service for managing schedule execution history and metrics"""
    
    def __init__(self):
        """Initialize the schedule history service"""
        super().__init__()
    
    def get_schedule_runs(
        self,
        schedule_id: str,
        limit: int = 30,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get paginated schedule run history
        
        Args:
            schedule_id: Schedule ID
            limit: Maximum number of records
            offset: Pagination offset
            status: Optional status filter
            
        Returns:
            List of schedule run records
        """
        try:
            query = self.client.table('schedule_runs').select(
                '*',
                'workflow_executions(*)'
            ).eq('schedule_id', schedule_id)
            
            if status:
                query = query.eq('status', status)
            
            query = query.order('scheduled_at', desc=True)
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting schedule runs: {e}")
            return []
    
    def get_run_executions(
        self,
        run_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all executions for a schedule run
        
        Args:
            run_id: Schedule run ID
            
        Returns:
            List of execution records
        """
        try:
            result = self.client.table('workflow_executions').select(
                '*',
                'workflows(name, workflow_id)'
            ).eq('schedule_run_id', run_id).execute()
            
            executions = result.data or []
            
            # Parse JSON fields
            for execution in executions:
                if isinstance(execution.get('parameters'), str):
                    execution['parameters'] = json.loads(execution['parameters'])
                if isinstance(execution.get('results'), str):
                    execution['results'] = json.loads(execution['results'])
                if isinstance(execution.get('error_details'), str):
                    execution['error_details'] = json.loads(execution['error_details'])
            
            return executions
            
        except Exception as e:
            logger.error(f"Error getting run executions: {e}")
            return []
    
    def get_schedule_metrics(
        self,
        schedule_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get schedule performance metrics
        
        Args:
            schedule_id: Schedule ID
            period_days: Period in days for metrics calculation
            
        Returns:
            Dictionary of metrics
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            # Get all runs within period
            result = self.client.table('schedule_runs').select('*').eq(
                'schedule_id', schedule_id
            ).gte('scheduled_at', cutoff_date.isoformat()).execute()
            
            runs = result.data or []
            
            # Calculate basic metrics
            total_runs = len(runs)
            successful_runs = sum(1 for r in runs if r['status'] == 'completed')
            failed_runs = sum(1 for r in runs if r['status'] == 'failed')
            pending_runs = sum(1 for r in runs if r['status'] == 'pending')
            running_runs = sum(1 for r in runs if r['status'] == 'running')
            
            # Calculate success rate
            success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
            
            # Calculate average runtime for successful runs
            runtimes = []
            for run in runs:
                if run['status'] == 'completed' and run.get('started_at') and run.get('completed_at'):
                    start = self._parse_datetime(run['started_at'])
                    end = self._parse_datetime(run['completed_at'])
                    if start and end:
                        runtimes.append((end - start).total_seconds())
            
            avg_runtime_seconds = sum(runtimes) / len(runtimes) if runtimes else None
            
            # Calculate totals
            total_rows_processed = sum(r.get('total_rows', 0) for r in runs)
            total_cost = sum(r.get('total_cost', 0) for r in runs)
            
            # Get schedule details for next/last run
            schedule_result = self.client.table('workflow_schedules').select('*').eq(
                'id', schedule_id
            ).single().execute()
            
            schedule = schedule_result.data if schedule_result.data else {}
            
            return {
                'schedule_id': schedule_id,
                'period_days': period_days,
                'total_runs': total_runs,
                'successful_runs': successful_runs,
                'failed_runs': failed_runs,
                'pending_runs': pending_runs,
                'running_runs': running_runs,
                'success_rate': round(success_rate, 2),
                'avg_runtime_seconds': round(avg_runtime_seconds, 2) if avg_runtime_seconds else None,
                'total_rows_processed': total_rows_processed,
                'total_cost': round(total_cost, 2),
                'next_run': schedule.get('next_run_at'),
                'last_run': schedule.get('last_run_at'),
                'first_run_in_period': min((r['scheduled_at'] for r in runs), default=None),
                'last_run_in_period': max((r['scheduled_at'] for r in runs), default=None)
            }
            
        except Exception as e:
            logger.error(f"Error getting schedule metrics: {e}")
            return {
                'schedule_id': schedule_id,
                'period_days': period_days,
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'pending_runs': 0,
                'running_runs': 0,
                'success_rate': 0.0,
                'avg_runtime_seconds': None,
                'total_rows_processed': 0,
                'total_cost': 0.0,
                'next_run': None,
                'last_run': None,
                'error': str(e)
            }
    
    def compare_periods(
        self,
        schedule_id: str,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> Dict[str, Any]:
        """
        Compare metrics between two periods
        
        Args:
            schedule_id: Schedule ID
            period1_start: Start of first period
            period1_end: End of first period
            period2_start: Start of second period
            period2_end: End of second period
            
        Returns:
            Comparison metrics
        """
        try:
            # Get runs for period 1
            period1_result = self.client.table('schedule_runs').select('*').eq(
                'schedule_id', schedule_id
            ).gte('scheduled_at', period1_start.isoformat()).lte(
                'scheduled_at', period1_end.isoformat()
            ).execute()
            
            period1_runs = period1_result.data or []
            
            # Get runs for period 2
            period2_result = self.client.table('schedule_runs').select('*').eq(
                'schedule_id', schedule_id
            ).gte('scheduled_at', period2_start.isoformat()).lte(
                'scheduled_at', period2_end.isoformat()
            ).execute()
            
            period2_runs = period2_result.data or []
            
            # Calculate metrics for each period
            def calculate_period_metrics(runs):
                total = len(runs)
                successful = sum(1 for r in runs if r['status'] == 'completed')
                failed = sum(1 for r in runs if r['status'] == 'failed')
                success_rate = (successful / total * 100) if total > 0 else 0
                total_rows = sum(r.get('total_rows', 0) for r in runs)
                total_cost = sum(r.get('total_cost', 0) for r in runs)
                
                return {
                    'total_runs': total,
                    'successful_runs': successful,
                    'failed_runs': failed,
                    'success_rate': round(success_rate, 2),
                    'total_rows': total_rows,
                    'total_cost': round(total_cost, 2)
                }
            
            period1_metrics = calculate_period_metrics(period1_runs)
            period2_metrics = calculate_period_metrics(period2_runs)
            
            # Calculate changes
            changes = {}
            for key in period1_metrics.keys():
                if isinstance(period1_metrics[key], (int, float)):
                    change = period2_metrics[key] - period1_metrics[key]
                    change_pct = (change / period1_metrics[key] * 100) if period1_metrics[key] != 0 else 0
                    changes[f'{key}_change'] = round(change, 2)
                    changes[f'{key}_change_pct'] = round(change_pct, 2)
            
            return {
                'schedule_id': schedule_id,
                'period1': {
                    'start': period1_start.isoformat(),
                    'end': period1_end.isoformat(),
                    **period1_metrics
                },
                'period2': {
                    'start': period2_start.isoformat(),
                    'end': period2_end.isoformat(),
                    **period2_metrics
                },
                'changes': changes
            }
            
        except Exception as e:
            logger.error(f"Error comparing periods: {e}")
            return {
                'schedule_id': schedule_id,
                'error': str(e)
            }
    
    def get_execution_timeline(
        self,
        schedule_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get execution timeline for visualization
        
        Args:
            schedule_id: Schedule ID
            days: Number of days to include
            
        Returns:
            Timeline data for visualization
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all runs and executions
            result = self.client.table('schedule_runs').select(
                '*',
                'workflow_executions(*)'
            ).eq('schedule_id', schedule_id).gte(
                'scheduled_at', cutoff_date.isoformat()
            ).order('scheduled_at', desc=False).execute()
            
            runs = result.data or []
            
            timeline = []
            for run in runs:
                executions = run.get('workflow_executions', [])
                
                timeline_entry = {
                    'run_id': run['id'],
                    'run_number': run['run_number'],
                    'scheduled_at': run['scheduled_at'],
                    'started_at': run.get('started_at'),
                    'completed_at': run.get('completed_at'),
                    'status': run['status'],
                    'execution_count': len(executions),
                    'duration_seconds': None
                }
                
                # Calculate duration
                if run.get('started_at') and run.get('completed_at'):
                    start = self._parse_datetime(run['started_at'])
                    end = self._parse_datetime(run['completed_at'])
                    if start and end:
                        timeline_entry['duration_seconds'] = (end - start).total_seconds()
                
                # Add execution details
                timeline_entry['executions'] = [
                    {
                        'id': exec['id'],
                        'status': exec['status'],
                        'started_at': exec.get('started_at'),
                        'completed_at': exec.get('completed_at'),
                        'row_count': exec.get('row_count', 0)
                    }
                    for exec in executions
                ]
                
                timeline.append(timeline_entry)
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting execution timeline: {e}")
            return []
    
    def get_aggregated_results(
        self,
        schedule_id: str,
        aggregation_type: str = 'daily',
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated results for a schedule
        
        Args:
            schedule_id: Schedule ID
            aggregation_type: 'daily', 'weekly', or 'monthly'
            days: Number of days to aggregate
            
        Returns:
            Aggregated results
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all runs with executions
            result = self.client.table('schedule_runs').select(
                '*',
                'workflow_executions(results, row_count, status)'
            ).eq('schedule_id', schedule_id).gte(
                'scheduled_at', cutoff_date.isoformat()
            ).eq('status', 'completed').execute()
            
            runs = result.data or []
            
            # Aggregate by period
            aggregated = {}
            
            for run in runs:
                # Determine aggregation key
                scheduled_at = self._parse_datetime(run['scheduled_at'])
                if not scheduled_at:
                    continue
                
                if aggregation_type == 'daily':
                    key = scheduled_at.strftime('%Y-%m-%d')
                elif aggregation_type == 'weekly':
                    # Get week start (Monday)
                    week_start = scheduled_at - timedelta(days=scheduled_at.weekday())
                    key = week_start.strftime('%Y-%m-%d')
                elif aggregation_type == 'monthly':
                    key = scheduled_at.strftime('%Y-%m')
                else:
                    key = scheduled_at.strftime('%Y-%m-%d')
                
                # Initialize aggregation entry
                if key not in aggregated:
                    aggregated[key] = {
                        'period': key,
                        'run_count': 0,
                        'total_rows': 0,
                        'executions': []
                    }
                
                # Add run data
                aggregated[key]['run_count'] += 1
                
                for execution in run.get('workflow_executions', []):
                    if execution['status'] == 'SUCCEEDED':
                        aggregated[key]['total_rows'] += execution.get('row_count', 0)
                        aggregated[key]['executions'].append({
                            'run_id': run['id'],
                            'run_number': run['run_number'],
                            'rows': execution.get('row_count', 0)
                        })
            
            # Convert to list and sort
            result_list = list(aggregated.values())
            result_list.sort(key=lambda x: x['period'])
            
            return result_list
            
        except Exception as e:
            logger.error(f"Error getting aggregated results: {e}")
            return []
    
    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """
        Parse datetime string to datetime object
        
        Args:
            dt_str: Datetime string
            
        Returns:
            Datetime object or None
        """
        if not dt_str:
            return None
        
        try:
            # Handle different formats
            if 'Z' in dt_str:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            elif 'T' in dt_str:
                return datetime.fromisoformat(dt_str)
            else:
                return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return None