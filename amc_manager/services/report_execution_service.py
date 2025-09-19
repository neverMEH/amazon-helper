"""
Report Execution Service for AMC Report Builder
Handles direct ad-hoc execution of reports via AMC API
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
import asyncio
from amc_manager.services.db_service import DatabaseService, with_connection_retry
from amc_manager.services.amc_api_client_with_retry import amc_api_client_with_retry
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


class ReportExecutionService(DatabaseService):
    """
    Service for executing reports via ad-hoc AMC API calls

    IMPORTANT DISTINCTION: Ad-hoc vs Saved Workflows
    ------------------------------------------------
    This service handles AD-HOC execution of SQL queries directly through AMC API.

    Ad-hoc Execution (This Service):
    - SQL query is sent directly to AMC's createWorkflowExecution API with sql_query parameter
    - No workflow is created or stored in AMC
    - Each execution is independent with its own SQL and parameters
    - Used for: Report Builder, one-time queries, dynamic SQL generation
    - AMC API call: POST /workflowExecutions with {sql_query: "...", parameter_values: {...}}

    Saved Workflow Execution (WorkflowService):
    - Workflow is first created in AMC with createWorkflow API
    - Workflow has a permanent ID and can be reused
    - Executions reference the workflow_id, not SQL directly
    - Used for: Scheduled workflows, recurring reports, version-controlled queries
    - AMC API calls:
        1. POST /workflows to create (one-time)
        2. POST /workflowExecutions with {workflow_id: "...", parameter_values: {...}}

    Key Differences:
    - Ad-hoc: sql_query parameter is REQUIRED, workflow_id is NOT ALLOWED
    - Saved: workflow_id parameter is REQUIRED, sql_query is NOT ALLOWED
    - These parameters are mutually exclusive in AMC API
    """

    def __init__(self):
        super().__init__()
        self.amc_client = amc_api_client_with_retry

    async def execute_report_adhoc(
        self,
        report_id: str,
        instance_id: str,
        sql_query: str,
        parameters: Dict[str, Any],
        user_id: str,
        entity_id: str,
        triggered_by: str = 'manual',
        schedule_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        time_window_start: Optional[datetime] = None,
        time_window_end: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a report directly via AMC ad-hoc API

        Args:
            report_id: Report definition UUID
            instance_id: AMC instance ID (string, not UUID)
            sql_query: Formatted SQL query to execute
            parameters: Execution parameters
            user_id: User ID for token refresh
            entity_id: AMC entity ID
            triggered_by: manual|schedule|backfill|api
            schedule_id: Optional schedule UUID
            collection_id: Optional collection UUID
            time_window_start: Optional time window start
            time_window_end: Optional time window end

        Returns:
            Execution record or None if failed
        """
        try:
            logger.info(f"execute_report_adhoc called with report_id={report_id}, instance_id={instance_id}")
            logger.info(f"SQL query received: {'Yes' if sql_query else 'No'}")
            logger.info(f"SQL query length: {len(sql_query) if sql_query else 0}")
            if sql_query:
                logger.info(f"SQL query first 200 chars: {sql_query[:200]}")
            else:
                logger.error("WARNING: SQL query is None or empty!")
            logger.info(f"Time window: {time_window_start} to {time_window_end}")

            # Generate execution ID
            execution_id = f"exec_{uuid.uuid4().hex[:8]}"

            # Create execution record first
            execution_record = {
                'execution_id': execution_id,
                'report_id': report_id,
                'instance_id': self._get_instance_uuid(instance_id),
                'user_id': user_id,
                'triggered_by': triggered_by,
                'schedule_id': schedule_id,
                'collection_id': collection_id,
                'status': 'pending',
                'parameters_snapshot': parameters,
                'time_window_start': time_window_start.isoformat() if time_window_start else None,
                'time_window_end': time_window_end.isoformat() if time_window_end else None,
                'started_at': datetime.utcnow().isoformat()
            }

            # Get template ID from report
            report = self._get_report_sync(report_id)
            if report:
                execution_record['template_id'] = report.get('template_id')

            # Insert execution record
            exec_response = self.client.table('report_executions').insert(execution_record).execute()

            if not exec_response.data:
                logger.error(f"Failed to create execution record for {execution_id}")
                return None

            execution_uuid = exec_response.data[0]['id']

            # Execute via AMC API (ad-hoc, no workflow creation)
            # CRITICAL: This is an AD-HOC execution - we pass sql_query directly
            # We do NOT create a workflow first, and do NOT pass workflow_id
            # The AMC API requires either sql_query OR workflow_id, never both
            try:
                # Call AMC API with sql_query only (no workflow)
                # Build parameters for AMC API - include time window in parameter_values
                amc_params = {}
                if time_window_start:
                    amc_params['timeWindowStart'] = self._format_amc_date(time_window_start)
                if time_window_end:
                    amc_params['timeWindowEnd'] = self._format_amc_date(time_window_end)

                # Add any other parameters passed
                if parameters:
                    amc_params.update(parameters)

                # Ad-hoc execution: SQL query is passed directly to AMC
                # The SQL must be fully processed (no template placeholders like {{param}})
                # because AMC doesn't understand template syntax
                logger.info(f"Executing ad-hoc report with SQL length: {len(sql_query) if sql_query else 0}")
                logger.info(f"Parameters being passed: {amc_params}")

                # Final check before AMC call
                if not sql_query:
                    logger.error("CRITICAL: SQL query is None/empty right before AMC API call!")
                    raise ValueError("SQL query is required for ad-hoc execution")
                else:
                    logger.info(f"SQL query confirmed present, length: {len(sql_query)}")

                # AD-HOC EXECUTION: Pass sql_query parameter (not workflow_id)
                # The AMC API will execute this SQL directly without creating a workflow
                # This is different from saved workflows which reference a workflow_id
                amc_result = await self.amc_client.create_workflow_execution(
                    instance_id=instance_id,
                    user_id=user_id,
                    entity_id=entity_id,
                    sql_query=sql_query,  # Ad-hoc: SQL passed directly
                    # workflow_id=None,   # Ad-hoc: NO workflow_id
                    parameter_values=amc_params if amc_params else None
                )

                # Update execution with AMC execution ID
                if amc_result and 'executionId' in amc_result:
                    self._update_execution_sync(
                        execution_uuid,
                        {
                            'amc_execution_id': amc_result['executionId'],
                            'status': 'running'
                        }
                    )
                    logger.info(f"Started AMC execution {amc_result['executionId']} for report {report_id}")
                    return self._get_execution_sync(execution_uuid)

            except Exception as amc_error:
                # Update execution as failed
                self._update_execution_sync(
                    execution_uuid,
                    {
                        'status': 'failed',
                        'error_message': str(amc_error),
                        'completed_at': datetime.utcnow().isoformat()
                    }
                )
                logger.error(f"AMC execution failed for {execution_id}: {amc_error}")
                return self._get_execution_sync(execution_uuid)

        except Exception as e:
            logger.error(f"Error executing report {report_id}: {e}")
            return None

    async def execute_with_time_window(
        self,
        report_id: str,
        sql_query: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Execute report with specific time window

        Args:
            report_id: Report definition UUID
            sql_query: SQL query to execute
            start_date: Time window start
            end_date: Time window end
            **kwargs: Additional execution parameters

        Returns:
            Execution record
        """
        # Adjust for AMC 14-day data lag
        adjusted_end = min(end_date, datetime.utcnow() - timedelta(days=14))

        return await self.execute_report_adhoc(
            report_id=report_id,
            sql_query=sql_query,
            time_window_start=start_date,
            time_window_end=adjusted_end,
            **kwargs
        )

    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running execution

        Args:
            execution_id: Execution UUID

        Returns:
            True if cancelled
        """
        try:
            # Get execution record
            execution = self._get_execution_sync(execution_id)
            if not execution:
                return False

            # Only cancel if running
            if execution['status'] != 'running':
                logger.warning(f"Cannot cancel execution {execution_id} with status {execution['status']}")
                return False

            # Cancel via AMC API if we have AMC execution ID
            if execution.get('amc_execution_id'):
                try:
                    await self.amc_client.cancel_execution(execution['amc_execution_id'])
                except Exception as e:
                    logger.error(f"Failed to cancel AMC execution: {e}")

            # Update status
            self._update_execution_sync(
                execution_id,
                {
                    'status': 'cancelled',
                    'completed_at': datetime.utcnow().isoformat()
                }
            )

            return True

        except Exception as e:
            logger.error(f"Error cancelling execution {execution_id}: {e}")
            return False

    async def update_status(
        self,
        execution_id: str,
        status: str,
        output_location: Optional[str] = None,
        row_count: Optional[int] = None,
        size_bytes: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update execution status

        Args:
            execution_id: Execution UUID
            status: New status
            output_location: S3 output location
            row_count: Number of rows in result
            size_bytes: Size of result in bytes
            error_message: Error message if failed

        Returns:
            Updated execution record
        """
        try:
            update_data = {'status': status}

            if output_location:
                update_data['output_location'] = output_location
            if row_count is not None:
                update_data['row_count'] = row_count
            if size_bytes is not None:
                update_data['size_bytes'] = size_bytes
            if error_message:
                update_data['error_message'] = error_message

            if status in ['completed', 'failed', 'cancelled']:
                update_data['completed_at'] = datetime.utcnow().isoformat()

            return self._update_execution_sync(execution_id, update_data)

        except Exception as e:
            logger.error(f"Error updating execution status: {e}")
            return None

    @with_connection_retry
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get execution by ID

        Args:
            execution_id: Execution UUID or execution_id string

        Returns:
            Execution record
        """
        return self._get_execution_sync(execution_id)

    @with_connection_retry
    def list_executions(
        self,
        report_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        status: Optional[str] = None,
        triggered_by: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List executions with filters

        Args:
            report_id: Filter by report
            instance_id: Filter by instance
            status: Filter by status
            triggered_by: Filter by trigger type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results

        Returns:
            List of execution records
        """
        try:
            query = self.client.table('report_executions').select('*')

            if report_id:
                query = query.eq('report_id', report_id)
            if instance_id:
                query = query.eq('instance_id', instance_id)
            if status:
                query = query.eq('status', status)
            if triggered_by:
                query = query.eq('triggered_by', triggered_by)
            if start_date:
                query = query.gte('started_at', start_date.isoformat())
            if end_date:
                query = query.lte('started_at', end_date.isoformat())

            query = query.order('started_at', desc=True).limit(limit)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error listing executions: {e}")
            return []

    async def poll_execution_status(self, execution_id: str, user_id: str) -> Optional[str]:
        """
        Poll AMC API for execution status

        Args:
            execution_id: Execution UUID
            user_id: User ID for token refresh

        Returns:
            Final status or None
        """
        try:
            execution = self._get_execution_sync(execution_id)
            if not execution or not execution.get('amc_execution_id'):
                return None

            # Get instance details
            instance = self._get_instance_with_entity(execution['instance_id'])
            if not instance:
                return None

            # Poll AMC API
            amc_status = await self.amc_client.get_execution_status(
                instance_id=instance['instance_id'],
                execution_id=execution['amc_execution_id'],
                user_id=user_id,
                entity_id=instance['entity_id']
            )

            if amc_status:
                # Map AMC status to our status
                status_map = {
                    'SUCCEEDED': 'completed',
                    'FAILED': 'failed',
                    'CANCELLED': 'cancelled',
                    'RUNNING': 'running',
                    'PENDING': 'running'
                }

                new_status = status_map.get(amc_status['status'], 'running')

                # Update execution
                await self.update_status(
                    execution_id=execution_id,
                    status=new_status,
                    output_location=amc_status.get('outputLocation'),
                    row_count=amc_status.get('rowCount'),
                    error_message=amc_status.get('error')
                )

                return new_status

        except Exception as e:
            logger.error(f"Error polling execution status: {e}")
            return None

    # Helper methods (synchronous for database operations)

    def _get_report_sync(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report synchronously"""
        try:
            response = self.client.table('report_definitions').select('*').eq('id', report_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching report: {e}")
            return None

    def _get_execution_sync(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution synchronously"""
        try:
            if execution_id.startswith('exec_'):
                response = self.client.table('report_executions').select('*').eq('execution_id', execution_id).execute()
            else:
                response = self.client.table('report_executions').select('*').eq('id', execution_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching execution: {e}")
            return None

    def _update_execution_sync(self, execution_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update execution synchronously"""
        try:
            response = self.client.table('report_executions').update(update_data).eq('id', execution_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating execution: {e}")
            return None

    def _get_instance_uuid(self, instance_id: str) -> Optional[str]:
        """Get instance UUID from instance_id string"""
        try:
            response = self.client.table('amc_instances').select('id').eq('instance_id', instance_id).execute()
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching instance UUID: {e}")
            return None

    def _get_instance_with_entity(self, instance_uuid: str) -> Optional[Dict[str, Any]]:
        """Get instance with entity ID"""
        try:
            response = self.client.table('amc_instances').select(
                '*, amc_accounts!inner(account_id)'
            ).eq('id', instance_uuid).execute()

            if response.data:
                instance = response.data[0]
                instance['entity_id'] = instance['amc_accounts']['account_id']
                return instance

            return None
        except Exception as e:
            logger.error(f"Error fetching instance with entity: {e}")
            return None

    def _format_amc_date(self, date: Optional[datetime]) -> Optional[str]:
        """Format date for AMC API (no Z suffix)"""
        if date:
            return date.strftime('%Y-%m-%dT%H:%M:%S')
        return None