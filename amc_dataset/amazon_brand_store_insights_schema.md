# Amazon Brand Store Insights Tables Schema

## Overview

**Data Sources:** 
- `amazon_brand_store_page_views` (and `_non_endemic` variant)
- `amazon_brand_store_engagement_events` (and `_non_endemic` variant)

Amazon Brand Store insights is a collection of two AMC datasets that represent Brand Store page renders and interactions. This is a **standalone AMC Paid Features resource** available for trial and subscription enrollments within the AMC Paid Features suite.

## Availability and Access

### Subscription Requirements
- **AMC Paid Features enrollment**: Trial and subscription options available
- **Advertiser types**: Available to both endemic and non-endemic advertisers
- **Powered by**: Amazon Advertising

### Geographic Coverage
Supported AMC Paid Features account marketplaces:
- **US**: United States
- **CA**: Canada  
- **JP**: Japan
- **AU**: Australia
- **FR**: France
- **IT**: Italy
- **ES**: Spain
- **UK**: United Kingdom
- **DE**: Germany

## Table Differences and Use Cases

### amazon_brand_store_page_views
- **Granularity**: Store page-level events
- **Primary focus**: Page view events and dwell time analysis
- **Use cases**: Traffic analysis, page performance, user journey mapping
- **Key metric**: Dwell time measurement

### amazon_brand_store_engagement_events  
- **Granularity**: Store widget-level interactions
- **Primary focus**: Detailed engagement tracking and clicks
- **Use cases**: Widget performance, ASIN-level analysis, conversion optimization
- **Key metrics**: Event types, widget interactions, ASIN engagement

## Schema: amazon_brand_store_page_views

Brand Store page view events, including dwell time. Events are at the Store page-level.

| Field Category | Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|----------------|------|-----------|-------------------|-------------|----------------------|
| Brand Store Insights | advertiser_id | LONG | Dimension | Advertiser ID. | LOW |
| Brand Store Insights | channel | STRING | Dimension | Channel tag ID, referenced as query string name. | LOW |
| Brand Store Insights | device_type | STRING | Dimension | Device type that viewed the store. | MEDIUM |
| Brand Store Insights | dwell_time | DECIMAL | Dimension | Dwell time of page view (in seconds). | LOW |
| Brand Store Insights | event_date_utc | DATE | Dimension | Date of event in UTC. | LOW |
| Brand Store Insights | event_dt_utc | TIMESTAMP | Dimension | Timestamp of event in UTC. | LOW |
| Brand Store Insights | ingress_type | STRING | Dimension | Enumerated list of store traffic source: 0 - uncategorized/default, 1 - search, 2 - detail page byline, 4 - ads, 6 - store recommendations, 7-11 - experimentation | MEDIUM |
| Brand Store Insights | marketplace_id | INTEGER | Dimension | Marketplace ID of the store. | INTERNAL |
| Brand Store Insights | page_id | STRING | Dimension | Store page ID. | LOW |
| Brand Store Insights | page_title | STRING | Dimension | Title of the page. | LOW |
| Brand Store Insights | reference_id | STRING | Dimension | Identifier for the ad campaign associated with the Brand Store page visit (ingress_type = 4). | LOW |
| Brand Store Insights | referrer_domain | STRING | Dimension | HTML referrer domain from which user arrived (e.g., google.com external, amazon.com internal). | LOW |
| Brand Store Insights | session_id | STRING | Dimension | Store session ID. | VERY_HIGH |
| Brand Store Insights | store_name | STRING | Dimension | Name of the store set by the store owner. | LOW |
| Brand Store Insights | user_id | STRING | Dimension | User ID that performed the event. | VERY_HIGH |
| Brand Store Insights | user_id_type | STRING | Dimension | Type of User ID. | LOW |
| Brand Store Insights | visit_id | STRING | Dimension | Store visit ID. | VERY_HIGH |
| Brand Store Insights | no_3p_trackers | BOOLEAN | Dimension | Indicates whether this item is not allowed to use 3P tracking. | NONE |

## Schema: amazon_brand_store_engagement_events

Brand Store engagement events providing web engagement metrics including page views and clicks. Events are interaction-based and presented at the Store widget-level.

| Field Category | Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|----------------|------|-----------|-------------------|-------------|----------------------|
| Brand Store Insights | advertiser_id | LONG | Dimension | Advertiser ID. | LOW |
| Brand Store Insights | asin | STRING | Dimension | Amazon Standard Identification Number (ASIN). | LOW |
| Brand Store Insights | channel | STRING | Dimension | Channel tag ID, referenced as query string name. | LOW |
| Brand Store Insights | device_type | STRING | Dimension | Device type that viewed the store. | MEDIUM |
| Brand Store Insights | event_date_utc | DATE | Dimension | Date of event in UTC. | LOW |
| Brand Store Insights | event_dt_utc | TIMESTAMP | Dimension | Timestamp of event in UTC. | LOW |
| Brand Store Insights | event_sub_type | STRING | Dimension | Sub-type of event - refer to schema for values. | LOW |
| Brand Store Insights | event_type | STRING | Dimension | Type of event - refer to schema for values. | LOW |
| Brand Store Insights | ingress_type | STRING | Dimension | Enumerated list of store traffic source: 0 - uncategorized/default, 1 - search, 2 - detail page byline, 4 - ads, 6 - store recommendations, 7-11 - experimentation | MEDIUM |
| Brand Store Insights | marketplace_id | INTEGER | Dimension | Marketplace ID of the store. | INTERNAL |
| Brand Store Insights | page_id | STRING | Dimension | Store page ID. | LOW |
| Brand Store Insights | page_title | STRING | Dimension | Title of the page. | LOW |
| Brand Store Insights | reference_id | STRING | Dimension | Identifier for the ad campaign associated with the Brand Store page visit (ingress_type = 4). | LOW |
| Brand Store Insights | referrer_domain | STRING | Dimension | HTML referrer domain from which user arrived (e.g., google.com external, amazon.com internal). | LOW |
| Brand Store Insights | session_id | STRING | Dimension | Store session ID. | VERY_HIGH |
| Brand Store Insights | store_name | STRING | Dimension | Name of the store set by the store owner. | LOW |
| Brand Store Insights | user_id | STRING | Dimension | User ID that performed the event. | VERY_HIGH |
| Brand Store Insights | user_id_type | STRING | Dimension | Type of User ID. | LOW |
| Brand Store Insights | widget_sub_type | STRING | Dimension | Sub-type of widget - refer to schema for values. | LOW |
| Brand Store Insights | widget_type | STRING | Dimension | Type of widget - refer to schema for values. | LOW |
| Brand Store Insights | no_3p_trackers | BOOLEAN | Dimension | Indicates whether this item is not allowed to use 3P tracking. | NONE |

## Traffic Source Analysis (ingress_type)

Understanding how users arrive at Brand Stores is crucial for optimization:

| Ingress Type | Description | Use Case |
|--------------|-------------|----------|
| 0 | Uncategorized/Default | General traffic analysis |
| 1 | Search | Organic search performance |
| 2 | Detail Page Byline | Product page traffic |
| 4 | Ads | Paid advertising traffic (use with reference_id) |
| 6 | Store Recommendations | Amazon's recommendation engine |
| 7-11 | Experimentation | A/B testing and experimental traffic |

## Common Query Patterns

### Traffic Source Performance
```sql
-- Analyze traffic sources and their performance
SELECT 
    ingress_type,
    CASE 
        WHEN ingress_type = '0' THEN 'Uncategorized'
        WHEN ingress_type = '1' THEN 'Search'
        WHEN ingress_type = '2' THEN 'Detail Page Byline'
        WHEN ingress_type = '4' THEN 'Ads'
        WHEN ingress_type = '6' THEN 'Store Recommendations'
        WHEN ingress_type BETWEEN '7' AND '11' THEN 'Experimentation'
        ELSE 'Other'
    END as traffic_source,
    COUNT(DISTINCT visit_id) as unique_visits,
    COUNT(DISTINCT session_id) as unique_sessions,
    AVG(dwell_time) as avg_dwell_time_seconds
FROM amazon_brand_store_page_views
WHERE event_date_utc >= '2025-01-01'
GROUP BY ingress_type
ORDER BY unique_visits DESC;
```

### Page Performance Analysis
```sql
-- Analyze individual page performance
SELECT 
    page_title,
    page_id,
    COUNT(DISTINCT visit_id) as page_visits,
    AVG(dwell_time) as avg_dwell_time,
    COUNT(DISTINCT user_id) as unique_users
FROM amazon_brand_store_page_views
WHERE event_date_utc >= '2025-01-01'
    AND dwell_time IS NOT NULL
GROUP BY page_title, page_id
ORDER BY page_visits DESC;
```

### Device Type Analysis
```sql
-- Compare performance across device types
SELECT 
    device_type,
    COUNT(DISTINCT visit_id) as visits,
    COUNT(DISTINCT session_id) as sessions,
    AVG(dwell_time) as avg_dwell_time,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dwell_time) as median_dwell_time
FROM amazon_brand_store_page_views
WHERE event_date_utc >= '2025-01-01'
    AND dwell_time > 0
GROUP BY device_type
ORDER BY visits DESC;
```

### Widget Engagement Analysis
```sql
-- Analyze widget performance and engagement
SELECT 
    widget_type,
    widget_sub_type,
    event_type,
    event_sub_type,
    COUNT(*) as total_events,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as unique_sessions
FROM amazon_brand_store_engagement_events
WHERE event_date_utc >= '2025-01-01'
GROUP BY widget_type, widget_sub_type, event_type, event_sub_type
ORDER BY total_events DESC;
```

### ASIN Performance in Brand Store
```sql
-- Analyze ASIN-level engagement within Brand Store
SELECT 
    asin,
    widget_type,
    event_type,
    COUNT(*) as interactions,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT visit_id) as unique_visits
FROM amazon_brand_store_engagement_events
WHERE event_date_utc >= '2025-01-01'
    AND asin IS NOT NULL
GROUP BY asin, widget_type, event_type
ORDER BY interactions DESC;
```

### Campaign Attribution Analysis
```sql
-- Analyze campaign-driven Brand Store traffic
SELECT 
    reference_id as campaign_id,
    store_name,
    COUNT(DISTINCT visit_id) as campaign_visits,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(dwell_time) as avg_dwell_time
FROM amazon_brand_store_page_views
WHERE ingress_type = '4'  -- Ads traffic
    AND reference_id IS NOT NULL
    AND event_date_utc >= '2025-01-01'
GROUP BY reference_id, store_name
ORDER BY campaign_visits DESC;
```

### Session Journey Analysis
```sql
-- Analyze user journey within Brand Store sessions
WITH session_journey AS (
    SELECT 
        session_id,
        COUNT(DISTINCT page_id) as pages_per_session,
        SUM(dwell_time) as total_session_time,
        MIN(event_dt_utc) as session_start,
        MAX(event_dt_utc) as session_end
    FROM amazon_brand_store_page_views
    WHERE event_date_utc >= '2025-01-01'
        AND session_id IS NOT NULL
    GROUP BY session_id
)
SELECT 
    pages_per_session,
    COUNT(*) as session_count,
    AVG(total_session_time) as avg_session_duration,
    AVG(TIMESTAMP_DIFF(session_end, session_start, SECOND)) as avg_session_length_seconds
FROM session_journey
GROUP BY pages_per_session
ORDER BY pages_per_session;
```

### Cross-Channel Analysis
```sql
-- Analyze referrer domains and external traffic
SELECT 
    referrer_domain,
    CASE 
        WHEN referrer_domain LIKE '%amazon.%' THEN 'Internal Amazon'
        WHEN referrer_domain LIKE '%google.%' THEN 'Google'
        WHEN referrer_domain LIKE '%facebook.%' THEN 'Facebook'
        WHEN referrer_domain LIKE '%instagram.%' THEN 'Instagram'
        WHEN referrer_domain IS NULL THEN 'Direct'
        ELSE 'Other External'
    END as referrer_category,
    COUNT(DISTINCT visit_id) as visits,
    AVG(dwell_time) as avg_dwell_time
FROM amazon_brand_store_page_views
WHERE event_date_utc >= '2025-01-01'
GROUP BY referrer_domain
ORDER BY visits DESC;
```

## Advanced Analytics

### Engagement Funnel Analysis
```sql
-- Create engagement funnel from page views to interactions
WITH page_views AS (
    SELECT DISTINCT 
        user_id,
        visit_id,
        session_id,
        event_date_utc
    FROM amazon_brand_store_page_views
    WHERE event_date_utc >= '2025-01-01'
),
engagements AS (
    SELECT DISTINCT
        user_id,
        session_id,
        event_type,
        event_date_utc
    FROM amazon_brand_store_engagement_events
    WHERE event_date_utc >= '2025-01-01'
)
SELECT 
    COUNT(DISTINCT pv.user_id) as total_visitors,
    COUNT(DISTINCT e.user_id) as engaged_visitors,
    COUNT(DISTINCT e.user_id) * 100.0 / COUNT(DISTINCT pv.user_id) as engagement_rate
FROM page_views pv
LEFT JOIN engagements e 
    ON pv.user_id = e.user_id 
    AND pv.session_id = e.session_id;
```

### Conversion Attribution
```sql
-- Connect Brand Store visits to conversions
WITH brand_store_visitors AS (
    SELECT DISTINCT 
        user_id,
        visit_id,
        session_id,
        event_date_utc as visit_date,
        ingress_type,
        reference_id
    FROM amazon_brand_store_page_views
    WHERE event_date_utc >= '2025-01-01'
)
SELECT 
    bsv.ingress_type,
    COUNT(DISTINCT bsv.user_id) as store_visitors,
    COUNT(DISTINCT c.user_id) as converting_visitors,
    SUM(c.total_purchases) as total_purchases,
    SUM(c.total_product_sales) as total_sales,
    COUNT(DISTINCT c.user_id) * 100.0 / COUNT(DISTINCT bsv.user_id) as conversion_rate
FROM brand_store_visitors bsv
LEFT JOIN amazon_attributed_events_by_conversion_time c
    ON bsv.user_id = c.user_id
    AND c.conversion_event_date >= bsv.visit_date
    AND c.conversion_event_date <= DATE_ADD(bsv.visit_date, INTERVAL 7 DAY)
GROUP BY bsv.ingress_type
ORDER BY total_sales DESC;
```

### Cohort Analysis
```sql
-- Analyze repeat visit behavior
WITH first_visits AS (
    SELECT 
        user_id,
        MIN(event_date_utc) as first_visit_date
    FROM amazon_brand_store_page_views
    WHERE event_date_utc >= '2025-01-01'
    GROUP BY user_id
),
return_visits AS (
    SELECT 
        pv.user_id,
        fv.first_visit_date,
        DATE_DIFF(pv.event_date_utc, fv.first_visit_date, DAY) as days_since_first_visit
    FROM amazon_brand_store_page_views pv
    JOIN first_visits fv ON pv.user_id = fv.user_id
    WHERE pv.event_date_utc > fv.first_visit_date
)
SELECT 
    CASE 
        WHEN days_since_first_visit <= 7 THEN '1 Week'
        WHEN days_since_first_visit <= 30 THEN '1 Month'
        WHEN days_since_first_visit <= 90 THEN '3 Months'
        ELSE '3+ Months'
    END as return_timeframe,
    COUNT(DISTINCT user_id) as returning_users
FROM return_visits
GROUP BY 
    CASE 
        WHEN days_since_first_visit <= 7 THEN '1 Week'
        WHEN days_since_first_visit <= 30 THEN '1 Month'
        WHEN days_since_first_visit <= 90 THEN '3 Months'
        ELSE '3+ Months'
    END
ORDER BY returning_users DESC;
```

## Metric Conversion Guidelines

### Using visit_id and session_id as Metrics
As noted in the documentation, `visit_id` and `session_id` can be converted to metrics:

```sql
-- Convert visit_id to visit count metric
SELECT 
    store_name,
    event_date_utc,
    COUNT(DISTINCT visit_id) as total_visits,
    COUNT(visit_id) as total_page_views,
    COUNT(visit_id) * 1.0 / COUNT(DISTINCT visit_id) as pages_per_visit
FROM amazon_brand_store_page_views
GROUP BY store_name, event_date_utc;

-- Convert session_id to session count metric
SELECT 
    device_type,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(session_id) as total_events,
    AVG(dwell_time) as avg_dwell_time
FROM amazon_brand_store_page_views
GROUP BY device_type;
```

## Best Practices

### Query Optimization
- **Use CTEs for user_id**: Due to VERY_HIGH aggregation threshold, use user_id in Common Table Expressions
- **Filter by date ranges**: Always include event_date_utc filters for performance
- **Leverage specific dimensions**: Use page_id, widget_type, or ASIN for focused analysis
- **Join tables strategically**: Combine page views and engagement events for comprehensive analysis

### Analysis Guidelines
- **Understand granularity differences**: Page-level vs widget-level events
- **Account for device differences**: Mobile vs desktop behavior patterns
- **Consider traffic sources**: Different ingress types have different optimization strategies
- **Track engagement depth**: Use dwell time and widget interactions for quality metrics

### Business Applications
- **Store optimization**: Identify high and low-performing pages and widgets
- **Campaign measurement**: Track ads-driven traffic performance (ingress_type = 4)
- **Content strategy**: Analyze which content types drive engagement
- **User experience**: Optimize based on device-specific behavior patterns

## Integration Opportunities

### Campaign Attribution
- **DSP campaigns**: Use reference_id to connect DSP campaigns to Brand Store performance
- **Sponsored ads**: Analyze Brand Store traffic from sponsored product campaigns
- **Cross-channel**: Track users from Brand Store visits to conversions

### Audience Building
```sql
-- Create audience of engaged Brand Store visitors
CREATE AUDIENCE engaged_brand_store_visitors AS
SELECT DISTINCT user_id
FROM amazon_brand_store_engagement_events
WHERE event_date_utc >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    AND event_type IN ('click', 'interaction')  -- Adjust based on available event types
    AND no_3p_trackers = false;
```

### Performance Measurement
- **Content effectiveness**: Compare widget performance across different store layouts
- **Traffic quality**: Analyze conversion rates by traffic source
- **Seasonal trends**: Track Brand Store performance across different time periods

## Limitations and Considerations

### Data Scope
- **Paid feature requirement**: AMC Paid Features subscription needed
- **Geographic limitations**: Limited to supported marketplaces
- **Endemic vs non-endemic**: Different table versions may have different data availability

### Technical Considerations
- **Aggregation thresholds**: Follow VERY_HIGH restrictions for user_id, session_id, and visit_id
- **Dwell time accuracy**: Consider how dwell time is calculated and potential limitations
- **Widget categorization**: Event and widget types may vary - refer to schema documentation

### Privacy and Compliance
- **3P tracking**: Respect no_3p_trackers flag for audience creation
- **User privacy**: Ensure compliance with privacy regulations across different marketplaces
- **Data retention**: Understand data availability and retention policies

## Aggregation Threshold Notes

- **NONE**: No aggregation threshold restrictions
- **LOW**: Standard low threshold applies
- **MEDIUM**: Medium aggregation threshold - use caution in small segments
- **VERY_HIGH**: Very high threshold - cannot be included in final SELECT statements but can be used in CTEs for aggregation
- **INTERNAL**: Internal use only - not available for customer queries