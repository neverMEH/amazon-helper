# Amazon Prime Video Channel Insights Schema

## Overview

⚠️ **Important Availability Notice**: Amazon Prime Video Channel Insights is a standalone AMC Paid Features resource available for trial and subscription enrollments within the AMC Paid Features suite of insight expansion options, powered by Amazon Advertising.

**Eligibility Requirements**: This resource is available to Amazon Advertisers that operate Prime Video Channels within the supported AMC Paid Features account marketplaces (US/CA/JP/AU/FR/IT/ES/UK/DE).

Amazon Prime Video Channel Insights is a collection of two AMC data views that represent Prime Video Channel subscriptions and streaming signals, providing comprehensive analytics for Prime Video Channel performance and user engagement.

## Data Organization

### Dataset Structure
Prime Video Channel Insights consists of two distinct dataset types:
- **Enrollment Data** (`amazon_pvc_enrollments`): Subscription enrollment records and billing information
- **Streaming Data** (`amazon_pvc_streaming_events_feed`): Content streaming and engagement events with detailed metadata

### Supported Marketplaces
- **US**: United States
- **CA**: Canada  
- **JP**: Japan
- **AU**: Australia
- **FR**: France
- **IT**: Italy
- **ES**: Spain
- **UK**: United Kingdom
- **DE**: Germany

## Available Tables

### Primary Data Tables
- `amazon_pvc_enrollments`
- `amazon_pvc_streaming_events_feed`

## Schema: amazon_pvc_enrollments

Amazon Prime Video Channels enrollment records presented per benefit id. The `pv_subscription_id` column can be converted to metrics via `COUNT()` or `COUNT(distinct)` SQL aggregate functions.

| Field Category | Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|----------------|------|-----------|-------------------|-------------|----------------------|
| Core Identifiers | marketplace_id | LONG | Dimension | ID of the marketplace where the Amazon Prime Video Channel enrollment event occurred. | INTERNAL |
| Core Identifiers | marketplace_name | STRING | Dimension | The marketplace associated with the Amazon Prime Video Channel record | LOW |
| Core Identifiers | pv_benefit_id | STRING | Dimension | Amazon Prime Video subscription benefit identifier | INTERNAL |
| Core Identifiers | pv_subscription_id | STRING | Dimension | Amazon Prime Video subscription id | INTERNAL |
| Core Identifiers | pv_sub_event_primary_key | STRING | Dimension | Unique identifier for the PVC enrollment event | INTERNAL |
| Subscription Details | pv_benefit_name | STRING | Dimension | Amazon Prime Video subscription benefit name | LOW |
| Subscription Details | pv_billing_type | STRING | Dimension | Amazon Prime Video billing type for the enrollment record | MEDIUM |
| Subscription Details | pv_subscription_name | STRING | Dimension | Amazon Prime Video subscription name | LOW |
| Subscription Details | pv_subscription_product_id | STRING | Dimension | Amazon Prime Video subscription product identifier | INTERNAL |
| Subscription Details | pv_offer_name | STRING | Dimension | Amazon Prime Video subscription offer name | HIGH |
| Subscription Details | pv_unit_price | DECIMAL | Dimension | Unit price for the PVC enrollment record | NONE |
| Temporal Data | pv_start_date | DATE | Dimension | Interval-specific start date associated with the PVC enrollment record | LOW |
| Temporal Data | pv_end_date | DATE | Dimension | Interval-specific end date associated with the PVC enrollment record | LOW |
| Status Indicators | pv_enrollment_status | STRING | Dimension | Status for the PVC enrollment record | LOW |
| Status Indicators | pv_is_latest_record | BOOLEAN | Dimension | Indicator of whether the PVC enrollment record is the most recent record within the table | INTERNAL |
| Status Indicators | pv_is_plan_conversion | BOOLEAN | Dimension | Indicates whether the PVC enrollment record has converted from Free Trial to a subscription. This is often associated with a change in the billing type for the PVC subscription | LOW |
| Status Indicators | pv_is_plan_start | BOOLEAN | Dimension | Indicates whether the PVC enrollment record is the start of a enrollment. This is often the opening of a free trial or the first subscription record for the PV subscription ID | LOW |
| Status Indicators | pv_is_promo | BOOLEAN | Dimension | Indicator of whether the PVC enrollment record is associated with a promotional offer | LOW |
| User Data | user_id | STRING | Dimension | Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERYHIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT userid). | VERY_HIGH |
| User Data | user_id_type | STRING | Dimension | Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for an impression event, the user_id and user_id_type values for that record will be NULL. Possible values include: 'adUserId', 'sisDeviceId', 'adBrowserId', and NULL. | LOW |
| Privacy Controls | no_3p_trackers | BOOLEAN | Dimension | Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Possible values for this field are: 'true', 'false'. | LOW |

## Schema: amazon_pvc_streaming_events_feed

Amazon Prime Video Channel Streaming and engagement events. Provides Amazon Prime Video Channel engagement metrics including content metadata, request context and duration. Events are session based and presented at the PVC benefit-level. The `pv_session_id` columns can be converted to metrics via `COUNT()` or `COUNT(distinct)` SQL aggregate functions.

| Field Category | Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|----------------|------|-----------|-------------------|-------------|----------------------|
| Core Identifiers | marketplace_id | LONG | Dimension | Marketplace ID of the event | INTERNAL |
| Core Identifiers | marketplace_name | STRING | Dimension | Marketplace name of the event | LOW |
| Core Identifiers | pv_session_id | STRING | Dimension | Unique identifier for streaming session | VERY_HIGH |
| Core Identifiers | pv_streaming_asin | STRING | Dimension | Amazon Standard Identification Number (ASIN) | LOW |
| Core Identifiers | pv_streaming_gti | STRING | Dimension | Global title information | LOW |
| Temporal Data | pv_playback_date_utc | DATE | Dimension | Date of the event in UTC | LOW |
| Temporal Data | pv_playback_dt_utc | TIMESTAMP | Dimension | Timestamp of the event in UTC | MEDIUM |
| Engagement Metrics | pv_seconds_viewed | DECIMAL | Metric | Seconds of view time associated with streaming event | MEDIUM |
| Content Metadata | pv_gti_series_or_movie_name | STRING | Dimension | Series or movie name | LOW |
| Content Metadata | pv_gti_title_name | STRING | Dimension | Content title (e.g., episode name) | LOW |
| Content Metadata | pv_gti_content_type | STRING | Dimension | Content type (e.g., TV Episode, Movie, Promotion) | LOW |
| Content Metadata | pv_gti_content_entity_type | STRING | Dimension | Content entity type (e.g., Short Film, Educational) | LOW |
| Content Metadata | pv_gti_content_rating | STRING | Dimension | Content rating | LOW |
| Content Metadata | pv_gti_genre | ARRAY | Dimension | Content genre | LOW |
| Content Metadata | pv_gti_studio | STRING | Dimension | Content studio | LOW |
| Content Metadata | pv_gti_release_date | DATE | Dimension | Content release date | LOW |
| Series Information | pv_gti_season | STRING | Dimension | Series season | LOW |
| Series Information | pv_gti_episode | STRING | Dimension | Series episode | LOW |
| Content Personnel | pv_gti_cast | ARRAY | Dimension | Content cast members | LOW |
| Content Personnel | pv_gti_director | ARRAY | Dimension | Content directors | LOW |
| Event Context | pv_gti_event_name | STRING | Dimension | Content event name | LOW |
| Event Context | pv_gti_event_context | STRING | Dimension | Content event context | LOW |
| Event Context | pv_gti_event_item | STRING | Dimension | Content event item | LOW |
| Event Context | pv_gti_event_league | STRING | Dimension | Content event league | LOW |
| Event Context | pv_gti_event_sport | STRING | Dimension | Content event sport | LOW |
| Stream Properties | pv_stream_type | STRING | Dimension | Type of stream content (e.g., linear TV, live-event, VOD) | LOW |
| Stream Properties | pv_material_type | STRING | Dimension | Video material type (e.g., full, live, promo, trailer) | LOW |
| Stream Properties | pv_access_type | STRING | Dimension | Content access type (e.g., free, prime subscription, rental, purchase) | LOW |
| Stream Properties | pv_offer_group | STRING | Dimension | Content offer group (e.g., free, prime, rental, purchase) | LOW |
| Content Flags | pv_gti_is_live | BOOLEAN | Dimension | Indicates if content is live | LOW |
| Content Flags | pv_is_avod | BOOLEAN | Dimension | Indicates if content is advertiser-supported VOD | LOW |
| Content Flags | pv_is_channels | BOOLEAN | Dimension | Indicates if content is a channel | LOW |
| Content Flags | pv_is_svod | BOOLEAN | Dimension | Indicates if content is subscription VOD | LOW |
| Content Flags | pv_is_user_initiated | BOOLEAN | Dimension | Indicates if content playback was user-initiated | LOW |
| Content Flags | pv_is_hh_share | BOOLEAN | Dimension | Indicates if content is shared within household | LOW |
| Geographic Data | pv_streaming_geo_country | STRING | Dimension | Country where event was accessed | LOW |
| Geographic Data | pv_streaming_language | STRING | Dimension | Language of the event | LOW |
| User Data | user_id | STRING | Dimension | Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERYHIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT userid). | VERY_HIGH |
| User Data | user_id_type | STRING | Dimension | Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for an impression event, the user_id and user_id_type values for that record will be NULL. Possible values include: 'adUserId', 'sisDeviceId', 'adBrowserId', and NULL. | LOW |
| Privacy Controls | no_3p_trackers | BOOLEAN | Dimension | Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Possible values for this field are: 'true', 'false'. | LOW |

## AMC Best Practices and Recommendations

### Critical Query Restrictions

1. **Benefit-Level Analysis**: Focus queries on specific `pv_benefit_id` values to optimize performance and relevance.

2. **Marketplace Filtering**: Always include marketplace-specific filtering using `marketplace_id` to ensure regional accuracy and performance.

3. **Date Range Limitation**: When analyzing streaming events, limit your date range using `pv_playback_date_utc` to prevent query timeouts.

4. **Session-Based Analysis**: Use `pv_session_id` for session-level aggregations rather than attempting to reconstruct sessions manually.

### User ID Handling

5. **Aggregation Requirements**: Remember that `user_id` has VERY_HIGH aggregation threshold - use only within CTEs for aggregation purposes.

6. **Cross-Table Joins**: When joining enrollment and streaming data, use `user_id` within CTEs to maintain privacy compliance.

7. **User Type Filtering**: Consider filtering by `user_id_type` based on your analysis requirements (adUserId, sisDeviceId, adBrowserId).

### Performance Optimization

8. **Latest Record Focus**: Use `pv_is_latest_record = true` when analyzing current subscription states.

9. **Content Type Filtering**: Apply early filtering on `pv_gti_content_type` and `pv_stream_type` for content-specific analysis.

10. **Geographic Scoping**: Filter by `pv_streaming_geo_country` when conducting regional analysis.

## Common Query Patterns

### Subscription Lifecycle Analysis
```sql
-- Analyze subscription conversion funnel
SELECT 
    pv_benefit_name,
    pv_billing_type,
    COUNT(DISTINCT pv_subscription_id) as subscription_count,
    COUNT(DISTINCT CASE WHEN pv_is_plan_start = true THEN pv_subscription_id END) as plan_starts,
    COUNT(DISTINCT CASE WHEN pv_is_plan_conversion = true THEN pv_subscription_id END) as conversions,
    AVG(pv_unit_price) as avg_unit_price
FROM amazon_pvc_enrollments
WHERE marketplace_id = 1  -- US marketplace
    AND pv_is_latest_record = true
    AND pv_start_date >= '2025-01-01'
GROUP BY pv_benefit_name, pv_billing_type
ORDER BY subscription_count DESC;
```

### Content Performance Analysis
```sql
-- Top performing content by viewing time
SELECT 
    pv_gti_series_or_movie_name,
    pv_gti_content_type,
    pv_gti_genre,
    COUNT(DISTINCT pv_session_id) as total_sessions,
    SUM(pv_seconds_viewed) as total_viewing_seconds,
    AVG(pv_seconds_viewed) as avg_session_duration
FROM amazon_pvc_streaming_events_feed
WHERE marketplace_id = 1
    AND pv_playback_date_utc >= '2025-01-01'
    AND pv_playback_date_utc <= '2025-01-31'
    AND pv_is_user_initiated = true
GROUP BY pv_gti_series_or_movie_name, pv_gti_content_type, pv_gti_genre
HAVING total_sessions >= 100  -- Filter for statistically significant content
ORDER BY total_viewing_seconds DESC
LIMIT 50;
```

### Cross-Platform Engagement Analysis
```sql
-- User engagement across subscription and streaming
WITH subscription_users AS (
    SELECT DISTINCT 
        user_id,
        pv_benefit_name,
        pv_billing_type
    FROM amazon_pvc_enrollments
    WHERE marketplace_id = 1
        AND pv_is_latest_record = true
        AND pv_enrollment_status = 'ACTIVE'
),
streaming_summary AS (
    SELECT 
        user_id,
        COUNT(DISTINCT pv_session_id) as streaming_sessions,
        SUM(pv_seconds_viewed) as total_viewing_time,
        COUNT(DISTINCT pv_gti_series_or_movie_name) as unique_content_consumed
    FROM amazon_pvc_streaming_events_feed
    WHERE marketplace_id = 1
        AND pv_playback_date_utc >= '2025-01-01'
        AND pv_playback_date_utc <= '2025-01-31'
    GROUP BY user_id
)
SELECT 
    s.pv_benefit_name,
    s.pv_billing_type,
    COUNT(DISTINCT s.user_id) as total_subscribers,
    COUNT(DISTINCT st.user_id) as active_viewers,
    AVG(st.streaming_sessions) as avg_sessions_per_user,
    AVG(st.total_viewing_time) as avg_viewing_time_per_user,
    AVG(st.unique_content_consumed) as avg_unique_content_per_user
FROM subscription_users s
LEFT JOIN streaming_summary st ON s.user_id = st.user_id
GROUP BY s.pv_benefit_name, s.pv_billing_type
ORDER BY total_subscribers DESC;
```

### Live Content Engagement
```sql
-- Live content streaming analysis
SELECT 
    pv_gti_event_sport,
    pv_gti_event_league,
    pv_gti_event_name,
    COUNT(DISTINCT pv_session_id) as live_sessions,
    SUM(pv_seconds_viewed) as total_live_viewing,
    AVG(pv_seconds_viewed) as avg_session_duration,
    COUNT(DISTINCT CASE WHEN pv_streaming_geo_country = 'US' THEN pv_session_id END) as us_sessions
FROM amazon_pvc_streaming_events_feed
WHERE marketplace_id = 1
    AND pv_gti_is_live = true
    AND pv_stream_type = 'live-event'
    AND pv_playback_date_utc >= '2025-01-01'
    AND pv_playback_date_utc <= '2025-01-31'
GROUP BY pv_gti_event_sport, pv_gti_event_league, pv_gti_event_name
HAVING live_sessions >= 50  -- Focus on popular events
ORDER BY total_live_viewing DESC;
```

### Promotional Offer Performance
```sql
-- Analyze promotional subscription performance
SELECT 
    pv_offer_name,
    pv_billing_type,
    COUNT(DISTINCT pv_subscription_id) as promo_subscriptions,
    COUNT(DISTINCT CASE WHEN pv_is_plan_conversion = true THEN pv_subscription_id END) as promo_conversions,
    SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN pv_is_plan_conversion = true THEN pv_subscription_id END),
        COUNT(DISTINCT pv_subscription_id)
    ) * 100 as conversion_rate_percent,
    AVG(pv_unit_price) as avg_promo_price
FROM amazon_pvc_enrollments
WHERE marketplace_id = 1
    AND pv_is_promo = true
    AND pv_start_date >= '2025-01-01'
GROUP BY pv_offer_name, pv_billing_type
HAVING promo_subscriptions >= 10
ORDER BY conversion_rate_percent DESC;
```

## Performance Optimization Strategies

### Query Design
- **Early Filtering**: Apply marketplace, date, and benefit filters as early as possible in your queries
- **Specific Targeting**: Focus on specific content types, subscription tiers, or geographic regions rather than broad analysis
- **Aggregation Strategy**: Use appropriate aggregation functions for session-based (`COUNT(DISTINCT pv_session_id)`) vs. subscription-based (`COUNT(DISTINCT pv_subscription_id)`) metrics
- **CTE Usage**: Leverage CTEs for complex user-level aggregations with VERY_HIGH threshold fields

### Index Optimization
- **Temporal Queries**: Structure date-based filters efficiently using `pv_playback_date_utc` for streaming and `pv_start_date`/`pv_end_date` for enrollments
- **Content Filtering**: Apply content-type filters early in streaming queries
- **Status Filtering**: Use `pv_is_latest_record = true` for current-state enrollment analysis

### Data Volume Management
```sql
-- Efficient large-scale content analysis pattern
WITH content_sessions AS (
    SELECT 
        pv_gti_series_or_movie_name,
        pv_gti_content_type,
        COUNT(DISTINCT pv_session_id) as session_count,
        SUM(pv_seconds_viewed) as total_seconds
    FROM amazon_pvc_streaming_events_feed
    WHERE marketplace_id = 1
        AND pv_playback_date_utc = '2025-01-15'  -- Single day analysis
        AND pv_gti_content_type IN ('Movie', 'TV Episode')  -- Specific content types
        AND pv_is_user_initiated = true  -- User-driven sessions only
    GROUP BY pv_gti_series_or_movie_name, pv_gti_content_type
    HAVING session_count >= 10  -- Filter low-volume content
)
SELECT 
    pv_gti_content_type,
    COUNT(*) as content_titles,
    SUM(session_count) as total_sessions,
    SUM(total_seconds) as total_viewing_seconds,
    AVG(total_seconds) as avg_seconds_per_title
FROM content_sessions
GROUP BY pv_gti_content_type
ORDER BY total_viewing_seconds DESC;
```

## Regional Marketplace Configuration

### Marketplace ID Reference
| Region | Country | Marketplace ID | Marketplace Name |
|--------|---------|----------------|------------------|
| Americas | United States | 1 | US |
| Americas | Canada | 7 | CA |
| APAC | Japan | 6 | JP |
| APAC | Australia | 35 | AU |
| Europe | United Kingdom | 3 | UK |
| Europe | Germany | 4 | DE |
| Europe | France | 5 | FR |
| Europe | Italy | 8 | IT |
| Europe | Spain | 44 | ES |

*Note: Always verify marketplace IDs for your specific account configuration*

## Data Freshness and Availability

### Enrollment Data
- **Refresh Frequency**: Near real-time for new enrollments
- **Historical Availability**: Full subscription lifecycle data
- **Latency**: Typically 2-4 hours for new subscription events

### Streaming Data  
- **Refresh Frequency**: Near real-time for streaming events
- **Historical Availability**: Comprehensive viewing history
- **Latency**: Typically 1-2 hours for completed viewing sessions

### Data Retention
- **Enrollment Records**: Long-term retention for subscription lifecycle analysis
- **Streaming Events**: Extended retention for trend analysis and content performance tracking

## Common Pitfalls and Solutions

### Performance Issues
❌ **Don't**: Query both tables simultaneously without proper filtering
✅ **Do**: Apply marketplace and date filters before joining datasets

❌ **Don't**: Use broad date ranges on streaming data without content filtering  
✅ **Do**: Limit analysis scope with specific content types and timeframes

❌ **Don't**: Ignore aggregation thresholds for user_id fields
✅ **Do**: Use user_id only within CTEs for aggregation purposes

### Data Quality
❌ **Don't**: Assume all sessions represent completed viewing
✅ **Do**: Filter for user-initiated sessions and apply minimum duration thresholds

❌ **Don't**: Mix current and historical subscription states
✅ **Do**: Use `pv_is_latest_record = true` for current state analysis

❌ **Don't**: Ignore null values in content metadata
✅ **Do**: Handle null values appropriately in content analysis queries

### Analysis Accuracy
❌ **Don't**: Count duplicate sessions without distinct aggregation
✅ **Do**: Use `COUNT(DISTINCT pv_session_id)` for accurate session metrics

❌ **Don't**: Compare metrics across different subscription billing types without context
✅ **Do**: Segment analysis by billing type and subscription tier

❌ **Don't**: Analyze promotional performance without conversion context
✅ **Do**: Track full subscription lifecycle from trial to conversion

## Content Metadata Best Practices

### Genre Analysis
```sql
-- Handling array-type genre data
SELECT 
    genre_element,
    COUNT(DISTINCT pv_session_id) as sessions_with_genre,
    SUM(pv_seconds_viewed) as total_viewing_time
FROM amazon_pvc_streaming_events_feed,
UNNEST(pv_gti_genre) as genre_element
WHERE marketplace_id = 1
    AND pv_playback_date_utc >= '2025-01-01'
    AND pv_playback_date_utc <= '2025-01-31'
GROUP BY genre_element
ORDER BY total_viewing_time DESC;
```

### Content Rating Analysis
- **Content Filtering**: Use `pv_gti_content_rating` for audience-appropriate content analysis
- **Geographic Variations**: Consider regional rating differences across marketplaces
- **Parental Controls**: Factor in household sharing patterns with `pv_is_hh_share`

### Live vs. On-Demand Performance
- **Content Classification**: Distinguish between live (`pv_gti_is_live = true`) and on-demand content
- **Material Types**: Analyze different material types (full, live, promo, trailer) separately
- **Access Types**: Consider subscription tier impact on content access patterns

## Use Case Examples

### Subscription Performance Analysis
Optimize subscription offerings by analyzing conversion rates, pricing effectiveness, and promotional campaign performance across different markets and content categories.

### Content Strategy Optimization  
Identify high-performing content genres, optimal content duration, and viewer engagement patterns to inform content acquisition and production decisions.

### Geographic Market Analysis
Compare content consumption patterns, subscription preferences, and engagement metrics across different geographic markets to tailor regional strategies.

### Live Event Performance Tracking
Monitor real-time engagement for live sports and events, analyzing audience reach, viewing duration, and geographic distribution.

### Customer Lifecycle Intelligence
Track user journey from initial subscription through content consumption patterns to identify retention opportunities and churn risk factors.

### Cross-Platform Attribution
Connect subscription enrollment events with content streaming behavior to measure the effectiveness of content in driving and retaining subscriptions.

### Competitive Content Analysis
Benchmark content performance against subscription tiers and promotional offers to optimize content placement and pricing strategies.

### Audience Development
Identify content preferences and viewing patterns to develop targeted audience segments for advertising and content recommendation engines.