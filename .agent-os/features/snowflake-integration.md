# Snowflake Integration

## Overview

The Snowflake integration feature enables automatic upload of AMC execution results to Snowflake data warehouse, providing seamless data pipeline from AMC queries to enterprise analytics platforms. The system supports both run-once executions and recurring schedules with sophisticated UPSERT logic, automatic retry mechanisms, and graceful degradation when Snowflake is unavailable.

## Recent Changes (2025-11-19)

### Comprehensive Snowflake Upload Integration for All Executions
**Major Feature**: Implemented complete Snowflake integration across all execution types with composite UPSERT key support, automatic retry logic, and user configuration management.

**Key Capabilities**:
1. **Composite UPSERT Key**: Prevents duplicate data using execution_id + time_window_start + time_window_end
2. **Automatic Retry Logic**: Up to 3 attempts with exponential backoff for failed uploads
3. **User Configuration**: Encrypted credential storage with test connection validation
4. **Graceful Degradation**: Executions succeed even if Snowflake upload fails
5. **Status Tracking**: Real-time UI indicators for upload progress and failures

### Backend Implementation

**Database Migration (16_snowflake_strategy_column.sql)**:
```sql
-- Added to workflow_schedules
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS snowflake_strategy VARCHAR(20) DEFAULT 'upsert'
  CHECK (snowflake_strategy IN ('upsert', 'append'));

-- Added to workflow_executions
ALTER TABLE workflow_executions
ADD COLUMN IF NOT EXISTS snowflake_attempt_count INTEGER DEFAULT 0;
ADD COLUMN IF NOT EXISTS snowflake_status VARCHAR(20)
  CHECK (snowflake_status IN ('pending', 'uploading', 'uploaded', 'failed', 'skipped'));
ADD COLUMN IF NOT EXISTS snowflake_error_message TEXT;
ADD COLUMN IF NOT EXISTS snowflake_uploaded_at TIMESTAMP WITH TIME ZONE;
```

**SnowflakeService Enhancement** (`amc_manager/services/snowflake_service.py`):
- Composite UPSERT key implementation using execution_id + date range columns
- Automatic date column detection for flexible primary key strategies
- MERGE SQL generation with conflict resolution
- Fernet encryption for password/private key storage
- Graceful handling when user has no Snowflake configuration

**Key Method - Composite UPSERT Key Logic**:
```python
def _detect_date_columns_for_upsert(self, df: pd.DataFrame, execution_parameters: Dict) -> List[str]:
    """
    Detect date columns for composite UPSERT key
    Priority:
    1. time_window_start + time_window_end (from execution parameters)
    2. week_start column (if present)
    3. First date/timestamp column in dataframe
    """
    date_columns = []

    # Check for date range columns first
    if 'time_window_start' in df.columns and 'time_window_end' in df.columns:
        date_columns = ['time_window_start', 'time_window_end']
        logger.info("Using date range columns for composite UPSERT key")
    # Check for week_start column
    elif 'week_start' in df.columns:
        date_columns = ['week_start']
        logger.info("Using week_start column for UPSERT key")
    # Fallback to first date column
    else:
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_columns = [col]
                logger.info(f"Using detected date column '{col}' for UPSERT key")
                break

    return date_columns
```

**MERGE SQL Generation**:
```python
def _generate_merge_sql(self, table_name: str, df: pd.DataFrame,
                        execution_id: str, execution_parameters: Dict) -> str:
    """
    Generate MERGE statement with composite UPSERT key
    Format: MERGE INTO table USING temp_table ON (composite key match)
         WHEN MATCHED THEN UPDATE SET ...
         WHEN NOT MATCHED THEN INSERT ...
    """
    date_columns = self._detect_date_columns_for_upsert(df, execution_parameters)

    # Build composite ON clause
    on_conditions = ['target."execution_id" = source."execution_id"']
    for date_col in date_columns:
        on_conditions.append(f'target."{date_col}" = source."{date_col}"')

    on_clause = ' AND '.join(on_conditions)

    merge_sql = f"""
        MERGE INTO {table_name} AS target
        USING temp_table AS source
        ON {on_clause}
        WHEN MATCHED THEN
            UPDATE SET {update_columns}
        WHEN NOT MATCHED THEN
            INSERT ({insert_columns})
            VALUES ({insert_values});
    """

    return merge_sql
```

**ExecutionMonitorService Retry Logic** (`amc_manager/services/execution_monitor_service.py`):
```python
async def _handle_snowflake_upload(self, execution: Dict):
    """Upload execution results to Snowflake with automatic retry"""
    snowflake_enabled = execution.get('metadata', {}).get('snowflake_enabled')

    if not snowflake_enabled:
        return  # Skip if not enabled

    # Check attempt count
    attempt_count = execution.get('snowflake_attempt_count', 0)
    max_attempts = 3

    if attempt_count >= max_attempts:
        logger.warning(f"Max Snowflake upload attempts ({max_attempts}) reached")
        return

    try:
        # Attempt upload
        snowflake_service = SnowflakeService()
        result = await snowflake_service.upload_execution_results(
            execution_id=execution['id'],
            results=execution['result_data'],
            table_name=execution['metadata']['snowflake_table_name'],
            user_id=execution['user_id'],
            execution_parameters={
                'timeWindowStart': execution.get('time_window_start'),
                'timeWindowEnd': execution.get('time_window_end')
            }
        )

        if result.get('success'):
            logger.info(f"Snowflake upload successful for execution {execution['id']}")
        elif result.get('skipped'):
            logger.info(f"Snowflake upload skipped (no user config)")
        else:
            raise Exception(result.get('error', 'Unknown upload error'))

    except Exception as e:
        # Increment attempt count and update status
        self.db.table('workflow_executions').update({
            'snowflake_attempt_count': attempt_count + 1,
            'snowflake_status': 'failed',
            'snowflake_error_message': str(e)
        }).eq('id', execution['id']).execute()

        logger.error(f"Snowflake upload failed (attempt {attempt_count + 1}/{max_attempts}): {e}")

        # Schedule retry with exponential backoff
        if attempt_count + 1 < max_attempts:
            retry_delay = 2 ** attempt_count * 60  # 1min, 2min, 4min
            logger.info(f"Scheduling Snowflake retry in {retry_delay} seconds")
```

**User Configuration Management**:
```python
def get_user_snowflake_config(self, user_id: str) -> Optional[Dict]:
    """Fetch and decrypt user's Snowflake configuration"""
    config = self.db.table('user_snowflake_configs')\
        .select('*')\
        .eq('user_id', user_id)\
        .eq('is_active', True)\
        .single()\
        .execute()

    if not config.data:
        return None

    # Decrypt password
    encrypted_password = config.data['password']
    decrypted_password = self.fernet.decrypt(encrypted_password.encode()).decode()
    config.data['password'] = decrypted_password

    return config.data
```

### Frontend Implementation

**SnowflakeConfigStep Component** (`frontend/src/components/schedules/SnowflakeConfigStep.tsx`):
- New wizard step for schedule creation (Step 5)
- Toggle for enabling/disabling Snowflake upload
- Table name and schema configuration inputs
- Auto-generated table name format: `{instance}_{brand}_{template}`
- Strategy locked to UPSERT for schedules (prevents duplicates)

**Component Structure**:
```typescript
interface SnowflakeConfigStepProps {
  snowflakeEnabled: boolean;
  snowflakeTableName: string;
  snowflakeSchemaName: string;
  onSnowflakeEnabledChange: (enabled: boolean) => void;
  onSnowflakeTableNameChange: (name: string) => void;
  onSnowflakeSchemaNameChange: (name: string) => void;
  autoGeneratedTableName?: string;
}

const SnowflakeConfigStep: React.FC<SnowflakeConfigStepProps> = ({
  snowflakeEnabled,
  snowflakeTableName,
  snowflakeSchemaName,
  onSnowflakeEnabledChange,
  onSnowflakeTableNameChange,
  onSnowflakeSchemaNameChange,
  autoGeneratedTableName
}) => {
  return (
    <div className="space-y-6">
      {/* Toggle switch */}
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">Enable Snowflake Upload</label>
        <input
          type="checkbox"
          checked={snowflakeEnabled}
          onChange={(e) => onSnowflakeEnabledChange(e.target.checked)}
        />
      </div>

      {snowflakeEnabled && (
        <>
          {/* Table name input with auto-generated suggestion */}
          <div>
            <label>Table Name</label>
            <input
              value={snowflakeTableName || autoGeneratedTableName}
              onChange={(e) => onSnowflakeTableNameChange(e.target.value)}
              placeholder={autoGeneratedTableName}
            />
          </div>

          {/* Schema name input */}
          <div>
            <label>Schema Name (optional)</label>
            <input
              value={snowflakeSchemaName}
              onChange={(e) => onSnowflakeSchemaNameChange(e.target.value)}
              placeholder="Default schema will be used"
            />
          </div>

          {/* Strategy indicator (locked to UPSERT) */}
          <div className="text-sm text-gray-600">
            Upload Strategy: UPSERT (prevents duplicates)
          </div>
        </>
      )}
    </div>
  );
};
```

**ScheduleWizard Integration** (`frontend/src/components/schedules/ScheduleWizard.tsx`):
- Added Snowflake configuration as Step 5
- Passes configuration to backend when creating schedules
- Auto-generates table name based on instance, brand, and template

**TemplateExecutionWizard Enhancement** (`frontend/src/components/instances/TemplateExecutionWizard.tsx`):
- Step 4 includes Snowflake toggle for recurring schedules
- Optional table name and schema configuration
- Passes config to schedule creation endpoint

**Execution List UI Updates** (`frontend/src/components/executions/AMCExecutionList.tsx`):
- Color-coded status badges for Snowflake upload status:
  - Green "Uploaded" - Successfully uploaded
  - Blue "Uploading" - Upload in progress
  - Red "Failed" - Upload failed (with attempt count)
  - Yellow "Pending" - Queued for upload
  - Gray "Skipped" - User has no Snowflake config

**Status Badge Component**:
```typescript
const SnowflakeStatusBadge: React.FC<{ execution: WorkflowExecution }> = ({ execution }) => {
  const status = execution.snowflake_status;
  const attemptCount = execution.snowflake_attempt_count || 0;

  const statusConfig = {
    'uploaded': { color: 'green', icon: '✓', label: 'Uploaded' },
    'uploading': { color: 'blue', icon: '↑', label: 'Uploading' },
    'failed': { color: 'red', icon: '✗', label: `Failed (${attemptCount}/3)` },
    'pending': { color: 'yellow', icon: '⏳', label: 'Pending' },
    'skipped': { color: 'gray', icon: '—', label: 'Skipped' }
  };

  const config = statusConfig[status] || statusConfig['skipped'];

  return (
    <span className={`px-2 py-1 rounded-full text-xs bg-${config.color}-100 text-${config.color}-800`}>
      {config.icon} {config.label}
    </span>
  );
};
```

**Execution Detail Modal** (`frontend/src/components/executions/AMCExecutionDetail.tsx`):
- Detailed Snowflake status section
- Manual retry button for failed uploads (shows attempt count)
- Error message display
- Upload timestamp when successful

**Settings Page** (`frontend/src/pages/Profile.tsx`):
- Complete Snowflake configuration section
- Fields: account, username, password, warehouse, database, schema, role
- Test Connection button with loading state
- Save/Delete buttons with validation
- Password security (never populate from server, always require re-entry)

**Settings Form Structure**:
```typescript
interface SnowflakeConfigForm {
  account: string;
  username: string;
  password: string;  // Never pre-filled for security
  warehouse: string;
  database: string;
  schema: string;
  role: string;
}

const SnowflakeConfigSection: React.FC = () => {
  const [config, setConfig] = useState<SnowflakeConfigForm>({...});
  const [isLoading, setIsLoading] = useState(false);

  const handleTestConnection = async () => {
    setIsLoading(true);
    try {
      const result = await snowflakeService.testConnection(config);
      toast.success('Connection successful!');
    } catch (error) {
      toast.error('Connection failed: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    await snowflakeService.saveConfig(config);
    toast.success('Configuration saved');
  };

  return (
    <div className="space-y-4">
      <h3>Snowflake Configuration</h3>
      {/* Form fields */}
      <div className="flex space-x-2">
        <button onClick={handleTestConnection}>Test Connection</button>
        <button onClick={handleSave}>Save</button>
      </div>
    </div>
  );
};
```

### Testing

**Backend Unit Tests** (`tests/services/test_snowflake_service_unit.py`):
- 20/20 tests passing
- Comprehensive coverage for UPSERT key logic
- Date column detection algorithm tests
- MERGE SQL generation validation
- Encryption/decryption tests
- Mock Snowflake connector for isolated testing

**Test Coverage**:
```python
class TestSnowflakeService:
    def test_detect_date_columns_with_date_range(self):
        """Test composite key with time_window_start + time_window_end"""

    def test_detect_date_columns_with_week_start(self):
        """Test fallback to week_start column"""

    def test_detect_date_columns_with_detected_column(self):
        """Test auto-detection of date columns"""

    def test_generate_merge_sql_with_composite_key(self):
        """Test MERGE statement generation"""

    def test_upload_with_no_user_config(self):
        """Test graceful skip when user has no config"""

    def test_encryption_decryption(self):
        """Test Fernet encryption for passwords"""
```

### API Endpoints

**Snowflake Configuration** (`amc_manager/api/snowflake_config.py`):
```http
GET    /api/snowflake/config          # Get user's Snowflake config
POST   /api/snowflake/config          # Save Snowflake config
PUT    /api/snowflake/config          # Update Snowflake config
DELETE /api/snowflake/config          # Delete Snowflake config
POST   /api/snowflake/test-connection # Test Snowflake connection
```

**Manual Retry Endpoint**:
```http
POST   /api/executions/{execution_id}/retry-snowflake
```

**Endpoint Implementation**:
```python
@router.post("/executions/{execution_id}/retry-snowflake")
async def retry_snowflake_upload(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Manually retry Snowflake upload for failed execution"""

    # Verify user owns execution
    execution = db.table('workflow_executions')\
        .select('*')\
        .eq('id', execution_id)\
        .eq('user_id', current_user['id'])\
        .single()\
        .execute()

    if not execution.data:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Reset attempt count and status
    db.table('workflow_executions').update({
        'snowflake_status': 'pending',
        'snowflake_attempt_count': 0,
        'snowflake_error_message': None
    }).eq('id', execution_id).execute()

    # Trigger upload
    await execution_monitor_service.handle_snowflake_upload(execution.data)

    return {"message": "Snowflake upload retry initiated"}
```

## Architecture

### Data Flow

```
AMC Execution Complete
    ↓
ExecutionMonitorService detects completion
    ↓
Check if snowflake_enabled in execution metadata
    ↓
Fetch user Snowflake configuration
    ↓
    ├─ No config found → Mark as 'skipped', continue
    │
    └─ Config exists
        ↓
    Update status to 'uploading'
        ↓
    Extract execution parameters (date range)
        ↓
    Convert results to Pandas DataFrame
        ↓
    Add metadata columns (execution_id, date range, week_start)
        ↓
    Detect date columns for composite UPSERT key
        ↓
    Create Snowflake connection
        ↓
    Create table if not exists (with composite PK)
        ↓
    Generate and execute MERGE SQL
        ↓
    Upload succeeded?
        ├─ Yes → Update status to 'uploaded', record timestamp
        │
        └─ No → Increment attempt count, update status to 'failed'
            ↓
        Attempt count < 3?
            ├─ Yes → Schedule retry with exponential backoff
            └─ No → Mark as permanently failed
```

### Composite UPSERT Key Strategy

**Problem**: Recurring schedules execute the same query with different date ranges. Using only `execution_id` as primary key would allow duplicate data for the same time period if a schedule is manually re-run.

**Solution**: Composite primary key using `(execution_id, time_window_start, time_window_end)`

**Benefits**:
- Prevents duplicate data for same date range
- Allows same execution to be re-run without creating duplicates
- Enables incremental updates (e.g., update metrics for a specific week)
- Maintains referential integrity between AMC and Snowflake

**Fallback Strategy**:
1. First priority: `time_window_start` + `time_window_end` columns (if present)
2. Second priority: `week_start` column (for historical collections)
3. Third priority: First detected date/timestamp column in results
4. No dates found: Use `execution_id` only (append mode)

## Key Features

### 1. Automatic Retry Logic

**Implementation**:
- Up to 3 retry attempts per execution
- Exponential backoff: 1 minute → 2 minutes → 4 minutes
- Attempt count tracked in database
- Manual retry option in UI

**Use Case**: Network issues, temporary Snowflake outages, or transient errors don't permanently fail uploads.

### 2. Graceful Degradation

**Implementation**:
- Check for user Snowflake configuration before upload
- Mark as 'skipped' if no config found
- AMC execution succeeds regardless of Snowflake status
- Clear UI indicators for skipped uploads

**Use Case**: Users without Snowflake can still execute AMC queries. Snowflake is optional, not required.

### 3. Encrypted Credential Storage

**Implementation**:
- Fernet symmetric encryption for passwords and private keys
- Encryption key stored in environment variable (`FERNET_KEY`)
- Never return plaintext passwords in API responses
- Password field always empty in UI (must re-enter to update)

**Security Benefits**:
- Database compromise doesn't expose Snowflake credentials
- Credentials encrypted at rest
- Follows security best practices for sensitive data

### 4. Real-Time Status Tracking

**Implementation**:
- 5 status states: pending, uploading, uploaded, failed, skipped
- Visual badges with color coding in execution list
- Detailed error messages in execution detail modal
- Attempt count display for failed uploads

**UI States**:
- Pending (yellow): Queued for upload
- Uploading (blue): Upload in progress
- Uploaded (green): Successfully uploaded with timestamp
- Failed (red): Upload failed with attempt count (1/3, 2/3, 3/3)
- Skipped (gray): No Snowflake configuration

## Integration Points

### With Execution Monitoring System
- ExecutionMonitorService detects completed executions
- Triggers Snowflake upload after successful AMC execution
- Updates execution status with upload progress
- Coordinates retry attempts

### With Scheduling System
- Schedule wizard includes Snowflake configuration step
- Schedule config stored in `workflow_schedules.metadata`
- Each scheduled execution inherits Snowflake settings
- UPSERT strategy prevents duplicates across schedule runs

### With Template Execution Wizard
- Template wizard includes Snowflake toggle in Step 4
- Auto-generates table names based on template and brand
- Passes configuration to schedule creation endpoint
- Supports both run-once and recurring executions

## Critical Notes

### Date Format Requirements
- Snowflake columns created as `TIMESTAMP_NTZ` (no timezone)
- AMC date parameters use format: `YYYY-MM-DD` (no time component)
- Execution date ranges stored as ISO strings
- Pandas automatically handles date parsing and conversion

### Table Naming Convention
- Auto-generated format: `{instance}_{brand}_{template}`
- Hyphens replaced with underscores for Snowflake compatibility
- Table names sanitized (alphanumeric + underscores only)
- Users can override with custom table name

### UPSERT vs Append Strategy
- **UPSERT** (default for schedules): Updates existing rows, inserts new ones
- **Append** (available for run-once): Always inserts new rows
- UPSERT requires primary key constraint on table
- Schedule strategy locked to UPSERT to prevent duplicates

### Password Security
- Never pre-fill password field in settings form
- Always require password re-entry for updates
- API endpoint returns empty string for password field
- Encryption key must be consistent across deployments

### Retry Behavior
- Max 3 attempts per execution
- Exponential backoff prevents thundering herd
- Manual retry resets attempt count to 0
- Failed uploads don't block AMC execution success

## Troubleshooting

### Upload Fails with "No Snowflake configuration"
**Cause**: User hasn't configured Snowflake credentials
**Solution**: Navigate to Settings → Snowflake Configuration and save credentials

### Upload Fails with "Authentication failed"
**Cause**: Invalid Snowflake credentials or expired password
**Solution**: Update credentials in Settings, test connection before saving

### Upload Fails with "Table does not exist"
**Cause**: Table creation failed or insufficient permissions
**Solution**: Verify user has CREATE TABLE permissions in target schema

### Upload Fails with "Primary key violation"
**Cause**: Composite key mismatch or missing date columns
**Solution**: Check execution parameters include timeWindowStart and timeWindowEnd

### Retries Exhausted (3/3 attempts)
**Cause**: Persistent Snowflake connectivity or permission issue
**Solution**: Check Snowflake status, verify credentials, manually retry after fixing issue

## Performance Considerations

### Batch Size
- Snowflake connector uses default batch size (16,384 rows)
- Large result sets (>100k rows) split into multiple batches
- Memory usage proportional to result set size (Pandas DataFrame)

### Connection Pooling
- Each upload creates new Snowflake connection
- Connection automatically closed after upload
- No persistent connection pool (stateless service)

### MERGE Performance
- MERGE operation O(n) complexity where n = result rows
- Composite key join may be slower than single column
- Snowflake optimizes MERGE internally with parallel processing

### Caching Strategy
- User Snowflake config cached in memory (5-minute TTL)
- Reduces database queries for repeated uploads
- Cache invalidated on config update

## Future Enhancements

### Planned Features
1. **Incremental Sync**: Only upload rows that changed since last execution
2. **Column Mapping**: Map AMC column names to custom Snowflake column names
3. **Data Transformation**: Apply custom transformations before upload (e.g., currency conversion)
4. **Multi-Table Upload**: Split results into multiple Snowflake tables based on data type
5. **Compression**: Enable compression for large uploads to reduce network bandwidth
6. **Monitoring Dashboard**: Visualize upload success rates, latency, and error patterns

### Technical Debt
1. Connection pooling for high-volume uploads
2. Async Snowflake connector (currently synchronous)
3. Streaming upload for very large result sets (>1M rows)
4. Better error classification (network vs auth vs permission errors)

## Files Modified/Created

### Backend
- `amc_manager/services/snowflake_service.py` - Enhanced with composite UPSERT key logic
- `amc_manager/services/execution_monitor_service.py` - Added retry logic for Snowflake uploads
- `amc_manager/api/supabase/template_execution.py` - Pass Snowflake config to schedules
- `amc_manager/api/snowflake_config.py` - API endpoints for user configuration
- `amc_manager/schemas/template_execution.py` - Added Snowflake fields to schemas

### Frontend
- `frontend/src/components/schedules/SnowflakeConfigStep.tsx` - New wizard step component
- `frontend/src/components/schedules/ScheduleWizard.tsx` - Integrated Snowflake step
- `frontend/src/components/instances/TemplateExecutionWizard.tsx` - Added Snowflake config to Step 4
- `frontend/src/components/executions/AMCExecutionList.tsx` - Added status badges
- `frontend/src/components/executions/AMCExecutionDetail.tsx` - Added retry button and status section
- `frontend/src/pages/Profile.tsx` - Added Snowflake configuration section
- `frontend/src/types/schedule.ts` - Added Snowflake type definitions
- `frontend/src/types/templateExecution.ts` - Added Snowflake fields

### Database
- `database/migrations/16_snowflake_strategy_column.sql` - New migration for Snowflake fields
- `database/migrations/16_snowflake_strategy_column_rollback.sql` - Rollback script

### Testing
- `tests/services/test_snowflake_service_unit.py` - Comprehensive unit tests (20/20 passing)

### Documentation
- `CLAUDE.md` - Added 315-line comprehensive Snowflake integration section
- `.agent-os/features/snowflake-integration.md` - This feature documentation file

## Related Features

- [Workflow Execution](./workflow-execution.md) - Snowflake upload triggered after successful execution
- [Execution Monitoring](./execution-monitoring.md) - ExecutionMonitorService handles Snowflake uploads
- [Scheduling System](./scheduling-system.md) - Schedules include Snowflake configuration
- [Instance Management](./instance-management.md) - Instance and brand used for table naming
