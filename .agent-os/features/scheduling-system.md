# Scheduling System

## Overview

The scheduling system enables automated execution of workflows at specified intervals using cron-like expressions. It includes deduplication logic, timezone handling, pause/resume functionality, and comprehensive execution history tracking.

## Key Components

### Backend Services
- `amc_manager/services/schedule_service.py` - Schedule management and validation
- `amc_manager/services/schedule_executor.py` - Background execution service
- `amc_manager/api/supabase/schedules.py` - API endpoints

### Frontend Components
- `frontend/src/pages/ScheduleList.tsx` - Schedule management interface
- `frontend/src/components/ScheduleForm.tsx` - Create/edit schedules
- `frontend/src/components/CronExpressionInput.tsx` - Cron expression builder
- `frontend/src/components/ScheduleHistory.tsx` - Execution history view

### Database Tables
- `workflow_schedules` - Schedule configurations
- `schedule_runs` - Execution history and results
- `workflows` - Referenced workflow definitions
- `amc_instances` - Instance configurations for execution

## Technical Implementation

### Schedule Creation and Validation
```python
# ScheduleService.create_schedule
async def create_schedule(self, schedule_data: dict):
    # Validate cron expression
    cron_expression = schedule_data['cron_expression']
    try:
        croniter(cron_expression)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {str(e)}")
    
    # Calculate next run time
    next_run = self.calculate_next_run(cron_expression, timezone)
    
    schedule = self.db.table('workflow_schedules').insert({
        'workflow_id': schedule_data['workflow_id'],
        'cron_expression': cron_expression,
        'timezone': schedule_data.get('timezone', 'UTC'),
        'is_active': True,
        'next_run_at': next_run.isoformat(),
        'created_at': datetime.utcnow().isoformat()
    }).execute()
    
    return schedule
```

### Schedule Executor Service
```python
# schedule_executor.py - Runs every 60 seconds
async def execute_due_schedules(self):
    current_time = datetime.utcnow()
    
    # Find schedules due for execution
    due_schedules = self.db.table('workflow_schedules')\
        .select('*, workflows(*), amc_instances(*)')\
        .eq('is_active', True)\
        .lte('next_run_at', current_time.isoformat())\
        .execute()
    
    for schedule in due_schedules.data:
        # Check for recent execution (deduplication)
        if not self.has_recent_execution(schedule['id'], minutes=5):
            await self.execute_schedule(schedule)
```

### Deduplication Logic
```python
def has_recent_execution(self, schedule_id: str, minutes: int = 5) -> bool:
    """Prevent duplicate executions within specified time window"""
    cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
    
    recent_runs = self.db.table('schedule_runs')\
        .select('id')\
        .eq('schedule_id', schedule_id)\
        .gte('created_at', cutoff_time.isoformat())\
        .execute()
    
    return len(recent_runs.data) > 0
```

## Cron Expression Support

### Supported Formats
- Standard 5-field cron: `minute hour day month weekday`
- Examples:
  - `0 9 * * MON-FRI` - 9 AM weekdays
  - `*/15 * * * *` - Every 15 minutes
  - `0 0 1 * *` - First day of every month
  - `0 */6 * * *` - Every 6 hours

### Timezone Handling
```python
def calculate_next_run(self, cron_expression: str, timezone: str) -> datetime:
    """Calculate next execution time in specified timezone"""
    import pytz
    
    tz = pytz.timezone(timezone)
    local_now = datetime.now(tz)
    
    cron = croniter(cron_expression, local_now)
    next_local = cron.get_next(datetime)
    
    # Convert to UTC for storage
    return next_local.astimezone(pytz.UTC).replace(tzinfo=None)
```

## Data Flow

1. **Schedule Creation**: User defines workflow and cron expression
2. **Validation**: Cron expression validated and next run calculated
3. **Background Monitoring**: Executor checks every 60 seconds
4. **Execution Trigger**: Due schedules trigger workflow execution
5. **History Recording**: Execution results stored in schedule_runs
6. **Next Run Calculation**: Schedule updated with next execution time

## Schedule Management

### Pause/Resume Functionality
```python
async def pause_schedule(self, schedule_id: str):
    """Pause schedule execution"""
    self.db.table('workflow_schedules')\
        .update({
            'is_active': False,
            'paused_at': datetime.utcnow().isoformat()
        })\
        .eq('id', schedule_id)\
        .execute()

async def resume_schedule(self, schedule_id: str, user_timezone: str = 'UTC'):
    """Resume schedule and recalculate next run"""
    schedule = self.get_schedule(schedule_id)
    next_run = self.calculate_next_run(
        schedule['cron_expression'], 
        schedule.get('timezone', user_timezone)
    )
    
    self.db.table('workflow_schedules')\
        .update({
            'is_active': True,
            'next_run_at': next_run.isoformat(),
            'paused_at': None
        })\
        .eq('id', schedule_id)\
        .execute()
```

### Schedule History
```python
async def get_schedule_history(self, schedule_id: str, limit: int = 50):
    """Get execution history for schedule"""
    runs = self.db.table('schedule_runs')\
        .select('*, workflow_executions(*)')\
        .eq('schedule_id', schedule_id)\
        .order('created_at', desc=True)\
        .limit(limit)\
        .execute()
    
    return runs.data
```

## Critical Implementation Details

### Entity ID Resolution
```python
async def execute_schedule(self, schedule: dict):
    """Execute scheduled workflow"""
    workflow = schedule['workflows']
    instance = schedule['workflows']['amc_instances']
    
    # CRITICAL: Must join amc_accounts for entity_id
    if not instance or not instance.get('amc_accounts'):
        raise ValueError("Schedule missing required AMC account information")
    
    entity_id = instance['amc_accounts']['account_id']
    instance_id = instance['instance_id']  # AMC string ID, not UUID
    
    # Execute workflow
    execution = await self.workflow_service.execute_workflow(
        workflow_id=workflow['id'],
        user_id=schedule['user_id'],
        instance_id=instance_id,
        entity_id=entity_id
    )
    
    # Record schedule run
    await self.record_schedule_run(schedule['id'], execution['id'])
```

### Next Run Calculation Update
```python
def update_next_run(self, schedule_id: str, cron_expression: str, timezone: str):
    """Update schedule with next execution time"""
    next_run = self.calculate_next_run(cron_expression, timezone)
    
    self.db.table('workflow_schedules')\
        .update({'next_run_at': next_run.isoformat()})\
        .eq('id', schedule_id)\
        .execute()
```

## Error Handling

### Execution Failures
```python
async def handle_schedule_execution_error(self, schedule: dict, error: Exception):
    """Handle schedule execution failures"""
    # Record failed run
    self.db.table('schedule_runs').insert({
        'schedule_id': schedule['id'],
        'status': 'FAILED',
        'error_message': str(error),
        'created_at': datetime.utcnow().isoformat()
    }).execute()
    
    # Update next run time (don't stop scheduling)
    self.update_next_run(
        schedule['id'], 
        schedule['cron_expression'], 
        schedule.get('timezone', 'UTC')
    )
    
    # Optional: Disable after consecutive failures
    if self.consecutive_failures(schedule['id']) >= 5:
        await self.pause_schedule(schedule['id'])
```

### Token Expiry Handling
```python
async def execute_with_token_refresh(self, schedule: dict):
    """Execute schedule with automatic token refresh"""
    try:
        await self.execute_schedule(schedule)
    except TokenExpiredException:
        # Attempt token refresh
        await self.token_service.refresh_user_token(schedule['user_id'])
        # Retry execution
        await self.execute_schedule(schedule)
```

## Frontend Integration

### Schedule Status Indicators
```typescript
const getScheduleStatus = (schedule: Schedule) => {
  if (!schedule.is_active) return 'Paused';
  
  const nextRun = new Date(schedule.next_run_at);
  const now = new Date();
  
  if (nextRun <= now) return 'Due';
  return `Next: ${formatDistanceToNow(nextRun)}`;
};
```

### Cron Expression Builder
```typescript
// Helper to build common cron expressions
const cronPresets = {
  'Every 15 minutes': '*/15 * * * *',
  'Every hour': '0 * * * *',
  'Daily at 9 AM': '0 9 * * *',
  'Weekdays at 9 AM': '0 9 * * 1-5',
  'Weekly on Monday': '0 9 * * 1',
  'Monthly on 1st': '0 9 1 * *'
};
```

## Interconnections

### With Workflow System
- Schedules trigger standard workflow execution
- Use same parameter substitution and result processing
- Inherit error handling and retry logic

### With Authentication System
- Schedules execute using user's stored tokens
- Automatic token refresh on expiry
- User-specific timezone preferences

### With Data Collections
- Collections can be scheduled for regular updates
- Incremental data gathering patterns

## Performance Considerations

### Executor Efficiency
- Single executor process handles all schedules
- Efficient database queries for due schedules
- Concurrent execution of multiple schedules

### Database Optimization
```sql
-- Index for efficient schedule queries
CREATE INDEX idx_schedules_due ON workflow_schedules(is_active, next_run_at)
WHERE is_active = true;

-- Index for deduplication queries
CREATE INDEX idx_schedule_runs_recent ON schedule_runs(schedule_id, created_at);
```

## Monitoring and Debugging

### Schedule Health Checks
```python
def check_schedule_health(self):
    """Monitor schedule execution patterns"""
    # Identify schedules with high failure rates
    # Check for stalled schedules (next_run in past but no recent runs)
    # Monitor execution duration trends
```

### Debug Commands
```bash
# Check active schedules
python scripts/list_active_schedules.py

# Validate schedule configuration
python scripts/validate_schedules.py

# Force schedule execution (testing)
python scripts/trigger_schedule.py <schedule_id>
```

## Testing Strategy

### Unit Tests
```python
def test_cron_expression_validation():
    # Test valid and invalid cron expressions

def test_next_run_calculation():
    # Test timezone handling and edge cases

def test_deduplication_logic():
    # Ensure no duplicate executions
```

### Integration Tests
```python
async def test_schedule_execution_flow():
    # Create schedule, wait for execution, verify results

async def test_error_recovery():
    # Test token refresh and retry logic
```