# Data Collections System

## Overview

The Data Collections system enables automated historical data gathering by executing workflows across multiple time periods. It supports 52-week backfills with parallel processing, automatic retry logic, and real-time progress tracking for reporting and analytics.

## Key Components

### Backend Services
- `amc_manager/services/data_collection_service.py` - Main collection management
- `amc_manager/services/collection_executor.py` - Background execution service
- `amc_manager/api/supabase/data_collections.py` - API endpoints

### Frontend Components
- `frontend/src/pages/DataCollections.tsx` - Collections list view
- `frontend/src/components/DataCollectionForm.tsx` - Collection creation form
- `frontend/src/components/DataCollectionProgress.tsx` - Progress tracking
- `frontend/src/components/CollectionExecutionModal.tsx` - Week execution details

### Database Tables
- `report_data_collections` - Collection configurations
- `report_data_weeks` - Individual week tracking
- `workflow_executions` - Actual execution records (joined)

## Technical Implementation

### Collection Creation
```python
# DataCollectionService.create_collection
async def create_collection(self, collection_data: dict):
    # 1. Create collection record
    collection = self.db.table('report_data_collections').insert({
        'name': collection_data['name'],
        'workflow_id': collection_data['workflow_id'],
        'instance_id': collection_data['instance_id'],  # UUID FK
        'start_date': collection_data['start_date'],
        'end_date': collection_data['end_date'],
        'status': 'ACTIVE'
    }).execute()
    
    # 2. Generate week records
    weeks = self._generate_week_periods(start_date, end_date)
    for week in weeks:
        self.db.table('report_data_weeks').insert({
            'collection_id': collection.data[0]['id'],
            'week_start_date': week['start'],
            'week_end_date': week['end'],
            'status': 'PENDING'
        }).execute()
```

### Parallel Execution Strategy
- **Collection Concurrency**: Max 5 collections running simultaneously
- **Week Concurrency**: Max 10 weeks per collection in parallel
- **Instance Throttling**: Respects AMC rate limits per instance

### Collection Executor Service
```python
# collection_executor.py - Background service
async def process_collections(self):
    active_collections = self.get_active_collections()
    
    for collection in active_collections:
        if self.can_process_collection(collection):
            await self.process_collection_weeks(collection)

async def process_collection_weeks(self, collection):
    pending_weeks = self.get_pending_weeks(collection['id'])
    
    # Process up to 10 weeks concurrently
    semaphore = asyncio.Semaphore(10)
    tasks = []
    
    for week in pending_weeks[:10]:
        task = self.execute_week_with_semaphore(semaphore, collection, week)
        tasks.append(task)
    
    await asyncio.gather(*tasks, return_exceptions=True)
```

## Data Flow

1. **Collection Setup**: User creates collection with date range
2. **Week Generation**: System creates individual week records
3. **Background Processing**: Executor service processes pending weeks
4. **Workflow Execution**: Each week triggers a workflow execution
5. **Status Updates**: Real-time progress tracking
6. **Result Aggregation**: All week results available for analysis

## Week Processing Logic

### Date Period Calculation
```python
def generate_week_periods(self, start_date: date, end_date: date) -> List[dict]:
    weeks = []
    current = start_date
    
    while current <= end_date:
        week_start = current - timedelta(days=current.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday
        
        weeks.append({
            'start': week_start,
            'end': min(week_end, end_date)
        })
        
        current = week_end + timedelta(days=1)
    
    return weeks
```

### Parameter Substitution
Each week execution includes:
- `{{start_date}}` → Week start date
- `{{end_date}}` → Week end date
- Campaign/ASIN filters from collection config

## Critical Gotchas

### Instance ID Resolution
```python
# CRITICAL: Collections store UUID reference but AMC needs string ID
collection_data = self.db.table('report_data_collections')\
    .select('*, amc_instances(*)')\
    .eq('id', collection_id)\
    .execute()

# Use amc_instances.instance_id for API calls, not collections.instance_id (UUID)
instance_id = collection_data['amc_instances']['instance_id']  # String like "amcibersblt"
entity_id = collection_data['amc_instances']['amc_accounts']['account_id']
```

## Status Management

### Collection Status States
- `ACTIVE` - Collection is running
- `PAUSED` - Temporarily paused by user
- `COMPLETED` - All weeks finished successfully
- `FAILED` - Collection failed with errors

### Week Status States
- `PENDING` - Week not yet executed
- `RUNNING` - Execution in progress
- `SUCCESS` - Week completed successfully
- `FAILED` - Week execution failed
- `SKIPPED` - Week skipped due to filters

## Error Handling and Retries

### Automatic Retry Logic
```python
async def retry_failed_week(self, week_id: str):
    # Reset week status to PENDING
    self.db.table('report_data_weeks')\
        .update({'status': 'PENDING', 'error_message': None})\
        .eq('id', week_id)\
        .execute()
    
    # Will be picked up by next executor cycle
```

### Collection Recovery
- Individual week failures don't stop entire collection
- Failed weeks can be retried individually
- Collections can be paused and resumed

## Frontend Integration

### Progress Tracking
```typescript
// Real-time progress updates
const { data: collections } = useQuery({
  queryKey: ['data-collections'],
  queryFn: () => dataCollectionService.list(),
  refetchInterval: 5000  // Update every 5 seconds
});

// Calculate progress percentage
const progress = {
  total: collection.total_weeks,
  completed: collection.completed_weeks,
  percentage: Math.round((collection.completed_weeks / collection.total_weeks) * 100)
};
```

### Week Execution Modal
```typescript
// View individual week executions
const openExecutionModal = (collection, week) => {
  // Fetch execution details for specific week
  // Show execution logs, results, timing
};
```

## Interconnections

### With Workflow System
- Each week creates a workflow execution
- Uses same parameter substitution system
- Inherits execution monitoring and results

### With Scheduling System
- Collections can be scheduled for regular updates
- Supports incremental data collection

### With Dashboard System
- Collection results feed into dashboard widgets
- Historical data enables trend analysis

## Performance Optimization

### Batch Processing
- Process multiple weeks concurrently
- Respect AMC API rate limits
- Efficient database queries for status updates

### Memory Management
- Stream large result sets
- Clean up completed execution data
- Optimize week record queries

## Monitoring and Analytics

### Collection Metrics
```sql
-- Track collection performance
SELECT 
  c.name,
  c.status,
  COUNT(w.id) as total_weeks,
  COUNT(CASE WHEN w.status = 'SUCCESS' THEN 1 END) as completed_weeks,
  AVG(CASE WHEN w.execution_duration IS NOT NULL THEN w.execution_duration END) as avg_duration
FROM report_data_collections c
LEFT JOIN report_data_weeks w ON w.collection_id = c.id
GROUP BY c.id, c.name, c.status;
```

### Failure Analysis
- Track common failure patterns
- Identify problematic date ranges
- Monitor AMC API response times

## Testing Strategy

### Unit Tests
- Week period generation
- Status transition logic
- Parameter substitution

### Integration Tests
- End-to-end collection execution
- Concurrent processing limits
- Error recovery scenarios