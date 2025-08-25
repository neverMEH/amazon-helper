#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/root/amazon-helper')

from supabase import create_client, Client
from datetime import datetime, timezone, timedelta
from croniter import croniter
import pytz

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    print("Missing Supabase credentials")
    sys.exit(1)

# Create Supabase client
client: Client = create_client(supabase_url, supabase_key)

schedule_id = 'sched_d0d8b2c5f533'

# Get the schedule
result = client.table('workflow_schedules').select('*').eq('schedule_id', schedule_id).execute()

if result.data:
    schedule = result.data[0]
    print(f"Current schedule state:")
    print(f"  Name: {schedule['name']}")
    print(f"  CRON: {schedule['cron_expression']}")
    print(f"  Timezone: {schedule.get('timezone', 'UTC')}")
    print(f"  Current next_run_at: {schedule['next_run_at']}")
    print(f"  Last run: {schedule['last_run_at']}")
    
    # Calculate the correct next run time
    now = datetime.now(timezone.utc)
    tz = pytz.timezone(schedule.get('timezone', 'UTC'))
    
    # Convert now to the schedule's timezone
    now_in_tz = now.astimezone(tz)
    
    # Calculate next run based on cron expression
    cron = croniter(schedule['cron_expression'], now_in_tz)
    next_run_local = cron.get_next(datetime)
    
    # Convert back to UTC for storage
    next_run_utc = next_run_local.astimezone(timezone.utc)
    
    print(f"\nCalculated next run:")
    print(f"  Current time (UTC): {now.isoformat()}")
    print(f"  Current time ({schedule.get('timezone', 'UTC')}): {now_in_tz.isoformat()}")
    print(f"  Next run (UTC): {next_run_utc.isoformat()}")
    
    # Update the schedule
    update_result = client.table('workflow_schedules').update({
        'next_run_at': next_run_utc.isoformat(),
        'updated_at': now.isoformat()
    }).eq('id', schedule['id']).execute()
    
    if update_result.data:
        print(f"\n✅ Successfully updated next_run_at to {next_run_utc.isoformat()}")
        
        # Also check if we need to clear consecutive failures
        if schedule.get('consecutive_failures', 0) > 0:
            clear_result = client.table('workflow_schedules').update({
                'consecutive_failures': 0
            }).eq('id', schedule['id']).execute()
            print(f"✅ Reset consecutive_failures counter")
    else:
        print("❌ Failed to update schedule")
else:
    print(f"Schedule {schedule_id} not found")