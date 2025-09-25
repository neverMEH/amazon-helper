# Snowflake Integration Implementation

## Overview

This document outlines the implementation of Snowflake data warehouse integration for the Amazon Helper report builder. The integration allows users to store execution results in both Supabase (existing) and Snowflake (new) simultaneously.

## Architecture

### Data Flow

1. **User Configuration**: Users configure their Snowflake connection in Settings
2. **Report Execution**: When creating a report, users can enable Snowflake storage via a checkbox
3. **Dual Storage**: Results are stored in both Supabase and Snowflake
4. **Monitoring**: Execution status includes Snowflake upload progress

### Components

#### Backend Services

1. **SnowflakeService** (`amc_manager/services/snowflake_service.py`)
   - Manages Snowflake connections and configurations
   - Handles data upload to Snowflake tables
   - Supports both password and key-pair authentication
   - Creates tables automatically if they don't exist

2. **ExecutionMonitorService** (updated)
   - Monitors AMC executions
   - Triggers Snowflake upload when execution completes
   - Updates execution status with Snowflake progress

3. **ReportExecutionService** (updated)
   - Accepts Snowflake configuration parameters
   - Stores Snowflake settings in execution records

#### Database Schema

**New Tables:**
- `snowflake_configurations`: User Snowflake connection settings
- Updated `workflow_executions`: Added Snowflake-related fields

**New Fields in `workflow_executions`:**
- `snowflake_enabled`: Boolean flag
- `snowflake_table_name`: Custom table name
- `snowflake_schema_name`: Custom schema name
- `snowflake_status`: Upload status (pending, uploading, completed, failed)
- `snowflake_error_message`: Error details if upload fails
- `snowflake_uploaded_at`: Upload timestamp
- `snowflake_row_count`: Number of rows uploaded

#### Frontend Components

1. **RunReportModal** (updated)
   - Added Snowflake toggle checkbox
   - Optional table/schema name inputs
   - Shows Snowflake status in review step

2. **Types** (updated)
   - Added Snowflake configuration interfaces
   - Extended `CreateReportRequest` with Snowflake options

#### API Endpoints

**New Snowflake API** (`/api/snowflake/`):
- `POST /config`: Create Snowflake configuration
- `GET /config`: Get user's Snowflake configuration
- `PUT /config`: Update Snowflake configuration
- `DELETE /config`: Delete Snowflake configuration
- `POST /test`: Test Snowflake connection
- `GET /tables`: List tables in Snowflake

## Implementation Details

### Authentication Methods

The integration supports two authentication methods:

1. **Password Authentication**
   ```python
   conn_params = {
       'account': account_identifier,
       'user': username,
       'password': password,
       'warehouse': warehouse,
       'database': database,
       'schema': schema
   }
   ```

2. **Key-Pair Authentication**
   ```python
   conn_params = {
       'account': account_identifier,
       'private_key': private_key,
       'warehouse': warehouse,
       'database': database,
       'schema': schema
   }
   ```

### Data Upload Process

1. **Connection**: Establish connection using user's stored credentials
2. **Table Creation**: Create table if it doesn't exist with proper schema
3. **Data Preparation**: Convert results to pandas DataFrame
4. **Metadata Addition**: Add execution metadata (execution_id, uploaded_at, user_id)
5. **Bulk Upload**: Use Snowflake's COPY INTO for efficient bulk loading
6. **Status Update**: Update execution record with upload status

### Error Handling

- **Connection Failures**: Graceful fallback, execution continues without Snowflake upload
- **Upload Failures**: Detailed error messages stored in execution record
- **Authentication Issues**: Clear error messages for configuration problems

### Security Considerations

- **Credential Encryption**: Passwords and private keys are encrypted before storage
- **Row Level Security**: Users can only access their own configurations
- **Connection Validation**: Test connections before saving configurations

## Usage Instructions

### For Users

1. **Configure Snowflake Connection**:
   - Go to Settings → Snowflake Configuration
   - Enter your Snowflake account details
   - Test the connection
   - Save the configuration

2. **Enable Snowflake Storage**:
   - When creating a report, check "Upload to Snowflake Data Warehouse"
   - Optionally specify custom table/schema names
   - Results will be stored in both Supabase and Snowflake

3. **Monitor Upload Status**:
   - Check execution details for Snowflake upload status
   - View any error messages if upload fails

### For Developers

1. **Database Migration**:
   ```sql
   -- Run the migration script
   \i database/supabase/08_snowflake_integration.sql
   ```

2. **Install Dependencies**:
   ```bash
   pip install snowflake-connector-python pandas
   ```

3. **Environment Variables**:
   - No additional environment variables required
   - Snowflake credentials are stored in database

## Configuration Examples

### Snowflake Configuration

```json
{
  "account_identifier": "myaccount.snowflakecomputing.com",
  "warehouse": "COMPUTE_WH",
  "database": "ANALYTICS_DB",
  "schema": "REPORTS",
  "role": "ANALYST_ROLE",
  "username": "myuser",
  "password": "mypassword"
}
```

### Report Creation with Snowflake

```json
{
  "name": "Campaign Performance Report",
  "template_id": "template_123",
  "instance_id": "instance_456",
  "parameters": {
    "campaign_ids": ["123", "456"],
    "date_range": "30d"
  },
  "execution_type": "once",
  "snowflake_enabled": true,
  "snowflake_table_name": "campaign_performance",
  "snowflake_schema_name": "marketing"
}
```

## Monitoring and Troubleshooting

### Execution Status Values

- `pending`: Snowflake upload not started
- `uploading`: Currently uploading to Snowflake
- `completed`: Successfully uploaded to Snowflake
- `failed`: Upload failed (check error message)

### Common Issues

1. **Connection Timeout**: Check network connectivity and firewall settings
2. **Authentication Failed**: Verify credentials and account identifier
3. **Permission Denied**: Ensure user has CREATE TABLE and INSERT permissions
4. **Table Already Exists**: System handles this automatically

### Logging

All Snowflake operations are logged with appropriate detail levels:
- INFO: Successful operations
- WARNING: Non-critical issues
- ERROR: Failed operations with error details

## Future Enhancements

1. **Incremental Updates**: Support for updating existing Snowflake tables
2. **Data Transformation**: Pre-upload data processing and transformation
3. **Partitioning**: Automatic table partitioning based on date ranges
4. **Compression**: Data compression for large datasets
5. **Real-time Sync**: Real-time data synchronization options

## Testing

### Unit Tests

```python
def test_snowflake_connection():
    config = {
        'account_identifier': 'test.snowflakecomputing.com',
        'warehouse': 'TEST_WH',
        'database': 'TEST_DB',
        'schema': 'TEST_SCHEMA',
        'username': 'testuser',
        'password': 'testpass'
    }
    
    result = snowflake_service.test_connection(config)
    assert result['success'] == True
```

### Integration Tests

1. Test end-to-end report execution with Snowflake enabled
2. Verify data integrity between Supabase and Snowflake
3. Test error handling scenarios

## Performance Considerations

- **Bulk Loading**: Uses Snowflake's COPY INTO for efficient data transfer
- **Connection Pooling**: Reuses connections when possible
- **Async Processing**: Snowflake upload doesn't block execution completion
- **Memory Management**: Processes large datasets in chunks if needed

## Cost Optimization

- **Warehouse Sizing**: Users can choose appropriate warehouse size
- **Data Retention**: Implement data retention policies
- **Compression**: Use Snowflake's automatic compression
- **Query Optimization**: Optimize table schemas for common query patterns
