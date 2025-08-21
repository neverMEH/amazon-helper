#!/usr/bin/env python3
"""
Seed script for Amazon Ad Server - Campaign Overlap and Conversions Build Guide
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

def create_adserver_campaign_overlap_guide():
    """Create the Amazon Ad Server - Campaign Overlap and Conversions guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_adserver_campaign_overlap',
            'name': 'Amazon Ad Server - Campaign Overlap and Conversions',
            'category': 'Campaign Optimization',
            'short_description': 'Measure overlap between multiple campaigns and evaluate impact on conversion KPIs to optimize audience targeting and campaign layering strategies.',
            'tags': ['ad server', 'campaign overlap', 'reach analysis', 'conversion attribution', 'multi-touch', 'audience overlap'],
            'icon': 'Users',
            'difficulty_level': 'advanced',
            'estimated_time_minutes': 35,
            'prerequisites': [
                'At least two active campaigns in AMC instance',
                'Amazon Ad Server conversion tracking setup',
                'Understanding of attribution models',
                'Basic knowledge of exposure groups'
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

This instructional query (IQ) measures overlap between multiple campaigns and evaluates impact on conversion KPIs. Understanding audience overlap (reach) helps estimate impact on all or specific conversion activities. This also helps uncover insights such as sizing the reach overlap between awareness and re-engagement campaigns, and whether layering brand marketing tactics over performance marketing engagements results in better conversion KPIs.

## 1.2 Requirements

To use this query, the AMC instance must have at least two campaigns that were active within reporting period. The advertiser also needs to use Amazon Ad Server conversion tracking solutions to be able to estimate the impact of overlapping audiences on conversions. Advertisers that don't use Amazon Ad Server conversion tracking can still use this query, but fields with conversion metrics will be empty.""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Tables Used

- **adserver_traffic**: This table contains all impressions and clicks measured by Amazon Ad Server.
- **adserver_conversions**: This table contains unattributed Amazon Ad Server conversion activities.

## 2.2 Data Returned

This query will return the count of unique users reached exclusively by each campaign and in overlap with another campaign (defined as exposure groups). It will return the size of each exposure group, the total conversions, the distinct count of users who converted, and the conversion rate. The metrics can be calculated for all campaigns that had traffic in the selected date range.

## 2.3 Query Templates

Exploratory queries are provided in section 4. Use the exploratory queries to make decisions about the filters to add to the query template in section 5.""",
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

### Campaign Overlap and Conversion Analysis Results

| exposure_group | reach | converted_users | conversions | size_of_the_exposure_group | conversion_rate | conversions_per_user |
|----------------|-------|-----------------|-------------|----------------------------|-----------------|---------------------|
| Campaign 1 | 5,020,234 | 19,077 | 28,000 | 50.86% | 0.38% | 1.47 |
| Campaign 2 | 3,870,433 | 7,741 | 11,373 | 39.21% | 0.20% | 1.47 |
| Campaign 1 & Campaign 2 | 980,586 | 18,729 | 32,474 | 9.93% | 1.91% | 1.73 |

## 3.2 Metrics Defined

### Key Metrics

- **exposure_group**: Determines a campaign or campaign combination that delivered an ad to a user
- **reach**: Number of distinct users exposed to the ads in each exposure group
- **converted_users**: Number of distinct users who made a conversion
- **conversions**: Total number of conversions made by users in each exposure group
- **conversion_rate**: The ratio of converted_users to reach ((converted_users/reach)*100)
- **conversions_per_user**: Number of conversions per user (conversions/converted_users)
- **size_of_the_exposure_group**: Percentage of users in each exposure group out of total users

### Exposure Groups Definition

- **Campaign 1**: Users exposed to ads from campaign 1 only
- **Campaign 2**: Users exposed to ads from campaign 2 only
- **Campaign 1 & Campaign 2**: Users exposed to ads from both campaigns

### Attribution Logic

- Last touch attribution with 30-day lookback window (customizable)
- Includes post-campaign conversions within lookback window
- Both impressions and clicks considered for reach calculation

## 3.3 Insights and Data Interpretation

### Key insights from example data:

- **50.86%** of users reached exclusively by Campaign 1 with **0.38%** conversion rate
- **39.21%** of users reached exclusively by Campaign 2 with **0.20%** conversion rate but **1.47** conversions per user
- Users exposed to both campaigns show **1.91%** conversion rate - **5x higher** than single campaign exposure
- Multi-campaign exposure drives higher conversion rates and more conversions per user

### Recommendations Based on Results

**Campaign Synergy Effect**: The dramatically higher conversion rate (1.91%) for users exposed to both campaigns compared to single campaign exposure (0.38% and 0.20%) indicates strong synergy between campaigns.

**Optimization Opportunities**:
1. **Increase Overlap**: Consider expanding targeting to increase the overlap audience segment
2. **Sequential Messaging**: Leverage the campaigns in sequence for better conversion outcomes
3. **Budget Allocation**: Allocate more budget to tactics that drive multi-campaign exposure
4. **Creative Alignment**: Ensure creative messaging is complementary across campaigns

**Audience Insights**:
- Users who see both campaigns are **5-9x more likely to convert**
- The overlapping audience segment (9.93%) represents high-value customers
- Consider creating dedicated remarketing campaigns for this high-intent audience""",
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
                'title': 'Campaigns and Advertisers Exploratory Query',
                'description': 'Use this query to explore advertisers and campaigns in the instance to select desired campaigns and advertiser IDs.',
                'sql_query': """-- Instructional query: Campaigns and Advertisers Exploratory Query for 'Amazon Ad Server - Campaign Overlap and Conversions'
SELECT
  advertiser,
  advertiser_id,
  campaign,
  campaign_id,
  SUM(impressions) AS imps,
  SUM(clicks) AS total_clicks
FROM
  adserver_traffic
GROUP BY
  1,
  2,
  3,
  4""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query helps you identify all available advertisers and campaigns in your AMC instance. Use the advertiser_id and campaign_id values from this query in the main analysis query.'
            },
            {
                'guide_id': guide_id,
                'title': 'Conversion Activity Exploratory Query',
                'description': 'Use this query to identify conversion activity IDs relevant to each advertiser in the instance.',
                'sql_query': """-- Instructional query: Conversion Activity Exploratory Query for 'Amazon Ad Server - Campaign Overlap and Conversions'
SELECT
  advertiser,
  advertiser_id,
  conversion_activity,
  conversion_activity_id,
  SUM(conversions) AS total_conversions
FROM
  adserver_conversions
GROUP BY
  1,
  2,
  3,
  4""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 2,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query shows all conversion activities tracked in your AMC instance. Use the conversion_activity_id values to filter specific conversion types in the main analysis query.'
            },
            {
                'guide_id': guide_id,
                'title': 'Campaign Overlap and Conversions Main Query',
                'description': 'Main query for measuring campaign overlap and evaluating conversion impact across multiple campaigns.',
                'sql_query': """-- Instructional Query: Amazon Ad Server - Campaign Overlap and Conversions
/*This instructional query (IQ) measures overlap between multiple campaigns and
 evaluates impact on conversion KPIs. Understanding audience overlap (reach) helps 
 estimate impact on all or specific conversion activities. This also helps uncover 
 insights such as sizing the reach overlap between awareness and re-engagement 
 campaigns, and whether layering brand marketing tactics over performance marketing 
 engagements results in better conversion KPIs. */
/* REQUIRED UPDATE your advertiser ID(s) */
WITH advertiser_ids (advertiser_id) AS (
  VALUES
    (1111111)
),
/* REQUIRED UPDATE your campaign ID(s) */
campaign_ids (campaign_id) AS (
  VALUES
    (222222222),
    (33333333)
),
/* OPTIONAL UPDATE your conversion activity id(s).
 If you update this section, you must uncomment the conversion_activity_ids 
 WHERE clause. Search 'UPDATE conversion_activity_id' */
conversion_activity_ids (conversion_activity_id) AS (
  VALUES
    (4444444)
),
-- gather impressions and clicks --
traffic_only AS (
  SELECT
    user_id,
    campaign_id,
    campaign,
    advertiser_id
  FROM
    adserver_traffic
  WHERE
    advertiser_id IN (
      SELECT
        advertiser_id
      FROM
        advertiser_ids
    )
    AND campaign_id IN (
      SELECT
        campaign_id
      FROM
        campaign_ids
    )
    AND (
      impressions = 1
      OR clicks = 1
    )
),
/* Create exposure_group dimension from 
 campaigns provided in the beginning of the query*/
assembled AS (
  SELECT
    user_id,
    ARRAY_SORT(COLLECT(DISTINCT campaign)) AS Exposure_Group
  FROM
    traffic_only
  GROUP BY
    1
),
/* Calculating conversions. Prepare traffic data set that include an extra 30 
 days of traffic post report end date to be used later to filter out conversions 
 that attributed to traffic that is not within the reporting period */
traffic AS (
  -- Read impression or clicks events.
  SELECT
    advertiser_id,
    campaign_id,
    campaign,
    clicks,
    event_dt_utc AS traffic_dt,
    event_date_utc,
    impressions,
    user_id
    /* 
     We are taking an extra 30 days of traffic events beyond the reporting period set by 
     the time window in order to have the full user journey when attributing the extra 30 
     days of conversion events. This will ensure that we are attributing conversions to 
     the right event and counting it as an attributed conversion only if the traffic event 
     is within the report period. Any conversions that could be attributed to traffic 
     outside the reporting period will be removed later in this query in the 'winners' CTE.
     */
    /* 
     OPTIONAL UPDATE change the attribution window from the following default 30 days 
     to another, and update the same value to 'adserver_conversions' extended time period below 
     */
  FROM
    TABLE(
      EXTEND_TIME_WINDOW('adserver_traffic', 'P0D', 'P30D')
    )
  WHERE
    advertiser_id IN (
      SELECT
        advertiser_id
      FROM
        advertiser_ids
    )
    AND (
      clicks = 1
      OR impressions = 1
    )
),
/* 
 Read conversion events from the adserver_conversions data source.
 Join conversion events to traffic events based on user_id and advertiser_id.
 Determine a match type based on the traffic event type and time from the conversion 
 event. 
 */
matched AS (
  SELECT
    t.advertiser_id,
    t.campaign_id,
    campaign,
    t.event_date_utc,
    -- traffic time.
    t.traffic_dt,
    c.conversion_id,
    c.conversion_activity_id,
    c.revenue,
    c.conversions,
    c.user_id,
    -- Determine a match type based on the traffic event type impressions vs clicks
    CASE
      WHEN t.clicks = 1 --If traffic event is a click
      THEN 1
      WHEN t.impressions = 1 --If traffic event is an impression
      THEN 2
    END AS match_type,
    SECONDS_BETWEEN(t.traffic_dt, c.event_dt_utc) AS match_age
    /* OPTIONAL UPDATE change the attribution window from the following default 30 days 
     to another, and update the same value to 'adserver_traffic' extended time period above */
  FROM
    TABLE(
      EXTEND_TIME_WINDOW('adserver_conversions', 'P0D', 'P30D')
    ) c
    INNER JOIN traffic t ON c.user_id = t.user_id
    AND c.advertiser_id = t.advertiser_id
    /* OPTIONAL UPDATE conversion_activity_id: Uncomment the line below if you used conversion_activity filter in the beginning of the query */
    -- where conversion_activity_id IN (SELECT conversion_activity_id FROM conversion_activity_ids)
),
/* For each conversion event, rank all the matching traffic events based on 
 match type and then match age. */
ranked AS (
  SELECT
    user_id,
    advertiser_id,
    campaign_id,
    campaign,
    event_date_utc,
    traffic_dt,
    revenue,
    conversions,
    --con_user_id,
    match_type,
    -- Rank the match based on match type and then age.
    ROW_NUMBER() OVER(
      PARTITION BY conversion_id
      ORDER BY
        match_type,
        match_age
    ) AS match_rank,
    conversion_id
  FROM
    matched
  WHERE
    -- Lookback window: define lookback window for impressions and clicks, it will instruct the workflow to select traffic events eligible for attribution based on their 'age'/ day distance from conversion.
    match_age BETWEEN 0 AND CASE
      WHEN match_type = 1 --clicks
      /* OPTIONAL UPDATE: The first number, X, of the expression 'X * 24 * 60 * 60' can be 
       configured with a number of days for the attribution window for clicks. 
       In this example, the attribution window, X, is 30 days for clicks. 
       If X is updated here, UPDATE also the attribution window in 'adserver_traffic' 
       and in 'adserver_conversions' extended the time periods above based on 
       the attribution window for impressions or for clicks, the larger of the two */
      THEN 30 * 24 * 60 * 60
      WHEN match_type = 2 --impressions
      /* OPTIONAL UPDATE: The first number, X, of the expression 'X * 24 * 60 * 60' can be 
       configured with a number of days for the attribution window for impressions. 
       In this example, the attribution window, X, is 30 days for impressions. 
       If X is updated here, UPDATE also the attribution window in 'adserver_traffic' 
       and in 'adserver_conversions' extended the time periods above based on 
       the attribution window for impressions or for clicks, the larger of the two */
      THEN 30 * 24 * 60 * 60
    END
    /* OPTIONAL UPDATE: To use click-based attribution, uncomment the line below.
     To consider both impressions and clicks, keep the line below commented out.
     */
    -- AND match_type = 2
),
-- Filter to only the best matching traffic event.
winners AS (
  SELECT
    campaign_id,
    campaign,
    user_id,
    traffic_dt,
    conversions,
    revenue
  FROM
    ranked
  WHERE
    -- keep only conversions with winners that happened in the report time range
    traffic_dt > BUILT_IN_PARAMETER('TIME_WINDOW_START')
    AND traffic_dt < BUILT_IN_PARAMETER('TIME_WINDOW_END')
    AND campaign_id IN (
      SELECT
        campaign_id
      FROM
        campaign_ids
    )
    AND -- Filter to only the best matching traffic event.
    match_rank = 1
),
joined AS (
  SELECT
    a.Exposure_Group,
    a.user_id,
    w.conversions,
    w.revenue,
    w.user_id AS con_user_id
  FROM
    assembled a
    LEFT JOIN winners w ON a.user_id = w.user_id
),
-- prepare table for final select and calcualate metrics
exposure_group_table AS (
  SELECT
    Exposure_Group,
    COUNT(DISTINCT user_id) AS reach,
    COUNT(DISTINCT con_user_id) AS converted_users,
    SUM(conversions) AS conversions,
    SUM(revenue) AS revenue
  FROM
    joined
  GROUP BY
    1
),
--calculate total users reached
total_users AS (
  SELECT
    SUM(reach) AS total_users_reached
  FROM
    exposure_group_table
) -- final select with all metrics calculation
SELECT
  exposure_group,
  reach,
  converted_users,
  conversions,
  --revenue,
  (reach / total_users_reached) * 100 AS size_of_the_exposure_group,
  (converted_users / reach) * 100 AS conversion_rate,
  conversions / converted_users AS conversions_per_user
FROM
  exposure_group_table
  INNER JOIN total_users ON 1 = 1""",
                'parameters_schema': {
                    'advertiser_id': {
                        'type': 'integer',
                        'description': 'Your advertiser ID from the exploratory query',
                        'required': True
                    },
                    'campaign_ids': {
                        'type': 'array',
                        'description': 'Array of campaign IDs to analyze for overlap',
                        'required': True
                    },
                    'conversion_activity_id': {
                        'type': 'integer',
                        'description': 'Optional: Specific conversion activity to track',
                        'required': False
                    },
                    'attribution_window_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Attribution window in days for conversions'
                    }
                },
                'default_parameters': {
                    'attribution_window_days': 30
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': """Key customization points:
- Search for 'UPDATE' comments to customize the query
- Default uses last-touch attribution with 30-day lookback
- Customizable attribution windows for impressions and clicks separately
- Supports filtering by specific conversion activities
- Automatically creates exposure groups for campaign combinations
- Post-campaign conversions included within attribution window"""
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
                        'example_name': 'Campaign Overlap Analysis Results',
                        'sample_data': {
                            'rows': [
                                {
                                    'exposure_group': 'Campaign 1',
                                    'reach': 5020234,
                                    'converted_users': 19077,
                                    'conversions': 28000,
                                    'size_of_the_exposure_group': 50.86,
                                    'conversion_rate': 0.38,
                                    'conversions_per_user': 1.47
                                },
                                {
                                    'exposure_group': 'Campaign 2',
                                    'reach': 3870433,
                                    'converted_users': 7741,
                                    'conversions': 11373,
                                    'size_of_the_exposure_group': 39.21,
                                    'conversion_rate': 0.20,
                                    'conversions_per_user': 1.47
                                },
                                {
                                    'exposure_group': 'Campaign 1 & Campaign 2',
                                    'reach': 980586,
                                    'converted_users': 18729,
                                    'conversions': 32474,
                                    'size_of_the_exposure_group': 9.93,
                                    'conversion_rate': 1.91,
                                    'conversions_per_user': 1.73
                                }
                            ]
                        },
                        'interpretation_markdown': """Based on these results:

**Single Campaign Performance:**
- Campaign 1 reaches 50.86% of total audience with 0.38% conversion rate
- Campaign 2 reaches 39.21% of total audience with 0.20% conversion rate
- Both campaigns show similar conversions per user (1.47)

**Multi-Touch Impact:**
- Users exposed to both campaigns: 9.93% of audience
- Conversion rate for overlap: 1.91% (5x higher than Campaign 1, 9.5x higher than Campaign 2)
- Higher conversions per user in overlap (1.73 vs 1.47)

**Strategic Recommendations:**
1. **Maximize Overlap**: The dramatic lift in conversion rate for users exposed to both campaigns suggests strong synergy
2. **Sequential Targeting**: Consider retargeting Campaign 2 audiences with Campaign 1 (or vice versa)
3. **Budget Optimization**: Allocate more budget to drive multi-campaign exposure
4. **Creative Testing**: Test complementary creative messages across campaigns to enhance the synergy effect""",
                        'insights': [
                            'Users exposed to both campaigns are 5-9x more likely to convert',
                            'Multi-campaign exposure drives 18% more conversions per user',
                            'Only 9.93% of users see both campaigns - opportunity to increase overlap',
                            'Campaign 1 has higher standalone conversion rate but both benefit from layering'
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
                'metric_name': 'exposure_group',
                'display_name': 'Exposure Group',
                'definition': 'Determines a campaign or campaign combination that delivered an ad to a user. Shows as "Campaign 1", "Campaign 2", or "Campaign 1 & Campaign 2" for overlapping audiences.',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'reach',
                'display_name': 'Reach',
                'definition': 'Number of distinct users exposed to the ads in each exposure group',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'converted_users',
                'display_name': 'Converted Users',
                'definition': 'Number of distinct users who made a conversion after exposure to the campaign(s)',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversions',
                'display_name': 'Total Conversions',
                'definition': 'Total number of conversions made by users in each exposure group',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'size_of_the_exposure_group',
                'display_name': 'Size of Exposure Group (%)',
                'definition': 'Percentage of users in each exposure group out of total users reached by all campaigns',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate',
                'display_name': 'Conversion Rate (%)',
                'definition': 'The ratio of converted_users to reach, expressed as a percentage ((converted_users/reach)*100)',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversions_per_user',
                'display_name': 'Conversions per User',
                'definition': 'Average number of conversions per converted user (conversions/converted_users)',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'revenue',
                'display_name': 'Revenue',
                'definition': 'Total revenue generated from conversions in each exposure group (optional metric)',
                'metric_type': 'metric',
                'display_order': 8
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created Amazon Ad Server - Campaign Overlap and Conversions guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_adserver_campaign_overlap_guide()
    sys.exit(0 if success else 1)