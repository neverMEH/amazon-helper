# amc_api_client.py

## Purpose
Core AMC API client for direct Amazon Marketing Cloud integration. Handles workflow execution, status monitoring, result retrieval, and comprehensive error parsing for AMC API operations.

## Dependencies
### External Dependencies
- requests: 2.31.0+ - HTTP client for AMC API calls
- csv: builtin - CSV parsing for result data
- json: builtin - JSON data handling
- logging: builtin - Application logging
- datetime: builtin - Date formatting for AMC compatibility

### Internal Dependencies
- ../config/settings: Application configuration and environment variables
- No other internal services (this is a base client)

## Exports
### Classes
- `AMCAPIClient`: Main client class for AMC API operations

### Functions
- `create_workflow_execution()`: Create AMC workflow execution (ad-hoc or saved)
- `get_execution_status()`: Poll execution status
- `get_execution_results()`: Retrieve execution results
- `create_workflow()`: Create/update AMC workflow
- `delete_workflow()`: Remove AMC workflow
- `test_execute_query()`: Ad-hoc query execution for testing
- `validate_date_format()`: Ensure AMC-compatible date formatting
- `parse_amc_error()`: Extract structured error information

### Constants
- `AMC_BASE_URL`: "https://advertising-api.amazon.com"
- `DEFAULT_MARKETPLACE`: "ATVPDKIKX0DER" (US marketplace)
- `SUPPORTED_FORMATS`: ["CSV", "JSON", "PARQUET"]

## Usage Examples
```python
# Initialize client
client = AMCAPIClient()

# Ad-hoc query execution
execution = await client.create_workflow_execution(
    instance_id="amcinstance123",
    access_token="Bearer_token",
    entity_id="ENTITY123",
    sql_query="SELECT * FROM amazon_attributed_events_by_conversion_time",
    parameter_values={"start_date": "2025-07-01T00:00:00"}
)

# Check execution status
status = await client.get_execution_status(
    instance_id="amcinstance123",
    execution_id=execution["executionId"],
    access_token="Bearer_token",
    entity_id="ENTITY123"
)

# Retrieve results
results = await client.get_execution_results(
    instance_id="amcinstance123",
    execution_id=execution["executionId"],
    access_token="Bearer_token",
    entity_id="ENTITY123"
)
```

## Relationships
### Used By
- amc_api_client_with_retry.py: Enhanced retry wrapper
- amc_execution_service.py: Execution management service
- workflow_service.py: Workflow synchronization
- All AMC-related API endpoints

### Uses
- settings.py: Configuration values (AMC_USE_REAL_API flag)
- External AMC API endpoints

## Side Effects
- Network calls to Amazon Marketing Cloud API
- Rate limiting considerations (respects AMC limits)
- Token consumption (access tokens have limited lifetime)
- File I/O for result caching (temporary CSV processing)

## Testing Considerations
### Key Scenarios
- Token expiration handling (401 responses)
- Network timeout scenarios
- Malformed SQL query responses (400 errors)
- Empty result sets (common with recent dates)
- Large result set handling (pagination)
- Date format validation

### Edge Cases
- Instance ID vs Internal UUID confusion
- Entity ID header requirements
- 14-day data lag considerations
- SQL compilation error parsing
- Missing table/column error handling

### Mocking Requirements
- Mock AMC API responses for testing
- Token validation simulation
- Network failure simulation
- Various error response formats

## Performance Notes
### Optimizations
- Connection pooling for HTTP requests
- Result streaming for large datasets
- Efficient CSV parsing
- Minimal memory footprint for result processing

### Bottlenecks
- Network latency to AMC API
- Large result set downloads
- JSON parsing for complex results
- Token refresh overhead

### Monitoring Points
- API response times
- Error rates by type
- Token refresh frequency
- Result set sizes

## Critical Implementation Patterns

### AMC ID Field Duality
```python
# CRITICAL: Use instance.instanceId for AMC API calls
# NOT instance.id (internal UUID)
def create_workflow_execution(self, instance_id: str, ...):
    # instance_id here must be AMC's actual instance ID
    url = f"{self.base_url}/amc/instances/{instance_id}/executions"
```

### Date Formatting for AMC
```python
def validate_date_format(self, date_str: str) -> str:
    """AMC requires specific format WITHOUT timezone"""
    # CORRECT: '2025-07-15T00:00:00'
    # WRONG: '2025-07-15T00:00:00Z' (causes empty results)
    if date_str.endswith('Z'):
        date_str = date_str[:-1]
    return date_str
```

### AMC Error Parsing
```python
def parse_amc_error(self, response_data: dict) -> dict:
    """Extract detailed error information from AMC responses"""
    if response.status_code == 400 and 'details' in response_data:
        # Parse SQL compilation errors
        # Extract line/column information
        # Identify missing tables/columns
        return {
            "type": "SQL_COMPILATION_ERROR",
            "message": "Table 'invalid_table' not found",
            "details": {
                "line": 5,
                "column": 25,
                "suggestion": "Check available tables in AMC schema"
            }
        }
```

### Required Headers Pattern
```python
def _get_headers(self, access_token: str, entity_id: str) -> dict:
    """Entity ID MUST be in headers, not query params"""
    return {
        'Amazon-Advertising-API-ClientId': settings.AMAZON_CLIENT_ID,
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-AdvertiserId': entity_id,  # Critical!
        'Content-Type': 'application/json'
    }
```

### 14-Day Data Lag Handling
```python
def adjust_dates_for_amc_lag(self, start_date: str, end_date: str) -> tuple:
    """Account for AMC's 14-day data processing lag"""
    end_date_obj = datetime.fromisoformat(end_date.replace('Z', ''))
    
    # Ensure end date is at least 14 days ago
    min_end_date = datetime.utcnow() - timedelta(days=14)
    if end_date_obj > min_end_date:
        logger.warning(f"Adjusting end date from {end_date} to account for AMC lag")
        end_date = min_end_date.strftime('%Y-%m-%dT%H:%M:%S')
    
    return start_date, end_date
```

## Error Handling Strategies

### AMC Response Codes
- **200**: Success with results
- **202**: Execution accepted, poll for completion
- **400**: Invalid request (SQL errors, missing parameters)
- **401**: Token expired or invalid
- **403**: Insufficient permissions or wrong entity ID
- **404**: Resource not found (instance, workflow)
- **429**: Rate limit exceeded
- **500**: Internal AMC error

### Error Classification
```python
def classify_error(self, status_code: int, response_data: dict) -> str:
    """Classify errors for appropriate handling"""
    if status_code == 400:
        if 'compile' in response_data.get('message', '').lower():
            return 'SQL_COMPILATION_ERROR'
        elif 'parameter' in response_data.get('message', '').lower():
            return 'PARAMETER_ERROR'
    elif status_code == 401:
        return 'TOKEN_EXPIRED'
    elif status_code == 403:
        return 'PERMISSION_ERROR'
    elif status_code == 404:
        return 'RESOURCE_NOT_FOUND'
    return 'UNKNOWN_ERROR'
```

## Configuration Integration

### Environment Variables
- `AMC_USE_REAL_API`: Toggle between real and mock responses
- `AMAZON_CLIENT_ID`: OAuth client identifier
- `AMC_RATE_LIMIT`: API call rate limiting
- `AMC_TIMEOUT`: Request timeout in seconds

### Mock Mode Support
```python
def create_workflow_execution(self, ...):
    if not settings.AMC_USE_REAL_API:
        return self._mock_execution_response()
    
    # Real API call
    response = requests.post(url, headers=headers, json=payload)
```

## Security Considerations

### Token Handling
- Never log access tokens
- Tokens passed as parameters, not stored in client
- Automatic token refresh handled by retry wrapper

### Data Protection
- No persistent storage of query results
- Secure transmission over HTTPS
- Entity ID validation

### Input Validation
- SQL injection prevention (parameterized queries)
- Date format validation
- Instance ID format validation

## Known Issues & Workarounds

### Token Refresh Timing
- AMC tokens expire after 1 hour
- Client doesn't handle refresh (delegated to retry wrapper)
- Background refresh service prevents expiration

### Large Result Sets
- AMC may timeout on very large queries
- Implement pagination where supported
- Consider result streaming for memory efficiency

### SQL Compatibility
- AMC SQL is Spark SQL, not standard SQL
- Some functions/syntax may not be supported
- Error messages can be cryptic

## Recent Updates

### 2025-08-14 Changes
- Enhanced error parsing for SQL compilation errors
- Improved date format validation
- Added support for parameter substitution
- Better handling of empty result sets

### Testing Improvements
- Added comprehensive mock responses
- Enhanced error simulation
- Better token expiration testing

## Integration Notes

### With AMCAPIClientWithRetry
- Base client should not handle retries
- All retry logic delegated to wrapper
- Original errors preserved for analysis

### With ExecutionService
- Client provides raw AMC responses
- Service layer handles business logic
- Status polling managed at service level

### With WorkflowService
- Workflow CRUD operations
- Synchronization between local and AMC workflows
- Conflict resolution strategies