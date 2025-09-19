# AMC Ad-Hoc Workflow Execution Documentation

## Overview

Amazon Marketing Cloud (AMC) supports two types of workflow executions:
1. **Saved Workflow Execution**: Executing a pre-saved workflow by its ID
2. **Ad-Hoc Execution**: Executing SQL queries directly without creating a persistent workflow

This document covers the implementation, requirements, and limitations of ad-hoc executions in the RecomAMP platform.

## Ad-Hoc vs Saved Workflows

### Ad-Hoc Execution
- SQL query is sent directly in the API request
- No workflow is persisted in AMC
- Ideal for one-time queries or testing
- Reduces workflow management overhead

### Saved Workflow Execution
- References a pre-created workflow by ID
- Workflow is stored in AMC for reuse
- Better for scheduled or repeated executions
- Allows for versioning and management

## API Implementation

### Key Requirements

1. **Mutual Exclusivity**: The AMC API requires either `sql_query` OR `workflow_id`, never both
2. **SQL Query Presence**: Ad-hoc executions must include a non-empty SQL query
3. **Date Format**: Dates must be in format `YYYY-MM-DDTHH:MM:SS` without timezone suffix ('Z')
4. **Data Lag**: AMC has a 14-day data lag - queries for recent data will return empty results

### Request Payload Structure

#### Ad-Hoc Execution Payload
```json
{
  "workflow": {
    "query": {
      "operations": [
        {
          "sql": "SELECT campaign_id, SUM(impressions) FROM sponsored_products GROUP BY campaign_id"
        }
      ]
    }
  },
  "timeWindowType": "EXPLICIT",
  "timeWindowStart": "2024-01-01T00:00:00",
  "timeWindowEnd": "2024-01-07T23:59:59",
  "timeWindowTimeZone": "America/New_York",
  "outputFormat": "CSV"
}
```

#### Saved Workflow Execution Payload
```json
{
  "workflowId": "saved-workflow-123",
  "timeWindowType": "EXPLICIT",
  "timeWindowStart": "2024-01-01T00:00:00",
  "timeWindowEnd": "2024-01-07T23:59:59",
  "timeWindowTimeZone": "America/New_York",
  "outputFormat": "CSV",
  "parameterValues": {
    "campaign_ids": ["123", "456"]
  }
}
```

## Implementation Details

### Backend Service Flow

1. **Report Execution Service** (`report_execution_service.py`)
   - Receives report execution request
   - Creates execution record in database
   - Formats SQL query and parameters
   - Calls AMC API client

2. **AMC API Client** (`amc_api_client.py`)
   - Validates mutual exclusivity of sql_query/workflow_id
   - Formats dates to AMC requirements
   - Builds appropriate payload structure
   - Sends request to AMC API

3. **Response Handling**
   - Extracts execution ID from response or Location header
   - Updates execution record with AMC execution ID
   - Polls for execution status asynchronously

### Frontend Flow

1. **Report Builder Wizard** (`RunReportModal.tsx`)
   - Collects SQL query from template or custom input
   - Sets execution parameters and date range
   - Submits to report service

2. **Report Service** (`reportService.ts`)
   - Formats request with SQL query and parameters
   - Includes time window for ad-hoc executions
   - Handles immediate execution for one-time runs

## Parameter Handling

### Date Parameters

AMC recognizes various date parameter formats:
- `startDate` / `endDate`
- `start_date` / `end_date`
- `timeWindowStart` / `timeWindowEnd`
- `beginDate` / `finishDate`

All are normalized to `timeWindowStart` and `timeWindowEnd` in the API request.

### Large Parameter Lists

For parameters with many values (e.g., 100+ campaign IDs):

1. **SQL Injection Method** (Recommended)
   - Inject VALUES clause directly into SQL
   - Avoids AMC parameter length limits
   - Example:
   ```sql
   WITH campaign_list AS (
     SELECT * FROM (VALUES ('camp1'), ('camp2'), ('camp3')) AS t(campaign_id)
   )
   SELECT * FROM sponsored_products
   WHERE campaign_id IN (SELECT campaign_id FROM campaign_list)
   ```

2. **Parameter Array Method**
   - Pass as array in parameterValues
   - Subject to AMC length limits (~1000 characters)

## Common Issues and Solutions

### Issue: Empty Results for Recent Dates
**Cause**: AMC has a 14-day data lag
**Solution**: Adjust end date to at least 14 days ago

### Issue: "No SQL query provided" Error
**Cause**: SQL query is null or empty in ad-hoc execution
**Solution**: Ensure SQL query is properly populated from template or custom input

### Issue: Date Format Errors
**Cause**: Dates include timezone suffix ('Z') or wrong format
**Solution**: Format dates as `YYYY-MM-DDTHH:MM:SS` without timezone

### Issue: Parameter Length Limit Exceeded
**Cause**: Too many campaign IDs or ASINs in parameter list
**Solution**: Use SQL injection method with VALUES clause

### Issue: 403 Forbidden on Execution
**Cause**: Using internal UUID instead of AMC instance ID
**Solution**: Use `instance_id` field, not `id` field from database

## Testing

Comprehensive test coverage is provided in `tests/test_adhoc_execution.py`:

- **Mutual Exclusivity Tests**: Verify sql_query and workflow_id cannot be used together
- **Payload Structure Tests**: Validate correct payload format for both execution types
- **Date Handling Tests**: Ensure proper date formatting and lag handling
- **Parameter Tests**: Verify parameter extraction and processing
- **Error Handling Tests**: Test graceful handling of missing SQL queries

Run tests with:
```bash
python3 -m pytest tests/test_adhoc_execution.py -v
```

## Best Practices

1. **Always validate SQL query presence** before making AMC API calls
2. **Account for data lag** when setting date ranges
3. **Use SQL injection** for large parameter lists to avoid limits
4. **Log SQL query details** for debugging and audit trails
5. **Handle both execution ID formats** (in response body or Location header)
6. **Implement retry logic** for transient AMC API failures
7. **Poll execution status** asynchronously to avoid blocking

## Limitations

1. **No Query Validation**: AMC doesn't validate SQL syntax until execution
2. **Data Lag**: 14-day minimum lag for all data
3. **Parameter Limits**: ~1000 character limit for parameter values
4. **Rate Limits**: Subject to AMC API rate limiting
5. **No Query History**: Ad-hoc queries aren't saved for reuse

## Future Enhancements

1. **SQL Validation**: Client-side SQL syntax validation before submission
2. **Query Caching**: Cache frequently used ad-hoc queries locally
3. **Smart Date Adjustment**: Automatically adjust dates for data lag
4. **Parameter Optimization**: Automatic switch between parameter methods based on size
5. **Execution Templates**: Save successful ad-hoc queries as templates

## Related Documentation

- [AMC API Reference](https://advertising.amazon.com/API/docs/en-us/amc/reporting)
- [Report Builder Implementation](./report-builder.md)
- [Workflow Management](./workflow-management.md)
- [Testing Guide](../tests/README.md)