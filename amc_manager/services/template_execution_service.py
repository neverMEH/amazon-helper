"""
Template Execution Service for Query Flow Templates
Integrates with existing AMC execution pipeline
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..services.db_service import DatabaseService, with_connection_retry
from ..services.parameter_engine import ParameterEngine, ParameterValidationError
from ..services.amc_execution_service import AMCExecutionService
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class TemplateExecutionService(DatabaseService):
    """Service for executing query flow templates"""
    
    def __init__(self):
        super().__init__()
        self.parameter_engine = ParameterEngine()
        self.amc_execution_service = AMCExecutionService()
    
    async def execute_template(
        self,
        template_id: str,
        template_data: Dict[str, Any],
        instance_id: str,
        parameters: Dict[str, Any],
        user_id: str,
        schedule_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a query flow template
        
        Args:
            template_id: Template UUID
            template_data: Full template data including parameters and SQL
            instance_id: AMC instance ID to execute on
            parameters: User-provided parameter values
            user_id: Executing user ID
            schedule_id: Optional schedule ID if triggered by schedule
            
        Returns:
            Execution record with status
        """
        try:
            # Start tracking execution
            execution_record = self._create_execution_record(
                template_id=template_id,
                instance_id=instance_id,
                parameters=parameters,
                user_id=user_id
            )
            
            execution_id = execution_record['id']
            
            try:
                # Process parameters and generate SQL
                logger.info(f"Processing template parameters for execution {execution_id}")
                
                # First, handle parameter dependencies and transformations
                processed_params = self._process_parameter_dependencies(
                    template_data['parameters'],
                    parameters
                )
                
                # Validate parameters
                validated_params = self.parameter_engine.validate_parameters(
                    parameter_definitions=template_data['parameters'],
                    parameter_values=processed_params
                )
                
                # Process the SQL template with validated parameters
                processed_sql = self.parameter_engine.process_template(
                    sql_template=template_data['sql_template'],
                    parameters=template_data['parameters'],
                    parameter_values=validated_params
                )
                
                logger.info(f"SQL processed successfully for execution {execution_id}")
                
                # Create or get workflow for this execution
                workflow_data = await self._create_workflow_from_template(
                    template_data=template_data,
                    processed_sql=processed_sql,
                    instance_id=instance_id,
                    user_id=user_id
                )
                
                workflow_id = workflow_data['id']
                
                # Update execution record with workflow
                self._update_execution_record(
                    execution_id=execution_id,
                    updates={'workflow_id': workflow_id, 'status': 'executing'}
                )
                
                # Execute via AMC execution service
                logger.info(f"Executing workflow {workflow_id} for template execution {execution_id}")
                
                amc_execution = await self.amc_execution_service.execute_workflow(
                    workflow_id=workflow_id,
                    user_id=user_id,
                    execution_parameters=validated_params,
                    triggered_by='template' if not schedule_id else 'schedule',
                    instance_id=instance_id
                )
                
                # Update execution record with AMC execution details
                self._update_execution_record(
                    execution_id=execution_id,
                    updates={
                        'execution_id': amc_execution.get('id'),
                        'status': amc_execution.get('status', 'running')
                    }
                )
                
                # Update template execution count
                self._increment_template_execution_count(template_id)
                
                return {
                    'execution_id': execution_id,
                    'template_id': template_id,
                    'workflow_id': workflow_id,
                    'amc_execution_id': amc_execution.get('id'),
                    'status': amc_execution.get('status', 'running'),
                    'created_at': execution_record['created_at']
                }
                
            except ParameterValidationError as e:
                # Update execution as failed
                self._update_execution_record(
                    execution_id=execution_id,
                    updates={
                        'status': 'failed',
                        'error_details': {'type': 'validation_error', 'message': str(e)},
                        'completed_at': datetime.utcnow().isoformat()
                    }
                )
                raise
                
            except Exception as e:
                # Update execution as failed
                self._update_execution_record(
                    execution_id=execution_id,
                    updates={
                        'status': 'failed',
                        'error_details': {'type': 'execution_error', 'message': str(e)},
                        'completed_at': datetime.utcnow().isoformat()
                    }
                )
                raise
                
        except Exception as e:
            logger.error(f"Error executing template {template_id}: {e}")
            raise
    
    @with_connection_retry
    async def get_executions(
        self,
        template_id: Optional[str] = None,
        user_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get execution history with filtering
        
        Args:
            template_id: Filter by template
            user_id: Filter by user
            instance_id: Filter by instance
            status: Filter by status
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Executions with metadata
        """
        try:
            query = self.client.table('template_executions').select(
                '*',
                count='exact'
            )
            
            # Apply filters
            if template_id:
                query = query.eq('template_id', template_id)
            if user_id:
                query = query.eq('user_id', user_id)
            if instance_id:
                query = query.eq('instance_id', instance_id)
            if status:
                query = query.eq('status', status)
            
            # Order by creation date
            query = query.order('created_at', desc=True)
            
            # Pagination
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            
            return {
                'executions': result.data,
                'total_count': result.count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < result.count
            }
            
        except Exception as e:
            logger.error(f"Error getting executions: {e}")
            return {
                'executions': [],
                'total_count': 0,
                'limit': limit,
                'offset': offset,
                'has_more': False
            }
    
    @with_connection_retry
    def _create_execution_record(
        self,
        template_id: str,
        instance_id: str,
        parameters: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Create execution record in database"""
        try:
            execution_data = {
                'template_id': template_id,
                'user_id': user_id,
                'instance_id': instance_id,
                'parameters_used': parameters,
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('template_executions')\
                .insert(execution_data)\
                .execute()
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error creating execution record: {e}")
            raise
    
    @with_connection_retry
    def _update_execution_record(
        self,
        execution_id: str,
        updates: Dict[str, Any]
    ) -> None:
        """Update execution record"""
        try:
            self.client.table('template_executions')\
                .update(updates)\
                .eq('id', execution_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Error updating execution record {execution_id}: {e}")
    
    async def _create_workflow_from_template(
        self,
        template_data: Dict[str, Any],
        processed_sql: str,
        instance_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create or get a workflow from template
        
        For now, creates a new workflow each time.
        In the future, could cache workflows for identical parameter sets.
        """
        try:
            # Generate unique workflow ID for this execution
            workflow_name = f"{template_data['name']} - {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            workflow_data = {
                'name': workflow_name,
                'sql_query': processed_sql,
                'instance_id': instance_id,
                'user_id': user_id,
                'is_template_generated': True,
                'template_id': template_data['id'],
                'description': f"Generated from template: {template_data['name']}",
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Create workflow directly in Supabase
            result = self.client.table('workflows')\
                .insert(workflow_data)\
                .execute()
            
            if not result.data:
                raise Exception("Failed to create workflow")
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error creating workflow from template: {e}")
            raise
    
    def _process_parameter_dependencies(
        self,
        parameter_definitions: List[Dict[str, Any]],
        user_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process parameter dependencies and compute derived values
        
        For example:
        - If date_range is provided, compute start_date and end_date
        - If campaigns are selected, generate campaign_filter SQL
        - If brand_keywords are provided, generate brand_keyword_conditions
        """
        processed = user_parameters.copy()
        
        for param_def in parameter_definitions:
            param_name = param_def['parameter_name']
            dependencies = param_def.get('dependencies', [])
            
            # Handle date range to individual dates
            if param_name == 'start_date' and 'date_range' in dependencies:
                if 'date_range' in processed and 'start' in processed['date_range']:
                    processed['start_date'] = processed['date_range']['start']
            
            if param_name == 'end_date' and 'date_range' in dependencies:
                if 'date_range' in processed and 'end' in processed['date_range']:
                    processed['end_date'] = processed['date_range']['end']
            
            # Handle campaign filter generation
            if param_name == 'campaign_filter' and 'campaigns' in dependencies:
                if 'campaigns' in processed and processed['campaigns']:
                    # Generate SQL filter
                    campaign_list = processed['campaigns']
                    if campaign_list:
                        quoted_campaigns = [f"'{c}'" for c in campaign_list]
                        processed['campaign_filter'] = f"AND campaign IN ({', '.join(quoted_campaigns)})"
                    else:
                        processed['campaign_filter'] = ''
                else:
                    processed['campaign_filter'] = ''
            
            # Handle brand keyword conditions
            if param_name == 'brand_keyword_conditions' and 'brand_keywords' in dependencies:
                if 'brand_keywords' in processed and processed['brand_keywords']:
                    conditions = []
                    for keyword in processed['brand_keywords']:
                        # Create case-insensitive pattern
                        pattern = f"(?i).*{keyword.replace(' ', '.?')}.*"
                        conditions.append(f"SUBSTRING(tracked_item, 9, 250) SIMILAR TO '{pattern}'")
                    
                    if conditions:
                        processed['brand_keyword_conditions'] = ' OR '.join(conditions)
                    else:
                        processed['brand_keyword_conditions'] = '1=0'  # No matches
                else:
                    processed['brand_keyword_conditions'] = '1=0'
        
        return processed
    
    @with_connection_retry
    def _increment_template_execution_count(self, template_id: str) -> None:
        """Increment template execution count"""
        try:
            # Get current count
            result = self.client.table('query_flow_templates')\
                .select('execution_count')\
                .eq('id', template_id)\
                .single()\
                .execute()
            
            current_count = result.data.get('execution_count', 0) or 0
            
            # Update count
            self.client.table('query_flow_templates')\
                .update({'execution_count': current_count + 1})\
                .eq('id', template_id)\
                .execute()
                
        except Exception as e:
            logger.warning(f"Failed to increment execution count for template {template_id}: {e}")
    
    async def update_execution_status(
        self,
        execution_id: str,
        amc_execution_id: str
    ) -> None:
        """
        Update execution status from AMC execution
        Called by background polling service
        """
        try:
            # Get AMC execution status
            amc_status = await self.amc_execution_service.get_execution_status(amc_execution_id)
            
            updates = {
                'status': amc_status['status']
            }
            
            if amc_status['status'] == 'completed':
                updates['completed_at'] = datetime.utcnow().isoformat()
                updates['execution_time_ms'] = amc_status.get('execution_time_ms')
                updates['result_summary'] = {
                    'row_count': amc_status.get('row_count'),
                    'data_scanned_gb': amc_status.get('data_scanned_gb')
                }
            
            elif amc_status['status'] == 'failed':
                updates['completed_at'] = datetime.utcnow().isoformat()
                updates['error_details'] = amc_status.get('error_details')
            
            self._update_execution_record(execution_id, updates)
            
        except Exception as e:
            logger.error(f"Error updating execution status for {execution_id}: {e}")