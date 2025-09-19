# Amazon Ads AMC Workflows API Context

## Overview
Workflows in AMC are reusable query definitions that process data sources to generate reports. They can be executed ad-hoc or scheduled for periodic runs. Workflows support parameterization, custom output schemas, and SQL or operation-based queries.

## Core API Operations

### Create Workflow
Creates a new reusable workflow definition.

**Endpoint:** `POST /amc/reporting/{instanceId}/workflows`

**Required Headers:**
- `Amazon-Advertising-API-ClientId` (required)
- `Amazon-Advertising-API-AdvertiserId` (required)
- `Amazon-Advertising-API-MarketplaceId` (required)

**Content Type:** `application/vnd.amcworkflows.v1+json`

**Request Body:** `Workflow` object

**Response:** `CreateWorkflowResponse` (empty success object)

### Get Workflow
Retrieves a specific workflow definition.

**Endpoint:** `GET /amc/reporting/{instanceId}/workflows/{workflowId}`

**Response Schema:**
```typescript
interface GetWorkflowResponse {
  workflow: Workflow;
}
```

### List Workflows
Returns paginated list of all workflows in the instance.

**Endpoint:** `GET /amc/reporting/{instanceId}/workflows`

**Query Parameters:**
- `nextToken` (string): Pagination token
- `limit` (string): Max 100, defaults to 100

**Response Schema:**
```typescript
interface ListWorkflowsResponse {
  workflows: Workflow[];
  nextToken?: string;
}
```

### Update Workflow
Replaces entire workflow definition.

**Endpoint:** `PUT /amc/reporting/{instanceId}/workflows/{workflowId}`

**Request Body:** Complete `Workflow` object

**Response:** `UpdateWorkflowResponse` (empty success object)

### Delete Workflow
Removes workflow definition (cannot be undone).

**Endpoint:** `DELETE /amc/reporting/{instanceId}/workflows/{workflowId}`

**Response:** `DeleteWorkflowResponse` (empty success object)

## Workflow Object Structure

```typescript
interface Workflow {
  // Identifier
  workflowId: string;            // User-supplied unique identifier
  
  // Query definition (one required)
  sqlQuery?: string;             // SQL-based query
  query?: string[];              // Operation-based query (Base64 encoded)
  
  // Schema configuration
  inputSchema?: string;          // Default schema for unqualified table names
  outputColumns?: OutputColumn[]; // Expected output schema (max 100)
  
  // Parameters
  inputParameters?: InputParameter[]; // Workflow parameters (max 100)
  
  // Output configuration
  outputFormat?: OutputFormat;
  privacyFilteringBehavior?: 'REMOVE_ROWS' | 'REMOVE_VALUES';
  filteredMetricsDiscriminatorColumn?: string;
}
```

## Query Definition Methods

### SQL Query Method
Use `sqlQuery` for standard SQL syntax:

```sql
SELECT 
  campaign_id,
  SUM(impressions) as total_impressions,
  SUM(clicks) as total_clicks
FROM sandbox.sponsored_ads_traffic
WHERE dt >= '${start_date}'
  AND dt <= '${end_date}'
GROUP BY campaign_id
HAVING total_impressions > ${min_impressions}
```

### Operation-Based Query Method
Use `query` array for structured operations (each Base64-encoded):

```typescript
interface QueryOperation {
  type: 'SELECT' | 'JOIN' | 'AGGREGATE' | 'FILTER' | 'UNION';
  // Operation-specific properties
}
```

**Limits:**
- Maximum 100 operations per workflow
- Operations must be Base64-encoded JSON strings
- First operation must be SELECT from a data source

## Input Parameters

Define reusable parameters for workflow flexibility:

```typescript
interface InputParameter {
  name: string;                  // Variable name in SQL
  displayName?: string;          // Human-readable name
  description?: string;
  columnType: 'METRIC' | 'DIMENSION';
  dataType: DataType;
  defaultValue?: string;
}

type DataType = 'BINARY' | 'BOOLEAN' | 'BYTE' | 'CALENDAR_INTERVAL' | 
                'DATE' | 'DECIMAL' | 'DOUBLE' | 'FLOAT' | 'INTEGER' | 
                'LONG' | 'SHORT' | 'STRING' | 'TIMESTAMP';
```

**Example Parameter Definition:**
```json
{
  "inputParameters": [
    {
      "name": "start_date",
      "displayName": "Start Date",
      "description": "Analysis period start",
      "columnType": "DIMENSION",
      "dataType": "DATE",
      "defaultValue": "2024-01-01"
    },
    {
      "name": "min_impressions",
      "displayName": "Minimum Impressions",
      "columnType": "METRIC",
      "dataType": "INTEGER",
      "defaultValue": "1000"
    }
  ]
}
```

**Parameter Limits:**
- Maximum 100 parameters per workflow
- Parameters referenced as `${parameter_name}` in SQL
- Values provided at execution time via `parameterValues`

## Output Schema Validation

Define expected output columns for validation:

```typescript
interface OutputColumn {
  name: string;
  columnType: 'METRIC' | 'DIMENSION';
  dataType: DataType;
  dataTypePrecision?: number;    // For DECIMAL type
  dataTypeScale?: number;         // For DECIMAL type
  description?: string;
}
```

**Example Output Definition:**
```json
{
  "outputColumns": [
    {
      "name": "campaign_id",
      "columnType": "DIMENSION",
      "dataType": "STRING"
    },
    {
      "name": "total_spend",
      "columnType": "METRIC",
      "dataType": "DECIMAL",
      "dataTypePrecision": 10,
      "dataTypeScale": 2
    }
  ]
}
```

**Limits:**
- Maximum 100 output columns
- Workflow fails compilation if output doesn't match schema

## Output Formatting

Configure CSV output format:

```typescript
interface OutputFormat {
  separatorCharacter?: string;   // Default: ","
  quoteCharacter?: string;        // Default: "\""
  escapeCharacter?: string;       // Default: "\\"
}
```

## Privacy and Filtering

Control how sensitive data is handled:

### Privacy Filtering Behavior
- `REMOVE_ROWS`: Entire row removed if privacy threshold not met
- `REMOVE_VALUES`: Only sensitive values removed, row retained

### Filtered Metrics Discriminator
When using `REMOVE_VALUES`:
```json
{
  "privacyFilteringBehavior": "REMOVE_VALUES",
  "filteredMetricsDiscriminatorColumn": "is_filtered"
}
```
Adds boolean column indicating filtered rows.

## Workflow Size Limits

### Structural Limits
- **Query operations**: Maximum 100
- **Input parameters**: Maximum 100
- **Output columns**: Maximum 100
- **Data source columns**: Maximum 500 per source

### Execution Limits
- **Timeout**: 900-86400 seconds (configurable)
- **Memory**: Instance-dependent
- **Result size**: S3 storage limits apply

## Common Workflow Patterns

### 1. Parameterized Date Range Report
```json
{
  "workflowId": "daily-performance-report",
  "sqlQuery": "SELECT date, SUM(impressions), SUM(clicks) FROM sponsored_ads_traffic WHERE date BETWEEN '${start_date}' AND '${end_date}' GROUP BY date",
  "inputParameters": [
    {
      "name": "start_date",
      "dataType": "DATE",
      "columnType": "DIMENSION"
    },
    {
      "name": "end_date",
      "dataType": "DATE",
      "columnType": "DIMENSION"
    }
  ]
}
```

### 2. Multi-Source Join Analysis
```json
{
  "workflowId": "conversion-path-analysis",
  "inputSchema": "sandbox",
  "sqlQuery": "WITH impressions AS (SELECT...), conversions AS (SELECT...) SELECT ... FROM impressions JOIN conversions ...",
  "outputColumns": [
    {"name": "touchpoint_count", "dataType": "INTEGER", "columnType": "METRIC"},
    {"name": "conversion_rate", "dataType": "DOUBLE", "columnType": "METRIC"}
  ]
}
```

### 3. Aggregation with Privacy Controls
```json
{
  "workflowId": "audience-insights",
  "sqlQuery": "SELECT audience_segment, COUNT(DISTINCT user_id) FROM ...",
  "privacyFilteringBehavior": "REMOVE_ROWS",
  "outputColumns": [
    {"name": "audience_segment", "dataType": "STRING", "columnType": "DIMENSION"},
    {"name": "unique_users", "dataType": "LONG", "columnType": "METRIC"}
  ]
}
```

## Workflow Management Best Practices

### Naming Conventions
- Use descriptive, lowercase IDs with hyphens
- Include version numbers for iterations
- Prefix with team/purpose identifiers

```
team-marketing-campaign-performance-v2
daily-sales-attribution-report
test-audience-overlap-analysis
```

### Version Control
Since updates replace entire workflows:
1. Clone workflow with new ID for major changes
2. Maintain changelog in description
3. Test new versions before deleting old ones
4. Consider external version control for SQL

### Parameter Design
- Provide sensible defaults
- Use descriptive parameter names
- Validate parameter ranges in SQL
- Document expected formats

### Error Handling
- Validate data source availability
- Handle NULL values explicitly
- Use COALESCE for missing data
- Test edge cases with parameters

## Integration Patterns

### Workflow Template System
```python
class WorkflowTemplate:
    def __init__(self, base_sql, parameters):
        self.base_sql = base_sql
        self.parameters = parameters
    
    def create_workflow(self, workflow_id, customizations):
        return {
            "workflowId": workflow_id,
            "sqlQuery": self.apply_customizations(customizations),
            "inputParameters": self.parameters
        }
```

### Dynamic Workflow Generation
```python
def generate_cohort_workflow(cohort_definition):
    sql = f"""
    WITH cohort AS ({cohort_definition})
    SELECT ... FROM cohort ...
    """
    return {
        "workflowId": f"cohort-{hash(cohort_definition)}",
        "sqlQuery": sql
    }
```

### Workflow Migration
```python
async def migrate_workflows(old_instance, new_instance):
    workflows = await list_workflows(old_instance)
    for workflow in workflows:
        await create_workflow(new_instance, workflow)
```

## Profile Scope Considerations

- Workflows are instance-specific
- Cannot share workflows across instances
- Marketplace access determined at execution time
- Consider multi-marketplace workflow design

## SQL Query Guidelines

### Supported SQL Features
- Standard SELECT, JOIN, WHERE, GROUP BY, HAVING
- Common Table Expressions (WITH clauses)
- Window functions
- CASE statements
- Subqueries
- UNION/INTERSECT operations

### AMC-Specific Considerations
- Use qualified table names: `schema.table`
- Time columns often named `dt` or `date`
- User counts subject to privacy thresholds
- Some operations require aggregation

### Performance Optimization
- Filter early in query execution
- Use appropriate JOIN types
- Leverage indexes on common columns
- Avoid SELECT * on wide tables
- Consider result set size limits

## Troubleshooting

### Common Issues
1. **Workflow compilation fails**: Check SQL syntax and table names
2. **Parameter substitution errors**: Ensure parameter names match
3. **Output schema mismatch**: Verify column names and types
4. **Timeout errors**: Optimize query or increase timeout
5. **Privacy threshold failures**: Adjust aggregation levels

### Validation Strategy
1. Create workflow with dry run execution
2. Test with small date ranges
3. Verify output schema matches expectations
4. Test parameter edge cases
5. Monitor execution times

## Notes for Implementation

- Workflow IDs must be unique within instance
- Deleted workflows cannot be recovered
- Updates are full replacements, not patches
- SQL injection prevention handled by parameter substitution
- Consider implementing workflow backup system
- Test workflows thoroughly before scheduling
- Monitor workflow execution patterns for optimization