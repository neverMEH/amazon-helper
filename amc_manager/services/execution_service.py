"""Execution tracking and monitoring service"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from ..core import AMCAPIClient, AMCAPIEndpoints, get_logger
from ..core.exceptions import APIError, WorkflowError


logger = get_logger(__name__)


class ExecutionStatus(Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ExecutionTrackingService:
    """Service for tracking and monitoring workflow executions"""
    
    def __init__(self, api_client: AMCAPIClient):
        """
        Initialize execution tracking service
        
        Args:
            api_client: Configured AMC API client
        """
        self.api_client = api_client
        self._polling_tasks = {}
        
    async def get_execution_status(
        self,
        instance_id: str,
        execution_id: str,
        user_id: str,
        user_token: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get current status of an execution
        
        Args:
            instance_id: AMC instance ID
            execution_id: Execution ID
            user_id: User identifier
            user_token: User's auth token
            
        Returns:
            Execution status details
        """
        try:
            endpoint = AMCAPIEndpoints.EXECUTION_STATUS.format(
                instance_id=instance_id,
                execution_id=execution_id
            )
            
            response = self.api_client.get(
                endpoint,
                user_id,
                user_token
            )
            
            # Enrich status data
            status_data = {
                'executionId': execution_id,
                'status': response.get('status', ExecutionStatus.PENDING.value),
                'progress': response.get('progress', 0),
                'startedAt': response.get('startedAt'),
                'completedAt': response.get('completedAt'),
                'error': response.get('error'),
                'outputLocation': response.get('outputLocation'),
                'rowCount': response.get('rowCount'),
                'duration': self._calculate_duration(
                    response.get('startedAt'),
                    response.get('completedAt')
                )
            }
            
            logger.info(f"Retrieved status for execution {execution_id}: {status_data['status']}")
            return status_data
            
        except APIError as e:
            logger.error(f"Failed to get execution status: {e}")
            raise
            
    async def list_executions(
        self,
        instance_id: str,
        user_id: str,
        user_token: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List executions for an instance
        
        Args:
            instance_id: AMC instance ID
            user_id: User identifier
            user_token: User's auth token
            filters: Optional filters (workflow_id, status, date range)
            
        Returns:
            List of executions
        """
        try:
            endpoint = AMCAPIEndpoints.EXECUTIONS.format(instance_id=instance_id)
            params = filters or {}
            
            response = self.api_client.get(
                endpoint,
                user_id,
                user_token,
                params=params
            )
            
            executions = response.get('executions', [])
            
            # Enrich execution data
            for execution in executions:
                execution['duration'] = self._calculate_duration(
                    execution.get('startedAt'),
                    execution.get('completedAt')
                )
                execution['isSuccess'] = execution.get('status') == ExecutionStatus.COMPLETED.value
                
            logger.info(f"Retrieved {len(executions)} executions for instance {instance_id}")
            return executions
            
        except APIError as e:
            logger.error(f"Failed to list executions: {e}")
            raise
            
    async def get_execution_history(
        self,
        instance_id: str,
        workflow_id: str,
        user_id: str,
        user_token: Dict[str, Any],
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get execution history for a specific workflow
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Workflow ID
            user_id: User identifier
            user_token: User's auth token
            limit: Maximum number of executions to retrieve
            
        Returns:
            Execution history with statistics
        """
        try:
            # Get executions for the workflow
            executions = await self.list_executions(
                instance_id,
                user_id,
                user_token,
                filters={
                    'workflowId': workflow_id,
                    'limit': limit
                }
            )
            
            # Calculate statistics
            total_executions = len(executions)
            successful_executions = sum(1 for e in executions if e.get('isSuccess'))
            failed_executions = sum(1 for e in executions if e.get('status') == ExecutionStatus.FAILED.value)
            
            # Calculate average duration for successful executions
            durations = [e['duration'] for e in executions if e.get('isSuccess') and e['duration']]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Get last execution details
            last_execution = executions[0] if executions else None
            
            history = {
                'workflowId': workflow_id,
                'totalExecutions': total_executions,
                'successfulExecutions': successful_executions,
                'failedExecutions': failed_executions,
                'successRate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                'averageDuration': avg_duration,
                'lastExecution': last_execution,
                'executions': executions
            }
            
            logger.info(f"Retrieved history for workflow {workflow_id}: {total_executions} executions")
            return history
            
        except APIError as e:
            logger.error(f"Failed to get execution history: {e}")
            raise
            
    async def monitor_execution(
        self,
        instance_id: str,
        execution_id: str,
        user_id: str,
        user_token: Dict[str, Any],
        polling_interval: int = 10,
        timeout: int = 3600
    ) -> Dict[str, Any]:
        """
        Monitor an execution until completion
        
        Args:
            instance_id: AMC instance ID
            execution_id: Execution ID
            user_id: User identifier
            user_token: User's auth token
            polling_interval: Seconds between status checks
            timeout: Maximum seconds to wait
            
        Returns:
            Final execution status
        """
        start_time = datetime.utcnow()
        timeout_delta = timedelta(seconds=timeout)
        
        logger.info(f"Starting monitoring for execution {execution_id}")
        
        while True:
            # Check timeout
            if datetime.utcnow() - start_time > timeout_delta:
                logger.warning(f"Execution {execution_id} timed out after {timeout} seconds")
                return {
                    'executionId': execution_id,
                    'status': ExecutionStatus.TIMEOUT.value,
                    'error': f'Execution monitoring timed out after {timeout} seconds'
                }
                
            # Get current status
            status = await self.get_execution_status(
                instance_id,
                execution_id,
                user_id,
                user_token
            )
            
            # Check if execution is complete
            if status['status'] in [
                ExecutionStatus.COMPLETED.value,
                ExecutionStatus.FAILED.value,
                ExecutionStatus.CANCELLED.value
            ]:
                logger.info(f"Execution {execution_id} completed with status: {status['status']}")
                return status
                
            # Wait before next check
            await asyncio.sleep(polling_interval)
            
    async def cancel_execution(
        self,
        instance_id: str,
        execution_id: str,
        user_id: str,
        user_token: Dict[str, Any]
    ) -> bool:
        """
        Cancel a running execution
        
        Args:
            instance_id: AMC instance ID
            execution_id: Execution ID
            user_id: User identifier
            user_token: User's auth token
            
        Returns:
            True if cancellation was successful
        """
        try:
            endpoint = AMCAPIEndpoints.EXECUTION_DETAIL.format(
                instance_id=instance_id,
                execution_id=execution_id
            )
            
            response = self.api_client.patch(
                endpoint,
                user_id,
                user_token,
                json_data={'status': ExecutionStatus.CANCELLED.value}
            )
            
            logger.info(f"Cancelled execution {execution_id}")
            return True
            
        except APIError as e:
            logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False
            
    async def get_execution_metrics(
        self,
        instance_id: str,
        user_id: str,
        user_token: Dict[str, Any],
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get execution metrics for an instance
        
        Args:
            instance_id: AMC instance ID
            user_id: User identifier
            user_token: User's auth token
            time_range_days: Number of days to analyze
            
        Returns:
            Execution metrics and statistics
        """
        # Get executions for the time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range_days)
        
        executions = await self.list_executions(
            instance_id,
            user_id,
            user_token,
            filters={
                'startDate': start_date.isoformat(),
                'endDate': end_date.isoformat()
            }
        )
        
        # Calculate metrics
        total = len(executions)
        successful = sum(1 for e in executions if e.get('status') == ExecutionStatus.COMPLETED.value)
        failed = sum(1 for e in executions if e.get('status') == ExecutionStatus.FAILED.value)
        
        # Group by date for trend analysis
        daily_stats = {}
        for execution in executions:
            if execution.get('startedAt'):
                date_key = execution['startedAt'][:10]  # YYYY-MM-DD
                if date_key not in daily_stats:
                    daily_stats[date_key] = {'total': 0, 'successful': 0, 'failed': 0}
                    
                daily_stats[date_key]['total'] += 1
                if execution.get('status') == ExecutionStatus.COMPLETED.value:
                    daily_stats[date_key]['successful'] += 1
                elif execution.get('status') == ExecutionStatus.FAILED.value:
                    daily_stats[date_key]['failed'] += 1
                    
        metrics = {
            'instanceId': instance_id,
            'timeRange': f'{time_range_days} days',
            'totalExecutions': total,
            'successfulExecutions': successful,
            'failedExecutions': failed,
            'successRate': (successful / total * 100) if total > 0 else 0,
            'dailyStats': daily_stats,
            'topErrors': self._get_top_errors(executions)
        }
        
        logger.info(f"Generated metrics for instance {instance_id}: {total} executions in {time_range_days} days")
        return metrics
        
    def _calculate_duration(self, started_at: Optional[str], completed_at: Optional[str]) -> Optional[int]:
        """Calculate execution duration in seconds"""
        if not started_at or not completed_at:
            return None
            
        try:
            start = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            end = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            return int((end - start).total_seconds())
        except Exception:
            return None
            
    def _get_top_errors(self, executions: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Extract top error messages from failed executions"""
        error_counts = {}
        
        for execution in executions:
            if execution.get('status') == ExecutionStatus.FAILED.value and execution.get('error'):
                error = execution['error']
                error_counts[error] = error_counts.get(error, 0) + 1
                
        # Sort by count and return top errors
        top_errors = sorted(
            [{'error': k, 'count': v} for k, v in error_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:limit]
        
        return top_errors