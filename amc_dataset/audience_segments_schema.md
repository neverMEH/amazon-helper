# Amazon Audience Segment Membership Tables Schema

## Overview

⚠️ **Important Performance Warning**: Workflows that use these tables will time out when run over extended periods of time.

Amazon audience segment membership is presented across multiple data views with two distinct dataset types:
- **Default data views** (DIMENSION type): Most recent user-to-segment associations, refreshed daily
- **Historical snapshots** (FACT type): User-to-segment associations recorded on the first Thursday of each calendar month

## Data Organization

### Regional Structure
Audience segment membership is organized by three regions:
- **AMER**: Americas region
- **EU**: Europe region  
- **APAC**: Asia-Pacific region

### Category Structure
Amazon audience subcategories include:
- **Lifestyle**: Lifestyle-based segments
- **Life event**: Life event-based segments (noted but not listed in available tables)
- **In-market**: In-market purchase intent segments
- **Interests**: Interest-based segments (noted but not listed in available tables)

## Available Tables

### Current Membership Tables (DIMENSION Type)
- `audience_segments_amer_inmarket`
- `audience_segments_amer_lifestyle`
- `audience_segments_apac_inmarket`
- `audience_segments_apac_lifestyle`
- `audience_segments_eu_inmarket`
- `audience_segments_eu_lifestyle`

### Historical Snapshot Tables (FACT Type)
- `audience_segments_amer_inmarket_snapshot`
- `audience_segments_amer_lifestyle_snapshot`
- `audience_segments_apac_inmarket_snapshot`
- `audience_segments_apac_lifestyle_snapshot`
- `audience_segments_eu_inmarket_snapshot`
- `audience_segments_eu_lifestyle_snapshot`

### Metadata Table
- `segment_metadata`

## Schema: audience_segments_<region>_<category>

Records of all active user-to-segment associations. Each user-to-segment association appears as a distinct row.

| Field Category | Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|----------------|------|-----------|-------------------|-------------|----------------------|
| Audience Segment Membership | no_3p_trackers | BOOLEAN | Dimension | Is this item not allowed to use 3P tracking? | NONE |
| Audience Segment Membership | segment_id | INTEGER | Dimension | Identification code for the segment. Not globally unique, but unique per segment_marketplace_id. | LOW |
| Audience Segment Membership | segment_marketplace_id | LONG | Dimension | Marketplace the segment belongs to; segments can belong to multiple marketplaces. | LOW |
| Audience Segment Membership | segment_name | STRING | Dimension | Name of the segment the user_id is tagged to. | LOW |
| Audience Segment Membership | user_id | STRING | Dimension | User ID of the customer. | VERY_HIGH |
| Audience Segment Membership | user_id_type | STRING | Dimension | Type of user ID. | LOW |

### Additional Fields for Snapshot Tables
| Field Category | Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|----------------|------|-----------|-------------------|-------------|----------------------|
| Audience Segment Membership | snapshot_datetime | DATE | Dimension | The date when snapshot was taken (first Thursday of calendar month). | LOW |

## Schema: segment_metadata

Metadata that describes the segment_id AND segment_marketplace_id from the audience segment membership tables.

**Recommendation**: When joining segment_metadata with audience_segments tables, use a SQL double join on segment_id AND segment_marketplace_id.

| Field Category | Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|----------------|------|-----------|-------------------|-------------|----------------------|
| Audience Segment Metadata | category_level_1 | STRING | Dimension | Top level of the audience segment taxonomy. | LOW |
| Audience Segment Metadata | category_level_2 | STRING | Dimension | Second level of the audience segment taxonomy. | LOW |
| Audience Segment Metadata | category_path | STRING | Dimension | Full path of the audience segment taxonomy. | LOW |
| Audience Segment Metadata | no_3p_trackers | BOOLEAN | Dimension | Is this item not allowed to use 3P tracking? | NONE |
| Audience Segment Metadata | segment_description | STRING | Dimension | Description of the segment. | LOW |
| Audience Segment Metadata | segment_id | INTEGER | Dimension | Identification code for the segment. | LOW |
| Audience Segment Metadata | segment_marketplace_id | LONG | Dimension | The marketplace the segment belongs to; segments can belong to multiple marketplaces. | LOW |
| Audience Segment Metadata | segment_name | STRING | Dimension | Name of the segment. | LOW |

## AMC Best Practices and Recommendations

### Critical Query Restrictions

1. **Single Table Per Query**: Never query more than 1 audience_segments_<region>_<category> table within a single SQL query.

2. **Single Region Per Query**: Never query audience segment membership tables from multiple regions (AMER/EU/APAC) within a single SQL query.

3. **Mandatory Marketplace Filtering**: Include SQL filtering using segment_marketplace_id for all queries. This filtering should be informed by the advertiser_country value.

4. **Segment ID Filtering**: Include SQL filtering using segment_id whenever the analysis scope can be refined to a subset of segments.

### Historical Snapshot Best Practices

5. **Date Range Limitation**: When querying historical snapshot tables, limit your analysis date-range and segment-scope through SQL filtering.

6. **First Thursday Requirement**: Ensure query date range includes the first Thursday of the calendar month for your analysis.

7. **Single Snapshot Per Analysis**: When joining snapshot tables with traffic or conversion datasets, restrict analysis to 1 historical snapshot per SQL query.

## Common Query Patterns

### Basic Segment Membership Analysis
```sql
-- Analyze current segment membership for AMER lifestyle segments
SELECT 
    s.segment_name,
    s.segment_description,
    COUNT(DISTINCT a.user_id) as member_count
FROM audience_segments_amer_lifestyle a
JOIN segment_metadata s 
    ON a.segment_id = s.segment_id 
    AND a.segment_marketplace_id = s.segment_marketplace_id
WHERE a.segment_marketplace_id = 1  -- Filter by marketplace
GROUP BY s.segment_name, s.segment_description
ORDER BY member_count DESC;
```

### Segment Overlap Analysis
```sql
-- Analyze overlap between specific segments (single region only)
WITH segment_users AS (
    SELECT 
        a.user_id,
        a.segment_id,
        s.segment_name
    FROM audience_segments_amer_inmarket a
    JOIN segment_metadata s 
        ON a.segment_id = s.segment_id 
        AND a.segment_marketplace_id = s.segment_marketplace_id
    WHERE a.segment_marketplace_id = 1
        AND a.segment_id IN (12345, 67890)  -- Specific segments
)
SELECT 
    COUNT(DISTINCT CASE WHEN segment_id = 12345 THEN user_id END) as segment_1_users,
    COUNT(DISTINCT CASE WHEN segment_id = 67890 THEN user_id END) as segment_2_users,
    COUNT(DISTINCT user_id) as total_unique_users
FROM segment_users;
```

### Historical Trend Analysis
```sql
-- Historical segment growth using snapshot data
SELECT 
    a.snapshot_datetime,
    s.segment_name,
    COUNT(DISTINCT a.user_id) as member_count
FROM audience_segments_eu_lifestyle_snapshot a
JOIN segment_metadata s 
    ON a.segment_id = s.segment_id 
    AND a.segment_marketplace_id = s.segment_marketplace_id
WHERE a.segment_marketplace_id = 3  -- EU marketplace
    AND a.segment_id = 98765  -- Specific segment
    AND a.snapshot_datetime >= '2024-01-01'
    AND a.snapshot_datetime <= '2024-12-31'
GROUP BY a.snapshot_datetime, s.segment_name
ORDER BY a.snapshot_datetime;
```

### Campaign Performance by Segment
```sql
-- Join segment membership with attributed conversions
-- (Example using single snapshot for performance)
SELECT 
    s.category_level_1,
    s.segment_name,
    COUNT(DISTINCT seg.user_id) as segment_members,
    SUM(conv.total_purchases) as attributed_purchases,
    SUM(conv.total_product_sales) as attributed_sales
FROM audience_segments_amer_inmarket seg
JOIN segment_metadata s 
    ON seg.segment_id = s.segment_id 
    AND seg.segment_marketplace_id = s.segment_marketplace_id
LEFT JOIN amazon_attributed_events_by_conversion_time conv
    ON seg.user_id = conv.user_id
WHERE seg.segment_marketplace_id = 1
    AND seg.segment_id IN (11111, 22222, 33333)  -- Specific segments
    AND conv.conversion_event_date >= '2025-01-01'
    AND conv.conversion_event_date <= '2025-01-31'
GROUP BY s.category_level_1, s.segment_name;
```

## Segment Taxonomy Structure

### Category Hierarchy
- **category_level_1**: Top-level categorization (e.g., "Lifestyle", "In-Market")
- **category_level_2**: Sub-categorization (e.g., specific lifestyle categories)
- **category_path**: Full hierarchical path for detailed classification

### Example Category Structure
```sql
-- Explore segment taxonomy
SELECT 
    category_level_1,
    category_level_2,
    category_path,
    COUNT(DISTINCT segment_id) as segment_count
FROM segment_metadata
WHERE segment_marketplace_id = 1  -- US marketplace
GROUP BY category_level_1, category_level_2, category_path
ORDER BY category_level_1, category_level_2;
```

## Performance Optimization Strategies

### Query Design
- **Pre-filter aggressively**: Use marketplace and segment ID filters early
- **Limit scope**: Focus on specific segments rather than broad analysis
- **Single table focus**: Never mix regions or categories in one query
- **Avoid large date ranges**: Especially for historical snapshots

### Snapshot Table Usage
- **Monthly analysis**: Align analysis periods with first Thursday snapshots
- **Point-in-time comparisons**: Use specific snapshot dates for consistency
- **Trend analysis**: Limit to essential time periods to avoid timeouts

### Join Optimization
```sql
-- Efficient join pattern
SELECT ...
FROM audience_segments_amer_lifestyle a
JOIN segment_metadata s 
    ON a.segment_id = s.segment_id 
    AND a.segment_marketplace_id = s.segment_marketplace_id
WHERE a.segment_marketplace_id = 1  -- Filter early
    AND a.segment_id IN (1001, 1002, 1003)  -- Specific segments
```

## Regional Marketplace Mapping

### Common Marketplace IDs
- **1**: United States (AMER)
- **3**: United Kingdom (EU)  
- **4**: Germany (EU)
- **5**: France (EU)
- **6**: Japan (APAC)
- **35**: Australia (APAC)

*Note: Always verify marketplace IDs for your specific analysis needs*

## Data Freshness and Updates

### Current Tables (DIMENSION Type)
- **Refresh frequency**: Daily
- **Data recency**: Most recent user-to-segment associations
- **Use case**: Current state analysis, real-time targeting

### Snapshot Tables (FACT Type)
- **Refresh frequency**: Monthly (first Thursday)
- **Data recency**: Point-in-time historical records
- **Use case**: Trend analysis, historical comparisons, longitudinal studies

## Common Pitfalls and Solutions

### Performance Issues
❌ **Don't**: Query multiple regions simultaneously
✅ **Do**: Focus on single region per query

❌ **Don't**: Use broad date ranges on snapshot tables
✅ **Do**: Limit to essential time periods with specific filtering

❌ **Don't**: Join multiple snapshot periods in one query
✅ **Do**: Analyze one snapshot period at a time

### Data Quality
❌ **Don't**: Assume segment_id is globally unique
✅ **Do**: Always join on both segment_id AND segment_marketplace_id

❌ **Don't**: Ignore marketplace filtering
✅ **Do**: Always filter by relevant segment_marketplace_id

### Query Design
❌ **Don't**: Mix current and snapshot tables
✅ **Do**: Choose appropriate table type for your analysis needs

❌ **Don't**: Query without segment metadata
✅ **Do**: Join with segment_metadata for meaningful segment names and descriptions

## Aggregation Threshold Notes

- **NONE**: No aggregation threshold restrictions
- **LOW**: Standard low threshold applies
- **VERY_HIGH**: Very high threshold - cannot be included in final SELECT statements but can be used in CTEs for aggregation

## Use Case Examples

### Audience Size Analysis
Perfect for understanding segment penetration and overlap across your target markets.

### Campaign Targeting Optimization
Identify high-performing segments for future campaign targeting.

### Market Research
Understand audience composition and behavior patterns over time.

### Competitive Analysis
Compare segment performance across different time periods and markets.

### Customer Journey Mapping
Track user progression through different life events and in-market segments.