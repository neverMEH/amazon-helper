"""AMC Workflow Execution Service - Handles execution of workflows on AMC instances"""

import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import re
from string import Template
import asyncio

from ..core.logger_simple import get_logger
from ..core.supabase_client import SupabaseManager
from .db_service import db_service
from .token_service import token_service

logger = get_logger(__name__)


class AMCExecutionService:
    """Service for executing workflows on AMC instances"""
    
    def __init__(self):
        self.db = db_service
        # Configuration flag to use real AMC API vs simulation
        # Set via environment variable AMC_USE_REAL_API=true
        import os
        self.use_real_api = os.getenv('AMC_USE_REAL_API', 'false').lower() == 'true'
        if self.use_real_api:
            logger.info("AMC Execution Service configured to use REAL AMC API")
        else:
            logger.info("AMC Execution Service configured to use SIMULATED execution")
        
    def execute_workflow(
        self,
        workflow_id: str,
        user_id: str,
        execution_parameters: Optional[Dict[str, Any]] = None,
        triggered_by: str = "manual",
        instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow on an AMC instance
        
        Args:
            workflow_id: Internal workflow UUID
            user_id: User ID
            execution_parameters: Parameters to substitute in SQL query
            triggered_by: How execution was triggered (manual, schedule, api)
            
        Returns:
            Execution record with ID and status
        """
        try:
            # Get workflow details
            workflow = self._get_workflow_with_instance(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Verify user has access
            if workflow['user_id'] != user_id:
                raise ValueError("Access denied to workflow")
            
            # Determine which instance to use
            if instance_id:
                # Use the provided instance (for templates run on different instances)
                logger.info(f"Looking up instance by instance_id: {instance_id}")
                instance = self._get_instance(instance_id)
                if not instance:
                    logger.error(f"AMC instance {instance_id} not found in database")
                    raise ValueError(f"AMC instance {instance_id} not found")
                logger.info(f"Found instance: {instance['instance_name']} (id: {instance['id']})")
                
                # Verify user has access to this instance
                logger.info(f"Checking user {user_id} access to instance {instance_id}")
                if not self.db.user_has_instance_access_sync(user_id, instance_id):
                    logger.error(f"User {user_id} does not have access to instance {instance_id}")
                    raise ValueError(f"Access denied to instance {instance_id}")
                logger.info(f"User has access to instance {instance_id}")
            else:
                # Use the workflow's default instance
                instance = workflow.get('amc_instances', {})
                if not instance:
                    logger.error(f"No AMC instance associated with workflow {workflow_id}")
                    raise ValueError("No AMC instance associated with workflow")
                logger.info(f"Using workflow's default instance: {instance.get('instance_id', 'unknown')}")
            
            # Prepare SQL query with parameter substitution
            sql_query = self._prepare_sql_query(
                workflow['sql_query'],
                execution_parameters or workflow.get('parameters', {})
            )
            
            # Create execution record
            execution_data = {
                "workflow_id": workflow_id,
                "status": "pending",
                "execution_parameters": execution_parameters or {},
                "triggered_by": triggered_by,
                "started_at": datetime.now(timezone.utc).isoformat()
                # Note: instance_id column must be added to workflow_executions table via migration
                # Once added, uncomment the line below:
                # "instance_id": instance['instance_id']
            }
            
            execution = self.db.create_execution_sync(execution_data)
            if not execution:
                raise ValueError("Failed to create execution record")
            
            # Choose between real AMC API or simulation
            if self.use_real_api:
                execution_result = self._execute_real_amc_query(
                    instance_id=instance['instance_id'],
                    workflow_id=workflow_id,
                    sql_query=sql_query,
                    execution_id=execution['execution_id'],
                    user_id=user_id,
                    execution_parameters=execution_parameters
                )
            else:
                execution_result = self._simulate_amc_execution(
                    instance_id=instance['instance_id'],
                    sql_query=sql_query,
                    execution_id=execution['execution_id']
                )
            
            # Update execution with results
            update_data = {
                "status": execution_result['status'],
                "completed_at": datetime.now(timezone.utc).isoformat() if execution_result['status'] in ['completed', 'failed'] else None,
                "error_message": execution_result.get('error'),
                "row_count": execution_result.get('row_count')
            }
            
            self._update_execution_status(execution['id'], update_data)
            
            # Note: last_executed_at column doesn't exist in workflows table
            
            return {
                "execution_id": execution['execution_id'],
                "workflow_id": workflow['workflow_id'],
                "status": update_data['status'],
                "started_at": execution['started_at'],
                "message": "Workflow execution started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            raise
    
    def _get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get instance details by instance_id"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            response = client.table('amc_instances')\
                .select('*')\
                .eq('instance_id', instance_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching instance {instance_id}: {e}")
            return None
    
    def _get_workflow_with_instance(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow with instance details"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            response = client.table('workflows')\
                .select('*, amc_instances(*)')\
                .eq('id', workflow_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching workflow: {e}")
            return None
    
    def _prepare_sql_query(self, sql_template: str, parameters: Dict[str, Any]) -> str:
        """
        Prepare SQL query by substituting parameters
        
        Args:
            sql_template: SQL query with {{parameter}} placeholders
            parameters: Parameter values to substitute
            
        Returns:
            SQL query with substituted values
        """
        # Find all parameters in the template
        param_pattern = r'\{\{(\w+)\}\}'
        required_params = re.findall(param_pattern, sql_template)
        
        # Check for missing required parameters
        missing_params = [p for p in required_params if p not in parameters]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
        
        # Substitute parameters
        query = sql_template
        for param, value in parameters.items():
            # Handle different value types
            if isinstance(value, (list, tuple)):
                # Convert list to SQL array format
                value_str = "({})".format(','.join(f"'{v}'" for v in value))
            elif isinstance(value, str):
                value_str = f"'{value}'"
            else:
                value_str = str(value)
            
            query = query.replace(f"{{{{{param}}}}}", value_str)
        
        return query
    
    def _execute_real_amc_query(
        self,
        instance_id: str,
        workflow_id: str,
        sql_query: str,
        execution_id: str,
        user_id: str,
        execution_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute real AMC query using Amazon API
        
        Returns:
            Execution result with status and details
        """
        try:
            # Ensure token is fresh before workflow execution
            from .token_refresh_service import token_refresh_service
            asyncio.run(token_refresh_service.refresh_before_workflow(user_id))
            
            # Get user's Amazon OAuth token
            valid_token = asyncio.run(token_service.get_valid_token(user_id))
            if not valid_token:
                logger.error(f"No valid Amazon token for user {user_id}")
                return {
                    "status": "failed",
                    "error": "No valid Amazon OAuth token. Please re-authenticate with Amazon."
                }
            
            # Get the AMC instance details to find entity ID
            client = SupabaseManager.get_client(use_service_role=True)
            instance_response = client.table('amc_instances')\
                .select('*, amc_accounts!inner(entity_id)')\
                .eq('instance_id', instance_id)\
                .execute()
            
            if not instance_response.data:
                return {
                    "status": "failed",
                    "error": f"AMC instance {instance_id} not found"
                }
            
            instance = instance_response.data[0]
            entity_id = instance['amc_accounts']['entity_id']
            marketplace_id = instance.get('marketplace_id', 'ATVPDKIKX0DER')
            
            logger.info(f"Executing on instance {instance_id} with entity {entity_id}")
            
            # Create workflow execution via AMC API
            from ..core.api_client import AMCAPIClient, AMCAPIEndpoints
            
            # Initialize API client
            api_client = AMCAPIClient(
                profile_id=entity_id,  # Using entity_id as profile_id
                marketplace_id=marketplace_id
            )
            
            # Prepare execution data
            execution_data = {
                'workflowId': workflow_id,
                'executionId': execution_id,
                'sqlQuery': sql_query,
                'parameters': execution_parameters or {},
                'triggeredBy': 'manual',
                'triggeredAt': datetime.now(timezone.utc).isoformat()
            }
            
            # Create the execution
            endpoint = f"amc/instances/{instance_id}/workflows/{workflow_id}/executions"
            
            # Update progress to show we're starting
            self._update_execution_progress(execution_id, 'running', 10)
            
            try:
                # Make the API call to create execution
                response = api_client.post(
                    endpoint,
                    user_id,
                    {'access_token': valid_token},  # Pass token as dict
                    json_data=execution_data
                )
                
                amc_execution_id = response.get('executionId', execution_id)
                logger.info(f"Created AMC execution: {amc_execution_id}")
                
                # Poll for completion
                max_attempts = 120  # 10 minutes max (5 second intervals)
                for attempt in range(max_attempts):
                    # Get execution status
                    status_endpoint = f"amc/instances/{instance_id}/executions/{amc_execution_id}/status"
                    status_response = api_client.get(
                        status_endpoint,
                        user_id,
                        {'access_token': valid_token}
                    )
                    
                    status = status_response.get('status', 'running')
                    progress = status_response.get('progress', 50)
                    
                    # Update our execution record
                    self._update_execution_progress(execution_id, status, progress)
                    
                    if status == 'completed' or status == 'SUCCEEDED':
                        # Get results
                        results_endpoint = f"amc/instances/{instance_id}/executions/{amc_execution_id}/results"
                        results_response = api_client.get(
                            results_endpoint,
                            user_id,
                            {'access_token': valid_token}
                        )
                        
                        # Parse results
                        result_data = {
                            "columns": results_response.get('schema', []),
                            "rows": results_response.get('data', []),
                            "total_rows": results_response.get('rowCount', 0),
                            "sample_size": results_response.get('rowCount', 0),
                            "execution_details": {
                                "query_runtime_seconds": results_response.get('queryRuntime', 0),
                                "data_scanned_gb": results_response.get('dataScanned', 0),
                                "cost_estimate_usd": results_response.get('costEstimate', 0)
                            }
                        }
                        
                        # Update execution with results
                        self._update_execution_completed(
                            execution_id=execution_id,
                            amc_execution_id=amc_execution_id,
                            row_count=result_data['total_rows'],
                            results=result_data
                        )
                        
                        return {
                            "status": "completed",
                            "amc_execution_id": amc_execution_id,
                            "row_count": result_data['total_rows'],
                            "results_url": status_response.get('outputLocation')
                        }
                    
                    elif status == 'failed' or status == 'FAILED':
                        error_msg = status_response.get('error', 'Query execution failed')
                        self._update_execution_completed(
                            execution_id=execution_id,
                            amc_execution_id=amc_execution_id,
                            row_count=0,
                            error_message=error_msg
                        )
                        return {
                            "status": "failed",
                            "error": error_msg
                        }
                    
                    # Wait before next poll
                    time.sleep(5)
                
                # Timeout
                self._update_execution_completed(
                    execution_id=execution_id,
                    amc_execution_id=amc_execution_id,
                    row_count=0,
                    error_message="Execution timed out after 10 minutes"
                )
                return {
                    "status": "failed",
                    "error": "Execution timed out"
                }
                
            except Exception as api_error:
                logger.error(f"AMC API error: {api_error}")
                return {
                    "status": "failed",
                    "error": f"AMC API error: {str(api_error)}"
                }
                
        except Exception as e:
            logger.error(f"Error executing real AMC query: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _simulate_amc_execution(
        self,
        instance_id: str,
        sql_query: str,
        execution_id: str
    ) -> Dict[str, Any]:
        """
        Simulate AMC execution for development
        In production, this would call the actual AMC API
        """
        # Update status to running
        self._update_execution_progress(execution_id, 'running', 10)
        time.sleep(1)
        
        # Simulate progress updates
        self._update_execution_progress(execution_id, 'running', 50)
        time.sleep(1)
        
        # For CJA queries, return sample results with full data structure
        if "customer journey" in sql_query.lower() or "conversion" in sql_query.lower():
            columns = [
                {"name": "journey_type", "type": "varchar"},
                {"name": "first_touch_channel", "type": "varchar"},
                {"name": "last_touch_channel", "type": "varchar"},
                {"name": "unique_channels", "type": "integer"},
                {"name": "touchpoint_bucket", "type": "varchar"},
                {"name": "user_count", "type": "integer"},
                {"name": "avg_journey_days", "type": "numeric"},
                {"name": "avg_touchpoints", "type": "numeric"},
                {"name": "avg_clicks", "type": "numeric"},
                {"name": "percentage_of_users", "type": "numeric"}
            ]
            
            rows = [
                ["Converted", "Display", "Sponsored Ads Click", 3, "4-7 touchpoints", 1250, 5.2, 5.8, 2.3, 35.7],
                ["Converted", "Sponsored Ads", "Display Click", 2, "1-3 touchpoints", 890, 2.1, 2.5, 1.8, 25.4],
                ["Non-Converted", "Display", "Display", 1, "1-3 touchpoints", 567, 1.5, 1.8, 0.2, 16.2],
                ["Converted", "DSP", "Sponsored Ads Click", 4, "8+ touchpoints", 432, 12.3, 9.2, 3.1, 12.3],
                ["Non-Converted", "Sponsored Ads", "DSP", 2, "1-3 touchpoints", 321, 2.8, 2.1, 0.5, 9.2]
            ]
            
            # Update to 90% before completion
            self._update_execution_progress(execution_id, 'running', 90)
            
            # Store results in database and mark complete
            results = {
                "columns": columns,
                "rows": rows,
                "total_rows": len(rows),
                "sample_size": len(rows),
                "execution_details": {
                    "query_runtime_seconds": 3.2,
                    "data_scanned_gb": 0.145,
                    "cost_estimate_usd": 0.0007
                }
            }
            
            logger.info(f"Generated results for execution {execution_id}: {len(columns)} columns, {len(rows)} rows")
            
            self._update_execution_completed(
                execution_id=execution_id,
                amc_execution_id=f"amc_exec_{execution_id}",
                row_count=len(rows),
                results=results
            )
            
            return {
                "status": "completed",
                "amc_execution_id": f"amc_exec_{execution_id}",
                "row_count": len(rows),
                "results_url": f"s3://amc-results/{instance_id}/{execution_id}/results.csv"
            }
        
        # Default simulation for other queries
        self._update_execution_progress(execution_id, 'running', 90)
        
        columns = [{"name": "col1", "type": "varchar"}, {"name": "col2", "type": "integer"}]
        rows = [["value1", 100], ["value2", 200]]
        
        results = {
            "columns": columns,
            "rows": rows,
            "total_rows": 2,
            "sample_size": 2,
            "execution_details": {
                "query_runtime_seconds": 1.5,
                "data_scanned_gb": 0.05,
                "cost_estimate_usd": 0.0002
            }
        }
        
        self._update_execution_completed(
            execution_id=execution_id,
            amc_execution_id=f"amc_exec_{execution_id}",
            row_count=2,
            results=results
        )
        
        return {
            "status": "completed",
            "amc_execution_id": f"amc_exec_{execution_id}",
            "row_count": 2,
            "results_url": f"s3://amc-results/{instance_id}/{execution_id}/results.csv"
        }
    
    def _update_execution_status(self, execution_id: str, update_data: Dict[str, Any]):
        """Update execution record status"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # Remove non-existent columns
            update_data.pop('amc_execution_id', None)
            update_data.pop('query_results_url', None)
            
            response = client.table('workflow_executions')\
                .update(update_data)\
                .eq('id', execution_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating execution status: {e}")
            return None
    
    def get_execution_status(self, execution_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status and results"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            response = client.table('workflow_executions')\
                .select('*, workflows!inner(user_id)')\
                .eq('execution_id', execution_id)\
                .execute()
            
            if not response.data:
                return None
            
            execution = response.data[0]
            
            # Verify user has access
            if execution['workflows']['user_id'] != user_id:
                return None
            
            return {
                "execution_id": execution['execution_id'],
                "status": execution['status'],
                "progress": execution.get('progress', 0),
                "started_at": execution['started_at'],
                "completed_at": execution.get('completed_at'),
                "duration_seconds": execution.get('duration_seconds'),
                "error_message": execution.get('error_message'),
                "row_count": execution.get('row_count'),
                "triggered_by": execution.get('triggered_by', 'manual')
            }
        except Exception as e:
            logger.error(f"Error fetching execution status: {e}")
            return None
    
    def get_execution_results(self, execution_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get execution results from database"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # Get execution with results
            response = client.table('workflow_executions')\
                .select('*, workflows!inner(user_id)')\
                .eq('execution_id', execution_id)\
                .execute()
            
            if not response.data:
                return None
            
            execution = response.data[0]
            
            # Verify user has access
            if execution['workflows']['user_id'] != user_id:
                return None
            
            # Check if execution is completed
            if execution['status'] != 'completed':
                return None
            
            # Return results from database
            return {
                "columns": execution.get('result_columns', []),
                "rows": execution.get('result_rows', []),
                "total_rows": execution.get('result_total_rows', 0),
                "sample_size": execution.get('result_sample_size', 0),
                "execution_details": {
                    "query_runtime_seconds": execution.get('query_runtime_seconds'),
                    "data_scanned_gb": execution.get('data_scanned_gb'),
                    "cost_estimate_usd": execution.get('cost_estimate_usd')
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching execution results: {e}")
            return None
    
    def _update_execution_progress(self, execution_id: str, status: str, progress: int):
        """Update execution progress"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            client.table('workflow_executions')\
                .update({"status": status, "progress": progress})\
                .eq('execution_id', execution_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Error updating execution progress: {e}")
    
    def _update_execution_completed(
        self, 
        execution_id: str, 
        amc_execution_id: str,
        row_count: int = 0,
        error_message: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None
    ):
        """Update execution status to completed or failed"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # Get execution to calculate duration
            response = client.table('workflow_executions')\
                .select('started_at')\
                .eq('execution_id', execution_id)\
                .execute()
            
            if not response.data:
                return
            
            # Parse started_at and ensure timezone awareness
            started_at_str = response.data[0]['started_at']
            if started_at_str.endswith('Z'):
                started_at_str = started_at_str.replace('Z', '+00:00')
            from datetime import timezone
            started_at = datetime.fromisoformat(started_at_str)
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            
            # Use timezone-aware datetime for completed_at
            completed_at = datetime.now(timezone.utc)
            duration_seconds = int((completed_at - started_at).total_seconds())
            
            # Update execution
            update_data = {
                'status': 'failed' if error_message else 'completed',
                'completed_at': completed_at.isoformat(),
                'duration_seconds': duration_seconds,
                'row_count': row_count,
                'progress': 100
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            # Add results if provided
            if results and not error_message:
                update_data.update({
                    'result_columns': results.get('columns', []),
                    'result_rows': results.get('rows', []),
                    'result_total_rows': results.get('total_rows', row_count),
                    'result_sample_size': results.get('sample_size', len(results.get('rows', []))),
                    'query_runtime_seconds': results.get('execution_details', {}).get('query_runtime_seconds'),
                    'data_scanned_gb': results.get('execution_details', {}).get('data_scanned_gb'),
                    'cost_estimate_usd': results.get('execution_details', {}).get('cost_estimate_usd')
                })
                logger.info(f"Updating execution {execution_id} with results: columns={len(results.get('columns', []))}, rows={len(results.get('rows', []))}")
            
            response = client.table('workflow_executions')\
                .update(update_data)\
                .eq('execution_id', execution_id)\
                .execute()
                
            if response.data:
                logger.info(f"Updated execution {execution_id} successfully")
            else:
                logger.error(f"Failed to update execution {execution_id} - no data returned")
                
        except Exception as e:
            logger.error(f"Error updating execution completion: {e}")


# Singleton instance
amc_execution_service = AMCExecutionService()