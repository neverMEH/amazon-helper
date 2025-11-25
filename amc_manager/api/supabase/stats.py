"""Dashboard stats API endpoint for fast dashboard loading"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
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
    Get aggregated dashboard statistics in a single efficient query.

    Returns counts instead of full lists for faster dashboard loading.
    Uses COUNT queries instead of fetching all records.
    """
    try:
        user_id = current_user['id']
        client = SupabaseManager.get_client(use_service_role=True)

        # Get instance IDs for this user first (needed for campaigns filter)
        accounts_result = client.table('amc_accounts')\
            .select('id')\
            .eq('user_id', user_id)\
            .execute()
        account_ids = [a['id'] for a in accounts_result.data] if accounts_result.data else []

        # Count instances
        if account_ids:
            instances_result = client.table('amc_instances')\
                .select('id', count='exact')\
                .in_('account_id', account_ids)\
                .execute()
            instances_count = instances_result.count if instances_result.count is not None else 0

            # Get instance IDs for campaigns filter
            instance_ids_result = client.table('amc_instances')\
                .select('id')\
                .in_('account_id', account_ids)\
                .execute()
            instance_ids = [i['id'] for i in instance_ids_result.data] if instance_ids_result.data else []
        else:
            instances_count = 0
            instance_ids = []

        # Count workflows for this user
        workflows_result = client.table('workflows')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        workflows_count = workflows_result.count if workflows_result.count is not None else 0

        # Count campaigns for user's instances
        if instance_ids:
            campaigns_result = client.table('campaigns')\
                .select('id', count='exact')\
                .in_('instance_id', instance_ids)\
                .execute()
            campaigns_count = campaigns_result.count if campaigns_result.count is not None else 0
        else:
            campaigns_count = 0

        # Count recent executions (last 7 days)
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        executions_result = client.table('workflow_executions')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .gte('started_at', seven_days_ago)\
            .execute()
        recent_executions_count = executions_result.count if executions_result.count is not None else 0

        return {
            "totalInstances": instances_count,
            "totalWorkflows": workflows_count,
            "totalCampaigns": campaigns_count,
            "recentExecutions": recent_executions_count
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        # Return zeros instead of failing - dashboard should still render
        return {
            "totalInstances": 0,
            "totalWorkflows": 0,
            "totalCampaigns": 0,
            "recentExecutions": 0
        }
