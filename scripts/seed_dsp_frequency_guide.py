#!/usr/bin/env python3
"""
Seed script for DSP Impression Frequency and Conversions Build Guide
This creates a comprehensive guide for analyzing optimal impression frequency in DSP campaigns
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.build_guide_formatter import create_guide_from_dict
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

# Define the complete guide data
guide_data = {
    'guide': {
        'guide_id': 'guide_dsp_impression_frequency_conversions',
        'name': 'Amazon DSP Impression Frequency and Conversions',
        'category': 'DSP Analysis',
        'short_description': 'Measure optimal impression frequency for DSP campaigns to maximize conversions while preventing overexposure',
        'difficulty_level': 'intermediate',
        'estimated_time_minutes': 30,
        'is_published': True,
        'display_order': 8,
        'tags': ['dsp', 'frequency-analysis', 'optimization', 'impression-frequency', 'conversion-optimization', 'reach'],
        'prerequisites': [
            'AMC Instance with DSP campaign data',
            'Understanding of frequency capping',
            'Active DSP campaigns with conversions'
        ],
        'icon': '📊'
    },
    'sections': [
        {
            'section_id': 'introduction',
            'title': 'Introduction',
            'display_order': 1,
            'is_collapsible': True,
            'default_expanded': True,
            'content_markdown': """## Purpose

This instructional query helps you determine the **optimal impression frequency** for your DSP campaigns by analyzing the relationship between ad exposure frequency and various conversion metrics. It answers critical questions about campaign efficiency and audience saturation.

### Key Business Questions Answered

1. **What is the optimal frequency cap** I should apply based on my KPIs?
2. **What percentage of impressions** are delivered to users in each frequency bucket?
3. **Would increasing frequency** translate to increased performance?
4. **Where is the point of diminishing returns** for ad exposure?
5. **Am I underexposing or overexposing** my audience?

### Why Frequency Analysis Matters

Frequency optimization can significantly impact campaign performance:
- **Cost Efficiency**: Avoid wasting budget on overexposed users
- **Reach Maximization**: Reallocate budget from high-frequency to new users
- **Performance Optimization**: Find the sweet spot between awareness and annoyance
- **Customer Experience**: Prevent ad fatigue while ensuring message retention

### Common Frequency Patterns

#### 1. Underexposure Pattern
- Majority of users in frequency_01 bucket
- Low overall conversion rates
- Opportunity to increase frequency caps

#### 2. Optimal Distribution
- Bell curve distribution across frequency buckets
- Clear performance peak at specific frequency
- Efficient budget utilization

#### 3. Overexposure Pattern
- Heavy concentration in high frequency buckets
- Flattening or declining performance
- Need for frequency capping

## Requirements

### Required:
- Active DSP campaigns during the analysis period
- Sufficient impression volume for statistical significance
- Conversion tracking properly configured

### Recommended:
- At least 30 days of campaign data
- Minimum 100,000 impressions
- Multiple campaigns for cross-campaign analysis"""
        },
        {
            'section_id': 'understanding_frequency',
            'title': 'Understanding Frequency Analysis',
            'display_order': 2,
            'is_collapsible': True,
            'default_expanded': True,
            'content_markdown': """## How Frequency Analysis Works

### Frequency Buckets Explained

Frequency buckets group users based on how many times they've seen your ads:

| Bucket | Definition | Typical Use |
|--------|------------|-------------|
| frequency_01 | Seen ad 1 time | Light exposure |
| frequency_02 | Seen ad 2 times | Minimal repetition |
| frequency_03-05 | Seen ad 3-5 times | Moderate exposure |
| frequency_06-10 | Seen ad 6-10 times | High exposure |
| frequency_11-24 | Seen ad 11-24 times | Very high exposure |
| frequency_25+ | Seen ad 25+ times | Excessive exposure |

### Key Metrics for Analysis

#### Volume Metrics
- **users_in_bucket**: Unique users at each frequency level
- **impressions_in_bucket**: Total impressions per frequency
- **reach_percentage**: % of total reach in each bucket

#### Performance Metrics
- **purchases**: Number of conversions per frequency
- **purchase_rate**: Conversion rate by frequency
- **product_sales**: Revenue generated per frequency
- **add_to_cart**: Mid-funnel actions
- **detail_page_view**: Upper-funnel engagement

### Analysis Approaches

#### 1. Cross-Campaign Analysis
- Aggregates all specified campaigns
- Provides overall frequency optimization
- Best for portfolio-level decisions

#### 2. Per-Campaign Analysis
- Individual campaign frequency patterns
- Identifies campaign-specific optimizations
- Useful for differentiated strategies

## Interpreting Frequency Curves

### Typical Performance Curve

```
Conversion Rate
    ^
    |     Peak Performance
    |         ___
    |       /     \\_____ Diminishing Returns
    |     /              \\___
    |   /                     Plateau
    | /
    |/________________________
    1  2  3  4  5  6  7  8  9  10+  Frequency
```

### Key Inflection Points

1. **Minimum Effective Frequency**: Where performance begins to rise
2. **Optimal Frequency**: Peak conversion rate
3. **Diminishing Returns**: Performance plateaus
4. **Oversaturation**: Performance may decline

## Common Patterns and Solutions

### Pattern 1: Steep Drop-off
**Observation**: 70%+ users at frequency_01
**Diagnosis**: Underexposure
**Solution**: 
- Increase frequency caps
- Extend campaign duration
- Improve audience targeting

### Pattern 2: Long Tail
**Observation**: Significant users at frequency_10+
**Diagnosis**: Overexposure to subset
**Solution**:
- Implement frequency caps
- Exclude converters
- Refresh creative

### Pattern 3: Flat Response
**Observation**: Similar performance across frequencies
**Diagnosis**: Message or audience mismatch
**Solution**:
- Review creative relevance
- Refine audience targeting
- Test different messages"""
        },
        {
            'section_id': 'interpreting_results',
            'title': 'Interpreting Results',
            'display_order': 3,
            'is_collapsible': True,
            'default_expanded': True,
            'content_markdown': """## Understanding Your Results

### Sample Analysis Results

| frequency_bucket | users_in_bucket | reach_percentage | purchase_rate | impressions_in_bucket |
|-----------------|-----------------|------------------|---------------|---------------------|
| frequency_01 | 1,299,242 | 66.65% | 0.02% | 1,299,242 |
| frequency_02 | 345,233 | 17.71% | 0.04% | 690,466 |
| frequency_03 | 125,587 | 6.44% | 0.05% | 376,761 |
| frequency_04 | 59,286 | 3.04% | 0.07% | 237,144 |
| frequency_05 | 38,472 | 1.97% | 0.09% | 192,360 |
| frequency_06-10 | 65,234 | 3.35% | 0.12% | 456,638 |
| frequency_11-15 | 12,456 | 0.64% | 0.11% | 155,700 |
| frequency_16-20 | 3,245 | 0.17% | 0.10% | 58,410 |
| frequency_21-25 | 567 | 0.03% | 0.09% | 12,474 |
| frequency_25+ | 123 | 0.01% | 0.08% | 3,690 |

### Key Insights from This Data

#### 1. Underexposure Problem
- **66.65% at frequency_01** indicates severe underexposure
- Majority of audience seeing ads only once
- Significant opportunity to increase frequency

#### 2. Performance Pattern
- Purchase rate increases from 0.02% to 0.12% (6x improvement)
- Peak performance at frequency_06-10 bucket
- Diminishing returns after frequency_10

#### 3. Reach Distribution
- 84.36% of users at frequency 1-2
- Only 4.19% reach optimal frequency (6-10)
- Less than 1% overexposed (frequency_16+)

### Recommendations Based on Pattern

#### For Underexposure Pattern (Example Above)
1. **Immediate Actions**:
   - Increase frequency cap from current to 10
   - Extend campaign flight dates
   - Increase daily budget to enable more impressions

2. **Targeting Adjustments**:
   - Narrow audience to increase frequency for core targets
   - Implement retargeting for single-exposure users
   - Use lookalike audiences for better engagement

3. **Expected Outcomes**:
   - 3-5x improvement in conversion rate
   - Better brand recall and consideration
   - More efficient CPM utilization

### Visual Analysis Guide

#### Creating Frequency Distribution Chart

```
Users by Frequency Bucket
70% |█████████████████████████| frequency_01 (66.65%)
    |████████| frequency_02 (17.71%)
    |███| frequency_03 (6.44%)
    |██| frequency_04 (3.04%)
    |█| frequency_05 (1.97%)
    |██| frequency_06-10 (3.35%)
    |·| frequency_11+ (<1%)
```

#### Performance Curve Visualization

```
Purchase Rate by Frequency
0.15% |                    ___
      |                  _/   \\_
0.10% |                _/       \\__
      |              _/            \\__
0.05% |            _/                 \\___
      |          _/                        \\___
0.00% |________/________________________________
      1  2  3  4  5  6-10  11-15  16-20  21-25  25+
```

### Identifying Optimal Frequency

#### Method 1: Peak Performance
Look for the frequency bucket with highest purchase rate:
- In example: frequency_06-10 at 0.12%
- Set frequency cap at upper bound (10)

#### Method 2: Diminishing Returns
Find where marginal benefit drops below 50%:
- Calculate improvement between buckets
- Identify where growth slows significantly
- Set cap just after this point

#### Method 3: Cost Efficiency
Calculate cost per incremental conversion:
- Compare additional impressions to additional conversions
- Find point where cost exceeds acceptable threshold
- Optimize for efficiency

### Common Scenarios and Solutions

#### Scenario 1: No Clear Peak
**Pattern**: Flat or continuously rising performance
**Solution**: 
- Test higher frequency caps
- May indicate strong message-market fit
- Consider budget/reach tradeoff

#### Scenario 2: Early Peak and Decline
**Pattern**: Performance drops after frequency_03-04
**Solution**:
- Implement strict frequency cap at peak
- Refresh creative more frequently
- Check for audience fatigue

#### Scenario 3: Bimodal Distribution
**Pattern**: Peaks at low and high frequency
**Solution**:
- Likely different audience segments
- Segment analysis recommended
- Differentiated frequency strategies

## Action Planning Template

Based on your frequency analysis:

### If Underexposed (>60% at frequency_01):
1. Week 1: Increase frequency cap to 2x current
2. Week 2: Monitor performance change
3. Week 3: Adjust based on results
4. Week 4: Test optimal frequency identified

### If Optimally Distributed:
1. Maintain current frequency settings
2. Test +/- 1 frequency level
3. Monitor for seasonal changes
4. Document as best practice

### If Overexposed (>10% at frequency_15+):
1. Immediately implement frequency cap
2. Exclude recent converters
3. Refresh creative assets
4. Reallocate budget to new audiences"""
        },
        {
            'section_id': 'optimization_strategies',
            'title': 'Optimization Strategies',
            'display_order': 4,
            'is_collapsible': True,
            'default_expanded': False,
            'content_markdown': """## Frequency Optimization Strategies

### Setting Frequency Caps

#### DSP Frequency Cap Options

| Cap Type | Setting | Use Case |
|----------|---------|----------|
| Daily | 2-3 impressions | High-frequency products |
| Weekly | 7-10 impressions | Standard campaigns |
| Monthly | 20-30 impressions | Long consideration cycles |
| Lifetime | 50+ impressions | Brand awareness campaigns |

#### Implementation Best Practices

1. **Gradual Adjustment**
   - Don't jump from no cap to strict cap
   - Reduce by 25% increments
   - Monitor performance at each level

2. **Segment-Specific Caps**
   - New customers: Higher frequency
   - Retargeting: Lower frequency
   - Cart abandoners: Medium frequency

3. **Creative Rotation**
   - Rotate every 3-5 exposures
   - Prevents message fatigue
   - Maintains engagement

### Advanced Optimization Techniques

#### 1. Dayparting with Frequency
```sql
-- Analyze frequency performance by hour of day
SELECT
  EXTRACT(HOUR FROM impression_time) AS hour_of_day,
  frequency_bucket,
  AVG(purchase_rate) AS avg_purchase_rate
FROM
  frequency_analysis
GROUP BY
  1, 2
```

Optimize delivery times based on when each frequency performs best.

#### 2. Cross-Device Frequency Management
- Account for multi-device exposure
- Implement household-level frequency caps
- Consider mobile vs. desktop patterns

#### 3. Sequential Messaging
Map creative sequence to frequency:
- Frequency 1-2: Awareness message
- Frequency 3-5: Consideration content
- Frequency 6+: Conversion focus

### Budget Reallocation Strategy

#### Calculate Wasted Impressions
```sql
-- Identify wasted impressions beyond optimal frequency
WITH optimal_frequency AS (
  SELECT 10 AS optimal_cap  -- Based on analysis
),
wasted AS (
  SELECT
    SUM(CASE 
      WHEN user_impressions > (SELECT optimal_cap FROM optimal_frequency)
      THEN user_impressions - (SELECT optimal_cap FROM optimal_frequency)
      ELSE 0
    END) AS wasted_impressions,
    SUM(user_impressions) AS total_impressions
  FROM
    user_impression_counts
)
SELECT
  wasted_impressions,
  total_impressions,
  ROUND(100.0 * wasted_impressions / total_impressions, 2) AS waste_percentage,
  wasted_impressions * avg_cpm / 1000 AS wasted_spend
FROM
  wasted
  CROSS JOIN (SELECT AVG(cpm) AS avg_cpm FROM campaign_metrics)
```

#### Reallocation Opportunities
1. **Reach Extension**: Use saved budget to reach new users
2. **Channel Diversification**: Invest in other ad products
3. **Creative Development**: Improve message quality
4. **Audience Testing**: Explore new segments

### Monitoring and Iteration

#### Weekly Monitoring Checklist
- [ ] Check frequency distribution changes
- [ ] Monitor conversion rate by frequency
- [ ] Review waste percentage
- [ ] Analyze new vs. returning user frequency
- [ ] Validate cap effectiveness

#### Monthly Optimization Cycle
1. **Week 1**: Gather data and run analysis
2. **Week 2**: Identify optimization opportunities
3. **Week 3**: Implement changes
4. **Week 4**: Monitor and document results

### Frequency Strategy by Campaign Type

#### Brand Awareness Campaigns
- **Goal**: Maximum reach with minimum frequency
- **Target**: 3-5 exposures per user
- **Cap**: Weekly cap of 5-7
- **Focus**: Reach over frequency

#### Consideration Campaigns
- **Goal**: Balanced frequency for engagement
- **Target**: 5-10 exposures per user
- **Cap**: Weekly cap of 10-12
- **Focus**: Engagement metrics

#### Conversion Campaigns
- **Goal**: Optimal frequency for purchase
- **Target**: Based on analysis (often 7-15)
- **Cap**: Match to optimal point
- **Focus**: Conversion rate and ROAS

#### Retargeting Campaigns
- **Goal**: Remind without annoying
- **Target**: 3-7 exposures
- **Cap**: Strict daily cap of 2-3
- **Focus**: Recency over frequency

## Success Metrics

### KPIs to Track

#### Efficiency Metrics
- Cost per reach point
- Wasted impression percentage
- Unique reach growth
- Frequency distribution health

#### Performance Metrics
- Conversion rate by frequency
- Optimal frequency stability
- Incremental conversions from optimization
- ROAS improvement

#### Experience Metrics
- Ad feedback scores
- Brand favorability
- Site engagement post-exposure
- Repeat purchase rates

### Reporting Template

Create monthly reports showing:
1. Frequency distribution chart
2. Performance curve
3. Optimal frequency identification
4. Waste analysis
5. Recommendations and next steps

### Expected Outcomes

After implementing frequency optimization:

#### Month 1
- 10-20% reduction in wasted impressions
- 5-10% increase in unique reach
- Baseline performance established

#### Month 2
- 15-25% improvement in conversion rate
- 20-30% better cost efficiency
- Clear optimal frequency identified

#### Month 3
- 25-40% overall ROAS improvement
- Stable frequency distribution
- Documented best practices"""
        }
    ],
    'queries': [
        {
            'title': 'Cross-Campaign Frequency Analysis',
            'description': 'Analyzes frequency and conversions across multiple campaigns',
            'sql_query': """-- DSP Impression Frequency and Conversions - Cross Campaign
WITH user_impression_counts AS (
  -- Count impressions per user
  SELECT
    user_id,
    SUM(impressions) AS user_impressions,
    MAX(campaign_id) AS sample_campaign_id
  FROM
    dsp_impressions
  WHERE
    -- Optional: Filter to specific campaigns
    (
      {{campaign_ids}} IS NULL 
      OR campaign_id = ANY({{campaign_ids}})
    )
  GROUP BY
    user_id
),
frequency_buckets AS (
  -- Assign users to frequency buckets
  SELECT
    user_id,
    user_impressions,
    CASE
      WHEN user_impressions = 1 THEN 'frequency_01'
      WHEN user_impressions = 2 THEN 'frequency_02'
      WHEN user_impressions = 3 THEN 'frequency_03'
      WHEN user_impressions = 4 THEN 'frequency_04'
      WHEN user_impressions = 5 THEN 'frequency_05'
      WHEN user_impressions BETWEEN 6 AND 10 THEN 'frequency_06-10'
      WHEN user_impressions BETWEEN 11 AND 15 THEN 'frequency_11-15'
      WHEN user_impressions BETWEEN 16 AND 20 THEN 'frequency_16-20'
      WHEN user_impressions BETWEEN 21 AND 25 THEN 'frequency_21-25'
      ELSE 'frequency_25+'
    END AS frequency_bucket
  FROM
    user_impression_counts
),
conversion_metrics AS (
  -- Get conversion metrics per user
  SELECT
    user_id,
    SUM(purchases) AS purchases,
    SUM(units_sold) AS units_sold,
    SUM(product_sales) AS product_sales,
    SUM(add_to_cart) AS add_to_cart,
    SUM(detail_page_view) AS detail_page_view
  FROM
    amazon_attributed_events_by_traffic_time
  WHERE
    -- Match campaign filter if provided
    (
      {{campaign_ids}} IS NULL 
      OR campaign_id = ANY({{campaign_ids}})
    )
  GROUP BY
    user_id
)
-- Final aggregation by frequency bucket
SELECT
  'Cross-Campaign Analysis' AS analysis_type,
  CURRENT_DATE - 7 AS start_date,
  CURRENT_DATE AS end_date,
  fb.frequency_bucket,
  COUNT(DISTINCT fb.user_id) AS users_in_bucket,
  SUM(fb.user_impressions) AS impressions_in_bucket,
  COALESCE(SUM(cm.purchases), 0) AS purchases,
  COALESCE(SUM(cm.units_sold), 0) AS units_sold,
  COALESCE(SUM(cm.product_sales), 0) AS product_sales,
  COALESCE(SUM(cm.add_to_cart), 0) AS add_to_cart,
  COALESCE(SUM(cm.detail_page_view), 0) AS detail_page_view,
  -- Calculate rates
  ROUND(
    100.0 * COALESCE(SUM(cm.purchases), 0) / NULLIF(COUNT(DISTINCT fb.user_id), 0), 
    2
  ) AS purchase_rate,
  ROUND(
    100.0 * COUNT(DISTINCT fb.user_id) / SUM(COUNT(DISTINCT fb.user_id)) OVER(), 
    2
  ) AS reach_percentage
FROM
  frequency_buckets fb
  LEFT JOIN conversion_metrics cm ON fb.user_id = cm.user_id
GROUP BY
  frequency_bucket
ORDER BY
  frequency_bucket""",
            'parameters_schema': {
                'campaign_ids': {
                    'type': 'array',
                    'description': 'Optional array of campaign IDs to filter',
                    'required': False
                }
            },
            'default_parameters': {
                'campaign_ids': None
            },
            'display_order': 1,
            'query_type': 'main_analysis',
            'interpretation_notes': 'Look for the frequency bucket with highest purchase rate to identify optimal frequency',
            'examples': [
                {
                    'example_name': 'Underexposure Pattern',
                    'sample_data': {
                        'rows': [
                            {
                                'frequency_bucket': 'frequency_01',
                                'users_in_bucket': 1299242,
                                'reach_percentage': 66.65,
                                'purchase_rate': 0.02,
                                'impressions_in_bucket': 1299242,
                                'purchases': 260,
                                'product_sales': 7800.00
                            },
                            {
                                'frequency_bucket': 'frequency_02',
                                'users_in_bucket': 345233,
                                'reach_percentage': 17.71,
                                'purchase_rate': 0.04,
                                'impressions_in_bucket': 690466,
                                'purchases': 138,
                                'product_sales': 4140.00
                            },
                            {
                                'frequency_bucket': 'frequency_03',
                                'users_in_bucket': 125587,
                                'reach_percentage': 6.44,
                                'purchase_rate': 0.05,
                                'impressions_in_bucket': 376761,
                                'purchases': 63,
                                'product_sales': 1890.00
                            },
                            {
                                'frequency_bucket': 'frequency_06-10',
                                'users_in_bucket': 65234,
                                'reach_percentage': 3.35,
                                'purchase_rate': 0.12,
                                'impressions_in_bucket': 456638,
                                'purchases': 78,
                                'product_sales': 2340.00
                            }
                        ]
                    },
                    'interpretation_markdown': """This data shows severe underexposure with 66.65% of users seeing ads only once. Purchase rate increases 6x from frequency_01 (0.02%) to frequency_06-10 (0.12%), indicating significant opportunity to improve performance by increasing frequency caps to 10.""",
                    'display_order': 1
                }
            ]
        },
        {
            'title': 'Per-Campaign Frequency Analysis',
            'description': 'Provides frequency analysis at individual campaign level',
            'sql_query': """-- DSP Impression Frequency and Conversions - Per Campaign
WITH campaign_user_impressions AS (
  -- Count impressions per user per campaign
  SELECT
    campaign_id,
    campaign_name,
    user_id,
    SUM(impressions) AS user_impressions
  FROM
    dsp_impressions
  WHERE
    (
      {{campaign_ids}} IS NULL 
      OR campaign_id = ANY({{campaign_ids}})
    )
  GROUP BY
    campaign_id,
    campaign_name,
    user_id
),
campaign_frequency_buckets AS (
  -- Assign frequency buckets per campaign
  SELECT
    campaign_id,
    campaign_name,
    user_id,
    user_impressions,
    CASE
      WHEN user_impressions = 1 THEN 'frequency_01'
      WHEN user_impressions = 2 THEN 'frequency_02'
      WHEN user_impressions = 3 THEN 'frequency_03'
      WHEN user_impressions = 4 THEN 'frequency_04'
      WHEN user_impressions = 5 THEN 'frequency_05'
      WHEN user_impressions BETWEEN 6 AND 10 THEN 'frequency_06-10'
      WHEN user_impressions BETWEEN 11 AND 15 THEN 'frequency_11-15'
      WHEN user_impressions BETWEEN 16 AND 20 THEN 'frequency_16-20'
      WHEN user_impressions BETWEEN 21 AND 25 THEN 'frequency_21-25'
      ELSE 'frequency_25+'
    END AS frequency_bucket
  FROM
    campaign_user_impressions
),
campaign_conversions AS (
  -- Get conversions by campaign and user
  SELECT
    campaign_id,
    user_id,
    SUM(purchases) AS purchases,
    SUM(units_sold) AS units_sold,
    SUM(product_sales) AS product_sales,
    SUM(add_to_cart) AS add_to_cart,
    SUM(detail_page_view) AS detail_page_view
  FROM
    amazon_attributed_events_by_traffic_time
  WHERE
    (
      {{campaign_ids}} IS NULL 
      OR campaign_id = ANY({{campaign_ids}})
    )
  GROUP BY
    campaign_id,
    user_id
)
-- Aggregate by campaign and frequency bucket
SELECT
  cfb.campaign_id,
  cfb.campaign_name,
  cfb.frequency_bucket,
  COUNT(DISTINCT cfb.user_id) AS users_in_bucket,
  SUM(cfb.user_impressions) AS impressions_in_bucket,
  COALESCE(SUM(cc.purchases), 0) AS purchases,
  COALESCE(SUM(cc.units_sold), 0) AS units_sold,
  COALESCE(SUM(cc.product_sales), 0) AS product_sales,
  COALESCE(SUM(cc.add_to_cart), 0) AS add_to_cart,
  COALESCE(SUM(cc.detail_page_view), 0) AS detail_page_view,
  ROUND(
    100.0 * COALESCE(SUM(cc.purchases), 0) / NULLIF(COUNT(DISTINCT cfb.user_id), 0), 
    2
  ) AS purchase_rate,
  ROUND(
    100.0 * COUNT(DISTINCT cfb.user_id) / 
    SUM(COUNT(DISTINCT cfb.user_id)) OVER(PARTITION BY cfb.campaign_id), 
    2
  ) AS reach_percentage_within_campaign
FROM
  campaign_frequency_buckets cfb
  LEFT JOIN campaign_conversions cc 
    ON cfb.campaign_id = cc.campaign_id 
    AND cfb.user_id = cc.user_id
GROUP BY
  cfb.campaign_id,
  cfb.campaign_name,
  cfb.frequency_bucket
ORDER BY
  cfb.campaign_id,
  cfb.frequency_bucket""",
            'parameters_schema': {
                'campaign_ids': {
                    'type': 'array',
                    'description': 'Optional array of campaign IDs to filter',
                    'required': False
                }
            },
            'default_parameters': {
                'campaign_ids': None
            },
            'display_order': 2,
            'query_type': 'main_analysis',
            'interpretation_notes': 'Compare frequency performance across different campaigns to identify campaign-specific optimization opportunities'
        },
        {
            'title': 'Optimal Frequency Finder',
            'description': 'Advanced query to identify optimal frequency automatically',
            'sql_query': """-- Find Optimal Frequency Point
WITH frequency_performance AS (
  SELECT
    frequency_bucket,
    users_in_bucket,
    purchase_rate,
    reach_percentage,
    impressions_in_bucket,
    purchases,
    -- Calculate marginal benefit
    purchase_rate - LAG(purchase_rate, 1, 0) OVER (ORDER BY frequency_bucket) AS marginal_benefit,
    -- Calculate cost per additional conversion
    CASE 
      WHEN purchases - LAG(purchases, 1, 0) OVER (ORDER BY frequency_bucket) > 0
      THEN (impressions_in_bucket - LAG(impressions_in_bucket, 1, 0) OVER (ORDER BY frequency_bucket)) / 
           (purchases - LAG(purchases, 1, 0) OVER (ORDER BY frequency_bucket))
      ELSE NULL
    END AS cost_per_incremental_conversion
  FROM (
    -- Insert the cross-campaign query CTEs here
    SELECT 
      frequency_bucket,
      users_in_bucket,
      impressions_in_bucket,
      purchases,
      purchase_rate,
      reach_percentage
    FROM cross_campaign_analysis
  ) AS aggregated_metrics
)
SELECT
  frequency_bucket,
  users_in_bucket,
  reach_percentage,
  purchase_rate,
  marginal_benefit,
  cost_per_incremental_conversion,
  CASE
    WHEN marginal_benefit > 0 AND 
         (LEAD(marginal_benefit, 1, 0) OVER (ORDER BY frequency_bucket) <= marginal_benefit * 0.5)
    THEN 'Potential Optimal Point'
    WHEN reach_percentage > 60 AND frequency_bucket = 'frequency_01'
    THEN 'Underexposure - Increase Frequency'
    WHEN reach_percentage < 1 AND purchase_rate > 0
    THEN 'Low Volume - Insufficient Data'
    ELSE 'Continue Analysis'
  END AS recommendation
FROM
  frequency_performance
ORDER BY
  frequency_bucket""",
            'parameters_schema': {},
            'default_parameters': {},
            'display_order': 3,
            'query_type': 'exploratory',
            'interpretation_notes': 'Look for "Potential Optimal Point" recommendation to identify where to set frequency caps'
        }
    ],
    'metrics': [
        {
            'metric_name': 'users_in_bucket',
            'display_name': 'Users in Bucket',
            'definition': 'Number of unique users who have been exposed to ads at this frequency level',
            'metric_type': 'metric',
            'display_order': 1
        },
        {
            'metric_name': 'impressions_in_bucket',
            'display_name': 'Impressions in Bucket',
            'definition': 'Total number of impressions delivered to users at this frequency level',
            'metric_type': 'metric',
            'display_order': 2
        },
        {
            'metric_name': 'reach_percentage',
            'display_name': 'Reach Percentage',
            'definition': 'Percentage of total campaign reach represented by users at this frequency level',
            'metric_type': 'metric',
            'display_order': 3
        },
        {
            'metric_name': 'purchase_rate',
            'display_name': 'Purchase Rate',
            'definition': 'Percentage of users at this frequency level who made a purchase',
            'metric_type': 'metric',
            'display_order': 4
        },
        {
            'metric_name': 'frequency_bucket',
            'display_name': 'Frequency Bucket',
            'definition': 'Grouping of users based on the number of times they have seen ads',
            'metric_type': 'dimension',
            'display_order': 5
        },
        {
            'metric_name': 'marginal_benefit',
            'display_name': 'Marginal Benefit',
            'definition': 'Incremental improvement in purchase rate compared to previous frequency level',
            'metric_type': 'metric',
            'display_order': 6
        },
        {
            'metric_name': 'cost_per_incremental_conversion',
            'display_name': 'Cost per Incremental Conversion',
            'definition': 'Number of additional impressions required to generate one additional conversion',
            'metric_type': 'metric',
            'display_order': 7
        },
        {
            'metric_name': 'wasted_impressions',
            'display_name': 'Wasted Impressions',
            'definition': 'Impressions delivered beyond the optimal frequency cap that could be reallocated',
            'metric_type': 'metric',
            'display_order': 8
        }
    ]
}

def main():
    """Main function to seed the guide"""
    try:
        logger.info("Starting to seed DSP Impression Frequency and Conversions guide...")
        
        # Create the guide using the formatter
        success = create_guide_from_dict(guide_data, update_existing=True)
        
        if success:
            logger.info("✅ Successfully created DSP Impression Frequency and Conversions guide!")
            logger.info(f"Guide ID: {guide_data['guide']['guide_id']}")
            logger.info(f"Sections: {len(guide_data['sections'])}")
            logger.info(f"Queries: {len(guide_data['queries'])}")
            logger.info(f"Metrics: {len(guide_data['metrics'])}")
        else:
            logger.error("Failed to create guide")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error creating guide: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()