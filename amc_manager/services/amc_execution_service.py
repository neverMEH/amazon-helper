"""AMC Workflow Execution Service - Handles execution of workflows on AMC instances"""

import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import re

from ..core.logger_simple import get_logger
from ..core.supabase_client import SupabaseManager
from .db_service import db_service
from .token_service import token_service
from .token_refresh_service import token_refresh_service
from .amc_api_client import AMCAPIClient

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
            client = SupabaseManager.get_client(use_service_role=True)
            
            # First try to find by UUID (id field)
            response = client.table('amc_instances')\
                .select('*, amc_accounts(*)')\
                .eq('id', instance_id)\
                .execute()
            
            if response.data:
                return response.data[0]
            
            # If not found, try by AMC instance_id
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
            client = SupabaseManager.get_client(use_service_role=True)
            
            response = client.table('workflows')\
                .select('*, amc_instances(*, amc_accounts(*))')\
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
        # Find all parameters in the template using multiple formats
        import re
        required_params = set()
        
        # Pattern for {{parameter}} format
        mustache_params = re.findall(r'\{\{(\w+)\}\}', sql_template)
        required_params.update(mustache_params)
        
        # Pattern for :parameter format  
        colon_params = re.findall(r':(\w+)\b', sql_template)
        required_params.update(colon_params)
        
        # Pattern for $parameter format
        dollar_params = re.findall(r'\$(\w+)\b', sql_template)
        required_params.update(dollar_params)
        
        required_params = list(required_params)
        
        # Check for missing required parameters
        missing_params = [p for p in required_params if p not in parameters]
        if missing_params:
            logger.error(f"Missing required parameters: {', '.join(missing_params)}")
            logger.error(f"Available parameters: {list(parameters.keys())}")
            logger.error(f"SQL template preview: {sql_template[:200]}...")
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
        
        # Substitute parameters with SQL injection prevention
        query = sql_template
        dangerous_keywords = ['DROP', 'DELETE FROM', 'INSERT INTO', 'UPDATE', 'ALTER', 
                            'CREATE', 'EXEC', 'EXECUTE', 'TRUNCATE', 'GRANT', 'REVOKE']
        
        for param, value in parameters.items():
            # Handle different value types
            if isinstance(value, (list, tuple)):
                # Validate and escape each list item
                escaped_values = []
                for v in value:
                    if isinstance(v, str):
                        # Escape single quotes
                        v_escaped = v.replace("'", "''")
                        # Check for dangerous SQL keywords
                        for keyword in dangerous_keywords:
                            if keyword in v_escaped.upper():
                                raise ValueError(f"Dangerous SQL keyword '{keyword}' detected in parameter '{param}'")
                        escaped_values.append(f"'{v_escaped}'")
                    else:
                        escaped_values.append(str(v))
                value_str = "({})".format(','.join(escaped_values))
            elif isinstance(value, str):
                # Escape single quotes to prevent SQL injection
                value_escaped = value.replace("'", "''")
                # Check for dangerous SQL keywords
                for keyword in dangerous_keywords:
                    if keyword in value_escaped.upper():
                        raise ValueError(f"Dangerous SQL keyword '{keyword}' detected in parameter '{param}'")
                value_str = f"'{value_escaped}'"
            else:
                value_str = str(value)
            
            # Replace multiple parameter formats
            old_query = query
            query = query.replace(f"{{{{{param}}}}}", value_str)  # {{param}} format
            query = query.replace(f":{param}", value_str)  # :param format  
            query = query.replace(f"${param}", value_str)  # $param format
            
            if old_query != query:
                logger.debug(f"Replaced parameter {param} with value: {value_str[:50]}...")
        
        # Log final query for debugging
        logger.debug(f"Final SQL after parameter substitution: {query[:300]}...")
        return query
    
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
            
            # Process SQL injection parameters - apply them to the SQL query
            processed_sql_query = sql_query
            amc_parameters = {}
            sql_injection_params = {}
            
            if execution_parameters:
                for param_name, param_value in execution_parameters.items():
                    # Check if this is a SQL injection parameter (campaigns/ASINs)
                    if isinstance(param_value, dict) and param_value.get('_sqlInject'):
                        sql_injection_params[param_name] = param_value
                        logger.info(f"SQL injection parameter detected: {param_name} with {len(param_value.get('_values', []))} values")
                        
                        # Apply SQL injection to query
                        values_clause = param_value.get('_valuesClause', '')
                        if values_clause:
                            # Replace parameter placeholder with VALUES clause
                            param_pattern = f"{{{{{param_name}}}}}"
                            processed_sql_query = processed_sql_query.replace(param_pattern, f"VALUES\n{values_clause}")
                            logger.info(f"Applied SQL injection for {param_name}: replaced {param_pattern} with VALUES clause")
                    # Check if this is a legacy array parameter that should be converted to SQL injection
                    elif isinstance(param_value, list) and self._is_campaign_or_asin_param(param_name):
                        # Convert legacy array to SQL injection
                        sql_injection_params[param_name] = param_value
                        logger.info(f"Converting legacy array parameter {param_name} to SQL injection with {len(param_value)} values")
                        
                        # Apply SQL injection to query
                        values_clause = '\n'.join([f"    ('{value}')" for value in param_value])
                        param_pattern = f"{{{{{param_name}}}}}"
                        processed_sql_query = processed_sql_query.replace(param_pattern, f"VALUES\n{values_clause}")
                        logger.info(f"Applied SQL injection for legacy parameter {param_name}: replaced {param_pattern} with VALUES clause")
                    else:
                        # Regular parameters (dates, etc.)
                        amc_parameters[param_name] = param_value
            
            logger.info(f"AMC parameters: {list(amc_parameters.keys())}")
            logger.info(f"SQL injection parameters: {list(sql_injection_params.keys())}")
            if processed_sql_query != sql_query:
                logger.info(f"SQL query modified by injection parameters")
            
            # Create workflow execution via AMC API
            # Initialize API client with correct service
            api_client = AMCAPIClient()
            
            # Update progress to show we're starting
            self._update_execution_progress(execution_id, 'running', 10)
            
            try:
                # Always try to execute using workflow ID first
                response = None
                if amc_workflow_id:
                    # Execute using saved workflow ID
                    logger.info(f"Executing saved workflow {amc_workflow_id}")
                    try:
                        response = api_client.create_workflow_execution(
                            instance_id=instance_id,
                            workflow_id=amc_workflow_id,
                            access_token=valid_token,
                            entity_id=entity_id,
                            marketplace_id=marketplace_id,
                            parameter_values=amc_parameters,  # Only pass non-injection parameters to AMC
                            output_format=amc_parameters.get('output_format', 'CSV')
                        )
                        
                        # Check if the response indicates the workflow doesn't exist
                        if isinstance(response, dict) and not response.get('success'):
                            error_msg = response.get('error', '')
                            if "does not exist" in str(error_msg).lower() or "not found" in str(error_msg).lower():
                                logger.info(f"Workflow {amc_workflow_id} not found (from response), will try to create it")
                                raise ValueError(f"Workflow not found: {error_msg}")
                    except (ValueError, Exception) as e:
                        # Check if the error is because the workflow doesn't exist in AMC
                        error_str = str(e)
                        logger.info(f"Caught exception during workflow execution: {error_str}")
                        if "does not exist" in error_str.lower() or "not found" in error_str.lower() or "workflow not found" in error_str.lower():
                            logger.warning(f"Workflow {amc_workflow_id} doesn't exist in AMC, will try to create it")
                            
                            # Try to create the workflow in AMC with processed query
                            create_response = api_client.create_workflow(
                                instance_id=instance_id,
                                workflow_id=amc_workflow_id,
                                sql_query=processed_sql_query,
                                access_token=valid_token,
                                entity_id=entity_id,
                                marketplace_id=marketplace_id,
                                output_format='CSV'
                            )
                            
                            if create_response.get('success'):
                                logger.info(f"Successfully created workflow {amc_workflow_id} in AMC, retrying execution")
                                # Update database to mark as synced
                                update_data = {
                                    'amc_workflow_id': amc_workflow_id,
                                    'is_synced_to_amc': True,
                                    'amc_sync_status': 'synced',
                                    'last_synced_at': datetime.now(timezone.utc).isoformat()
                                }
                                self.db.update_workflow_sync(workflow['workflow_id'], update_data)
                                
                                # Retry execution with the newly created workflow
                                response = api_client.create_workflow_execution(
                                    instance_id=instance_id,
                                    workflow_id=amc_workflow_id,
                                    access_token=valid_token,
                                    entity_id=entity_id,
                                    marketplace_id=marketplace_id,
                                    parameter_values=execution_parameters,
                                    output_format=execution_parameters.get('output_format', 'CSV') if execution_parameters else 'CSV'
                                )
                            else:
                                logger.warning(f"Failed to create workflow in AMC: {create_response.get('error')}, falling back to ad-hoc")
                                # Fall back to ad-hoc execution with processed query
                                response = api_client.create_workflow_execution(
                                    instance_id=instance_id,
                                    sql_query=processed_sql_query,
                                    access_token=valid_token,
                                    entity_id=entity_id,
                                    marketplace_id=marketplace_id,
                                    output_format=amc_parameters.get('output_format', 'CSV')
                                )
                        else:
                            # Other error, re-raise
                            raise
                
                # If we still don't have a response, use ad-hoc execution
                if not response:
                    logger.warning("No AMC workflow ID available, using ad-hoc execution")
                    response = api_client.create_workflow_execution(
                        instance_id=instance_id,
                        sql_query=processed_sql_query,
                        access_token=valid_token,
                        entity_id=entity_id,
                        marketplace_id=marketplace_id,
                        output_format=amc_parameters.get('output_format', 'CSV')
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
                
                # Return immediately with pending status
                # The frontend will poll for status updates
                return {
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