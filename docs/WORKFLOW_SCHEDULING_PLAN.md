# Workflow Scheduling Feature - Implementation Plan

## Executive Summary

### Overview
This document outlines the comprehensive plan for implementing a robust workflow scheduling system for RecomAMP's Amazon Marketing Cloud (AMC) platform. The feature will enable users to schedule recurring query executions with flexible intervals, automatic parameter calculation, and easy access to historical results.

### Key Capabilities
- **Flexible Scheduling**: Every 1, 3, 7, 14, 30, 60, 90 days
- **Advanced Patterns**: Monthly, weekly, business days, custom CRON
- **Smart Parameters**: Dynamic date range calculation with AMC's 14-day lag
- **Result Management**: Grouped execution history with easy access to past runs
- **Timezone Support**: Global scheduling with DST handling
- **Cost Tracking**: Budget monitoring and forecasting

### Timeline
- **Week 1-2**: Core backend infrastructure
- **Week 2-3**: Basic frontend UI
- **Week 3-4**: History and reporting features
- **Week 4-5**: Advanced features and templates
- **Week 5-6**: Monitoring and optimization

## Current State Analysis

### Existing Infrastructure We Can Leverage

#### Backend Services
- ✅ **TokenRefreshService**: Automatic OAuth token refresh every 10 minutes
- ✅ **ExecutionStatusPoller**: 15-second polling for execution status
- ✅ **AMCAPIClientWithRetry**: Automatic 401 retry with token refresh
- ✅ **WorkflowService**: Basic workflow CRUD and execution
- ✅ **Database Schema**: `workflow_schedules` table already exists

#### Database Tables
```sql
-- Already exists
workflow_schedules:
- id UUID PRIMARY KEY
- schedule_id TEXT UNIQUE
- workflow_id UUID REFERENCES workflows(id)
- cron_expression TEXT
- timezone TEXT DEFAULT 'UTC'
- default_parameters JSONB
- is_active BOOLEAN DEFAULT true
- last_run_at TIMESTAMP WITH TIME ZONE
- next_run_at TIMESTAMP WITH TIME ZONE
- created_at TIMESTAMP WITH TIME ZONE
- updated_at TIMESTAMP WITH TIME ZONE
```

### AMC API Capabilities and Limitations

#### What AMC Provides
- ✅ Basic CRON-based scheduling support
- ✅ Workflow execution API
- ✅ Execution status polling
- ✅ Result retrieval (48-72 hour window)

#### What AMC Doesn't Provide
- ❌ Native recurring execution management
- ❌ Execution grouping by schedule
- ❌ Long-term result storage
- ❌ Webhooks for completion notifications
- ❌ Batch execution endpoints

#### Key Constraints
- **Token Expiry**: Access tokens expire in 1 hour
- **Data Lag**: 14-day minimum lag for AMC data
- **Result Expiry**: Results available for 48-72 hours only
- **Rate Limits**: 10 requests/second, dynamic throttling
- **Execution Timeout**: 30 minutes maximum per workflow

## Detailed Technical Specification

### Backend Architecture

#### 1. Schedule Service Enhancement (`amc_manager/services/schedule_service.py`)

```python
class EnhancedScheduleService:
    """Enhanced scheduling service with flexible interval support"""
    
    # Interval types
    INTERVAL_TYPES = {
        'daily': lambda n: f'0 2 */{n} * *',
        'weekly': lambda d: f'0 2 * * {d}',
        'monthly_day': lambda d: f'0 2 {d} * *',
        'monthly_last': lambda: '0 2 L * *',
        'business_day_first': lambda: '0 2 1-3 * 1-5',
        'business_day_last': lambda: '0 2 L * 1-5',
        'custom': lambda cron: cron
    }
    
    async def create_schedule_from_preset(
        self,
        workflow_id: str,
        preset_type: str,
        interval_config: dict,
        timezone: str = 'UTC',
        parameters: dict = None
    ) -> dict:
        """Create schedule from user-friendly preset"""
        
    async def calculate_next_runs(
        self,
        schedule_id: str,
        count: int = 10
    ) -> List[datetime]:
        """Preview next N execution times"""
        
    async def get_schedule_with_history(
        self,
        schedule_id: str,
        limit: int = 30
    ) -> dict:
        """Get schedule with grouped execution history"""
```

#### 2. Schedule Executor Service (`amc_manager/services/schedule_executor_service.py`)

```python
class ScheduleExecutorService:
    """Background service for executing scheduled workflows"""
    
    def __init__(self):
        self.running = False
        self.check_interval = 60  # Check every minute
        
    async def start(self):
        """Start the schedule executor background task"""
        self.running = True
        while self.running:
            try:
                await self.check_and_execute_schedules()
            except Exception as e:
                logger.error(f"Schedule executor error: {e}")
            await asyncio.sleep(self.check_interval)
    
    async def check_and_execute_schedules(self):
        """Check for due schedules and execute them"""
        # Get all active schedules where next_run_at <= now
        due_schedules = await self.get_due_schedules()
        
        for schedule in due_schedules:
            asyncio.create_task(self.execute_schedule(schedule))
    
    async def execute_schedule(self, schedule: dict):
        """Execute a single scheduled workflow"""
        try:
            # Create schedule run record
            run_id = await self.create_schedule_run(schedule)
            
            # Refresh token if needed
            await self.ensure_fresh_token(schedule['user_id'])
            
            # Calculate dynamic parameters
            params = self.calculate_parameters(schedule)
            
            # Execute workflow
            execution = await self.execute_workflow(
                schedule['workflow_id'],
                params,
                schedule_run_id=run_id
            )
            
            # Update schedule record
            await self.update_schedule_after_run(schedule['id'])
            
        except Exception as e:
            await self.handle_execution_error(schedule, e)
    
    def calculate_parameters(self, schedule: dict) -> dict:
        """Calculate dynamic parameters based on schedule frequency"""
        params = schedule.get('default_parameters', {})
        
        # Account for AMC's 14-day data lag
        end_date = datetime.utcnow() - timedelta(days=14)
        
        # Calculate lookback based on schedule frequency
        if schedule['interval_days']:
            start_date = end_date - timedelta(days=schedule['interval_days'])
        else:
            # Default to 7 days
            start_date = end_date - timedelta(days=7)
        
        params.update({
            'startDate': start_date.strftime('%Y-%m-%dT00:00:00'),
            'endDate': end_date.strftime('%Y-%m-%dT23:59:59')
        })
        
        return params
```

#### 3. Schedule History Service (`amc_manager/services/schedule_history_service.py`)

```python
class ScheduleHistoryService:
    """Service for managing schedule execution history"""
    
    async def get_schedule_runs(
        self,
        schedule_id: str,
        limit: int = 30,
        offset: int = 0
    ) -> List[dict]:
        """Get paginated schedule run history"""
        
    async def get_run_executions(
        self,
        run_id: str
    ) -> List[dict]:
        """Get all executions for a schedule run"""
        
    async def get_schedule_metrics(
        self,
        schedule_id: str,
        period_days: int = 30
    ) -> dict:
        """Get schedule performance metrics"""
        return {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'success_rate': 0.0,
            'avg_runtime_seconds': 0,
            'total_rows_processed': 0,
            'total_cost': 0.0,
            'next_run': None,
            'last_run': None
        }
    
    async def compare_periods(
        self,
        schedule_id: str,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> dict:
        """Compare metrics between two periods"""
```

### Database Schema Enhancements

```sql
-- Enhanced workflow_schedules table
ALTER TABLE workflow_schedules ADD COLUMN IF NOT EXISTS
    schedule_type TEXT DEFAULT 'cron', -- 'interval', 'monthly', 'weekly', 'cron'
    interval_days INTEGER, -- For simple N-day intervals
    interval_config JSONB, -- Advanced configuration
    execution_history_limit INTEGER DEFAULT 30,
    notification_config JSONB, -- Email/webhook settings
    cost_limit DECIMAL(10, 2), -- Maximum cost per execution
    auto_pause_on_failure BOOLEAN DEFAULT false,
    failure_threshold INTEGER DEFAULT 3;

-- New table for schedule runs (groups executions)
CREATE TABLE IF NOT EXISTS schedule_runs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    schedule_id UUID REFERENCES workflow_schedules(id) ON DELETE CASCADE,
    run_number INTEGER NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL, -- 'pending', 'running', 'completed', 'failed'
    execution_count INTEGER DEFAULT 0,
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    total_rows BIGINT DEFAULT 0,
    total_cost DECIMAL(10, 2) DEFAULT 0,
    error_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(schedule_id, run_number)
);

-- Link executions to schedule runs
ALTER TABLE workflow_executions ADD COLUMN IF NOT EXISTS
    schedule_run_id UUID REFERENCES schedule_runs(id) ON DELETE SET NULL;

-- Index for efficient queries
CREATE INDEX IF NOT EXISTS idx_schedule_runs_schedule_id ON schedule_runs(schedule_id);
CREATE INDEX IF NOT EXISTS idx_schedule_runs_status ON schedule_runs(status);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_schedule_run_id ON workflow_executions(schedule_run_id);
```

### API Endpoints

```python
# Schedule Management
POST   /api/workflows/{workflow_id}/schedules        # Create schedule
GET    /api/workflows/{workflow_id}/schedules        # List schedules for workflow
GET    /api/schedules                                # List all schedules
GET    /api/schedules/{schedule_id}                  # Get schedule details
PUT    /api/schedules/{schedule_id}                  # Update schedule
DELETE /api/schedules/{schedule_id}                  # Delete schedule
POST   /api/schedules/{schedule_id}/enable           # Enable schedule
POST   /api/schedules/{schedule_id}/disable          # Disable schedule

# Schedule Execution History
GET    /api/schedules/{schedule_id}/runs             # Get run history
GET    /api/schedules/{schedule_id}/runs/{run_id}    # Get specific run
GET    /api/schedules/{schedule_id}/metrics          # Get performance metrics
GET    /api/schedules/{schedule_id}/next-runs        # Preview next N runs

# Schedule Operations
POST   /api/schedules/{schedule_id}/test-run         # Execute immediately
POST   /api/schedules/{schedule_id}/pause            # Pause schedule
POST   /api/schedules/{schedule_id}/resume           # Resume schedule
GET    /api/schedules/{schedule_id}/export           # Export all results

# Bulk Operations
POST   /api/schedules/bulk/enable                    # Enable multiple schedules
POST   /api/schedules/bulk/disable                   # Disable multiple schedules
DELETE /api/schedules/bulk                           # Delete multiple schedules
```

## Frontend Implementation

### Component Architecture

#### 1. Schedule Creation Wizard (`frontend/src/components/schedules/ScheduleWizard.tsx`)

```typescript
interface ScheduleWizardProps {
  workflowId: string;
  onComplete: (schedule: Schedule) => void;
  onCancel: () => void;
}

const ScheduleWizard: React.FC<ScheduleWizardProps> = ({ workflowId, onComplete, onCancel }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    type: 'interval',
    intervalDays: 7,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    executeTime: '09:00',
    parameters: {},
    notifications: {
      onSuccess: false,
      onFailure: true,
      email: null
    }
  });

  const steps = [
    { id: 1, name: 'Schedule Type', component: ScheduleTypeStep },
    { id: 2, name: 'Timing', component: TimingStep },
    { id: 3, name: 'Parameters', component: ParametersStep },
    { id: 4, name: 'Review', component: ReviewStep }
  ];

  return (
    <div className="schedule-wizard">
      <StepIndicator steps={steps} currentStep={currentStep} />
      <CurrentStepComponent 
        config={scheduleConfig}
        onChange={setScheduleConfig}
        onNext={() => setCurrentStep(prev => prev + 1)}
        onBack={() => setCurrentStep(prev => prev - 1)}
        onComplete={handleComplete}
      />
    </div>
  );
};
```

#### 2. Schedule Type Selection (`frontend/src/components/schedules/ScheduleTypeStep.tsx`)

```typescript
const ScheduleTypeStep: React.FC<StepProps> = ({ config, onChange, onNext }) => {
  const presets = [
    { 
      id: 'daily', 
      name: 'Daily', 
      description: 'Run every day at the same time',
      icon: Calendar 
    },
    { 
      id: 'interval', 
      name: 'Every N Days', 
      description: 'Run every 3, 7, 14, 30 days etc.',
      icon: Clock,
      options: [1, 3, 7, 14, 30, 60, 90]
    },
    { 
      id: 'weekly', 
      name: 'Weekly', 
      description: 'Run on specific days of the week',
      icon: Calendar 
    },
    { 
      id: 'monthly', 
      name: 'Monthly', 
      description: 'Run on specific day of month',
      icon: Calendar,
      options: ['first', 'last', 'specific', 'firstBusiness', 'lastBusiness']
    },
    { 
      id: 'custom', 
      name: 'Custom CRON', 
      description: 'Advanced scheduling with CRON expression',
      icon: Settings 
    }
  ];

  return (
    <div className="grid grid-cols-2 gap-4">
      {presets.map(preset => (
        <PresetCard 
          key={preset.id}
          preset={preset}
          selected={config.type === preset.id}
          onSelect={() => {
            onChange({ ...config, type: preset.id });
            if (preset.id !== 'custom') {
              onNext();
            }
          }}
        />
      ))}
    </div>
  );
};
```

#### 3. Schedule History View (`frontend/src/components/schedules/ScheduleHistory.tsx`)

```typescript
interface ScheduleHistoryProps {
  scheduleId: string;
  limit?: number;
}

const ScheduleHistory: React.FC<ScheduleHistoryProps> = ({ scheduleId, limit = 30 }) => {
  const { data: runs, isLoading } = useQuery({
    queryKey: ['schedule-runs', scheduleId, limit],
    queryFn: () => scheduleService.getScheduleRuns(scheduleId, limit)
  });

  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'timeline' | 'table' | 'metrics'>('timeline');

  return (
    <div className="schedule-history">
      {/* View mode selector */}
      <ViewModeSelector value={viewMode} onChange={setViewMode} />
      
      {/* Main content based on view mode */}
      {viewMode === 'timeline' && (
        <TimelineView 
          runs={runs}
          onRunSelect={setSelectedRun}
          selectedRun={selectedRun}
        />
      )}
      
      {viewMode === 'table' && (
        <TableView 
          runs={runs}
          onRunSelect={setSelectedRun}
        />
      )}
      
      {viewMode === 'metrics' && (
        <MetricsView 
          scheduleId={scheduleId}
          runs={runs}
        />
      )}
      
      {/* Run details modal */}
      {selectedRun && (
        <RunDetailsModal
          runId={selectedRun}
          onClose={() => setSelectedRun(null)}
        />
      )}
    </div>
  );
};
```

#### 4. Schedule Management Page (`frontend/src/pages/ScheduleManager.tsx`)

```typescript
const ScheduleManager: React.FC = () => {
  const [filters, setFilters] = useState<ScheduleFilters>({
    status: 'all', // all, active, paused, failed
    workflowId: null,
    nextRunWithin: null // hours
  });
  
  const { data: schedules, isLoading } = useQuery({
    queryKey: ['schedules', filters],
    queryFn: () => scheduleService.listSchedules(filters)
  });

  const [selectedSchedule, setSelectedSchedule] = useState<string | null>(null);
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'calendar'>('grid');

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Schedule Manager</h1>
        <button 
          onClick={() => setShowCreateWizard(true)}
          className="btn btn-primary"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Schedule
        </button>
      </div>

      {/* Filters */}
      <ScheduleFilters 
        filters={filters}
        onChange={setFilters}
      />

      {/* View mode toggle */}
      <ViewModeToggle 
        value={viewMode}
        onChange={setViewMode}
      />

      {/* Schedule list/grid/calendar */}
      {viewMode === 'grid' && (
        <ScheduleGrid 
          schedules={schedules}
          onScheduleSelect={setSelectedSchedule}
        />
      )}

      {viewMode === 'list' && (
        <ScheduleList 
          schedules={schedules}
          onScheduleSelect={setSelectedSchedule}
        />
      )}

      {viewMode === 'calendar' && (
        <ScheduleCalendar 
          schedules={schedules}
          onScheduleSelect={setSelectedSchedule}
        />
      )}

      {/* Modals */}
      {showCreateWizard && (
        <ScheduleWizard 
          onComplete={() => {
            setShowCreateWizard(false);
            queryClient.invalidateQueries(['schedules']);
          }}
          onCancel={() => setShowCreateWizard(false)}
        />
      )}

      {selectedSchedule && (
        <ScheduleDetailsModal
          scheduleId={selectedSchedule}
          onClose={() => setSelectedSchedule(null)}
        />
      )}
    </div>
  );
};
```

## Scheduling Options Matrix

### Interval-Based Scheduling

| Interval | CRON Expression | Description | Use Case |
|----------|----------------|-------------|----------|
| Daily | `0 2 * * *` | Every day at 2 AM | Daily reports |
| Every 3 days | `0 2 */3 * *` | Every 3rd day | Regular monitoring |
| Weekly | `0 2 * * 1` | Every Monday | Weekly summaries |
| Bi-weekly | `0 2 */14 * *` | Every 14 days | Bi-weekly analysis |
| Monthly | `0 2 1 * *` | 1st of month | Monthly reports |
| Quarterly | `0 2 1 */3 *` | Every 3 months | Quarterly reviews |
| Every 30 days | `0 2 */30 * *` | Every 30 days | Monthly cycles |
| Every 60 days | `0 2 */60 * *` | Every 60 days | Bi-monthly |
| Every 90 days | `0 2 */90 * *` | Every 90 days | Quarterly |

### Advanced Patterns

| Pattern | CRON Expression | Description |
|---------|----------------|-------------|
| First business day | `0 8 1-3 * 1-5` | First weekday of month |
| Last business day | `0 8 L * 1-5` | Last weekday of month |
| First Monday | `0 8 * * 1#1` | First Monday of month |
| Last Friday | `0 17 * * 5L` | Last Friday of month |
| Weekdays only | `0 9 * * 1-5` | Monday-Friday |
| Weekend only | `0 10 * * 0,6` | Saturday & Sunday |
| Multiple daily | `0 9,14,18 * * *` | 9 AM, 2 PM, 6 PM |
| Specific dates | `0 8 1,15 * *` | 1st and 15th |

### Dynamic Parameter Calculation

```javascript
const parameterCalculators = {
  daily: (lastRun) => ({
    startDate: subDays(new Date(), 15), // Account for 14-day lag
    endDate: subDays(new Date(), 14)
  }),
  
  weekly: (lastRun) => ({
    startDate: subDays(new Date(), 21), // 7 days + 14 lag
    endDate: subDays(new Date(), 14)
  }),
  
  monthly: (lastRun) => ({
    startDate: subDays(new Date(), 44), // 30 days + 14 lag
    endDate: subDays(new Date(), 14)
  }),
  
  custom: (lastRun, config) => {
    const lookback = config.lookbackDays || 7;
    return {
      startDate: subDays(new Date(), lookback + 14),
      endDate: subDays(new Date(), 14)
    };
  }
};
```

## Implementation Phases

### Phase 1: Core Backend Infrastructure (Week 1-2)

#### Week 1
- [ ] Create enhanced schedule service with preset support
- [ ] Implement schedule executor background service
- [ ] Add database schema enhancements
- [ ] Create schedule run tracking system
- [ ] Implement parameter calculation logic

#### Week 2
- [ ] Build REST API endpoints for schedule management
- [ ] Integrate with existing token refresh service
- [ ] Add schedule validation and conflict detection
- [ ] Implement error handling and retry logic
- [ ] Create unit tests for schedule services

### Phase 2: Basic Frontend UI (Week 2-3)

#### Week 2 (continued)
- [ ] Create schedule creation wizard component
- [ ] Build schedule type selection UI
- [ ] Implement timing configuration step

#### Week 3
- [ ] Add parameter configuration UI
- [ ] Create schedule list view
- [ ] Implement enable/disable functionality
- [ ] Add basic schedule editing
- [ ] Create delete confirmation flow

### Phase 3: History and Reporting (Week 3-4)

#### Week 3 (continued)
- [ ] Build schedule history component
- [ ] Create execution timeline view
- [ ] Implement run details modal

#### Week 4
- [ ] Add metrics dashboard
- [ ] Create comparison views
- [ ] Build export functionality
- [ ] Implement result grouping UI
- [ ] Add pagination for history

### Phase 4: Advanced Features (Week 4-5)

#### Week 4 (continued)
- [ ] Create schedule calendar view
- [ ] Build schedule templates library
- [ ] Add CRON expression builder

#### Week 5
- [ ] Implement smart parameter calculation
- [ ] Add cost estimation
- [ ] Create notification configuration
- [ ] Build bulk operations UI
- [ ] Add schedule dependencies

### Phase 5: Monitoring and Optimization (Week 5-6)

#### Week 5 (continued)
- [ ] Create health monitoring dashboard
- [ ] Implement failure alerting

#### Week 6
- [ ] Add performance optimization
- [ ] Create resource usage tracking
- [ ] Implement auto-pause on failures
- [ ] Add comprehensive logging
- [ ] Performance testing and optimization

## Testing Strategy

### Unit Tests

```python
# Backend test coverage targets
test_schedule_service.py         # Schedule CRUD operations
test_schedule_executor.py        # Execution logic
test_cron_generator.py           # CRON expression generation
test_parameter_calculator.py     # Dynamic parameter calculation
test_schedule_history.py         # History aggregation
```

```typescript
// Frontend test coverage targets
ScheduleWizard.test.tsx          // Wizard flow
ScheduleTypeStep.test.tsx        // Type selection
TimingConfiguration.test.tsx     // Timing setup
ScheduleHistory.test.tsx         // History display
ScheduleCalendar.test.tsx        // Calendar view
```

### Integration Tests

```python
# End-to-end schedule flows
test_create_and_execute_schedule.py
test_schedule_with_failures.py
test_bulk_schedule_operations.py
test_schedule_history_aggregation.py
test_timezone_handling.py
```

### E2E Test Scenarios

1. **Create Daily Schedule**
   - Navigate to workflow
   - Open schedule wizard
   - Select daily preset
   - Configure time
   - Verify creation

2. **View Schedule History**
   - Open schedule details
   - Navigate through runs
   - View execution details
   - Export results

3. **Handle Failed Execution**
   - Trigger failure scenario
   - Verify auto-pause
   - Check notifications
   - Manual retry

## Performance Considerations

### Optimization Strategies

1. **Execution Staggering**
   ```python
   # Add random jitter to prevent simultaneous executions
   jitter_seconds = random.randint(0, 60)
   execution_time = scheduled_time + timedelta(seconds=jitter_seconds)
   ```

2. **Resource Pooling**
   ```python
   # Limit concurrent executions
   MAX_CONCURRENT_EXECUTIONS = 10
   execution_semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXECUTIONS)
   ```

3. **Result Caching**
   ```python
   # Cache frequently accessed results
   @cache(ttl=300)  # 5-minute cache
   async def get_schedule_metrics(schedule_id: str):
       # Expensive calculation
   ```

4. **Database Query Optimization**
   ```sql
   -- Efficient schedule run query with pagination
   SELECT sr.*, 
          COUNT(we.id) as execution_count,
          SUM(CASE WHEN we.status = 'SUCCEEDED' THEN 1 ELSE 0 END) as success_count
   FROM schedule_runs sr
   LEFT JOIN workflow_executions we ON we.schedule_run_id = sr.id
   WHERE sr.schedule_id = $1
   GROUP BY sr.id
   ORDER BY sr.scheduled_at DESC
   LIMIT $2 OFFSET $3;
   ```

## Security Considerations

### Access Control
- Schedules inherit workflow permissions
- Users can only manage their own schedules
- Admin override for system schedules

### Token Security
- Encrypted storage of refresh tokens
- Automatic token rotation
- Secure parameter handling

### Audit Trail
- Log all schedule modifications
- Track execution history
- Monitor failed authentication attempts

## Cost Management

### Budget Controls

```python
class ScheduleCostManager:
    async def estimate_monthly_cost(self, schedule: dict) -> float:
        """Estimate monthly cost based on frequency"""
        executions_per_month = self.calculate_monthly_executions(schedule)
        avg_cost_per_execution = await self.get_average_execution_cost(
            schedule['workflow_id']
        )
        return executions_per_month * avg_cost_per_execution
    
    async def check_budget_before_execution(self, schedule: dict) -> bool:
        """Check if execution would exceed budget"""
        if not schedule.get('cost_limit'):
            return True
        
        current_month_cost = await self.get_current_month_cost(schedule['id'])
        estimated_execution_cost = await self.estimate_execution_cost(
            schedule['workflow_id']
        )
        
        return (current_month_cost + estimated_execution_cost) <= schedule['cost_limit']
```

### Cost Tracking Dashboard

```typescript
interface CostMetrics {
  currentMonthCost: number;
  projectedMonthCost: number;
  costTrend: Array<{ date: string; cost: number }>;
  topExpensiveSchedules: Array<{ scheduleId: string; cost: number }>;
  budgetUtilization: number; // percentage
}
```

## Deployment Considerations

### Migration Steps

1. **Database Migration**
   ```bash
   # Apply schema changes
   python scripts/migrations/add_schedule_enhancements.py
   ```

2. **Deploy Backend Services**
   ```bash
   # Start schedule executor service
   python -m amc_manager.services.schedule_executor_service
   ```

3. **Feature Flag Rollout**
   ```python
   # Gradual rollout with feature flags
   if feature_flags.is_enabled('advanced_scheduling', user_id):
       # Show new UI
   ```

### Rollback Plan

1. Disable schedule executor service
2. Revert API endpoints to previous version
3. Keep database schema (backward compatible)
4. Restore previous UI components

### Monitoring Metrics

- Schedule execution success rate
- Average execution latency
- Token refresh failures
- API rate limit hits
- Cost per schedule
- User adoption rate

## Future Enhancements

### Phase 6+ Roadmap

1. **Machine Learning Integration**
   - Optimal execution time prediction
   - Anomaly detection in results
   - Cost optimization recommendations

2. **Advanced Orchestration**
   - Multi-step workflows
   - Conditional branching
   - Data pipeline integration

3. **External Integrations**
   - Slack/Teams notifications
   - Email reports with attachments
   - S3 automatic archival
   - Tableau/PowerBI connectors

4. **Enhanced Analytics**
   - Cross-schedule comparisons
   - Trend analysis
   - Predictive insights
   - Custom dashboards

## Appendix

### CRON Expression Reference

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

Special characters:
- `*` - Any value
- `,` - Value list separator
- `-` - Range of values
- `/` - Step values
- `L` - Last day of month/week
- `#` - Nth occurrence in month

### Timezone Considerations

```python
# Convert schedule time to UTC for storage
from zoneinfo import ZoneInfo

def convert_to_utc(local_time: datetime, timezone: str) -> datetime:
    local_tz = ZoneInfo(timezone)
    local_dt = local_time.replace(tzinfo=local_tz)
    return local_dt.astimezone(ZoneInfo('UTC'))

# Calculate next run in user's timezone
def get_next_run_local(schedule: dict) -> datetime:
    utc_next = schedule['next_run_at']
    user_tz = ZoneInfo(schedule['timezone'])
    return utc_next.astimezone(user_tz)
```

### Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| SCH001 | Invalid CRON expression | Validate expression format |
| SCH002 | Schedule conflict | Adjust timing or merge |
| SCH003 | Token refresh failed | Re-authenticate user |
| SCH004 | Execution timeout | Optimize query or increase limit |
| SCH005 | Budget exceeded | Increase limit or reduce frequency |
| SCH006 | Workflow not found | Verify workflow exists |
| SCH007 | Instance offline | Check instance status |

---

*This document is a living specification and will be updated as the implementation progresses.*

**Last Updated**: 2025-01-19
**Version**: 1.0.0
**Status**: Planning Phase