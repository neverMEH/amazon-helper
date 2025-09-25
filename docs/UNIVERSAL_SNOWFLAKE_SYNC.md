# Universal Snowflake Sync Integration

This document describes the Universal Snowflake Sync system that automatically syncs all workflow executions to Snowflake for users with Snowflake configurations.

## Overview

The Universal Snowflake Sync system ensures that **all** workflow executions are automatically synced to Snowflake, regardless of whether the user explicitly enabled Snowflake storage during execution. This provides a comprehensive data warehouse solution where all execution results are preserved in Snowflake.

## Architecture

### Components

1. **Database Trigger**: Automatically queues completed executions for sync
2. **Sync Queue Table**: Tracks sync status and retry attempts
3. **Background Service**: Processes sync queue items
4. **Monitoring API**: Provides endpoints for monitoring and management

### Data Flow

```
Workflow Execution Completes
         ↓
Database Trigger Fires
         ↓
Execution Queued for Sync
         ↓
Background Service Processes Queue
         ↓
Check User Snowflake Config
         ↓
Upload to Snowflake (if config exists)
         ↓
Update Execution Record
```

## Database Schema

### `snowflake_sync_queue` Table

```sql
CREATE TABLE snowflake_sync_queue (
    id UUID PRIMARY KEY,
    execution_id TEXT REFERENCES workflow_executions(execution_id),
    user_id UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);
```

### Database Trigger

The trigger automatically queues executions when they complete:

```sql
CREATE TRIGGER trigger_queue_universal_snowflake_sync
    AFTER UPDATE ON workflow_executions
    FOR EACH ROW
    EXECUTE FUNCTION queue_execution_for_universal_snowflake_sync();
```

## Services

### UniversalSnowflakeSyncService

The main service that processes the sync queue:

- **Processes queue every 30 seconds**
- **Handles up to 5 concurrent syncs**
- **Retries failed syncs up to 3 times**
- **Only syncs for users with Snowflake configurations**

### Key Methods

- `start()`: Start the background service
- `stop()`: Stop the service gracefully
- `process_sync_queue()`: Process pending sync items
- `sync_execution_to_snowflake()`: Sync a single execution
- `get_sync_stats()`: Get sync statistics
- `get_failed_syncs()`: Get failed sync details
- `retry_failed_sync()`: Retry a failed sync

## API Endpoints

### Monitoring Endpoints

- `GET /api/snowflake-sync/stats` - Get sync queue statistics
- `GET /api/snowflake-sync/failed` - Get failed syncs
- `POST /api/snowflake-sync/retry/{sync_id}` - Retry a failed sync
- `GET /api/snowflake-sync/queue` - Get sync queue items
- `GET /api/snowflake-sync/execution/{execution_id}/sync-status` - Get execution sync status
- `POST /api/snowflake-sync/backfill` - Manually trigger sync for existing executions

### Example API Usage

```bash
# Get sync statistics
curl -X GET "http://localhost:8000/api/snowflake-sync/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get failed syncs
curl -X GET "http://localhost:8000/api/snowflake-sync/failed?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Retry a failed sync
curl -X POST "http://localhost:8000/api/snowflake-sync/retry/SYNC_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Backfill existing executions
curl -X POST "http://localhost:8000/api/snowflake-sync/backfill" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

### User Snowflake Configuration

Users must have a Snowflake configuration in the `snowflake_configurations` table:

```sql
INSERT INTO snowflake_configurations (
    user_id,
    account_identifier,
    warehouse,
    database,
    schema,
    username,
    password_encrypted,
    is_active
) VALUES (
    'user-uuid',
    'your-account.snowflakecomputing.com',
    'COMPUTE_WH',
    'AMC_DATA',
    'WORKFLOW_RESULTS',
    'your-username',
    'encrypted-password',
    true
);
```

### Service Configuration

The service can be configured by modifying the `UniversalSnowflakeSyncService` class:

```python
class UniversalSnowflakeSyncService:
    def __init__(self):
        self.check_interval = 30  # Check every 30 seconds
        self.max_concurrent_syncs = 5  # Max concurrent syncs
```

## Installation

### 1. Run Database Migration

```bash
# Apply the migration
psql -h your-supabase-host -U postgres -d postgres -f database/supabase/migrations/13_universal_snowflake_sync.sql
```

### 2. Start the Service

The service is automatically started with the main application:

```python
# In main_supabase.py
from amc_manager.services.universal_snowflake_sync_service import universal_snowflake_sync_service

# Service starts automatically in lifespan event
asyncio.create_task(universal_snowflake_sync_service.start())
```

### 3. Test the Integration

```bash
# Run the test script
python test_universal_snowflake_sync.py
```

## Monitoring

### Sync Statistics

The system provides comprehensive monitoring through the API:

```python
# Get sync statistics
stats = await universal_snowflake_sync_service.get_sync_stats()
print(f"Pending: {stats.get('pending', {}).get('count', 0)}")
print(f"Processing: {stats.get('processing', {}).get('count', 0)}")
print(f"Completed: {stats.get('completed', {}).get('count', 0)}")
print(f"Failed: {stats.get('failed', {}).get('count', 0)}")
```

### Database Views

The system includes helpful views for monitoring:

- `snowflake_sync_queue_summary`: Summary statistics by status
- `snowflake_sync_failures`: Detailed view of failed syncs

### Logs

The service logs all activities:

```
INFO: Processing 5 universal Snowflake sync items
INFO: Syncing execution exec_12345678 to Snowflake table workflow_execution_2024-01-15_exec_12345678
INFO: Successfully synced execution exec_12345678 to Snowflake
```

## Troubleshooting

### Common Issues

1. **No Snowflake Configuration**: Users without Snowflake configs are skipped
2. **Connection Issues**: Failed connections are retried up to 3 times
3. **Data Issues**: Executions without results are marked as failed

### Debugging

1. **Check Sync Queue**: Use the API to view queue status
2. **Check Logs**: Review service logs for errors
3. **Test Connection**: Verify Snowflake configuration
4. **Manual Retry**: Use the retry endpoint for failed syncs

### Performance Tuning

- **Adjust `check_interval`**: Reduce for faster processing
- **Adjust `max_concurrent_syncs`**: Increase for higher throughput
- **Monitor Queue Size**: Use stats endpoint to monitor backlog

## Benefits

1. **Universal Coverage**: All executions are automatically synced
2. **User-Controlled**: Only syncs for users with Snowflake configs
3. **Reliable**: Database triggers ensure no executions are missed
4. **Scalable**: Background service handles high volume
5. **Non-Blocking**: Doesn't slow down execution completion
6. **Monitoring**: Comprehensive monitoring and management tools
7. **Backward Compatible**: Existing `snowflake_enabled` flag still works

## Migration from Existing System

The Universal Snowflake Sync system is backward compatible with the existing opt-in system:

- Existing executions with `snowflake_enabled = true` continue to work
- New executions are automatically queued for sync
- Users can still manually enable Snowflake for specific executions
- The system respects user Snowflake configurations

## Future Enhancements

1. **Selective Sync**: Allow users to exclude certain executions
2. **Data Transformation**: Add data transformation capabilities
3. **Multiple Destinations**: Support syncing to multiple Snowflake accounts
4. **Real-time Sync**: Reduce sync delay for critical executions
5. **Advanced Monitoring**: Add dashboards and alerts
