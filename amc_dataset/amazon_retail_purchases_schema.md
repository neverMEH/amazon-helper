# amazon_retail_purchases Data Source Schema

## Overview

**Data Source:** `amazon_retail_purchases`

The Amazon Retail Purchases (ARP) dataset enables advertisers to analyze **long-term (up to 60 months)** customer purchase behavior and create more comprehensive insights. This dataset provides retail purchase data sourced from Amazon's retail data pipeline rather than advertising data pipeline.

## Availability and Access

### Geographic Coverage
Available for measurement queries through Paid features subscription in:
- **United States**
- **Canada** 
- **Japan**
- **Australia**
- **United Kingdom**
- **France**
- **Germany**
- **Italy**
- **Spain**

⚠️ **Important**: Data from the United Kingdom and European Union (EU) regions will be **excluded from audience creation**.

### Subscription Requirements
- **Paid features subscription**: Required for access
- **Free trial**: 60-day trial available
- **Account setup**: Vendor/Seller Central accounts must be properly associated
- **Data verification**: Scope matches Vendor Central (Distributor View = Manufacturing) or Seller Central (By ASIN Detail report)

## Key Differences from Conversion Datasets

| Aspect | Conversions (CONV) | Amazon Retail Purchases (ARP) |
|--------|-------------------|--------------------------------|
| **Scope of conversion types** | Various conversion event types (purchases, considerations, pixel-based conversions) | Amazon store purchase conversion events only |
| **Scope of events** | Advertising-centric (promoted, brand-halo, brand-owned ASINs) | Entire purchase activity in Amazon store, regardless of advertising |
| **Data pipeline** | Advertising data pipelines; subject to restatements and advertising augmentation | Retail data pipeline; matches Vendor/Seller Central reporting |
| **Historical data** | 13 months | **60 months (5 years)** |
| **Attribution focus** | Ad-attributed events | All retail purchases |

⚠️ **Critical Warning**: The ARP dataset contains 60 months of historical data vs 13 months for advertising datasets. Exercise caution when joining retail purchase data with other AMC datasets to avoid mismatched time windows.

## Table Schema

| Field Name | Data Type | Description | Aggregation Threshold |
|------------|-----------|-------------|----------------------|
| asin | STRING | Amazon Standard Identification Number. Unique identifier for all products sold on Amazon. | LOW |
| asin_brand | STRING | ASIN item merchant brand name. | LOW |
| asin_name | STRING | ASIN item name. | LOW |
| asin_parent | STRING | The parent ASIN of this ASIN for the retail event. | LOW |
| currency_code | STRING | ISO currency code of the retail event. | LOW |
| event_id | STRING | Unique identifier of the retail event record. Each row has a unique event_id. Can have many-to-one relationship with purchase_id. | VERY_HIGH |
| is_business_flag | BOOLEAN | Indicates whether the retail event is associated with "Amazon Business" program. | LOW |
| is_gift_flag | BOOLEAN | Indicates whether the retail event is associated with "send an order as a gift". | LOW |
| marketplace_id | INTEGER | Marketplace ID where the retail event occurred. | INTERNAL |
| marketplace_name | STRING | Name of the marketplace where the retail event occurred (e.g., AMAZON.COM, AMAZON.CO.UK). | LOW |
| no_3p_trackers | BOOLEAN | Indicates if this item is not allowed to use 3P tracking. | NONE |
| origin_session_id | STRING | Describes the session when the retail item was added to cart. | VERY_HIGH |
| purchase_date_utc | DATE | Date of the retail event in UTC. | LOW |
| purchase_day_utc | INTEGER | Day of the month of the retail event in UTC. | LOW |
| purchase_dt_hour_utc | TIMESTAMP | Timestamp of the retail event in UTC truncated to the hour. | LOW |
| purchase_dt_utc | TIMESTAMP | Timestamp of the retail event in UTC. | MEDIUM |
| purchase_hour_utc | INTEGER | Hour of the day of the retail event in UTC. | LOW |
| purchase_id | STRING | Unique identifier of the retail purchase record. Can have one-to-many relationship with event_id. | VERY_HIGH |
| purchase_month_utc | INTEGER | Month of the conversion event in UTC. | LOW |
| purchase_order_method | STRING | How the shopper purchased: S = Shopping Cart, B = Buy Now, 1 = 1-Click Buy. | LOW |
| purchase_order_type | STRING | Type of retail order: "Prime" or "NON-PRIME". | LOW |
| purchase_program_name | STRING | Purchase program associated with the retail event. | LOW |
| purchase_session_id | STRING | Describes the session when the retail item was purchased. | VERY_HIGH |
| purchase_units_sold | LONG | Total quantity of retail items. A record can have multiple units of a single item. | NONE |
| unit_price | DECIMAL | Per unit price of the product sold. | NONE |
| user_id | STRING | User ID of the shopper that purchased the item. | VERY_HIGH |
| user_id_type | STRING | Type of user ID. Only value for this dataset is "adUserId". | LOW |

## Key Use Cases and Analysis

### Long-Term Customer Behavior Analysis
The 60-month historical window enables deep customer insights:

#### Customer Lifetime Value Analysis
```sql
-- Calculate customer lifetime value over 5 years
WITH customer_purchases AS (
    SELECT 
        user_id,
        COUNT(DISTINCT purchase_id) as total_orders,
        SUM(purchase_units_sold) as total_units,
        SUM(unit_price * purchase_units_sold) as total_spend,
        MIN(purchase_date_utc) as first_purchase,
        MAX(purchase_date_utc) as last_purchase,
        DATE_DIFF(MAX(purchase_date_utc), MIN(purchase_date_utc), DAY) as customer_lifespan_days
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= '2020-01-01'
    GROUP BY user_id
)
SELECT 
    CASE 
        WHEN total_spend >= 1000 THEN 'High Value'
        WHEN total_spend >= 500 THEN 'Medium Value'
        ELSE 'Low Value'
    END as customer_segment,
    COUNT(*) as customer_count,
    AVG(total_spend) as avg_lifetime_value,
    AVG(total_orders) as avg_orders,
    AVG(customer_lifespan_days) as avg_lifespan_days
FROM customer_purchases
GROUP BY 
    CASE 
        WHEN total_spend >= 1000 THEN 'High Value'
        WHEN total_spend >= 500 THEN 'Medium Value'
        ELSE 'Low Value'
    END;
```

#### Purchase Frequency and Retention
```sql
-- Analyze purchase frequency patterns
WITH customer_metrics AS (
    SELECT 
        user_id,
        COUNT(DISTINCT purchase_id) as order_count,
        COUNT(DISTINCT DATE_TRUNC('month', purchase_date_utc)) as active_months,
        MIN(purchase_date_utc) as first_purchase,
        MAX(purchase_date_utc) as last_purchase
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= '2020-01-01'
    GROUP BY user_id
    HAVING COUNT(DISTINCT purchase_id) > 1
)
SELECT 
    active_months,
    COUNT(*) as customer_count,
    AVG(order_count) as avg_orders_per_customer,
    AVG(DATE_DIFF(last_purchase, first_purchase, DAY)) as avg_customer_lifespan
FROM customer_metrics
GROUP BY active_months
ORDER BY active_months;
```

### Brand and Product Analysis

#### Brand Performance Over Time
```sql
-- Analyze brand performance trends over 5 years
SELECT 
    asin_brand,
    EXTRACT(YEAR FROM purchase_date_utc) as purchase_year,
    COUNT(DISTINCT user_id) as unique_customers,
    COUNT(DISTINCT purchase_id) as total_orders,
    SUM(purchase_units_sold) as total_units,
    SUM(unit_price * purchase_units_sold) as total_revenue,
    AVG(unit_price) as avg_unit_price
FROM amazon_retail_purchases
WHERE asin_brand IS NOT NULL
    AND purchase_date_utc >= '2020-01-01'
GROUP BY asin_brand, EXTRACT(YEAR FROM purchase_date_utc)
ORDER BY asin_brand, purchase_year;
```

#### Product Portfolio Analysis
```sql
-- Analyze product performance and customer overlap
SELECT 
    asin,
    asin_name,
    asin_brand,
    COUNT(DISTINCT user_id) as unique_customers,
    COUNT(DISTINCT purchase_id) as total_orders,
    SUM(purchase_units_sold) as total_units_sold,
    SUM(unit_price * purchase_units_sold) as total_revenue,
    AVG(unit_price) as avg_unit_price,
    AVG(purchase_units_sold) as avg_units_per_order
FROM amazon_retail_purchases
WHERE purchase_date_utc >= '2024-01-01'
GROUP BY asin, asin_name, asin_brand
ORDER BY total_revenue DESC;
```

### Purchase Behavior Analysis

#### Purchase Method and Prime Analysis
```sql
-- Analyze purchase methods and Prime usage
SELECT 
    purchase_order_method,
    CASE 
        WHEN purchase_order_method = 'S' THEN 'Shopping Cart'
        WHEN purchase_order_method = 'B' THEN 'Buy Now'
        WHEN purchase_order_method = '1' THEN '1-Click Buy'
        ELSE purchase_order_method
    END as method_description,
    purchase_order_type,
    COUNT(DISTINCT purchase_id) as orders,
    COUNT(DISTINCT user_id) as unique_customers,
    SUM(purchase_units_sold) as total_units,
    SUM(unit_price * purchase_units_sold) as total_revenue,
    AVG(unit_price * purchase_units_sold) as avg_order_value
FROM amazon_retail_purchases
WHERE purchase_date_utc >= '2024-01-01'
GROUP BY purchase_order_method, purchase_order_type
ORDER BY orders DESC;
```

#### Gift and Business Purchase Analysis
```sql
-- Analyze gift purchases and business orders
SELECT 
    is_gift_flag,
    is_business_flag,
    COUNT(DISTINCT purchase_id) as orders,
    COUNT(DISTINCT user_id) as unique_customers,
    SUM(unit_price * purchase_units_sold) as total_revenue,
    AVG(unit_price * purchase_units_sold) as avg_order_value,
    AVG(purchase_units_sold) as avg_units_per_order
FROM amazon_retail_purchases
WHERE purchase_date_utc >= '2024-01-01'
GROUP BY is_gift_flag, is_business_flag
ORDER BY total_revenue DESC;
```

### Seasonal and Temporal Analysis

#### Seasonal Purchase Patterns
```sql
-- Analyze seasonal trends over multiple years
SELECT 
    purchase_month_utc as month,
    EXTRACT(YEAR FROM purchase_date_utc) as year,
    COUNT(DISTINCT purchase_id) as orders,
    SUM(unit_price * purchase_units_sold) as revenue,
    COUNT(DISTINCT user_id) as unique_customers,
    AVG(unit_price * purchase_units_sold) as avg_order_value
FROM amazon_retail_purchases
WHERE purchase_date_utc >= '2020-01-01'
GROUP BY purchase_month_utc, EXTRACT(YEAR FROM purchase_date_utc)
ORDER BY year, month;
```

#### Hour-of-Day Purchase Patterns
```sql
-- Analyze purchase timing patterns
SELECT 
    purchase_hour_utc,
    purchase_order_method,
    COUNT(DISTINCT purchase_id) as orders,
    AVG(unit_price * purchase_units_sold) as avg_order_value,
    COUNT(DISTINCT user_id) as unique_customers
FROM amazon_retail_purchases
WHERE purchase_date_utc >= '2024-01-01'
GROUP BY purchase_hour_utc, purchase_order_method
ORDER BY purchase_hour_utc, purchase_order_method;
```

## Advanced Attribution Analysis

### Incremental Analysis with Advertising Data
```sql
-- Compare retail purchases vs ad-attributed conversions
-- (Use appropriate time windows for each dataset)
WITH recent_retail AS (
    SELECT 
        user_id,
        asin,
        SUM(purchase_units_sold) as retail_units,
        SUM(unit_price * purchase_units_sold) as retail_revenue
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= '2024-01-01'  -- Match advertising data window
    GROUP BY user_id, asin
),
ad_attributed AS (
    SELECT 
        user_id,
        tracked_asin as asin,
        SUM(total_units_sold) as attributed_units,
        SUM(total_product_sales) as attributed_revenue
    FROM amazon_attributed_events_by_conversion_time
    WHERE conversion_event_date >= '2024-01-01'
        AND conversion_event_category = 'purchase'
    GROUP BY user_id, tracked_asin
)
SELECT 
    COALESCE(r.asin, a.asin) as asin,
    COUNT(DISTINCT COALESCE(r.user_id, a.user_id)) as total_customers,
    COUNT(DISTINCT r.user_id) as retail_customers,
    COUNT(DISTINCT a.user_id) as attributed_customers,
    SUM(COALESCE(r.retail_units, 0)) as total_retail_units,
    SUM(COALESCE(a.attributed_units, 0)) as total_attributed_units,
    SUM(COALESCE(r.retail_revenue, 0)) as total_retail_revenue,
    SUM(COALESCE(a.attributed_revenue, 0)) as total_attributed_revenue
FROM recent_retail r
FULL OUTER JOIN ad_attributed a 
    ON r.user_id = a.user_id AND r.asin = a.asin
GROUP BY COALESCE(r.asin, a.asin)
ORDER BY total_retail_revenue DESC;
```

### Customer Journey Analysis
```sql
-- Analyze customer purchase journey over time
WITH customer_journey AS (
    SELECT 
        user_id,
        purchase_date_utc,
        asin,
        asin_brand,
        unit_price * purchase_units_sold as order_value,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY purchase_date_utc) as purchase_sequence
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= '2023-01-01'
)
SELECT 
    purchase_sequence,
    COUNT(DISTINCT user_id) as customers_at_stage,
    AVG(order_value) as avg_order_value,
    COUNT(DISTINCT asin_brand) as avg_brands_purchased
FROM customer_journey
WHERE purchase_sequence <= 10  -- First 10 purchases
GROUP BY purchase_sequence
ORDER BY purchase_sequence;
```

## Audience Creation (Non-EU Markets)

### High-Value Customer Segments
```sql
-- Create audience of high-value customers (non-EU markets only)
CREATE AUDIENCE high_value_retail_customers AS
WITH customer_value AS (
    SELECT 
        user_id,
        SUM(unit_price * purchase_units_sold) as total_spend,
        COUNT(DISTINCT purchase_id) as order_count
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
        AND marketplace_name NOT IN ('AMAZON.CO.UK', 'AMAZON.FR', 'AMAZON.DE', 'AMAZON.IT', 'AMAZON.ES')  -- Exclude EU
    GROUP BY user_id
)
SELECT user_id
FROM customer_value
WHERE total_spend >= 1000
    AND order_count >= 5;
```

### Brand Loyalty Segments
```sql
-- Create audience of brand-loyal customers
CREATE AUDIENCE brand_loyal_customers AS
WITH brand_purchases AS (
    SELECT 
        user_id,
        asin_brand,
        COUNT(DISTINCT purchase_id) as brand_orders,
        SUM(unit_price * purchase_units_sold) as brand_spend
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= DATE_SUB(CURRENT_DATE(), INTERVAL 18 MONTH)
        AND marketplace_name = 'AMAZON.COM'  -- US market only
        AND asin_brand IS NOT NULL
    GROUP BY user_id, asin_brand
),
customer_brand_metrics AS (
    SELECT 
        user_id,
        MAX(brand_orders) as max_brand_orders,
        SUM(brand_orders) as total_orders
    FROM brand_purchases
    GROUP BY user_id
)
SELECT DISTINCT bp.user_id
FROM brand_purchases bp
JOIN customer_brand_metrics cbm ON bp.user_id = cbm.user_id
WHERE bp.brand_orders = cbm.max_brand_orders  -- Most purchased brand
    AND bp.brand_orders >= 3  -- At least 3 orders from the brand
    AND bp.brand_orders * 1.0 / cbm.total_orders >= 0.6;  -- 60%+ of orders from this brand
```

## Data Quality and Validation

### Purchase vs Event Relationship Analysis
```sql
-- Understand purchase_id to event_id relationships
SELECT 
    COUNT(DISTINCT purchase_id) as unique_purchases,
    COUNT(DISTINCT event_id) as unique_events,
    COUNT(*) as total_rows,
    COUNT(*) * 1.0 / COUNT(DISTINCT purchase_id) as events_per_purchase,
    COUNT(*) * 1.0 / COUNT(DISTINCT event_id) as rows_per_event
FROM amazon_retail_purchases
WHERE purchase_date_utc >= '2024-01-01';
```

### Data Completeness Analysis
```sql
-- Analyze data completeness across key fields
SELECT 
    marketplace_name,
    COUNT(*) as total_records,
    COUNT(asin) as has_asin,
    COUNT(asin_brand) as has_brand,
    COUNT(asin_name) as has_name,
    COUNT(unit_price) as has_price,
    COUNT(user_id) as has_user_id,
    COUNT(asin_brand) * 100.0 / COUNT(*) as brand_completeness_pct,
    COUNT(unit_price) * 100.0 / COUNT(*) as price_completeness_pct
FROM amazon_retail_purchases
WHERE purchase_date_utc >= '2024-01-01'
GROUP BY marketplace_name;
```

## Best Practices

### Query Optimization
- **Use appropriate time windows**: Be mindful of 60-month vs 13-month data differences
- **Filter by marketplace**: Focus on relevant geographic markets
- **Leverage user_id in CTEs**: Due to VERY_HIGH aggregation threshold
- **Consider data volume**: 5 years of data requires efficient filtering

### Business Applications
- **Customer lifetime value**: Long-term customer behavior analysis
- **Brand portfolio optimization**: Multi-year brand performance trends
- **Seasonal planning**: Historical seasonal patterns for forecasting
- **Customer segmentation**: Deep behavioral segmentation based on purchase history

### Data Integration
- **Time window alignment**: Carefully align with advertising datasets (13 months)
- **Attribution comparison**: Compare retail vs advertising-attributed performance
- **Incremental analysis**: Understand advertising's incremental impact
- **Customer journey mapping**: Connect retail behavior to advertising exposure

## Limitations and Considerations

### Geographic Restrictions
- **EU audience creation**: UK and EU data excluded from audience creation
- **Marketplace coverage**: Limited to 9 supported marketplaces
- **Account setup**: Requires proper Vendor/Seller Central configuration

### Data Characteristics
- **Retail pipeline**: Different from advertising data pipeline
- **60-month window**: Significantly longer than other AMC datasets
- **Purchase events only**: No consideration events like other conversion tables
- **User ID type**: Only "adUserId" type available

### Technical Considerations
- **Aggregation thresholds**: Multiple VERY_HIGH threshold fields requiring CTEs
- **Data volume**: Large historical dataset may impact query performance
- **Time zone**: All timestamps in UTC
- **Relationship complexity**: One-to-many relationships between purchases and events

## Integration with Other Datasets

### Cross-Dataset Analysis
- **Conversion attribution**: Compare ARP with conversions tables
- **Traffic analysis**: Connect retail behavior to advertising exposure
- **Audience insights**: Layer retail behavior with demographic segments
- **Campaign optimization**: Use retail insights to inform advertising strategy

### Measurement Applications
- **Incrementality studies**: Long-term advertising impact assessment
- **Brand health tracking**: Multi-year brand performance monitoring
- **Customer lifecycle analysis**: Complete purchase journey understanding
- **Market share analysis**: Competitive positioning over time

## Aggregation Threshold Notes

- **NONE**: No aggregation threshold restrictions
- **LOW**: Standard low threshold applies
- **MEDIUM**: Medium aggregation threshold - use caution in small segments
- **VERY_HIGH**: Very high threshold - cannot be included in final SELECT statements but can be used in CTEs for aggregation
- **INTERNAL**: Internal use only - not available for customer queries