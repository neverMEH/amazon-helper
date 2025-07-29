"""AMC Workflow Management Service"""

import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from croniter import croniter

from ..core import AMCAPIClient, AMCAPIEndpoints, get_logger
from ..core.exceptions import APIError, ValidationError, WorkflowError


logger = get_logger(__name__)


class WorkflowService:
    """Service for managing AMC workflows"""
    
    def __init__(self, api_client: AMCAPIClient):
        """
        Initialize workflow service
        
        Args:
            api_client: Configured AMC API client
        """
        self.api_client = api_client
        
    async def create_workflow(
        self,
        instance_id: str,
        user_id: str,
        user_token: Dict[str, Any],
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new AMC workflow
        
        Args:
            instance_id: AMC instance ID
            user_id: User identifier
            user_token: User's auth token
            workflow_data: Workflow configuration including SQL query
            
        Returns:
            Created workflow details
        """
        # Validate workflow data
        self._validate_workflow_data(workflow_data)
        
        # Generate workflow ID if not provided
        if 'workflowId' not in workflow_data:
            workflow_data['workflowId'] = f"wf_{uuid.uuid4().hex[:12]}"
            
        # Add metadata
        workflow_data['createdAt'] = datetime.utcnow().isoformat()
        workflow_data['createdBy'] = user_id
        workflow_data['status'] = 'active'
        
        try:
            endpoint = AMCAPIEndpoints.WORKFLOWS.format(instance_id=instance_id)
            response = self.api_client.post(
                endpoint,
                user_id,
                user_token,
                json_data=workflow_data
            )
            
            logger.info(f"Created workflow {workflow_data['workflowId']} in instance {instance_id}")
            return response
            
        except APIError as e:
            logger.error(f"Failed to create workflow: {e}")
            raise WorkflowError(f"Failed to create workflow: {str(e)}")
            
    async def list_workflows(
        self,
        instance_id: str,
        user_id: str,
        user_token: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List workflows in an AMC instance
        
        Args:
            instance_id: AMC instance ID
            user_id: User identifier
            user_token: User's auth token
            filters: Optional filters (status, created_after, etc.)
            
        Returns:
            List of workflows
        """
        try:
            endpoint = AMCAPIEndpoints.WORKFLOWS.format(instance_id=instance_id)
            params = filters or {}
            
            response = self.api_client.get(
                endpoint,
                user_id,
                user_token,
                params=params
            )
            
            workflows = response.get('workflows', [])
            logger.info(f"Retrieved {len(workflows)} workflows from instance {instance_id}")
            
            # Enrich workflow data
            for workflow in workflows:
                workflow['has_schedule'] = bool(workflow.get('schedules'))
                workflow['last_execution'] = workflow.get('lastExecutionTime')
                
            return workflows
            
        except APIError as e:
            logger.error(f"Failed to list workflows: {e}")
            raise
            
    async def get_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        user_id: str,
        user_token: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get detailed workflow information
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Workflow ID
            user_id: User identifier
            user_token: User's auth token
            
        Returns:
            Workflow details
        """
        try:
            endpoint = AMCAPIEndpoints.WORKFLOW_DETAIL.format(
                instance_id=instance_id,
                workflow_id=workflow_id
            )
            
            response = self.api_client.get(
                endpoint,
                user_id,
                user_token
            )
            
            logger.info(f"Retrieved workflow {workflow_id} from instance {instance_id}")
            return response
            
        except APIError as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            raise
            
    async def update_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        user_id: str,
        user_token: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing workflow
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Workflow ID
            user_id: User identifier
            user_token: User's auth token
            updates: Fields to update
            
        Returns:
            Updated workflow details
        """
        # Validate updates
        if 'sqlQuery' in updates:
            self._validate_sql_query(updates['sqlQuery'])
            
        updates['updatedAt'] = datetime.utcnow().isoformat()
        updates['updatedBy'] = user_id
        
        try:
            endpoint = AMCAPIEndpoints.WORKFLOW_DETAIL.format(
                instance_id=instance_id,
                workflow_id=workflow_id
            )
            
            response = self.api_client.patch(
                endpoint,
                user_id,
                user_token,
                json_data=updates
            )
            
            logger.info(f"Updated workflow {workflow_id} in instance {instance_id}")
            return response
            
        except APIError as e:
            logger.error(f"Failed to update workflow {workflow_id}: {e}")
            raise WorkflowError(f"Failed to update workflow: {str(e)}")
            
    async def delete_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        user_id: str,
        user_token: Dict[str, Any]
    ) -> bool:
        """
        Delete a workflow
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Workflow ID
            user_id: User identifier
            user_token: User's auth token
            
        Returns:
            True if successful
        """
        try:
            endpoint = AMCAPIEndpoints.WORKFLOW_DETAIL.format(
                instance_id=instance_id,
                workflow_id=workflow_id
            )
            
            self.api_client.delete(
                endpoint,
                user_id,
                user_token
            )
            
            logger.info(f"Deleted workflow {workflow_id} from instance {instance_id}")
            return True
            
        except APIError as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            raise WorkflowError(f"Failed to delete workflow: {str(e)}")
            
    async def execute_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        user_id: str,
        user_token: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Workflow ID
            user_id: User identifier
            user_token: User's auth token
            parameters: Execution parameters (timeWindowStart, timeWindowEnd, etc.)
            
        Returns:
            Execution details including execution ID
        """
        execution_data = {
            'executionId': f"exec_{uuid.uuid4().hex[:12]}",
            'parameters': parameters or {},
            'triggeredBy': user_id,
            'triggeredAt': datetime.utcnow().isoformat()
        }
        
        try:
            endpoint = AMCAPIEndpoints.WORKFLOW_EXECUTE.format(
                instance_id=instance_id,
                workflow_id=workflow_id
            )
            
            response = self.api_client.post(
                endpoint,
                user_id,
                user_token,
                json_data=execution_data
            )
            
            logger.info(f"Executed workflow {workflow_id} with execution ID {response.get('executionId')}")
            return response
            
        except APIError as e:
            logger.error(f"Failed to execute workflow {workflow_id}: {e}")
            raise WorkflowError(f"Failed to execute workflow: {str(e)}")
            
    async def create_schedule(
        self,
        instance_id: str,
        workflow_id: str,
        user_id: str,
        user_token: Dict[str, Any],
        schedule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a schedule for workflow execution
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Workflow ID
            user_id: User identifier
            user_token: User's auth token
            schedule_data: Schedule configuration with CRON expression
            
        Returns:
            Schedule details
        """
        # Validate CRON expression
        if 'cronExpression' in schedule_data:
            self._validate_cron_expression(schedule_data['cronExpression'])
            
        schedule_data['scheduleId'] = f"sched_{uuid.uuid4().hex[:12]}"
        schedule_data['createdAt'] = datetime.utcnow().isoformat()
        schedule_data['status'] = 'active'
        
        try:
            endpoint = AMCAPIEndpoints.WORKFLOW_SCHEDULE.format(
                instance_id=instance_id,
                workflow_id=workflow_id
            )
            
            response = self.api_client.post(
                endpoint,
                user_id,
                user_token,
                json_data=schedule_data
            )
            
            logger.info(f"Created schedule for workflow {workflow_id}")
            return response
            
        except APIError as e:
            logger.error(f"Failed to create schedule for workflow {workflow_id}: {e}")
            raise WorkflowError(f"Failed to create schedule: {str(e)}")
            
    async def list_schedules(
        self,
        instance_id: str,
        workflow_id: str,
        user_id: str,
        user_token: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        List schedules for a workflow
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Workflow ID
            user_id: User identifier
            user_token: User's auth token
            
        Returns:
            List of schedules
        """
        try:
            endpoint = AMCAPIEndpoints.WORKFLOW_SCHEDULE.format(
                instance_id=instance_id,
                workflow_id=workflow_id
            )
            
            response = self.api_client.get(
                endpoint,
                user_id,
                user_token
            )
            
            schedules = response.get('schedules', [])
            
            # Calculate next run times
            for schedule in schedules:
                if schedule.get('cronExpression') and schedule.get('status') == 'active':
                    cron = croniter(schedule['cronExpression'])
                    schedule['nextRunTime'] = cron.get_next(datetime).isoformat()
                    
            return schedules
            
        except APIError as e:
            logger.error(f"Failed to list schedules for workflow {workflow_id}: {e}")
            raise
            
    def _validate_workflow_data(self, workflow_data: Dict[str, Any]):
        """Validate workflow configuration"""
        required_fields = ['name', 'sqlQuery']
        
        for field in required_fields:
            if field not in workflow_data:
                raise ValidationError(f"Missing required field: {field}")
                
        if not workflow_data['name'].strip():
            raise ValidationError("Workflow name cannot be empty")
            
        self._validate_sql_query(workflow_data['sqlQuery'])
        
    def _validate_sql_query(self, sql_query: str):
        """Basic validation of AMC SQL query"""
        if not sql_query or not sql_query.strip():
            raise ValidationError("SQL query cannot be empty")
            
        # Check for basic SQL structure
        sql_lower = sql_query.lower().strip()
        if not sql_lower.startswith('select'):
            raise ValidationError("AMC queries must start with SELECT")
            
        # Check for required FROM clause
        if 'from' not in sql_lower:
            raise ValidationError("AMC queries must include a FROM clause")
            
    def _validate_cron_expression(self, cron_expression: str):
        """Validate CRON expression"""
        try:
            croniter(cron_expression)
        except Exception as e:
            raise ValidationError(f"Invalid CRON expression: {str(e)}")