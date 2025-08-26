# conversions_with_relevance Data Source Schema

## Overview

**Data Source:** `conversions_with_relevance`

The data sources `conversions` and `conversions_with_relevance` are used to create custom attribution models both for ASIN conversions (purchases) and pixel conversions. This table extends the base conversions data with campaign attribution information.

**Key Difference from `conversions` table**: In `conversions_with_relevance`, **the same conversion event will appear multiple times** if a conversion is determined to be relevant to multiple campaigns, engagement scopes, or brand halo types.

## Purpose and Use Cases

- **Custom attribution modeling** for ASIN and pixel conversions
- **Cross-campaign attribution** analysis
- **Brand halo effect** measurement
- **Campaign-level conversion attribution** with engagement scope details

## Table Schema

### Advertiser Setup

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| advertiser | STRING | Dimension | Advertiser name. | LOW |
| advertiser_id | LONG | Dimension | Advertiser ID. | LOW |
| advertiser_timezone | STRING | Dimension | Time zone of the advertiser. | LOW |

### Campaign Setup

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| campaign | STRING | Dimension | Campaign name. | LOW |
| campaign_budget_amount | LONG | Dimension | Campaign budget amount (millicents). | LOW |
| campaign_end_date | DATE | Dimension | Campaign end date in the advertiser time zone. | LOW |
| campaign_end_date_utc | DATE | Dimension | Campaign end date in UTC | LOW |
| campaign_end_dt | TIMESTAMP | Dimension | Campaign end timestamp in the advertiser time zone. | LOW |
| campaign_end_dt_utc | TIMESTAMP | Dimension | Campaign end timestamp in UTC | LOW |
| campaign_id | LONG | Dimension | Campaign ID. | LOW |
| campaign_id_internal | LONG | Dimension | The globally unique internal campaign ID. | INTERNAL |
| campaign_id_string | STRING | Dimension | Campaign ID as a string data_type, covers DSP and Sponsored Advertising campaign objects. | LOW |
| campaign_sales_type | STRING | Dimension | Campaign sales type | LOW |
| campaign_source | STRING | Dimension | Campaign source. | LOW |
| campaign_start_date | DATE | Dimension | Campaign start date in the advertiser time zone. | LOW |
| campaign_start_date_utc | DATE | Dimension | Campaign start date in UTC. | LOW |
| campaign_start_dt | TIMESTAMP | Dimension | Campaign start timestamp in the advertiser time zone. | LOW |
| campaign_start_dt_utc | TIMESTAMP | Dimension | Campaign start timestamp in UTC. | LOW |
| targeting | STRING | Dimension | The keyword used by advertiser for targeting. | LOW |

### Conversion Info

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| conversion_id | STRING | Dimension | Unique identifier of the conversion event. In the dataset conversions, each row has a unique conversion_id. In the dataset conversions_with_relevance, the same conversion event will appear multiple times if a conversion is determined to be relevant to multiple campaigns, engagement scopes, or brand halo types. | VERY_HIGH |
| conversions | LONG | Metric | Conversion count. | NONE |
| engagement_scope | STRING | Dimension | The engagement scope between the campaign setup and the conversion. Possible values for this column are PROMOTED, BRAND_HALO, and null. See also the definition for halo_code. The engagement_scope will always be 'PROMOTED' for pixel conversions (when event_category = 'pixel'). | LOW |
| event_category | STRING | Dimension | For ASIN conversions, the event_category is the high level category of the conversion event, either 'purchase' or 'website'. Examples of ASIN conversions when event_category = 'website' include: detail page views, add to wishlist, or the first Subscribe and Save order. For search conversions (when event_subtype = 'searchConversion'), the event_category is always 'website'. For pixel conversions, this field is always 'pixel'. | LOW |
| event_date | DATE | Dimension | Date of the conversion event in the advertiser time zone. | LOW |
| event_date_utc | DATE | Dimension | Date of the conversion event in UTC. | LOW |
| event_day | INTEGER | Dimension | Day of the month of the conversion event in the advertiser time zone. | LOW |
| event_day_utc | INTEGER | Dimension | Day of the month of the conversion event in UTC. | LOW |
| event_dt | TIMESTAMP | Dimension | Timestamp of the conversion event in the advertiser time zone. | MEDIUM |
| event_dt_hour | TIMESTAMP | Dimension | Timestamp of the conversion event in the advertiser time zone truncated to the hour. | LOW |
| event_dt_hour_utc | TIMESTAMP | Dimension | Timestamp of the conversion event in UTC truncated to the hour. | LOW |
| event_dt_utc | TIMESTAMP | Dimension | Timestamp of the conversion event in UTC. | MEDIUM |
| event_hour | INTEGER | Dimension | Hour of the day of the conversion event in the advertiser time zone. | LOW |
| event_hour_utc | INTEGER | Dimension | Hour of the day of the conversion event in UTC. | LOW |
| event_source | STRING | Dimension | System that generated the conversion event. | VERY_HIGH |
| event_subtype | STRING | Dimension | Subtype of the conversion event. For ASIN conversions, the examples of event_subtype include: 'alexaSkillEnable', 'babyRegistry', 'customerReview', 'detailPageView', 'order', 'shoppingCart', 'snsSubscription', 'weddingRegistry', 'wishList'. For search conversions, event_subtype is always 'searchConversion'. For pixel conversions, the numeric ID of the event_subtype is provided. | LOW |
| event_type | STRING | Dimension | Type of the conversion event. | LOW |
| event_type_class | STRING | Dimension | For ASIN conversions, the event_type_class is the High level classification of the event type, e.g. consideration, conversion, etc. This field will be blank for pixel conversions (when event_category = 'pixel') and search conversions (when event_subtype = 'searchConversion'). | LOW |
| event_type_description | STRING | Dimension | Human-readable description of the conversion event. For ASIN conversions, examples include: 'add to baby registry', 'Add to Shopping Cart', 'add to wedding registry', 'add to wishlist', 'Customer Reviews Page', 'New SnS Subscription', 'Product detail page viewed', 'Product purchased'. This field will be blank for search conversions (when event_subtype = 'searchConversion'). For pixel conversions (when event_category = 'pixel'), the event_type_description will include additional information about the pixel based on information provided as part of the campaign setup. | LOW |
| halo_code | STRING | Dimension | The halo code between the campaign and conversion. Possible values for this column are TRACKED_ASIN, VARIATIONAL_ASIN, BRAND_KEYWORD, CATEGORY_KEYWORD, BRAND_MARKETPLACE, BRAND_GL_PRODUCT, BRAND_CATEGORY, BRAND_SUBCATEGORY, and null. See also the definition for engagement_scope. The halo_code will be NULL for pixel conversions (when event_category = 'pixel'). | LOW |
| marketplace_id | INTEGER | Dimension | Marketplace ID of where the conversion event occurred. | INTERNAL |
| marketplace_name | STRING | Dimension | Name of the marketplace where the conversion event occurred. Example values are online marketplaces such as AMAZON.COM, AMAZON.CO.UK. Or in-store marketplaces, such as WHOLE_FOODS_MARKET_US or AMAZON_FRESH_STORES_US. | LOW |
| new_to_brand | BOOLEAN | Dimension | True if the user was new to the brand. | LOW |
| tracked_asin | STRING | Dimension | The dimension tracked_asin is the tracked Amazon Standard Identification Number, which is either the promoted or brand halo ASIN. When the tracked_item results in a purchase conversion, the tracked_asin will be populated in this column, in addition to being tracked in the tracked_item column with the same ASIN value. The tracked_asin is populated only if the event_category = 'purchase'. | LOW |
| tracked_item | STRING | Dimension | Each campaign can track zero or more items. Depending on the type of campaign, these items might be ASINs, pixel IDs, DSP ad-attributed branded search keywords or apps. The tracked items for a campaign are the basis for which we determine which conversion events are sent to each AMC instance. | LOW |
| user_id | STRING | Dimension | User ID. | VERY_HIGH |
| conversion_event_source | STRING | Dimension | Source through which the conversion event was sent to Amazon DSP | LOW |
| conversion_event_name | STRING | Dimension | Advertiser defined name for the conversion event | LOW |
| off_amazon_conversion_value | LONG | Metric | Value of off Amazon non-purchase conversions. Value is unitless and advertiser defined. | NONE |

### Purchase Info

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| purchase_currency | STRING | Dimension | ISO currency code of the purchase order. | LOW |
| purchase_unit_price | DECIMAL | Metric | Unit price of the product sold. | NONE |
| total_product_sales | DECIMAL | Metric | Total sales (in local currency) of promoted ASINs and ASINs from the same brands as promoted ASINs purchased by customers on Amazon. | NONE |
| total_units_sold | LONG | Metric | Total quantity of promoted products and products from the same brand as promoted products purchased by customers on Amazon. A campaign can have multiple units sold in a single purchase event. | NONE |
| off_amazon_product_sales | LONG | Metric | Sales amount for off-Amazon purchase conversions | NONE |
| combined_sales | LONG | Metric | Sum of total_product_sales (Amazon product sales) and off_amazon_product_sales | NONE |

## Key Concepts and Attribution Framework

### Record Multiplication
**Critical Understanding**: Unlike the base `conversions` table where each conversion appears once, in `conversions_with_relevance`:
- **Same conversion = Multiple rows** if relevant to multiple campaigns
- **Same conversion = Multiple rows** if has different engagement scopes (PROMOTED vs BRAND_HALO)
- **Same conversion = Multiple rows** if matches different halo codes

### Engagement Scope
Defines the relationship between campaign and conversion:

- **PROMOTED**: Direct attribution to promoted ASINs/items
- **BRAND_HALO**: Attribution to brand halo effects (same brand, different ASIN)
- **NULL**: No specific engagement scope identified

### Halo Code Classification
More granular attribution than engagement_scope:

#### Direct Attribution
- **TRACKED_ASIN**: Exact ASIN promoted in campaign
- **VARIATIONAL_ASIN**: Variant of promoted ASIN (size, color, etc.)

#### Brand Halo Attribution
- **BRAND_KEYWORD**: Branded search keyword attribution
- **CATEGORY_KEYWORD**: Category keyword attribution
- **BRAND_MARKETPLACE**: General brand marketplace activity
- **BRAND_GL_PRODUCT**: Brand global product attribution
- **BRAND_CATEGORY**: Brand category-level attribution
- **BRAND_SUBCATEGORY**: Brand subcategory attribution

### Event Categories Extended

#### ASIN Conversions
- **Purchase** (`event_category = 'purchase'`): Product purchases
- **Website** (`event_category = 'website'`): Browsing activities

#### Pixel Conversions
- **Pixel** (`event_category = 'pixel'`): Off-Amazon conversion events
- Always have `engagement_scope = 'PROMOTED'`
- Always have `halo_code = NULL`

#### Search Conversions
- **Website** (`event_category = 'website'`) with `event_subtype = 'searchConversion'`
- Branded search keyword attribution

## Common Query Patterns

### Campaign Attribution Analysis
```sql
-- Attribution breakdown by engagement scope
SELECT 
    campaign,
    engagement_scope,
    COUNT(*) as conversions,
    SUM(total_product_sales) as attributed_sales
FROM conversions_with_relevance
WHERE event_category = 'purchase'
GROUP BY campaign, engagement_scope;
```

### Brand Halo Analysis
```sql
-- Detailed halo effect breakdown
SELECT 
    campaign,
    halo_code,
    COUNT(*) as conversions,
    SUM(combined_sales) as total_sales,
    AVG(purchase_unit_price) as avg_unit_price
FROM conversions_with_relevance
WHERE event_category = 'purchase'
    AND engagement_scope = 'BRAND_HALO'
GROUP BY campaign, halo_code;
```

### Cross-Campaign Attribution
```sql
-- Find conversions attributed to multiple campaigns
WITH conversion_campaigns AS (
    SELECT 
        conversion_id,
        COUNT(DISTINCT campaign_id) as campaign_count,
        STRING_AGG(DISTINCT campaign, ', ') as attributed_campaigns
    FROM conversions_with_relevance
    GROUP BY conversion_id
)
SELECT * FROM conversion_campaigns
WHERE campaign_count > 1;
```

### Pixel vs ASIN Performance
```sql
-- Compare pixel vs ASIN conversion performance
SELECT 
    event_category,
    COUNT(*) as conversions,
    SUM(COALESCE(combined_sales, off_amazon_conversion_value)) as total_value
FROM conversions_with_relevance
GROUP BY event_category;
```

## Custom Attribution Modeling

### Deduplication Considerations
```sql
-- Count unique conversions (avoid double-counting)
SELECT 
    COUNT(DISTINCT conversion_id) as unique_conversions,
    COUNT(*) as total_attribution_records
FROM conversions_with_relevance;

-- Campaign-level unique conversions
SELECT 
    campaign,
    COUNT(DISTINCT conversion_id) as unique_conversions
FROM conversions_with_relevance
GROUP BY campaign;
```

### Attribution Weight Distribution
```sql
-- Understand attribution distribution per conversion
WITH attribution_depth AS (
    SELECT 
        conversion_id,
        COUNT(*) as attribution_count,
        STRING_AGG(DISTINCT engagement_scope, ', ') as scopes,
        STRING_AGG(DISTINCT halo_code, ', ') as halo_types
    FROM conversions_with_relevance
    GROUP BY conversion_id
)
SELECT 
    attribution_count,
    COUNT(*) as conversions_with_this_depth,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM attribution_depth
GROUP BY attribution_count
ORDER BY attribution_count;
```

## Best Practices

### Query Performance
- **Filter early**: Use campaign_id, event_category, or date filters in WHERE clauses
- **Understand multiplicity**: Account for record multiplication in aggregations
- **Use DISTINCT**: Apply DISTINCT conversion_id when counting unique conversions

### Attribution Analysis
- **Separate direct vs halo**: Analyze PROMOTED vs BRAND_HALO separately
- **Weight attribution**: Consider fractional attribution for conversions with multiple campaigns
- **Validate totals**: Cross-check with base conversions table for data validation

### Campaign Optimization
- **Halo effect measurement**: Use halo_code to understand brand impact beyond direct attribution
- **Cross-campaign coordination**: Identify overlapping attribution for budget optimization
- **Pixel integration**: Combine ASIN and pixel conversions for full-funnel analysis

## Relationship to Other Tables

- **Base conversions**: Contains same conversion events but without campaign attribution details
- **Traffic tables**: Join on user_id and campaign_id to connect exposure to conversion
- **Campaign tables**: Natural joins on campaign_id for campaign metadata
- **Data consistency**: Unique conversion counts should match base conversions table

## Aggregation Threshold Notes

- **NONE**: No aggregation threshold restrictions
- **LOW**: Standard low threshold applies  
- **MEDIUM**: Medium aggregation threshold - use caution in small segments
- **VERY_HIGH**: Very high threshold - cannot be included in final SELECT statements but can be used in CTEs for aggregation
- **INTERNAL**: Internal use only - not available for customer queries