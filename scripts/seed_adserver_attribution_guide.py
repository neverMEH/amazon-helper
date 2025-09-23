#!/usr/bin/env python3
"""
Seed script for Amazon Ad Server - Custom Attribution of ASIN Conversions Build Guide
This script creates the comprehensive guide content in the database
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def create_adserver_attribution_guide():
    """Create the Amazon Ad Server Custom Attribution guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_adserver_custom_attribution',
            'name': 'Amazon Ad Server - Custom Attribution of ASIN Conversions',
            'category': 'Attribution Analysis',
            'short_description': 'Demonstrate the impact of Amazon Ad Server advertising on Amazon conversions using custom attribution models.',
            'tags': ['ad server', 'custom attribution', 'ASIN conversions', 'cross-channel', 'last-click attribution'],
            'icon': 'Server',
            'difficulty_level': 'advanced',
            'estimated_time_minutes': 45,
            'prerequisites': [
                'Active campaigns running through Amazon DSP',
                'Ad Server traffic data available in AMC',
                'Understanding of attribution models',
                'Familiarity with CTEs and window functions'
            ],
            'is_published': True,
            'display_order': 10,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Insert guide
        guide_response = client.table('build_guides').insert(guide_data).execute()
        if not guide_response.data:
            logger.error("Failed to create guide")
            return False
        
        guide_id = guide_response.data[0]['id']
        logger.info(f"Created guide with ID: {guide_id}")
        
        # Create sections
        sections = [
            {
                'guide_id': guide_id,
                'section_id': 'introduction',
                'title': '1. Introduction',
                'content_markdown': """## 1.1 Purpose

This instructional query (IQ) demonstrates the impact that Amazon Ad Server advertising has on Amazon conversions. When customers are exposed to ads running outside of the Amazon DSP, what is the impact on ad-attributed conversion rates (for example, purchase rates)? This IQ provides an example of Custom Attribution of ASIN conversions on all Amazon Ad Server traffic.

### Key Questions Answered
- What is the conversion impact of ads served through Amazon Ad Server?
- Which sites and placements drive the highest conversion rates?
- How do different attribution models affect conversion measurement?
- What is the optimal attribution window for your campaigns?

## 1.2 Requirements

To use this query, advertisers must have:
- Campaigns that ran through the Amazon DSP
- Other media channels that use the Amazon Ad Server for ad serving or measurement
- Access to both `adserver_traffic` and `conversions` tables in AMC
- Basic understanding of SQL CTEs (Common Table Expressions)

### Important Notes
- The query supports both last-click and first-touch attribution models
- Default attribution window is 14 days (customizable)
- Supports various conversion types beyond purchases
- Can include or exclude Amazon DSP traffic based on your analysis needs""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Tables Used

### adserver_traffic
This table contains all impressions and clicks measured by the Amazon Ad Server. Key fields include:
- `user_id`: Unique identifier for users
- `advertiser_id`: Your advertiser identifier
- `campaign_id`: Campaign identifier
- `adserver_site`: Site where the ad was served
- `placement`: Placement identifier
- `ad_id`: Creative identifier
- `impressions`: Number of impressions
- `clicks`: Number of clicks
- `event_dt_utc`: Event timestamp

### conversions
This table contains relevant conversions for all ASINs that were tracked to an Amazon DSP or Sponsored Ads campaign in the AMC instance if the user was served a qualifying traffic event within the 28-day period before the conversion event. Key fields include:
- `user_id`: Unique identifier for users
- `conversion_id`: Unique conversion identifier
- `tracked_item`: ASIN that was converted
- `event_subtype`: Type of conversion (order, detailPageView, etc.)
- `conversions`: Number of conversions
- `total_product_sales`: Sales value
- `total_units_sold`: Units sold
- `event_dt_utc`: Conversion timestamp

## 2.2 Query Structure

The query uses several CTEs (Common Table Expressions) to build the attribution logic:

1. **advertiser_ids**: Define which advertisers to analyze
2. **campaign_ids**: Specify campaigns to include
3. **asin_conversions**: List ASINs to track conversions for
4. **traffic**: Gather and filter traffic events
5. **matched**: Join traffic with conversions based on user_id
6. **ranked**: Apply attribution model (last-click or first-touch)
7. **attributed_conversions**: Aggregate attributed conversions
8. **campaign_traffic**: Calculate delivery metrics
9. **Final SELECT**: Combine all metrics for reporting

## 2.3 Customization Points

Look for **UPDATE** comments in the query to customize:
- Advertiser and campaign IDs
- ASINs to track
- Attribution model (last-click vs first-touch)
- Lookback windows
- Conversion types
- DCO (Dynamic Creative Optimization) tracking""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': '3. Data Interpretation Instructions',
                'content_markdown': """## 3.1 Example Query Results

*This data is for instructional purposes only. Your results will differ.*

| site_name | campaign_type | campaign | placement | ad_id_or_search_keyword_id | conversions | total_product_sales | total_units_sold | users_that_purchased | user_reach | impressions | clicks | user_purchase_rate |
|-----------|---------------|----------|-----------|---------------------------|-------------|-------------------|------------------|---------------------|------------|-------------|--------|-------------------|
| Site 1 | Display | Summer Sale | Homepage Banner | AD_12345 | 150 | $4,500.00 | 175 | 145 | 10,000 | 50,000 | 500 | 1.45% |
| Site 2 | Display | Summer Sale | Sidebar | AD_12346 | 85 | $2,550.00 | 95 | 82 | 8,500 | 42,500 | 340 | 0.96% |
| Site 3 | Video | Brand Awareness | Pre-roll | AD_12347 | 220 | $6,600.00 | 250 | 210 | 15,000 | 75,000 | 750 | 1.40% |
| Site 4 | Display | Retargeting | Footer | AD_12348 | 45 | $1,350.00 | 50 | 43 | 5,000 | 25,000 | 200 | 0.86% |
| Site 5 | Native | Content Push | In-feed | AD_12349 | 180 | $5,400.00 | 200 | 175 | 12,000 | 60,000 | 600 | 1.46% |

## 3.2 Metrics Defined

### Primary Metrics
- **conversions**: Number of distinct conversion events attributed to campaigns based on the conversion_event_subtype selected
- **total_product_sales**: The total ad-attributed sales (in local currency) from converted ASINs
- **total_units_sold**: The total ad-attributed quantity of promoted products sold
- **users_that_purchased**: Distinct users who made an attributed purchase after exposure

### Delivery Metrics  
- **user_reach**: Number of unique users exposed to the campaign
- **impressions**: Total impressions for each ad_id or placement
- **clicks**: Total clicks for each ad_id or placement
- **user_purchase_rate**: Percentage of users with an attributed purchase (users_that_purchased / user_reach * 100)

### Attribution Metrics
- **match_age**: Time between traffic event and conversion (in seconds)
- **match_rank**: Ranking of traffic events for attribution (1 = attributed event)
- **conversion_rate**: Conversions divided by user reach, expressed as percentage

## 3.3 Insights and Data Interpretation

### Site Performance Analysis
You can use the results from this query to understand the conversion rates by site when users are exposed to media outside of Amazon through adserver. Key insights include:

1. **High-Performing Sites**: 
   - Sites 1, 3, and 5 show user purchase rates above 1.4%
   - These audiences appear more responsive to your ads
   - Consider increasing investment in these sites

2. **Optimization Opportunities**:
   - Sites 2 and 4 show lower conversion rates (< 1%)
   - Evaluate creative messaging for these audiences
   - Consider testing different placements or formats

3. **Format Performance**:
   - Video (Site 3) and Native (Site 5) formats show strong performance
   - Display performance varies by placement (Homepage > Sidebar > Footer)

### Attribution Model Considerations

**Last-Click Attribution (Default)**:
- Credits the conversion to the last touchpoint before purchase
- Best for understanding immediate conversion drivers
- May undervalue upper-funnel activities

**First-Touch Attribution (Optional)**:
- Credits the conversion to the first touchpoint in the journey
- Better for understanding awareness drivers
- May overvalue initial touchpoints

### Recommended Actions

1. **Budget Allocation**: Shift budget toward sites with higher user purchase rates
2. **Creative Testing**: Test new creative variations on underperforming sites
3. **Placement Optimization**: Focus on high-visibility placements (homepage, pre-roll)
4. **Attribution Window Testing**: Test different windows to understand optimal measurement period
5. **Cross-Channel Analysis**: Compare Ad Server performance to Amazon DSP campaigns""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'advanced_customization',
                'title': '4. Advanced Customization',
                'content_markdown': """## 4.1 Attribution Model Customization

### Switching Attribution Models

**Last-Click Attribution (Default)**:
```sql
ROW_NUMBER() OVER(PARTITION BY conversion_id ORDER BY match_age) AS match_rank
```

**First-Touch Attribution**:
```sql
ROW_NUMBER() OVER(PARTITION BY conversion_id ORDER BY match_age DESC) AS match_rank
```

**Custom Time-Decay Attribution** (Advanced):
```sql
-- Apply exponential decay based on time from conversion
EXP(-0.1 * match_age / (24 * 60 * 60)) AS attribution_weight
```

## 4.2 Lookback Window Configuration

### Different Windows for Impressions vs Clicks
```sql
-- In the ranked CTE WHERE clause:
WHERE
  (traffic_type = 'click' AND match_age BETWEEN 0 AND 10 * 24 * 60 * 60)  -- 10 days for clicks
  OR (traffic_type = 'impression' AND match_age BETWEEN 0 AND 5 * 24 * 60 * 60)  -- 5 days for impressions
```

### Dynamic Lookback Based on Campaign Type
```sql
-- Adjust lookback based on campaign objectives
CASE 
  WHEN campaign_type = 'Awareness' THEN 28 * 24 * 60 * 60  -- 28 days
  WHEN campaign_type = 'Consideration' THEN 14 * 24 * 60 * 60  -- 14 days
  WHEN campaign_type = 'Conversion' THEN 7 * 24 * 60 * 60  -- 7 days
  ELSE 14 * 24 * 60 * 60  -- Default 14 days
END AS lookback_seconds
```

## 4.3 Conversion Type Variations

### Available Conversion Types
- `'order'` - Purchase conversions (default)
- `'detailPageView'` - Product page views
- `'shoppingCart'` - Add to cart events
- `'wishList'` - Add to wishlist
- `'customerReview'` - Product reviews
- `'babyRegistry'` - Baby registry additions
- `'weddingRegistry'` - Wedding registry additions
- `'snsSubscription'` - Subscribe & Save subscriptions

### Multi-Touch Conversion Analysis
```sql
-- Track multiple conversion types in one query
AND event_subtype IN ('order', 'shoppingCart', 'detailPageView')
```

## 4.4 DCO (Dynamic Creative Optimization) Tracking

To enable DCO tracking, uncomment the relevant sections in the query:

```sql
-- In SELECT clauses, add:
version_name,
version_id,
target_audience_name,
target_audience_id,

-- In GROUP BY clauses, add corresponding numbers:
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11

-- In JOIN conditions, add:
AND c.version_id = t.version_id 
AND c.target_audience_id = t.target_audience_id
```

## 4.5 Performance Optimization Tips

1. **Use Appropriate Time Windows**: Smaller windows = faster queries
2. **Filter Early**: Apply filters in the traffic CTE to reduce data volume
3. **Index Utilization**: Ensure user_id and event_dt_utc are properly indexed
4. **Partition Pruning**: Use date filters to leverage table partitioning
5. **Limit Results**: Add LIMIT clauses during testing and development""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            }
        ]
        
        # Insert sections
        for section in sections:
            response = client.table('build_guide_sections').insert(section).execute()
            if response.data:
                logger.info(f"Created section: {section['title']}")
            else:
                logger.error(f"Failed to create section: {section['title']}")
        
        # Create queries
        queries = [
            {
                'guide_id': guide_id,
                'title': 'Campaign and Advertisers Exploratory Query',
                'description': 'Use this query to explore advertisers and campaigns in the instance to select desired campaigns and advertiser IDs.',
                'sql_query': """-- Instructional query: Campaign and Advertisers Exploratory Query for Amazon Ad Server Site Reach Overlap and Conversions
SELECT
  advertiser,
  advertiser_id,
  campaign,
  campaign_id,
  SUM(impressions) AS impressions,
  SUM(clicks) AS total_clicks
FROM
  adserver_traffic
WHERE
  event_dt_utc >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
GROUP BY
  advertiser,
  advertiser_id,
  campaign,
  campaign_id
ORDER BY
  impressions DESC
LIMIT 100""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for campaign data'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query helps identify active advertisers and campaigns with Ad Server traffic. Use the advertiser_id and campaign_id values from this query in the main attribution query.'
            },
            {
                'guide_id': guide_id,
                'title': 'ASIN Conversions Exploratory Query',
                'description': 'Use this query to identify conversion activity and ASINs relevant to each advertiser in the instance.',
                'sql_query': """-- Instructional Query: Custom Attribution exploratory query for ASIN conversion advertisers
SELECT
  tracked_item AS ASIN,
  event_subtype,
  COUNT(DISTINCT user_id) as unique_converters,
  SUM(conversions) AS total_conversions,
  SUM(total_product_sales) AS revenue,
  SUM(total_units_sold) AS units
FROM
  conversions c
WHERE
  c.user_id IS NOT NULL
  AND event_dt_utc >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
  AND event_subtype IN ({{conversion_types}})
GROUP BY
  tracked_item,
  event_subtype
HAVING 
  SUM(conversions) >= {{min_conversions}}
ORDER BY
  total_conversions DESC
LIMIT 100""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for conversion data'
                    },
                    'conversion_types': {
                        'type': 'array',
                        'default': ['order'],
                        'description': 'Types of conversions to analyze'
                    },
                    'min_conversions': {
                        'type': 'integer',
                        'default': 10,
                        'description': 'Minimum conversions threshold'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'conversion_types': ['order'],
                    'min_conversions': 10
                },
                'display_order': 2,
                'query_type': 'exploratory',
                'interpretation_notes': 'Identify which ASINs have conversion activity. Use these ASIN values in the asin_conversions CTE of the main query.'
            },
            {
                'guide_id': guide_id,
                'title': 'Custom Attribution of ASIN Conversions to Ad Server Traffic',
                'description': 'Main query for attributing ASIN conversions to Amazon Ad Server traffic with customizable attribution windows and models.',
                'sql_query': """-- Instructional Query Library: Custom Attribution of ASIN conversions to Amazon Ad Server traffic.
/*Custom Attribution of ASIN conversions on all Amazon Ad Server traffic (including users who were exposed to both Amazon & non Amazon ads.
 Returns number of ASIN conversions, total_product_sales, total_units_sold, 
 users_that_purchased, impressions, clicks, reach, conversion rate, 
 broken down by Amazon Ad Server entities that were attributed the conversion */
/*UPDATE to your advertiser id */
WITH advertiser_ids (advertiser_id) AS (
  VALUES
    ({{advertiser_id}})
),
/*UPDATE to your campaign ids */
campaign_ids (campaign_id) AS (
  VALUES
    {{#each campaign_ids}}
    ({{this}}){{#unless @last}},{{/unless}}
    {{/each}}
),
/*UPDATE to your asin conversions */
asin_conversions (asin_conversion) AS (
  VALUES
    {{#each target_asins}}
    ('{{this}}'){{#unless @last}},{{/unless}}
    {{/each}}
),
traffic AS (
  -- Read impression or click events.
  SELECT
    COALESCE(adserver_site, search_vendor) AS site_name,
    campaign,
    campaign_id,
    campaign_type,
    COALESCE(
      CAST(placement AS VARCHAR),
      CAST(search_ad_group AS VARCHAR)
    ) AS placement,
    COALESCE(
      CAST(ad_id AS VARCHAR),
      CAST(search_keyword_id AS VARCHAR)
    ) AS ad_id_or_search_keyword_id,
    COALESCE(
      CAST(ad AS VARCHAR),
      CAST(search_keyword_text AS VARCHAR)
    ) AS ad_or_search_keyword,
    -- UPDATE: Uncomment to use dco ad versions
    /*
     version_name,
     version_id,
     target_audience_name,
     target_audience_id,
     */
    user_id,
    event_dt_utc AS traffic_dt,
    impressions,
    clicks
  FROM
    TABLE(
      EXTEND_TIME_WINDOW('adserver_traffic', 'P{{lookback_days}}D', 'P0D')
    )
  WHERE
    (
      clicks = 1
      OR impressions = 1
    )
    AND advertiser_id IN (
      SELECT
        advertiser_id
      FROM
        advertiser_ids
    )
    {{#if exclude_amazon_dsp}}
    -- Excluding Amazon DSP traffic
    AND site NOT SIMILAR to '^Amazon.*'
    {{/if}}
),
-- Read conversion events from the amazon conversions data source.
-- Join conversion events to traffic events based on the user ID.
-- Determine a match age based on the time from the conversion event.
matched AS (
  SELECT
    t.site_name,
    t.campaign,
    t.campaign_id,
    t.campaign_type,
    t.placement,
    t.ad_id_or_search_keyword_id,
    t.ad_or_search_keyword,
    -- UPDATE: Uncomment to use dco ad versions
    /*
     t.version_name,
     t.version_id,
     t.target_audience_name,
     t.target_audience_id,
     */
    t.traffic_dt,
    c.conversion_id,
    c.conversions,
    c.total_product_sales,
    c.total_units_sold,
    c.user_id,
    -- Determine a match age between the traffic event and conversion event
    SECONDS_BETWEEN(t.traffic_dt, c.event_dt_utc) AS match_age
  FROM
    conversions c
    INNER JOIN traffic t ON c.user_id = t.user_id
  WHERE
    tracked_item IN (
      SELECT
        asin_conversion
      FROM
        asin_conversions
    )
    AND event_subtype = '{{conversion_type}}'
),
-- For each conversion event, rank all the matching traffic events based on match age.
ranked AS (
  SELECT
    site_name,
    campaign,
    campaign_id,
    campaign_type,
    placement,
    ad_id_or_search_keyword_id,
    -- UPDATE: Uncomment to use dco ad versions
    /*
     version_name, 
     version_id,
     target_audience_name,
     target_audience_id,
     */
    ad_or_search_keyword,
    user_id,
    -- Rank the match based on match age. For first touch attribution, use: ORDER BY match_age DESC
    ROW_NUMBER() OVER(
      PARTITION BY conversion_id
      ORDER BY
        {{#if attribution_model_first_touch}}
        match_age DESC
        {{else}}
        match_age
        {{/if}}
    ) AS match_rank,
    conversions,
    total_product_sales,
    total_units_sold
  FROM
    matched
  WHERE
    -- Lookback window for attribution
    match_age BETWEEN 0 AND {{attribution_window_days}} * 24 * 60 * 60
),
-- Filter to only the best matching traffic event for each conversion event.
attributed_conversions AS (
  SELECT
    site_name,
    campaign,
    campaign_id,
    campaign_type,
    placement,
    ad_id_or_search_keyword_id,
    ad_or_search_keyword,
    -- UPDATE: Uncomment to use dco ad versions
    /*
     version_name, 
     version_id,
     target_audience_name,
     target_audience_id,
     */
    COUNT(DISTINCT user_id) as users_that_purchased,
    SUM(conversions) conversions,
    SUM(total_product_sales) total_product_sales,
    SUM(total_units_sold) total_units_sold
  FROM
    ranked
  WHERE
    -- Filter to the attributed touch event
    match_rank = 1
    AND campaign_id IN (
      SELECT
        campaign_id
      FROM
        campaign_ids
    )
  GROUP BY
    site_name,
    campaign,
    campaign_id,
    campaign_type,
    placement,
    ad_id_or_search_keyword_id,
    ad_or_search_keyword
    -- UPDATE: Uncomment to use dco ad versions
    /*
     ,version_name, 
     version_id,
     target_audience_name,
     target_audience_id
     */
),
/* Calculating the user_reach, impressions and clicks report metrics */
campaign_traffic AS (
  SELECT
    site_name,
    campaign,
    campaign_id,
    campaign_type,
    placement,
    ad_id_or_search_keyword_id,
    ad_or_search_keyword,
    -- UPDATE: Uncomment to use dco ad versions
    /*
     version_name, 
     version_id,
     target_audience_name,
     target_audience_id,
     */
    COUNT(DISTINCT user_id) user_reach,
    SUM(impressions) impressions,
    SUM(clicks) clicks
  FROM
    traffic
  WHERE
    campaign_id IN (
      SELECT
        campaign_id
      FROM
        campaign_ids
    )
  GROUP BY
    site_name,
    campaign,
    campaign_id,
    campaign_type,
    placement,
    ad_id_or_search_keyword_id,
    ad_or_search_keyword
    -- UPDATE: Uncomment to use dco ad versions
    /*
     ,version_name, 
     version_id,
     target_audience_name,
     target_audience_id
     */
)
/* 
 Assemble conversion events with traffic events. 
 The final select statement joins the delivery metrics from the 'campaign_traffic' 
 CTE with the conversion metrics from the 'attributed_conversions' CTE to form the 
 final report output. It also calculates the conversion rate as additional report 
 metric 
 */
SELECT
  c.site_name,
  c.campaign_type,
  c.campaign,
  c.placement,
  c.ad_id_or_search_keyword_id,
  -- UPDATE: Uncomment to use dco ad versions
  /*
   c.version_name, 
   c.version_id,
   c.target_audience_name,
   c.target_audience_id,
   */
  c.conversions,
  c.total_product_sales,
  c.total_units_sold,
  c.users_that_purchased,
  t.user_reach,
  t.impressions,
  t.clicks,
  ROUND((CAST(c.users_that_purchased AS DOUBLE) / CAST(t.user_reach AS DOUBLE)) * 100, 2) AS user_purchase_rate
FROM
  attributed_conversions c
  JOIN campaign_traffic t ON c.site_name = t.site_name
  AND c.campaign_type = t.campaign_type
  AND c.campaign_id = t.campaign_id
  AND c.ad_id_or_search_keyword_id = t.ad_id_or_search_keyword_id
  AND c.placement = t.placement
  -- UPDATE: Uncomment to use ad dco versions
  /* AND c.version_id = t.version_id 
   AND c.target_audience_id = t.target_audience_id */
ORDER BY
  c.conversions DESC,
  t.user_reach DESC""",
                'parameters_schema': {
                    'advertiser_id': {
                        'type': 'integer',
                        'required': True,
                        'description': 'Your advertiser ID from the exploratory query'
                    },
                    'campaign_ids': {
                        'type': 'array',
                        'required': True,
                        'description': 'List of campaign IDs to analyze'
                    },
                    'target_asins': {
                        'type': 'array',
                        'required': True,
                        'description': 'List of ASINs to track conversions for'
                    },
                    'lookback_days': {
                        'type': 'integer',
                        'default': 14,
                        'description': 'Days to look back for traffic events'
                    },
                    'attribution_window_days': {
                        'type': 'integer',
                        'default': 14,
                        'description': 'Attribution window in days'
                    },
                    'conversion_type': {
                        'type': 'string',
                        'default': 'order',
                        'description': 'Type of conversion to track (order, detailPageView, shoppingCart, etc.)'
                    },
                    'exclude_amazon_dsp': {
                        'type': 'boolean',
                        'default': False,
                        'description': 'Exclude Amazon DSP traffic from attribution'
                    },
                    'attribution_model_first_touch': {
                        'type': 'boolean',
                        'default': False,
                        'description': 'Use first-touch attribution instead of last-click'
                    }
                },
                'default_parameters': {
                    'advertiser_id': 11111111,
                    'campaign_ids': [22222222, 33333333, 44444444, 55555555],
                    'target_asins': ['ASIN1234', 'ASIN5678'],
                    'lookback_days': 14,
                    'attribution_window_days': 14,
                    'conversion_type': 'order',
                    'exclude_amazon_dsp': False,
                    'attribution_model_first_touch': False
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': '''Key customization points:
- Search for 'UPDATE' comments to find all customization options
- Default attribution is last-click with 14-day window
- Switch to first-touch by setting attribution_model_first_touch to true
- Adjust conversion_type to track different events (order, shoppingCart, detailPageView, etc.)
- Enable DCO tracking by uncommenting version and target_audience fields
- Set exclude_amazon_dsp to true to focus only on non-Amazon traffic'''
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results for the main analysis query
                if query['query_type'] == 'main_analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Attribution Analysis Results',
                        'sample_data': {
                            'rows': [
                                {
                                    'site_name': 'Site 1',
                                    'campaign_type': 'Display',
                                    'campaign': 'Summer Sale',
                                    'placement': 'Homepage Banner',
                                    'ad_id_or_search_keyword_id': 'AD_12345',
                                    'conversions': 150,
                                    'total_product_sales': 4500.00,
                                    'total_units_sold': 175,
                                    'users_that_purchased': 145,
                                    'user_reach': 10000,
                                    'impressions': 50000,
                                    'clicks': 500,
                                    'user_purchase_rate': 1.45
                                },
                                {
                                    'site_name': 'Site 2',
                                    'campaign_type': 'Display',
                                    'campaign': 'Summer Sale',
                                    'placement': 'Sidebar',
                                    'ad_id_or_search_keyword_id': 'AD_12346',
                                    'conversions': 85,
                                    'total_product_sales': 2550.00,
                                    'total_units_sold': 95,
                                    'users_that_purchased': 82,
                                    'user_reach': 8500,
                                    'impressions': 42500,
                                    'clicks': 340,
                                    'user_purchase_rate': 0.96
                                },
                                {
                                    'site_name': 'Site 3',
                                    'campaign_type': 'Video',
                                    'campaign': 'Brand Awareness',
                                    'placement': 'Pre-roll',
                                    'ad_id_or_search_keyword_id': 'AD_12347',
                                    'conversions': 220,
                                    'total_product_sales': 6600.00,
                                    'total_units_sold': 250,
                                    'users_that_purchased': 210,
                                    'user_reach': 15000,
                                    'impressions': 75000,
                                    'clicks': 750,
                                    'user_purchase_rate': 1.40
                                },
                                {
                                    'site_name': 'Site 4',
                                    'campaign_type': 'Display',
                                    'campaign': 'Retargeting',
                                    'placement': 'Footer',
                                    'ad_id_or_search_keyword_id': 'AD_12348',
                                    'conversions': 45,
                                    'total_product_sales': 1350.00,
                                    'total_units_sold': 50,
                                    'users_that_purchased': 43,
                                    'user_reach': 5000,
                                    'impressions': 25000,
                                    'clicks': 200,
                                    'user_purchase_rate': 0.86
                                },
                                {
                                    'site_name': 'Site 5',
                                    'campaign_type': 'Native',
                                    'campaign': 'Content Push',
                                    'placement': 'In-feed',
                                    'ad_id_or_search_keyword_id': 'AD_12349',
                                    'conversions': 180,
                                    'total_product_sales': 5400.00,
                                    'total_units_sold': 200,
                                    'users_that_purchased': 175,
                                    'user_reach': 12000,
                                    'impressions': 60000,
                                    'clicks': 600,
                                    'user_purchase_rate': 1.46
                                }
                            ]
                        },
                        'interpretation_markdown': """Based on these attribution results:

**High-Performing Sites:**
- **Site 5 (Native)**: Highest user purchase rate at 1.46% with in-feed native placements
- **Site 1 (Display)**: Strong 1.45% conversion rate on homepage banner placements  
- **Site 3 (Video)**: Pre-roll video ads achieving 1.40% purchase rate

**Optimization Opportunities:**
- **Site 4 (Display)**: Footer placement underperforming at 0.86% - consider moving to more prominent positions
- **Site 2 (Display)**: Sidebar placement at 0.96% - test different creative formats or messaging

**Format Performance Analysis:**
- Native and video formats outperform standard display
- Placement matters: Homepage > Sidebar > Footer for display ads
- Pre-roll video shows strong engagement and conversion

**Recommended Actions:**
1. Increase budget allocation to Sites 1, 3, and 5
2. Test native ad formats on underperforming sites
3. Move Site 4 ads from footer to above-the-fold placements
4. Consider pausing or optimizing Site 2 sidebar campaigns
5. Expand successful video pre-roll strategy to additional sites""",
                        'insights': [
                            'Native in-feed placements drive the highest user purchase rate at 1.46%',
                            'Homepage banner placements outperform sidebar by 51% in conversion rate',
                            'Video pre-roll shows strong performance with 1.40% purchase rate',
                            'Footer placements significantly underperform at 0.86% purchase rate',
                            'Sites with purchase rates above 1.4% should receive increased budget allocation'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example results")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'site_name',
                'display_name': 'Site Name',
                'definition': 'The website or platform where the ad was served through Amazon Ad Server',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'campaign_type',
                'display_name': 'Campaign Type',
                'definition': 'The type of advertising campaign (Display, Video, Native, etc.)',
                'metric_type': 'dimension',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'campaign',
                'display_name': 'Campaign',
                'definition': 'The name of the advertising campaign',
                'metric_type': 'dimension',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'placement',
                'display_name': 'Placement',
                'definition': 'The specific location on the site where the ad was displayed',
                'metric_type': 'dimension',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'ad_id_or_search_keyword_id',
                'display_name': 'Ad ID or Keyword ID',
                'definition': 'Unique identifier for the creative or search keyword',
                'metric_type': 'dimension',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversions',
                'display_name': 'Conversions',
                'definition': 'Number of distinct conversion events attributed to the campaign based on the selected attribution model',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_product_sales',
                'display_name': 'Total Product Sales',
                'definition': 'The total ad-attributed sales value in local currency',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_units_sold',
                'display_name': 'Total Units Sold',
                'definition': 'The total ad-attributed quantity of products sold',
                'metric_type': 'metric',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'users_that_purchased',
                'display_name': 'Users That Purchased',
                'definition': 'Distinct count of users who made an attributed purchase after ad exposure',
                'metric_type': 'metric',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_reach',
                'display_name': 'User Reach',
                'definition': 'Number of unique users exposed to the campaign',
                'metric_type': 'metric',
                'display_order': 10
            },
            {
                'guide_id': guide_id,
                'metric_name': 'impressions',
                'display_name': 'Impressions',
                'definition': 'Total number of times the ad was displayed',
                'metric_type': 'metric',
                'display_order': 11
            },
            {
                'guide_id': guide_id,
                'metric_name': 'clicks',
                'display_name': 'Clicks',
                'definition': 'Total number of clicks on the ad',
                'metric_type': 'metric',
                'display_order': 12
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_purchase_rate',
                'display_name': 'User Purchase Rate',
                'definition': 'Percentage of exposed users who made a purchase (users_that_purchased / user_reach * 100)',
                'metric_type': 'metric',
                'display_order': 13
            },
            {
                'guide_id': guide_id,
                'metric_name': 'match_age',
                'display_name': 'Match Age',
                'definition': 'Time in seconds between the traffic event and the conversion event',
                'metric_type': 'metric',
                'display_order': 14
            },
            {
                'guide_id': guide_id,
                'metric_name': 'match_rank',
                'display_name': 'Match Rank',
                'definition': 'Ranking of traffic events for attribution (1 = attributed event based on the model)',
                'metric_type': 'metric',
                'display_order': 15
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created Amazon Ad Server Custom Attribution guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_adserver_attribution_guide()
    sys.exit(0 if success else 1)