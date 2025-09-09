#!/usr/bin/env python3
"""
Apply fix for workflow_execution_id column data
Copies execution_id to workflow_execution_id where it's missing
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def fix_workflow_execution_ids():
    """Fix workflow_execution_id column data"""
    
    print("\n" + "="*60)
    print("FIXING WORKFLOW_EXECUTION_ID COLUMN DATA")
    print("="*60)
    
    try:
        # Get Supabase client
        client = SupabaseManager.get_client(use_service_role=True)
        
        # First, check current state
        print("\n1. Checking current state...")
        all_records = client.table('report_data_weeks')\
            .select('id, execution_id, workflow_execution_id')\
            .execute()
        
        if not all_records.data:
            print("   No records found in report_data_weeks")
            return True
        
        total_records = len(all_records.data)
        has_execution_id = sum(1 for r in all_records.data if r.get('execution_id'))
        has_workflow_execution_id = sum(1 for r in all_records.data if r.get('workflow_execution_id'))
        needs_fix = sum(1 for r in all_records.data if r.get('execution_id') and not r.get('workflow_execution_id'))
        
        print(f"   Total records: {total_records}")
        print(f"   Records with execution_id: {has_execution_id}")
        print(f"   Records with workflow_execution_id: {has_workflow_execution_id}")
        print(f"   Records needing fix: {needs_fix}")
        
        if needs_fix == 0:
            print("\n✅ No records need fixing!")
            return True
        
        # Fix records that need it
        print(f"\n2. Fixing {needs_fix} records...")
        fixed_count = 0
        failed_count = 0
        
        for record in all_records.data:
            if record.get('execution_id') and not record.get('workflow_execution_id'):
                try:
                    # Update workflow_execution_id to match execution_id
                    update_response = client.table('report_data_weeks')\
                        .update({'workflow_execution_id': record['execution_id']})\
                        .eq('id', record['id'])\
                        .execute()
                    
                    if update_response.data:
                        fixed_count += 1
                        if fixed_count % 10 == 0:
                            print(f"   Fixed {fixed_count}/{needs_fix} records...")
                except Exception as e:
                    logger.error(f"Failed to fix record {record['id']}: {e}")
                    failed_count += 1
        
        print(f"\n3. Results:")
        print(f"   ✅ Fixed: {fixed_count}")
        if failed_count > 0:
            print(f"   ❌ Failed: {failed_count}")
        
        # Verify the fix
        print("\n4. Verifying fix...")
        verify_response = client.table('report_data_weeks')\
            .select('id, execution_id, workflow_execution_id')\
            .execute()
        
        if verify_response.data:
            after_has_workflow_execution_id = sum(1 for r in verify_response.data if r.get('workflow_execution_id'))
            still_needs_fix = sum(1 for r in verify_response.data if r.get('execution_id') and not r.get('workflow_execution_id'))
            
            print(f"   Records with workflow_execution_id after fix: {after_has_workflow_execution_id}")
            print(f"   Records still needing fix: {still_needs_fix}")
            
            if still_needs_fix == 0:
                print("\n✅ All records successfully fixed!")
            else:
                print(f"\n⚠️  {still_needs_fix} records still need fixing")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during fix: {e}")
        logger.error(f"Fix failed: {e}", exc_info=True)
        return False

def check_specific_collection(collection_id: str = None):
    """Check records for a specific collection"""
    if not collection_id:
        return
    
    print(f"\n5. Checking collection {collection_id}...")
    
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        collection_records = client.table('report_data_weeks')\
            .select('id, week_start_date, status, execution_id, workflow_execution_id')\
            .eq('collection_id', collection_id)\
            .order('week_start_date')\
            .execute()
        
        if collection_records.data:
            print(f"   Found {len(collection_records.data)} weeks for this collection")
            
            # Show sample records
            for record in collection_records.data[:5]:
                exec_id = record.get('execution_id', 'None')
                wf_exec_id = record.get('workflow_execution_id', 'None')
                match = "✅" if exec_id == wf_exec_id and exec_id != 'None' else "❌"
                
                print(f"   Week {record['week_start_date']}: exec_id={exec_id[:8] if exec_id != 'None' else 'None'}..., "
                      f"workflow_exec_id={wf_exec_id[:8] if wf_exec_id != 'None' else 'None'}... {match}")
    except Exception as e:
        print(f"   Error checking collection: {e}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run fix
    success = fix_workflow_execution_ids()
    
    # Check specific collection if provided
    if len(sys.argv) > 1:
        collection_id = sys.argv[1]
        check_specific_collection(collection_id)
    
    if success:
        print("\n✅ Fix completed successfully")
        sys.exit(0)
    else:
        print("\n⚠️  Fix encountered issues")
        sys.exit(1)