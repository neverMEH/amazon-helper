# conversions Data Source Schema

## Overview

**Data Source:** `conversions`

The conversions table contains AMC conversion events. Ad-attributed conversions for ASINs tracked to an Amazon DSP or sponsored ads campaigns and pixel conversions are included. Conversions are ad-attributed if a user was served a traffic event within the **28-day period** prior to the conversion event.

## Table Schema

| Field | Data Type | Metric / Dimension | Definition | Aggregation Threshold |
|-------|-----------|-------------------|------------|----------------------|
| combined_sales | LONG | Metric | Sum of total_product_sales + off_Amazon_product_sales | NONE |
| conversions | LONG | Metric | The count of conversion events. This field always contains a value of 1, allowing you to calculate conversion totals for the records selected in your query. Conversion events can include on-Amazon activities like purchases and detail page views, as well as off-Amazon events measured through Events Manager. Possible values for this field are: '1' (the record represents a conversion event). | NONE |
| conversion_event_name | STRING | Dimension | The advertiser's name of the conversion definition. | LOW |
| conversion_event_source_name | STRING | Dimension | The source of the advertiser-provided conversion data. | LOW |
| conversion_id | STRING | Dimension | Unique identifier of the conversion event. In the conversions table, each row has a unique conversion_id value. | VERY_HIGH |
| event_category | STRING | Dimension | High-level category of the conversion event. For ASIN conversions, this categorizes whether the event was a purchase or website browsing interaction. Website events include activities like detail page views, add to wishlist actions, and first Subscribe and Save orders. For conversions measured through Events Manager, this field is always 'off-Amazon'. Possible values include: 'purchase', 'website', and 'off-Amazon'. | LOW |
| event_date_utc | DATE | Dimension | Date of the conversion event in Coordinated Universal Time (UTC) timezone. Example value: '2025-01-01'. | LOW |
| event_day_utc | INTEGER | Dimension | Day of month when the conversion event occurred in Coordinated Universal Time (UTC). Example value: '1'. | LOW |
| event_dt_hour_utc | TIMESTAMP | Dimension | Timestamp of the conversion event in Coordinated Universal Time (UTC) truncated to hour. Example value: '2025-01-01T00:00:00.000Z'. | LOW |
| event_dt_utc | TIMESTAMP | Dimension | Timestamp of the conversion event in Coordinated Universal Time (UTC). Example value: '2025-01-01T00:00:00.000Z'. | MEDIUM |
| event_hour_utc | INTEGER | Dimension | Hour of the day (0-23) when the conversion event occurred in Coordinated Universal Time (UTC) timezone. Example value: '0'. | LOW |
| event_subtype | STRING | Dimension | Subtype of the conversion event. This field provides additional detail about the subtype of conversion event that occurred, such as whether it represents viewing a product's detail page on Amazon.com or completing a purchase on an advertiser's website. For on-Amazon conversion events, this field contains human-readable values, while off-Amazon events measured via Events Manager are represented by numeric values. Possible values include: 'detailPageView', 'shoppingCart', 'order', 'searchConversion', 'wishList', 'babyRegistry', 'weddingRegistry', 'customerReview' for on-Amazon events, and numeric values like '134', '140', '141' for off-Amazon events. | LOW |
| event_type | STRING | Dimension | Type of conversion event. Conversion events in AMC can include both on-Amazon events (like purchases and detail page views) and off-Amazon events (like website visits and app installs measured through Events Manager). This field will always have a value of 'CONVERSION'. | LOW |
| event_type_class | STRING | Dimension | Classification of conversion events based on customer behavior. This field categorizes conversion events into consideration events (like detail page views) versus actual conversion events (like purchases). Possible values include: 'consideration', 'conversion', and NULL. | LOW |
| event_type_description | STRING | Dimension | Human-readable description of the conversion event type. Conversion events can occur on Amazon (like product purchases or detail page views) or off Amazon (like brand site page views or in-store transactions measured via Events Manager). Example values: 'Product purchased', 'Add to Shopping Cart', 'Product detail page viewed'. | LOW |
| marketplace_id | INTEGER | Dimension | ID of the marketplace where the conversion event occurred. A marketplace represents a regional Amazon storefront where customers can make purchases (for example, Amazon.com, Amazon.co.uk). | LOW |
| marketplace_name | STRING | Dimension | Name of the marketplace where the conversion event occurred. A marketplace can be an online shopping site (like Amazon.com) or a physical retail location (like Amazon Fresh stores). This field helps distinguish between conversions that happen on different Amazon online marketplaces versus those that occur in Amazon's physical retail locations. Example values include: 'AMAZON.COM', 'AMAZON.CO.UK', 'WHOLE_FOODS_MARKET_US', and 'AMAZON_FRESH_STORES_US'. | LOW |
| new_to_brand | BOOLEAN | Dimension | Boolean value indicating whether the customer associated with a purchase event is new-to-brand. A customer is considered new-to-brand if they have not purchased from the brand in the previous 12 months. This field is only applicable for purchase events. Possible values for this field are: 'true', 'false'. | LOW |
| no_3p_trackers | BOOLEAN | Dimension | Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Possible values for this field are: 'true', 'false'. | NONE |
| off_amazon_conversion_value | LONG | Metric | Non monetary "value" of conversion for non-purchase conversions | NONE |
| off_amazon_product_sales | LONG | Metric | "Value" of purchase conversions provided via Conversion Builder | NONE |
| purchase_currency | STRING | Dimension | ISO currency code of the purchase. Currency codes follow the ISO 4217 standard for representing currencies (e.g., USD for US Dollar). Example value: 'USD'. | LOW |
| purchase_unit_price | STRING | Dimension | The unit price of the product sold for on-Amazon purchase events, in local currency. This field represents the price per individual unit, not the total purchase price which may include multiple units. Example value: '29.99'. | NONE |
| total_product_sales | DECIMAL | Metric | Product sales (in local currency) for on-Amazon purchase events. Example value: '12.99'. | NONE |
| total_units_sold | LONG | Metric | Units sold for on-Amazon purchase events. Example value: '3'. | NONE |
| tracked_asin | STRING | Dimension | The ASIN of the conversion event. An ASIN (Amazon Standard Identification Number) is a unique 10-character identifier assigned to products sold on Amazon. ASINs that appear in this field were either directly promoted by the campaign or are products from the same brand as the promoted ASINs. This field will only be for on-Amazon purchases (event_category = 'purchase'); for other conversion types, this field will be NULL. When this field is populated, tracked_item will have the same value. Example value: 'B01234ABCD'. | LOW |
| tracked_item | STRING | Dimension | Identifier for the conversion event item. The value in this field depends on the subtype of the conversion event. For ASIN-related conversions on Amazon such as purchases, detail page views, add to cart events, this field will contain the ASIN of the product. For branded search conversions on Amazon, this field will contain the ad-attributed branded search keyword. For off-Amazon conversions, this field will contain the ID of the conversion definition. Note that when tracked_asin is populated, the same value will appear in tracked_item. | LOW |
| user_id | STRING | Dimension | Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERY_HIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT user_id). | VERY_HIGH |
| user_id_type | STRING | Dimension | Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for a conversion event, the 'user_id' and 'user_id_type' values for that record will be NULL. Possible values include: 'adUserId', 'sisDeviceId', 'adBrowserId', and NULL. | LOW |

## Key Concepts and Event Types

### Attribution Window
- **28-day attribution**: Conversions are attributed to ads if user was served a traffic event within 28 days prior to conversion
- **Cross-channel attribution**: Includes both Amazon DSP and Sponsored Ads campaigns

### Event Categories

#### On-Amazon Events
**Purchase Events** (`event_category = 'purchase'`)
- Actual product purchases on Amazon
- Include sales values, units sold, and ASIN information
- New-to-brand tracking available

**Website Events** (`event_category = 'website'`)
- Detail page views
- Add to cart actions
- Wishlist additions
- Registry additions
- Customer reviews
- Branded search conversions

#### Off-Amazon Events
**Off-Amazon Conversions** (`event_category = 'off-Amazon'`)
- Website visits and interactions
- App installs and engagement
- In-store transactions
- Custom conversion events via Events Manager

### Event Classification
- **Consideration** (`event_type_class = 'consideration'`): Upper-funnel activities (detail page views, searches)
- **Conversion** (`event_type_class = 'conversion'`): Lower-funnel activities (purchases, app installs)

## Sales and Value Metrics

### On-Amazon Sales
- **total_product_sales**: Revenue from Amazon purchases in local currency
- **total_units_sold**: Number of units purchased
- **purchase_unit_price**: Price per individual unit
- **purchase_currency**: ISO currency code (USD, EUR, etc.)

### Off-Amazon Sales
- **off_amazon_product_sales**: Purchase value from off-Amazon conversions
- **off_amazon_conversion_value**: Non-monetary value for non-purchase events

### Combined Metrics
- **combined_sales**: Total of on-Amazon + off-Amazon sales

## ASIN and Product Tracking

### ASIN Fields
- **tracked_asin**: ASIN for purchase events only
- **tracked_item**: Universal item identifier (ASIN for products, keyword for searches, etc.)

### Brand Attribution
- Direct product promotion: ASINs directly advertised
- Brand halo: Other products from same brand purchased due to advertising

## Common Query Patterns

### Purchase Analysis
```sql
-- Purchase conversions with sales data
SELECT 
    event_date_utc,
    COUNT(*) as purchase_conversions,
    SUM(total_product_sales) as total_sales,
    SUM(total_units_sold) as total_units,
    AVG(purchase_unit_price) as avg_unit_price
FROM conversions
WHERE event_category = 'purchase'
GROUP BY event_date_utc;
```

### New-to-Brand Analysis
```sql
-- New vs existing customer purchases
SELECT 
    new_to_brand,
    COUNT(*) as conversions,
    SUM(total_product_sales) as sales
FROM conversions
WHERE event_category = 'purchase'
    AND new_to_brand IS NOT NULL
GROUP BY new_to_brand;
```

### Conversion Funnel Analysis
```sql
-- Conversion funnel by event type
SELECT 
    event_subtype,
    event_type_class,
    COUNT(*) as events,
    COUNT(DISTINCT user_id) as unique_users
FROM conversions
WHERE event_category IN ('website', 'purchase')
GROUP BY event_subtype, event_type_class
ORDER BY events DESC;
```

### Cross-Channel Performance
```sql
-- On-Amazon vs Off-Amazon conversions
SELECT 
    event_category,
    COUNT(*) as conversions,
    SUM(COALESCE(total_product_sales, 0)) as amazon_sales,
    SUM(COALESCE(off_amazon_product_sales, 0)) as off_amazon_sales
FROM conversions
GROUP BY event_category;
```

## Event Subtypes Reference

### On-Amazon Event Subtypes
- **detailPageView**: Product page viewed
- **shoppingCart**: Added to cart
- **order**: Purchase completed
- **searchConversion**: Branded search performed
- **wishList**: Added to wishlist
- **babyRegistry**: Added to baby registry
- **weddingRegistry**: Added to wedding registry
- **customerReview**: Customer review written

### Off-Amazon Event Subtypes
- Numeric values (e.g., '134', '140', '141')
- Refer to Events Manager documentation for specific definitions

## Marketplace Coverage

### Online Marketplaces
- **AMAZON.COM**: US marketplace
- **AMAZON.CO.UK**: UK marketplace
- **Other regional Amazon sites**

### Physical Retail
- **WHOLE_FOODS_MARKET_US**: Whole Foods stores
- **AMAZON_FRESH_STORES_US**: Amazon Fresh stores
- **Other Amazon physical retail locations**

## Best Practices

### Attribution Analysis
- Use `user_id` in CTEs for cross-event user journey analysis
- Consider 28-day attribution window when analyzing conversion timing
- Account for both direct and brand halo effects

### Sales Reporting
- Use `combined_sales` for total revenue impact
- Separate on-Amazon vs off-Amazon performance for channel analysis
- Factor in `new_to_brand` for customer acquisition insights

### Event Analysis
- Filter by `event_category` to focus on specific conversion types
- Use `event_type_class` to separate consideration vs conversion events
- Leverage `event_subtype` for granular event analysis

## Aggregation Threshold Notes

- **NONE**: No aggregation threshold restrictions
- **LOW**: Standard low threshold applies
- **MEDIUM**: Medium aggregation threshold - use caution in small segments
- **VERY_HIGH**: Very high threshold - cannot be included in final SELECT statements but can be used in CTEs for aggregation