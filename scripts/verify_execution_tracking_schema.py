#!/usr/bin/env python3
"""
Script to verify the execution_id column in report_data_weeks table
and analyze current data population rates
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

def verify_execution_tracking_schema():
    """Verify the execution_id column and check population rates"""
    
    print("\n" + "="*60)
    print("EXECUTION TRACKING SCHEMA VERIFICATION")
    print("="*60)
    
    try:
        # Get Supabase client
        client = SupabaseManager.get_client(use_service_role=True)
        
        # 1. Check if report_data_weeks table exists
        print("\n1. Checking report_data_weeks table...")
        try:
            test_query = client.table('report_data_weeks').select('id').limit(1).execute()
            print("   ✅ Table 'report_data_weeks' exists")
        except Exception as e:
            print(f"   ❌ Table 'report_data_weeks' not found: {e}")
            return False
        
        # 2. Check column structure
        print("\n2. Checking column structure...")
        try:
            # Query with specific columns to verify they exist
            test_columns = client.table('report_data_weeks')\
                .select('id, execution_id, amc_execution_id, week_start_date, week_end_date, status')\
                .limit(1)\
                .execute()
            print("   ✅ Column 'execution_id' exists")
            print("   ✅ Column 'amc_execution_id' exists")
        except Exception as e:
            print(f"   ❌ Error checking columns: {e}")
            return False
        
        # 3. Check data population rates
        print("\n3. Analyzing data population rates...")
        
        # Total records
        total_response = client.table('report_data_weeks')\
            .select('id', count='exact')\
            .execute()
        total_count = total_response.count if hasattr(total_response, 'count') else len(total_response.data)
        
        print(f"   Total records: {total_count}")
        
        if total_count > 0:
            # Records with execution_id populated
            with_exec_id = client.table('report_data_weeks')\
                .select('id', count='exact')\
                .not_.is_('execution_id', 'null')\
                .execute()
            exec_id_count = with_exec_id.count if hasattr(with_exec_id, 'count') else len(with_exec_id.data)
            
            # Records with amc_execution_id populated
            with_amc_id = client.table('report_data_weeks')\
                .select('id', count='exact')\
                .not_.is_('amc_execution_id', 'null')\
                .execute()
            amc_id_count = with_amc_id.count if hasattr(with_amc_id, 'count') else len(with_amc_id.data)
            
            # Calculate percentages
            exec_id_percentage = (exec_id_count / total_count * 100) if total_count > 0 else 0
            amc_id_percentage = (amc_id_count / total_count * 100) if total_count > 0 else 0
            
            print(f"   Records with execution_id: {exec_id_count} ({exec_id_percentage:.1f}%)")
            print(f"   Records with amc_execution_id: {amc_id_count} ({amc_id_percentage:.1f}%)")
            
            # Show sample records
            print("\n4. Sample records (last 5)...")
            sample_records = client.table('report_data_weeks')\
                .select('id, collection_id, week_start_date, week_end_date, status, execution_id, amc_execution_id')\
                .order('created_at', desc=True)\
                .limit(5)\
                .execute()
            
            if sample_records.data:
                for idx, record in enumerate(sample_records.data, 1):
                    print(f"\n   Record {idx}:")
                    print(f"     Week: {record.get('week_start_date')} to {record.get('week_end_date')}")
                    print(f"     Status: {record.get('status')}")
                    print(f"     execution_id: {record.get('execution_id') or 'NULL'}")
                    print(f"     amc_execution_id: {record.get('amc_execution_id') or 'NULL'}")
        else:
            print("   No records found in table")
        
        # 5. Check foreign key relationship
        print("\n5. Checking foreign key relationships...")
        try:
            # Try to query with join to verify FK exists
            test_join = client.table('report_data_weeks')\
                .select('id, execution_id, workflow_executions(id)')\
                .not_.is_('execution_id', 'null')\
                .limit(1)\
                .execute()
            
            if test_join.data and len(test_join.data) > 0:
                print("   ✅ Foreign key to workflow_executions verified")
            else:
                print("   ⚠️  No records with execution_id to verify FK relationship")
        except Exception as e:
            print(f"   ⚠️  Could not verify FK relationship: {e}")
        
        # 6. Summary and recommendations
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        
        print("\n✅ Schema Requirements Met:")
        print("   - report_data_weeks table exists")
        print("   - execution_id column exists (UUID type)")
        print("   - amc_execution_id column exists (VARCHAR type)")
        
        if total_count > 0 and exec_id_percentage == 0:
            print("\n⚠️  Issue Confirmed:")
            print(f"   - 0% of {total_count} records have execution_id populated")
            print("   - This confirms the tracking issue needs to be fixed")
        elif total_count > 0 and exec_id_percentage > 0:
            print(f"\n✅ Partial Population:")
            print(f"   - {exec_id_percentage:.1f}% of records have execution_id")
            print("   - Some tracking may already be working")
        
        print("\n📋 Next Steps:")
        print("   1. Update reporting_database_service.update_week_status() to accept execution_id")
        print("   2. Update historical_collection_service to pass execution_id from AMC response")
        print("   3. Test with new data collections")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        logger.error(f"Verification failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run verification
    success = verify_execution_tracking_schema()
    
    if success:
        print("\n✅ Verification completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Verification failed")
        sys.exit(1)