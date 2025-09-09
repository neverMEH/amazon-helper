#!/usr/bin/env python3
"""
Script to update stuck 'running' week statuses by checking their linked executions
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def update_stuck_weeks(collection_id: str = None, force_complete: bool = False):
    """
    Update week statuses that are stuck in 'running' state
    
    Args:
        collection_id: Optional - specific collection to update
        force_complete: If True, mark all running weeks as completed (use with caution!)
    """
    
    print("\n" + "="*80)
    print("UPDATING STUCK WEEK STATUSES")
    print("="*80)
    
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Build query for running weeks
        query = client.table('report_data_weeks')\
            .select('id, collection_id, week_start_date, week_end_date, status, execution_id, workflow_execution_id')
        
        # Filter by status
        query = query.eq('status', 'running')
        
        # Optionally filter by collection
        if collection_id:
            query = query.eq('collection_id', collection_id)
            print(f"\nChecking collection: {collection_id}")
        else:
            print("\nChecking all collections")
        
        # Execute query
        response = query.execute()
        
        if not response.data:
            print("✅ No running weeks found - all weeks have terminal status!")
            return True
        
        print(f"\nFound {len(response.data)} weeks in 'running' status")
        
        updated_count = 0
        completed_count = 0
        failed_count = 0
        still_running_count = 0
        
        for week in response.data:
            week_id = week['id']
            week_dates = f"{week['week_start_date']} to {week['week_end_date']}"
            
            # Get the execution ID (try both columns)
            exec_uuid = week.get('execution_id') or week.get('workflow_execution_id')
            
            if not exec_uuid and not force_complete:
                print(f"\n❌ Week {week_dates}: No execution ID linked")
                failed_count += 1
                continue
            
            if force_complete:
                # Force complete mode - mark as completed without checking execution
                print(f"\n⚠️  Force completing week {week_dates}")
                update_data = {
                    'status': 'completed',
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                update_response = client.table('report_data_weeks')\
                    .update(update_data)\
                    .eq('id', week_id)\
                    .execute()
                
                if update_response.data:
                    completed_count += 1
                    print(f"   ✅ Marked as completed (forced)")
                else:
                    print(f"   ❌ Failed to update")
                    failed_count += 1
                continue
            
            # Check the linked execution status
            exec_response = client.table('workflow_executions')\
                .select('execution_id, status, row_count')\
                .eq('id', exec_uuid)\
                .single()\
                .execute()
            
            if not exec_response.data:
                print(f"\n❌ Week {week_dates}: Execution {exec_uuid[:8]}... not found")
                failed_count += 1
                continue
            
            execution = exec_response.data
            exec_status = execution['status']
            exec_id = execution['execution_id']
            
            print(f"\n📊 Week {week_dates}:")
            print(f"   Execution: {exec_id}")
            print(f"   Execution Status: {exec_status}")
            
            # Update based on execution status
            if exec_status == 'completed':
                update_data = {
                    'status': 'completed',
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Add row count if available
                if execution.get('row_count'):
                    update_data['record_count'] = execution['row_count']
                
                update_response = client.table('report_data_weeks')\
                    .update(update_data)\
                    .eq('id', week_id)\
                    .execute()
                
                if update_response.data:
                    completed_count += 1
                    updated_count += 1
                    print(f"   ✅ Updated to completed")
                else:
                    print(f"   ❌ Failed to update")
                    failed_count += 1
                    
            elif exec_status == 'failed':
                update_data = {
                    'status': 'failed',
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'error_message': 'Execution failed'
                }
                
                update_response = client.table('report_data_weeks')\
                    .update(update_data)\
                    .eq('id', week_id)\
                    .execute()
                
                if update_response.data:
                    failed_count += 1
                    updated_count += 1
                    print(f"   ✅ Updated to failed")
                else:
                    print(f"   ❌ Failed to update")
                    
            elif exec_status in ['pending', 'running']:
                still_running_count += 1
                print(f"   ⏳ Still running (execution in progress)")
            else:
                print(f"   ❓ Unknown execution status: {exec_status}")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total weeks processed: {len(response.data)}")
        print(f"✅ Completed: {completed_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"⏳ Still Running: {still_running_count}")
        print(f"📝 Total Updated: {updated_count}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Update failed: {e}", exc_info=True)
        return False

def check_collection_status(collection_id: str):
    """Check the current status of a collection's weeks"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get collection info
        collection_response = client.table('report_data_collections')\
            .select('name, status')\
            .eq('id', collection_id)\
            .single()\
            .execute()
        
        if collection_response.data:
            print(f"\n📊 Collection: {collection_response.data['name']}")
            print(f"   Status: {collection_response.data['status']}")
        
        # Get week statistics
        weeks_response = client.table('report_data_weeks')\
            .select('status')\
            .eq('collection_id', collection_id)\
            .execute()
        
        if weeks_response.data:
            status_counts = {}
            for week in weeks_response.data:
                status = week['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"\n   Week Status Summary:")
            for status, count in sorted(status_counts.items()):
                emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⏳" if status == "running" else "⏸️"
                print(f"   {emoji} {status}: {count}")
                
    except Exception as e:
        print(f"Error checking collection: {e}")

if __name__ == "__main__":
    load_dotenv()
    
    # Parse arguments
    collection_id = None
    force_complete = False
    
    for arg in sys.argv[1:]:
        if arg == '--force':
            force_complete = True
            print("⚠️  FORCE MODE ENABLED - Will mark all running weeks as completed")
        elif not collection_id and len(arg) == 36:  # UUID length
            collection_id = arg
    
    # If collection provided, show its current status first
    if collection_id:
        check_collection_status(collection_id)
    
    # Run the update
    success = update_stuck_weeks(collection_id, force_complete)
    
    # Show final status if collection provided
    if collection_id and success:
        print("\n" + "="*40)
        print("FINAL STATUS")
        check_collection_status(collection_id)
    
    if success:
        print("\n✅ Update completed")
    else:
        print("\n⚠️  Update failed")
        
    # Instructions
    if not force_complete:
        print("\n💡 TIP: If executions are stuck, you can force complete with:")
        print(f"   python3 {sys.argv[0]} {collection_id or '[collection_id]'} --force")