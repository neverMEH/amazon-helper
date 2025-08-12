"""
Service for monitoring AMC executions and fetching results when completed
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..core.supabase_client import SupabaseManager
from .amc_api_client import AMCAPIClient
from .token_service import TokenService

logger = logging.getLogger(__name__)


class ExecutionMonitorService:
    """Service to monitor AMC executions and fetch results when completed"""
    
    def __init__(self):
        self.api_client = AMCAPIClient()
        self.token_service = TokenService()
        self.monitoring_tasks = {}
        
    async def start_monitoring(self, execution_id: str, amc_execution_id: str, instance_id: str, user_id: str):
        """
        Start monitoring an execution
        
        Args:
            execution_id: Internal execution ID
            amc_execution_id: AMC execution ID
            instance_id: AMC instance ID
            user_id: User ID who started the execution
        """
        if execution_id in self.monitoring_tasks:
            logger.info(f"Already monitoring execution {execution_id}")
            return
            
        # Create monitoring task
        task = asyncio.create_task(
            self._monitor_execution(execution_id, amc_execution_id, instance_id, user_id)
        )
        self.monitoring_tasks[execution_id] = task
        logger.info(f"Started monitoring execution {execution_id} (AMC: {amc_execution_id})")
        
    async def _monitor_execution(
        self, 
        execution_id: str, 
        amc_execution_id: str, 
        instance_id: str, 
        user_id: str,
        max_duration: int = 3600,  # Max 1 hour
        poll_interval: int = 10  # Check every 10 seconds
    ):
        """
        Monitor a single execution until completion
        """
        start_time = datetime.utcnow()
        max_time = start_time + timedelta(seconds=max_duration)
        
        try:
            while datetime.utcnow() < max_time:
                # Get valid token
                valid_token = await self.token_service.get_valid_token(user_id)
                if not valid_token:
                    logger.error(f"No valid token for user {user_id}, stopping monitoring")
                    self._update_execution_failed(execution_id, "Authentication token expired")
                    break
                
                # Get instance and account details
                client = SupabaseManager.get_client(use_service_role=True)
                instance_response = client.table('amc_instances')\
                    .select('*, amc_accounts!inner(*)')\
                    .eq('instance_id', instance_id)\
                    .single()\
                    .execute()
                    
                if not instance_response.data:
                    logger.error(f"Instance {instance_id} not found")
                    self._update_execution_failed(execution_id, "Instance not found")
                    break
                    
                instance = instance_response.data
                account = instance['amc_accounts']
                
                # Check execution status
                status_response = self.api_client.get_execution_status(
                    execution_id=amc_execution_id,
                    access_token=valid_token,
                    entity_id=account['account_id'],
                    marketplace_id=account['marketplace_id'],
                    instance_id=instance_id
                )
                
                if not status_response.get('success'):
                    logger.error(f"Failed to get status for {amc_execution_id}: {status_response.get('error')}")
                    await asyncio.sleep(poll_interval)
                    continue
                    
                amc_status = status_response.get('amcStatus', 'UNKNOWN')
                logger.info(f"Execution {execution_id} status: {amc_status}")
                
                # Update progress in database
                self._update_execution_progress(execution_id, status_response)
                
                # Check if completed
                if amc_status in ['SUCCEEDED', 'COMPLETED']:
                    # Fetch and store results
                    await self._fetch_and_store_results(
                        execution_id, 
                        amc_execution_id, 
                        instance_id, 
                        valid_token,
                        account['account_id'],
                        account['marketplace_id']
                    )
                    break
                elif amc_status in ['FAILED', 'CANCELLED']:
                    # Update as failed
                    error_msg = status_response.get('error') or status_response.get('errorDetails')
                    self._update_execution_failed(execution_id, error_msg)
                    break
                    
                # Wait before next check
                await asyncio.sleep(poll_interval)
                
            else:
                # Timeout reached
                logger.warning(f"Execution {execution_id} monitoring timed out after {max_duration} seconds")
                self._update_execution_failed(execution_id, "Execution monitoring timed out")
                
        except Exception as e:
            logger.error(f"Error monitoring execution {execution_id}: {e}")
            self._update_execution_failed(execution_id, str(e))
        finally:
            # Remove from monitoring tasks
            if execution_id in self.monitoring_tasks:
                del self.monitoring_tasks[execution_id]
            logger.info(f"Stopped monitoring execution {execution_id}")
            
    async def _fetch_and_store_results(
        self, 
        execution_id: str, 
        amc_execution_id: str, 
        instance_id: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str
    ):
        """
        Fetch results from AMC and store in database
        """
        try:
            logger.info(f"Fetching results for execution {execution_id} (AMC: {amc_execution_id})")
            
            # Get download URLs
            download_response = self.api_client.get_download_urls(
                execution_id=amc_execution_id,
                access_token=access_token,
                entity_id=entity_id,
                marketplace_id=marketplace_id,
                instance_id=instance_id
            )
            
            if not download_response.get('success'):
                logger.error(f"Failed to get download URLs: {download_response.get('error')}")
                self._update_execution_completed(execution_id, None, error_message="Failed to get download URLs")
                return
                
            urls = download_response.get('downloadUrls', [])
            if not urls:
                logger.warning(f"No download URLs available for {amc_execution_id}")
                self._update_execution_completed(execution_id, None, error_message="No results available")
                return
                
            # Download and parse CSV
            csv_response = self.api_client.download_and_parse_csv(urls[0])
            if not csv_response.get('success'):
                logger.error(f"Failed to parse CSV: {csv_response.get('error')}")
                self._update_execution_completed(execution_id, None, error_message="Failed to parse results")
                return
                
            # Prepare results for storage
            results = {
                'columns': csv_response.get('columns', []),
                'rows': csv_response.get('rows', []),
                'total_rows': csv_response.get('rowCount', 0),
                'sample_size': csv_response.get('rowCount', 0),
                'execution_details': {
                    'query_runtime_seconds': None,
                    'data_scanned_gb': None,
                    'cost_estimate_usd': None
                }
            }
            
            logger.info(f"Fetched {results['total_rows']} rows for execution {execution_id}")
            
            # Store results in database
            self._update_execution_completed(execution_id, results)
            
        except Exception as e:
            logger.error(f"Error fetching results for {execution_id}: {e}")
            self._update_execution_completed(execution_id, None, error_message=str(e))
            
    def _update_execution_progress(self, execution_id: str, status_response: Dict[str, Any]):
        """Update execution progress in database"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            update_data = {
                'status': status_response.get('status', 'running'),
                'progress': status_response.get('progress', 50)
            }
            
            client.table('workflow_executions')\
                .update(update_data)\
                .eq('execution_id', execution_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Error updating execution progress: {e}")
            
    def _update_execution_completed(
        self, 
        execution_id: str, 
        results: Optional[Dict[str, Any]],
        error_message: Optional[str] = None
    ):
        """Update execution as completed with results"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # Get execution to calculate duration
            response = client.table('workflow_executions')\
                .select('started_at')\
                .eq('execution_id', execution_id)\
                .execute()
                
            if not response.data:
                return
                
            # Calculate duration
            from datetime import timezone
            started_at_str = response.data[0]['started_at']
            if started_at_str.endswith('Z'):
                started_at_str = started_at_str.replace('Z', '+00:00')
            started_at = datetime.fromisoformat(started_at_str)
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            
            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()
            
            # Prepare update data
            update_data = {
                'status': 'failed' if error_message else 'completed',
                'progress': 100,
                'completed_at': completed_at.isoformat(),
                'duration_seconds': duration
            }
            
            if error_message:
                update_data['error_message'] = error_message
            elif results:
                update_data.update({
                    'result_columns': results['columns'],
                    'result_rows': results['rows'],
                    'result_total_rows': results['total_rows'],
                    'result_sample_size': results['sample_size'],
                    'row_count': results['total_rows'],
                    'query_runtime_seconds': results['execution_details'].get('query_runtime_seconds'),
                    'data_scanned_gb': results['execution_details'].get('data_scanned_gb'),
                    'cost_estimate_usd': results['execution_details'].get('cost_estimate_usd')
                })
                
            client.table('workflow_executions')\
                .update(update_data)\
                .eq('execution_id', execution_id)\
                .execute()
                
            logger.info(f"Updated execution {execution_id} as {'completed' if not error_message else 'failed'}")
            
        except Exception as e:
            logger.error(f"Error updating execution completion: {e}")
            
    def _update_execution_failed(self, execution_id: str, error_message: str):
        """Update execution as failed"""
        self._update_execution_completed(execution_id, None, error_message)


# Singleton instance
execution_monitor_service = ExecutionMonitorService()