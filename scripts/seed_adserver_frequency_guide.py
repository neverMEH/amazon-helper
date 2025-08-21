#!/usr/bin/env python3
"""
Seed script for Amazon Ad Server - Ad Exposure Frequency and Conversions Build Guide
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

def create_adserver_frequency_guide():
    """Create the Amazon Ad Server - Ad Exposure Frequency and Conversions guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_adserver_frequency_conversions',
            'name': 'Amazon Ad Server - Ad Exposure Frequency and Conversions',
            'category': 'Campaign Optimization',
            'short_description': 'Measure optimal frequency of ad exposure for Amazon Ad Server campaigns by analyzing conversion patterns across different frequency buckets to optimize frequency caps.',
            'tags': ['Frequency analysis', 'Conversion optimization', 'Ad Server', 'Campaign optimization', 'Frequency capping'],
            'icon': 'ChartBar',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 45,
            'prerequisites': [
                'Amazon Ad Server campaigns must be active',
                'Conversion tracking using Amazon Ad Server conversion activity tags',
                'Note: Without Amazon Ad Server conversion tracking, conversion metrics will be empty but frequency analysis is still possible'
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

This instructional query measures optimal frequency of ad exposure for Amazon Ad Server campaigns by conversion number. It helps answer critical questions:

1. **What is the optimal frequency cap I should apply to my campaigns based on my KPIs?**
2. **What percentage of my impressions/clicks are delivered to users in each frequency bin?**
3. **Would increasing my frequency translate to increased performance?**

By analyzing conversion patterns across different frequency buckets, you can identify the point of diminishing returns and set optimal frequency caps to maximize campaign efficiency.

## 1.2 Requirements

To use this query effectively, you need:

- **Amazon Ad Server campaigns must be active** - The query analyzes Amazon Ad Server traffic data
- **Conversion tracking using Amazon Ad Server conversion activity tags** - Required for conversion attribution
- **Note:** Without Amazon Ad Server conversion tracking, conversion metrics will be empty but frequency analysis is still possible for impression/click distribution

The query supports both impression-based and click-based frequency analysis, allowing you to choose the most relevant metric for your campaign objectives.""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Tables Used

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `adserver_traffic` | All impressions and clicks from Amazon Ad Server | `user_id`, `campaign_id`, `impressions`, `clicks`, `event_dt_utc` |
| `adserver_conversions` | Unattributed conversion activities | `user_id`, `conversion_id`, `conversion_activity_id`, `conversions` |

## 2.2 Data Returned

The query returns comprehensive frequency analysis data:

- **Frequency of ad exposure** (impressions or clicks)
- **Audience size** per frequency bin
- **Number of ad exposures** (impressions or clicks) in each bin
- **Conversions attributed** to ad exposures

### Conversion Calculation Methodology:
- Measures impact of ad-exposures in reporting period on conversions up to 30 days post-period
- Uses last touch attribution with 30-day lookback window (configurable)
- Attribution window controlled via AMC time window settings
- Ensures proper attribution by tracking full user journey

## 2.3 Example User Journey

To understand how frequency attribution works, consider two users with different conversion paths:

### **User1 Journey:**
```
1/2  - Impression (counted)
1/20 - Impression (counted)
1/30 - Impression (counted)
2/20 - Conversion activity ✓
```

### **User2 Journey:**
```
1/2  - Impression (counted)
1/20 - Impression (counted)
1/30 - Impression (counted)
2/5  - Impression (not counted - outside period)
2/20 - Conversion activity ✗
```

**Query Period: January 1 - January 31**

Analysis:
- Both users fall under `frequency_03` bucket (3 impressions in period)
- User1's conversion is attributed (within-period exposures led to conversion)
- User2's conversion is NOT attributed (needed 4th impression outside period for conversion)

**Result Table:**
| campaign_id | frequency_bucket | users_in_bucket | impressions_in_bucket | conversions |
|------------|------------------|-----------------|----------------------|-------------|
| 1111111111 | frequency_03 | 2 | 6 | 1 |

## 2.4 Configuration Options

### Frequency Buckets:
- **Default:** 10 buckets (frequency_01 through frequency_10+)
- Bucket 10+ represents users with 10 or more exposures
- Adjustable based on your campaign's exposure distribution

### Filtering Options:
- Filter by specific campaign IDs
- Filter by conversion activity types
- Customize attribution windows for clicks vs impressions

### Attribution Windows:
- **Default:** 30 days for both impressions and clicks
- **Customizable:** Different windows for impressions vs clicks
- **Example:** 7-day window for impressions, 14-day window for clicks""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': '3. Data Interpretation',
                'content_markdown': """## 3.1 Metrics Defined

| Metric | Definition | Usage |
|--------|------------|-------|
| **frequency_bucket** | Exposure groups (frequency_01 = 1 exposure, frequency_10+ = 10+ exposures) | Categorizes users by exposure count |
| **users_in_bucket** | Number of distinct users in each frequency bucket | Audience size at each frequency level |
| **impressions_in_bucket** | Total impressions delivered to users in bucket | Total exposure volume |
| **conversions** | Number of conversions attributed to bucket | Performance indicator |
| **conversion_rate** | Calculated as (conversions / users_in_bucket) × 100 | Efficiency metric |
| **percentage_users_in_bucket** | Distribution of users across frequency buckets | Reach distribution |

## 3.2 Example Results Analysis

### Sample Campaign Results:

| campaign_id | frequency_bucket | users_in_bucket | impressions_in_bucket | conversions | conversion_rate | pc_of_users |
|------------|------------------|-----------------|----------------------|-------------|-----------------|-------------|
| 1111111111 | frequency_01 | 123,763 | 123,763 | 700 | 0.57% | 40.23% |
| 1111111111 | frequency_02 | 98,345 | 196,690 | 650 | 0.66% | 31.97% |
| 1111111111 | frequency_03 | 45,333 | 135,999 | 500 | 1.10% | 14.74% |
| 1111111111 | **frequency_04** | **20,874** | **83,496** | **450** | **2.16%** | **6.79%** |
| 1111111111 | frequency_05 | 10,992 | 54,960 | 100 | 0.91% | 3.57% |
| 1111111111 | frequency_06 | 4,325 | 25,950 | 25 | 0.58% | 1.41% |
| 1111111111 | frequency_07 | 2,001 | 14,007 | 10 | 0.50% | 0.65% |
| 1111111111 | frequency_08 | 780 | 6,240 | 2 | 0.26% | 0.25% |
| 1111111111 | frequency_09 | 345 | 3,105 | 1 | 0.29% | 0.11% |
| 1111111111 | frequency_10+ | 882 | 12,566 | 1 | 0.11% | 0.29% |

## 3.3 Finding the Optimal Frequency

### Diminishing Returns Analysis:

1. **Initial Growth Phase (Frequency 1-4):**
   - Conversion rate increases from 0.57% to peak of 2.16%
   - Each additional exposure improves performance
   - Frequency 4 shows optimal conversion rate

2. **Declining Performance (Frequency 5+):**
   - Sharp drop from 2.16% to 0.91% at frequency 5
   - Continued decline in subsequent frequencies
   - Clear point of diminishing returns

3. **User Distribution:**
   - 40.23% of users see only 1 ad (largest segment)
   - 93.47% of users see 4 or fewer ads
   - Only 6.53% exceed optimal frequency

### **Key Finding:** 
🎯 **Optimal Frequency Cap = 4**

**Recommendation:** Set frequency cap to 4 in delivery group settings

### Impact Analysis:
- **Current State:** Wasted impressions on users seeing 5+ ads
- **With Cap of 4:** Redirect budget to reach new users or increase frequency for users below cap
- **Expected Outcome:** Higher overall conversion rate and improved campaign efficiency""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': '4. Best Practices',
                'content_markdown': """## 4.1 Implementation Strategy

### Step-by-Step Approach:

1. **Start with Exploratory Queries**
   - Identify relevant campaigns and conversion activities
   - Understand current frequency distribution
   - Check data availability and quality

2. **Wait for Attribution Window**
   - Allow full attribution window to complete before analyzing
   - For 30-day window, wait 30 days after campaign period
   - Ensures all conversions are properly attributed

3. **Analyze Distribution Patterns**
   - Consider that 80% of users may be in frequency bin 1
   - This is normal for broad reach campaigns
   - Focus on conversion rate patterns, not just user counts

4. **Adjust Frequency Buckets**
   - Default 10 buckets work for most campaigns
   - For high-frequency campaigns, extend to 15 or 20 buckets
   - For low-frequency campaigns, reduce to 5-7 buckets

5. **Set Optimal Frequency Caps**
   - Identify peak conversion rate frequency
   - Set cap at or slightly above peak
   - Monitor performance after implementation

6. **Monitor Post-Implementation**
   - Track changes in conversion rates
   - Monitor reach expansion
   - Adjust caps based on performance

7. **Consider Different Attribution Windows**
   - Test different windows for clicks vs impressions
   - Shorter windows for direct response campaigns
   - Longer windows for consideration campaigns

## 4.2 Common Pitfalls to Avoid

### Data Quality Issues:
- **Missing Conversion Tracking:** Ensure conversion tags are properly implemented
- **Incomplete Attribution:** Wait for full attribution window before analysis
- **Data Lag:** Account for AMC's typical 24-48 hour data processing lag

### Analysis Mistakes:
- **Ignoring User Distribution:** Don't just look at conversion rates, consider volume
- **Over-Capping:** Setting cap too low limits brand awareness
- **Under-Capping:** Setting cap too high wastes budget on oversaturated users

### Implementation Errors:
- **Immediate Full Implementation:** Test with subset of campaigns first
- **Ignoring Campaign Types:** Different campaigns need different caps
- **Static Caps:** Regularly review and adjust based on performance

## 4.3 Advanced Optimization Techniques

### Segmented Frequency Capping:
- Different caps for different audience segments
- Higher caps for high-value customers
- Lower caps for broad prospecting

### Time-Based Frequency Management:
- Daily caps for intense campaigns
- Weekly caps for sustained campaigns
- Monthly caps for brand awareness

### Cross-Campaign Coordination:
- Account for frequency across multiple campaigns
- Implement portfolio-level frequency management
- Balance frequency across campaign objectives""",
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
                'description': 'Explore available campaigns and advertisers in Amazon Ad Server to identify what data is available for frequency analysis.',
                'sql_query': """-- Campaign and Advertisers Exploratory Query
-- Use this to understand what campaigns are available in your AMC instance
SELECT
  advertiser,
  advertiser_id,
  campaign,
  campaign_id,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  COUNT(DISTINCT user_id) AS unique_users,
  MIN(event_dt_utc) AS first_impression,
  MAX(event_dt_utc) AS last_impression
FROM
  adserver_traffic
WHERE
  event_dt_utc >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
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
                'interpretation_notes': 'This query helps identify which campaigns have sufficient volume for frequency analysis. Look for campaigns with at least 10,000 unique users for meaningful results.'
            },
            {
                'guide_id': guide_id,
                'title': 'Conversion Activity Exploratory Query',
                'description': 'Explore available conversion activities to understand what conversion tracking is available.',
                'sql_query': """-- Conversion Activity Exploratory Query
-- Use this to identify conversion activities for attribution
SELECT
  advertiser,
  advertiser_id,
  conversion_activity,
  conversion_activity_id,
  SUM(conversions) AS conversions,
  COUNT(DISTINCT user_id) AS converting_users,
  MIN(event_dt_utc) AS first_conversion,
  MAX(event_dt_utc) AS last_conversion
FROM
  adserver_conversions
WHERE
  event_dt_utc >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
GROUP BY
  advertiser,
  advertiser_id,
  conversion_activity,
  conversion_activity_id
ORDER BY
  conversions DESC
LIMIT 50""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for conversion data'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30
                },
                'display_order': 2,
                'query_type': 'exploratory',
                'interpretation_notes': 'Identify which conversion activities are most relevant for your analysis. Higher volume activities provide more reliable frequency optimization insights.'
            },
            {
                'guide_id': guide_id,
                'title': 'Amazon Ad Server Ad Exposure Frequency and Conversions Analysis',
                'description': 'Main analysis query that measures optimal frequency of ad exposure by analyzing conversion patterns across frequency buckets.',
                'sql_query': """-- Instructional Query: Amazon Ad Server Ad Exposure Frequency and Conversions
/*This query returns frequency of ad exposure (impressions or clicks), size of
 the audience per frequency, number of ad exposures (impressions or clicks),  
 number of conversions attributed to ad exposures within the date range for 
 every or selected campaign/s of the advertiser that had traffic in the selected 
 date range. Conversions are calculated based on the conversion activities 
 that occurred up to 30 days after the reporting end date which are attributed 
 to the traffic within the reporting date range */

/* REQUIRED UPDATE your advertiser id(s) */
WITH advertiser_ids (advertiser_id) AS (
  VALUES
    ({{advertiser_id}})
),
/*OPTIONAL UPDATE your campaign id(s). 
 If you update this section, you must uncomment the campaign_id WHERE clause 
 in two sections. Search 'UPDATE campaign_id' */
campaign_ids (campaign_id) AS (
  VALUES
    ({{campaign_id_1}}),
    ({{campaign_id_2}}),
    ({{campaign_id_3}})
),
/* OPTIONAL UPDATE your conversion activity id(s).
 If you update this section, you must uncomment the conversion_activity_ids 
 WHERE clause. Search 'UPDATE conversion_activity_id' */
conversion_activity_ids (conversion_activity_id) AS (
  VALUES
    ({{conversion_activity_id}})
),
/*Prepare traffic data set that include an extra 30 days of traffic post report 
 end date to be used later to filter out conversions that attributed to 
 traffic that is not within the reporting period */
traffic AS (
  -- Read impression or clicks events.
  SELECT
    ad_id,
    ad,
    advertiser_id,
    advertiser,
    campaign_id,
    campaign,
    clicks,
    event_dt_utc AS traffic_dt,
    event_date_utc,
    impressions,
    placement_id,
    placement,
    search_ad_group,
    search_keyword_id,
    user_id,
    adserver_site
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
      EXTEND_TIME_WINDOW('adserver_traffic', 'P0D', 'P{{attribution_window_days}}D')
    )
  WHERE
    advertiser_id IN (
      SELECT
        advertiser_id
      FROM
        advertiser_ids
    )
    AND (
      clicks = {{use_clicks}}
      OR impressions = {{use_impressions}}
    )
    -- UPDATE campaign_id: uncomment below if filtering by campaign
    -- AND campaign_id IN (SELECT campaign_id FROM campaign_ids)
),
/* 
 Read conversion events from the adserver_conversions data source.
 Join conversion events to traffic events based on user_id and advertiser_id.
 Determine a match type based on the traffic event type and time from the conversion 
 event. 
 */
matched AS (
  SELECT
    t.ad_id,
    t.ad,
    t.advertiser_id,
    t.advertiser,
    t.campaign_id,
    t.campaign,
    t.event_date_utc,
    t.placement_id,
    t.placement,
    t.search_ad_group,
    t.search_keyword_id,
    t.adserver_site,
    t.traffic_dt,
    c.conversion_id,
    c.conversion_activity_id,
    c.conversion_activity,
    c.conversion_type,
    c.revenue,
    c.conversions,
    c.user_id,
    -- Determine a match type based on the traffic event type impressions vs clicks
    CASE
      WHEN t.clicks = 1 --If traffic event is a click
      THEN 1
      WHEN t.impressions = 1 --If traffic event is a impression
      THEN 2
    END AS match_type,
    SECONDS_BETWEEN(t.traffic_dt, c.event_dt_utc) AS match_age
    /* conversion events that occurred up to 30 days after the reporting end date 
     will be attributed to the traffic within the reporting date range */
    /* OPTIONAL UPDATE change the attribution window from the following default 30 days 
     to another, and update the same value to 'adserver_traffic' extended time period above */
  FROM
    TABLE(
      EXTEND_TIME_WINDOW('adserver_conversions', 'P0D', 'P{{attribution_window_days}}D')
    ) c
    INNER JOIN traffic t ON c.user_id = t.user_id
    AND c.advertiser_id = t.advertiser_id
    /* OPTIONAL UPDATE conversion_activity_id: 
     Uncomment the line below if you used conversion_activity filter 
     in the beginning of the query */
    -- WHERE conversion_activity_id IN (SELECT conversion_activity_id FROM conversion_activity_ids)
),
/* For each conversion event, rank all the matching traffic events based on 
 match type and then match age. */
ranked AS (
  SELECT
    conversion_activity_id,
    conversion_activity,
    user_id,
    ad_id,
    ad,
    search_ad_group,
    search_keyword_id,
    placement_id,
    placement,
    advertiser_id,
    advertiser,
    campaign_id,
    campaign,
    adserver_site,
    event_date_utc,
    traffic_dt,
    conversion_type,
    revenue,
    match_type,
    -- Rank the match based on match type and then age.
    ROW_NUMBER() OVER(
      PARTITION BY conversion_id
      ORDER BY
        match_type,
        match_age
    ) AS match_rank,
    conversions
  FROM
    matched
  WHERE
    /* Attribution window: define the attribution window for impressions and clicks.
     This will instruct the workflow to select traffic events eligible for attribution 
     based on their age, or the number of days between the user's conversion and 
     traffic event. For example, if you select an attribution window of 5 days for impressions 
     and 10 days for clicks, impressions older than 5 days are not eligible
     for attribution, but clicks up to 10 days old are considered attributable. */
    match_age BETWEEN 0 AND CASE
      WHEN match_type = 1 --clicks
      /* OPTIONAL UPDATE: The first number, X, of the expression 'X * 24 * 60 * 60' can be 
       configured with a number of days for the attribution window for clicks. 
       In this example, the attribution window, X, is 30 days for clicks. */
      THEN {{click_attribution_days}} * 24 * 60 * 60
      WHEN match_type = 2 --impressions
      /* OPTIONAL UPDATE: The first number, X, of the expression 'X * 24 * 60 * 60' can be 
       configured with a number of days for the attribution window for impressions. 
       In this example, the attribution window, X, is 30 days for impressions. */
      THEN {{impression_attribution_days}} * 24 * 60 * 60
    END
    /* UPDATE: To use click-based attribution only, uncomment the line below.
     To consider both impressions and clicks, keep the line below commented out. */
    -- AND match_type = 1
),
-- Filter to only the best matching traffic event for each conversion event.
-- Calculate conversion metric sums for selected breakdowns.
-- Keep only winner events that happened inside the report date range
winners AS (
  SELECT
    campaign_id,
    user_id,
    SUM(conversions) AS conversions
  FROM
    ranked
  WHERE
    /*UPDATE campaign_id: uncomment the line below if you used campaign filter in 
     the beginning of the query */
    -- campaign_id IN (SELECT campaign_id FROM campaign_ids) AND
    /* In order to measure the impact of the frequency buckets within the report period 
     on conversions that also happened post reporting period, this condition will filter out
     conversions that are attributed to traffic that happened after the reporting period. 
     If we had only brought in traffic events from the traffic CTE within the reporting 
     period, we could have attributed the wrong traffic event (one that has a better match
     outside of the reporting window). This methodology considers the
     full user journey */
    traffic_dt > BUILT_IN_PARAMETER('TIME_WINDOW_START')
    AND traffic_dt < BUILT_IN_PARAMETER('TIME_WINDOW_END')
    AND -- Filter to only the best matching traffic event.
    match_rank = 1
  GROUP BY
    campaign_id, user_id
),
joined AS (
  SELECT
    campaign_id,
    user_id,
    IF(SUM(impressions) > 0, SUM(impressions), SUM(clicks)) AS impressions,
    SUM(clicks) AS clicks,
    0 AS conversions
  FROM
    adserver_traffic
  WHERE
    advertiser_id IN (
      SELECT
        advertiser_id
      FROM
        advertiser_ids
    )
    /*UPDATE campaign_id: uncomment the line below if you used campaign filter in the 
     beginning of the query */
    -- AND campaign_id IN (SELECT campaign_id FROM campaign_ids)
  GROUP BY
    campaign_id, user_id
  UNION ALL
  SELECT
    campaign_id,
    user_id,
    0 AS impressions,
    0 AS clicks,
    SUM(conversions) AS conversions
  FROM
    winners
  GROUP BY
    campaign_id, user_id
),
events_by_user AS (
  SELECT
    user_id,
    campaign_id,
    IF(SUM(impressions) > 0, SUM(impressions), SUM(clicks)) AS impressions,
    LEAST(
      IF(SUM(impressions) > 0, SUM(impressions), SUM(clicks)),
      {{max_frequency_bucket}}
    ) AS frequency,
    /*OPTIONAL UPDATE frequency bucket if necessary*/
    SUM(conversions) AS conversions
  FROM
    joined
  GROUP BY
    user_id, campaign_id
),
frequency_by_user AS (
  SELECT
    campaign_id,
    impressions,
    CONCAT(
      FORMAT('frequency_%02d', frequency),
      /*OPTIONAL UPDATE frequency bucket if necessary*/
      IF(frequency = {{max_frequency_bucket}}, '+', '')
    ) AS frequency_bucket,
    conversions,
    user_id
  FROM
    events_by_user
  WHERE
    user_id IS NOT NULL
),
frequency_by_bucket AS (
  SELECT
    campaign_id,
    frequency_bucket,
    COUNT(user_id) AS users_in_bucket,
    SUM(impressions) AS impressions_in_bucket,
    SUM(conversions) AS conversions,
    ROUND((SUM(conversions) / COUNT(user_id)) * 100, 2) AS conversion_rate
  FROM
    frequency_by_user
  GROUP BY
    campaign_id, frequency_bucket
),
total_users AS (
  SELECT
    campaign_id,
    SUM(users_in_bucket) AS total_users_sum
  FROM
    frequency_by_bucket
  GROUP BY
    campaign_id
)
SELECT
  frequency_by_bucket.campaign_id,
  frequency_bucket,
  users_in_bucket,
  impressions_in_bucket,
  conversions,
  conversion_rate,
  ROUND((users_in_bucket / total_users_sum) * 100, 2) AS percentage_users_in_bucket
FROM
  frequency_by_bucket
  INNER JOIN total_users ON total_users.campaign_id = frequency_by_bucket.campaign_id
ORDER BY
  frequency_by_bucket.campaign_id,
  frequency_bucket""",
                'parameters_schema': {
                    'advertiser_id': {
                        'type': 'integer',
                        'required': True,
                        'description': 'Your advertiser ID (required)'
                    },
                    'campaign_id_1': {
                        'type': 'integer',
                        'required': False,
                        'description': 'Optional: First campaign ID to filter'
                    },
                    'campaign_id_2': {
                        'type': 'integer',
                        'required': False,
                        'description': 'Optional: Second campaign ID to filter'
                    },
                    'campaign_id_3': {
                        'type': 'integer',
                        'required': False,
                        'description': 'Optional: Third campaign ID to filter'
                    },
                    'conversion_activity_id': {
                        'type': 'integer',
                        'required': False,
                        'description': 'Optional: Conversion activity ID to track'
                    },
                    'attribution_window_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Attribution window in days (default: 30)'
                    },
                    'click_attribution_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Attribution window for clicks in days'
                    },
                    'impression_attribution_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Attribution window for impressions in days'
                    },
                    'use_clicks': {
                        'type': 'integer',
                        'default': 1,
                        'description': 'Include clicks in analysis (1=yes, 0=no)'
                    },
                    'use_impressions': {
                        'type': 'integer',
                        'default': 1,
                        'description': 'Include impressions in analysis (1=yes, 0=no)'
                    },
                    'max_frequency_bucket': {
                        'type': 'integer',
                        'default': 10,
                        'description': 'Maximum frequency bucket (10 means 10+)'
                    }
                },
                'default_parameters': {
                    'advertiser_id': 111111,
                    'campaign_id_1': 22222222,
                    'campaign_id_2': 3333333,
                    'campaign_id_3': 4444444,
                    'conversion_activity_id': 5555555,
                    'attribution_window_days': 30,
                    'click_attribution_days': 30,
                    'impression_attribution_days': 30,
                    'use_clicks': 1,
                    'use_impressions': 1,
                    'max_frequency_bucket': 10
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Look for the frequency bucket with the highest conversion rate to identify optimal frequency cap. Consider both conversion rate and user volume when making decisions.'
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
                        'example_name': 'Sample Frequency Analysis Results',
                        'sample_data': {
                            'rows': [
                                {'campaign_id': 1111111111, 'frequency_bucket': 'frequency_01', 'users_in_bucket': 123763, 'impressions_in_bucket': 123763, 'conversions': 700, 'conversion_rate': 0.57, 'percentage_users_in_bucket': 40.23},
                                {'campaign_id': 1111111111, 'frequency_bucket': 'frequency_02', 'users_in_bucket': 98345, 'impressions_in_bucket': 196690, 'conversions': 650, 'conversion_rate': 0.66, 'percentage_users_in_bucket': 31.97},
                                {'campaign_id': 1111111111, 'frequency_bucket': 'frequency_03', 'users_in_bucket': 45333, 'impressions_in_bucket': 135999, 'conversions': 500, 'conversion_rate': 1.10, 'percentage_users_in_bucket': 14.74},
                                {'campaign_id': 1111111111, 'frequency_bucket': 'frequency_04', 'users_in_bucket': 20874, 'impressions_in_bucket': 83496, 'conversions': 450, 'conversion_rate': 2.16, 'percentage_users_in_bucket': 6.79},
                                {'campaign_id': 1111111111, 'frequency_bucket': 'frequency_05', 'users_in_bucket': 10992, 'impressions_in_bucket': 54960, 'conversions': 100, 'conversion_rate': 0.91, 'percentage_users_in_bucket': 3.57},
                                {'campaign_id': 1111111111, 'frequency_bucket': 'frequency_06', 'users_in_bucket': 4325, 'impressions_in_bucket': 25950, 'conversions': 25, 'conversion_rate': 0.58, 'percentage_users_in_bucket': 1.41},
                                {'campaign_id': 1111111111, 'frequency_bucket': 'frequency_07', 'users_in_bucket': 2001, 'impressions_in_bucket': 14007, 'conversions': 10, 'conversion_rate': 0.50, 'percentage_users_in_bucket': 0.65},
                                {'campaign_id': 1111111111, 'frequency_bucket': 'frequency_08', 'users_in_bucket': 780, 'impressions_in_bucket': 6240, 'conversions': 2, 'conversion_rate': 0.26, 'percentage_users_in_bucket': 0.25},
                                {'campaign_id': 1111111111, 'frequency_bucket': 'frequency_09', 'users_in_bucket': 345, 'impressions_in_bucket': 3105, 'conversions': 1, 'conversion_rate': 0.29, 'percentage_users_in_bucket': 0.11},
                                {'campaign_id': 1111111111, 'frequency_bucket': 'frequency_10+', 'users_in_bucket': 882, 'impressions_in_bucket': 12566, 'conversions': 1, 'conversion_rate': 0.11, 'percentage_users_in_bucket': 0.29}
                            ]
                        },
                        'interpretation_markdown': """Based on these frequency analysis results:

**Optimal Frequency Identified:** Frequency 4 shows the highest conversion rate at 2.16%

**Performance Pattern:**
- Conversion rate increases from frequency 1 (0.57%) to frequency 4 (2.16%)
- Sharp decline after frequency 4, dropping to 0.91% at frequency 5
- Continued deterioration for frequencies 6+ 

**User Distribution:**
- 40.23% of users are in frequency bucket 1 (single exposure)
- 93.47% of users see 4 or fewer ads
- Only 6.53% of users exceed the optimal frequency

**Key Insights:**
1. Clear point of diminishing returns after 4 exposures
2. Significant wasted impressions on users with 5+ exposures
3. Opportunity to redirect budget from over-exposed users to new audiences

**Recommendation:** 
Set frequency cap to 4 in your Amazon Ad Server delivery group settings. This will:
- Maximize conversion efficiency
- Reduce wasted impressions
- Allow budget reallocation to reach new users
- Improve overall campaign ROI

**Expected Impact:**
- Improved overall conversion rate
- Increased unique reach
- Better cost efficiency
- Reduced ad fatigue""",
                        'insights': [
                            'Frequency 4 delivers 3.8x higher conversion rate than frequency 1',
                            'Diminishing returns begin after 4 exposures per user',
                            '93.47% of users already receive optimal or below-optimal frequency',
                            'Implementing frequency cap of 4 could improve efficiency by 15-20%',
                            'Consider testing frequency caps between 3-5 for fine-tuning'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example results")
                    
                    # Add a second example for campaigns with different patterns
                    example_data_2 = {
                        'guide_query_id': query_id,
                        'example_name': 'Alternative Pattern - High Frequency Campaign',
                        'sample_data': {
                            'rows': [
                                {'campaign_id': 2222222222, 'frequency_bucket': 'frequency_01', 'users_in_bucket': 45000, 'impressions_in_bucket': 45000, 'conversions': 150, 'conversion_rate': 0.33, 'percentage_users_in_bucket': 15.00},
                                {'campaign_id': 2222222222, 'frequency_bucket': 'frequency_02', 'users_in_bucket': 60000, 'impressions_in_bucket': 120000, 'conversions': 300, 'conversion_rate': 0.50, 'percentage_users_in_bucket': 20.00},
                                {'campaign_id': 2222222222, 'frequency_bucket': 'frequency_03', 'users_in_bucket': 55000, 'impressions_in_bucket': 165000, 'conversions': 385, 'conversion_rate': 0.70, 'percentage_users_in_bucket': 18.33},
                                {'campaign_id': 2222222222, 'frequency_bucket': 'frequency_04', 'users_in_bucket': 45000, 'impressions_in_bucket': 180000, 'conversions': 405, 'conversion_rate': 0.90, 'percentage_users_in_bucket': 15.00},
                                {'campaign_id': 2222222222, 'frequency_bucket': 'frequency_05', 'users_in_bucket': 35000, 'impressions_in_bucket': 175000, 'conversions': 385, 'conversion_rate': 1.10, 'percentage_users_in_bucket': 11.67},
                                {'campaign_id': 2222222222, 'frequency_bucket': 'frequency_06', 'users_in_bucket': 25000, 'impressions_in_bucket': 150000, 'conversions': 325, 'conversion_rate': 1.30, 'percentage_users_in_bucket': 8.33},
                                {'campaign_id': 2222222222, 'frequency_bucket': 'frequency_07', 'users_in_bucket': 15000, 'impressions_in_bucket': 105000, 'conversions': 225, 'conversion_rate': 1.50, 'percentage_users_in_bucket': 5.00},
                                {'campaign_id': 2222222222, 'frequency_bucket': 'frequency_08', 'users_in_bucket': 10000, 'impressions_in_bucket': 80000, 'conversions': 160, 'conversion_rate': 1.60, 'percentage_users_in_bucket': 3.33},
                                {'campaign_id': 2222222222, 'frequency_bucket': 'frequency_09', 'users_in_bucket': 6000, 'impressions_in_bucket': 54000, 'conversions': 102, 'conversion_rate': 1.70, 'percentage_users_in_bucket': 2.00},
                                {'campaign_id': 2222222222, 'frequency_bucket': 'frequency_10+', 'users_in_bucket': 4000, 'impressions_in_bucket': 60000, 'conversions': 72, 'conversion_rate': 1.80, 'percentage_users_in_bucket': 1.33}
                            ]
                        },
                        'interpretation_markdown': """This campaign shows a different pattern - continuous improvement with frequency:

**Pattern Analysis:**
- Conversion rate steadily increases from 0.33% (frequency 1) to 1.80% (frequency 10+)
- No clear point of diminishing returns
- Higher frequencies continue to show value

**User Distribution:**
- More evenly distributed across frequency buckets
- 35% of users receive 5+ exposures
- Higher engagement audience

**Recommendation for This Pattern:**
- Consider a higher frequency cap (8-10) or no cap
- This pattern suggests a considered purchase or B2B product
- Users need multiple touchpoints before converting
- Test incremental frequency increases to find optimal point""",
                        'insights': [
                            'Linear improvement pattern suggests complex purchase decision',
                            'Higher frequency tolerance indicates engaged audience',
                            'Consider product category and purchase cycle when setting caps',
                            'May benefit from sequential messaging strategy'
                        ],
                        'display_order': 2
                    }
                    
                    example_response_2 = client.table('build_guide_examples').insert(example_data_2).execute()
                    if example_response_2.data:
                        logger.info("Created alternative example results")
                        
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'campaign_id',
                'display_name': 'Campaign ID',
                'definition': 'Unique identifier for the Amazon Ad Server campaign',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'frequency_bucket',
                'display_name': 'Frequency Bucket',
                'definition': 'Exposure frequency groups (frequency_01 = 1 exposure, frequency_02 = 2 exposures, etc., frequency_10+ = 10 or more exposures)',
                'metric_type': 'dimension',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'users_in_bucket',
                'display_name': 'Users in Bucket',
                'definition': 'Number of distinct users who fall into each frequency bucket based on their ad exposure count',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'impressions_in_bucket',
                'display_name': 'Impressions in Bucket',
                'definition': 'Total number of impressions (or clicks if impression data not available) delivered to users in each frequency bucket',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversions',
                'display_name': 'Conversions',
                'definition': 'Number of conversions attributed to users in each frequency bucket using last-touch attribution within the attribution window',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate',
                'display_name': 'Conversion Rate (%)',
                'definition': 'Percentage of users in each frequency bucket who converted, calculated as (conversions / users_in_bucket) × 100',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'percentage_users_in_bucket',
                'display_name': 'Percentage of Users (%)',
                'definition': 'Distribution of total audience across frequency buckets, showing what percentage of all users fall into each frequency group',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'match_type',
                'display_name': 'Match Type',
                'definition': 'Attribution priority indicator: 1 = click-based attribution (higher priority), 2 = impression-based attribution (lower priority)',
                'metric_type': 'dimension',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'match_age',
                'display_name': 'Match Age',
                'definition': 'Time between ad exposure and conversion in seconds, used to determine attribution within the lookback window',
                'metric_type': 'metric',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'attribution_window',
                'display_name': 'Attribution Window',
                'definition': 'Time period after ad exposure during which conversions can be attributed to that exposure (default: 30 days, configurable)',
                'metric_type': 'dimension',
                'display_order': 10
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created Amazon Ad Server Frequency Analysis guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_adserver_frequency_guide()
    sys.exit(0 if success else 1)