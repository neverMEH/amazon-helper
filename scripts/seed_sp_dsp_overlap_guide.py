#!/usr/bin/env python3
"""
Seed script for Sponsored Products and DSP Display Overlap Analysis Build Guide
This script creates the comprehensive cross-channel analysis guide in the database
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

def create_sp_dsp_overlap_guide():
    """Create the Sponsored Products and DSP Display Overlap Analysis guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_sp_dsp_overlap',
            'name': 'Sponsored Products and DSP Display Overlap Analysis',
            'category': 'Cross-Channel Analysis',
            'short_description': 'Analyze the combined impact of Sponsored Products and DSP Display advertising to understand how multi-channel exposure affects purchase rates.',
            'tags': ['Cross-channel', 'Multi-touch attribution', 'Sponsored Products', 'DSP Display', 'Purchase analysis'],
            'icon': 'Layers',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 45,
            'prerequisites': [
                'Advertisers must have data from both Sponsored Products and Display in a single AMC instance',
                'Both ad types should have advertised the same products during the same time period',
                'Both ad products should have been running for at least one week during the same time period',
                'Wait at least 14 full days after the query\'s end date (see section 2.6 for explanation)'
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

This instructional query demonstrates the impact when Sponsored Products is used together with DSP Display advertising. When shoppers are exposed to both Display and Sponsored Products ads, we analyze the impact on ad-attributed purchase rate.

## 1.2 Requirements

- Advertisers must have data from both Sponsored Products and Display in a single AMC instance
- Both ad types should have advertised the same products during the same time period
- Both ad products should have been running for at least one week during the same time period
- Wait at least 14 full days after the query's end date (see section 2.6 for explanation)""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Data Returned

The query returns:
- **exposure_group**: Sponsored Products only, Display only, or both
- **unique_reach**: Number of distinct users reached
- **users_that_purchased**: Count of unique users that purchased
- **purchases**: Total purchases

## 2.2 Tables Used

| Table | Purpose | Notes |
|-------|---------|-------|
| `sponsored_ads_traffic` | Sponsored Products traffic data | Filter: `ad_product_type = 'sponsored_products'` |
| `dsp_impressions` | Display advertising impressions | Contains DSP campaign data |
| `amazon_attributed_events_by_traffic_time` | Purchase attribution data | Requires 14-day wait after query end date |

## 2.3 Query Configuration

**Important Updates Required:**
1. Replace placeholder Display campaign IDs: `(11111111111),(2222222222)`
2. Replace placeholder SP campaign names: `'SP_campaign_name1', 'SP_campaign_name2'`

Search for 'UPDATE' comments in the query to find these locations.

## 2.4 CFIDs Limitation

Customer Facing IDs (CFIDs) are not yet available for Sponsored Products. Use campaign names for filtering until CFIDs are available.

## 2.5 Time Considerations

- Query time depends on number of advertisers, traffic volume, and conversions
- Start with 1 day for testing, then expand to week/month
- Month-long queries may timeout for high-volume instances
- The AMC team is actively working on performance improvements

## 2.6 14-Day Attribution Window

Since the query uses `traffic_time` attributed table, wait at least 14 full days after the query's end date. 

**Example:** For November data (11/1-11/30), wait until 12/15 or later to run the query to capture all ad-attributed sales.""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': '3. Data Interpretation',
                'content_markdown': """## 3.1 Exposure Groups Defined

| Exposure Group | Definition |
|---------------|------------|
| **both** | Users exposed to both Sponsored Products and Display ads |
| **SP** | Users exposed to Sponsored Products only (or both, but Display came after conversion) |
| **DISPLAY** | Users exposed to Display only (or both, but SP came after conversion) |
| **none** | Users who purchased without recorded impressions (ignore for insights) |

## 3.2 Metrics Defined

| Metric | Definition |
|--------|------------|
| **unique_reach** | Number of distinct users reached (each user assigned to one group only) |
| **users_that_purchased** | Number of unique users who purchased at least once |
| **purchases** | Total number of purchase events including promoted products |""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'analysis',
                'title': '4. Analysis Examples',
                'content_markdown': """## 4.1 Calculating Reach Distribution

Calculate what percentage of users were exposed to each ad type:

1. Sum total unique reach across all exposure groups
2. Calculate % reach = (group reach / total reach) × 100

**Example Results:**

| Exposure Group | Unique Reach | % Reach |
|---------------|-------------|---------|
| both | 201,820 | 6.63% |
| SP | 807,175 | 26.50% |
| DISPLAY | 2,036,761 | 66.87% |
| TOTAL | 3,045,756 | 100% |

## 4.2 Calculating Purchase Rates

For each exposure group: Purchase Rate = users_that_purchased / unique_reach

**Example Results:**

| Exposure Group | Unique Reach | Users That Purchased | Purchase Rate |
|---------------|-------------|---------------------|---------------|
| both | 201,820 | 5,590 | 2.77% |
| SP | 807,175 | 8,680 | 1.08% |
| DISPLAY | 2,036,761 | 1,842 | 0.09% |

## 4.3 Multi-Channel Impact Analysis

Compare the 'both' group to single-channel groups:

- **vs SP only:** 2.77% / 1.08% = **2.56x more likely to purchase**
- **vs Display only:** 2.77% / 0.09% = **30.78x more likely to purchase**

These results demonstrate the powerful synergy when users are exposed to both advertising channels, with multi-channel exposure significantly outperforming single-channel exposure.""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': '5. Best Practices',
                'content_markdown': """## Best Practices for Overlap Analysis

1. **Always wait 14+ days** after the query end date before running to ensure complete attribution data
2. **Start with small time windows** for testing (1 day) to validate query performance
3. **Filter out the 'none' exposure group** for insights as these represent unattributed purchases
4. **Use campaign names for Sponsored Products** until CFIDs are available
5. **Consider query performance** when selecting date ranges - high-volume instances may require shorter periods
6. **Document your campaign IDs** clearly for reproducibility
7. **Compare purchase rates** rather than absolute numbers for fair comparison across groups
8. **Consider seasonality** when interpreting results - run analysis across different time periods
9. **Monitor both reach and conversion** to understand the full funnel impact
10. **Use results to inform budget allocation** between channels based on incremental impact""",
                'display_order': 5,
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
        
        # Create the main overlap analysis query
        main_query = {
            'guide_id': guide_id,
            'title': 'Sponsored Products and DSP Display Overlap Analysis',
            'description': 'Analyze the combined impact of Sponsored Products and DSP Display advertising on purchase rates',
            'sql_query': """-- Instructional Query: Sponsored Products and DSP Display Overlap
-- UPDATE with your Display campaign ID(s)
WITH Display (campaign_id) AS (
  VALUES
    (11111111111),
    (2222222222)
),
-- UPDATE the Sponsored Products campaign names
SP (campaign) AS (
  VALUES
    ('SP_campaign_name1'),
    ('SP_campaign_name2')
),
-- all purchases attributed to Display or SP
purchases AS (
  SELECT
    user_id,
    conversion_event_dt,
    UUID() AS conversion_id,
    SUM(if(ad_product_type IS NULL, purchases, 0)) AS display_purchases,
    SUM(
      IF(
        ad_product_type = 'sponsored_products',
        total_purchases_clicks,
        0
      )
    ) AS search_purchases
  FROM
    amazon_attributed_events_by_traffic_time
  WHERE
    (
      campaign_id IN (
        SELECT
          campaign_id
        FROM
          Display
      )
      OR campaign IN (
        SELECT
          campaign
        FROM
          SP
      )
    )
  GROUP BY
    1, 2, 3
),
-- one line per user_id with date of last purchase
purchases_last_total AS (
  SELECT
    user_id,
    MAX(conversion_event_dt) AS conversion_event_dt_last,
    SUM(display_purchases + search_purchases) AS purchases,
    SUM(display_purchases) AS display_purchases,
    SUM(search_purchases) AS search_purchases
  FROM
    purchases
  WHERE
    display_purchases + search_purchases > 0
  GROUP BY
    1
),
-- UNION all table to get all impressions: Sponsored and Display
impressions AS (
  -- Table for Sponsored Products Impressions
  SELECT
    user_id,
    UUID() AS impression_id,
    event_dt AS impression_dt,
    'SP' AS IMP_ad_type,
    SUM(impressions) AS impressions
  FROM
    sponsored_ads_traffic
  WHERE
    impressions > 0
    AND ad_product_type = 'sponsored_products'
    AND campaign IN (
      SELECT
        campaign
      FROM
        SP
    )
  GROUP BY
    1, 2, 3
  UNION ALL
  --Table for Display
  SELECT
    user_id,
    UUID() AS impression_id,
    impression_dt AS impression_dt,
    'DISPLAY' AS IMP_ad_type,
    SUM(impressions) AS impressions
  FROM
    dsp_impressions
  WHERE
    impressions > 0
    AND campaign_id IN (
      SELECT
        campaign_id
      FROM
        Display
    )
  GROUP BY
    1, 2, 3
),
-- reducing impression table, max 2 rows per user_id
impressions_first_total AS (
  SELECT
    user_id,
    IMP_ad_type,
    MIN(impression_dt) AS impression_dt_first,
    SUM(impressions) AS impressions
  FROM
    impressions
  GROUP BY
    1, 2
),
-- Combine purchases + impressions and add impression timing dimension
combined AS (
  SELECT
    imp.user_id AS imp_USER,
    pur.user_id AS pur_USER,
    IMP_ad_type,
    impressions,
    impression_dt_first,
    purchases,
    display_purchases,
    search_purchases,
    conversion_event_dt_last,
    CASE
      WHEN conversion_event_dt_last IS NULL THEN 'no purchase'
      WHEN conversion_event_dt_last > impression_dt_first THEN 'pre-purchase'
      WHEN conversion_event_dt_last < impression_dt_first THEN 'post-purchase'
      ELSE 'other'
    END AS impression_timing
  FROM
    purchases_last_total pur
    FULL OUTER JOIN impressions_first_total imp ON pur.user_id = imp.user_id
),
-- Bin the data based on impression timing and separate by ad product
binned_data AS (
  SELECT
    imp_USER,
    pur_USER,
    SUM(
      IF(
        impression_timing = 'no purchase'
        AND IMP_ad_type = 'DISPLAY',
        impressions,
        0
      )
    ) AS no_purch_DISPLAY_impressions,
    SUM(
      IF(
        impression_timing = 'pre-purchase'
        AND IMP_ad_type = 'DISPLAY',
        impressions,
        0
      )
    ) AS pre_purch_DISPLAY_impressions,
    SUM(
      IF(
        impression_timing = 'post-purchase'
        AND IMP_ad_type = 'DISPLAY',
        impressions,
        0
      )
    ) AS post_purch_DISPLAY_impressions,
    SUM(
      IF(
        impression_timing = 'other'
        AND IMP_ad_type = 'DISPLAY',
        impressions,
        0
      )
    ) AS other_DISPLAY_impressions,
    SUM(IF(IMP_ad_type = 'DISPLAY', impressions, 0)) AS total_DISPLAY_impressions,
    SUM(
      IF(
        impression_timing = 'no purchase'
        AND IMP_ad_type = 'SP',
        impressions,
        0
      )
    ) AS no_purch_SP_impressions,
    SUM(
      IF(
        impression_timing = 'pre-purchase'
        AND IMP_ad_type = 'SP',
        impressions,
        0
      )
    ) AS pre_purch_SP_impressions,
    SUM(
      IF(
        impression_timing = 'post-purchase'
        AND IMP_ad_type = 'SP',
        impressions,
        0
      )
    ) AS post_purch_SP_impressions,
    SUM(
      IF(
        impression_timing = 'other'
        AND IMP_ad_type = 'SP',
        impressions,
        0
      )
    ) AS other_SP_impressions,
    SUM(IF(IMP_ad_type = 'SP', impressions, 0)) AS total_SP_impressions,
    MAX(purchases) AS purchases,
    MAX(display_purchases) AS display_purchases,
    MAX(search_purchases) AS search_purchases
  FROM
    combined
  GROUP BY
    1, 2
),
users_purchased AS (
  SELECT
    imp_USER,
    pur_USER,
    SUM(no_purch_DISPLAY_impressions) AS no_purch_DISPLAY_impressions,
    SUM(pre_purch_DISPLAY_impressions) AS pre_purch_DISPLAY_impressions,
    SUM(no_purch_SP_impressions) AS no_purch_SP_impressions,
    SUM(pre_purch_SP_impressions) AS pre_purch_SP_impressions
  FROM
    binned_data
  WHERE
    purchases > 0
  GROUP BY
    1, 2
),
users_purchased_exp AS (
  SELECT
    IF(
      (
        pre_purch_DISPLAY_impressions > 0
        AND pre_purch_SP_impressions > 0
      )
      OR (
        no_purch_DISPLAY_impressions > 0
        AND no_purch_SP_impressions > 0
      ),
      'both',
      IF(
        (
          pre_purch_DISPLAY_impressions > 0
          OR no_purch_DISPLAY_impressions > 0
        )
        AND (
          pre_purch_SP_impressions = 0
          AND no_purch_SP_impressions = 0
        ),
        'DISPLAY',
        IF(
          (
            pre_purch_DISPLAY_impressions = 0
            AND no_purch_DISPLAY_impressions = 0
          )
          AND (
            pre_purch_SP_impressions > 0
            OR no_purch_SP_impressions > 0
          ),
          'SP',
          IF(
            pre_purch_DISPLAY_impressions = 0
            AND no_purch_DISPLAY_impressions = 0
            AND pre_purch_SP_impressions = 0
            AND no_purch_SP_impressions = 0,
            'none',
            'NA'
          )
        )
      )
    ) AS exposure_group,
    COUNT(DISTINCT imp_USER) AS users_that_purchased_with_impressions,
    COUNT(DISTINCT pur_USER) AS users_that_purchased
  FROM
    users_purchased
  GROUP BY
    exposure_group
),
-- Create exposure group showing when exposed to one, both, or neither ad product
users_all_exp AS (
  SELECT
    IF(
      (
        pre_purch_DISPLAY_impressions > 0
        AND pre_purch_SP_impressions > 0
      )
      OR (
        no_purch_DISPLAY_impressions > 0
        AND no_purch_SP_impressions > 0
      ),
      'both',
      IF(
        (
          pre_purch_DISPLAY_impressions > 0
          OR no_purch_DISPLAY_impressions > 0
        )
        AND (
          pre_purch_SP_impressions = 0
          AND no_purch_SP_impressions = 0
        ),
        'DISPLAY',
        IF(
          (
            pre_purch_DISPLAY_impressions = 0
            AND no_purch_DISPLAY_impressions = 0
          )
          AND (
            pre_purch_SP_impressions > 0
            OR no_purch_SP_impressions > 0
          ),
          'SP',
          IF(
            pre_purch_DISPLAY_impressions = 0
            AND no_purch_DISPLAY_impressions = 0
            AND pre_purch_SP_impressions = 0
            AND no_purch_SP_impressions = 0,
            'none',
            'NA'
          )
        )
      )
    ) AS exposure_group,
    COUNT(DISTINCT imp_USER) AS unique_reach,
    SUM(purchases) AS purchases,
    SUM(display_purchases) AS display_purchases,
    SUM(search_purchases) AS search_purchases,
    SUM(no_purch_DISPLAY_impressions) AS no_purch_DISPLAY_impressions,
    SUM(pre_purch_DISPLAY_impressions) AS pre_purch_DISPLAY_impressions,
    SUM(post_purch_DISPLAY_impressions) AS post_purch_DISPLAY_impressions,
    SUM(other_DISPLAY_impressions) AS other_DISPLAY_impressions,
    SUM(total_DISPLAY_impressions) AS total_DISPLAY_impressions,
    SUM(no_purch_SP_impressions) AS no_purch_SP_impressions,
    SUM(pre_purch_SP_impressions) AS pre_purch_SP_impressions,
    SUM(post_purch_SP_impressions) AS post_purch_SP_impressions,
    SUM(other_SP_impressions) AS other_SP_impressions,
    SUM(total_SP_impressions) AS total_SP_impressions
  FROM
    binned_data
  GROUP BY
    exposure_group
)
SELECT
  a.exposure_group,
  unique_reach,
  users_that_purchased,
  purchases
FROM
  users_all_exp a
  LEFT JOIN users_purchased_exp p ON a.exposure_group = p.exposure_group""",
            'parameters_schema': {
                'display_campaign_ids': {
                    'type': 'array',
                    'default': [11111111111, 2222222222],
                    'description': 'Display campaign IDs to analyze'
                },
                'sp_campaign_names': {
                    'type': 'array',
                    'default': ['SP_campaign_name1', 'SP_campaign_name2'],
                    'description': 'Sponsored Products campaign names to analyze'
                }
            },
            'default_parameters': {
                'display_campaign_ids': [11111111111, 2222222222],
                'sp_campaign_names': ['SP_campaign_name1', 'SP_campaign_name2']
            },
            'display_order': 1,
            'query_type': 'main_analysis',
            'interpretation_notes': 'Focus on the "both" exposure group to understand multi-channel impact. Compare purchase rates across groups to quantify the incremental value of multi-channel exposure.'
        }
        
        # Insert main query
        response = client.table('build_guide_queries').insert(main_query).execute()
        if response.data:
            query_id = response.data[0]['id']
            logger.info(f"Created query: {main_query['title']}")
            
            # Add example results
            example_data = {
                'guide_query_id': query_id,
                'example_name': 'Sample Overlap Analysis Results',
                'sample_data': {
                    'rows': [
                        {'exposure_group': 'both', 'unique_reach': 201820, 'users_that_purchased': 5590, 'purchases': 6280},
                        {'exposure_group': 'SP', 'unique_reach': 807175, 'users_that_purchased': 8680, 'purchases': 10160},
                        {'exposure_group': 'DISPLAY', 'unique_reach': 2036761, 'users_that_purchased': 1842, 'purchases': 1921},
                        {'exposure_group': 'none', 'unique_reach': 40, 'users_that_purchased': 310, 'purchases': 345}
                    ]
                },
                'interpretation_markdown': """## Key Insights from Sample Results

### Reach Distribution
- **Display dominates reach** with 66.87% of users (2,036,761)
- **Sponsored Products** reaches 26.50% of users (807,175)
- **Multi-channel overlap** affects 6.63% of users (201,820)

### Purchase Rate Analysis
- **Multi-channel exposure (both):** 2.77% purchase rate (5,590 / 201,820)
- **SP only:** 1.08% purchase rate (8,680 / 807,175)
- **Display only:** 0.09% purchase rate (1,842 / 2,036,761)

### Multi-Channel Impact
Users exposed to both channels are:
- **2.56x more likely to purchase** than SP-only users
- **30.78x more likely to purchase** than Display-only users

### Strategic Recommendations
1. **Increase multi-channel coordination** - The synergy effect is substantial
2. **Expand Display reach for SP campaigns** - Low overlap suggests opportunity
3. **Optimize Display targeting** - Single-channel Display has lowest conversion
4. **Budget reallocation** - Consider increasing investment in coordinated campaigns
5. **Sequential messaging** - Design Display to prime users for SP conversion""",
                'insights': [
                    'Multi-channel exposure drives 2.77% purchase rate vs 1.08% for SP-only',
                    'Display reaches 2.5x more users but has 12x lower conversion when used alone',
                    'Only 6.63% of users see both channels - significant opportunity to increase overlap',
                    'The multiplier effect suggests strong complementary value between channels',
                    'Consider using Display for awareness and SP for conversion in coordinated campaigns'
                ],
                'display_order': 1
            }
            
            example_response = client.table('build_guide_examples').insert(example_data).execute()
            if example_response.data:
                logger.info("Created example results")
        else:
            logger.error(f"Failed to create query: {main_query['title']}")
        
        # Create exploratory query for checking available campaigns
        exploratory_query = {
            'guide_id': guide_id,
            'title': 'Explore Available Campaigns',
            'description': 'Check which Display and Sponsored Products campaigns are available in your AMC instance',
            'sql_query': """-- Exploratory query to find available campaigns
WITH display_campaigns AS (
    SELECT 
        'Display' as ad_type,
        campaign_id,
        campaign_name,
        COUNT(DISTINCT user_id) as unique_users,
        SUM(impressions) as total_impressions,
        MIN(impression_dt) as first_impression,
        MAX(impression_dt) as last_impression
    FROM dsp_impressions
    WHERE 
        impression_dt >= (CURRENT_DATE - INTERVAL '30' DAY)
    GROUP BY 
        campaign_id,
        campaign_name
    HAVING COUNT(DISTINCT user_id) > 100
),
sp_campaigns AS (
    SELECT 
        'Sponsored Products' as ad_type,
        campaign_id,
        campaign as campaign_name,
        COUNT(DISTINCT user_id) as unique_users,
        SUM(impressions) as total_impressions,
        MIN(event_dt) as first_impression,
        MAX(event_dt) as last_impression
    FROM sponsored_ads_traffic
    WHERE 
        ad_product_type = 'sponsored_products'
        AND event_dt >= (CURRENT_DATE - INTERVAL '30' DAY)
    GROUP BY 
        campaign_id,
        campaign
    HAVING COUNT(DISTINCT user_id) > 100
)
SELECT * FROM display_campaigns
UNION ALL
SELECT * FROM sp_campaigns
ORDER BY ad_type, unique_users DESC""",
            'parameters_schema': {},
            'default_parameters': {},
            'display_order': 0,
            'query_type': 'exploratory',
            'interpretation_notes': 'Use this query to identify which campaigns are available for analysis. Look for campaigns that ran during the same time period for best overlap analysis results.'
        }
        
        # Insert exploratory query
        response = client.table('build_guide_queries').insert(exploratory_query).execute()
        if response.data:
            logger.info(f"Created query: {exploratory_query['title']}")
        else:
            logger.error(f"Failed to create query: {exploratory_query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'exposure_group',
                'display_name': 'Exposure Group',
                'definition': 'Classification of user exposure: "both" (SP and Display), "SP" (Sponsored Products only), "DISPLAY" (Display only), or "none" (purchased without recorded impressions)',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'unique_reach',
                'display_name': 'Unique Reach',
                'definition': 'Number of distinct users reached in each exposure group. Each user is assigned to exactly one group based on their pre-purchase exposure pattern.',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'users_that_purchased',
                'display_name': 'Users That Purchased',
                'definition': 'Count of unique users who made at least one purchase after exposure to the advertising channel(s)',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'purchases',
                'display_name': 'Total Purchases',
                'definition': 'Total number of purchase events including promoted products and brand halo effects',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'purchase_rate',
                'display_name': 'Purchase Rate',
                'definition': 'Percentage of exposed users who made a purchase (users_that_purchased / unique_reach × 100)',
                'metric_type': 'calculated',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'display_purchases',
                'display_name': 'Display-Attributed Purchases',
                'definition': 'Purchases attributed specifically to Display advertising',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'search_purchases',
                'display_name': 'Search-Attributed Purchases',
                'definition': 'Purchases attributed specifically to Sponsored Products (search) advertising',
                'metric_type': 'metric',
                'display_order': 7
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created Sponsored Products and DSP Display Overlap Analysis guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_sp_dsp_overlap_guide()
    sys.exit(0 if success else 1)