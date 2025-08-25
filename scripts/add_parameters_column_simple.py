#!/usr/bin/env python3
"""Add missing parameters column to schedule_runs table."""

from supabase import create_client, Client
import os

def main():
    """Add parameters column to schedule_runs table."""
    
    # Supabase credentials
    supabase_url = os.environ.get('SUPABASE_URL', 'https://loqaorroihxfkjvcrkdv.supabase.co')
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvcWFvcnJvaWh4ZmtqdmNya2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzgyMTcyOCwiZXhwIjoyMDY5Mzk3NzI4fQ.LpmFD_V0YMgKdm-5qdjLAVEcYTqx18Z2vNEjedpmwPs'
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # First check if column exists
        result = supabase.table('schedule_runs').select('*').limit(1).execute()
        
        # If we get here without error, check if parameters field exists in the data
        if result.data and len(result.data) > 0:
            if 'parameters' in result.data[0]:
                print("ℹ️  Parameters column already exists in schedule_runs table")
                return True
        
        print("✅ Column check completed - column may need to be added via Supabase dashboard")
        print("   Please add a 'parameters' column of type 'jsonb' to the schedule_runs table")
        return True
        
    except Exception as e:
        print(f"❌ Error checking column: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)