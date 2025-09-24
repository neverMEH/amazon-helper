# Query Library Accepted Parameters

This document provides a comprehensive list of all parameters accepted by the RecomAMP Query Library system for AMC (Amazon Marketing Cloud) SQL queries.

## Parameter Syntax Formats

The system accepts three different parameter placeholder formats:

1. **Mustache Format**: `{{parameter_name}}`
2. **Colon Format**: `:parameter_name`
3. **Dollar Format**: `$parameter_name`

## Core Parameter Categories

### 1. Date Parameters

Date parameters are used for time-based filtering and analysis. AMC requires dates without timezone suffixes.

| Parameter Name | Type | Format | Description |
|---------------|------|--------|-------------|
| `start_date` | string | `YYYY-MM-DDTHH:MM:SS` | Start date for analysis period |
| `end_date` | string | `YYYY-MM-DDTHH:MM:SS` | End date for analysis period |
| `date_from` | string | `YYYY-MM-DDTHH:MM:SS` | Alternative start date parameter |
| `date_to` | string | `YYYY-MM-DDTHH:MM:SS` | Alternative end date parameter |
| `begin_date` | string | `YYYY-MM-DDTHH:MM:SS` | Query begin date |
| `finish_date` | string | `YYYY-MM-DDTHH:MM:SS` | Query finish date |
| `from_date` | string | `YYYY-MM-DDTHH:MM:SS` | From date for range |
| `to_date` | string | `YYYY-MM-DDTHH:MM:SS` | To date for range |
| `timestamp` | string | `YYYY-MM-DDTHH:MM:SS` | Single timestamp parameter |
| `date_start` | string | `YYYY-MM-DDTHH:MM:SS` | Start of date range |
| `date_end` | string | `YYYY-MM-DDTHH:MM:SS` | End of date range |

**Format Requirements:**
- Must NOT include 'Z' timezone suffix
- Example: `2025-07-15T00:00:00` ✓
- Incorrect: `2025-07-15T00:00:00Z` ✗

### 2. ASIN Parameters

ASIN (Amazon Standard Identification Number) parameters for product filtering.

| Parameter Name | Type | Description |
|---------------|------|-------------|
| `asin` | string/array | Single or multiple ASINs |
| `product_asin` | string/array | Product ASIN identifier |
| `parent_asin` | string/array | Parent ASIN for variations |
| `child_asin` | string/array | Child ASIN for variations |
| `asins` | array | Multiple ASINs list |
| `asin_list` | array | List of ASINs to filter |
| `tracked_asins` | array | ASINs being tracked |
| `target_asins` | array | Target ASINs for analysis |
| `promoted_asins` | array | ASINs in promotions |
| `competitor_asins` | array | Competitor product ASINs |
| `purchased_asins` | array | ASINs that were purchased |
| `viewed_asins` | array | ASINs that were viewed |

**Format for Arrays:**
- SQL IN clause: `('B00ABC123','B00DEF456')`
- VALUES clause: `('B00ABC123'), ('B00DEF456')`

### 3. Campaign Parameters

Campaign-related parameters for filtering advertising data.

| Parameter Name | Type | Description |
|---------------|------|-------------|
| `campaign` | string/array | Campaign identifier or name |
| `campaign_id` | string/array | Campaign ID(s) |
| `campaign_name` | string/array | Campaign name(s) |
| `campaigns` | array | Multiple campaigns |
| `campaign_ids` | array | List of campaign IDs |
| `campaign_list` | array | List of campaigns |
| `campaign_brand` | string | Brand name for LIKE pattern matching |

**Pattern Matching:**
- When used with LIKE clause, wildcards are automatically added
- Example: `campaign_brand` → `'%BrandName%'`

### 4. Brand Parameters

Brand-specific parameters for multi-brand analysis.

| Parameter Name | Type | Description |
|---------------|------|-------------|
| `brand` | string | Brand name |
| `brand_tag` | string | Brand tag identifier |
| `brand_name` | string | Full brand name |
| `brand_pattern` | string | Pattern for LIKE matching |

### 5. Advertising Type Parameters

Parameters for filtering by advertising product types.

| Parameter Name | Type | Description |
|---------------|------|-------------|
| `ad_product_type` | string | AMC ad product type |
| `product_type` | string | Product type filter |
| `advertiser_type` | string | Type of advertiser |

**Valid Values for `ad_product_type`:**
- `sponsored_products`
- `sponsored_brands`
- `sponsored_display`
- `dsp`

### 6. Numeric Parameters

General numeric parameters for thresholds and limits.

| Parameter Name | Type | Description |
|---------------|------|-------------|
| `days` | integer | Number of days (e.g., for INTERVAL) |
| `lookback_days` | integer | Days to look back from current date |
| `threshold` | number | Numeric threshold value |
| `limit` | integer | Result limit |
| `min_value` | number | Minimum value filter |
| `max_value` | number | Maximum value filter |

### 7. Pattern Parameters

Parameters specifically designed for pattern matching with LIKE.

| Parameter Name | Type | Description |
|---------------|------|-------------|
| `pattern` | string | Generic pattern parameter |
| `like_pattern` | string | LIKE clause pattern |
| `search_pattern` | string | Search pattern |

**Automatic Wildcard Addition:**
- System automatically adds `%` wildcards when parameter is used with LIKE
- Template: `LIKE {{pattern}}` → Result: `LIKE '%value%'`
- Template: `LIKE '%{{pattern}}%'` → Wildcards in template, not duplicated

## Parameter Processing Rules

### 1. Array Handling

Arrays can be processed in two ways:

**IN Clause Format** (for lists < 1000 items):
```sql
WHERE campaign_id IN {{campaign_ids}}
-- Becomes: WHERE campaign_id IN ('camp1','camp2','camp3')
```

**VALUES Clause Format** (for large lists or CTEs):
```sql
WITH campaign_filter AS (
    VALUES {{campaign_ids}}
)
-- Becomes:
WITH campaign_filter AS (
    VALUES ('camp1'), ('camp2'), ('camp3')
)
```

### 2. String Escaping

- Single quotes in values are escaped: `'` → `''`
- Pre-quoted values are detected and handled appropriately
- SQL injection protection checks for dangerous keywords

### 3. NULL Handling

- `null` or `None` values → `NULL` in SQL
- Empty arrays → Special handling with `WHERE FALSE`

### 4. Boolean Parameters

- `true` → `TRUE`
- `false` → `FALSE`

## AMC-Specific Limits

| Limit | Value | Description |
|-------|-------|-------------|
| Max IN clause items | 1,000 | Maximum items in a single IN clause |
| Max query length | 100 KB | Maximum SQL query size (102,400 bytes) |
| Date format | No timezone | Dates must not include 'Z' suffix |

## Parameter Validation

### Required vs Optional

- Required parameters must be provided or query fails
- Optional parameters can be omitted
- System validates all required parameters before execution

### Type Checking

The system performs automatic type detection and validation:
- Dates must be valid ISO format
- Numbers must be numeric
- Arrays must be proper lists

### Security Validation

Dangerous SQL keywords are blocked:
- `DROP`, `DELETE` (without WHERE)
- `INSERT INTO`, `UPDATE` (without WHERE)
- `ALTER`, `CREATE`, `TRUNCATE`
- `EXEC`, `EXECUTE`, `GRANT`, `REVOKE`

## Default Values

When parameters are not provided, the system may apply defaults:

| Parameter Type | Default Value |
|---------------|--------------|
| ASIN | `['B00DUMMY01']` |
| Campaign | `['dummy_campaign']` |
| Brand | `['dummy_brand']` |
| Start Date | 30 days ago |
| End Date | 15 days ago |
| ad_product_type | `['sponsored_products']` |

## Usage Examples

### Basic Parameter Substitution
```sql
SELECT * FROM campaigns
WHERE campaign_id = {{campaign_id}}
  AND date BETWEEN {{start_date}} AND {{end_date}}
```

### Array Parameter with IN Clause
```sql
SELECT * FROM sponsored_ads_traffic
WHERE asin IN {{tracked_asins}}
  AND campaign_id IN {{campaign_ids}}
```

### LIKE Pattern Matching
```sql
SELECT * FROM campaigns
WHERE campaign_name LIKE {{campaign_brand}}
-- Automatically becomes: LIKE '%BrandName%'
```

### VALUES Clause for Large Lists
```sql
WITH asin_filter AS (
    VALUES {{tracked_asins}}
)
SELECT * FROM sponsored_ads_traffic t
JOIN asin_filter f ON t.asin = f.column1
```

### Date Range with Lookback
```sql
SELECT * FROM amazon_attributed_events_by_traffic_time
WHERE event_dt >= {{start_date}}::DATE - INTERVAL '{{lookback_days}}' DAY
  AND event_dt <= {{end_date}}
```

## Frontend Integration

The frontend automatically detects parameters in SQL queries and provides appropriate UI components:

- **Date parameters**: Date picker components
- **ASIN parameters**: ASIN selector with search
- **Campaign parameters**: Campaign multi-select with brand filtering
- **Pattern parameters**: Text input with wildcard help text
- **Unknown parameters**: Generic text input

## Parameter Storage

Parameters are stored in the database as JSONB:

```json
{
  "start_date": "2025-01-01T00:00:00",
  "end_date": "2025-01-31T23:59:59",
  "campaign_ids": ["camp1", "camp2"],
  "tracked_asins": ["B00ABC123", "B00DEF456"],
  "brand": "MyBrand"
}
```

## Best Practices

1. **Use descriptive parameter names** that clearly indicate their purpose
2. **Prefer arrays over single values** for flexibility (users can still select one item)
3. **Use consistent naming** across queries (e.g., always `start_date` not `begin_date`)
4. **Document parameter requirements** in query descriptions
5. **Validate parameter limits** before sending to AMC API
6. **Handle empty parameters gracefully** with appropriate SQL logic
7. **Use VALUES clause for large lists** to avoid query length limits

## Troubleshooting

### Common Issues

1. **"Missing required parameters"**: Ensure all `{{param}}` placeholders have values
2. **"Query too long"**: Use VALUES clause or reduce parameter list size
3. **"Invalid date format"**: Remove 'Z' suffix from dates
4. **"Dangerous SQL detected"**: Check for unintended SQL keywords in values
5. **"Empty results"**: Verify date ranges account for AMC's 14-day data lag

### Debug Mode

Enable debug logging to see parameter processing:
```python
# Backend logs show:
# - Required parameters detected
# - Parameter substitution process
# - Final SQL query
# - AMC API response
```