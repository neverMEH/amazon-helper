# Amazon Your Garage Tables Schema

## Overview

**Data Sources:** 
- `amazon_your_garage`
- `amazon_your_garage_for_audiences`

Amazon Your Garage signals are available within an Amazon Marketing Cloud (AMC) account belonging to the **North America marketplaces** as an **AMC Paid Feature enrollment**. The Amazon Your Garage dataset includes signals across United States, Mexico, and Canada Amazon marketplaces.

**Dataset Type**: DIMENSION (not FACT) - no associated lookback, provides most recent user-to-vehicle associations only.

## Key Features

### Geographic Coverage
- **United States**: Amazon.com marketplace
- **Mexico**: Amazon Mexico marketplace  
- **Canada**: Amazon Canada marketplace

### Data Characteristics
- **Refresh frequency**: Daily updates
- **Data snapshot**: Most recent available user-to-vehicle associations
- **Historical data**: No lookback - current state only
- **Subscription requirement**: AMC Paid Feature enrollment required

## Table Schema

### Core Vehicle Association Fields

| Field Category | Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|----------------|------|-----------|-------------------|-------------|----------------------|
| Amazon Your Garage | marketplace_name | STRING | Dimension | The marketplace associated with the Amazon Garage record. | LOW |
| Amazon Your Garage | user_id | STRING | Dimension | The User ID of the customer owning the vehicle. | VERY_HIGH |
| Amazon Your Garage | user_id_type | STRING | Dimension | The user_id type. | LOW |
| Amazon Your Garage | no_3p_trackers | BOOLEAN | Dimension | Is this item not allowed to use 3P tracking? | NONE |

### Record Metadata

| Field Category | Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|----------------|------|-----------|-------------------|-------------|----------------------|
| Amazon Your Garage | creation_date | DATE | Dimension | Creation date (in UTC) of the record. | LOW |
| Amazon Your Garage | last_accessed_date | DATE | Dimension | The last accessed date (in UTC) for a customer invoked interaction with an Amazon Garage record. | LOW |
| Amazon Your Garage | update_date | DATE | Dimension | The date (in UTC) for the most recent garage record edit. | LOW |

### Vehicle Attributes

| Field Category | Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|----------------|------|-----------|-------------------|-------------|----------------------|
| Amazon Your Garage | garage_year | STRING | Dimension | Vehicle year attribute. | LOW |
| Amazon Your Garage | vehicle_type | STRING | Dimension | Vehicle type attribute. | LOW |
| Amazon Your Garage | garage_make | STRING | Dimension | Vehicle make attribute. | LOW |
| Amazon Your Garage | garage_model | STRING | Dimension | Vehicle model attribute. | LOW |
| Amazon Your Garage | garage_submodel | STRING | Dimension | Vehicle sub-model (trim) attribute. | LOW |
| Amazon Your Garage | garage_bodystyle | STRING | Dimension | Vehicle body style attribute. | LOW |
| Amazon Your Garage | garage_engine | STRING | Dimension | Vehicle engine attribute. | LOW |
| Amazon Your Garage | garage_transmission | STRING | Dimension | Vehicle transmission attribute. | LOW |
| Amazon Your Garage | garage_drivetype | STRING | Dimension | Vehicle drive type attribute. | LOW |
| Amazon Your Garage | garage_brakes | STRING | Dimension | Vehicle brakes attribute. | LOW |

## Use Cases and Applications

### Planning
- **Audience segmentation** by vehicle characteristics
- **Market research** for automotive products and services
- **Campaign targeting** based on vehicle ownership patterns
- **Product recommendation** strategies for automotive accessories

### Measurement
- **Campaign performance** analysis by vehicle segments
- **Cross-sell effectiveness** for automotive products
- **Brand affinity** analysis within vehicle categories
- **Conversion attribution** for automotive-related purchases

### Activation
- **Targeted advertising** to specific vehicle owners
- **Personalized product recommendations** based on vehicle type
- **Lookalike audience creation** using vehicle characteristics
- **Retargeting campaigns** for automotive accessories and services

## Common Query Patterns

### Vehicle Ownership Analysis
```sql
-- Analyze vehicle distribution by make and model
SELECT 
    marketplace_name,
    garage_make,
    garage_model,
    garage_year,
    COUNT(DISTINCT user_id) as owner_count
FROM amazon_your_garage
WHERE marketplace_name = 'AMAZON.COM'
    AND garage_year >= '2015'  -- Focus on newer vehicles
GROUP BY marketplace_name, garage_make, garage_model, garage_year
ORDER BY owner_count DESC;
```

### Vehicle Type Segmentation
```sql
-- Segment users by vehicle type and characteristics
SELECT 
    vehicle_type,
    garage_bodystyle,
    garage_drivetype,
    COUNT(DISTINCT user_id) as user_count
FROM amazon_your_garage
WHERE marketplace_name IN ('AMAZON.COM', 'AMAZON_CA')
GROUP BY vehicle_type, garage_bodystyle, garage_drivetype
ORDER BY user_count DESC;
```

### Premium Vehicle Analysis
```sql
-- Identify premium vehicle owners (example luxury brands)
SELECT 
    garage_make,
    garage_model,
    garage_submodel,
    garage_year,
    COUNT(DISTINCT user_id) as premium_owners
FROM amazon_your_garage
WHERE garage_make IN ('BMW', 'Mercedes-Benz', 'Audi', 'Lexus', 'Acura')
    AND marketplace_name = 'AMAZON.COM'
GROUP BY garage_make, garage_model, garage_submodel, garage_year
ORDER BY premium_owners DESC;
```

### Vehicle Age Analysis
```sql
-- Analyze vehicle age distribution
WITH vehicle_age AS (
    SELECT 
        user_id,
        garage_make,
        garage_model,
        garage_year,
        CAST(EXTRACT(YEAR FROM CURRENT_DATE()) AS INT) - CAST(garage_year AS INT) as vehicle_age_years
    FROM amazon_your_garage
    WHERE garage_year IS NOT NULL
        AND garage_year != ''
        AND marketplace_name = 'AMAZON.COM'
)
SELECT 
    CASE 
        WHEN vehicle_age_years <= 3 THEN '0-3 years'
        WHEN vehicle_age_years <= 7 THEN '4-7 years'
        WHEN vehicle_age_years <= 12 THEN '8-12 years'
        ELSE '13+ years'
    END as age_bracket,
    COUNT(DISTINCT user_id) as owner_count,
    COUNT(DISTINCT user_id) * 100.0 / SUM(COUNT(DISTINCT user_id)) OVER () as percentage
FROM vehicle_age
GROUP BY 
    CASE 
        WHEN vehicle_age_years <= 3 THEN '0-3 years'
        WHEN vehicle_age_years <= 7 THEN '4-7 years'
        WHEN vehicle_age_years <= 12 THEN '8-12 years'
        ELSE '13+ years'
    END;
```

### User Engagement Patterns
```sql
-- Analyze user engagement with garage records
SELECT 
    marketplace_name,
    DATE_DIFF(CURRENT_DATE(), last_accessed_date, DAY) as days_since_access,
    COUNT(DISTINCT user_id) as users
FROM amazon_your_garage
WHERE last_accessed_date IS NOT NULL
GROUP BY marketplace_name, DATE_DIFF(CURRENT_DATE(), last_accessed_date, DAY)
HAVING days_since_access <= 365  -- Last year
ORDER BY marketplace_name, days_since_access;
```

## Campaign Attribution Analysis

### Automotive Campaign Performance
```sql
-- Analyze campaign performance for vehicle owners
-- (Using CTE for user_id due to VERY_HIGH aggregation threshold)
WITH garage_users AS (
    SELECT DISTINCT 
        user_id,
        garage_make,
        vehicle_type
    FROM amazon_your_garage
    WHERE marketplace_name = 'AMAZON.COM'
        AND garage_make IN ('Ford', 'Chevrolet', 'Toyota', 'Honda')
)
SELECT 
    g.garage_make,
    g.vehicle_type,
    SUM(a.total_purchases) as attributed_purchases,
    SUM(a.total_product_sales) as attributed_sales,
    COUNT(DISTINCT a.user_id) as converting_users
FROM garage_users g
JOIN amazon_attributed_events_by_conversion_time a
    ON g.user_id = a.user_id
WHERE a.conversion_event_date >= '2025-01-01'
    AND a.conversion_event_category = 'purchase'
GROUP BY g.garage_make, g.vehicle_type
ORDER BY attributed_sales DESC;
```

### Cross-Category Purchase Analysis
```sql
-- Analyze purchase patterns by vehicle characteristics
WITH vehicle_owners AS (
    SELECT DISTINCT 
        user_id,
        garage_make,
        garage_bodystyle,
        garage_year
    FROM amazon_your_garage
    WHERE marketplace_name = 'AMAZON.COM'
        AND garage_year >= '2020'
)
SELECT 
    v.garage_make,
    v.garage_bodystyle,
    COUNT(DISTINCT c.conversion_id) as total_conversions,
    SUM(c.total_product_sales) as total_sales
FROM vehicle_owners v
JOIN conversions c
    ON v.user_id = c.user_id
WHERE c.event_date_utc >= '2025-01-01'
    AND c.event_category = 'purchase'
GROUP BY v.garage_make, v.garage_bodystyle
ORDER BY total_sales DESC;
```

## Audience Creation for Targeting

### Vehicle-Based Audience Segments
```sql
-- Create audience of luxury vehicle owners
CREATE AUDIENCE luxury_vehicle_owners AS
SELECT DISTINCT user_id
FROM amazon_your_garage_for_audiences
WHERE garage_make IN ('BMW', 'Mercedes-Benz', 'Audi', 'Lexus', 'Infiniti', 'Cadillac')
    AND marketplace_name = 'AMAZON.COM'
    AND last_accessed_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);

-- Create audience of truck owners
CREATE AUDIENCE truck_owners AS
SELECT DISTINCT user_id
FROM amazon_your_garage_for_audiences
WHERE vehicle_type = 'Truck'
    AND marketplace_name IN ('AMAZON.COM', 'AMAZON_CA')
    AND garage_year >= '2018';

-- Create audience of electric vehicle owners
CREATE AUDIENCE ev_owners AS
SELECT DISTINCT user_id
FROM amazon_your_garage_for_audiences
WHERE garage_make IN ('Tesla', 'Rivian', 'Lucid')
    OR (garage_make = 'Chevrolet' AND garage_model = 'Bolt')
    OR (garage_make = 'Nissan' AND garage_model = 'Leaf')
    OR (garage_engine LIKE '%Electric%' OR garage_engine LIKE '%EV%');
```

### Seasonal Campaign Targeting
```sql
-- Create audience for winter tire campaign
CREATE AUDIENCE winter_driving_audience AS
SELECT DISTINCT user_id
FROM amazon_your_garage_for_audiences
WHERE marketplace_name IN ('AMAZON.COM', 'AMAZON_CA')  -- Cold weather markets
    AND garage_drivetype IN ('AWD', '4WD', 'All-Wheel Drive', 'Four-Wheel Drive')
    AND last_accessed_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 180 DAY);
```

## Vehicle Attribute Analysis

### Make and Model Distribution
```sql
-- Top vehicle makes and models
SELECT 
    garage_make,
    garage_model,
    COUNT(DISTINCT user_id) as owner_count,
    COUNT(DISTINCT user_id) * 100.0 / SUM(COUNT(DISTINCT user_id)) OVER () as market_share_percent
FROM amazon_your_garage
WHERE marketplace_name = 'AMAZON.COM'
GROUP BY garage_make, garage_model
ORDER BY owner_count DESC
LIMIT 50;
```

### Feature Analysis
```sql
-- Analyze vehicle features distribution
SELECT 
    garage_transmission,
    garage_drivetype,
    garage_bodystyle,
    COUNT(DISTINCT user_id) as users
FROM amazon_your_garage
WHERE marketplace_name = 'AMAZON.COM'
    AND garage_transmission IS NOT NULL
    AND garage_drivetype IS NOT NULL
    AND garage_bodystyle IS NOT NULL
GROUP BY garage_transmission, garage_drivetype, garage_bodystyle
ORDER BY users DESC;
```

## Data Quality and Validation

### Record Completeness Analysis
```sql
-- Analyze data completeness across fields
SELECT 
    marketplace_name,
    COUNT(*) as total_records,
    COUNT(garage_year) as has_year,
    COUNT(garage_make) as has_make,
    COUNT(garage_model) as has_model,
    COUNT(garage_submodel) as has_submodel,
    COUNT(garage_engine) as has_engine,
    COUNT(garage_transmission) as has_transmission
FROM amazon_your_garage
GROUP BY marketplace_name;
```

### User Activity Analysis
```sql
-- Analyze user engagement with garage records
SELECT 
    marketplace_name,
    DATE_DIFF(CURRENT_DATE(), creation_date, DAY) as days_since_creation,
    DATE_DIFF(CURRENT_DATE(), last_accessed_date, DAY) as days_since_access,
    DATE_DIFF(CURRENT_DATE(), update_date, DAY) as days_since_update,
    COUNT(DISTINCT user_id) as users
FROM amazon_your_garage
WHERE creation_date IS NOT NULL
    AND last_accessed_date IS NOT NULL
    AND update_date IS NOT NULL
GROUP BY marketplace_name, days_since_creation, days_since_access, days_since_update
ORDER BY marketplace_name, days_since_creation;
```

## Best Practices

### Query Optimization
- **Use CTEs for user_id**: Due to VERY_HIGH aggregation threshold, use user_id in Common Table Expressions
- **Filter by marketplace**: Always include marketplace_name filtering for performance
- **Leverage recent activity**: Use last_accessed_date or update_date to focus on active users
- **Specific vehicle targeting**: Use detailed attributes for precise audience segmentation

### Business Applications
- **Automotive industry**: Perfect for auto parts, accessories, and service providers
- **Insurance targeting**: Vehicle characteristics for insurance product targeting
- **Lifestyle segmentation**: Vehicle type as indicator of lifestyle and interests
- **Seasonal campaigns**: Vehicle features for weather-related product targeting

### Data Interpretation
- **Current state only**: Remember this is DIMENSION data - no historical trends
- **User engagement**: Use access dates to understand data freshness and user engagement
- **Market coverage**: Focus on North American marketplaces only
- **Feature combinations**: Combine multiple vehicle attributes for detailed segmentation

## Integration Opportunities

### Cross-Dataset Analysis
- **Traffic analysis**: Join with DSP and sponsored ads traffic for campaign optimization
- **Conversion attribution**: Connect with conversion tables for automotive campaign measurement
- **Audience segments**: Combine with Amazon audience segments for enhanced targeting
- **Shopping behavior**: Analyze purchase patterns relative to vehicle ownership

### Campaign Activation
- **DSP targeting**: Use vehicle segments for Amazon DSP campaign targeting
- **Sponsored ads**: Apply insights to sponsored products and brands campaigns
- **Lookalike modeling**: Create lookalike audiences based on vehicle characteristics
- **Cross-sell strategies**: Develop automotive accessory and service campaigns

## Limitations and Considerations

### Data Scope
- **Geographic limitation**: North America marketplaces only (US, Mexico, Canada)
- **Subscription requirement**: AMC Paid Feature enrollment required
- **Current state**: No historical data or trends available
- **User opt-in**: Based on users who have engaged with Amazon Your Garage feature

### Privacy and Compliance
- **3P tracking**: Respect no_3p_trackers flag for audience creation
- **Aggregation thresholds**: Follow VERY_HIGH threshold requirements for user_id
- **Data retention**: Understand data refresh and retention policies
- **Consent management**: Ensure compliance with privacy regulations

## Aggregation Threshold Notes

- **NONE**: No aggregation threshold restrictions
- **LOW**: Standard low threshold applies
- **VERY_HIGH**: Very high threshold - cannot be included in final SELECT statements but can be used in CTEs for aggregation