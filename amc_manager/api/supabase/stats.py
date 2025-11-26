"""Dashboard stats API endpoint for fast dashboard loading"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ...core.supabase_client import SupabaseManager
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard statistics including:
    - Instance counts and active status
    - Execution metrics with status breakdown
    - Schedule status and health
    - Recent activity summary
    """
    try:
        user_id = current_user['id']
        client = SupabaseManager.get_client(use_service_role=True)

        # Get account and instance IDs for this user
        accounts_result = client.table('amc_accounts')\
            .select('id')\
            .eq('user_id', user_id)\
            .execute()
        account_ids = [a['id'] for a in accounts_result.data] if accounts_result.data else []

        # Get instances with status
        instances_count = 0
        active_instances = 0
        instance_ids = []

        if account_ids:
            instances_result = client.table('amc_instances')\
                .select('id, status')\
                .in_('account_id', account_ids)\
                .execute()

            if instances_result.data:
                instances_count = len(instances_result.data)
                active_instances = len([i for i in instances_result.data if i.get('status') == 'active'])
                instance_ids = [i['id'] for i in instances_result.data]

        # Count workflows
        workflows_result = client.table('workflows')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        workflows_count = workflows_result.count if workflows_result.count is not None else 0

        # Get execution stats (last 7 days with status breakdown)
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        twenty_four_hours_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()

        executions_result = client.table('workflow_executions')\
            .select('id, status, started_at, completed_at')\
            .eq('user_id', user_id)\
            .gte('started_at', seven_days_ago)\
            .order('started_at', desc=True)\
            .execute()

        executions_data = executions_result.data or []
        total_executions_7d = len(executions_data)

        # Calculate status breakdown
        status_counts = {'completed': 0, 'failed': 0, 'running': 0, 'pending': 0}
        executions_24h = 0

        for ex in executions_data:
            status = (ex.get('status') or 'pending').lower()
            if status in status_counts:
                status_counts[status] += 1

            # Count 24h executions
            started = ex.get('started_at')
            if started and started >= twenty_four_hours_ago:
                executions_24h += 1

        # Calculate success rate
        completed_or_failed = status_counts['completed'] + status_counts['failed']
        success_rate = round((status_counts['completed'] / completed_or_failed * 100), 1) if completed_or_failed > 0 else 0

        # Get schedule stats
        schedules_result = client.table('workflow_schedules')\
            .select('id, is_active, last_run_at, next_run_at, consecutive_failures')\
            .eq('user_id', user_id)\
            .execute()

        schedules_data = schedules_result.data or []
        total_schedules = len(schedules_data)
        active_schedules = len([s for s in schedules_data if s.get('is_active')])

        # Find schedules needing attention (consecutive failures > 2)
        failing_schedules = len([s for s in schedules_data if s.get('consecutive_failures', 0) > 2])

        # Find upcoming schedules (next run within 24 hours)
        now = datetime.utcnow()
        tomorrow = now + timedelta(hours=24)
        upcoming_schedules = 0
        for s in schedules_data:
            if s.get('next_run_at') and s.get('is_active'):
                try:
                    next_run = datetime.fromisoformat(s['next_run_at'].replace('Z', '+00:00').replace('+00:00', ''))
                    if now <= next_run <= tomorrow:
                        upcoming_schedules += 1
                except:
                    pass

        # Get recent executions for activity feed (last 10)
        recent_executions_result = client.table('workflow_executions')\
            .select('''
                execution_id,
                status,
                started_at,
                completed_at,
                workflows!inner(name, amc_instances(instance_name))
            ''')\
            .eq('user_id', user_id)\
            .order('started_at', desc=True)\
            .limit(10)\
            .execute()

        recent_activity = []
        for ex in (recent_executions_result.data or []):
            workflow = ex.get('workflows') or {}
            instance = workflow.get('amc_instances') or {}
            recent_activity.append({
                'executionId': ex.get('execution_id'),
                'workflowName': workflow.get('name', 'Unknown'),
                'instanceName': instance.get('instance_name', 'Unknown'),
                'status': (ex.get('status') or 'pending').upper(),
                'startedAt': ex.get('started_at'),
                'completedAt': ex.get('completed_at'),
            })

        return {
            # Instance metrics
            "totalInstances": instances_count,
            "activeInstances": active_instances,

            # Workflow metrics
            "totalWorkflows": workflows_count,

            # Execution metrics
            "executions": {
                "total7d": total_executions_7d,
                "total24h": executions_24h,
                "successRate": success_rate,
                "statusBreakdown": {
                    "succeeded": status_counts['completed'],
                    "failed": status_counts['failed'],
                    "running": status_counts['running'],
                    "pending": status_counts['pending'],
                }
            },

            # Schedule metrics
            "schedules": {
                "total": total_schedules,
                "active": active_schedules,
                "failing": failing_schedules,
                "upcoming24h": upcoming_schedules,
            },

            # Recent activity feed
            "recentActivity": recent_activity,
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        # Return zeros instead of failing - dashboard should still render
        return {
            "totalInstances": 0,
            "activeInstances": 0,
            "totalWorkflows": 0,
            "executions": {
                "total7d": 0,
                "total24h": 0,
                "successRate": 0,
                "statusBreakdown": {
                    "succeeded": 0,
                    "failed": 0,
                    "running": 0,
                    "pending": 0,
                }
            },
            "schedules": {
                "total": 0,
                "active": 0,
                "failing": 0,
                "upcoming24h": 0,
            },
            "recentActivity": [],
        }
