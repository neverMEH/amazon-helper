#!/usr/bin/env python3
"""
Seed script for DSP Display and Streaming TV Overlap Analysis Build Guide
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

def create_dsp_streaming_tv_overlap_guide():
    """Create the DSP Display and Streaming TV Overlap Analysis guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_dsp_streaming_tv_overlap',
            'name': 'Amazon DSP Display and Streaming TV Overlap Analysis',
            'category': 'Campaign Optimization',
            'short_description': 'Analyze the synergistic impact of Streaming TV (OTT) and DSP Display advertising to understand how multi-channel exposure affects conversion rates.',
            'tags': ['DSP', 'streaming TV', 'OTT', 'display ads', 'media overlap', 'cross-channel', 'conversion analysis'],
            'icon': 'Layers',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 25,
            'prerequisites': [
                'Two or more DSP campaigns running simultaneously',
                'Campaigns targeting similar audiences for overlap potential',
                'Understanding of exposure groups',
                '14-day attribution window consideration'
            ],
            'is_published': True,
            'display_order': 3,
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

This instructional query (IQ) demonstrates the immediate impact that Streaming TV (previously called OTT) advertising has when used together with DSP Display advertising. When customers are exposed to both Streaming TV and Display ads, what is the impact on ad-attributed conversion rates (for example, purchase rates, pixel conversion rates, detail page view rates)? 

A CPG brand used this instructional query and found that audiences exposed to both Streaming TV and Display ads were **2x more likely to purchase** when compared to audiences exposed to only one media type.

## 1.2 Requirements

To use this query, advertisers need at least two different campaigns that were running at the same time for the same product or brand. While the query was developed for the overlap between Display and Streaming TV, it can be used for any two individual or any two sets of DSP campaigns (where impressions are stored in the dsp_impressions table). 

**Important Notes:**
- This IQ does not require a Streaming TV campaign - it can analyze any two DSP campaign types
- There should be some expected overlap with the users from both campaigns / campaign groups
- Choose campaigns that have at least some overlapping targeting

**Targeting Considerations:**
For example, do not choose a Display campaign that targeted shoppers who have purchased and a Streaming TV campaign that targeted shoppers who never purchased in the past. This is because both campaigns were set up to reach separate groups and the overlap will be minimal.""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Tables Used

| Table | Purpose | Notes |
|-------|---------|-------|
| `dsp_impressions` | Contains all DSP impression data | Includes both Display and Streaming TV campaigns |
| `amazon_attributed_events_by_traffic_time` | Contains conversion events | Uses 14-day attribution window |

**Important**: Due to the 14-day attribution window, wait two weeks past the end of the campaign to run this query to capture all conversions.

## 2.2 Query Template

The query is located in Section 4. Search "UPDATE" to find two places where you have to add campaign IDs replacing the current placeholders.

## 2.3 Code Modifications: Update the Campaign IDs

Note the changes required below to the campaign IDs in four locations:
- `11111111111` is a placeholder for your Display campaign(s)
- `22222222222` is a placeholder for your Streaming TV campaign(s)

This query can be modified for any two campaigns with conversions in `amazon_attributed_events_by_traffic_time` and impressions in `dsp_impressions`. It is not limited to Display + Streaming TV.

**Critical Requirements:**
- All campaign_ids in the 'conversions' CTE must also be present in the 'impressions' CTE and vice versa
- Campaign IDs must be properly segmented into the correct groups (Display vs Streaming TV)
- Misplacing campaign IDs will produce inaccurate results

## 2.4 Code Modifications: Update the metrics (optional)

The query example uses 'purchases' as the key metric. You can change this to any other metric like pixel conversions or detail page views by finding/replacing 'purchases' throughout the query.

**Available Metrics:**
- `purchases` - Total purchase events
- `pixel_conversions` - Custom pixel conversion events
- `detail_page_views` - Product detail page views
- `add_to_carts` - Add to cart events
- `subscribe_and_save_subscriptions` - Subscribe & Save signups""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': '3. Data Interpretation Instructions',
                'content_markdown': """## 3.1 Example Query Results

Sample data showing overlap performance:

| Exposure Group | Unique Reach | Users That Purchased | Purchases | User Purchase Rate | Purchases Per User |
|---------------|--------------|---------------------|-----------|-------------------|-------------------|
| Display_only | 542,000 | 14,000 | 19,600 | 2.58% | 1.4 |
| Streaming_TV_only | 1,500,000 | 1,050 | 1,575 | 0.07% | 1.5 |
| Both | 32,000 | 1,200 | 2,400 | 3.75% | 2.0 |
| None | 150 | 150 | 165 | - | 1.1 |

## 3.2 Exposure Groups Defined

**Exposure Groups:**

| Group | Definition |
|-------|------------|
| **both** | Users exposed to both Streaming TV and Display ads |
| **none** | Users that purchased but without recorded impressions (ignore for insights) |
| **Streaming_TV_only** | Users exposed only to Streaming TV ads, or both but Display came after conversion |
| **Display_only** | Users exposed only to Display ads, or both but Streaming TV came after conversion |

## 3.3 Metrics Defined

**Key Metrics:**

| Metric | Definition | Calculation |
|--------|------------|-------------|
| **unique_reach** | Number of distinct users reached | Each user assigned to one exposure group only |
| **users_that_purchased** | Number of unique users who purchased at least once | Count of distinct user_ids with purchases > 0 |
| **purchases** | Total purchase events | Including video rentals and Subscribe & Save subscriptions |
| **user_purchase_rate** | Percentage of reached users who purchased | users_that_purchased / unique_reach × 100 |
| **purchases_per_user** | Average purchases per converting user | purchases / users_that_purchased |

## 3.4 Results Interpretation

### 3.4.1 Purchase Rate Calculation

Purchase rate uses 'reach' in denominator with two options for numerator:
1. **Unique users who purchased** (users_that_purchased) - Recommended
2. Total purchases

The example uses option 1 for clearer user-level insights.

### 3.4.2 Interpretation of Example Data

Based on the sample results:
- Users exposed to both Display and Streaming TV are **1.45x more likely to purchase** than Display only (3.75% vs 2.58%)
- Users exposed to both ads purchase **2x on average** compared to 1.4x for Display only
- **Synergistic effect** demonstrates value of cross-channel advertising
- Streaming TV alone has very low conversion (0.07%) but dramatically amplifies Display effectiveness

### 3.4.3 Why Use Reach Instead of Impressions?

We're measuring user exposure to two ad types, not frequency of exposure. Using impressions would:
- Not accurately answer the exposure question
- Bias results since 'both' group always has minimum 2 impressions per user
- Conflate frequency effects with channel overlap effects

**Key Insight**: Reach-based analysis provides cleaner insights into channel synergy without frequency bias.""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'analysis',
                'title': '4. Advanced Analysis Techniques',
                'content_markdown': """## 4.1 Calculating Incremental Lift

### Baseline Performance
First, establish the baseline conversion rate for single-channel exposure:

```
Weighted Single Channel Rate = 
(Display_only_rate × Display_only_reach + Streaming_TV_only_rate × Streaming_TV_only_reach) / 
(Display_only_reach + Streaming_TV_only_reach)
```

### Incremental Lift Calculation
```
Incremental Lift = (Both_rate - Weighted_Single_Channel_Rate) / Weighted_Single_Channel_Rate × 100
```

**Example:**
- Weighted Single Channel: 1.06%
- Both exposure rate: 3.75%
- Incremental Lift: **253% improvement**

## 4.2 ROI Analysis Framework

### Cost Per Acquisition (CPA) by Exposure Group

| Exposure Group | Media Cost | Conversions | CPA | Index vs Display |
|---------------|------------|-------------|-----|------------------|
| Display_only | $54,200 | 14,000 | $3.87 | 100 |
| Streaming_TV_only | $225,000 | 1,050 | $214.29 | 5,537 |
| Both | $9,600 | 1,200 | $8.00 | 207 |

### Strategic Insights:
- While "both" has higher CPA than Display-only, the quality of conversions is higher
- Streaming TV alone is inefficient but acts as a force multiplier
- Optimal strategy: Use Streaming TV to prime high-value audiences for Display conversion

## 4.3 Audience Quality Analysis

### Purchase Frequency Distribution

| Exposure Group | Single Purchase | 2-3 Purchases | 4+ Purchases | Avg Order Value |
|---------------|----------------|---------------|--------------|-----------------|
| Display_only | 75% | 20% | 5% | $45 |
| Streaming_TV_only | 70% | 25% | 5% | $52 |
| Both | 60% | 30% | 10% | $68 |

**Key Finding**: Multi-channel exposed users show higher engagement and lifetime value potential.

## 4.4 Time-Based Analysis

### Conversion Window Analysis
Analyze when conversions occur relative to last exposure:

```sql
-- Add to main query
DATEDIFF('day', 
    GREATEST(last_display_impression, last_streaming_tv_impression), 
    conversion_event_dt) as days_to_conversion
```

**Typical Pattern:**
- Display_only: 80% convert within 3 days
- Streaming_TV_only: Conversions spread over 14 days
- Both: 70% convert within 5 days with higher total conversion rate""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': '5. Best Practices and Recommendations',
                'content_markdown': """## 5.1 Query Optimization Best Practices

1. **Start Small**: Begin with 1-day date ranges to test query performance
2. **Campaign Selection**: Ensure campaigns have overlapping target audiences
3. **Attribution Window**: Always wait 14+ days after campaign end before analysis
4. **Data Validation**: Check that campaign IDs exist in both conversions and impressions tables
5. **Metric Alignment**: Use consistent metrics across all CTEs

## 5.2 Common Pitfalls to Avoid

### ❌ Don't Do This:
- Mix campaign IDs between Display and Streaming TV groups
- Run query immediately after campaign ends (misses conversions)
- Compare campaigns with completely different audiences
- Use impression count for overlap analysis (use reach instead)
- Ignore the "none" group without investigation

### ✅ Do This Instead:
- Carefully map campaign IDs to correct media types
- Wait full attribution window (14+ days)
- Select campaigns with audience overlap potential
- Use unique user reach for fair comparison
- Investigate if "none" group is unusually large

## 5.3 Strategic Recommendations

### Campaign Planning
- **Sequential Messaging**: Design Streaming TV for awareness, Display for conversion
- **Audience Alignment**: Ensure targeting overlap of 10-20% minimum
- **Budget Allocation**: Start with 70/30 split (Display/Streaming TV) and adjust based on results
- **Creative Coordination**: Align messaging across channels for consistency

### Performance Optimization
- **Frequency Caps**: Set different caps per channel to maximize reach
- **Dayparting**: Streaming TV in evening, Display throughout day
- **Retargeting**: Use Display to retarget Streaming TV exposed users
- **Lookalike Expansion**: Create lookalikes from high-converting "both" segment

## 5.4 Reporting Template

### Executive Summary Format
```
Campaign Period: [Start Date] - [End Date]
Total Reach: [X] unique users
Multi-Channel Overlap: [X]% of total reach

Key Performance Indicators:
• Single Channel Conversion: [X]%
• Multi-Channel Conversion: [X]%
• Incremental Lift: [X]%
• Efficiency Gain: [X]x

Recommendation: [Increase/Maintain/Decrease] multi-channel investment
Expected Impact: [X]% increase in conversions with [X]% budget increase
```

## 5.5 Next Steps and Advanced Analysis

1. **Frequency Analysis**: Add impression frequency to understand optimal exposure levels
2. **Creative Performance**: Compare different creative combinations across channels
3. **Competitive Separation**: Analyze impact when competitors also advertise
4. **Seasonal Patterns**: Run analysis across different time periods
5. **Category Expansion**: Test strategy across different product categories
6. **Attribution Modeling**: Compare last-touch vs multi-touch attribution""",
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
            'title': 'DSP Display and Streaming TV Overlap Analysis',
            'description': 'Comprehensive query measuring the synergistic effect of Display and Streaming TV advertising on conversion rates',
            'sql_query': """-- Instructional Query: DSP Display and Streaming TV Overlap
-- UPDATE with your Display campaign ID/s
WITH Display (campaign_id) AS (
  VALUES
    (11111111111)
),
-- UPDATE with your Streaming TV campaign ID/s
streaming_TV (campaign_id) AS (
  VALUES
    (22222222222)
),
conversions AS (
  SELECT
    user_id,
    conversion_event_dt,
    SUM(purchases) AS purchases
  FROM
    amazon_attributed_events_by_traffic_time
  WHERE
    purchases > 0
    AND (
      campaign_id IN (
        SELECT
          campaign_id
        FROM
          streaming_TV
      )
      OR campaign_id IN (
        SELECT
          campaign_id
        FROM
          Display
      )
    )
  GROUP BY
    1,
    2
),
conversions_last_total AS (
  SELECT
    user_id,
    MAX(conversion_event_dt) AS conversion_event_dt_last,
    SUM(purchases) AS purchases
  FROM
    conversions
  GROUP BY
    1
),
impressions AS (
  SELECT
    user_id,
    impression_dt,
    'Streaming_TV' AS IMP_ad_type,
    SUM(impressions) AS impressions
  FROM
    dsp_impressions
  WHERE
    impressions > 0
    AND campaign_id IN (
      SELECT
        campaign_id
      FROM
        streaming_TV
    )
  GROUP BY
    1,
    2,
    3
  UNION ALL
  SELECT
    user_id,
    impression_dt,
    'Display' AS IMP_ad_type,
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
    1,
    2,
    3
),
impressions_first_total AS (
  SELECT
    user_id,
    IMP_ad_type,
    MIN(impression_dt) AS impression_dt_first,
    SUM(impressions) AS impressions
  FROM
    impressions
  GROUP BY
    1,
    2
),
combined AS (
  SELECT
    imp.user_id,
    IMP_ad_type,
    purchases,
    impressions,
    CASE
      WHEN conversion_event_dt_last IS NULL THEN 'no conversion'
      WHEN conversion_event_dt_last > impression_dt_first THEN 'pre-conversion'
      WHEN conversion_event_dt_last < impression_dt_first THEN 'post-conversion'
      ELSE 'other'
    END AS impression_timing
  FROM
    conversions_last_total conv
    FULL OUTER JOIN impressions_first_total imp ON conv.user_id = imp.user_id
),
combined2 AS (
  SELECT
    user_id,
    SUM(
      IF(
        impression_timing = 'no conversion'
        AND IMP_ad_type = 'Display',
        impressions,
        0
      )
    ) AS no_conv_display_impressions,
    SUM(
      IF(
        impression_timing = 'pre-conversion'
        AND IMP_ad_type = 'Display',
        impressions,
        0
      )
    ) AS pre_conv_display_impressions,
    SUM(
      IF(
        impression_timing = 'post-conversion'
        AND IMP_ad_type = 'Display',
        impressions,
        0
      )
    ) AS post_conv_display_impressions,
    SUM(
      IF(
        impression_timing = 'other'
        AND IMP_ad_type = 'Display',
        impressions,
        0
      )
    ) AS other_display_impressions,
    SUM(IF(IMP_ad_type = 'Display', impressions, 0)) AS total_display_impressions,
    SUM(
      IF(
        impression_timing = 'no conversion'
        AND IMP_ad_type = 'Streaming_TV',
        impressions,
        0
      )
    ) AS no_conv_Streaming_TV_impressions,
    SUM(
      IF(
        impression_timing = 'pre-conversion'
        AND IMP_ad_type = 'Streaming_TV',
        impressions,
        0
      )
    ) AS pre_conv_Streaming_TV_impressions,
    SUM(
      IF(
        impression_timing = 'post-conversion'
        AND IMP_ad_type = 'Streaming_TV',
        impressions,
        0
      )
    ) AS post_conv_Streaming_TV_impressions,
    SUM(
      IF(
        impression_timing = 'other'
        AND IMP_ad_type = 'Streaming_TV',
        impressions,
        0
      )
    ) AS other_Streaming_TV_impressions,
    SUM(IF(IMP_ad_type = 'Streaming_TV', impressions, 0)) AS total_Streaming_TV_impressions,
    MAX(purchases) AS purchases
  FROM
    combined
  GROUP BY
    user_id
),
users_converted AS (
  SELECT
    user_id,
    no_conv_display_impressions,
    pre_conv_display_impressions,
    post_conv_display_impressions,
    other_display_impressions,
    total_display_impressions,
    no_conv_Streaming_TV_impressions,
    pre_conv_Streaming_TV_impressions,
    post_conv_Streaming_TV_impressions,
    other_Streaming_TV_impressions,
    total_Streaming_TV_impressions,
    purchases
  FROM
    combined2
  WHERE
    purchases > 0
),
users_converted_exp AS (
  SELECT
    IF(
      (
        pre_conv_display_impressions > 0
        AND pre_conv_Streaming_TV_impressions > 0
      )
      OR (
        no_conv_display_impressions > 0
        AND no_conv_Streaming_TV_impressions > 0
      ),
      'both',
      IF(
        (
          pre_conv_display_impressions > 0
          OR no_conv_display_impressions > 0
        )
        AND (
          pre_conv_Streaming_TV_impressions = 0
          AND no_conv_Streaming_TV_impressions = 0
        ),
        'Display_only',
        IF(
          (
            pre_conv_display_impressions = 0
            AND no_conv_display_impressions = 0
          )
          AND (
            pre_conv_Streaming_TV_impressions > 0
            OR no_conv_Streaming_TV_impressions > 0
          ),
          'Streaming_TV_only',
          IF(
            pre_conv_display_impressions = 0
            AND no_conv_display_impressions = 0
            AND pre_conv_Streaming_TV_impressions = 0
            AND no_conv_Streaming_TV_impressions = 0,
            'none',
            'NA'
          )
        )
      )
    ) AS exposure_group,
    COUNT(DISTINCT user_id) AS users_that_purchased
  FROM
    users_converted
  GROUP BY
    exposure_group
),
users_all_exp AS (
  SELECT
    IF(
      (
        pre_conv_display_impressions > 0
        AND pre_conv_Streaming_TV_impressions > 0
      )
      OR (
        no_conv_display_impressions > 0
        AND no_conv_Streaming_TV_impressions > 0
      ),
      'both',
      IF(
        (
          pre_conv_display_impressions > 0
          OR no_conv_display_impressions > 0
        )
        AND (
          pre_conv_Streaming_TV_impressions = 0
          AND no_conv_Streaming_TV_impressions = 0
        ),
        'Display_only',
        IF(
          (
            pre_conv_display_impressions = 0
            AND no_conv_display_impressions = 0
          )
          AND (
            pre_conv_Streaming_TV_impressions > 0
            OR no_conv_Streaming_TV_impressions > 0
          ),
          'Streaming_TV_only',
          IF(
            pre_conv_display_impressions = 0
            AND no_conv_display_impressions = 0
            AND pre_conv_Streaming_TV_impressions = 0
            AND no_conv_Streaming_TV_impressions = 0,
            'none',
            'NA'
          )
        )
      )
    ) AS exposure_group,
    COUNT(DISTINCT user_id) AS unique_reach,
    SUM(purchases) AS purchases,
    SUM(no_conv_display_impressions) AS no_conv_display_impressions,
    SUM(pre_conv_display_impressions) AS pre_conv_display_impressions,
    SUM(post_conv_display_impressions) AS post_conv_display_impressions,
    SUM(other_display_impressions) AS other_display_impressions,
    SUM(total_display_impressions) AS total_display_impressions,
    SUM(no_conv_Streaming_TV_impressions) AS no_conv_Streaming_TV_impressions,
    SUM(pre_conv_Streaming_TV_impressions) AS pre_conv_Streaming_TV_impressions,
    SUM(post_conv_Streaming_TV_impressions) AS post_conv_Streaming_TV_impressions,
    SUM(other_Streaming_TV_impressions) AS other_Streaming_TV_impressions,
    SUM(total_Streaming_TV_impressions) AS total_Streaming_TV_impressions
  FROM
    combined2
  GROUP BY
    exposure_group
)
SELECT
  a.exposure_group,
  users_that_purchased,
  unique_reach,
  purchases,
  ROUND((users_that_purchased / unique_reach) * 100, 2) AS user_purchase_rate,
  ROUND((purchases / users_that_purchased), 2) AS purchases_per_user
FROM
  users_all_exp a
  LEFT JOIN users_converted_exp c ON a.exposure_group = c.exposure_group
ORDER BY
  CASE exposure_group
    WHEN 'both' THEN 1
    WHEN 'Display_only' THEN 2
    WHEN 'Streaming_TV_only' THEN 3
    WHEN 'none' THEN 4
    ELSE 5
  END""",
            'parameters_schema': {
                'display_campaign_ids': {
                    'type': 'array',
                    'default': [11111111111],
                    'description': 'Display campaign IDs to analyze'
                },
                'streaming_tv_campaign_ids': {
                    'type': 'array',
                    'default': [22222222222],
                    'description': 'Streaming TV campaign IDs to analyze'
                }
            },
            'default_parameters': {
                'display_campaign_ids': [11111111111],
                'streaming_tv_campaign_ids': [22222222222]
            },
            'display_order': 1,
            'query_type': 'main_analysis',
            'interpretation_notes': 'Search for UPDATE to add your campaign IDs. Wait 14 days after campaign end to capture all conversions. Ensure campaign ID alignment between conversions and impressions CTEs. Focus on the "both" exposure group to understand multi-channel impact.'
        }
        
        # Insert main query
        response = client.table('build_guide_queries').insert(main_query).execute()
        if response.data:
            query_id = response.data[0]['id']
            logger.info(f"Created query: {main_query['title']}")
            
            # Add example results
            example_data = {
                'guide_query_id': query_id,
                'example_name': 'Sample DSP and Streaming TV Overlap Results',
                'sample_data': {
                    'rows': [
                        {'exposure_group': 'both', 'unique_reach': 32000, 'users_that_purchased': 1200, 'purchases': 2400, 'user_purchase_rate': 3.75, 'purchases_per_user': 2.0},
                        {'exposure_group': 'Display_only', 'unique_reach': 542000, 'users_that_purchased': 14000, 'purchases': 19600, 'user_purchase_rate': 2.58, 'purchases_per_user': 1.4},
                        {'exposure_group': 'Streaming_TV_only', 'unique_reach': 1500000, 'users_that_purchased': 1050, 'purchases': 1575, 'user_purchase_rate': 0.07, 'purchases_per_user': 1.5},
                        {'exposure_group': 'none', 'unique_reach': None, 'users_that_purchased': 150, 'purchases': 165, 'user_purchase_rate': None, 'purchases_per_user': 1.1}
                    ]
                },
                'interpretation_markdown': """## Key Insights from Sample Results

### Reach Distribution
- **Streaming TV dominates reach** with 1,500,000 users (72.1% of total)
- **Display** reaches 542,000 users (26.0% of total)
- **Multi-channel overlap** affects only 32,000 users (1.5% of total)
- **Significant opportunity** to increase overlap exposure

### Purchase Rate Analysis
- **Multi-channel exposure (both):** 3.75% purchase rate
- **Display only:** 2.58% purchase rate
- **Streaming TV only:** 0.07% purchase rate

### Multi-Channel Impact - The Power of Synergy
Users exposed to both channels show:
- **1.45x higher purchase rate** than Display-only users
- **53.6x higher purchase rate** than Streaming TV-only users
- **2x purchases per user** compared to 1.4x for Display only

### Strategic Insights

#### 1. Streaming TV as a Force Multiplier
While Streaming TV alone has minimal direct conversion (0.07%), it dramatically amplifies Display effectiveness when combined.

#### 2. Untapped Opportunity
Only 1.5% of users see both channels, suggesting massive potential for coordinated campaigns.

#### 3. Quality over Quantity
Multi-channel exposed users not only convert more frequently but also make more purchases per user (2.0 vs 1.4).

### Recommended Actions
1. **Increase targeting overlap** between Display and Streaming TV campaigns
2. **Sequential strategy**: Use Streaming TV for awareness, followed by Display for conversion
3. **Budget reallocation**: Shift investment toward coordinated multi-channel campaigns
4. **Creative alignment**: Ensure consistent messaging across channels
5. **Audience expansion**: Create lookalike audiences from high-converting "both" segment""",
                'insights': [
                    'Users exposed to both Display and Streaming TV are 1.45x more likely to purchase than Display only',
                    'Streaming TV alone converts at 0.07% but acts as powerful amplifier for Display',
                    'Only 1.5% of users see both channels - massive opportunity to increase overlap',
                    'Multi-channel users make 2x purchases on average vs 1.4x for Display only',
                    'CPG brand case study showed 2x purchase likelihood with multi-channel exposure'
                ],
                'display_order': 1
            }
            
            example_response = client.table('build_guide_examples').insert(example_data).execute()
            if example_response.data:
                logger.info("Created example results")
        else:
            logger.error(f"Failed to create query: {main_query['title']}")
        
        # Create exploratory query for checking available DSP campaigns
        exploratory_query = {
            'guide_id': guide_id,
            'title': 'Explore Available DSP Campaigns',
            'description': 'Identify Display and Streaming TV campaigns available in your AMC instance for overlap analysis',
            'sql_query': """-- Exploratory query to identify Display vs Streaming TV campaigns
WITH campaign_summary AS (
    SELECT 
        campaign_id,
        campaign_name,
        -- Identify campaign type based on common naming patterns or metadata
        CASE 
            WHEN LOWER(campaign_name) LIKE '%streaming%' 
                OR LOWER(campaign_name) LIKE '%ott%' 
                OR LOWER(campaign_name) LIKE '%ctv%'
                OR LOWER(campaign_name) LIKE '%connected tv%'
            THEN 'Streaming TV'
            WHEN LOWER(campaign_name) LIKE '%display%'
                OR LOWER(campaign_name) LIKE '%banner%'
                OR LOWER(campaign_name) LIKE '%retarget%'
            THEN 'Display'
            ELSE 'Unclassified DSP'
        END AS campaign_type,
        COUNT(DISTINCT user_id) AS unique_users,
        SUM(impressions) AS total_impressions,
        COUNT(DISTINCT impression_dt) AS active_days,
        MIN(impression_dt) AS start_date,
        MAX(impression_dt) AS end_date
    FROM dsp_impressions
    WHERE 
        impression_dt >= (CURRENT_DATE - INTERVAL '90' DAY)
        AND impressions > 0
    GROUP BY 
        campaign_id,
        campaign_name
    HAVING COUNT(DISTINCT user_id) > 100
)
SELECT 
    campaign_type,
    campaign_id,
    campaign_name,
    unique_users,
    total_impressions,
    active_days,
    start_date,
    end_date,
    ROUND(total_impressions::FLOAT / unique_users, 2) AS avg_frequency
FROM campaign_summary
ORDER BY 
    campaign_type,
    unique_users DESC
LIMIT 100""",
            'parameters_schema': {},
            'default_parameters': {},
            'display_order': 0,
            'query_type': 'exploratory',
            'interpretation_notes': 'Review campaign names to identify which are Display vs Streaming TV. Look for campaigns running during overlapping time periods with similar audience sizes for best analysis results.'
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
                'definition': 'Classification of user exposure: "both" (Display and Streaming TV), "Display_only", "Streaming_TV_only", or "none" (purchased without recorded impressions)',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'unique_reach',
                'display_name': 'Unique Reach',
                'definition': 'Number of distinct users reached in each exposure group. Each user is counted exactly once based on their pre-conversion exposure pattern.',
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
                'definition': 'Total number of purchase events including video rentals and Subscribe & Save subscriptions',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_purchase_rate',
                'display_name': 'User Purchase Rate',
                'definition': 'Percentage of exposed users who made a purchase (users_that_purchased / unique_reach × 100)',
                'metric_type': 'calculated',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'purchases_per_user',
                'display_name': 'Purchases Per User',
                'definition': 'Average number of purchases per converting user (purchases / users_that_purchased)',
                'metric_type': 'calculated',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'incremental_lift',
                'display_name': 'Incremental Lift',
                'definition': 'Percentage improvement in conversion rate for multi-channel exposure compared to weighted single-channel baseline',
                'metric_type': 'calculated',
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
        
        logger.info("✅ Successfully created DSP Display and Streaming TV Overlap Analysis guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_dsp_streaming_tv_overlap_guide()
    sys.exit(0 if success else 1)