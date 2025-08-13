# conversions_all Data Source Schema

## Overview

**Data Source:** `conversions_all`

Contains both ad-exposed and non-ad-exposed conversions for tracked ASINs. Conversions are ad-exposed if a user was served a traffic event within the **28-day period** prior to the conversion event.

⚠️ **Important**: This data source is only available for measurement queries through **Paid feature subscription**. However, this data source can be used for AMC Audience creation without a Paid feature subscription.

## Key Distinction from Other Conversion Tables

This table is unique because it includes **both ad-exposed and non-ad-exposed conversions**, allowing for incremental impact analysis and total market understanding.

### Exposure Types

The `exposure_type` field categorizes conversions:
- **ad-exposed**: Conversions that occurred within 28 days after a traffic event
- **non-ad-exposed**: Conversions with no recent ad exposure (baseline/organic)
- **pixel**: Off-Amazon conversions measured via Events Manager

## Table Schema

### Conversion Info

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| conversion_id | STRING | Dimension | Unique identifier of the conversion event. Each row has a unique conversion_id. | VERY_HIGH |
| conversions | LONG | Metric | Conversion count. | NONE |
| exposure_type | STRING | Dimension | Attribution of the conversion. For website and purchase conversions: 'ad-exposed' if conversion happened within 28-days after a traffic event, else 'non-ad-exposed'. For pixel conversions, this field is always 'pixel'. | LOW |
| event_category | STRING | Dimension | For ASIN conversions: 'purchase' or 'website'. For search conversions: always 'website'. For pixel conversions: always 'pixel'. | LOW |
| event_date_utc | DATE | Dimension | Date of the conversion event in UTC. | LOW |
| event_day_utc | INTEGER | Dimension | Day of the month of the conversion event in UTC. | LOW |
| event_dt_hour_utc | TIMESTAMP | Dimension | Timestamp of the conversion event in UTC truncated to the hour. | LOW |
| event_dt_utc | TIMESTAMP | Dimension | Timestamp of the conversion event in UTC. | MEDIUM |
| event_hour_utc | INTEGER | Dimension | Hour of the day of the conversion event in UTC. | LOW |
| event_source | STRING | Dimension | System that generated the conversion event. | VERY_HIGH |
| event_subtype | STRING | Dimension | Subtype of conversion event. For ASIN conversions: 'alexaSkillEnable', 'babyRegistry', 'customerReview', 'detailPageView', 'order', 'shoppingCart', 'snsSubscription', 'weddingRegistry', 'wishList'. For search conversions: 'searchConversion'. For pixel conversions: numeric ID. | LOW |
| event_type | STRING | Dimension | Type of the conversion event. | LOW |
| event_type_class | STRING | Dimension | High level classification: 'consideration', 'conversion', etc. Blank for pixel and search conversions. | LOW |
| event_type_description | STRING | Dimension | Human-readable description of conversion event. Examples: 'Add to Shopping Cart', 'Product purchased', 'Product detail page viewed'. Blank for search conversions. | LOW |
| marketplace_id | INTEGER | Dimension | Marketplace ID where conversion occurred. | INTERNAL |
| marketplace_name | STRING | Dimension | Marketplace name (e.g., 'AMAZON.COM', 'AMAZON.CO.UK', 'WHOLE_FOODS_MARKET_US'). | LOW |
| new_to_brand | BOOLEAN | Dimension | True if the user was new to the brand (no purchase in previous 12 months). | LOW |
| tracked_asin | STRING | Dimension | The tracked ASIN (promoted or brand halo). Only populated for purchase events (event_category = 'purchase'). | LOW |
| tracked_item | STRING | Dimension | Identifier for conversion event item. Can be ASIN, pixel ID, branded search keyword, or app. When tracked_asin is populated, tracked_item has the same value. | LOW |
| user_id | STRING | Dimension | Pseudonymous user identifier. VERY_HIGH aggregation threshold - use in CTEs only. | VERY_HIGH |
| conversion_event_source | STRING | Dimension | Source through which conversion event was sent to Amazon DSP. | LOW |
| conversion_event_name | STRING | Dimension | Advertiser defined name for the conversion event. | LOW |
| sns_subscription_id | STRING | Dimension | Subscribe-and-save subscription ID. | INTERNAL |

### Purchase Info

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| purchase_currency | STRING | Dimension | ISO currency code of the purchase order. | LOW |
| purchase_unit_price | DECIMAL | Metric | Unit price of the product sold. | NONE |
| total_product_sales | DECIMAL | Metric | Total sales (in local currency) of promoted ASINs and ASINs from the same brands as promoted ASINs purchased by customers on Amazon. | NONE |
| total_units_sold | LONG | Metric | Total quantity of promoted products and products from the same brand as promoted products purchased by customers on Amazon. | NONE |
| off_amazon_product_sales | LONG | Metric | Sales amount for off-Amazon purchase conversions. | NONE |
| off_amazon_conversion_value | LONG | Metric | Value of off Amazon non-purchase conversions. Value is unitless and advertiser defined. | NONE |
| combined_sales | LONG | Metric | Sum of total_product_sales (Amazon product sales) and off_amazon_product_sales. | NONE |

## Key Use Cases and Analysis

### Incremental Impact Analysis

The primary value of this table is understanding the incremental impact of advertising by comparing ad-exposed vs non-ad-exposed conversions.

#### Incrementality Calculation
```sql
-- Basic incrementality analysis
SELECT 
    tracked_asin,
    SUM(CASE WHEN exposure_type = 'ad-exposed' THEN conversions ELSE 0 END) as ad_exposed_conversions,
    SUM(CASE WHEN exposure_type = 'non-ad-exposed' THEN conversions ELSE 0 END) as non_ad_exposed_conversions,
    SUM(CASE WHEN exposure_type = 'ad-exposed' THEN total_product_sales ELSE 0 END) as ad_exposed_sales,
    SUM(CASE WHEN exposure_type = 'non-ad-exposed' THEN total_product_sales ELSE 0 END) as non_ad_exposed_sales
FROM conversions_all
WHERE event_category = 'purchase'
    AND tracked_asin IS NOT NULL
GROUP BY tracked_asin;
```

#### Conversion Rate Impact
```sql
-- Compare conversion rates by exposure type
SELECT 
    exposure_type,
    event_type_class,
    COUNT(*) as total_events,
    SUM(CASE WHEN event_category = 'purchase' THEN conversions ELSE 0 END) as purchases,
    CASE 
        WHEN COUNT(*) > 0 
        THEN SUM(CASE WHEN event_category = 'purchase' THEN conversions ELSE 0 END) * 100.0 / COUNT(*)
        ELSE 0 
    END as purchase_conversion_rate
FROM conversions_all
WHERE exposure_type IN ('ad-exposed', 'non-ad-exposed')
GROUP BY exposure_type, event_type_class;
```

### Brand Performance Analysis

#### New-to-Brand Impact
```sql
-- New-to-brand acquisition by exposure type
SELECT 
    exposure_type,
    new_to_brand,
    COUNT(*) as conversions,
    SUM(total_product_sales) as sales,
    AVG(purchase_unit_price) as avg_order_value
FROM conversions_all
WHERE event_category = 'purchase'
    AND new_to_brand IS NOT NULL
    AND exposure_type IN ('ad-exposed', 'non-ad-exposed')
GROUP BY exposure_type, new_to_brand;
```

#### Marketplace Performance
```sql
-- Cross-marketplace exposure impact
SELECT 
    marketplace_name,
    exposure_type,
    SUM(conversions) as total_conversions,
    SUM(total_product_sales) as total_sales
FROM conversions_all
WHERE event_category = 'purchase'
GROUP BY marketplace_name, exposure_type
ORDER BY marketplace_name, total_sales DESC;
```

### Temporal Analysis

#### Time-Based Exposure Patterns
```sql
-- Daily exposure type breakdown
SELECT 
    event_date_utc,
    exposure_type,
    SUM(conversions) as conversions,
    SUM(combined_sales) as total_sales
FROM conversions_all
WHERE event_category = 'purchase'
GROUP BY event_date_utc, exposure_type
ORDER BY event_date_utc, exposure_type;
```

#### Hour-of-Day Analysis
```sql
-- Conversion patterns by hour and exposure
SELECT 
    event_hour_utc,
    exposure_type,
    COUNT(*) as conversion_events,
    AVG(total_product_sales) as avg_sales_per_conversion
FROM conversions_all
WHERE event_category = 'purchase'
    AND exposure_type IN ('ad-exposed', 'non-ad-exposed')
GROUP BY event_hour_utc, exposure_type
ORDER BY event_hour_utc, exposure_type;
```

### Audience Creation

This table can be used for audience creation without a paid subscription:

```sql
-- Create audience of users with ad-exposed purchases
CREATE AUDIENCE high_value_ad_exposed_customers AS
SELECT user_id
FROM conversions_all
WHERE exposure_type = 'ad-exposed'
    AND event_category = 'purchase'
    AND total_product_sales > 100
    AND event_date_utc >= '2025-01-01';
```

### Cross-Channel Analysis

#### On-Amazon vs Off-Amazon
```sql
-- Compare on-Amazon vs off-Amazon conversion patterns
SELECT 
    CASE 
        WHEN event_category IN ('purchase', 'website') THEN 'On-Amazon'
        WHEN event_category = 'pixel' THEN 'Off-Amazon'
        ELSE 'Other'
    END as channel,
    exposure_type,
    SUM(conversions) as total_conversions,
    SUM(COALESCE(total_product_sales, 0)) as amazon_sales,
    SUM(COALESCE(off_amazon_product_sales, 0)) as off_amazon_sales
FROM conversions_all
GROUP BY 
    CASE 
        WHEN event_category IN ('purchase', 'website') THEN 'On-Amazon'
        WHEN event_category = 'pixel' THEN 'Off-Amazon'
        ELSE 'Other'
    END,
    exposure_type;
```

## Understanding Baseline vs Incremental

### Key Metrics for Analysis

1. **Baseline Performance**: Non-ad-exposed conversions represent organic/baseline activity
2. **Total Performance**: Ad-exposed + non-ad-exposed = total brand performance
3. **Incremental Lift**: Ad-exposed conversions above baseline expectations
4. **Exposure Effect**: Differences in behavior between exposed and non-exposed users

### Statistical Considerations

#### Sample Size Requirements
- Ensure sufficient volume in both ad-exposed and non-ad-exposed groups
- Consider seasonality and external factors affecting baseline performance
- Account for user behavior differences between groups

#### Attribution Window Impact
- 28-day window may miss longer-term brand effects
- Consider interaction with other marketing channels
- Evaluate based on typical customer purchase cycles

## Data Quality and Validation

### Validation Queries
```sql
-- Validate exposure type distribution
SELECT 
    exposure_type,
    COUNT(*) as conversion_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM conversions_all
GROUP BY exposure_type;

-- Check for data completeness
SELECT 
    event_date_utc,
    COUNT(CASE WHEN exposure_type = 'ad-exposed' THEN 1 END) as ad_exposed,
    COUNT(CASE WHEN exposure_type = 'non-ad-exposed' THEN 1 END) as non_ad_exposed,
    COUNT(CASE WHEN exposure_type = 'pixel' THEN 1 END) as pixel
FROM conversions_all
WHERE event_date_utc >= '2025-01-01'
GROUP BY event_date_utc
ORDER BY event_date_utc;
```

## Best Practices

### Analysis Guidelines
- **Control for external factors** when comparing exposure types
- **Account for user selection bias** between exposed and non-exposed groups
- **Consider incrementality holistically** across the entire customer journey
- **Validate findings** with other measurement approaches when possible

### Query Optimization
- **Filter by exposure_type** early in queries for performance
- **Use appropriate date ranges** to ensure sufficient sample sizes
- **Leverage user_id in CTEs** for user-level analysis due to aggregation thresholds

### Business Applications
- **Media mix optimization**: Understand true incremental value of advertising
- **Budget allocation**: Allocate spend based on incremental performance
- **Baseline forecasting**: Use non-ad-exposed data for organic projections
- **Audience insights**: Identify differences between exposed and non-exposed customers

## Limitations and Considerations

### Data Scope
- **Tracked ASINs only**: Limited to products being tracked by campaigns
- **28-day attribution window**: May not capture longer-term effects
- **Paid subscription required**: Full analysis capabilities require subscription

### Interpretation Caveats
- **Correlation vs causation**: Ad exposure correlation doesn't prove causation
- **Selection effects**: Exposed users may differ systematically from non-exposed
- **External factors**: Market conditions, seasonality, and other marketing affect baseline

### Technical Limitations
- **User-level analysis**: Limited by VERY_HIGH aggregation thresholds
- **Historical data**: Availability may be limited for older time periods
- **Cross-product tracking**: Focus on ASIN conversions may miss other conversion types

## Aggregation Threshold Notes

- **NONE**: No aggregation threshold restrictions
- **LOW**: Standard low threshold applies
- **MEDIUM**: Medium aggregation threshold - use caution in small segments
- **VERY_HIGH**: Very high threshold - cannot be included in final SELECT statements but can be used in CTEs for aggregation
- **INTERNAL**: Internal use only - not available for customer queries