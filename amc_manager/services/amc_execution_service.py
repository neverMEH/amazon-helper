"""AMC Workflow Execution Service - Handles execution of workflows on AMC instances"""

import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import re

from ..core.logger_simple import get_logger
from ..core.supabase_client import SupabaseManager
from ..config import settings
from .db_service import db_service
from .token_service import token_service
from .token_refresh_service import token_refresh_service
from .amc_api_client import AMCAPIClient
from ..utils.parameter_processor import ParameterProcessor

logger = get_logger(__name__)


class AMCExecutionService:
    """Service for executing workflows on AMC instances"""
    
    def __init__(self):
        self.db = db_service
        # Always use real AMC API - no test/simulation mode
        logger.info("AMC Execution Service configured to use REAL AMC API")
        
    async def execute_workflow(
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
                logger.error(f"Workflow not found with UUID: {workflow_id}")
                # Check if it's a truncated ID issue
                if len(workflow_id) < 36:  # UUID should be 36 chars
                    logger.error(f"Workflow ID appears truncated: {workflow_id} (length: {len(workflow_id)})")
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
                # Use the instance UUID for access check
                instance_uuid = instance['id']
                logger.info(f"Checking user {user_id} access to instance {instance_id} (UUID: {instance_uuid})")
                if not self.db.user_has_instance_access_sync(user_id, instance_uuid):
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
            
            # Log execution parameters for debugging
            logger.info(f"Execution parameters received: {execution_parameters}")
            logger.info(f"Workflow default parameters: {workflow.get('parameters', {})}")
            
            # Always substitute parameters for the SQL query
            sql_query = self._prepare_sql_query(
                workflow['sql_query'],
                execution_parameters or workflow.get('parameters', {})
            )
            
            # Log the prepared SQL for debugging (first 500 chars)
            logger.info(f"Prepared SQL query (first 500 chars): {sql_query[:500] if sql_query else 'None'}")
            
            # All executions now use saved workflows (no more ad-hoc mode)
            execution_mode = 'saved_workflow'
            
            # Get or create AMC workflow ID
            amc_workflow_id = workflow.get('amc_workflow_id')
            if not amc_workflow_id:
                # Auto-create AMC workflow if it doesn't exist
                logger.info(f"No AMC workflow ID found, auto-creating workflow in AMC")
                
                # Use the workflow's workflow_id field if available, otherwise generate one
                if workflow.get('workflow_id'):
                    # Use existing workflow_id from database (already in AMC-compliant format)
                    amc_workflow_id = workflow['workflow_id']
                    logger.info(f"Using existing workflow_id from database: {amc_workflow_id}")
                else:
                    # Generate AMC-compliant workflow ID from workflow name or UUID
                    workflow_name = workflow.get('name', workflow_id)
                    # Ensure AMC-compliant format: alphanumeric and underscores only
                    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', workflow_name[:30])
                    amc_workflow_id = f"wf_{clean_name}"
                    logger.info(f"Generated new AMC workflow ID: {amc_workflow_id} from name: {workflow_name}")
                
                # Get valid token for workflow creation
                valid_token = await token_service.get_valid_token(user_id)
                if valid_token:
                    # Get AMC account details
                    account = instance.get('amc_accounts')
                    if account:
                        entity_id = account['account_id']
                        marketplace_id = account.get('marketplace_id', 'ATVPDKIKX0DER')
                        
                        # Create workflow in AMC
                        api_client = AMCAPIClient()
                        
                        create_response = api_client.create_workflow(
                            instance_id=instance['instance_id'],
                            workflow_id=amc_workflow_id,
                            sql_query=sql_query,
                            access_token=valid_token,
                            entity_id=entity_id,
                            marketplace_id=marketplace_id,
                            output_format='CSV'
                        )
                        
                        if create_response.get('success'):
                            logger.info(f"Successfully auto-created AMC workflow: {amc_workflow_id}")
                            # Update database with AMC workflow ID
                            update_data = {
                                'amc_workflow_id': amc_workflow_id,
                                'is_synced_to_amc': True,
                                'amc_sync_status': 'synced',
                                'last_synced_at': datetime.now(timezone.utc).isoformat()
                            }
                            # update_workflow_sync expects the workflow_id field value, not the UUID
                            self.db.update_workflow_sync(workflow['workflow_id'], update_data)
                            workflow['amc_workflow_id'] = amc_workflow_id
                        else:
                            logger.warning(f"Failed to auto-create AMC workflow: {create_response.get('error')}")
                            # Continue anyway - will fall back to ad-hoc if needed
                else:
                    logger.warning("No valid token for auto-creating AMC workflow")
            
            # Get the latest version of the workflow for tracking (if versioning table exists)
            workflow_version_id = None
            try:
                client = SupabaseManager.get_client(use_service_role=True)
                version_response = client.table('workflow_versions')\
                    .select('id, version_number')\
                    .eq('workflow_id', workflow_id)\
                    .order('version_number', desc=True)\
                    .limit(1)\
                    .execute()
                
                if version_response.data and len(version_response.data) > 0:
                    workflow_version_id = version_response.data[0]['id']
            except Exception as e:
                # Table might not exist yet - this is okay, versioning is optional
                logger.info(f"Workflow versioning not available yet: {e}")
                workflow_version_id = None
            
            # Create execution record with version tracking
            execution_data = {
                "workflow_id": workflow_id,
                "status": "pending",
                "progress": 0,  # Initialize progress to ensure delay works
                "execution_parameters": execution_parameters or {},
                "triggered_by": triggered_by,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "execution_mode": execution_mode,
                "amc_workflow_id": amc_workflow_id  # Use the potentially auto-created ID
            }
            
            # Only add version ID if versioning is available
            if workflow_version_id:
                execution_data["workflow_version_id"] = workflow_version_id
            
            execution = self.db.create_execution_sync(execution_data)
            if not execution:
                raise ValueError("Failed to create execution record")
            
            # Always use real AMC API
            execution_result = await self._execute_real_amc_query(
                instance_id=instance['instance_id'],
                workflow_id=workflow_id,
                sql_query=sql_query,
                execution_id=execution['execution_id'],
                user_id=user_id,
                execution_parameters=execution_parameters,
                execution_mode=execution_mode,
                amc_workflow_id=amc_workflow_id  # Use the potentially auto-created ID
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
                "id": execution['id'],  # Add internal UUID for historical collection service
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
        """Get instance details by instance_id (can be UUID or AMC instance_id)"""
        try:
            import uuid
            client = SupabaseManager.get_client(use_service_role=True)

            # Check if instance_id is a valid UUID
            try:
                # Try to parse as UUID
                uuid.UUID(instance_id)
                is_uuid = True
            except (ValueError, AttributeError):
                is_uuid = False

            if is_uuid:
                # Try to find by UUID (id field)
                response = client.table('amc_instances')\
                    .select('*, amc_accounts(*)')\
                    .eq('id', instance_id)\
                    .execute()

                if response.data:
                    return response.data[0]

            # Try by AMC instance_id (string)
            response = client.table('amc_instances')\
                .select('*, amc_accounts(*)')\
                .eq('instance_id', instance_id)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching instance {instance_id}: {e}")
            return None
    
    def _get_workflow_with_instance(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow with instance details"""
        try:
            # Use db_service method which handles both UUID and string workflow IDs
            return self.db.get_workflow_by_id_sync(workflow_id)
        except Exception as e:
            logger.error(f"Error fetching workflow: {e}")
            return None
    
    def _prepare_sql_query(self, sql_template: str, parameters: Dict[str, Any]) -> str:
        """
        Prepare SQL query by substituting parameters

        Uses the shared ParameterProcessor for consistent handling

        Args:
            sql_template: SQL query with {{parameter}} placeholders
            parameters: Parameter values to substitute

        Returns:
            SQL query with substituted values
        """
        # Use the shared parameter processor for consistency
        return ParameterProcessor.process_sql_parameters(sql_template, parameters)
    
    def _is_campaign_or_asin_param(self, param_name: str) -> bool:
        """
        Check if a parameter name indicates it's a campaign or ASIN parameter
        that should be handled via SQL injection instead of AMC parameters
        """
        param_lower = param_name.lower()
        
        # Campaign keywords
        campaign_keywords = ['campaign', 'campaign_id', 'campaign_name', 'campaigns', 'campaign_ids', 'campaign_list']
        if any(keyword in param_lower for keyword in campaign_keywords):
            return True
            
        # ASIN keywords  
        asin_keywords = ['asin', 'product_asin', 'parent_asin', 'child_asin', 'asins', 'asin_list',
                        'tracked_asins', 'target_asins', 'promoted_asins', 'competitor_asins', 
                        'purchased_asins', 'viewed_asins']
        if any(keyword in param_lower for keyword in asin_keywords):
            return True
            
        return False
    
    async def _execute_real_amc_query(
        self,
        instance_id: str,
        workflow_id: str,
        sql_query: str,
        execution_id: str,
        user_id: str,
        execution_parameters: Optional[Dict[str, Any]] = None,
        execution_mode: str = 'saved_workflow',
        amc_workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute real AMC query using Amazon API
        
        Returns:
            Execution result with status and details
        """
        try:
            # Ensure token is fresh before workflow execution
            await token_refresh_service.refresh_before_workflow(user_id)
            
            # Get user's full token data
            user = await db_service.get_user_by_id(user_id)
            if not user or not user.get('auth_tokens'):
                logger.error(f"No tokens found for user {user_id}")
                return {
                    "status": "failed",
                    "error": "No valid Amazon OAuth token. Please re-authenticate with Amazon."
                }
            
            # Decrypt tokens for API usage
            auth_tokens = user['auth_tokens']
            try:
                decrypted_tokens = {
                    'access_token': token_service.decrypt_token(auth_tokens['access_token']),
                    'refresh_token': token_service.decrypt_token(auth_tokens['refresh_token']),
                    'expires_at': auth_tokens.get('expires_at'),
                    'expires_in': auth_tokens.get('expires_in', 3600),
                    'obtained_at': auth_tokens.get('obtained_at', time.time())
                }
            except ValueError as e:
                logger.error(f"Token decryption failed - likely due to key mismatch: {e}")
                return {
                    "status": "failed",
                    "error": "Authentication tokens cannot be decrypted. This usually happens when the encryption key has changed. Please log out and log in again with Amazon to refresh your authentication."
                }
            except Exception as e:
                logger.error(f"Unexpected error decrypting tokens: {e}")
                return {
                    "status": "failed",
                    "error": "Failed to decrypt authentication tokens. Please re-authenticate with Amazon."
                }
            
            # Get valid access token (this will refresh if needed)
            valid_token = await token_service.get_valid_token(user_id)
            if not valid_token:
                logger.error(f"No valid Amazon token for user {user_id}")
                return {
                    "status": "failed",
                    "error": "No valid Amazon OAuth token. Please re-authenticate with Amazon."
                }
            
            # Debug: Log token prefix to verify it's decrypted
            logger.info(f"Valid token starts with: {valid_token[:20]}..." if len(valid_token) > 20 else "Token too short")
            
            # Get the AMC instance details to find entity ID
            client = SupabaseManager.get_client(use_service_role=True)
            instance_response = client.table('amc_instances')\
                .select('*, amc_accounts!inner(account_id)')\
                .eq('instance_id', instance_id)\
                .execute()
            
            if not instance_response.data:
                return {
                    "status": "failed",
                    "error": f"AMC instance {instance_id} not found"
                }
            
            instance = instance_response.data[0]
            entity_id = instance['amc_accounts']['account_id']
            marketplace_id = instance['amc_accounts'].get('marketplace_id', 'ATVPDKIKX0DER')
            
            logger.info(f"Executing on instance {instance_id} with entity {entity_id}")

            # Process all parameters - both template placeholders and SQL injection
            processed_sql_query = sql_query
            template_params = {}
            sql_injection_params = {}

            if execution_parameters:
                # Step 1: Categorize parameters
                for param_name, param_value in execution_parameters.items():
                    # Check if this is a SQL injection parameter (campaigns/ASINs)
                    if isinstance(param_value, dict) and param_value.get('_sqlInject'):
                        sql_injection_params[param_name] = param_value
                        logger.info(f"SQL injection parameter detected: {param_name} with {len(param_value.get('_values', []))} values")
                    # Check if this is a legacy array parameter that should be converted to SQL injection
                    elif isinstance(param_value, list) and self._is_campaign_or_asin_param(param_name):
                        sql_injection_params[param_name] = param_value
                        logger.info(f"Converting legacy array parameter {param_name} to SQL injection with {len(param_value)} values")
                    else:
                        # Regular template parameters that need substitution
                        template_params[param_name] = param_value

                # Step 2: Apply template parameter substitution FIRST
                if template_params:
                    logger.info(f"Processing {len(template_params)} template parameters: {list(template_params.keys())}")
                    try:
                        # Use ParameterProcessor with validate_all=False for partial processing
                        # This allows SQL injection params to be handled separately
                        processed_sql_query = ParameterProcessor.process_sql_parameters(
                            processed_sql_query, template_params, validate_all=False
                        )
                        logger.info("Successfully replaced template placeholders")
                    except ValueError as e:
                        logger.error(f"Failed to substitute template parameters: {e}")
                        # Return error to user instead of sending invalid SQL to AMC
                        self._update_execution_completed(
                            execution_id=execution_id,
                            amc_execution_id=execution_id,
                            row_count=0,
                            error_message=f"Parameter substitution failed: {str(e)}"
                        )
                        return {
                            "status": "failed",
                            "error": f"Parameter substitution failed: {str(e)}"
                        }

                # Step 3: Apply SQL injection parameters
                for param_name, param_value in sql_injection_params.items():
                    if isinstance(param_value, dict) and param_value.get('_sqlInject'):
                        # Apply SQL injection to query
                        values_clause = param_value.get('_valuesClause', '')
                        if values_clause:
                            # Replace parameter placeholder with VALUES clause
                            param_pattern = f"{{{{{param_name}}}}}"
                            processed_sql_query = processed_sql_query.replace(param_pattern, f"VALUES\n{values_clause}")
                            logger.info(f"Applied SQL injection for {param_name}: replaced {param_pattern} with VALUES clause")
                    elif isinstance(param_value, list):
                        # Convert legacy array to SQL injection
                        values_clause = '\n'.join([f"    ('{value}')" for value in param_value])
                        param_pattern = f"{{{{{param_name}}}}}"
                        processed_sql_query = processed_sql_query.replace(param_pattern, f"VALUES\n{values_clause}")
                        logger.info(f"Applied SQL injection for legacy parameter {param_name}: replaced {param_pattern} with VALUES clause")

            # Step 4: Validate no placeholders remain
            import re
            placeholder_pattern = r'\{\{(\w+)\}\}'
            remaining_placeholders = re.findall(placeholder_pattern, processed_sql_query)

            if remaining_placeholders:
                error_msg = f"Missing parameter values for: {', '.join(remaining_placeholders)}"
                logger.error(f"Unresolved template placeholders found: {remaining_placeholders}")

                # Update execution as failed
                self._update_execution_completed(
                    execution_id=execution_id,
                    amc_execution_id=execution_id,
                    row_count=0,
                    error_message=error_msg
                )

                return {
                    "status": "failed",
                    "error": error_msg,
                    "missing_parameters": remaining_placeholders
                }

            logger.info(f"Template parameters substituted: {list(template_params.keys())}")
            logger.info(f"SQL injection parameters applied: {list(sql_injection_params.keys())}")
            logger.info(f"Final SQL query ready for AMC (length: {len(processed_sql_query)} chars)")
            # Log first 500 chars of SQL for debugging (without sensitive data)
            logger.debug(f"SQL preview: {processed_sql_query[:500]}...")
            
            # Create workflow execution via AMC API
            # Initialize API client with correct service
            api_client = AMCAPIClient()

            # Update progress to show we're starting
            self._update_execution_progress(execution_id, 'running', 10)

            try:
                # ALWAYS use ad-hoc execution - simpler and no size limits
                # This handles queries of any size without needing workflow management
                logger.info(f"Executing query via ad-hoc execution (query size: {len(processed_sql_query)} chars)")

                # Pass the template parameters (which include timeWindowStart/End) to AMC
                # These are needed for BUILT_IN_PARAMETER functions in the SQL
                logger.info(f"Template parameters for AMC execution: {template_params}")

                response = api_client.create_workflow_execution(
                    instance_id=instance_id,
                    sql_query=processed_sql_query,
                    access_token=valid_token,
                    entity_id=entity_id,
                    marketplace_id=marketplace_id,
                    parameter_values=template_params,  # Pass the date parameters for BUILT_IN_PARAMETER
                    output_format=execution_parameters.get('output_format', 'CSV') if execution_parameters else 'CSV'
                )
                
                # Check if execution was created successfully
                if not response.get('success'):
                    error_msg = response.get('error', 'Failed to create workflow execution')
                    error_details = response.get('errorDetails')
                    
                    # Format detailed error message if we have error details
                    if error_details:
                        detailed_error = error_msg
                        if error_details.get('validationErrors'):
                            detailed_error += "\n\nValidation Errors:\n" + "\n".join(error_details['validationErrors'])
                        if error_details.get('queryValidation'):
                            detailed_error += f"\n\nDetails: {error_details['queryValidation']}"
                        error_msg = detailed_error
                    
                    self._update_execution_completed(
                        execution_id=execution_id,
                        amc_execution_id=execution_id,
                        row_count=0,
                        error_message=error_msg
                    )
                    
                    result = {
                        "status": "failed",
                        "error": error_msg
                    }
                    
                    # Include errorDetails if available
                    if error_details:
                        result["errorDetails"] = error_details
                    
                    return result
                
                amc_execution_id = response.get('executionId', execution_id)
                logger.info(f"Created AMC execution: {amc_execution_id}")
                
                # Store the AMC execution ID in the database
                self._update_execution_amc_id(execution_id, amc_execution_id)
                
                # Start monitoring the execution to fetch results when completed
                # Note: We'll skip async monitoring for now since we're in a sync context
                # The frontend will poll for status updates
                logger.info(f"Execution {execution_id} created - frontend will poll for status")
                
                # Get execution record to get the UUID
                client = SupabaseManager.get_client(use_service_role=True)
                exec_response = client.table('workflow_executions')\
                    .select('id')\
                    .eq('execution_id', execution_id)\
                    .execute()
                
                execution_uuid = exec_response.data[0]['id'] if exec_response.data else None
                
                # Return immediately with pending status
                # The frontend will poll for status updates
                return {
                    "id": execution_uuid,  # Add internal UUID for historical collection service
                    "execution_id": execution_id,
                    "status": "pending",
                    "amc_execution_id": amc_execution_id,
                    "message": "Workflow execution started successfully"
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
    
    async def poll_and_update_execution(self, execution_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Poll AMC for execution status and update database
        This is called by the status endpoint to check real-time status
        """
        try:
            # Get execution record with AMC execution ID
            client = SupabaseManager.get_client(use_service_role=True)
            
            response = client.table('workflow_executions')\
                .select('*, workflows!inner(user_id, instance_id, amc_instances!inner(instance_id, amc_accounts!inner(account_id, marketplace_id)))')\
                .eq('execution_id', execution_id)\
                .execute()
            
            if not response.data:
                return None
            
            execution = response.data[0]
            
            # Verify user has access
            if execution['workflows']['user_id'] != user_id:
                return None
            
            # Skip if already completed or failed
            if execution['status'] in ['completed', 'failed']:
                return self.get_execution_status(execution_id, user_id)
            
            # Get AMC execution ID
            amc_execution_id = execution.get('amc_execution_id')
            if not amc_execution_id:
                logger.error(f"No AMC execution ID found for {execution_id}")
                return self.get_execution_status(execution_id, user_id)
            
            logger.info(f"AMC execution ID: {amc_execution_id}, Internal execution ID: {execution_id}")
            
            # Get instance details
            instance = execution['workflows']['amc_instances']
            instance_id = instance['instance_id']
            entity_id = instance['amc_accounts']['account_id']
            marketplace_id = instance['amc_accounts'].get('marketplace_id', 'ATVPDKIKX0DER')
            
            # Get valid token
            valid_token = await token_service.get_valid_token(user_id)
            if not valid_token:
                logger.error(f"No valid token for user {user_id}")
                return self.get_execution_status(execution_id, user_id)
            
            # Check status with AMC
            api_client = AMCAPIClient()
            
            # If in mock mode, simulate execution completion
            if not settings.amc_use_real_api:
                logger.info(f"Mock mode enabled - simulating execution completion for {execution_id}")
                # Simulate progression
                current_progress = execution.get('progress', 0)
                if current_progress < 100:
                    new_progress = min(current_progress + 30, 100)
                    new_status = 'completed' if new_progress >= 100 else 'running'
                    
                    self._update_execution_progress(execution_id, new_status, new_progress)
                    
                    if new_status == 'completed':
                        # Simulate some results
                        mock_results = {
                            "columns": ["date", "impressions", "clicks"],
                            "rows": [["2025-01-01", 1000, 50]],
                            "total_rows": 1,
                            "sample_size": 1
                        }
                        
                        # Store mock results
                        self._store_execution_results(execution_id, mock_results, row_count=1)
                    
                    return self.get_execution_status(execution_id, user_id)
                else:
                    return self.get_execution_status(execution_id, user_id)
            
            # Add a delay on first check to allow AMC to register the execution
            if execution.get('status') == 'pending' and execution.get('progress', 0) < 20:
                logger.info(f"First status check - execution status: {execution.get('status')}, progress: {execution.get('progress', 0)}")
                logger.info("Waiting 10 seconds for AMC to register execution...")
                time.sleep(10)
                logger.info("Delay complete, checking AMC status now")
            
            # Try status check with retry on first attempt
            max_retries = 3 if execution.get('progress', 0) < 20 else 1
            status_response = None
            
            for attempt in range(max_retries):
                status_response = api_client.get_execution_status(
                    execution_id=amc_execution_id,
                    access_token=valid_token,
                    entity_id=entity_id,
                    marketplace_id=marketplace_id,
                    instance_id=instance_id
                )
                
                if status_response.get('success'):
                    break
                    
                # If execution not found and this is not the last attempt, wait and retry
                error_msg = status_response.get('error', '')
                if 'does not exist' in error_msg and attempt < max_retries - 1:
                    logger.info(f"Execution not found on attempt {attempt + 1}, waiting 10 seconds before retry...")
                    time.sleep(10)
                    
                    # On second attempt, try listing executions to find it
                    if attempt == 1:
                        logger.info("Trying to find execution by listing all executions...")
                        list_response = api_client.list_executions(
                            instance_id=instance_id,
                            access_token=valid_token,
                            entity_id=entity_id,
                            marketplace_id=marketplace_id,
                            limit=10
                        )
                        
                        if list_response.get('success'):
                            executions = list_response.get('executions', [])
                            logger.info(f"Found {len(executions)} recent executions")
                            for exec_item in executions:
                                logger.info(f"Execution: {exec_item.get('workflowExecutionId', 'N/A')} - Status: {exec_item.get('status', 'N/A')}")
                else:
                    break
            
            if status_response.get('success'):
                status = status_response.get('status', 'running')
                progress = status_response.get('progress', 50)
                
                # Update our execution record
                self._update_execution_progress(execution_id, status, progress)
                
                # If completed, fetch results
                if status == 'completed':
                    logger.info(f"Execution {execution_id} completed, fetching results from S3...")
                    results_response = api_client.get_execution_results(
                        execution_id=amc_execution_id,
                        access_token=valid_token,
                        entity_id=entity_id,
                        marketplace_id=marketplace_id,
                        instance_id=instance_id
                    )
                    
                    if results_response.get('success'):
                        logger.info(f"Successfully fetched results for execution {execution_id}")
                        logger.info(f"Results: {results_response.get('rowCount', 0)} rows, {len(results_response.get('columns', []))} columns")
                        
                        result_data = {
                            "columns": results_response.get('columns', []),
                            "rows": results_response.get('rows', []),
                            "total_rows": results_response.get('rowCount', 0),
                            "sample_size": results_response.get('rowCount', 0),
                            "execution_details": results_response.get('metadata', {})
                        }
                        
                        logger.info(f"Storing results in database for execution {execution_id}...")
                        self._update_execution_completed(
                            execution_id=execution_id,
                            amc_execution_id=amc_execution_id,
                            row_count=result_data['total_rows'],
                            results=result_data
                        )
                    else:
                        logger.error(f"Failed to fetch results for execution {execution_id}: {results_response.get('error')}")
                elif status == 'failed':
                    error_msg = status_response.get('error', 'Query execution failed')
                    error_details = status_response.get('errorDetails', {})
                    
                    # Format detailed error message
                    detailed_error = error_msg
                    if error_details:
                        if error_details.get('validationErrors'):
                            detailed_error += "\n\nValidation Errors:\n" + "\n".join(error_details['validationErrors'])
                        if error_details.get('errorCode'):
                            detailed_error += f"\n\nError Code: {error_details['errorCode']}"
                        if error_details.get('errorMessage') and error_details['errorMessage'] != error_msg:
                            detailed_error += f"\n\nDetails: {error_details['errorMessage']}"
                        if error_details.get('queryValidation'):
                            detailed_error += f"\n\nQuery Validation: {error_details['queryValidation']}"
                    
                    self._update_execution_completed(
                        execution_id=execution_id,
                        amc_execution_id=amc_execution_id,
                        row_count=0,
                        error_message=detailed_error,
                        error_details=error_details
                    )
            
            # Return current status
            return self.get_execution_status(execution_id, user_id)
            
        except Exception as e:
            logger.error(f"Error polling execution status: {e}")
            return self.get_execution_status(execution_id, user_id)
    
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
                "id": execution['id'],  # Internal UUID for foreign key reference
                "execution_id": execution['execution_id'],  # AMC's execution ID
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
    
    def _update_execution_amc_id(self, execution_id: str, amc_execution_id: str):
        """Update execution with AMC execution ID"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            client.table('workflow_executions')\
                .update({"amc_execution_id": amc_execution_id})\
                .eq('execution_id', execution_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Error updating AMC execution ID: {e}")
    
    def _update_execution_completed(
        self, 
        execution_id: str, 
        amc_execution_id: str,
        row_count: int = 0,
        error_message: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
        error_details: Optional[Dict[str, Any]] = None
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