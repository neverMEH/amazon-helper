# Amazon Marketing Cloud (AMC) Technical Specifications

> Critical documentation for understanding AMC's unique SQL dialect and API behavior
> Last Updated: 2025-09-10

## AMC SQL Dialect

### Overview
Amazon Marketing Cloud uses a modified SQL dialect with specific limitations and requirements that differ from standard SQL. Understanding these differences is critical for query development and AI integration.

### Key Differences from Standard SQL

#### 1. Date/Time Handling
```sql
-- AMC Format (REQUIRED)
WHERE event_dt BETWEEN '2025-07-01T00:00:00' AND '2025-07-31T23:59:59'

-- Standard SQL (WILL FAIL)
WHERE event_dt BETWEEN '2025-07-01' AND '2025-07-31'

-- Timezone suffix 'Z' causes empty results
-- NEVER use: '2025-07-01T00:00:00Z'
```

#### 2. Required Aggregation Rules
- ALL queries must include at least one aggregation (COUNT, SUM, AVG, etc.)
- Minimum aggregation threshold: 50 users per grouping
- Results below threshold are automatically suppressed

```sql
-- Valid AMC Query
SELECT 
    campaign_id,
    COUNT(DISTINCT user_id) as unique_users  -- Required aggregation
FROM impressions
WHERE event_dt BETWEEN '2025-07-01T00:00:00' AND '2025-07-31T23:59:59'
GROUP BY campaign_id
HAVING COUNT(DISTINCT user_id) >= 50  -- Threshold enforcement
```

#### 3. Table Access Patterns
```sql
-- AMC tables have specific prefixes
sponsored_ads_traffic       -- Traffic data
sponsored_ads_conversion    -- Conversion events
dsp_impressions             -- DSP impression data
dsp_clicks                  -- DSP click data

-- Cross-dataset joins require specific syntax
SELECT * FROM sponsored_ads_traffic
INNER JOIN dsp_impressions USING (user_id, event_dt)
```

#### 4. Parameter Limitations
- Maximum 100 campaign IDs per query
- Maximum 1000 ASINs per query
- Maximum query length: 65,536 characters
- Parameter arrays must be properly formatted

```sql
-- For large lists, use VALUES clause injection
WITH campaign_list AS (
    VALUES ('campaign1'), ('campaign2'), ...
)
SELECT * FROM sponsored_ads_traffic
WHERE campaign_id IN (SELECT * FROM campaign_list)
```

## AMC API Integration

### Instance ID Duality
```python
# CRITICAL: Two different ID systems
instance_id = "amcibersblt"           # AMC's actual instance ID (string)
internal_id = "uuid-1234-5678"        # Our database UUID

# Always use instance_id for AMC API calls
# Join tables to get entity_id from amc_accounts
```

### API Call Requirements
```python
# Every AMC API call needs:
headers = {
    "Amazon-Advertising-API-ClientId": client_id,
    "Amazon-Advertising-API-AdvertiserId": entity_id,  # From amc_accounts.account_id
    "Authorization": f"Bearer {access_token}"
}

# Endpoint format
url = f"https://advertising-api.amazon.com/amc/instances/{instance_id}/workflows"
```

### Execution Flow
```python
# 1. Create workflow
workflow_response = create_workflow(sql_query, parameters)
workflow_id = workflow_response["workflowId"]

# 2. Create execution
execution_response = create_execution(workflow_id, time_window)
execution_id = execution_response["executionId"]

# 3. Poll for status (AMC executions can take 30s - 10min)
while status not in ["SUCCEEDED", "FAILED"]:
    status = get_execution_status(execution_id)
    await asyncio.sleep(15)

# 4. Download results if successful
if status == "SUCCEEDED":
    results = download_results(execution_id)
```

### Rate Limits & Retry Logic
```python
# AMC API Rate Limits
- 10 requests per second per instance
- 100 concurrent executions per instance
- 429 responses include Retry-After header

# Retry strategy (implemented in amc_api_client_with_retry.py)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((HTTPStatusError, RequestError))
)
```

## Data Collection Patterns

### Historical Backfill Strategy
```python
# 52-week backfill approach
# Process 10 weeks concurrently, 5 collections in parallel
# Each week is independent to allow for partial failures

for week in range(52, 0, -1):
    start_date = today - timedelta(weeks=week)
    end_date = start_date + timedelta(days=6)
    
    # Create execution for this week
    execute_workflow(
        sql_query=template_query,
        parameters={
            "startDate": format_amc_date(start_date),
            "endDate": format_amc_date(end_date)
        }
    )
```

### Continuous Collection Pattern
```python
# After backfill, continue with scheduled runs
# Weekly: Run every Monday for previous week
# Daily: Run at 2 AM for T-14 days (AMC data lag)
# Monthly: Run on 1st for previous month

# Account for AMC's 14-day data processing lag
effective_date = today - timedelta(days=14)
```

## AMC Schema Structure

### Core Data Sources
```yaml
Attribution Tables:
  - sponsored_ads_attribution: Click and conversion attribution
  - dsp_attribution: Display attribution data
  - audience_attribution: Audience segment performance

Traffic Tables:
  - sponsored_ads_traffic: Search and shopping traffic
  - dsp_traffic: Display traffic events
  - video_traffic: Video ad engagement

Conversion Tables:
  - sponsored_ads_conversion: Purchase and cart events
  - subscription_conversion: Subscribe & Save conversions
  - offline_conversion: Store and offline conversions

Audience Tables:
  - audience_segment: Custom audience definitions
  - remarketing_audience: Remarketing list data
  - lookalike_audience: Lookalike modeling results
```

### Field Types & Indicators
```yaml
Dimensions (D):
  - campaign_id, asin, keyword_id
  - Can be used in GROUP BY
  - Text or ID fields

Metrics (M):
  - impressions, clicks, conversions, spend
  - Must be aggregated (SUM, AVG, COUNT)
  - Numeric fields

Restricted Fields:
  - user_id: Never exposed in results
  - email_hash: Requires special permissions
  - device_id: Aggregation only
```

## Query Optimization Techniques

### Performance Best Practices
```sql
-- 1. Use appropriate time windows (smaller = faster)
WHERE event_dt BETWEEN start AND end  -- Max 90 days recommended

-- 2. Pre-filter before joins
WITH filtered_impressions AS (
    SELECT * FROM impressions 
    WHERE campaign_id IN (...)  -- Filter first
)

-- 3. Use APPROXIMATE functions for large datasets
SELECT APPROXIMATE_COUNT_DISTINCT(user_id) as approx_users

-- 4. Leverage partitioning
WHERE event_dt >= '2025-07-01T00:00:00'  -- Partition pruning
  AND campaign_id = 'ABC123'  -- Additional filtering
```

### Common Query Patterns

#### Attribution Analysis
```sql
-- Path to conversion analysis
SELECT 
    path_position,
    touchpoint_type,
    COUNT(DISTINCT user_id) as users,
    SUM(attributed_conversions) as conversions
FROM sponsored_ads_attribution
WHERE event_dt BETWEEN @startDate AND @endDate
GROUP BY path_position, touchpoint_type
```

#### Audience Overlap
```sql
-- Find overlap between audiences
SELECT 
    COUNT(DISTINCT a.user_id) as audience_a_only,
    COUNT(DISTINCT b.user_id) as audience_b_only,
    COUNT(DISTINCT CASE WHEN a.user_id = b.user_id THEN a.user_id END) as overlap
FROM audience_segment_a a
FULL OUTER JOIN audience_segment_b b ON a.user_id = b.user_id
```

## Error Handling & Troubleshooting

### Common AMC Errors
```yaml
VALIDATION_ERROR:
  - Invalid SQL syntax
  - Missing required aggregation
  - Date format issues
  Solution: Validate query against AMC SQL rules

THRESHOLD_NOT_MET:
  - Results below 50 user minimum
  - Privacy threshold violation
  Solution: Broaden query scope or time window

QUOTA_EXCEEDED:
  - Too many concurrent executions
  - Rate limit hit
  Solution: Implement queuing and retry logic

PERMISSION_DENIED:
  - Missing instance access
  - Invalid entity_id
  Solution: Verify OAuth tokens and instance configuration
```

### Debugging Workflow
1. Check SQL syntax against AMC rules
2. Verify date formats (no 'Z' suffix)
3. Confirm instance_id and entity_id mapping
4. Review execution logs for specific errors
5. Test with smaller date ranges
6. Validate parameter substitution

## Future AI Integration Considerations

### Training Data Requirements
- Collect successful and failed queries for pattern recognition
- Document query intent and business questions
- Map natural language to AMC SQL patterns
- Build library of query templates and variations

### Context for AI Assistant
```yaml
Must Understand:
  - AMC SQL limitations and syntax
  - Parameter constraints and formatting
  - Performance optimization techniques
  - Privacy thresholds and aggregation rules
  - Date handling requirements
  - Instance/entity ID relationships

Can Help With:
  - Converting business questions to AMC SQL
  - Optimizing query performance
  - Interpreting error messages
  - Suggesting query improvements
  - Analyzing result patterns
  - Generating insight narratives
```

### Prompt Engineering for AMC
```python
# Example prompt structure for AI
prompt = f"""
You are an AMC SQL expert. Convert this business question to AMC-compatible SQL:
Question: {user_question}

Remember:
- All dates must be formatted as 'YYYY-MM-DDTHH:MM:SS' without timezone
- Include required aggregations (COUNT, SUM, etc.)
- Respect the 50-user minimum threshold
- Use appropriate AMC table names and fields

Available tables: {amc_tables}
Available fields: {amc_fields}
"""
```

## Testing & Validation

### Query Validation Checklist
- [ ] Date format correct (no 'Z' suffix)
- [ ] Required aggregation present
- [ ] GROUP BY includes all non-aggregated fields
- [ ] Time window within limits (90 days recommended)
- [ ] Parameter count within limits (100 campaigns, 1000 ASINs)
- [ ] Query length under 65,536 characters
- [ ] Instance ID correctly mapped
- [ ] Entity ID properly retrieved

### Integration Testing
```python
# Test suite for AMC integration
def test_amc_workflow():
    # 1. Test query validation
    assert validate_amc_sql(query) == True
    
    # 2. Test parameter substitution
    assert len(substitute_parameters(query, params)) < 65536
    
    # 3. Test execution flow
    execution = create_and_monitor_execution(query)
    assert execution.status in ["SUCCEEDED", "FAILED"]
    
    # 4. Test result parsing
    if execution.status == "SUCCEEDED":
        results = parse_results(execution.results)
        assert results.row_count >= 0
```

---

This documentation serves as the authoritative guide for AMC-specific implementation details and should be referenced when developing new features, debugging issues, or training AI models for the platform.