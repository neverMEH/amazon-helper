#!/usr/bin/env python3
"""
Seed script for Amazon Ad Server - Audiences with ASIN Conversions Build Guide
This script creates the guide content in the database
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

def create_ad_server_audience_guide():
    """Create the Amazon Ad Server - Audiences with ASIN Conversions guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_ad_server_audience_conversions',
            'name': 'Amazon Ad Server - Audiences with ASIN Conversions',
            'category': 'Audience Insights',
            'short_description': 'Measure audience performance, behavior, and preference for off-Amazon media served through Amazon Ad Server and discover conversion metrics by audience segments.',
            'tags': ['ad server', 'audience segments', 'ASIN conversions', 'behavior analysis', 'custom attribution', 'DPV', 'ATC'],
            'icon': 'Users',
            'difficulty_level': 'advanced',
            'estimated_time_minutes': 40,
            'prerequisites': [
                'Amazon Ad Server campaign data available in AMC',
                'ASIN conversions present in custom attribution datasets',
                'Amazon DSP or SA entity IDs added to AMC instance',
                'Understanding of audience segmentation'
            ],
            'is_published': True,
            'display_order': 2,
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

This Instructional Query (IQ) measures audience performance, behavior, and preference for off-Amazon media served through Amazon Ad Server and helps in discovering conversion metrics by audience segments.

By analyzing conversions across different audience segments, advertisers can:
- Identify high-performing audience segments for optimization
- Understand audience behavior patterns and preferences
- Make data-driven decisions about audience targeting strategies
- Optimize media spend allocation across segments

## 1.2 Requirements

All advertisers globally who run campaigns using Amazon Ad Server are eligible to use this IQ. To use this query, you need:

- **Amazon Ad Server campaign data** available in your AMC instance
- **ASIN conversions** present in custom attribution data sets in AMC
- **Amazon DSP or SA entity IDs** added to the AMC instance (if conversions are not available in custom attribution data sets)

**Important:** If conversions are not available in custom attribution data sets, please create a request to add your Amazon DSP or SA entity IDs to the AMC instance to enable conversion tracking.""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Tables Used

### adserver_traffic_by_user_segments
This table contains all impressions and clicks measured by Amazon Ad Server breakout by segments. Key fields include:
- User segments and behavior data
- Impression and click events
- Campaign and placement identifiers
- Timestamp information for attribution windows

### conversions
This data source contains the subset of relevant conversions, including:
- **Purchase events** (orders)
- **Detail page views** (DPV)
- **Add-to-cart events** (ATC)
- **First subscribe and save events**

**Conversion Relevance Criteria:**
A conversion is deemed relevant to your AMC instance if:
1. User must have been served an impression or click within **28 days** before conversion
2. Traffic events include: `sponsored_ads_traffic`, `dsp_impressions`, `adserver_traffic`
3. Conversion must be from tracked ASIN or brand family (brand halo)
4. 28-day window doubles standard attribution window
5. Higher volume than standard attribution due to:
   - Longer lookback period
   - Not competition-aware
   - Includes both viewable and non-viewable impressions

### conversions_with_relevance
Same conversions as above but includes campaign-dependent columns. Each conversion can appear on multiple rows if relevant to multiple campaigns. Use this table when filtering by specific campaigns for better performance.

## 2.2 Data Returned

This query returns comprehensive metrics broken down by Amazon Ad Server dimensions and audience segments:

### Delivery Metrics
- **Impressions**: Total impressions by segment
- **Clicks**: Total clicks by segment

### Conversion Metrics (with attribution split)
- **DPV (Detail Page Views)**
  - Total DPV
  - DPV Views (impression-attributed)
  - DPV Clicks (click-attributed)
- **ATC (Add to Cart)**
  - Total ATC
  - ATC Views (impression-attributed)
  - ATC Clicks (click-attributed)
- **Purchases**
  - Total Purchases
  - Purchases Views (impression-attributed)
  - Purchases Clicks (click-attributed)

### Dimensions
- Advertiser and campaign information
- Placement details
- Site information
- Audience behavior segments

## 2.3 Query Templates

Three query templates are provided:
1. **Exploratory Query 1**: Campaign and Advertisers exploration
2. **Exploratory Query 2**: ASIN Conversions identification
3. **Main Analysis Query**: Custom Audience Attribution of ASIN Conversions

Use the exploratory queries first to make informed decisions about the filters to apply in the main analysis query.""",
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

### Query: Custom Audience Attribution of ASIN Conversions

| advertiser_name | campaign_name | site_name | placement_name | segment | impressions | clicks | Total_DPV | DPV_views | DPV_clicks | Total_ATC | ATC_views | ATC_clicks | Total_Purchases | Purchases_views | Purchases_clicks |
|-----------------|---------------|-----------|----------------|---------|-------------|--------|-----------|-----------|------------|-----------|-----------|------------|-----------------|-----------------|------------------|
| Brand ABC | Summer Campaign | news-site.com | Homepage_Banner | High_Intent_Shoppers | 50,000 | 1,250 | 850 | 600 | 250 | 425 | 300 | 125 | 212 | 150 | 62 |
| Brand ABC | Summer Campaign | news-site.com | Homepage_Banner | New_Customers | 75,000 | 1,125 | 562 | 450 | 112 | 281 | 225 | 56 | 140 | 112 | 28 |
| Brand ABC | Summer Campaign | sports-blog.com | Sidebar_300x250 | High_Intent_Shoppers | 30,000 | 900 | 630 | 450 | 180 | 315 | 225 | 90 | 157 | 112 | 45 |
| Brand ABC | Summer Campaign | sports-blog.com | Sidebar_300x250 | Deal_Seekers | 45,000 | 675 | 337 | 270 | 67 | 168 | 135 | 33 | 84 | 67 | 17 |
| Brand XYZ | Fall Promo | lifestyle-mag.com | Article_Mid | Frequent_Buyers | 60,000 | 1,800 | 1,260 | 900 | 360 | 630 | 450 | 180 | 315 | 225 | 90 |

## 3.2 Metrics Defined

### Delivery Metrics
- **Impressions**: Total number of ad impressions served to users in the segment
- **Clicks**: Total number of clicks from users in the segment

### Conversion Metrics
- **DPV (Detail Page Views)**: Total conversions for detail page views
  - **DPV Views**: DPV conversions attributed to impressions
  - **DPV Clicks**: DPV conversions attributed to clicks
- **ATC (Add to Cart)**: Total add-to-cart conversions
  - **ATC Views**: ATC conversions attributed to impressions
  - **ATC Clicks**: ATC conversions attributed to clicks
- **Purchases**: Total sales attributed
  - **Purchases Views**: Purchases attributed to impressions
  - **Purchases Clicks**: Purchases attributed to clicks

### Dimensions
- **Behavior Segment**: User behavior segment classification (e.g., High_Intent_Shoppers, New_Customers, Deal_Seekers)
- **Site Name**: The website where the ad was served
- **Placement**: The specific ad placement on the site

### Attribution Logic
- **Model**: Last Click Over Impression (default)
- **Lookback Window**: 14 days (customizable up to 28 days)
- **Priority**: Click events prioritized over impression events
- **Date Range**: Only conversions within selected date range included

## 3.3 Insights and Data Interpretation

### Understanding Audience Performance

Advertisers can use this query to understand total conversions by audience segments when users are exposed to media outside of Amazon through Amazon Ad Server. This helps understand audience behavior and preferences.

**Key Performance Indicators by Segment:**

1. **Conversion Rate Analysis**
   - Calculate conversion rates: (Total_Purchases / Impressions) × 100
   - Compare rates across segments to identify high-performers
   - Example: High_Intent_Shoppers showing 0.42% purchase rate vs New_Customers at 0.19%

2. **Attribution Channel Effectiveness**
   - Compare click-attributed vs view-attributed conversions
   - Higher click attribution indicates engaging creative
   - Higher view attribution suggests brand awareness impact

3. **Funnel Analysis by Segment**
   - Track progression: Impressions → DPV → ATC → Purchases
   - Identify drop-off points for each segment
   - Optimize targeting for segments with better funnel progression

### Sample Insights from Example Data

**High Performers:**
- **High_Intent_Shoppers** segment shows:
  - Highest conversion rate (0.42% on news-site.com)
  - Strong click-to-purchase ratio (5.0% of clicks convert)
  - Recommendation: Increase investment in this segment

- **Frequent_Buyers** segment demonstrates:
  - Consistent performance across funnel stages
  - Balanced view/click attribution
  - Recommendation: Maintain current strategy

**Optimization Opportunities:**
- **Deal_Seekers** segment shows:
  - Lower conversion rates (0.19%)
  - Weak click performance
  - Recommendation: Test promotional messaging or different creative

- **New_Customers** segment indicates:
  - High impression volume but lower engagement
  - Opportunity for creative optimization
  - Consider different messaging approach

### Strategic Recommendations

1. **Budget Allocation**: Shift spend toward segments with conversion rates above benchmark
2. **Creative Strategy**: Develop segment-specific creative for underperforming audiences
3. **Placement Optimization**: Focus on site/placement combinations showing best performance
4. **Testing Framework**: A/B test messaging for low-performing segments
5. **Attribution Insights**: Use view/click split to inform creative and placement decisions

Segments with higher conversion rates indicate more responsive audiences where investment should be increased. Consider both immediate conversions and upper-funnel metrics (DPV, ATC) for full-funnel optimization.""",
                'display_order': 3,
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
                'description': 'Use this query to explore advertisers and campaigns in the instance and to select desired campaigns and advertiser for filtering.',
                'sql_query': """-- Exploratory query: Campaign and Advertisers Exploratory Query for Amazon Ad Server Site Traffic
SELECT
  advertiser,
  advertiser_id,
  campaign,
  campaign_id,
  SUM(impressions) AS impressions,
  SUM(clicks) AS total_clicks
FROM
  adserver_traffic
GROUP BY
  1,
  2,
  3,
  4
ORDER BY
  impressions DESC""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'Use this query to identify available advertisers and campaigns in your AMC instance. Focus on campaigns with significant impression volume for meaningful analysis.'
            },
            {
                'guide_id': guide_id,
                'title': 'ASIN Conversions Exploratory Query',
                'description': 'Use this query to identify ASINs based on conversions that are relevant to advertisers in the instance.',
                'sql_query': """-- Exploratory Query: custom attribution exploratory query for ASIN conversion advertisers
SELECT
  tracked_item AS ASIN,
  SUM(conversions) AS purchases
FROM
  conversions c
WHERE
  (event_subtype = 'order'
  OR event_subtype = 'detailPageView'
  OR event_subtype = 'shoppingCart') -- update based on conversion types needed
  AND c.user_id IS NOT NULL
GROUP BY
  1
ORDER BY
  purchases DESC
LIMIT 100""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 2,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query helps identify which ASINs have conversions in your instance. Use the results to filter the main analysis query to relevant products.'
            },
            {
                'guide_id': guide_id,
                'title': 'Audiences with ASIN Conversions Main Query',
                'description': 'Main query for analyzing audience segment performance with ASIN conversions through Amazon Ad Server traffic.',
                'sql_query': """-- Audiences with ASIN Conversion custom attribution
/*
 Custom Attribution of ASIN conversions on all Amazon Ad Server traffic (including users who were exposed to both Amazon & non Amazon ads) Brand Halo conversions set. 
 Attribution methodology - 14 days look back, click over impression 
 Returns number of ASIN conversions per segment and placement, total_product_sales, total_units_sold, users_that_purchased, impressions, clicks, conversion rate,broken down by all Amazon Ad Server entities (not only attributed entities) 
 The default setting for this query is to attribute conversions based on the last click or impression with a 14-day look back window. If you want attribute conversions based on first touch, Use ROW_NUMBER() OVER(PARTITION BY conversion_id ORDER BY match_age DESC) in the ranked CTE (Common Table Expression). Additionally, you may change the look back window from the default 14 days to any other look back window (for example 30 days).
 Search for the comment 'UPDATE' to find the locations where you may update to customize the query for your use case. 
 */
/*UPDATE: Add list of advertiser ids for filtering below */
WITH advertiser_ids (advertiser_id) AS (
  VALUES
    (111111111),
    (222222222),
    (333333333)
),
/*UPDATE: Add list of campaign_ids for filtering below */
campaign_ids (campaign_id) AS (
  VALUES
    (111111111),
    (222222222),
    (333333333)
),
/*UPDATE: Add list of ASINs for filtering below */
asin_conversions (asin_conversion) AS (
  VALUES
    ('ASIN111'),
    ('ASIN222'),
    ('ASIN333')
),
/*
 Read Amazon Ad Server traffic with segments
 */
traffic AS (
  SELECT
    COALESCE(adserver_site, search_vendor) AS adserver_site,
    advertiser,
    advertiser_id,
    campaign,
    campaign_id,
    COALESCE(
      CAST(placement AS VARCHAR),
      CAST(search_ad_group AS VARCHAR)
    ) AS placement_id_or_search_ad_group,
    COALESCE(
      CAST(placement_id AS VARCHAR),
      CAST(search_ad_group_id AS VARCHAR)
    ) AS placement_id_or_search_ad_group_id,
    ad_id,
    -- UPDATE: Uncomment to use dco ad versions
    /*
     version_name, 
     version_id,
     target_audience_name,
     target_audience_id,
     */
    behavior_segment_name,
    user_id,
    event_dt_utc,
    impressions,
    clicks
  FROM
    TABLE(
      EXTEND_TIME_WINDOW('adserver_traffic_by_user_segments', 'P14D', 'P0D')
    )
  WHERE
    (
      clicks = 1
      OR impressions = 1
    ) -- UPDATE. Comment this if you want to look at campaigns including Amazon DSP traffic.
    AND (
      adserver_site NOT SIMILAR TO '%amazon%'
      AND adserver_site NOT SIMILAR TO '%Amazon%'
      AND adserver_site NOT SIMILAR TO '%AMAZON%'
      AND adserver_site NOT SIMILAR TO '%imdb%'
      AND adserver_site NOT SIMILAR TO '%IMDB%'
      AND adserver_site NOT SIMILAR TO '%IMDb%'
    ) -- UPDATE: Uncomment if you want to use advertiser_ids
    /* AND advertiser_id IN (SELECT advertiser_id FROM advertiser_ids ) */
    -- UPDATE: Uncomment in order to filter by campaign_ids
    /* AND campaign_id IN (SELECT campaign_id FROM campaign_ids) */
),
/* 
 Read conversion events from the amazon conversions data source.
 Join conversion events to traffic events based on the user ID.
 Determine a match age based on the time from the conversion event.
 For each conversion event, rank all the matching traffic events based on click over impression and match age.
 */
matched_and_ranked AS (
  SELECT
    t.adserver_site,
    t.advertiser,
    t.advertiser_id,
    t.campaign,
    t.campaign_id,
    t.placement_id_or_search_ad_group,
    t.placement_id_or_search_ad_group_id,
    t.ad_id,
    -- UPDATE: Uncomment to use dco ad versions
    /*
     t.version_name, 
     t.version_id,
     t.target_audience_name,
     t.target_audience_id,
     */
    c.user_id,
    t.behavior_segment_name,
    t.event_dt_utc,
    c.conversion_id,
    c.event_subtype,
    c.event_category,
    CASE
      WHEN c.event_subtype = 'detailPageView' THEN c.conversions
      ELSE 0
    END AS DPV,
    CASE
      WHEN c.event_subtype = 'shoppingCart' THEN c.conversions
      ELSE 0
    END AS ATC,
    CASE
      WHEN c.event_category = 'purchase' THEN c.conversions
      ELSE 0
    END AS Purchases,
    ROW_NUMBER() OVER(
      PARTITION BY conversion_id,
      behavior_segment_name
      ORDER BY
        (clicks * -1),
        SECONDS_BETWEEN(t.event_dt_utc, c.event_dt_utc) asc
    ) AS match_rank,
    impressions,
    clicks
  FROM
    -- UPDATE: Uncomment and use conversions_with_relevance instead of conversions only if you filter by campaign_id (performance wise)
    /* conversions_with_relevance c */
    -- UPDATE: Comment and use conversions_with_relevance if filtering by campaign
    conversions c
    INNER JOIN traffic t ON c.user_id = t.user_id
  WHERE
    SECONDS_BETWEEN(t.event_dt_utc, c.event_dt_utc) BETWEEN 0 AND 14 * 24 * 60 * 60
    /* 
     optional conversion types: 'babyRegistry', 'customerReview', 'detailPageView', 'shoppingCart',
     'snsSubscription', 'weddingRegistry', or 'wishList'.
     */
    AND (
      event_subtype = 'detailPageView'
      OR event_subtype = 'shoppingCart'
      OR event_category = 'purchase'
    ) -- UPDATE: Uncomment in order to filter by campaign_ids
    /*AND c.campaign_id IN (SELECT campaign_id FROM campaign_ids) */
    -- UPDATE: Uncomment to filter by asin_conversions
    /*AND c.tracked_item IN (SELECT asin_conversion FROM asin_conversions ) */
    -- UPDATE: Uncomment to filter by advertiser id
    /*AND c.advertiser_id IN (SELECT advertiser_id FROM advertiser_ids ) */
),
/*
 Filter to only the best matching traffic event ('winner') for each amazon conversion event.
 */
attributed_conversions AS (
  SELECT
    adserver_site,
    advertiser,
    advertiser_id,
    campaign,
    campaign_id,
    placement_id_or_search_ad_group,
    placement_id_or_search_ad_group_id,
    ad_id,
    -- UPDATE: Uncomment to use dco ad versions
    /*
     version_name, 
     version_id,
     target_audience_name,
     target_audience_id,
     */
    behavior_segment_name,
    SUM(DPV) AS DPV,
    SUM(
      CASE
        WHEN DPV = 1
        AND impressions = 1 THEN DPV
        ELSE 0
      END
    ) AS DPV_views,
    SUM(
      CASE
        WHEN DPV = 1
        AND clicks = 1 THEN DPV
        ELSE 0
      END
    ) AS DPV_clicks,
    SUM(ATC) AS ATC,
    SUM(
      CASE
        WHEN ATC = 1
        AND impressions = 1 THEN ATC
        ELSE 0
      END
    ) AS ATC_views,
    SUM(
      CASE
        WHEN ATC = 1
        AND clicks = 1 THEN ATC
        ELSE 0
      END
    ) AS ATC_clicks,
    SUM(Purchases) AS Purchases,
    SUM(
      CASE
        WHEN Purchases = 1
        AND impressions = 1 THEN Purchases
        ELSE 0
      END
    ) AS Purchases_views,
    SUM(
      CASE
        WHEN Purchases = 1
        AND clicks = 1 THEN Purchases
        ELSE 0
      END
    ) AS Purchases_clicks
  FROM
    matched_and_ranked r
  WHERE
    match_rank = 1
  GROUP BY
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9 -- UPDATE: Uncomment to use dco ad versions
    /*
     ,10, 
     11,
     12,
     13
     */
),
/* 
 Calculating the user_reach, total impressions and total clicks metrics
 from traffic, based only on the relevant dates
 */
relevant_traffic AS (
  SELECT
    adserver_site,
    advertiser,
    advertiser_id,
    campaign,
    campaign_id,
    placement_id_or_search_ad_group,
    placement_id_or_search_ad_group_id,
    -- UPDATE: Uncomment to use dco ad versions
    /*
     version_name, 
     version_id,
     target_audience_name,
     target_audience_id,
     */
    behavior_segment_name,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks
  FROM
    traffic
  WHERE
    event_dt_utc >= BUILT_IN_PARAMETER('TIME_WINDOW_START')
    AND event_dt_utc < BUILT_IN_PARAMETER('TIME_WINDOW_END')
  GROUP BY
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8 -- UPDATE: Uncomment to use dco ad versions
    /*
     ,9, 
     10,
     11,
     12
     */
)
/*
 Final query 
 */
SELECT
  t.advertiser AS advertiser_name,
  t.advertiser_id AS advertiser_id,
  t.campaign AS campaign_name,
  t.campaign_id AS campaign_id,
  t.adserver_site AS site_name,
  t.placement_id_or_search_ad_group AS placement_or_search_ad_group_name,
  t.placement_id_or_search_ad_group_id AS placement_or_search_ad_group_id,
  -- UPDATE: Uncomment to use dco ad versions
  /*
   t.version_name AS Ad_Version,
   t.version_id AS Version_ID,
   t.target_audience_name AS Target_Audience,
   t.target_audience_id AS Target_Audience_ID,
   */
  t.behavior_segment_name AS segment,
  SUM(COALESCE(t.impressions, 0)) AS impressions,
  SUM(COALESCE(t.clicks, 0)) AS clicks,
  SUM(COALESCE(ac.DPV, 0)) AS Total_DPV,
  SUM(COALESCE(ac.DPV_views, 0)) AS Total_DPV_views,
  SUM(COALESCE(ac.DPV_clicks, 0)) AS Total_DPV_clicks,
  SUM(COALESCE(ac.ATC, 0)) AS Total_ATC,
  SUM(COALESCE(ac.ATC_views, 0)) AS Total_ATC_views,
  SUM(COALESCE(ac.ATC_clicks, 0)) AS Total_ATC_clicks,
  SUM(COALESCE(ac.Purchases, 0)) AS Total_Purchases,
  SUM(COALESCE(ac.Purchases_views, 0)) AS Total_Purchases_views,
  SUM(COALESCE(ac.Purchases_clicks, 0)) AS Total_Purchases_clicks
FROM
  relevant_traffic t
  INNER JOIN attributed_conversions ac ON ac.placement_id_or_search_ad_group_id = t.placement_id_or_search_ad_group_id
  AND ac.behavior_segment_name = t.behavior_segment_name
  AND ac.adserver_site = t.adserver_site -- UPDATE: Uncomment to use ad dco versions
  /* AND ac.version_id = t.version_id 
   AND ac.target_audience_id = t.target_audience_id */
GROUP BY
  1,
  2,
  3,
  4,
  5,
  6,
  7,
  8 -- UPDATE: Uncomment to use dco ad versions
  /*
   ,9, 
   10,
   11,
   12
   */
HAVING
  impressions > 1000
  OR Total_DPV > 0
  OR Total_ATC > 0
  OR Total_Purchases > 0
ORDER BY
  segment,
  Total_Purchases DESC""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': """Key customization points (search for 'UPDATE' comments):
- Default uses Last Click Over Impression attribution
- 14-day lookback window (customizable up to 28 days)
- Filters exclude Amazon-owned properties by default
- Supports DCO ad version tracking when uncommented
- Use conversions_with_relevance table when filtering by campaign for better performance
- To change to first-touch attribution, modify ROW_NUMBER() ordering in matched_and_ranked CTE"""
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
                        'example_name': 'Sample Audience Segment Analysis Results',
                        'sample_data': {
                            'rows': [
                                {
                                    'advertiser_name': 'Brand ABC',
                                    'campaign_name': 'Summer Campaign',
                                    'site_name': 'news-site.com',
                                    'placement_or_search_ad_group_name': 'Homepage_Banner',
                                    'segment': 'High_Intent_Shoppers',
                                    'impressions': 50000,
                                    'clicks': 1250,
                                    'Total_DPV': 850,
                                    'Total_DPV_views': 600,
                                    'Total_DPV_clicks': 250,
                                    'Total_ATC': 425,
                                    'Total_ATC_views': 300,
                                    'Total_ATC_clicks': 125,
                                    'Total_Purchases': 212,
                                    'Total_Purchases_views': 150,
                                    'Total_Purchases_clicks': 62
                                },
                                {
                                    'advertiser_name': 'Brand ABC',
                                    'campaign_name': 'Summer Campaign',
                                    'site_name': 'news-site.com',
                                    'placement_or_search_ad_group_name': 'Homepage_Banner',
                                    'segment': 'New_Customers',
                                    'impressions': 75000,
                                    'clicks': 1125,
                                    'Total_DPV': 562,
                                    'Total_DPV_views': 450,
                                    'Total_DPV_clicks': 112,
                                    'Total_ATC': 281,
                                    'Total_ATC_views': 225,
                                    'Total_ATC_clicks': 56,
                                    'Total_Purchases': 140,
                                    'Total_Purchases_views': 112,
                                    'Total_Purchases_clicks': 28
                                },
                                {
                                    'advertiser_name': 'Brand ABC',
                                    'campaign_name': 'Summer Campaign',
                                    'site_name': 'sports-blog.com',
                                    'placement_or_search_ad_group_name': 'Sidebar_300x250',
                                    'segment': 'High_Intent_Shoppers',
                                    'impressions': 30000,
                                    'clicks': 900,
                                    'Total_DPV': 630,
                                    'Total_DPV_views': 450,
                                    'Total_DPV_clicks': 180,
                                    'Total_ATC': 315,
                                    'Total_ATC_views': 225,
                                    'Total_ATC_clicks': 90,
                                    'Total_Purchases': 157,
                                    'Total_Purchases_views': 112,
                                    'Total_Purchases_clicks': 45
                                },
                                {
                                    'advertiser_name': 'Brand ABC',
                                    'campaign_name': 'Summer Campaign',
                                    'site_name': 'sports-blog.com',
                                    'placement_or_search_ad_group_name': 'Sidebar_300x250',
                                    'segment': 'Deal_Seekers',
                                    'impressions': 45000,
                                    'clicks': 675,
                                    'Total_DPV': 337,
                                    'Total_DPV_views': 270,
                                    'Total_DPV_clicks': 67,
                                    'Total_ATC': 168,
                                    'Total_ATC_views': 135,
                                    'Total_ATC_clicks': 33,
                                    'Total_Purchases': 84,
                                    'Total_Purchases_views': 67,
                                    'Total_Purchases_clicks': 17
                                },
                                {
                                    'advertiser_name': 'Brand XYZ',
                                    'campaign_name': 'Fall Promo',
                                    'site_name': 'lifestyle-mag.com',
                                    'placement_or_search_ad_group_name': 'Article_Mid',
                                    'segment': 'Frequent_Buyers',
                                    'impressions': 60000,
                                    'clicks': 1800,
                                    'Total_DPV': 1260,
                                    'Total_DPV_views': 900,
                                    'Total_DPV_clicks': 360,
                                    'Total_ATC': 630,
                                    'Total_ATC_views': 450,
                                    'Total_ATC_clicks': 180,
                                    'Total_Purchases': 315,
                                    'Total_Purchases_views': 225,
                                    'Total_Purchases_clicks': 90
                                }
                            ]
                        },
                        'interpretation_markdown': """Based on these results:

**High-Performing Segments:**
- **High_Intent_Shoppers** (news-site.com): 
  - 0.42% purchase conversion rate (212/50,000)
  - 5.0% click-to-purchase rate (62/1,250)
  - Strong funnel progression: 1.7% DPV rate → 0.85% ATC rate → 0.42% purchase rate
  - **Recommendation:** Increase budget allocation to this segment

- **Frequent_Buyers** (lifestyle-mag.com):
  - 0.53% purchase conversion rate (315/60,000)
  - Balanced view/click attribution (71% view, 29% click)
  - **Recommendation:** Maintain current strategy, test similar placements

**Underperforming Segments:**
- **Deal_Seekers** (sports-blog.com):
  - 0.19% purchase conversion rate (84/45,000)
  - Low click engagement (1.5% CTR)
  - **Recommendation:** Test promotional messaging or different creative

- **New_Customers** (news-site.com):
  - 0.19% purchase conversion rate despite high reach
  - Lower funnel progression rates
  - **Recommendation:** Develop specific onboarding creative for this segment

**Key Insights:**
1. High_Intent_Shoppers segment delivers 2.2x better conversion rate than average
2. News-site.com placement shows strong performance across multiple segments
3. Click attribution accounts for 29% of purchases, indicating engaged audiences
4. Consider segment-specific creative strategies for optimization""",
                        'insights': [
                            'High_Intent_Shoppers segment shows 2.2x higher conversion rate than Deal_Seekers',
                            'Frequent_Buyers demonstrate best overall performance with 0.53% conversion rate',
                            'News-site.com placement outperforms sports-blog.com by 40% for same segments',
                            'Click-attributed conversions represent 29% of total purchases, indicating engaged audiences',
                            'Deal_Seekers and New_Customers segments require creative optimization or different targeting'
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
                'metric_name': 'behavior_segment_name',
                'display_name': 'Behavior Segment',
                'definition': 'User behavior segment classification used for audience targeting (e.g., High_Intent_Shoppers, New_Customers, Deal_Seekers, Frequent_Buyers)',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'impressions',
                'display_name': 'Impressions',
                'definition': 'Total number of ad impressions served to users in the segment',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'clicks',
                'display_name': 'Clicks',
                'definition': 'Total number of clicks from users in the segment',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'Total_DPV',
                'display_name': 'Total Detail Page Views',
                'definition': 'Total conversions for detail page views, combining both impression and click attribution',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'DPV_views',
                'display_name': 'DPV Views',
                'definition': 'Detail page view conversions attributed to ad impressions (view-through conversions)',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'DPV_clicks',
                'display_name': 'DPV Clicks',
                'definition': 'Detail page view conversions attributed to ad clicks (click-through conversions)',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'Total_ATC',
                'display_name': 'Total Add to Cart',
                'definition': 'Total add-to-cart conversions, combining both impression and click attribution',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'ATC_views',
                'display_name': 'ATC Views',
                'definition': 'Add-to-cart conversions attributed to ad impressions (view-through conversions)',
                'metric_type': 'metric',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'ATC_clicks',
                'display_name': 'ATC Clicks',
                'definition': 'Add-to-cart conversions attributed to ad clicks (click-through conversions)',
                'metric_type': 'metric',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'Total_Purchases',
                'display_name': 'Total Purchases',
                'definition': 'Total sales attributed to the segment, combining both impression and click attribution',
                'metric_type': 'metric',
                'display_order': 10
            },
            {
                'guide_id': guide_id,
                'metric_name': 'Purchases_views',
                'display_name': 'Purchases Views',
                'definition': 'Purchases attributed to ad impressions (view-through conversions)',
                'metric_type': 'metric',
                'display_order': 11
            },
            {
                'guide_id': guide_id,
                'metric_name': 'Purchases_clicks',
                'display_name': 'Purchases Clicks',
                'definition': 'Purchases attributed to ad clicks (click-through conversions)',
                'metric_type': 'metric',
                'display_order': 12
            },
            {
                'guide_id': guide_id,
                'metric_name': 'advertiser_name',
                'display_name': 'Advertiser Name',
                'definition': 'Name of the advertiser running the campaign',
                'metric_type': 'dimension',
                'display_order': 13
            },
            {
                'guide_id': guide_id,
                'metric_name': 'campaign_name',
                'display_name': 'Campaign Name',
                'definition': 'Name of the advertising campaign',
                'metric_type': 'dimension',
                'display_order': 14
            },
            {
                'guide_id': guide_id,
                'metric_name': 'site_name',
                'display_name': 'Site Name',
                'definition': 'The website where the ad was served (excludes Amazon-owned properties by default)',
                'metric_type': 'dimension',
                'display_order': 15
            },
            {
                'guide_id': guide_id,
                'metric_name': 'placement_name',
                'display_name': 'Placement Name',
                'definition': 'The specific ad placement on the site (e.g., Homepage_Banner, Sidebar_300x250)',
                'metric_type': 'dimension',
                'display_order': 16
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created Amazon Ad Server - Audiences with ASIN Conversions guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_ad_server_audience_guide()
    sys.exit(0 if success else 1)