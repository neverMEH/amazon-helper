# sponsored_ads_traffic Data Source Schema

## Overview

**Data Source:** `sponsored_ads_traffic`

This table contains impression events, click events, and video creative messages from Sponsored Products, Sponsored Brands, Sponsored Display, and Sponsored TV campaigns. There will be 1 record per sponsored ads impression event and 1 record per click event originated from a sponsored ads campaign.

## Product Coverage

Use the `ad_product_type` field to filter traffic events by specific ad product:

- **Sponsored Products**: `ad_product_type = 'sponsored_products'`
- **Sponsored Brands**: `ad_product_type = 'sponsored_brands'`
- **Sponsored Display**: `ad_product_type = 'sponsored_display'`
- **Sponsored TV**: `ad_product_type = 'sponsored_television'`

## Table Schema

### Core Traffic Metrics

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| impressions | LONG | Metric | Count of sponsored ads impressions. Possible values: '1' (if the record represents a sponsored ads impression) or '0' (if not). | NONE |
| clicks | LONG | Metric | Count of sponsored ads clicks. Possible values: '1' (if the record represents a click event) or '0' (if not). | NONE |
| spend | LONG | Metric | The total advertising cost in microcents for the sponsored ads traffic event. Note that some ad products, such as Sponsored Products, only incur costs for click events. Divide by 100,000,000 to convert to dollars (e.g., 100,000,000 microcents = $1.00). Example value: '325000'. | LOW |

### Product and Campaign Information

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| ad_product_type | STRING | Dimension | Type of sponsored ads campaign that generated the traffic event. Possible values include: 'sponsored_products', 'sponsored_brands', 'sponsored_display', and 'sponsored_television'. | LOW |
| advertiser | STRING | Dimension | Name of the business entity running advertising campaigns on sponsored ads. Example value: 'Widgets Inc'. | LOW |
| campaign | STRING | Dimension | Name of the sponsored ads campaign responsible for the traffic event. Example value: 'Widgets_Q1_2024_Keywords_US'. | LOW |
| campaign_id | LONG | Dimension | The ID of the sponsored ads campaign associated with the traffic event. This campaign ID can be used in the Ads API, and may differ from the campaign ID shown in the ads console (found in campaign_id_string). | LOW |
| campaign_id_string | STRING | Dimension | The ID of the sponsored ads campaign associated with the traffic event. This is the campaign ID shown in the ads console, and may differ from the campaign ID used in the Ads API (found in campaign_id). | LOW |
| campaign_budget_type | STRING | Dimension | Type of budget allocation for a sponsored ads campaign. Possible values include: 'DAILY_BUDGET' and 'LIFETIME_BUDGET'. | LOW |

### Ad Group / Line Item Information

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| ad_group | STRING | Dimension | Name of the sponsored ads ad group. Values will match the line_item field. Example value: 'SP_Widgets_Spring_2025'. | LOW |
| line_item | STRING | Dimension | Name of the sponsored ads ad group. Values will match the ad_group field. Example value: 'SP_Widgets_Spring_2025'. | LOW |
| ad_group_id / line_item_id | LONG | Dimension | ID of the sponsored ads ad group. | LOW |
| ad_group_status / line_item_status | STRING | Dimension | Status of the sponsored ads ad group. Possible values include: 'ENABLED', 'PAUSED', and 'ARCHIVED'. | LOW |
| ad_group_type | STRING | Dimension | Type of sponsored ads ad group. | LOW |

### Portfolio Organization

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| porfolio_id | STRING | Dimension | The ID of the portfolio that the campaign belongs to. Portfolios are groups of campaigns organized by brand, product category, or season. | LOW |
| portfolio_name | STRING | Dimension | The name of the portfolio that the campaign belongs to. | LOW |

### Creative and Content

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| creative | STRING | Dimension | Name of the sponsored ads creative/ad. Example value: '2025_US_Widgets_B01234ABC'. | LOW |
| creative_asin | STRING | Dimension | The ASIN that appears in the ad. Note: Only populated for a subset of Sponsored Products and Sponsored Display events. For other ad products, this will be NULL. | LOW |
| creative_type | STRING | Dimension | Type of creative/ad. Possible values include: 'static_image', 'video', 'third_party_creative'. | LOW |

### Search and Targeting

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| customer_search_term | STRING | Dimension | Search term entered by a shopper on Amazon that led to the traffic event. Represents actual text shoppers type into search bar. Example value: 'blue widgets 3 pack'. | LOW |
| targeting | STRING | Dimension | Keyword used by the advertiser for targeting. Example value: 'premium widgets'. | LOW |
| match_type | STRING | Dimension | Type of match between targeting keyword and customer search term. Possible values: 'BROAD', 'PHRASE', 'EXACT', and NULL (for non-keyword-targeted media). | LOW |
| placement_type | STRING | Dimension | Location where the sponsored ad appeared. Example values: 'Top of Search on-Amazon', 'Detail Page on-Amazon', 'Homepage on-Amazon', 'Off Amazon'. | LOW |

### Event Timing

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| event_date | DATE | Dimension | Date of the sponsored ads traffic event in advertiser timezone. Example value: '2025-01-01'. | LOW |
| event_date_utc | DATE | Dimension | Date of the sponsored ads traffic event in Coordinated Universal Time (UTC). | LOW |
| event_dt | TIMESTAMP | Dimension | Timestamp of the sponsored ads traffic event in advertiser timezone. | MEDIUM |
| event_dt_utc | TIMESTAMP | Dimension | Timestamp of the sponsored ads traffic event in Coordinated Universal Time (UTC). | MEDIUM |
| event_hour | INTEGER | Dimension | Hour of day when the traffic event occurred (0-23) in advertiser timezone. | LOW |
| event_hour_utc | INTEGER | Dimension | Hour of day when the traffic event occurred (0-23) in UTC. | LOW |

### Video Performance Metrics

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| five_sec_views | LONG | Metric | Count of video impressions where video was viewed for at least five seconds. For videos shorter than 5 seconds, this is always '1'. Values: '1' (qualifying view) or '0' (not qualifying). | NONE |
| video_first_quartile_views | LONG | Metric | Count of video impressions where video was viewed to first quartile (25% completion). Values: '1' (reached 25%) or '0' (did not reach 25%). | NONE |
| video_midpoint_views | LONG | Metric | Count of video impressions where video was viewed to midpoint (50% completion). Values: '1' (reached 50%) or '0' (did not reach 50%). | NONE |
| video_third_quartile_views | LONG | Metric | Count of video impressions where video was viewed to third quartile (75% completion). Values: '1' (reached 75%) or '0' (did not reach 75%). | NONE |
| video_complete_views | LONG | Metric | Count of video impressions where video was viewed to completion (100%). Values: '1' (completed) or '0' (not completed). | NONE |
| video_unmutes | LONG | Metric | Count of video impressions where shopper unmuted the video. Values: '1' (unmuted) or '0' (not unmuted). | NONE |

### Viewability Metrics

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| viewable_impressions | LONG | Metric | Count of impressions considered viewable per MRC standards (50% pixels visible for 1+ seconds for display, 2+ seconds for video). Values: '1' (viewable) or '0' (not viewable). | NONE |
| unmeasurable_viewable_impressions | LONG | Metric | Count of unmeasurable viewable/synthetic view events estimated to be viewable but couldn't be measured. Values: '1' (unmeasurable viewable) or '0' (not unmeasurable viewable). | NONE |
| view_definition | STRING | Dimension | Type of viewability measurement definition used to classify the view event. NULL for non-view events. | LOW |

### Audience and Segmentation

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| matched_behavior_segment_ids | ARRAY | Metric | For impressions subject to audience bid multiplier, the segment ID for the matched audience. May include first-party segments or Amazon-created segments. | LOW |
| user_id | STRING | Dimension | Pseudonymous identifier connecting user activity across events. VERY_HIGH aggregation threshold - use in CTEs only. | VERY_HIGH |
| user_id_type | STRING | Dimension | Type of user ID value: 'adUserId', 'sisDeviceId', 'adBrowserId', or NULL. | LOW |

### Technical and System Fields

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| event_id | STRING | Dimension | Internal event ID that uniquely identifies sponsored ads traffic events. Use to join with amazon_attributed_* tables (traffic_event_id). | VERY_HIGH |
| entity_id | STRING | Dimension | ID of the Amazon Ads entity (seat) associated with the traffic event. | LOW |
| marketplace_name | STRING | Dimension | Marketplace name where event occurred. | LOW |
| currency_iso_code | STRING | Dimension | Currency ISO code for monetary values (e.g., 'USD'). | LOW |
| currency_name | STRING | Dimension | Currency name for monetary values (e.g., 'Dollar (USA)'). | LOW |

### Device and Environment

| Field | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|-------|-----------|-------------------|-------------|----------------------|
| operating_system | STRING | Dimension | Operating system of device where event occurred. Example values: 'iOS', 'Android', 'Windows', 'macOS', 'Roku OS'. | LOW |
| os_version | STRING | Dimension | Operating system version. Format varies by OS type. Example: '17.5.1'. | LOW |
| no_3p_trackers | BOOLEAN | Dimension | Whether event can be used for third-party tracking enabled audience creation. Values: 'true', 'false'. | NONE |

## Key Concepts and Usage

### Record Structure
- **One record per event**: Separate records for impressions and clicks
- **Event identification**: Use `impressions = 1` for impression events, `clicks = 1` for click events
- **Cost model varies**: Some products (like Sponsored Products) only charge for clicks

### Video Engagement Funnel
For video ads, track the engagement progression:
1. **Impression**: Ad started loading
2. **five_sec_views**: Viewed for 5+ seconds
3. **video_first_quartile_views**: 25% completion
4. **video_midpoint_views**: 50% completion
5. **video_third_quartile_views**: 75% completion
6. **video_complete_views**: 100% completion

### Search Term vs Keyword
- **customer_search_term**: What shoppers actually typed in search
- **targeting**: Advertiser's targeted keyword
- **match_type**: How closely they matched (BROAD, PHRASE, EXACT)

### Campaign Organization Hierarchy
1. **Portfolio**: Groups of campaigns (optional)
2. **Campaign**: Container for ad groups
3. **Ad Group / Line Item**: Organizes ads and targeting
4. **Creative**: Individual ads

## Common Query Patterns

### Traffic Overview by Product Type
```sql
SELECT 
    ad_product_type,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    SUM(spend) / 100000000.0 as total_spend_dollars,
    CASE 
        WHEN SUM(impressions) > 0 
        THEN SUM(clicks) * 100.0 / SUM(impressions) 
        ELSE 0 
    END as ctr_percent
FROM sponsored_ads_traffic
GROUP BY ad_product_type;
```

### Video Performance Analysis
```sql
SELECT 
    campaign,
    SUM(impressions) as video_impressions,
    SUM(five_sec_views) as five_sec_views,
    SUM(video_first_quartile_views) as q1_views,
    SUM(video_midpoint_views) as q2_views,
    SUM(video_third_quartile_views) as q3_views,
    SUM(video_complete_views) as completed_views,
    CASE 
        WHEN SUM(impressions) > 0 
        THEN SUM(video_complete_views) * 100.0 / SUM(impressions)
        ELSE 0 
    END as completion_rate_percent
FROM sponsored_ads_traffic
WHERE creative_type = 'video'
    AND impressions = 1
GROUP BY campaign;
```

### Search Performance Analysis
```sql
-- Search term performance
SELECT 
    customer_search_term,
    targeting as keyword,
    match_type,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    SUM(spend) / 100000000.0 as spend_dollars
FROM sponsored_ads_traffic
WHERE customer_search_term IS NOT NULL
GROUP BY customer_search_term, targeting, match_type
ORDER BY SUM(spend) DESC;
```

### Portfolio Performance
```sql
-- Portfolio-level analysis
SELECT 
    portfolio_name,
    campaign,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    SUM(spend) / 100000000.0 as spend_dollars,
    CASE 
        WHEN SUM(clicks) > 0 
        THEN SUM(spend) / 100000000.0 / SUM(clicks)
        ELSE 0 
    END as avg_cpc
FROM sponsored_ads_traffic
WHERE portfolio_name IS NOT NULL
GROUP BY portfolio_name, campaign
ORDER BY portfolio_name, SUM(spend) DESC;
```

### Placement Performance
```sql
-- Performance by ad placement
SELECT 
    placement_type,
    ad_product_type,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    SUM(viewable_impressions) as viewable_impressions,
    CASE 
        WHEN SUM(impressions) > 0 
        THEN SUM(viewable_impressions) * 100.0 / SUM(impressions)
        ELSE 0 
    END as viewability_rate_percent
FROM sponsored_ads_traffic
WHERE impressions = 1
GROUP BY placement_type, ad_product_type;
```

### Hourly Performance Patterns
```sql
-- Traffic patterns by hour of day
SELECT 
    event_hour,
    ad_product_type,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    AVG(CASE WHEN clicks > 0 THEN spend / 100000000.0 ELSE NULL END) as avg_cpc
FROM sponsored_ads_traffic
GROUP BY event_hour, ad_product_type
ORDER BY event_hour, ad_product_type;
```

## Attribution Joins

### Connecting to Conversion Data
```sql
-- Join traffic to attributed conversions
SELECT 
    t.campaign,
    t.customer_search_term,
    SUM(t.clicks) as traffic_clicks,
    SUM(a.total_purchases) as attributed_purchases
FROM sponsored_ads_traffic t
LEFT JOIN amazon_attributed_events_by_conversion_time a
    ON t.event_id = a.traffic_event_id
WHERE t.ad_product_type = 'sponsored_products'
GROUP BY t.campaign, t.customer_search_term;
```

## Best Practices

### Query Performance
- **Filter by ad_product_type** early to focus on specific sponsored ads products
- **Use event date filters** to limit time ranges for better performance
- **Consider impressions vs clicks** - filter appropriately for your analysis needs

### Video Analysis
- **Check creative_type = 'video'** when analyzing video metrics
- **Focus on impression events** for video engagement metrics
- **Use completion funnel** to identify drop-off points

### Search Term Analysis
- **Distinguish search terms from keywords** for accurate performance analysis
- **Account for match types** when aggregating keyword performance
- **NULL handling**: Not all traffic has search terms (e.g., display placements)

### Cost Analysis
- **Convert microcents properly**: Divide by 100,000,000 for dollar amounts
- **Product-specific costs**: Some products only charge for clicks, others for impressions
- **Currency considerations**: Check currency_iso_code for multi-currency accounts

### Attribution Considerations
- **Use event_id for joins** to connect with attributed conversion tables
- **Account for attribution windows** when analyzing conversion performance
- **User-level analysis**: Use user_id in CTEs only due to aggregation thresholds

## Data Availability Notes

- **Sponsored Brands**: Available from December 2, 2022
- **Keywords and search terms**: 13 months historical or instance creation date, whichever is sooner
- **Video metrics**: Only populated for video creative types
- **ASIN data**: creative_asin only available for subset of Sponsored Products and Display

## Aggregation Threshold Notes

- **NONE**: No aggregation threshold restrictions
- **LOW**: Standard low threshold applies
- **MEDIUM**: Medium aggregation threshold - use caution in small segments
- **VERY_HIGH**: Very high threshold - cannot be included in final SELECT statements but can be used in CTEs for aggregation
- **INTERNAL**: Internal use only - not available for customer queries