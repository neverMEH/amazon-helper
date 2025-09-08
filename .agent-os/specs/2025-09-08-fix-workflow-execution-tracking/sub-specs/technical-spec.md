# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-08-fix-workflow-execution-tracking/spec.md

> Created: 2025-09-08
> Version: 1.0.0

## Technical Requirements

### Primary Requirement
Modify the data collection service layer to capture and store workflow execution IDs in the report_data_weeks table during historical data collection operations.

### Data Flow Requirements
1. **Execution ID Capture**: Extract execution_id from AMC API workflow execution responses
2. **Parameter Passing**: Extend service method signatures to pass execution_id through the call chain
3. **Database Storage**: Store execution_id in report_data_weeks.execution_id column
4. **Error Handling**: Handle cases where execution_id might be null or missing
5. **Backward Compatibility**: Ensure existing calls without execution_id continue to work

### Performance Requirements
- No significant performance impact on data collection operations
- Database updates should remain atomic and consistent
- Memory usage should not increase significantly

### Data Integrity Requirements
- execution_id must be stored correctly when available
- NULL values should be handled gracefully for backward compatibility
- Foreign key constraints should be maintained if they exist

## Approach

### Code Changes Required

#### 1. HistoricalCollectionService Modifications

**File**: `amc_manager/services/historical_collection_service.py`

**Method**: `_collect_week_data()`

**Current Implementation Issues**:
```python
# Current problematic flow
execution_result = await amc_api_client_with_retry.create_workflow_execution(...)
# execution_result contains execution_id but it's not captured
await self.update_week_status(collection_id, week_id, 'completed', result_data)
# execution_id is lost here
```

**Required Changes**:
```python
# Extract execution_id from result
execution_result = await amc_api_client_with_retry.create_workflow_execution(...)
execution_id = execution_result.get('execution_id') if execution_result else None

# Pass execution_id to update method
await self.update_week_status(
    collection_id=collection_id,
    week_id=week_id, 
    status='completed',
    data=result_data,
    execution_id=execution_id  # New parameter
)
```

#### 2. DataCollectionService Method Signature Updates

**File**: `amc_manager/services/data_collection_service.py`

**Method**: `update_week_status()`

**Current Signature**:
```python
async def update_week_status(self, collection_id: str, week_id: str, status: str, data: dict = None):
```

**New Signature**:
```python
async def update_week_status(
    self, 
    collection_id: str, 
    week_id: str, 
    status: str, 
    data: dict = None,
    execution_id: str = None  # New optional parameter
):
```

**Implementation Update**:
```python
# Build update dictionary
update_data = {
    'status': status,
    'updated_at': datetime.utcnow().isoformat()
}

# Add execution_id if provided
if execution_id is not None:
    update_data['execution_id'] = execution_id

# Add data if provided  
if data is not None:
    update_data['data'] = data

# Execute database update
result = self.supabase.table('report_data_weeks')\
    .update(update_data)\
    .eq('collection_id', collection_id)\
    .eq('id', week_id)\
    .execute()
```

#### 3. Error Handling Enhancements

**Scenarios to Handle**:
- AMC API returns null/missing execution_id
- Database update fails with execution_id
- Invalid execution_id format
- Rollback scenarios when execution tracking fails

**Implementation**:
```python
try:
    # Extract execution_id safely
    execution_id = None
    if execution_result and isinstance(execution_result, dict):
        execution_id = execution_result.get('execution_id')
        
    # Log execution tracking
    self.logger.info(f"Tracking execution_id: {execution_id} for week {week_id}")
    
    # Update with execution tracking
    await self.update_week_status(
        collection_id, week_id, 'completed', 
        data=result_data, execution_id=execution_id
    )
    
except Exception as e:
    self.logger.error(f"Failed to update execution tracking for week {week_id}: {e}")
    # Fallback to update without execution_id to maintain functionality
    await self.update_week_status(collection_id, week_id, 'completed', data=result_data)
```

### Database Considerations

#### Column Validation
The `report_data_weeks.execution_id` column should:
- Accept NULL values (for backward compatibility)
- Be of appropriate string type (VARCHAR or TEXT)
- Have proper indexing if execution_id lookups are needed

#### Query Pattern Updates
```sql
-- Verify column exists and type
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'report_data_weeks' 
AND column_name = 'execution_id';

-- Sample queries with execution tracking
SELECT rdw.*, we.status as execution_status
FROM report_data_weeks rdw
LEFT JOIN workflow_executions we ON we.id = rdw.execution_id
WHERE rdw.collection_id = ?;
```

### Testing Strategy

#### Unit Tests Required
1. **HistoricalCollectionService Tests**:
   - Test execution_id extraction from AMC API responses
   - Test parameter passing to update_week_status
   - Test error handling when execution_id is missing

2. **DataCollectionService Tests**:
   - Test update_week_status with execution_id parameter
   - Test backward compatibility (calls without execution_id)
   - Test database update queries include execution_id

#### Integration Tests Required  
1. **End-to-End Collection Tests**:
   - Test full data collection flow stores execution_id
   - Test multiple week collections maintain separate execution_ids
   - Test error scenarios don't break existing functionality

#### Database Tests Required
1. **Schema Validation Tests**:
   - Verify execution_id column exists and accepts NULLs
   - Test foreign key constraints if applicable
   - Test data retrieval with execution_id joins

### Migration Considerations

#### Deployment Strategy
1. **Backward Compatibility**: All changes must be backward compatible
2. **Gradual Rollout**: New execution_id tracking should not break existing collections
3. **Fallback Mechanism**: System should continue working even if execution_id tracking fails

#### Data Migration
- Existing report_data_weeks records will have NULL execution_id (acceptable)
- No immediate backfill required - future collections will have proper tracking
- Consider optional backfill script for recent collections if execution history is available

## External Dependencies

### AMC API Dependencies
- Relies on consistent execution_id format in AMC API responses
- Depends on AMC workflow execution endpoints returning execution metadata
- Requires stable AMC authentication for execution tracking

### Database Dependencies
- Supabase PostgreSQL database with existing report_data_weeks table
- Proper database connection handling in services
- Transaction support for atomic updates

### Service Dependencies
- AMC API client with retry mechanism
- Existing data collection service architecture
- Historical collection service workflow execution logic
- Background task processing system

### Monitoring Requirements
- Log execution_id capture and storage operations
- Monitor execution_id NULL rates to detect API issues
- Alert on execution tracking failures
- Track data collection success rates with execution tracking