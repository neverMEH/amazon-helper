"""Schedule Management Service for workflow scheduling"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from croniter import croniter

from ..core.logger_simple import get_logger
from ..core.supabase_client import SupabaseManager
from .db_service import db_service

logger = get_logger(__name__)


class ScheduleService:
    """Service for managing workflow schedules"""
    
    def __init__(self):
        self.db = db_service
    
    def create_schedule(
        self,
        workflow_id: str,
        cron_expression: str,
        user_id: str,
        timezone: str = "UTC",
        default_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a schedule for a workflow
        
        Args:
            workflow_id: Workflow ID (external)
            cron_expression: CRON expression for scheduling
            user_id: User ID
            timezone: Timezone for schedule (default: UTC)
            default_parameters: Default parameters for scheduled executions
            
        Returns:
            Created schedule details
        """
        try:
            # Validate CRON expression
            if not self._validate_cron_expression(cron_expression):
                raise ValueError(f"Invalid CRON expression: {cron_expression}")
            
            # Get workflow to verify access and get internal ID
            workflow = self.db.get_workflow_by_id_sync(workflow_id)
            if not workflow:
                raise ValueError("Workflow not found")
            
            if workflow['user_id'] != user_id:
                raise ValueError("Access denied to workflow")
            
            # Check if schedule already exists
            existing = self._get_workflow_schedules(workflow['id'])
            if existing:
                # For now, limit to one schedule per workflow
                raise ValueError("Workflow already has a schedule. Delete existing schedule first.")
            
            # Calculate next run time
            cron = croniter(cron_expression, datetime.utcnow())
            next_run = cron.get_next(datetime)
            
            # Create schedule
            schedule_data = {
                "schedule_id": f"sched_{uuid.uuid4().hex[:12]}",
                "workflow_id": workflow['id'],  # Use internal UUID
                "cron_expression": cron_expression,
                "timezone": timezone,
                "default_parameters": default_parameters or {},
                "is_active": True,
                "next_run_at": next_run.isoformat()
            }
            
            client = SupabaseManager.get_client(use_service_role=True)
            response = client.table('workflow_schedules').insert(schedule_data).execute()
            
            if not response.data:
                raise ValueError("Failed to create schedule")
            
            created = response.data[0]
            
            return {
                "schedule_id": created['schedule_id'],
                "workflow_id": workflow_id,
                "cron_expression": created['cron_expression'],
                "timezone": created['timezone'],
                "is_active": created['is_active'],
                "next_run_at": created['next_run_at'],
                "created_at": created['created_at']
            }
            
        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            raise
    
    def get_schedule(self, schedule_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule details"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            response = client.table('workflow_schedules')\
                .select('*, workflows!inner(workflow_id, user_id)')\
                .eq('schedule_id', schedule_id)\
                .execute()
            
            if not response.data:
                return None
            
            schedule = response.data[0]
            
            # Verify user has access
            if schedule['workflows']['user_id'] != user_id:
                return None
            
            return {
                "schedule_id": schedule['schedule_id'],
                "workflow_id": schedule['workflows']['workflow_id'],
                "cron_expression": schedule['cron_expression'],
                "timezone": schedule['timezone'],
                "default_parameters": schedule.get('default_parameters', {}),
                "is_active": schedule['is_active'],
                "last_run_at": schedule.get('last_run_at'),
                "next_run_at": schedule.get('next_run_at'),
                "created_at": schedule['created_at'],
                "updated_at": schedule['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            return None
    
    def list_schedules(self, workflow_id: str, user_id: str) -> List[Dict[str, Any]]:
        """List all schedules for a workflow"""
        try:
            # Get workflow to verify access
            workflow = self.db.get_workflow_by_id_sync(workflow_id)
            if not workflow or workflow['user_id'] != user_id:
                return []
            
            schedules = self._get_workflow_schedules(workflow['id'])
            
            return [{
                "schedule_id": s['schedule_id'],
                "workflow_id": workflow_id,
                "cron_expression": s['cron_expression'],
                "timezone": s['timezone'],
                "is_active": s['is_active'],
                "last_run_at": s.get('last_run_at'),
                "next_run_at": s.get('next_run_at'),
                "created_at": s['created_at']
            } for s in schedules]
            
        except Exception as e:
            logger.error(f"Error listing schedules: {e}")
            return []
    
    def update_schedule(
        self,
        schedule_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a schedule"""
        try:
            # Get current schedule
            current = self.get_schedule(schedule_id, user_id)
            if not current:
                return None
            
            # Validate new CRON expression if provided
            if 'cron_expression' in updates:
                if not self._validate_cron_expression(updates['cron_expression']):
                    raise ValueError(f"Invalid CRON expression: {updates['cron_expression']}")
                
                # Calculate new next run time
                cron = croniter(updates['cron_expression'], datetime.utcnow())
                updates['next_run_at'] = cron.get_next(datetime).isoformat()
            
            # Update schedule
            client = SupabaseManager.get_client(use_service_role=True)
            response = client.table('workflow_schedules')\
                .update(updates)\
                .eq('schedule_id', schedule_id)\
                .execute()
            
            if not response.data:
                return None
            
            return self.get_schedule(schedule_id, user_id)
            
        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            return None
    
    def delete_schedule(self, schedule_id: str, user_id: str) -> bool:
        """Delete a schedule"""
        try:
            # Verify access
            schedule = self.get_schedule(schedule_id, user_id)
            if not schedule:
                return False
            
            client = SupabaseManager.get_client(use_service_role=True)
            response = client.table('workflow_schedules')\
                .delete()\
                .eq('schedule_id', schedule_id)\
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting schedule: {e}")
            return False
    
    def get_due_schedules(self) -> List[Dict[str, Any]]:
        """Get all schedules that are due to run"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # Get active schedules where next_run_at is in the past
            response = client.table('workflow_schedules')\
                .select('*, workflows!inner(workflow_id, instance_id, user_id)')\
                .eq('is_active', True)\
                .lte('next_run_at', datetime.utcnow().isoformat())\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error fetching due schedules: {e}")
            return []
    
    def update_schedule_after_run(
        self,
        schedule_id: str,
        execution_id: Optional[str] = None,
        success: bool = True
    ):
        """Update schedule after execution"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # Get current schedule
            response = client.table('workflow_schedules')\
                .select('*')\
                .eq('schedule_id', schedule_id)\
                .execute()
            
            if not response.data:
                return
            
            schedule = response.data[0]
            
            # Calculate next run time
            cron = croniter(schedule['cron_expression'], datetime.utcnow())
            next_run = cron.get_next(datetime)
            
            # Update schedule
            update_data = {
                "last_run_at": datetime.utcnow().isoformat(),
                "next_run_at": next_run.isoformat()
            }
            
            client.table('workflow_schedules')\
                .update(update_data)\
                .eq('schedule_id', schedule_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Error updating schedule after run: {e}")
    
    def _validate_cron_expression(self, cron_expression: str) -> bool:
        """Validate CRON expression"""
        try:
            croniter(cron_expression)
            return True
        except Exception:
            return False
    
    def _get_workflow_schedules(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get schedules for a workflow (internal ID)"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            response = client.table('workflow_schedules')\
                .select('*')\
                .eq('workflow_id', workflow_id)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error fetching workflow schedules: {e}")
            return []


# Singleton instance
schedule_service = ScheduleService()