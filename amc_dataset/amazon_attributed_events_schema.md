# Amazon Attributed Events Tables Schema

## Overview

**Data Sources:** 
- `amazon_attributed_events_by_conversion_time`
- `amazon_attributed_events_by_traffic_time`

These tables both contain pairs of traffic and conversion events. "Traffic events" are impressions and clicks. "Conversion events" include purchases, various interactions with Amazon website, such as detailed page views and pixel fires. Each conversion event in the table is attributed to its corresponding traffic event.

## Critical Table Differences

⚠️ **Important**: While the tables include the same metrics and dimensions, they differ with respect to the set of events that are contained within.

### amazon_attributed_events_by_conversion_time
- **Conversion events** all happened within the time window the query is run over
- **Traffic events** the conversions were attributed to may happen up to **14 days before** the time period for the query
- **Amazon DSP default**: This matches Amazon DSP reporting logic (recommended for DSP analysis)
- **Use case**: Standard conversion reporting where you want conversions that occurred in a specific period

### amazon_attributed_events_by_traffic_time  
- **Traffic events** all happened within the time window for the query
- **Conversion events** may have occurred up to **30 days after** the time window
- **Dynamic results**: Output may change over time as more conversion data becomes available
- **Use case**: Campaign performance analysis focused on traffic delivery periods

## Multi-Product Coverage

These tables include data from multiple Amazon Ads products if your instance includes advertisers from multiple sources:

- **Amazon DSP**: `ad_product_type = NULL`
- **Sponsored Products**: `ad_product_type = 'sponsored_products'`
- **Sponsored Brands**: `ad_product_type = 'sponsored_brands'`
- **Sponsored Display**: `ad_product_type = 'sponsored_display'`
- **Sponsored Television**: `ad_product_type = 'sponsored_television'`

## Table Schema

*Note: Due to the extensive schema (200+ fields), key fields are highlighted below. Both tables share the same schema.*

### Core Attribution Fields

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| ad_product_type | STRING | Dimension | Type of Amazon Ads ad product responsible for the traffic event to which the conversion is attributed. This field helps distinguish between individual sponsored ads products and Amazon DSP. Possible values include: 'sponsored_products', 'sponsored_brands', 'sponsored_display', 'sponsored_television', and NULL (which represents Amazon DSP events). | LOW |
| conversions | LONG | Dimension | The count of conversion events. This field always contains a value of 1, allowing you to calculate conversion totals for the records selected in your query. | LOW |
| impressions | LONG | Dimension | Count of impressions. For each conversion record, this field indicates whether the conversion was attributed to an ad view. Possible values: '1' (attributed to ad view) or '0' (not attributed to ad view). | LOW |
| clicks | LONG | Metric | Count of clicks. For each conversion record, this field indicates whether the conversion was attributed to an ad click. Possible values: '1' (attributed to ad click) or '0' (not attributed to ad click). | NONE |

### Campaign Information

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| advertiser | STRING | Dimension | Name of the business entity running advertising campaigns on Amazon Ads. | LOW |
| campaign | STRING | Dimension | Name of the Amazon Ads campaign to which the conversion event is attributed. | LOW |
| campaign_id | LONG | Dimension | The ID of the Amazon Ads campaign associated with the conversion event. | LOW |
| line_item | STRING | Dimension | Name of the line item to which the conversion is attributed. | LOW |
| line_item_id | LONG | Dimension | ID of the line item to which the conversion is attributed. | LOW |

### Conversion Event Details

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| conversion_event_category | STRING | Dimension | High-level category of the conversion event. Possible values include: 'website' (browsing event on Amazon), 'purchase' (purchase event on Amazon), and 'off-Amazon'. | LOW |
| conversion_event_subtype | STRING | Dimension | Subtype of the conversion event. For on-Amazon: 'detailPageView', 'shoppingCart', 'order', etc. For off-Amazon: numeric values like '134', '140', '141'. | LOW |
| conversion_event_date | DATE | Dimension | Date of the conversion event in advertiser timezone. | LOW |
| conversion_event_dt | TIMESTAMP | Dimension | Timestamp of the conversion event in advertiser timezone. | MEDIUM |

### Traffic Event Details

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| traffic_event_subtype | STRING | Dimension | Type of traffic event that led to the conversion. Possible values include: 'AD_IMP' (ad view event) and 'AD_CLICK' (ad click event). | LOW |
| traffic_event_date | DATE | Dimension | Date of the traffic event in advertiser timezone. | NONE |
| traffic_event_dt | TIMESTAMP | Dimension | Timestamp of the traffic event in advertiser timezone. | MEDIUM |
| impression_date | DATE | Dimension | Date of the impression event in advertiser timezone (populated for view-attributed conversions). | LOW |
| click_date | DATE | Dimension | Date of the click event in advertiser timezone (populated for click-attributed conversions). | LOW |

### Sales and Performance Metrics

#### Direct Product Performance
| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| product_sales | DECIMAL(38, 4) | Metric | The sales (in local currency) of promoted ASINs purchased on Amazon, attributed to an ad view or click. | LOW |
| purchases | LONG | Metric | The number of purchases of promoted ASINs on Amazon, attributed to an ad view or click. | NONE |
| units_sold | LONG | Metric | The quantity of promoted ASINs purchased on Amazon, attributed to an ad view or click. | NONE |
| detail_page_view | LONG | Metric | The number of detail page views on advertised ASINs, attributed to an ad view or click. | NONE |
| add_to_cart | LONG | Metric | The number of times a promoted ASIN was added to a customer's cart on Amazon, attributed to an ad view or click. | NONE |

#### Brand Halo Performance
| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| brand_halo_product_sales | DECIMAL(38, 4) | Metric | The sales (in local currency) of brand halo ASINs purchased on Amazon, attributed to an ad view or click. Brand halo ASINs are products from the same brand as the ASINs promoted by the campaign. | NONE |
| brand_halo_purchases | LONG | Metric | The number of purchases of brand halo ASINs on Amazon, attributed to an ad view or click. | NONE |
| brand_halo_units_sold | LONG | Metric | The quantity of brand halo ASINs purchased on Amazon, attributed to an ad view or click. | NONE |

#### Total Performance (Direct + Brand Halo)
| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| total_product_sales | DECIMAL(38, 4) | Dimension | The sales (in local currency) of promoted and brand halo ASINs purchased on Amazon, attributed to an ad view or click. Note: total_product_sales = product_sales + brand_halo_product_sales. | LOW |
| total_purchases | LONG | Dimension | The number of purchases of promoted and brand halo ASINs on Amazon, attributed to an ad view or click. Note: total_purchases = purchases + brand_halo_purchases. | NONE |
| total_units_sold | LONG | Dimension | The quantity of promoted and brand halo ASINs purchased on Amazon, attributed to an ad view or click. Note: total_units_sold = units_sold + brand_halo_units_sold. | LOW |

#### New-to-Brand Metrics
| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| new_to_brand | BOOLEAN | Metric | Boolean value indicating whether the customer is new-to-brand (not purchased from brand in previous 12 months). | NONE |
| new_to_brand_product_sales | DECIMAL(38, 4) | Metric | The sales (in local currency) of promoted ASINs purchased by new-to-brand customers. | NONE |
| new_to_brand_total_product_sales | DECIMAL(38, 4) | Metric | The sales (in local currency) of promoted and brand halo ASINs purchased by new-to-brand customers. | NONE |

### Off-Amazon Conversions

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| off_amazon_product_sales | LONG | Metric | Product sales amount associated with the off-Amazon conversion event. | NONE |
| off_amazon_conversion_value | LONG | Metric | The non-monetary value assigned to non-purchase conversion events that occur off Amazon. | NONE |
| combined_sales | LONG | Metric | The total sales amount combining both on-Amazon product sales and off-Amazon product sales. combined_sales = total_product_sales + off_amazon_product_sales. | NONE |

### Search and Targeting

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| customer_search_term | STRING | Dimension | Search term entered by a shopper on Amazon that led to the traffic event. | LOW |
| targeting | STRING | Dimension | Keyword used by the advertiser for targeting on sponsored ads campaigns. | LOW |
| match_type | STRING | Dimension | Type of match between targeting keyword and customer search term. Possible values: 'BROAD', 'PHRASE', 'EXACT', and NULL. | MEDIUM |

## Key Concepts and Usage

### Attribution Framework
- **View Attribution**: Conversions credited to ad impressions (view-through conversions)
- **Click Attribution**: Conversions credited to ad clicks (click-through conversions)
- **Attribution Windows**: Determined by campaign settings, not modifiable in AMC
- **Cross-Product Attribution**: Single table covers DSP, Sponsored Products, Sponsored Brands, etc.

### Performance Metrics Structure
Each metric often has three versions:
- **Base metric**: Total (view + click attributed)
- **_clicks**: Only click-attributed conversions
- **_views**: Only view-attributed conversions

Example: `purchases`, `purchases_clicks`, `purchases_views`

### Brand Halo Effects
- **Direct**: Performance of promoted ASINs
- **Brand Halo**: Performance of other products from same brand
- **Total**: Combined direct + brand halo performance
- **New-to-Brand**: Subset focusing on customer acquisition

### Modeled Conversions
- Available in these tables for improved measurement
- Reporting below ad line level shows as NULL for modeled events
- To exclude: Join to user identifiers or dimensions below ad line level
- **Note**: All NULL user_id rows are not necessarily modeled

## Common Query Patterns

### Basic Attribution Analysis
```sql
-- Conversion attribution breakdown
SELECT 
    campaign,
    SUM(CASE WHEN impressions = 1 THEN conversions ELSE 0 END) as view_conversions,
    SUM(CASE WHEN clicks = 1 THEN conversions ELSE 0 END) as click_conversions,
    SUM(conversions) as total_conversions
FROM amazon_attributed_events_by_conversion_time
GROUP BY campaign;
```

### Multi-Product Performance
```sql
-- Performance by ad product type
SELECT 
    COALESCE(ad_product_type, 'Amazon DSP') as product_type,
    SUM(total_purchases) as purchases,
    SUM(total_product_sales) as sales
FROM amazon_attributed_events_by_conversion_time
WHERE conversion_event_category = 'purchase'
GROUP BY ad_product_type;
```

### Brand Halo Analysis
```sql
-- Direct vs Brand Halo performance
SELECT 
    campaign,
    SUM(product_sales) as direct_sales,
    SUM(brand_halo_product_sales) as halo_sales,
    SUM(total_product_sales) as total_sales,
    CASE 
        WHEN SUM(total_product_sales) > 0 
        THEN SUM(brand_halo_product_sales) * 100.0 / SUM(total_product_sales)
        ELSE 0 
    END as halo_percentage
FROM amazon_attributed_events_by_conversion_time
WHERE conversion_event_category = 'purchase'
GROUP BY campaign;
```

### Time-to-Conversion Analysis
```sql
-- Days between traffic and conversion
SELECT 
    campaign,
    DATE_DIFF(conversion_event_date, traffic_event_date, DAY) as days_to_conversion,
    COUNT(*) as conversions
FROM amazon_attributed_events_by_conversion_time
WHERE traffic_event_date IS NOT NULL 
    AND conversion_event_date IS NOT NULL
GROUP BY campaign, days_to_conversion
ORDER BY campaign, days_to_conversion;
```

### New-to-Brand Performance
```sql
-- Customer acquisition analysis
SELECT 
    campaign,
    new_to_brand,
    SUM(total_purchases) as purchases,
    SUM(total_product_sales) as sales,
    AVG(purchase_unit_price) as avg_order_value
FROM amazon_attributed_events_by_conversion_time
WHERE conversion_event_category = 'purchase'
    AND new_to_brand IS NOT NULL
GROUP BY campaign, new_to_brand;
```

## Table Selection Guidelines

### Use amazon_attributed_events_by_conversion_time when:
- **Standard reporting**: Match Amazon DSP business logic
- **Conversion-focused analysis**: Want conversions from specific time period
- **Campaign performance review**: Measuring results for specific periods
- **Budget allocation**: Understanding conversion delivery by time period

### Use amazon_attributed_events_by_traffic_time when:
- **Campaign delivery analysis**: Focus on traffic served in specific period
- **Media planning**: Understanding traffic performance and future conversions
- **Real-time optimization**: Monitoring recent traffic performance
- **Attribution modeling**: Building custom attribution models

## Best Practices

### Query Optimization
- **Filter by ad_product_type** early to focus on specific ad products
- **Use conversion_event_category** to separate purchase vs website events
- **Apply date filters** appropriate to your table choice
- **Consider modeled events** when interpreting user-level data

### Attribution Analysis
- **Account for attribution windows** when analyzing time-to-conversion
- **Separate view vs click attribution** for channel analysis
- **Include brand halo effects** for complete performance picture
- **Monitor new-to-brand metrics** for customer acquisition insights

### Data Quality
- **Validate totals** between direct, halo, and total metrics
- **Check for NULL values** in key attribution fields
- **Understand data availability** windows for each table
- **Account for dynamic results** when using traffic_time table

## Data Availability Notes

### Historical Data
- **Sponsored Brands**: Available from December 2, 2022
- **Backfill period**: 0-28 days before instance creation (varies by instance age)
- **Keywords and search terms**: 13 months or instance creation date, whichever is sooner

### Cross-Product Considerations
- **Campaign uniqueness**: Campaigns likely unique to each ad product
- **ID differences**: DSP vs Sponsored Ads use different ID formats
- **Feature availability**: Some fields only apply to specific ad products

## Aggregation Threshold Notes

- **NONE**: No aggregation threshold restrictions
- **LOW**: Standard low threshold applies
- **MEDIUM**: Medium aggregation threshold - use caution in small segments
- **HIGH**: High aggregation threshold - significant restrictions on granular queries  
- **VERY_HIGH**: Very high threshold - cannot be included in final SELECT statements but can be used in CTEs for aggregation