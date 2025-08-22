#!/usr/bin/env python3
"""
Seed script for Amazon Ad Server - Site Overlap and Conversions Build Guide
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

def create_adserver_site_overlap_guide():
    """Create the Amazon Ad Server - Site Overlap and Conversions guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_adserver_site_overlap_conversions',
            'name': 'Amazon Ad Server - Site Overlap and Conversions',
            'category': 'Amazon Ad Server',
            'short_description': 'Measure audience overlap between multiple sites in Amazon Ad Server campaigns and evaluate the impact on conversion KPIs',
            'tags': ['ad-server', 'site-overlap', 'reach-analysis', 'audience-overlap', 'conversion-impact'],
            'icon': 'Globe',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 30,
            'prerequisites': [
                'AMC Instance with Ad Server data',
                'Multiple sites in campaign',
                'Ad Server conversion tracking (optional)'
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
                'title': 'Introduction',
                'content_markdown': """## Purpose

This instructional query measures audience overlap (reach) between multiple sites used in Amazon Ad Server campaign media plans and evaluates the impact on conversion KPIs. It helps you understand:

- Size of overlapping and incremental reach across sites
- Conversion likelihood when users are exposed to ads on multiple sites vs. single sites
- Efficiency of media mix and site selection strategy

### What is a Site in Amazon Ad Server?

An **Amazon Ad Server Site** is an entity in a campaign media plan representing a media buying channel such as:
- DSPs (Demand Side Platforms)
- Direct media publishers
- Search platforms

Sites indicate the channel assigned to serving or tracking placements in your campaign setup.

### Key Insights This Query Provides

1. **Audience Overlap Rate**: Percentage of users reached by multiple sites
2. **Incremental Reach**: Unique users reached exclusively by each site
3. **Conversion Impact**: How exposure to multiple sites affects conversion rates
4. **Engagement Depth**: Conversions per user across different exposure groups

## Requirements

### Required:
- AMC instance with at least one Amazon Ad Server campaign
- Campaign must have ads delivered to multiple sites

### Optional but Recommended:
- Amazon Ad Server conversion tracking enabled
- Multiple campaigns for comparative analysis

> **Note**: Without Ad Server conversion tracking, the query will still run but conversion metrics will be empty.""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_sources',
                'title': 'Data Sources Overview',
                'content_markdown': """## Tables Used

### 1. adserver_traffic
Contains all impressions and clicks measured by Amazon Ad Server.

**Key fields used:**
- `adserver_site` or `search_vendor`: Site/channel identifier
- `user_id`: Unique user identifier for overlap analysis
- `campaign_id`, `advertiser_id`: Campaign identifiers
- `impressions`, `clicks`: Traffic events
- `event_dt_utc`: Event timestamp for attribution

### 2. adserver_conversions
Contains unattributed Amazon Ad Server conversion activities.

**Key fields used:**
- `conversion_id`: Unique conversion identifier
- `conversion_activity_id`: Type of conversion activity
- `conversions`: Number of conversions
- `revenue`: Revenue from conversions
- `user_id`: User who converted
- `event_dt_utc`: Conversion timestamp

## How the Query Works

### Step 1: Identify User Exposure
The query identifies which sites each user was exposed to within your campaign(s).

### Step 2: Create Exposure Groups
Users are categorized into mutually exclusive groups:
- Single site exposure (e.g., "[DSP A]" only)
- Multiple site exposure (e.g., "[DSP A, DSP B]")

### Step 3: Calculate Metrics
For each exposure group, the query calculates:
- Reach (unique users)
- Conversion metrics
- Overlap percentages

### Attribution Model

**Default Settings:**
- **Model**: Last touch attribution
- **Lookback Window**: 30 days
- **Priority**: Clicks over impressions

The query considers conversions that happen after the campaign ends, attributing them to ad exposures within the selected date range.""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'implementation',
                'title': 'Implementation Steps',
                'content_markdown': """## Step-by-Step Implementation

### Step 1: Run Exploratory Queries

#### 1.1 Identify Campaigns with Multiple Sites
Run the first exploratory query to find campaigns using multiple sites. Look for campaigns where the same `campaign_id` appears with different `adserver_site` values.

#### 1.2 Identify Conversion Activities
Run the second exploratory query to find available conversion activities for your advertiser. Note the `conversion_activity_id` values you want to track.

### Step 2: Configure the Main Query

#### Required Updates:
1. **Advertiser ID**: Update the `advertiser_ids` CTE with your advertiser ID(s)
```sql
WITH advertiser_ids (advertiser_id) AS (
  VALUES (your_advertiser_id)
)
```

#### Optional Updates:
2. **Campaign Filter**: To analyze specific campaigns, update `campaign_ids` and uncomment the WHERE clauses
3. **Conversion Activities**: To focus on specific conversions, update `conversion_activity_ids`
4. **Attribution Window**: Modify the lookback window (default is 30 days)

### Step 3: Customize Attribution Settings

#### Change Lookback Window:
Find and update all instances of `30` in these expressions:
```sql
-- For 14-day window, change 30 to 14:
THEN 30 * 24 * 60 * 60  -- Change to: THEN 14 * 24 * 60 * 60
```

Also update the EXTEND_TIME_WINDOW parameters:
```sql
EXTEND_TIME_WINDOW('adserver_traffic', 'P0D', 'P30D')  -- Change P30D to P14D
```

#### Click-Only Attribution:
To use click-based attribution only (ignore impressions):
```sql
-- Uncomment this line in the ranked CTE:
-- AND match_type = 2
```

### Step 4: Run and Validate

1. Execute the query with your configured parameters
2. Verify the exposure groups make sense for your campaign structure
3. Check that total reach equals sum of all exposure groups
4. Validate conversion metrics against other reports (accounting for attribution differences)""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'metrics_glossary',
                'title': 'Metrics Definitions',
                'content_markdown': """## Core Metrics Explained

### Reach and Exposure Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **exposure_group** | Site or site combination that delivered ads | Array of sites per user |
| **reach** | Unique users in each exposure group | COUNT(DISTINCT user_id) |
| **size_of_the_exposure_group** | Percentage of total audience | (reach / total_users) × 100 |

### Conversion Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **converted_users** | Unique users who converted | COUNT(DISTINCT converting_user_id) |
| **conversions** | Total conversion events | SUM(conversions) |
| **conversion_rate** | Percentage of users who converted | (converted_users / reach) × 100 |
| **conversions_per_user** | Average conversions per converting user | conversions / converted_users |

## Understanding Exposure Groups

### Single Site Exposure
Example: `[DSP A]`
- Users reached ONLY by DSP A
- No exposure to other sites in the campaign
- Represents incremental reach of DSP A

### Multi-Site Exposure
Example: `[DSP A, DSP B]`
- Users reached by BOTH DSP A and DSP B
- Represents overlapping audience
- Often shows higher engagement metrics

### Interpreting Overlap Rates

| Overlap Rate | Interpretation | Action |
|--------------|----------------|---------|
| < 5% | Very low overlap, sites reaching different audiences | Good for reach maximization |
| 5-15% | Moderate overlap, some shared audience | Balanced approach |
| > 15% | High overlap, significant audience duplication | Consider consolidating sites |

## Key Performance Indicators

### Reach Efficiency
- **High incremental reach**: Sites are complementary
- **Low incremental reach**: Consider removing redundant sites

### Conversion Performance
- **Higher conversion rate in overlap**: Frequency drives conversions
- **Similar rates across groups**: Single exposure may be sufficient

### Engagement Depth
- **Higher conversions per user in overlap**: Multi-touch increases engagement
- **Similar across groups**: Frequency may not impact engagement""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'query_templates',
                'title': 'Query Templates',
                'content_markdown': """## Exploratory Queries

### 1. Find Campaigns with Multiple Sites
```sql
-- Campaign and Advertisers Exploratory Query
SELECT
  advertiser,
  advertiser_id,
  campaign,
  campaign_id,
  adserver_site,
  SUM(impressions) AS imps,
  SUM(clicks) AS total_clicks
FROM
  adserver_traffic
GROUP BY
  1, 2, 3, 4, 5
ORDER BY 
  campaign_id, 
  adserver_site
```

### 2. Identify Conversion Activities
```sql
-- Conversion Activity Exploratory Query
SELECT
  advertiser,
  advertiser_id,
  conversion_activity,
  conversion_activity_id,
  SUM(conversions) AS total_conversions
FROM
  adserver_conversions
GROUP BY
  1, 2, 3, 4
ORDER BY 
  total_conversions DESC
```

## Main Query Template

```sql
-- Instructional Query: Amazon Ad Server - Site Overlap and Conversions
/* This query measures audience overlap between sites and conversion impact */

/* REQUIRED UPDATE: Set your advertiser ID(s) */
WITH advertiser_ids (advertiser_id) AS (
  VALUES
    (11111111)  -- UPDATE with your advertiser_id
),

/* OPTIONAL: Filter to specific campaigns */
campaign_ids (campaign_id) AS (
  VALUES
    (22222222),
    (33333333)
),

/* OPTIONAL: Filter to specific conversion activities */
conversion_activity_ids (conversion_activity_id) AS (
  VALUES
    (55555555)
),

-- Gather impressions and clicks
traffic_only AS (
  SELECT
    COALESCE(adserver_site, search_vendor) AS site,
    user_id,
    campaign_id,
    campaign,
    advertiser_id
  FROM
    adserver_traffic
  WHERE
    advertiser_id IN (SELECT advertiser_id FROM advertiser_ids)
    -- Uncomment if using campaign filter:
    -- AND campaign_id IN (SELECT campaign_id FROM campaign_ids)
    AND (impressions = 1 OR clicks = 1)
),

-- Create exposure groups by user and campaign
assembled AS (
  SELECT
    campaign_id,
    campaign,
    user_id,
    ARRAY_SORT(COLLECT(DISTINCT site)) AS site_channel
  FROM
    traffic_only
  GROUP BY
    1, 2, 3
),

-- Prepare traffic data with extended window for attribution
traffic AS (
  SELECT
    advertiser_id,
    campaign_id,
    campaign,
    clicks,
    event_dt_utc AS traffic_dt,
    event_date_utc,
    impressions,
    user_id
  FROM
    TABLE(
      EXTEND_TIME_WINDOW('adserver_traffic', 'P0D', 'P30D')
    )
  WHERE
    advertiser_id IN (SELECT advertiser_id FROM advertiser_ids)
    AND (clicks = 1 OR impressions = 1)
),

-- Match conversions to traffic events
matched AS (
  SELECT
    t.advertiser_id,
    t.campaign_id,
    t.event_date_utc,
    t.traffic_dt,
    c.conversion_id,
    c.conversion_activity_id,
    c.revenue,
    c.conversions,
    c.user_id,
    CASE
      WHEN t.clicks = 1 THEN 1
      WHEN t.impressions = 1 THEN 2
    END AS match_type,
    SECONDS_BETWEEN(t.traffic_dt, c.event_dt_utc) AS match_age
  FROM
    TABLE(
      EXTEND_TIME_WINDOW('adserver_conversions', 'P0D', 'P30D')
    ) c
    INNER JOIN traffic t 
      ON c.user_id = t.user_id
      AND c.advertiser_id = t.advertiser_id
    -- Uncomment if using conversion activity filter:
    -- WHERE c.conversion_activity_id IN (SELECT conversion_activity_id FROM conversion_activity_ids)
),

-- Rank matches for attribution
ranked AS (
  SELECT
    user_id,
    advertiser_id,
    campaign_id,
    event_date_utc,
    traffic_dt,
    revenue,
    conversions,
    match_type,
    ROW_NUMBER() OVER(
      PARTITION BY conversion_id
      ORDER BY match_type, match_age
    ) AS match_rank,
    conversion_id
  FROM
    matched
  WHERE
    match_age BETWEEN 0 AND CASE
      WHEN match_type = 1 THEN 30 * 24 * 60 * 60  -- Clicks: 30 days
      WHEN match_type = 2 THEN 30 * 24 * 60 * 60  -- Impressions: 30 days
    END
),

-- Select winning attribution
winners AS (
  SELECT
    campaign_id,
    user_id,
    traffic_dt,
    conversions,
    revenue
  FROM
    ranked
  WHERE
    match_rank = 1
    AND traffic_dt > BUILT_IN_PARAMETER('TIME_WINDOW_START')
    AND traffic_dt < BUILT_IN_PARAMETER('TIME_WINDOW_END')
),

-- Join exposure groups with conversions
joined AS (
  SELECT
    a.campaign_id,
    a.campaign,
    a.site_channel,
    a.user_id,
    w.conversions,
    w.revenue,
    w.user_id AS con_user_id
  FROM
    assembled a
    LEFT JOIN winners w 
      ON a.campaign_id = w.campaign_id
      AND a.user_id = w.user_id
),

-- Calculate metrics by exposure group
exposure_group_table AS (
  SELECT
    campaign_id,
    campaign,
    site_channel AS exposure_group,
    COUNT(DISTINCT user_id) AS reach,
    COUNT(DISTINCT con_user_id) AS converted_users,
    SUM(conversions) AS conversions,
    (COUNT(DISTINCT con_user_id) / COUNT(DISTINCT user_id)) * 100 AS conversion_rate,
    (SUM(conversions) / NULLIF(COUNT(DISTINCT con_user_id), 0)) AS conversions_per_user
  FROM
    joined
  GROUP BY
    1, 2, 3
),

-- Calculate total reach
total_users AS (
  SELECT
    campaign_id,
    SUM(reach) AS total_users_reached
  FROM
    exposure_group_table
  GROUP BY
    1
)

-- Final output with all metrics
SELECT
  e.campaign_id,
  e.campaign,
  e.exposure_group,
  e.reach,
  e.converted_users,
  e.conversions,
  e.conversion_rate,
  e.conversions_per_user,
  (e.reach / t.total_users_reached) * 100 AS size_of_the_exposure_group
FROM
  exposure_group_table e
  INNER JOIN total_users t 
    ON t.campaign_id = e.campaign_id
ORDER BY
  e.campaign_id,
  e.reach DESC
```""",
                'display_order': 5,
                'is_collapsible': True,
                'default_expanded': False
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': 'Interpreting Results',
                'content_markdown': """## Understanding Your Results

### Sample Output Analysis

Here's an example result set with interpretation:

| campaign_id | exposure_group | reach | converted_users | conversions | conversion_rate | conversions_per_user | size_of_exposure_group |
|-------------|---------------|--------|-----------------|-------------|-----------------|---------------------|------------------------|
| 11111111 | [DSP A] | 2,345,034 | 13,000 | 17,890 | 0.55% | 1.38 | 55.95% |
| 11111111 | [DSP B] | 1,789,552 | 7,563 | 9,762 | 0.42% | 1.29 | 42.70% |
| 11111111 | [DSP A, DSP B] | 56,843 | 322 | 998 | 0.57% | 3.10 | 1.36% |

### Key Insights from This Example

#### 1. Audience Overlap Analysis
- **98.64% unique reach**: DSP A and DSP B reach mostly different audiences
- **1.36% overlap**: Very small shared audience between sites
- **Interpretation**: Sites are complementary, good for maximizing reach

#### 2. Incremental Reach
- **DSP A exclusive**: 55.95% of total audience
- **DSP B exclusive**: 42.70% of total audience
- **Both provide significant incremental reach**

#### 3. Conversion Performance
- **DSP A only**: 0.55% conversion rate
- **DSP B only**: 0.42% conversion rate
- **Both DSPs**: 0.57% conversion rate (slightly higher)
- **Insight**: Multi-site exposure has minimal impact on conversion rate

#### 4. Engagement Depth
- **Single site exposure**: ~1.3 conversions per user
- **Multi-site exposure**: 3.1 conversions per user
- **Key finding**: Users exposed to both sites are 2.4x more engaged

## Strategic Recommendations Based on Results

### Scenario 1: Low Overlap (<5%)
**Finding**: Sites reach different audiences
**Actions**:
- Continue using both sites for maximum reach
- Consider increasing budgets proportionally
- Test audience targeting refinements

### Scenario 2: High Overlap (>20%)
**Finding**: Significant audience duplication
**Actions**:
- Evaluate site performance individually
- Consider consolidating to best-performing site
- Refine targeting to reduce overlap

### Scenario 3: High Conversion Impact from Overlap
**Finding**: Multi-site exposure drives conversions
**Actions**:
- Intentionally cultivate overlap through targeting
- Implement frequency capping strategies
- Develop sequential messaging strategies

## Optimization Strategies

### For Reach Maximization
Focus on sites with high incremental reach:
- Prioritize sites with low overlap rates
- Diversify media mix across different channels
- Monitor overlap trends over time

### For Conversion Optimization
If overlapping audiences convert better:
- Increase frequency through multiple sites
- Coordinate messaging across sites
- Test optimal exposure combinations

### For Efficiency
Balance reach and conversion goals:
- Calculate cost per incremental user
- Compare conversion rates to costs
- Optimize site mix based on ROI""",
                'display_order': 6,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'troubleshooting',
                'title': 'Common Issues and Solutions',
                'content_markdown': """## Troubleshooting Guide

### Issue: No Results or Empty Output

**Possible Causes:**
- No campaigns with multiple sites
- Incorrect advertiser or campaign IDs
- No traffic in the selected date range

**Solutions:**
1. Run exploratory query to verify multiple sites exist
2. Confirm advertiser_id is correct
3. Check date range has traffic data
4. Verify sites are properly tagged in Ad Server

### Issue: Missing Conversion Data

**Possible Causes:**
- Ad Server conversion tracking not implemented
- Conversion activity IDs incorrect
- Conversions outside attribution window

**Solutions:**
1. Verify Ad Server conversion tags are firing
2. Run conversion exploratory query to find valid activity IDs
3. Extend attribution window if needed (default is 30 days)
4. Check that conversions are properly attributed to the advertiser

### Issue: Unexpected Overlap Percentages

**Possible Causes:**
- Site naming inconsistencies
- Missing traffic data
- Incorrect campaign filtering

**Solutions:**
1. Check for variations in site names (e.g., "DSP A" vs "DSP_A")
2. Verify all sites have traffic in the date range
3. Remove campaign filters to see full picture
4. Check for data quality issues in adserver_traffic

### Issue: Conversion Rates Don't Match Other Reports

**Expected Differences:**
- AMC uses last-touch attribution
- 30-day lookback window (configurable)
- Includes post-campaign conversions
- Not competition-aware

**Understanding Discrepancies:**
- AMC may show higher conversion counts
- Different attribution models produce different results
- Post-campaign conversions included in AMC

### Issue: Query Performance

**Optimization Tips:**
1. Limit date ranges to necessary periods
2. Use campaign filters to reduce data volume
3. Consider running for individual campaigns first
4. Remove revenue calculations if not needed

### Issue: Sites Not Showing in Results

**Possible Causes:**
- Sites have no impressions or clicks
- Site field is NULL in adserver_traffic
- Search vendors stored in different field

**Solutions:**
1. Check COALESCE logic for adserver_site and search_vendor
2. Verify sites have traffic events (impressions or clicks)
3. Run exploratory query to see all available sites
4. Check for data ingestion issues

## Best Practices

### Data Quality Checks
1. Verify total reach equals sum of exposure groups
2. Check that converted_users ≤ reach for each group
3. Ensure overlap percentages sum to 100%

### Attribution Configuration
1. Align lookback windows with business logic
2. Consider click vs. impression attribution needs
3. Document any custom attribution settings

### Regular Monitoring
1. Track overlap trends over time
2. Monitor conversion rate changes
3. Compare incremental reach by site
4. Evaluate cost efficiency metrics""",
                'display_order': 7,
                'is_collapsible': True,
                'default_expanded': False
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
                'title': 'Find Campaigns with Multiple Sites',
                'description': 'Explore campaigns and sites to identify those with multiple site placements',
                'sql_query': """-- Campaign and Advertisers Exploratory Query
SELECT
  advertiser,
  advertiser_id,
  campaign,
  campaign_id,
  adserver_site,
  SUM(impressions) AS imps,
  SUM(clicks) AS total_clicks
FROM
  adserver_traffic
WHERE
  event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
GROUP BY
  1, 2, 3, 4, 5
ORDER BY 
  campaign_id, 
  adserver_site
LIMIT 500""",
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
                'interpretation_notes': 'Look for campaigns where the same campaign_id appears with different adserver_site values. These are candidates for overlap analysis.'
            },
            {
                'guide_id': guide_id,
                'title': 'Identify Conversion Activities',
                'description': 'Find available conversion activities for your advertiser',
                'sql_query': """-- Conversion Activity Exploratory Query
SELECT
  advertiser,
  advertiser_id,
  conversion_activity,
  conversion_activity_id,
  SUM(conversions) AS total_conversions
FROM
  adserver_conversions
WHERE
  event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
GROUP BY
  1, 2, 3, 4
ORDER BY 
  total_conversions DESC
LIMIT 100""",
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
                'interpretation_notes': 'Note the conversion_activity_id values you want to track in your main analysis.'
            },
            {
                'guide_id': guide_id,
                'title': 'Site Overlap and Conversions Analysis',
                'description': 'Main query to analyze site overlap and conversion impact',
                'sql_query': """-- Instructional Query: Amazon Ad Server - Site Overlap and Conversions
/* This query measures audience overlap between sites and conversion impact */

/* REQUIRED UPDATE: Set your advertiser ID(s) */
WITH advertiser_ids (advertiser_id) AS (
  VALUES
    ({{advertiser_id}})  -- UPDATE with your advertiser_id
),

/* OPTIONAL: Filter to specific campaigns - leave empty to analyze all */
campaign_ids (campaign_id) AS (
  VALUES
    {{#if campaign_ids}}
    {{#each campaign_ids}}
    ({{this}}){{#unless @last}},{{/unless}}
    {{/each}}
    {{else}}
    (NULL)  -- Will be ignored
    {{/if}}
),

/* OPTIONAL: Filter to specific conversion activities */
conversion_activity_ids (conversion_activity_id) AS (
  VALUES
    {{#if conversion_activity_ids}}
    {{#each conversion_activity_ids}}
    ({{this}}){{#unless @last}},{{/unless}}
    {{/each}}
    {{else}}
    (NULL)  -- Will be ignored
    {{/if}}
),

-- Gather impressions and clicks
traffic_only AS (
  SELECT
    COALESCE(adserver_site, search_vendor) AS site,
    user_id,
    campaign_id,
    campaign,
    advertiser_id
  FROM
    adserver_traffic
  WHERE
    advertiser_id IN (SELECT advertiser_id FROM advertiser_ids)
    {{#if campaign_ids}}
    AND campaign_id IN (SELECT campaign_id FROM campaign_ids WHERE campaign_id IS NOT NULL)
    {{/if}}
    AND (impressions = 1 OR clicks = 1)
),

-- Create exposure groups by user and campaign
assembled AS (
  SELECT
    campaign_id,
    campaign,
    user_id,
    ARRAY_SORT(COLLECT(DISTINCT site)) AS site_channel
  FROM
    traffic_only
  GROUP BY
    1, 2, 3
),

-- Prepare traffic data with extended window for attribution
traffic AS (
  SELECT
    advertiser_id,
    campaign_id,
    campaign,
    clicks,
    event_dt_utc AS traffic_dt,
    event_date_utc,
    impressions,
    user_id
  FROM
    TABLE(
      EXTEND_TIME_WINDOW('adserver_traffic', 'P0D', 'P{{attribution_window}}D')
    )
  WHERE
    advertiser_id IN (SELECT advertiser_id FROM advertiser_ids)
    AND (clicks = 1 OR impressions = 1)
),

-- Match conversions to traffic events
matched AS (
  SELECT
    t.advertiser_id,
    t.campaign_id,
    t.event_date_utc,
    t.traffic_dt,
    c.conversion_id,
    c.conversion_activity_id,
    c.revenue,
    c.conversions,
    c.user_id,
    CASE
      WHEN t.clicks = 1 THEN 1
      WHEN t.impressions = 1 THEN 2
    END AS match_type,
    SECONDS_BETWEEN(t.traffic_dt, c.event_dt_utc) AS match_age
  FROM
    TABLE(
      EXTEND_TIME_WINDOW('adserver_conversions', 'P0D', 'P{{attribution_window}}D')
    ) c
    INNER JOIN traffic t 
      ON c.user_id = t.user_id
      AND c.advertiser_id = t.advertiser_id
  {{#if conversion_activity_ids}}
  WHERE c.conversion_activity_id IN (SELECT conversion_activity_id FROM conversion_activity_ids WHERE conversion_activity_id IS NOT NULL)
  {{/if}}
),

-- Rank matches for attribution
ranked AS (
  SELECT
    user_id,
    advertiser_id,
    campaign_id,
    event_date_utc,
    traffic_dt,
    revenue,
    conversions,
    match_type,
    ROW_NUMBER() OVER(
      PARTITION BY conversion_id
      ORDER BY match_type, match_age
    ) AS match_rank,
    conversion_id
  FROM
    matched
  WHERE
    match_age BETWEEN 0 AND CASE
      WHEN match_type = 1 THEN {{attribution_window}} * 24 * 60 * 60  -- Clicks
      WHEN match_type = 2 THEN {{attribution_window}} * 24 * 60 * 60  -- Impressions
    END
    {{#if click_only_attribution}}
    AND match_type = 1  -- Clicks only
    {{/if}}
),

-- Select winning attribution
winners AS (
  SELECT
    campaign_id,
    user_id,
    traffic_dt,
    conversions,
    revenue
  FROM
    ranked
  WHERE
    match_rank = 1
    AND traffic_dt > BUILT_IN_PARAMETER('TIME_WINDOW_START')
    AND traffic_dt < BUILT_IN_PARAMETER('TIME_WINDOW_END')
),

-- Join exposure groups with conversions
joined AS (
  SELECT
    a.campaign_id,
    a.campaign,
    a.site_channel,
    a.user_id,
    w.conversions,
    w.revenue,
    w.user_id AS con_user_id
  FROM
    assembled a
    LEFT JOIN winners w 
      ON a.campaign_id = w.campaign_id
      AND a.user_id = w.user_id
),

-- Calculate metrics by exposure group
exposure_group_table AS (
  SELECT
    campaign_id,
    campaign,
    site_channel AS exposure_group,
    COUNT(DISTINCT user_id) AS reach,
    COUNT(DISTINCT con_user_id) AS converted_users,
    SUM(conversions) AS conversions,
    ROUND((COUNT(DISTINCT con_user_id) * 100.0 / COUNT(DISTINCT user_id)), 2) AS conversion_rate,
    ROUND((SUM(conversions) * 1.0 / NULLIF(COUNT(DISTINCT con_user_id), 0)), 2) AS conversions_per_user
  FROM
    joined
  GROUP BY
    1, 2, 3
),

-- Calculate total reach
total_users AS (
  SELECT
    campaign_id,
    SUM(reach) AS total_users_reached
  FROM
    exposure_group_table
  GROUP BY
    1
)

-- Final output with all metrics
SELECT
  e.campaign_id,
  e.campaign,
  e.exposure_group,
  e.reach,
  e.converted_users,
  e.conversions,
  e.conversion_rate,
  e.conversions_per_user,
  ROUND((e.reach * 100.0 / t.total_users_reached), 2) AS size_of_the_exposure_group
FROM
  exposure_group_table e
  INNER JOIN total_users t 
    ON t.campaign_id = e.campaign_id
ORDER BY
  e.campaign_id,
  e.reach DESC""",
                'parameters_schema': {
                    'advertiser_id': {
                        'type': 'integer',
                        'required': True,
                        'description': 'Your advertiser ID (required)'
                    },
                    'campaign_ids': {
                        'type': 'array',
                        'default': None,
                        'description': 'Optional: specific campaign IDs to analyze'
                    },
                    'conversion_activity_ids': {
                        'type': 'array', 
                        'default': None,
                        'description': 'Optional: specific conversion activity IDs to track'
                    },
                    'attribution_window': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Attribution lookback window in days'
                    },
                    'click_only_attribution': {
                        'type': 'boolean',
                        'default': False,
                        'description': 'Use click-based attribution only (ignore impressions)'
                    }
                },
                'default_parameters': {
                    'advertiser_id': None,
                    'attribution_window': 30,
                    'click_only_attribution': False
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Focus on exposure groups with high reach and analyze conversion rate differences between single-site and multi-site exposure groups.'
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
                    # Example 1: Low overlap scenario
                    example1_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Low Overlap Scenario (Good for Reach)',
                        'sample_data': {
                            'rows': [
                                {'campaign_id': 11111111, 'campaign': 'Summer Campaign 2024', 'exposure_group': '[DSP A]', 'reach': 2345034, 'converted_users': 13000, 'conversions': 17890, 'conversion_rate': 0.55, 'conversions_per_user': 1.38, 'size_of_the_exposure_group': 55.95},
                                {'campaign_id': 11111111, 'campaign': 'Summer Campaign 2024', 'exposure_group': '[DSP B]', 'reach': 1789552, 'converted_users': 7563, 'conversions': 9762, 'conversion_rate': 0.42, 'conversions_per_user': 1.29, 'size_of_the_exposure_group': 42.70},
                                {'campaign_id': 11111111, 'campaign': 'Summer Campaign 2024', 'exposure_group': '[DSP A, DSP B]', 'reach': 56843, 'converted_users': 322, 'conversions': 998, 'conversion_rate': 0.57, 'conversions_per_user': 3.10, 'size_of_the_exposure_group': 1.36}
                            ]
                        },
                        'interpretation_markdown': """**Low Overlap Analysis (1.36% overlap)**

**Key Findings:**
- Sites reach almost entirely different audiences (98.64% unique reach)
- DSP A delivers 55.95% incremental reach
- DSP B delivers 42.70% incremental reach
- Minimal audience duplication between sites

**Performance Insights:**
- DSP A has better conversion rate (0.55% vs 0.42%)
- Users exposed to both sites show higher engagement (3.1 conversions per user)
- Overall conversion impact from overlap is minimal due to small overlap size

**Recommendations:**
1. Continue using both sites for maximum reach
2. Allocate budget proportionally to incremental reach
3. DSP A appears more efficient - consider slight budget shift
4. No need to worry about frequency capping between sites""",
                        'insights': [
                            'Sites are highly complementary with only 1.36% overlap',
                            'DSP A delivers better conversion rate and larger reach',
                            'Multi-site exposure users are 2.4x more engaged',
                            'Strategy is optimized for reach maximization'
                        ],
                        'display_order': 1
                    }
                    
                    # Example 2: High overlap scenario
                    example2_data = {
                        'guide_query_id': query_id,
                        'example_name': 'High Overlap Scenario (Potential Inefficiency)',
                        'sample_data': {
                            'rows': [
                                {'campaign_id': 22222222, 'campaign': 'Holiday Campaign 2024', 'exposure_group': '[Publisher Network]', 'reach': 987654, 'converted_users': 4567, 'conversions': 5890, 'conversion_rate': 0.46, 'conversions_per_user': 1.29, 'size_of_the_exposure_group': 32.15},
                                {'campaign_id': 22222222, 'campaign': 'Holiday Campaign 2024', 'exposure_group': '[Display Network]', 'reach': 876543, 'converted_users': 3890, 'conversions': 4567, 'conversion_rate': 0.44, 'conversions_per_user': 1.17, 'size_of_the_exposure_group': 28.54},
                                {'campaign_id': 22222222, 'campaign': 'Holiday Campaign 2024', 'exposure_group': '[Publisher Network, Display Network]', 'reach': 1206789, 'converted_users': 6789, 'conversions': 9876, 'conversion_rate': 0.56, 'conversions_per_user': 1.45, 'size_of_the_exposure_group': 39.31}
                            ]
                        },
                        'interpretation_markdown': """**High Overlap Analysis (39.31% overlap)**

**Key Findings:**
- Significant audience duplication between sites
- Only 60.69% of reach is incremental
- Publisher Network: 32.15% exclusive reach
- Display Network: 28.54% exclusive reach

**Performance Insights:**
- Overlapping audience has highest conversion rate (0.56%)
- Similar performance between individual sites (0.46% vs 0.44%)
- Moderate engagement increase in overlap group

**Recommendations:**
1. Consider consolidating to one primary site
2. If keeping both, implement frequency capping
3. Test reducing one site's budget by 50% and measure impact
4. Analyze cost efficiency - you may be paying twice for 39% of audience
5. If overlap converts better, this might be intentional frequency strategy""",
                        'insights': [
                            '39.31% of audience is reached by both sites - significant duplication',
                            'Overlap audience converts 22% better than single-site exposure',
                            'High overlap suggests targeting parameters are too similar',
                            'Opportunity to improve efficiency by 20-30% through consolidation'
                        ],
                        'display_order': 2
                    }
                    
                    # Example 3: Overlap drives conversions
                    example3_data = {
                        'guide_query_id': query_id,
                        'example_name': 'High Conversion Impact from Overlap',
                        'sample_data': {
                            'rows': [
                                {'campaign_id': 33333333, 'campaign': 'Product Launch 2024', 'exposure_group': '[Search Platform]', 'reach': 1567890, 'converted_users': 3456, 'conversions': 4321, 'conversion_rate': 0.22, 'conversions_per_user': 1.25, 'size_of_the_exposure_group': 45.67},
                                {'campaign_id': 33333333, 'campaign': 'Product Launch 2024', 'exposure_group': '[Social Media]', 'reach': 1234567, 'converted_users': 2345, 'conversions': 2890, 'conversion_rate': 0.19, 'conversions_per_user': 1.23, 'size_of_the_exposure_group': 35.96},
                                {'campaign_id': 33333333, 'campaign': 'Product Launch 2024', 'exposure_group': '[Search Platform, Social Media]', 'reach': 629874, 'converted_users': 8765, 'conversions': 15678, 'conversion_rate': 1.39, 'conversions_per_user': 1.79, 'size_of_the_exposure_group': 18.37}
                            ]
                        },
                        'interpretation_markdown': """**High Conversion Impact from Multi-Site Exposure**

**Key Findings:**
- Moderate overlap at 18.37%
- Dramatic conversion rate increase in overlap (1.39% vs 0.22%/0.19%)
- 6.3x higher conversion rate for multi-site exposed users
- Higher engagement depth (1.79 conversions per user)

**Performance Insights:**
- Single-site exposure shows low conversion rates
- Multi-touch strategy is highly effective
- Overlap group generates 53% of all conversions despite being 18% of reach
- Clear evidence of synergy between Search and Social

**Recommendations:**
1. Intentionally cultivate overlap - this is working!
2. Increase frequency targets to 2+ exposures across sites
3. Develop sequential messaging: Search (awareness) → Social (consideration)
4. Test increasing overlap to 25-30% through lookalike audiences
5. Implement conversion-optimized bidding on overlapping audiences
6. Consider this a successful full-funnel strategy""",
                        'insights': [
                            'Multi-site exposure increases conversion rate by 6.3x',
                            'Overlap audience generates 53% of conversions with 18% of reach',
                            'Clear synergy between Search Platform and Social Media',
                            'Full-funnel strategy is highly effective - maintain current approach'
                        ],
                        'display_order': 3
                    }
                    
                    # Insert example results
                    for example in [example1_data, example2_data, example3_data]:
                        example_response = client.table('build_guide_examples').insert(example).execute()
                        if example_response.data:
                            logger.info(f"Created example: {example['example_name']}")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'exposure_group',
                'display_name': 'Exposure Group',
                'definition': 'Site or combination of sites that delivered ads to a user. Displayed as an array like [DSP A] or [DSP A, DSP B]',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'reach',
                'display_name': 'Reach',
                'definition': 'Number of unique users in each exposure group',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'size_of_the_exposure_group',
                'display_name': 'Size of Exposure Group (%)',
                'definition': 'Percentage of total campaign audience in this exposure group',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'converted_users',
                'display_name': 'Converted Users',
                'definition': 'Number of unique users who completed a conversion after exposure',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversions',
                'display_name': 'Total Conversions',
                'definition': 'Total number of conversion events from users in the exposure group',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate',
                'display_name': 'Conversion Rate (%)',
                'definition': 'Percentage of exposed users who converted (converted_users / reach × 100)',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversions_per_user',
                'display_name': 'Conversions per User',
                'definition': 'Average number of conversions per converting user, indicating engagement depth',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'incremental_reach',
                'display_name': 'Incremental Reach',
                'definition': 'Users reached exclusively by a single site (not exposed to other sites)',
                'metric_type': 'concept',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'overlap_rate',
                'display_name': 'Overlap Rate (%)',
                'definition': 'Percentage of audience exposed to multiple sites',
                'metric_type': 'concept',
                'display_order': 9
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created Amazon Ad Server - Site Overlap and Conversions guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_adserver_site_overlap_guide()
    sys.exit(0 if success else 1)