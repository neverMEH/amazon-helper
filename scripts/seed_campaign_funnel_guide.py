#!/usr/bin/env python3
"""
Seed script for Campaign Performance by User Funnel Stages Build Guide
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

def create_campaign_funnel_guide():
    """Create the Campaign Performance by User Funnel Stages guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_campaign_funnel_performance',
            'name': 'Campaign Performance by User Funnel Stages',
            'category': 'Campaign Analytics',
            'short_description': 'Analyze the efficiency of Amazon ad campaigns across different purchase funnel stages (awareness, consideration, purchase, loyalty) to optimize investment.',
            'tags': ['funnel', 'campaign', 'performance', 'awareness', 'consideration', 'conversion', 'attribution', 'dsp', 'sponsored-ads'],
            'icon': 'TrendingUp',
            'difficulty_level': 'advanced',
            'estimated_time_minutes': 45,
            'prerequisites': [
                'Amazon FSI subscription',
                'Understanding of purchase funnel',
                'Knowledge of behavior segments',
                'AMC data structure familiarity'
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
                'content_markdown': """## 1.1 Summary

This guide helps you analyze campaign performance across different stages of the purchase funnel to understand where your advertising investments are most effective. By segmenting users into awareness, consideration, and purchase stages, you can optimize budget allocation and messaging strategies.

## 1.2 Purpose and Key Benefits

- **Funnel Stage Analysis**: Understand how campaigns perform at each stage of the customer journey
- **Budget Optimization**: Identify which funnel stages deliver the highest ROI
- **Audience Insights**: Discover where your customers are in their purchase journey
- **Strategic Planning**: Inform creative and targeting decisions based on funnel performance

## 1.3 Requirements

To use this guide effectively, you need:
- **Amazon FSI subscription** (required for behavior segment data)
- **Active DSP and/or Sponsored Ads campaigns** with tracked ASINs
- **ASIN lists** defining your brand and competitor products
- **Behavior segments** configured for awareness and consideration stages
- **AMC instance** with at least 30 days of campaign data

## 1.4 Visual Representation of Funnel Stages

```
┌─────────────────────────────────────────────┐
│             AWARENESS                        │
│  (Category-level interest segments)          │
│  ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼  │
├─────────────────────────────────────────────┤
│           CONSIDERATION                      │
│  (Sub-category interest segments)            │
│  ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼               │
├─────────────────────────────────────────────┤
│          BRAND VIEWERS                       │
│  (Viewed brand ASINs - 180d lookback)        │
│  ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼                          │
├─────────────────────────────────────────────┤
│        BRAND PURCHASERS                      │
│  (Purchased brand ASINs - 180d lookback)     │
│  ▼ ▼ ▼ ▼ ▼                                   │
└─────────────────────────────────────────────┘
        │
        ▼
   CONVERSION
```""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query_instructions',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Data Returned Overview

This guide provides queries that return campaign performance metrics segmented by funnel stage:

- **Traffic Metrics**: Impressions and unique user reach per funnel stage
- **Conversion Metrics**: Users who converted and total conversions
- **Sales Metrics**: Units sold and revenue generated
- **Efficiency Metrics**: Conversion rates and cost per acquisition

## 2.2 Tables Used

### Primary Tables
- **dsp_impressions**: DSP campaign impression data with user IDs and behavior segments
- **sponsored_ads_traffic**: Sponsored ads traffic data with user interactions
- **conversions_with_relevance**: Conversion events with attribution details
- **conversions_all**: All conversion events including non-attributed

### Supporting Tables
- **dsp_campaigns**: Campaign metadata and settings
- **audience_segment**: Behavior segment definitions (FSI required)

## 2.3 Important Notes

⚠️ **User Reach Duplication**: The same user may appear in multiple funnel stages if they match multiple segment criteria. This is intentional and helps understand the overlap between stages.

⚠️ **Data Availability**: Behavior segment data requires an active FSI subscription. Without FSI, only Brand Viewers and Brand Purchasers segments will be available.

⚠️ **Attribution Window**: Default attribution uses a 14-day post-click window. Adjust based on your product purchase cycle.""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'funnel_stage_definitions',
                'title': '3. Funnel Stage Definitions',
                'content_markdown': """## 3.1 Awareness Stage

**Definition**: Users showing category-level interest but not yet engaged with specific products

**Identification Method**: 
- Behavior segments for broad category interests
- Example: "Electronics Shoppers", "Home & Garden Enthusiasts"
- Typically the largest audience segment

**Typical Behavior**:
- Browse category pages
- Search for general category terms
- Low brand awareness

## 3.2 Consideration Stage

**Definition**: Users actively researching and comparing options within your sub-category

**Identification Method**:
- Behavior segments for specific sub-category interests
- Example: "Wireless Headphones Shoppers", "Coffee Maker Researchers"
- More qualified than awareness stage

**Typical Behavior**:
- Compare multiple products
- Read reviews and ratings
- Search for specific features

## 3.3 Brand Viewers

**Definition**: Users who have viewed your brand's product detail pages

**Identification Method**:
- Users with page views of specified brand ASINs
- 180-day lookback window (customizable)
- Direct indicator of brand interest

**Typical Behavior**:
- Actively viewed your products
- May have added to cart
- High purchase intent

## 3.4 Brand Purchasers

**Definition**: Existing customers who have purchased your brand's products

**Identification Method**:
- Users with confirmed purchases of brand ASINs
- 180-day lookback window (customizable)
- Highest value segment for retention

**Typical Behavior**:
- Previous purchasers
- Potential for repeat purchases
- Brand loyalty opportunities

## 3.5 Outside Funnel

**Definition**: Users reached by campaigns but not matching any defined funnel stage

**Identification Method**:
- Users not in any behavior segment
- No brand interaction history
- Catch-all category

**Typical Behavior**:
- Accidental or exploratory clicks
- Very broad browsing patterns
- Lowest conversion probability""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'example_results',
                'title': '4. Example Query Results',
                'content_markdown': """## 4.1 Sample Data Table

*This data is for instructional purposes only. Your results will differ.*

### Campaign Performance by Funnel Stage

| campaign_name | ad_product_type | user_type | impressions | user_reach | users_that_converted | conversions | conversion_rate | total_units_sold | total_product_sales |
|--------------|----------------|-----------|-------------|------------|---------------------|-------------|----------------|------------------|-------------------|
| Summer_DSP_2024 | DSP | AWARENESS | 412,589 | 26,571 | 216 | 287 | 0.813% | 342 | $8,550 |
| Summer_DSP_2024 | DSP | CONSIDERATION | 287,432 | 15,234 | 458 | 612 | 3.006% | 724 | $18,100 |
| Summer_DSP_2024 | DSP | BRAND VIEWERS | 178,923 | 8,456 | 892 | 1,245 | 10.551% | 1,489 | $37,225 |
| Summer_DSP_2024 | DSP | BRAND PURCHASERS | 98,234 | 3,287 | 724 | 1,087 | 22.027% | 1,298 | $32,450 |
| Summer_DSP_2024 | DSP | OUTSIDE FUNNEL | 523,478 | 42,189 | 87 | 98 | 0.206% | 112 | $2,800 |
| SA_Brand_Terms | Sponsored Ads | BRAND VIEWERS | 67,234 | 4,521 | 567 | 823 | 12.542% | 987 | $24,675 |
| SA_Brand_Terms | Sponsored Ads | BRAND PURCHASERS | 45,678 | 2,134 | 489 | 721 | 22.915% | 865 | $21,625 |
| SA_Category | Sponsored Ads | CONSIDERATION | 234,567 | 18,923 | 234 | 298 | 1.237% | 356 | $8,900 |
| SA_Category | Sponsored Ads | OUTSIDE FUNNEL | 456,789 | 34,567 | 45 | 52 | 0.130% | 62 | $1,550 |

## 4.2 Metrics Breakdown by Campaign and User Type

The sample data shows clear performance differences across funnel stages:

- **Conversion Rate Gradient**: Brand Purchasers (22%) > Brand Viewers (10-12%) > Consideration (1-3%) > Awareness (0.8%) > Outside Funnel (0.1-0.2%)
- **Volume vs. Efficiency Trade-off**: Upper funnel reaches more users but at lower conversion rates
- **Channel Differences**: DSP excels at upper funnel reach, Sponsored Ads performs better for lower funnel conversion""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'metrics_definitions',
                'title': '5. Metrics Definitions',
                'content_markdown': """## 5.1 Traffic Metrics

### impressions
**Definition**: Total number of ad impressions delivered
**Calculation**: COUNT of all impression events
**Use Case**: Measure campaign reach and frequency

### user_reach
**Definition**: Count of unique users who saw the ad
**Calculation**: COUNT(DISTINCT user_id)
**Use Case**: Understand actual audience size reached

### ad_product_type
**Definition**: Advertising channel identifier (DSP or Sponsored Ads)
**Values**: 'DSP', 'Sponsored Ads'
**Use Case**: Compare performance across advertising channels

## 5.2 Conversion Metrics

### users_that_converted
**Definition**: Unique users who made a purchase after ad exposure
**Calculation**: COUNT(DISTINCT user_id) WHERE purchase_flag = 1
**Use Case**: Measure unique converter count

### conversions
**Definition**: Total number of purchase events
**Calculation**: COUNT of conversion events
**Use Case**: Track total conversion volume

### conversion_rate
**Definition**: Percentage of reached users who converted
**Calculation**: (users_that_converted / user_reach) * 100
**Use Case**: Measure campaign effectiveness

## 5.3 Sales Metrics

### total_units_sold
**Definition**: Sum of all units purchased by converting users
**Calculation**: SUM(units_sold)
**Use Case**: Track product movement

### total_product_sales
**Definition**: Total revenue generated from conversions
**Calculation**: SUM(product_sales)
**Use Case**: Measure revenue impact

## 5.4 Cost Metrics

### total_cost
**Definition**: Total advertising spend for the campaign and segment
**Calculation**: SUM(cost) or calculated from eCPM
**Use Case**: Budget tracking and ROI calculation

### cost_per_acquisition (CPA)
**Definition**: Average cost to acquire one customer
**Calculation**: total_cost / users_that_converted
**Use Case**: Efficiency benchmarking

### return_on_ad_spend (ROAS)
**Definition**: Revenue generated per dollar spent
**Calculation**: total_product_sales / total_cost
**Use Case**: Campaign profitability assessment""",
                'display_order': 5,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'insights_interpretation',
                'title': '6. Insights and Data Interpretation',
                'content_markdown': """## 6.1 Customer Reach Distribution Analysis

### Understanding Your Funnel Shape

Analyze the distribution of users across funnel stages to identify opportunities:

**Healthy Funnel Pattern**:
- Awareness: 40-50% of reach
- Consideration: 25-35% of reach
- Brand Viewers: 15-20% of reach
- Brand Purchasers: 5-10% of reach

**Red Flags**:
- ✗ Majority in "Outside Funnel" → Poor audience targeting
- ✗ Minimal Consideration stage → Weak mid-funnel strategy
- ✗ Low Brand Viewers → Product visibility issues

## 6.2 Converter Distribution by Funnel Stage

### Where Are Your Converters Coming From?

**Example Analysis** (from sample data):
- Brand Purchasers contribute 35% of converters despite being only 5% of reach
- Brand Viewers contribute 40% of converters from 15% of reach
- Consideration stage contributes 20% of converters from 30% of reach
- Awareness contributes only 5% of converters from 50% of reach

**Key Insight**: Lower funnel segments are 10-20x more efficient at driving conversions

## 6.3 Effectiveness Assessment by Stage

### Conversion Rate Benchmarks

| Funnel Stage | Expected Conversion Rate | Action if Below |
|--------------|-------------------------|-----------------|
| Awareness | 0.5-1.5% | Improve audience targeting |
| Consideration | 2-5% | Enhance product messaging |
| Brand Viewers | 8-15% | Optimize product pages |
| Brand Purchasers | 20-35% | Focus on loyalty offers |
| Outside Funnel | <0.5% | Reduce or exclude segment |

## 6.4 Sample Recommendations

Based on the example data, here are actionable recommendations:

### 1. Budget Reallocation
**Current State**: High spend on Awareness with 0.813% conversion
**Recommendation**: Shift 20% of Awareness budget to Consideration (3% conversion rate)
**Expected Impact**: +15% total conversions with same budget

### 2. Audience Refinement
**Current State**: 42,189 users in "Outside Funnel" with 0.206% conversion
**Recommendation**: Implement negative targeting to exclude these users
**Expected Impact**: -30% wasted impressions, improved overall ROAS

### 3. Channel Optimization
**Current State**: DSP strong in upper funnel, SA strong in lower funnel
**Recommendation**: 
- Use DSP for Awareness and Consideration campaigns
- Focus Sponsored Ads on Brand Viewers and Purchasers
**Expected Impact**: +25% efficiency improvement

### 4. Creative Strategy
**By Funnel Stage**:
- **Awareness**: Educational content about category benefits
- **Consideration**: Comparison charts and feature highlights
- **Brand Viewers**: Urgency messaging and special offers
- **Brand Purchasers**: Loyalty rewards and cross-sell opportunities

## 6.5 Advanced Analysis Techniques

### Funnel Velocity Analysis
Track how quickly users move between stages:
```sql
-- Calculate average days between stages
SELECT 
    AVG(DATEDIFF(consideration_date, awareness_date)) as awareness_to_consideration,
    AVG(DATEDIFF(view_date, consideration_date)) as consideration_to_view,
    AVG(DATEDIFF(purchase_date, view_date)) as view_to_purchase
```

### Overlap Analysis
Understand user presence across multiple stages:
```sql
-- Find users in multiple funnel stages
SELECT 
    COUNT(DISTINCT CASE WHEN in_awareness AND in_consideration THEN user_id END) as both_upper,
    COUNT(DISTINCT CASE WHEN in_consideration AND brand_viewer THEN user_id END) as both_middle
```

### Cohort Performance
Track funnel performance over time:
```sql
-- Monthly cohort analysis
SELECT 
    DATE_TRUNC('month', first_impression_date) as cohort_month,
    user_type,
    conversion_rate
```""",
                'display_order': 6,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'implementation_guide',
                'title': '7. Query Implementation Guide',
                'content_markdown': """## 7.1 Step-by-Step Customization Instructions

### Step 1: Define Your Brand ASINs
```sql
-- UPDATE: Replace with your brand ASINs
AND asin IN ('B00XXXXX01', 'B00XXXXX02', 'B00XXXXX03')
```

### Step 2: Identify Behavior Segments
First, run the exploratory query to find available segments:
```sql
-- This will list all behavior segments in your AMC instance
SELECT DISTINCT 
    audience_segment_id,
    audience_segment_name
FROM dsp_impressions
WHERE audience_segment_name IS NOT NULL
```

### Step 3: Configure Funnel Stages
```sql
-- UPDATE: Map segments to funnel stages

-- Awareness segments (broad category interest)
AND audience_segment_id IN (123456, 234567, 345678)  -- e.g., "Electronics Shoppers"

-- Consideration segments (specific sub-category)
AND audience_segment_id IN (456789, 567890, 678901)  -- e.g., "Headphones Researchers"
```

### Step 4: Select Campaigns
```sql
-- UPDATE: Choose specific campaigns or use patterns

-- For DSP campaigns
AND campaign_id IN (789012, 890123, 901234)

-- For Sponsored Ads (use name patterns)
AND campaign_name LIKE '%Brand%'
OR campaign_name LIKE '%Category%'
```

### Step 5: Set Time Parameters
```sql
-- UPDATE: Adjust lookback windows

-- Analysis period (recommended 30-90 days)
AND impression_dt >= CURRENT_DATE - INTERVAL '30' DAY

-- Attribution window (typically 7-14 days)
AND conversion_dt <= impression_dt + INTERVAL '14' DAY

-- Brand interaction lookback (typically 180 days)
AND view_dt >= CURRENT_DATE - INTERVAL '180' DAY
```

## 7.2 Required vs Optional Updates

### Required Updates ⚠️
These must be customized for the query to work:

1. **Brand ASIN List** - Define your product catalog
2. **Campaign Selection** - Choose campaigns to analyze
3. **Date Range** - Set appropriate analysis period

### Optional Updates ✓
These have sensible defaults but can be customized:

1. **Behavior Segments** - Only if using upper funnel analysis
2. **Attribution Window** - Default 14 days works for most
3. **Lookback Period** - Default 180 days for brand interactions
4. **Minimum Thresholds** - Filter noise from results
5. **Cost Calculations** - eCPM values for ROI analysis

## 7.3 Performance Optimization Tips

### Query Performance
```sql
-- Add date partition filters first
WHERE impression_dt >= CURRENT_DATE - INTERVAL '30' DAY
  AND impression_dt < CURRENT_DATE

-- Use EXISTS instead of IN for large lists
WHERE EXISTS (
    SELECT 1 FROM campaign_list cl 
    WHERE cl.campaign_id = main.campaign_id
)

-- Materialize intermediate results for complex queries
WITH base_data AS (
    SELECT /*+ MATERIALIZE */ 
    ...
)
```

### Data Quality Checks
```sql
-- Verify segment coverage
SELECT 
    COUNT(DISTINCT user_id) as total_users,
    COUNT(DISTINCT CASE WHEN audience_segment_id IS NOT NULL THEN user_id END) as segmented_users,
    COUNT(DISTINCT CASE WHEN audience_segment_id IS NULL THEN user_id END) as unsegmented_users

-- Check for data gaps
SELECT 
    DATE(impression_dt) as date,
    COUNT(*) as impressions
GROUP BY 1
ORDER BY 1
```

### Incremental Implementation
Start simple and add complexity:

1. **Phase 1**: Run lower funnel only (Brand Viewers/Purchasers)
2. **Phase 2**: Add consideration stage with basic segments
3. **Phase 3**: Include awareness with full segmentation
4. **Phase 4**: Add cost data and ROI calculations
5. **Phase 5**: Implement attribution modeling options

## 7.4 Common Customization Scenarios

### Scenario 1: B2B Long Sales Cycle
```sql
-- Extend attribution window to 30+ days
AND conversion_dt <= impression_dt + INTERVAL '30' DAY

-- Extend brand interaction lookback to 365 days
AND view_dt >= CURRENT_DATE - INTERVAL '365' DAY
```

### Scenario 2: High-Frequency Purchase (CPG)
```sql
-- Shorten attribution to capture immediate impact
AND conversion_dt <= impression_dt + INTERVAL '3' DAY

-- Focus on recent purchasers (30-60 days)
AND purchase_dt >= CURRENT_DATE - INTERVAL '60' DAY
```

### Scenario 3: New Product Launch
```sql
-- Exclude historical purchasers to focus on new customers
AND user_id NOT IN (
    SELECT DISTINCT user_id 
    FROM conversions_all 
    WHERE purchase_dt < launch_date
)
```

### Scenario 4: Competitive Analysis
```sql
-- Include competitor ASINs in consideration
CASE 
    WHEN viewed_asin IN (competitor_list) THEN 'COMPETITOR_VIEWER'
    WHEN viewed_asin IN (brand_list) THEN 'BRAND_VIEWER'
END as viewer_type
```""",
                'display_order': 7,
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
                'title': 'Exploratory: Identify Segment Names and IDs',
                'description': 'Discover behavior segments reached by your DSP campaigns to use in funnel stage definitions.',
                'sql_query': """-- Exploratory Query: Identify Available Behavior Segments
-- Use this to discover segment IDs for awareness and consideration stages

WITH segment_summary AS (
    SELECT 
        audience_segment_id,
        audience_segment_name,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(DISTINCT campaign_id) as campaigns_using,
        COUNT(*) as total_impressions,
        MIN(impression_dt) as first_seen,
        MAX(impression_dt) as last_seen
    FROM dsp_impressions
    WHERE 
        audience_segment_id IS NOT NULL
        AND impression_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
        -- UPDATE: Add campaign filter if analyzing specific campaigns
        -- AND campaign_id IN (your_campaign_ids)
    GROUP BY 
        audience_segment_id,
        audience_segment_name
    HAVING COUNT(DISTINCT user_id) >= {{min_users}}  -- Filter out small segments
)
SELECT 
    audience_segment_id,
    audience_segment_name,
    unique_users,
    campaigns_using,
    total_impressions,
    ROUND(total_impressions::DOUBLE / unique_users::DOUBLE, 2) as avg_frequency,
    first_seen,
    last_seen,
    DATEDIFF('day', first_seen, last_seen) + 1 as active_days
FROM segment_summary
ORDER BY unique_users DESC
LIMIT 100""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for segment data'
                    },
                    'min_users': {
                        'type': 'integer',
                        'default': 100,
                        'description': 'Minimum unique users to include segment'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'min_users': 100
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'Look for segments with names indicating category-level interest (awareness) vs. sub-category interest (consideration). Note segment IDs for use in the main analysis query.'
            },
            {
                'guide_id': guide_id,
                'title': 'Exploratory: Identify Campaigns',
                'description': 'List campaigns with tracked ASINs to select for funnel analysis.',
                'sql_query': """-- Exploratory Query: Identify Campaigns with Tracked ASINs
-- Works for both DSP and Sponsored Ads campaigns

WITH dsp_campaigns AS (
    SELECT 
        'DSP' as ad_product_type,
        campaign_id,
        campaign_name,
        advertiser_id,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(*) as impressions,
        MIN(impression_dt) as start_date,
        MAX(impression_dt) as end_date,
        COUNT(DISTINCT creative_id) as creative_count
    FROM dsp_impressions
    WHERE 
        impression_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
        -- UPDATE: Add advertiser filter if needed
        -- AND advertiser_id = 'your_advertiser_id'
    GROUP BY 
        campaign_id,
        campaign_name,
        advertiser_id
),
sa_campaigns AS (
    SELECT 
        'Sponsored Ads' as ad_product_type,
        campaign_id,
        campaign_name,
        NULL as advertiser_id,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(*) as impressions,
        MIN(event_dt) as start_date,
        MAX(event_dt) as end_date,
        COUNT(DISTINCT asin) as creative_count
    FROM sponsored_ads_traffic
    WHERE 
        event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
        AND asin IS NOT NULL
        -- UPDATE: Add campaign type filter if needed
        -- AND campaign_type IN ('Sponsored Products', 'Sponsored Display')
    GROUP BY 
        campaign_id,
        campaign_name
)
SELECT * FROM (
    SELECT * FROM dsp_campaigns
    UNION ALL
    SELECT * FROM sa_campaigns
)
WHERE unique_users >= {{min_users}}
ORDER BY 
    ad_product_type,
    unique_users DESC
LIMIT 200""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for campaign data'
                    },
                    'min_users': {
                        'type': 'integer',
                        'default': 100,
                        'description': 'Minimum unique users to include campaign'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'min_users': 100
                },
                'display_order': 2,
                'query_type': 'exploratory',
                'interpretation_notes': 'Review campaigns with significant reach and activity. Note campaign IDs or name patterns for inclusion in the main analysis.'
            },
            {
                'guide_id': guide_id,
                'title': 'Main Analysis: DSP Campaigns (All Funnel Stages)',
                'description': 'Full funnel analysis for DSP campaigns including awareness and consideration stages (requires FSI).',
                'sql_query': """-- Main Analysis: DSP Campaign Performance by Funnel Stage
-- Analyzes upper and lower funnel performance for DSP campaigns

WITH brand_definition AS (
    -- UPDATE: Define your brand ASINs
    SELECT asin
    FROM (VALUES 
        ('B00XXXXX01'),
        ('B00XXXXX02'),
        ('B00XXXXX03')
    ) AS t(asin)
),
campaign_selection AS (
    -- UPDATE: Select your DSP campaigns
    SELECT campaign_id
    FROM (VALUES
        (123456),
        (234567),
        (345678)
    ) AS t(campaign_id)
),
awareness_segments AS (
    -- UPDATE: Define awareness-level behavior segments (broad category interest)
    SELECT segment_id
    FROM (VALUES
        (111111),  -- e.g., "Electronics Shoppers"
        (222222),  -- e.g., "Tech Enthusiasts"
        (333333)   -- e.g., "Online Shoppers"
    ) AS t(segment_id)
),
consideration_segments AS (
    -- UPDATE: Define consideration-level behavior segments (sub-category interest)
    SELECT segment_id
    FROM (VALUES
        (444444),  -- e.g., "Headphones Researchers"
        (555555),  -- e.g., "Audio Equipment Shoppers"
        (666666)   -- e.g., "Premium Audio Interest"
    ) AS t(segment_id)
),
analysis_period AS (
    SELECT 
        CURRENT_DATE - INTERVAL '{{analysis_days}}' DAY as start_date,
        CURRENT_DATE as end_date,
        {{attribution_window}} as attribution_days,
        {{lookback_window}} as lookback_days
),
-- Get brand viewers and purchasers
brand_interactions AS (
    SELECT 
        user_id,
        MAX(CASE WHEN view_flag = 1 THEN 1 ELSE 0 END) as is_viewer,
        MAX(CASE WHEN purchase_flag = 1 THEN 1 ELSE 0 END) as is_purchaser,
        MIN(CASE WHEN view_flag = 1 THEN event_dt END) as first_view_date,
        MIN(CASE WHEN purchase_flag = 1 THEN event_dt END) as first_purchase_date
    FROM conversions_all
    CROSS JOIN analysis_period ap
    WHERE 
        asin IN (SELECT asin FROM brand_definition)
        AND event_dt >= ap.start_date - INTERVAL '{{lookback_window}}' DAY
        AND event_dt < ap.end_date
    GROUP BY user_id
),
-- Classify users into funnel stages
user_classification AS (
    SELECT DISTINCT
        dsp.user_id,
        dsp.campaign_id,
        CASE 
            WHEN bi.is_purchaser = 1 THEN 'BRAND_PURCHASER'
            WHEN bi.is_viewer = 1 THEN 'BRAND_VIEWER'
            WHEN dsp.audience_segment_id IN (SELECT segment_id FROM consideration_segments) THEN 'CONSIDERATION'
            WHEN dsp.audience_segment_id IN (SELECT segment_id FROM awareness_segments) THEN 'AWARENESS'
            ELSE 'OUTSIDE_FUNNEL'
        END as user_type,
        MIN(dsp.impression_dt) as first_impression
    FROM dsp_impressions dsp
    CROSS JOIN analysis_period ap
    LEFT JOIN brand_interactions bi ON dsp.user_id = bi.user_id
    WHERE 
        dsp.campaign_id IN (SELECT campaign_id FROM campaign_selection)
        AND dsp.impression_dt >= ap.start_date
        AND dsp.impression_dt < ap.end_date
    GROUP BY 
        dsp.user_id,
        dsp.campaign_id,
        bi.is_purchaser,
        bi.is_viewer,
        dsp.audience_segment_id
),
-- Aggregate traffic metrics
traffic_metrics AS (
    SELECT 
        uc.campaign_id,
        uc.user_type,
        COUNT(DISTINCT uc.user_id) as user_reach,
        COUNT(DISTINCT di.impression_id) as impressions,
        SUM(di.cost) as total_cost
    FROM user_classification uc
    JOIN dsp_impressions di 
        ON uc.user_id = di.user_id 
        AND uc.campaign_id = di.campaign_id
    CROSS JOIN analysis_period ap
    WHERE di.impression_dt >= ap.start_date
        AND di.impression_dt < ap.end_date
    GROUP BY 
        uc.campaign_id,
        uc.user_type
),
-- Get conversion metrics
conversion_metrics AS (
    SELECT 
        uc.campaign_id,
        uc.user_type,
        COUNT(DISTINCT CASE WHEN c.purchase_flag = 1 THEN uc.user_id END) as users_that_converted,
        COUNT(CASE WHEN c.purchase_flag = 1 THEN 1 END) as conversions,
        SUM(CASE WHEN c.purchase_flag = 1 THEN c.units END) as total_units_sold,
        SUM(CASE WHEN c.purchase_flag = 1 THEN c.product_sales END) as total_product_sales
    FROM user_classification uc
    CROSS JOIN analysis_period ap
    LEFT JOIN conversions_with_relevance c
        ON uc.user_id = c.user_id
        AND c.event_dt >= uc.first_impression
        AND c.event_dt <= uc.first_impression + INTERVAL '{{attribution_window}}' DAY
        AND c.asin IN (SELECT asin FROM brand_definition)
    GROUP BY 
        uc.campaign_id,
        uc.user_type
)
-- Final output
SELECT 
    dc.campaign_name,
    'DSP' as ad_product_type,
    tm.user_type,
    tm.impressions,
    tm.user_reach,
    cm.users_that_converted,
    cm.conversions,
    ROUND(cm.users_that_converted::DOUBLE / NULLIF(tm.user_reach, 0)::DOUBLE * 100, 3) as conversion_rate,
    cm.total_units_sold,
    cm.total_product_sales,
    tm.total_cost,
    ROUND(tm.total_cost / NULLIF(cm.users_that_converted, 0), 2) as cpa,
    ROUND(cm.total_product_sales / NULLIF(tm.total_cost, 0), 2) as roas
FROM traffic_metrics tm
JOIN conversion_metrics cm 
    ON tm.campaign_id = cm.campaign_id 
    AND tm.user_type = cm.user_type
JOIN dsp_campaigns dc 
    ON tm.campaign_id = dc.campaign_id
WHERE tm.user_reach >= {{min_reach}}  -- Filter out very small segments
ORDER BY 
    dc.campaign_name,
    CASE tm.user_type
        WHEN 'AWARENESS' THEN 1
        WHEN 'CONSIDERATION' THEN 2
        WHEN 'BRAND_VIEWER' THEN 3
        WHEN 'BRAND_PURCHASER' THEN 4
        WHEN 'OUTSIDE_FUNNEL' THEN 5
    END""",
                'parameters_schema': {
                    'analysis_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to analyze'
                    },
                    'attribution_window': {
                        'type': 'integer',
                        'default': 14,
                        'description': 'Attribution window in days'
                    },
                    'lookback_window': {
                        'type': 'integer',
                        'default': 180,
                        'description': 'Lookback window for brand interactions'
                    },
                    'min_reach': {
                        'type': 'integer',
                        'default': 10,
                        'description': 'Minimum user reach to include in results'
                    }
                },
                'default_parameters': {
                    'analysis_days': 30,
                    'attribution_window': 14,
                    'lookback_window': 180,
                    'min_reach': 10
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Focus on conversion rate differences between funnel stages. High-performing stages indicate where your messaging resonates most. Consider reallocating budget from low-performing stages.'
            },
            {
                'guide_id': guide_id,
                'title': 'Main Analysis: DSP + Sponsored Ads (Lower Funnel)',
                'description': 'Lower funnel analysis for Brand Viewers and Brand Purchasers across DSP and Sponsored Ads.',
                'sql_query': """-- Main Analysis: Lower Funnel Performance (DSP + Sponsored Ads)
-- Analyzes Brand Viewers and Brand Purchasers only (no FSI required)

WITH brand_definition AS (
    -- UPDATE: Define your brand ASINs
    SELECT asin
    FROM (VALUES 
        ('B00XXXXX01'),
        ('B00XXXXX02'),
        ('B00XXXXX03')
    ) AS t(asin)
),
dsp_campaign_selection AS (
    -- UPDATE: Select your DSP campaign IDs (optional)
    SELECT campaign_id
    FROM (VALUES
        (123456),
        (234567),
        (345678)
    ) AS t(campaign_id)
),
sa_campaign_selection AS (
    -- UPDATE: Define Sponsored Ads campaign name patterns (optional)
    SELECT pattern
    FROM (VALUES
        ('%Brand%'),
        ('%Category%'),
        ('%Competitor%')
    ) AS t(pattern)
),
analysis_period AS (
    SELECT 
        CURRENT_DATE - INTERVAL '{{analysis_days}}' DAY as start_date,
        CURRENT_DATE as end_date,
        {{attribution_window}} as attribution_days,
        {{lookback_window}} as lookback_days
),
-- Get brand viewers and purchasers
brand_interactions AS (
    SELECT 
        user_id,
        MAX(CASE WHEN view_flag = 1 THEN 1 ELSE 0 END) as is_viewer,
        MAX(CASE WHEN purchase_flag = 1 THEN 1 ELSE 0 END) as is_purchaser,
        MIN(CASE WHEN view_flag = 1 THEN event_dt END) as first_view_date,
        MIN(CASE WHEN purchase_flag = 1 THEN event_dt END) as first_purchase_date
    FROM conversions_all
    CROSS JOIN analysis_period ap
    WHERE 
        asin IN (SELECT asin FROM brand_definition)
        AND event_dt >= ap.start_date - INTERVAL '{{lookback_window}}' DAY
        AND event_dt < ap.end_date
    GROUP BY user_id
),
-- DSP traffic and classification
dsp_traffic AS (
    SELECT 
        'DSP' as ad_product_type,
        di.campaign_id,
        dc.campaign_name,
        di.user_id,
        CASE 
            WHEN bi.is_purchaser = 1 THEN 'BRAND_PURCHASER'
            WHEN bi.is_viewer = 1 THEN 'BRAND_VIEWER'
            ELSE 'OUTSIDE_FUNNEL'
        END as user_type,
        MIN(di.impression_dt) as first_impression,
        COUNT(*) as impressions,
        SUM(di.cost) as cost
    FROM dsp_impressions di
    JOIN dsp_campaigns dc ON di.campaign_id = dc.campaign_id
    CROSS JOIN analysis_period ap
    LEFT JOIN brand_interactions bi ON di.user_id = bi.user_id
    WHERE 
        di.campaign_id IN (SELECT campaign_id FROM dsp_campaign_selection)
        AND di.impression_dt >= ap.start_date
        AND di.impression_dt < ap.end_date
    GROUP BY 
        di.campaign_id,
        dc.campaign_name,
        di.user_id,
        bi.is_purchaser,
        bi.is_viewer
),
-- Sponsored Ads traffic and classification
sa_traffic AS (
    SELECT 
        'Sponsored Ads' as ad_product_type,
        sat.campaign_id,
        sat.campaign_name,
        sat.user_id,
        CASE 
            WHEN bi.is_purchaser = 1 THEN 'BRAND_PURCHASER'
            WHEN bi.is_viewer = 1 THEN 'BRAND_VIEWER'
            ELSE 'OUTSIDE_FUNNEL'
        END as user_type,
        MIN(sat.event_dt) as first_impression,
        COUNT(*) as impressions,
        SUM(sat.cost) as cost
    FROM sponsored_ads_traffic sat
    CROSS JOIN analysis_period ap
    LEFT JOIN brand_interactions bi ON sat.user_id = bi.user_id
    WHERE 
        EXISTS (
            SELECT 1 FROM sa_campaign_selection scs 
            WHERE sat.campaign_name LIKE scs.pattern
        )
        AND sat.event_dt >= ap.start_date
        AND sat.event_dt < ap.end_date
    GROUP BY 
        sat.campaign_id,
        sat.campaign_name,
        sat.user_id,
        bi.is_purchaser,
        bi.is_viewer
),
-- Combine all traffic
all_traffic AS (
    SELECT * FROM dsp_traffic
    UNION ALL
    SELECT * FROM sa_traffic
),
-- Aggregate metrics by campaign and user type
traffic_summary AS (
    SELECT 
        ad_product_type,
        campaign_name,
        user_type,
        COUNT(DISTINCT user_id) as user_reach,
        SUM(impressions) as total_impressions,
        SUM(cost) as total_cost,
        MIN(first_impression) as campaign_start
    FROM all_traffic
    GROUP BY 
        ad_product_type,
        campaign_name,
        user_type
),
-- Get conversions
conversion_summary AS (
    SELECT 
        at.ad_product_type,
        at.campaign_name,
        at.user_type,
        COUNT(DISTINCT CASE WHEN c.purchase_flag = 1 THEN at.user_id END) as users_that_converted,
        COUNT(CASE WHEN c.purchase_flag = 1 THEN 1 END) as conversions,
        SUM(CASE WHEN c.purchase_flag = 1 THEN c.units END) as total_units_sold,
        SUM(CASE WHEN c.purchase_flag = 1 THEN c.product_sales END) as total_product_sales
    FROM all_traffic at
    CROSS JOIN analysis_period ap
    LEFT JOIN conversions_with_relevance c
        ON at.user_id = c.user_id
        AND c.event_dt >= at.first_impression
        AND c.event_dt <= at.first_impression + INTERVAL '{{attribution_window}}' DAY
        AND c.asin IN (SELECT asin FROM brand_definition)
    GROUP BY 
        at.ad_product_type,
        at.campaign_name,
        at.user_type
)
-- Final output
SELECT 
    ts.campaign_name,
    ts.ad_product_type,
    ts.user_type,
    ts.total_impressions as impressions,
    ts.user_reach,
    cs.users_that_converted,
    cs.conversions,
    ROUND(cs.users_that_converted::DOUBLE / NULLIF(ts.user_reach, 0)::DOUBLE * 100, 3) as conversion_rate,
    cs.total_units_sold,
    cs.total_product_sales,
    ts.total_cost,
    ROUND(ts.total_cost / NULLIF(cs.users_that_converted, 0), 2) as cpa,
    ROUND(cs.total_product_sales / NULLIF(ts.total_cost, 0), 2) as roas
FROM traffic_summary ts
JOIN conversion_summary cs 
    ON ts.ad_product_type = cs.ad_product_type
    AND ts.campaign_name = cs.campaign_name
    AND ts.user_type = cs.user_type
WHERE 
    ts.user_reach >= {{min_reach}}
    AND ts.user_type IN ('BRAND_VIEWER', 'BRAND_PURCHASER', 'OUTSIDE_FUNNEL')
ORDER BY 
    ts.campaign_name,
    ts.ad_product_type,
    CASE ts.user_type
        WHEN 'BRAND_VIEWER' THEN 1
        WHEN 'BRAND_PURCHASER' THEN 2
        WHEN 'OUTSIDE_FUNNEL' THEN 3
    END""",
                'parameters_schema': {
                    'analysis_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to analyze'
                    },
                    'attribution_window': {
                        'type': 'integer',
                        'default': 14,
                        'description': 'Attribution window in days'
                    },
                    'lookback_window': {
                        'type': 'integer',
                        'default': 180,
                        'description': 'Lookback window for brand interactions'
                    },
                    'min_reach': {
                        'type': 'integer',
                        'default': 10,
                        'description': 'Minimum user reach to include in results'
                    }
                },
                'default_parameters': {
                    'analysis_days': 30,
                    'attribution_window': 14,
                    'lookback_window': 180,
                    'min_reach': 10
                },
                'display_order': 4,
                'query_type': 'main_analysis',
                'interpretation_notes': 'This query works without FSI subscription. Compare Brand Viewers vs Brand Purchasers performance. High Brand Viewer conversion indicates strong product page experience. Low Brand Purchaser retention suggests opportunity for loyalty programs.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results for main analysis queries
                if query['query_type'] == 'main_analysis' and 'DSP Campaigns' in query['title']:
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample DSP Funnel Analysis Results',
                        'sample_data': {
                            'rows': [
                                {
                                    'campaign_name': 'Summer_DSP_2024',
                                    'ad_product_type': 'DSP',
                                    'user_type': 'AWARENESS',
                                    'impressions': 412589,
                                    'user_reach': 26571,
                                    'users_that_converted': 216,
                                    'conversions': 287,
                                    'conversion_rate': 0.813,
                                    'total_units_sold': 342,
                                    'total_product_sales': 8550.00,
                                    'total_cost': 1237.77,
                                    'cpa': 5.73,
                                    'roas': 6.91
                                },
                                {
                                    'campaign_name': 'Summer_DSP_2024',
                                    'ad_product_type': 'DSP',
                                    'user_type': 'CONSIDERATION',
                                    'impressions': 287432,
                                    'user_reach': 15234,
                                    'users_that_converted': 458,
                                    'conversions': 612,
                                    'conversion_rate': 3.006,
                                    'total_units_sold': 724,
                                    'total_product_sales': 18100.00,
                                    'total_cost': 862.30,
                                    'cpa': 1.88,
                                    'roas': 20.99
                                },
                                {
                                    'campaign_name': 'Summer_DSP_2024',
                                    'ad_product_type': 'DSP',
                                    'user_type': 'BRAND_VIEWER',
                                    'impressions': 178923,
                                    'user_reach': 8456,
                                    'users_that_converted': 892,
                                    'conversions': 1245,
                                    'conversion_rate': 10.551,
                                    'total_units_sold': 1489,
                                    'total_product_sales': 37225.00,
                                    'total_cost': 536.77,
                                    'cpa': 0.60,
                                    'roas': 69.34
                                },
                                {
                                    'campaign_name': 'Summer_DSP_2024',
                                    'ad_product_type': 'DSP',
                                    'user_type': 'BRAND_PURCHASER',
                                    'impressions': 98234,
                                    'user_reach': 3287,
                                    'users_that_converted': 724,
                                    'conversions': 1087,
                                    'conversion_rate': 22.027,
                                    'total_units_sold': 1298,
                                    'total_product_sales': 32450.00,
                                    'total_cost': 294.70,
                                    'cpa': 0.41,
                                    'roas': 110.13
                                },
                                {
                                    'campaign_name': 'Summer_DSP_2024',
                                    'ad_product_type': 'DSP',
                                    'user_type': 'OUTSIDE_FUNNEL',
                                    'impressions': 523478,
                                    'user_reach': 42189,
                                    'users_that_converted': 87,
                                    'conversions': 98,
                                    'conversion_rate': 0.206,
                                    'total_units_sold': 112,
                                    'total_product_sales': 2800.00,
                                    'total_cost': 1570.43,
                                    'cpa': 18.06,
                                    'roas': 1.78
                                }
                            ]
                        },
                        'interpretation_markdown': """**Funnel Performance Analysis:**

**Conversion Rate Progression:**
- Outside Funnel: 0.206% (baseline)
- Awareness: 0.813% (4x baseline)
- Consideration: 3.006% (15x baseline)
- Brand Viewers: 10.551% (51x baseline)
- Brand Purchasers: 22.027% (107x baseline)

**Cost Efficiency (CPA):**
- Brand Purchasers: $0.41 (most efficient)
- Brand Viewers: $0.60
- Consideration: $1.88
- Awareness: $5.73
- Outside Funnel: $18.06 (least efficient)

**Key Insights:**
1. **Strong Funnel Progression**: Clear conversion rate improvement at each stage
2. **Lower Funnel Excellence**: ROAS of 69-110x for Brand Viewers/Purchasers
3. **Upper Funnel Opportunity**: Awareness stage shows positive ROAS (6.91x) but room for improvement
4. **Outside Funnel Waste**: 42% of reach is outside funnel with minimal return

**Recommendations:**
- Reduce Outside Funnel exposure through better targeting
- Increase investment in Consideration stage (20.99x ROAS)
- Maintain strong lower funnel presence
- Test awareness messaging to improve 0.813% conversion rate""",
                        'insights': [
                            'Lower funnel segments deliver 69-110x ROAS vs 1.78x for Outside Funnel',
                            'Consideration stage shows best balance of reach (15K users) and efficiency (3% conversion)',
                            '42% of reach is Outside Funnel - opportunity to improve targeting',
                            'Brand Purchasers convert at 22% - focus on retention and loyalty',
                            'Sequential improvement from Awareness to Purchase validates funnel strategy'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created DSP example results")
                
                elif query['query_type'] == 'main_analysis' and 'Lower Funnel' in query['title']:
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Lower Funnel Analysis Results',
                        'sample_data': {
                            'rows': [
                                {
                                    'campaign_name': 'SA_Brand_Terms',
                                    'ad_product_type': 'Sponsored Ads',
                                    'user_type': 'BRAND_VIEWER',
                                    'impressions': 67234,
                                    'user_reach': 4521,
                                    'users_that_converted': 567,
                                    'conversions': 823,
                                    'conversion_rate': 12.542,
                                    'total_units_sold': 987,
                                    'total_product_sales': 24675.00,
                                    'total_cost': 403.40,
                                    'cpa': 0.71,
                                    'roas': 61.16
                                },
                                {
                                    'campaign_name': 'SA_Brand_Terms',
                                    'ad_product_type': 'Sponsored Ads',
                                    'user_type': 'BRAND_PURCHASER',
                                    'impressions': 45678,
                                    'user_reach': 2134,
                                    'users_that_converted': 489,
                                    'conversions': 721,
                                    'conversion_rate': 22.915,
                                    'total_units_sold': 865,
                                    'total_product_sales': 21625.00,
                                    'total_cost': 274.07,
                                    'cpa': 0.56,
                                    'roas': 78.92
                                },
                                {
                                    'campaign_name': 'SA_Category',
                                    'ad_product_type': 'Sponsored Ads',
                                    'user_type': 'BRAND_VIEWER',
                                    'impressions': 123456,
                                    'user_reach': 8923,
                                    'users_that_converted': 234,
                                    'conversions': 298,
                                    'conversion_rate': 2.623,
                                    'total_units_sold': 356,
                                    'total_product_sales': 8900.00,
                                    'total_cost': 740.74,
                                    'cpa': 3.17,
                                    'roas': 12.02
                                },
                                {
                                    'campaign_name': 'SA_Category',
                                    'ad_product_type': 'Sponsored Ads',
                                    'user_type': 'OUTSIDE_FUNNEL',
                                    'impressions': 456789,
                                    'user_reach': 34567,
                                    'users_that_converted': 45,
                                    'conversions': 52,
                                    'conversion_rate': 0.130,
                                    'total_units_sold': 62,
                                    'total_product_sales': 1550.00,
                                    'total_cost': 2740.73,
                                    'cpa': 60.90,
                                    'roas': 0.57
                                }
                            ]
                        },
                        'interpretation_markdown': """**Lower Funnel Performance Comparison:**

**Sponsored Ads Performance by Campaign Type:**

**Brand Terms Campaigns:**
- Brand Viewers: 12.54% conversion, $0.71 CPA, 61x ROAS
- Brand Purchasers: 22.92% conversion, $0.56 CPA, 79x ROAS
- Highly efficient for capturing existing demand

**Category Campaigns:**
- Brand Viewers: 2.62% conversion, $3.17 CPA, 12x ROAS
- Outside Funnel: 0.13% conversion, $60.90 CPA, 0.57x ROAS
- Less efficient but important for new customer acquisition

**Key Findings:**
1. **Brand Terms Excellence**: 61-79x ROAS for users with brand affinity
2. **Category Challenge**: 79% of Category campaign reach is Outside Funnel
3. **CPA Variance**: $0.56-0.71 for brand terms vs $3.17-60.90 for category
4. **Conversion Gradient**: Clear 100x difference between Brand Purchasers (23%) and Outside Funnel (0.13%)

**Strategic Recommendations:**
- Maximize brand terms budget given exceptional ROAS
- Refine category targeting to reduce Outside Funnel exposure
- Consider separate strategies for acquisition vs retention
- Test competitor conquesting for Brand Viewers segment""",
                        'insights': [
                            'Brand term campaigns deliver 61-79x ROAS vs 0.57x for category Outside Funnel',
                            'Brand Purchasers convert at 23% - strongest segment across all campaigns',
                            'Category campaigns waste 79% of budget on Outside Funnel users',
                            'CPA ranges from $0.56 (brand purchasers) to $60.90 (outside funnel)',
                            'Sponsored Ads excels at lower funnel but struggles with broad targeting'
                        ],
                        'display_order': 2
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created Lower Funnel example results")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'ad_product_type',
                'display_name': 'Ad Product Type',
                'definition': 'Advertising channel identifier - either DSP (Display) or Sponsored Ads (Search/Shopping)',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'impressions',
                'display_name': 'Impressions',
                'definition': 'Total number of times ads were displayed to users',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_reach',
                'display_name': 'User Reach',
                'definition': 'Count of unique users who were exposed to the campaign ads',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_type',
                'display_name': 'User Type / Funnel Stage',
                'definition': 'Classification of users into funnel stages: AWARENESS, CONSIDERATION, BRAND_VIEWER, BRAND_PURCHASER, or OUTSIDE_FUNNEL',
                'metric_type': 'dimension',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'users_that_converted',
                'display_name': 'Users That Converted',
                'definition': 'Number of unique users who made a purchase after ad exposure within the attribution window',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversions',
                'display_name': 'Conversions',
                'definition': 'Total number of purchase events attributed to the campaign',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate',
                'display_name': 'Conversion Rate %',
                'definition': 'Percentage of reached users who made a purchase (users_that_converted / user_reach * 100)',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_units_sold',
                'display_name': 'Total Units Sold',
                'definition': 'Sum of all product units purchased by converting users',
                'metric_type': 'metric',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_product_sales',
                'display_name': 'Total Product Sales',
                'definition': 'Total revenue generated from attributed conversions in currency',
                'metric_type': 'metric',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_cost',
                'display_name': 'Total Cost',
                'definition': 'Total advertising spend for the campaign and segment',
                'metric_type': 'metric',
                'display_order': 10
            },
            {
                'guide_id': guide_id,
                'metric_name': 'cpa',
                'display_name': 'Cost Per Acquisition (CPA)',
                'definition': 'Average cost to acquire one converting customer (total_cost / users_that_converted)',
                'metric_type': 'metric',
                'display_order': 11
            },
            {
                'guide_id': guide_id,
                'metric_name': 'roas',
                'display_name': 'Return on Ad Spend (ROAS)',
                'definition': 'Revenue generated per dollar of ad spend (total_product_sales / total_cost)',
                'metric_type': 'metric',
                'display_order': 12
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created Campaign Funnel Performance guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_campaign_funnel_guide()
    sys.exit(0 if success else 1)