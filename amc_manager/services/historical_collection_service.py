"""Historical Data Collection Service - Manages 52-week backfill operations"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, date
import uuid
from ..core.logger_simple import get_logger
from .reporting_database_service import reporting_db_service
from .amc_execution_service import AMCExecutionService
from .db_service import db_service
import re

logger = get_logger(__name__)


class HistoricalCollectionService:
    """Service for managing historical data collection (52-week backfill)"""
    
    def __init__(self):
        self.db = db_service
        self.reporting_db = reporting_db_service
        self.amc_execution = AMCExecutionService()
        
        # Configuration
        self.MAX_WEEKS = 52  # Maximum weeks for backfill
        self.DELAY_BETWEEN_WEEKS = 2  # Seconds between week executions (rate limiting)
        self.MAX_RETRIES = 3  # Max retries for failed weeks
        self.AMC_DATA_LAG_DAYS = 14  # AMC data availability lag
    
    async def start_backfill(
        self,
        workflow_id: str,
        instance_id: str,
        user_id: str,
        target_weeks: int = 52,
        end_date: Optional[date] = None,
        collection_type: str = 'backfill'
    ) -> Dict[str, Any]:
        """
        Start a 52-week historical data backfill operation
        
        Args:
            workflow_id: UUID of the workflow to execute
            instance_id: AMC instance UUID
            user_id: User ID initiating the backfill
            target_weeks: Number of weeks to collect (max 52)
            end_date: End date for collection (defaults to 14 days ago)
            collection_type: Type of collection ('backfill' or 'weekly_update')
            
        Returns:
            Collection record with ID and initial status
        """
        try:
            # Validate inputs
            if target_weeks > self.MAX_WEEKS:
                target_weeks = self.MAX_WEEKS
                logger.warning(f"Target weeks capped at {self.MAX_WEEKS}")
            
            # Get workflow details
            workflow = self.db.get_workflow_by_id_sync(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Verify user has access
            if workflow['user_id'] != user_id:
                raise ValueError("Access denied to workflow")
            
            # Calculate date range (accounting for AMC data lag)
            if not end_date:
                end_date = date.today() - timedelta(days=self.AMC_DATA_LAG_DAYS)
            
            start_date = end_date - timedelta(weeks=target_weeks)
            
            logger.info(f"Starting {collection_type} for workflow {workflow_id}")
            logger.info(f"Date range: {start_date} to {end_date} ({target_weeks} weeks)")
            
            # Create collection record
            collection_data = {
                'workflow_id': workflow['id'],  # Internal UUID
                'instance_id': instance_id,
                'user_id': user_id,
                'collection_type': collection_type,
                'target_weeks': target_weeks,
                'start_date': start_date,
                'end_date': end_date,
                'status': 'pending',
                'configuration': {
                    'workflow_name': workflow['name'],
                    'instance_id_amc': workflow.get('amc_instances', {}).get('instance_id'),
                    'parameters': workflow.get('parameters', {})
                }
            }
            
            collection = self.reporting_db.create_collection(collection_data)
            if not collection:
                raise ValueError("Failed to create collection record")
            
            logger.info(f"Created collection {collection['collection_id']}")
            
            # Create week records for tracking
            await self._create_week_records(
                collection['id'],
                start_date,
                end_date,
                target_weeks
            )
            
            # Return collection info (actual execution happens in background)
            return {
                'collection_id': collection['collection_id'],
                'status': 'pending',
                'target_weeks': target_weeks,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'message': 'Collection queued for processing'
            }
            
        except Exception as e:
            logger.error(f"Error starting backfill: {e}")
            raise
    
    async def _create_week_records(
        self,
        collection_id: str,
        start_date: date,
        end_date: date,
        num_weeks: int
    ) -> None:
        """Create individual week records for tracking progress"""
        try:
            current_date = start_date
            week_count = 0
            
            while current_date < end_date and week_count < num_weeks:
                week_end = min(current_date + timedelta(days=6), end_date)
                
                week_data = {
                    'collection_id': collection_id,
                    'week_start_date': current_date,
                    'week_end_date': week_end,
                    'status': 'pending'
                }
                
                self.reporting_db.create_week_record(week_data)
                
                current_date = week_end + timedelta(days=1)
                week_count += 1
            
            logger.info(f"Created {week_count} week records for collection {collection_id}")
            
        except Exception as e:
            logger.error(f"Error creating week records: {e}")
            raise
    
    async def execute_collection_week(
        self,
        collection_id: str,
        week_record_id: str,
        week_start: date,
        week_end: date
    ) -> bool:
        """
        Execute workflow for a single week of data collection
        
        Args:
            collection_id: Collection UUID
            week_record_id: Week record UUID
            week_start: Start date of the week
            week_end: End date of the week
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get collection details
            collection = self.reporting_db.get_collection_status(collection_id)
            if not collection:
                logger.error(f"Collection {collection_id} not found")
                return False
            
            # Get workflow and instance details
            workflow = self.db.get_workflow_by_id_sync(collection['workflow_id'])
            if not workflow:
                logger.error(f"Workflow not found for collection {collection_id}")
                return False
            
            # Prepare parameters with date substitution
            parameters = collection['configuration'].get('parameters', {}).copy()
            
            # Substitute date parameters for this week
            parameters = self._substitute_date_parameters(
                parameters,
                week_start,
                week_end
            )
            
            logger.info(f"Executing week {week_start} to {week_end}")
            logger.info(f"Parameters: {parameters}")
            
            # Update week status to running
            self.reporting_db.update_week_status(
                week_record_id,
                'running',
                execution_date=datetime.now(timezone.utc)
            )
            
            # Execute workflow via AMC
            try:
                execution_result = await self.amc_execution.execute_workflow(
                    workflow_id=collection['workflow_id'],
                    user_id=collection['user_id'],
                    execution_parameters=parameters,
                    triggered_by='collection',
                    instance_id=collection['instance_id']
                )
                
                # Store execution ID in week record
                if execution_result and 'id' in execution_result:
                    # Calculate data checksum if results available
                    checksum = None
                    row_count = 0
                    
                    if 'results' in execution_result:
                        checksum = self.reporting_db.compute_data_checksum(
                            execution_result['results']
                        )
                        row_count = len(execution_result.get('results', []))
                    
                    # Update week record with success
                    self.reporting_db.update_week_status(
                        week_record_id,
                        'completed',
                        row_count=row_count,
                        data_checksum=checksum
                    )
                    
                    logger.info(f"Week {week_start} completed successfully")
                    return True
                else:
                    raise ValueError("No execution ID returned")
                    
            except Exception as exec_error:
                logger.error(f"AMC execution failed for week {week_start}: {exec_error}")
                
                # Update week record with failure
                self.reporting_db.update_week_status(
                    week_record_id,
                    'failed',
                    error_message=str(exec_error)
                )
                return False
            
        except Exception as e:
            logger.error(f"Error executing collection week: {e}")
            
            # Update week record with error
            self.reporting_db.update_week_status(
                week_record_id,
                'failed',
                error_message=str(e)
            )
            return False
    
    def _substitute_date_parameters(
        self,
        parameters: Dict[str, Any],
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Substitute date parameters with week-specific values
        
        Handles various date parameter patterns:
        - {{start_date}}, {{end_date}}
        - {{week_start}}, {{week_end}}
        - {{date_from}}, {{date_to}}
        """
        if not parameters:
            parameters = {}
        
        # Format dates for AMC (no timezone)
        start_str = start_date.strftime('%Y-%m-%dT00:00:00')
        end_str = end_date.strftime('%Y-%m-%dT23:59:59')
        
        # Create substitution map
        substitutions = {
            'start_date': start_str,
            'end_date': end_str,
            'week_start': start_str,
            'week_end': end_str,
            'date_from': start_str,
            'date_to': end_str,
            'from_date': start_str,
            'to_date': end_str
        }
        
        # Apply substitutions
        result = {}
        for key, value in parameters.items():
            if isinstance(value, str):
                # Check if it's a template variable
                if value.startswith('{{') and value.endswith('}}'):
                    param_name = value[2:-2].strip()
                    if param_name in substitutions:
                        result[key] = substitutions[param_name]
                    else:
                        result[key] = value
                else:
                    result[key] = value
            else:
                result[key] = value
        
        # Add standard date parameters if not present
        if 'startDate' not in result:
            result['startDate'] = start_str
        if 'endDate' not in result:
            result['endDate'] = end_str
        
        return result
    
    async def pause_collection(self, collection_id: str) -> bool:
        """Pause an active collection"""
        try:
            return self.reporting_db.update_collection_progress(
                collection_id,
                {'status': 'paused'}
            ) is not None
        except Exception as e:
            logger.error(f"Error pausing collection: {e}")
            return False
    
    async def resume_collection(self, collection_id: str) -> bool:
        """Resume a paused collection"""
        try:
            return self.reporting_db.update_collection_progress(
                collection_id,
                {'status': 'pending'}
            ) is not None
        except Exception as e:
            logger.error(f"Error resuming collection: {e}")
            return False
    
    async def get_collection_progress(self, collection_id: str) -> Dict[str, Any]:
        """
        Get detailed progress for a collection
        
        Returns:
            Progress details including completed weeks, failures, etc.
        """
        try:
            collection = self.reporting_db.get_collection_status(collection_id)
            if not collection:
                raise ValueError(f"Collection {collection_id} not found")
            
            # Get week details
            weeks_query = self.reporting_db.client.table('report_data_weeks')\
                .select('*')\
                .eq('collection_id', collection['id'])\
                .order('week_start_date')
            
            weeks_response = weeks_query.execute()
            weeks = weeks_response.data or []
            
            # Calculate statistics
            total_weeks = len(weeks)
            completed_weeks = len([w for w in weeks if w['status'] == 'completed'])
            failed_weeks = len([w for w in weeks if w['status'] == 'failed'])
            pending_weeks = len([w for w in weeks if w['status'] == 'pending'])
            running_weeks = len([w for w in weeks if w['status'] == 'running'])
            
            # Find next pending week
            next_week = None
            for week in weeks:
                if week['status'] == 'pending':
                    next_week = {
                        'start_date': week['week_start_date'],
                        'end_date': week['week_end_date']
                    }
                    break
            
            return {
                'collection_id': collection['collection_id'],
                'status': collection['status'],
                'progress_percentage': collection['progress_percentage'],
                'statistics': {
                    'total_weeks': total_weeks,
                    'completed': completed_weeks,
                    'failed': failed_weeks,
                    'pending': pending_weeks,
                    'running': running_weeks
                },
                'next_week': next_week,
                'weeks': weeks,
                'started_at': collection['created_at'],
                'updated_at': collection['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Error getting collection progress: {e}")
            raise
    
    async def check_duplicate_data(
        self,
        collection_id: str,
        week_start: date,
        data: Any
    ) -> bool:
        """
        Check if data for a week already exists (duplicate detection)
        
        Args:
            collection_id: Collection UUID
            week_start: Week start date
            data: Data to check for duplicates
            
        Returns:
            True if duplicate found, False otherwise
        """
        try:
            # Compute checksum for the data
            checksum = self.reporting_db.compute_data_checksum(data)
            
            # Check if this checksum already exists for this week
            return self.reporting_db.check_duplicate_week(
                collection_id,
                week_start,
                checksum
            )
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return False
    
    async def cleanup_abandoned_collections(self, hours_old: int = 24) -> int:
        """
        Clean up collections that have been abandoned
        
        Args:
            hours_old: Collections older than this many hours in 'running' state
            
        Returns:
            Number of collections cleaned up
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_old)
            
            # Find abandoned collections
            response = self.reporting_db.client.table('report_data_collections')\
                .select('id, collection_id')\
                .eq('status', 'running')\
                .lt('updated_at', cutoff_time.isoformat())\
                .execute()
            
            abandoned = response.data or []
            
            # Mark them as failed
            for collection in abandoned:
                self.reporting_db.update_collection_progress(
                    collection['collection_id'],
                    {
                        'status': 'failed',
                        'error_message': f'Collection abandoned after {hours_old} hours'
                    }
                )
            
            if abandoned:
                logger.info(f"Cleaned up {len(abandoned)} abandoned collections")
            
            return len(abandoned)
            
        except Exception as e:
            logger.error(f"Error cleaning up abandoned collections: {e}")
            return 0


# Import timezone for datetime operations
from datetime import timezone

# Create singleton instance
historical_collection_service = HistoricalCollectionService()