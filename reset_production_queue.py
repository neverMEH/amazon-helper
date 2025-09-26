#!/usr/bin/env python3
"""
Reset failed Snowflake sync items in production
"""

from datetime import datetime, timezone
from supabase import create_client, Client

# Production Supabase credentials
SUPABASE_URL = "https://loqaorroihxfkjvcrkdv.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvcWFvcnJvaWh4ZmtqdmNya2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzgyMTcyOCwiZXhwIjoyMDY5Mzk3NzI4fQ.LpmFD_V0YMgKdm-5qdjLAVEcYTqx18Z2vNEjedpmwPs"

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("Resetting failed Snowflake sync items in production...")
print("=" * 60)

try:
    # Reset failed items to pending
    response = supabase.table('snowflake_sync_queue')\
        .update({
            'status': 'pending',
            'retry_count': 0,
            'error_message': None,
            'updated_at': datetime.now(timezone.utc).isoformat()
        })\
        .eq('status', 'failed')\
        .execute()

    if response.data:
        print(f"✅ Reset {len(response.data)} failed items to pending")
        print("\nThese executions will be retried when Railway deploys the fixed code.")
    else:
        print("No failed items to reset")

    # Get current queue status
    response = supabase.table('snowflake_sync_queue').select('status').execute()
    if response.data:
        status_counts = {}
        for item in response.data:
            status = item['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        print(f"\nCurrent queue status: {status_counts}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Next steps:")
print("1. Railway will auto-deploy the fixed code")
print("2. The sync service will start processing these items")
print("3. Monitor Railway logs for successful uploads")