#!/usr/bin/env python
"""
Seed script for First-Party vs Unknown Customer Performance Analysis Build Guide
Creates a comprehensive guide for analyzing customer segment performance
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

def seed_first_party_performance_guide():
    """Seed the First-Party vs Unknown Customer Performance Analysis guide"""
    
    # 1. Create the main guide
    guide_data = {
        "guide_id": "guide_first_party_performance",
        "name": "First-Party vs Unknown Customer Performance Analysis",
        "category": "Customer Analytics",
        "difficulty_level": "advanced",
        "estimated_time_minutes": 60,
        "short_description": "Analyze how your Amazon Ads campaigns perform across your known first-party customers versus unknown audiences to optimize targeting and budget allocation",
        "prerequisites": [
            "First-party audience data uploaded to AMC",
            "Active Amazon Ads campaigns (DSP, Sponsored Products, Display, or Brands)",
            "Understanding of first-party data usage in AMC",
            "At least 30 days of campaign data"
        ],
        "tags": [
            "First-party data",
            "Customer segmentation",
            "Performance comparison",
            "Audience analysis",
            "Cross-channel analysis"
        ],
        "icon": "UserGroup",
        "is_published": True,
        "display_order": 7
    }
    
    result = supabase.table("build_guides").upsert(guide_data).execute()
    guide_record = result.data[0] if result.data else None
    if not guide_record:
        raise Exception("Failed to create guide")
    
    guide_uuid = guide_record["id"]  # Get the UUID
    guide_id = guide_data["guide_id"]  # Keep the string ID for reference
    print(f"✅ Created guide: {guide_id}")
    
    # 2. Create guide sections
    sections = [
        {
            "guide_id": guide_uuid,
            "section_id": "introduction",
            "title": "Introduction",
            "display_order": 1,
            "content_markdown": """## Purpose

This analysis helps you understand the reach and performance of your Amazon Ads campaigns in the context of your known first-party (1P) customer set. You can analyze how your media delivery is distributed across 1P (known) and other (unknown) audiences, as well as compare performance between the two groups.

In this context:
- **Known/1P Customers**: Those who have transacted via your retail site or with whom you have a pre-existing customer relationship
- **Unknown Customers**: Everyone outside of your 1P audience - potential new customers

## What You'll Learn

- Distribution of ad spend between known and unknown customers
- Purchase rates comparison across customer segments
- Reach percentage of your known customer base per ad product
- ROI differences between customer acquisition and retention
- Optimal channel mix for different audience strategies

## Business Applications

| Application | Description |
|------------|-------------|
| **Customer Acquisition Strategy** | Assess how well campaigns reach net-new customers |
| **Retention Marketing** | Evaluate effectiveness in reaching existing customers |
| **Budget Optimization** | Allocate spend based on performance by customer type |
| **Channel Strategy** | Identify which ad products work best for each audience |
| **Growth Analysis** | Measure expansion beyond your existing customer base |

## Requirements

### Essential Requirements
- First-party audience table uploaded to AMC
- Active Amazon Ads campaigns during analysis period
- User-level match between 1P data and Amazon user IDs

### Supported Ad Products
- Amazon DSP (Display and Streaming TV)
- Sponsored Products
- Sponsored Display
- Sponsored Brands

**Note**: You don't need campaigns in all channels - the query works with any combination."""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "data_query_instructions",
            "title": "Data Query Instructions",
            "display_order": 2,
            "content_markdown": """## Data Returned

The query returns comprehensive delivery and performance metrics segmented by:
- Customer set (known vs unknown)
- Ad product type (DSP, SP, SD, SB)
- Key performance indicators per segment

## Tables Used

| Table | Purpose | Type |
|-------|---------|------|
| `first_party_audience_table` | Your uploaded 1P customer data | Advertiser uploaded |
| `dsp_impressions` | DSP campaign impression data | AMC system table |
| `sponsored_ads_traffic` | Sponsored ads traffic events | AMC system table |
| `amazon_attributed_events_by_traffic_time` | Conversion events with attribution | AMC system table |

## First-Party Data Integration

Your 1P tables appear under "Advertiser uploaded" in AMC's Schema explorer. Common 1P data sources include:

- **CRM customer lists**: Export from Salesforce, HubSpot, or similar
- **Email subscriber databases**: Marketing automation platforms
- **Loyalty program members**: Rewards program participants
- **Website visitor data**: Pixel-based audience segments
- **Offline transaction records**: In-store purchase history

### Upload Format Requirements

```sql
-- Your 1P table should have this structure:
CREATE TABLE your_first_party_table (
    user_id VARCHAR,           -- Hashed identifier
    segment VARCHAR,           -- Optional: customer segment
    lifetime_value DECIMAL,    -- Optional: CLV
    first_purchase_date DATE   -- Optional: acquisition date
);
```

## Query Parameters

The main query accepts these customization points:

1. **First-party table name**: Replace `<<first_party_audience_table>>` with your actual table
2. **Analysis period**: Adjust `startDate` and `endDate` parameters
3. **Campaign filters**: Add specific campaign IDs or names
4. **ASIN filters**: Focus on specific products
5. **Cost data inclusion**: Toggle spend metrics on/off"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "data_interpretation",
            "title": "Data Interpretation",
            "display_order": 3,
            "content_markdown": """## Understanding Your Results

The query output provides a comprehensive view of how your advertising reaches and performs across known versus unknown customer segments.

## Key Metrics Explained

| Metric | Definition | Strategic Use |
|--------|------------|---------------|
| **audience_size** | Total known customers in your 1P data | Benchmark for reach potential |
| **unique_reach** | Unique users reached by campaigns | Actual audience touched |
| **audience_reach** | % of known customers reached | Penetration rate metric |
| **spend** | Total ad spend per segment | Budget allocation insight |
| **percent_of_spend** | Share of total spend | Resource distribution |
| **user_purchase_rate** | Conversion rate by segment | Performance comparison |

## Performance Benchmarks

### Typical Patterns by Strategy Type

| Strategy | Known Customer Spend | Unknown Customer Spend | Focus |
|----------|---------------------|------------------------|-------|
| **Growth-Focused** | 5-20% | 80-95% | New customer acquisition |
| **Balanced** | 30-50% | 50-70% | Growth + retention |
| **Retention-Focused** | 50-70% | 30-50% | Customer lifetime value |

## Interpreting Purchase Rates

**Higher rates for known customers (typical):**
- Indicates brand affinity working
- Suggests retention messaging effective
- Validates 1P data quality

**Higher rates for unknown customers (less common):**
- May indicate saturated known audience
- Could suggest acquisition offers more compelling
- Potentially indicates data match issues

## Channel Performance Patterns

### Amazon DSP
- **Strengths**: Broad reach, programmatic efficiency
- **Known customers**: Good for awareness, cross-sell
- **Unknown customers**: Excellent for prospecting

### Sponsored Products
- **Strengths**: High purchase intent, search-based
- **Known customers**: Often highest conversion rates
- **Unknown customers**: Strong for category conquesting

### Sponsored Display
- **Strengths**: Retargeting capabilities
- **Known customers**: Good for consideration phase
- **Unknown customers**: Effective for competitor targeting

### Sponsored Brands
- **Strengths**: Brand awareness, top-of-funnel
- **Known customers**: Reinforces brand loyalty
- **Unknown customers**: Introduces brand to new audiences"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "implementation_strategy",
            "title": "Implementation Strategy",
            "display_order": 4,
            "content_markdown": """## Analysis Workflow

### Step 1: Upload and Validate 1P Data
```sql
-- Verify your 1P data upload
SELECT COUNT(DISTINCT user_id) as total_customers
FROM your_first_party_table;
```

### Step 2: Run Exploratory Query
Identify which campaigns to include by checking for ASIN conversions and sufficient volume.

### Step 3: Execute Main Analysis
Run the comprehensive query with your specific parameters and date range.

### Step 4: Segment Deep Dive
Analyze specific channels or campaigns that show interesting patterns.

### Step 5: Implement Optimizations
Apply insights to campaign structure, targeting, and budgets.

## Customer Strategy Framework

### Acquisition-First Strategy (>80% unknown spend)

**Characteristics:**
- Primary goal: Market expansion
- Focus on broad targeting
- Emphasis on new customer offers

**Optimization tactics:**
```
1. Increase DSP prospecting budgets
2. Use lookalike audiences from best customers
3. Implement new customer welcome series
4. Track 90-day LTV of acquired customers
```

### Balanced Strategy (50-50 split)

**Characteristics:**
- Dual focus on growth and retention
- Separate campaign structures
- Different messaging strategies

**Optimization tactics:**
```
1. Create dedicated retention campaigns
2. Use negative targeting to separate audiences
3. A/B test offers: new vs returning
4. Monitor incremental lift per segment
```

### Retention-First Strategy (>50% known spend)

**Characteristics:**
- Focus on customer lifetime value
- Emphasis on loyalty and repeat purchase
- Precision targeting using 1P data

**Optimization tactics:**
```
1. Increase frequency caps for known customers
2. Deploy VIP customer segments
3. Focus on cross-sell/upsell messaging
4. Implement win-back campaigns for lapsed
```

## Budget Allocation Framework

### Calculate Optimal Spend Distribution

```python
# Pseudo-code for optimization
def calculate_optimal_allocation(current_data):
    known_roi = known_revenue / known_spend
    unknown_roi = unknown_revenue / unknown_spend
    
    if growth_priority > 0.7:
        target_unknown_percent = 0.8
    elif retention_priority > 0.7:
        target_known_percent = 0.6
    else:
        # Balance based on ROI
        target_known_percent = known_roi / (known_roi + unknown_roi)
    
    return recommended_allocation
```

## Testing and Iteration

### Month 1: Baseline
- Run initial analysis
- Document current performance
- Identify opportunity areas

### Month 2: Test
- Implement 20% budget shift
- A/B test messaging strategies
- Monitor daily performance

### Month 3: Scale
- Roll out successful changes
- Expand to additional channels
- Refine audience segments"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "advanced_analysis",
            "title": "Advanced Analysis",
            "display_order": 5,
            "content_markdown": """## Conversion Path Analysis

### Multi-Touch Attribution by Segment

Combine this analysis with path-to-conversion queries to understand:

```sql
-- Example: Touch points by customer type
SELECT 
    CASE 
        WHEN user_id IN (SELECT user_id FROM first_party_table) 
        THEN 'known' 
        ELSE 'unknown' 
    END as customer_type,
    COUNT(DISTINCT touch_point) as avg_touches,
    STRING_AGG(DISTINCT ad_product, ' > ') as typical_path
FROM conversion_paths
GROUP BY customer_type;
```

### Typical Journey Differences

| Customer Type | Average Touches | Common Path | Time to Convert |
|--------------|-----------------|-------------|-----------------|
| **Known** | 3-5 | DSP > SP > Purchase | 7-14 days |
| **Unknown** | 5-8 | DSP > SD > SP > SB > Purchase | 14-30 days |

## Lifetime Value Considerations

### Known Customer Economics
- **Acquisition cost**: $0 (already acquired)
- **Retention cost**: $5-15 per customer
- **Repeat purchase rate**: 40-60%
- **Average order value**: 20-30% higher

### Unknown Customer Economics
- **Acquisition cost**: $20-50 per customer
- **First purchase value**: Variable
- **Repeat purchase rate**: 15-25%
- **LTV development**: 12-18 months

### ROI Calculation Framework

```python
# Calculate true ROI including LTV
def calculate_segment_roi(segment_data, time_horizon_days=365):
    if segment == 'known':
        # Include repeat purchase probability
        projected_value = immediate_revenue * (1 + repeat_rate * 2.5)
    else:
        # Include future value of new customer
        projected_value = immediate_revenue + (avg_ltv * 0.7)
    
    true_roi = (projected_value - ad_spend) / ad_spend
    return true_roi
```

## Cross-Channel Synergies

### Optimal Channel Mix by Objective

| Objective | DSP | SP | SD | SB | Rationale |
|-----------|-----|----|----|----|-----------| 
| **Acquire New** | 40% | 30% | 20% | 10% | Broad reach + high intent |
| **Retain Existing** | 20% | 40% | 30% | 10% | Purchase intent + retargeting |
| **Balanced Growth** | 30% | 35% | 25% | 10% | Even distribution |

## Competitive Intelligence

### Using Unknown Customer Data

Unknown customer performance can reveal:
- Market share opportunities
- Competitor customer acquisition
- Category growth potential
- Brand switching behaviors

### Competitive Benchmarking

```sql
-- Compare your unknown reach to category
SELECT 
    your_unknown_reach / category_total_shoppers as market_penetration,
    your_unknown_conversions / category_conversions as conversion_share
FROM market_analysis;
```

## Seasonal Adjustments

### Peak Period Strategy

**Q4/Holiday:**
- Increase unknown % for gift-givers
- Higher budgets on acquisition
- Broader targeting parameters

**Prime Day:**
- Focus on known customers
- Exclusive member offers
- Higher frequency messaging

**Off-Peak:**
- Test new audiences
- Optimize for efficiency
- Build 1P data pool"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "troubleshooting",
            "title": "Troubleshooting Guide",
            "display_order": 6,
            "content_markdown": """## Common Issues and Solutions

### Issue: No Known Customers Showing in Results

**Potential Causes:**
1. 1P table not properly joined
2. User ID mismatch/hashing issues
3. Time period misalignment

**Solutions:**
```sql
-- Check 1P table exists and has data
SELECT COUNT(*) FROM your_first_party_table;

-- Verify user_id format matches
SELECT 
    SUBSTRING(user_id, 1, 10) as sample_id,
    COUNT(*) as count
FROM your_first_party_table
GROUP BY 1
LIMIT 5;
```

### Issue: Unusually Low Match Rates

**Expected match rates:** 40-60% typical, 60-80% excellent

**Improvement strategies:**
1. Include more identifiers (email, phone)
2. Expand time window for matching
3. Check data freshness
4. Verify hashing methodology

### Issue: Zero Spend for Known Customers

**Likely scenarios:**
- No targeting of 1P audiences
- Exclusion lists preventing delivery
- Budget constraints limiting reach

**Quick fixes:**
```sql
-- Check if campaigns are reaching 1P at all
SELECT COUNT(DISTINCT user_id)
FROM dsp_impressions
WHERE user_id IN (SELECT user_id FROM first_party_table)
  AND impression_dt >= CURRENT_DATE - 7;
```

### Issue: Purchase Rates Seem Wrong

**Validation checks:**

```sql
-- Verify conversion tracking
SELECT 
    COUNT(DISTINCT order_id) as orders,
    COUNT(DISTINCT user_id) as purchasers,
    SUM(revenue) as total_revenue
FROM amazon_attributed_events_by_traffic_time
WHERE purchase_dt >= CURRENT_DATE - 30;
```

**Common calculation errors:**
- Wrong attribution window
- Missing conversion types
- Duplicate order counting

## Performance Optimization

### Query Running Slowly

**Optimization tips:**
1. Reduce date range to last 30-60 days initially
2. Filter to specific campaigns/ASINs
3. Use sampling for large datasets
4. Pre-aggregate 1P data

### Memory Issues

```sql
-- Use incremental approach
CREATE TEMPORARY TABLE known_users_sample AS
SELECT user_id 
FROM first_party_table 
SAMPLE (10000 ROWS);
```

## Data Quality Checks

### Validate 1P Data Quality

```sql
-- Check for duplicates
SELECT user_id, COUNT(*) as occurrences
FROM first_party_table
GROUP BY user_id
HAVING COUNT(*) > 1;

-- Check for nulls
SELECT 
    COUNT(*) as total_records,
    COUNT(user_id) as valid_ids,
    COUNT(*) - COUNT(user_id) as null_ids
FROM first_party_table;
```

### Verify Campaign Data

```sql
-- Ensure campaigns have sufficient data
SELECT 
    campaign_id,
    COUNT(DISTINCT user_id) as users,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks
FROM sponsored_ads_traffic
WHERE traffic_dt >= CURRENT_DATE - 30
GROUP BY campaign_id
HAVING impressions > 1000;
```"""
        }
    ]
    
    for section in sections:
        result = supabase.table("build_guide_sections").upsert(section).execute()
    print(f"✅ Created {len(sections)} sections")
    
    # 3. Create queries
    queries = [
        {
            "guide_id": guide_uuid,
            "query_type": "exploratory",
            "title": "Identify Campaigns with ASIN Conversions",
            "description": "Find campaigns that have driven conversions for analysis inclusion",
            "sql_query": """-- Identify campaigns with ASIN conversions for analysis
WITH campaign_performance AS (
    SELECT DISTINCT
        campaign_id,
        campaign_name,
        ad_product_type,
        COUNT(DISTINCT user_id) as reach,
        COUNT(DISTINCT order_id) as conversions
    FROM (
        -- DSP Campaigns
        SELECT 
            dsp.campaign_id,
            dsp.campaign as campaign_name,
            'amazon_dsp' as ad_product_type,
            dsp.user_id,
            attr.order_id
        FROM dsp_impressions dsp
        LEFT JOIN amazon_attributed_events_by_traffic_time attr
            ON dsp.user_id = attr.user_id
            AND attr.traffic_dt BETWEEN dsp.impression_dt AND dsp.impression_dt + INTERVAL '14' DAY
        WHERE dsp.impression_dt >= CURRENT_DATE - {{lookback_days}}
            AND attr.purchase_dt IS NOT NULL
        
        UNION ALL
        
        -- Sponsored Ads Campaigns
        SELECT 
            sp.campaign_id,
            sp.campaign_name,
            sp.ad_product_type,
            sp.user_id,
            attr.order_id
        FROM sponsored_ads_traffic sp
        LEFT JOIN amazon_attributed_events_by_traffic_time attr
            ON sp.user_id = attr.user_id
            AND attr.traffic_dt BETWEEN sp.traffic_dt AND sp.traffic_dt + INTERVAL '14' DAY
        WHERE sp.traffic_dt >= CURRENT_DATE - {{lookback_days}}
            AND attr.purchase_dt IS NOT NULL
    )
    GROUP BY 1, 2, 3
)
SELECT 
    ad_product_type,
    campaign_id,
    campaign_name,
    reach,
    conversions,
    ROUND(CAST(conversions AS DECIMAL) / NULLIF(reach, 0) * 100, 2) as conversion_rate
FROM campaign_performance
WHERE conversions > 0
ORDER BY ad_product_type, conversions DESC;""",
            "parameters_schema": {
                "lookback_days": {
                    "type": "integer",
                    "default": 30,
                    "description": "Number of days to look back"
                }
            },
            "display_order": 1
        },
        {
            "guide_id": guide_uuid,
            "query_type": "main_analysis",
            "title": "First-Party vs Unknown Customer Performance Analysis",
            "description": "Complete performance comparison between known and unknown customers across all ad products",
            "sql_query": """-- First-Party vs Unknown Customer Performance Analysis
-- Customize these 5 points:
-- 1. Replace <<first_party_audience_table>> with your actual 1P table name
-- 2. Update startDate and endDate for your analysis period
-- 3. Add campaign_id filters if analyzing specific campaigns
-- 4. Include ASIN filters if focusing on specific products
-- 5. Set include_cost_data to TRUE if you want spend metrics

WITH parameters AS (
    SELECT
        DATE '{{start_date}}' as startDate,
        DATE '{{end_date}}' as endDate,
        {{include_cost_data}} as include_cost_data
),

first_party_users AS (
    SELECT DISTINCT user_id
    FROM {{first_party_table_name}}
),

first_party_audience_size AS (
    SELECT COUNT(DISTINCT user_id) as audience_size
    FROM first_party_users
),

-- Combine all ad product impressions and clicks
combined_traffic AS (
    -- DSP Traffic
    SELECT 
        'amazon_dsp' as ad_product_type,
        user_id,
        impression_dt as event_dt,
        campaign_id,
        1 as impressions,
        clicks,
        CASE WHEN include_cost_data THEN total_cost ELSE 0 END as cost
    FROM dsp_impressions, parameters
    WHERE impression_dt BETWEEN parameters.startDate AND parameters.endDate
    
    UNION ALL
    
    -- Sponsored Products
    SELECT 
        'sponsored_products' as ad_product_type,
        user_id,
        traffic_dt as event_dt,
        campaign_id,
        impressions,
        clicks,
        CASE WHEN include_cost_data THEN spend ELSE 0 END as cost
    FROM sponsored_ads_traffic, parameters
    WHERE ad_product_type = 'sponsored_products'
        AND traffic_dt BETWEEN parameters.startDate AND parameters.endDate
    
    UNION ALL
    
    -- Sponsored Display
    SELECT 
        'sponsored_display' as ad_product_type,
        user_id,
        traffic_dt as event_dt,
        campaign_id,
        impressions,
        clicks,
        CASE WHEN include_cost_data THEN spend ELSE 0 END as cost
    FROM sponsored_ads_traffic, parameters
    WHERE ad_product_type = 'sponsored_display'
        AND traffic_dt BETWEEN parameters.startDate AND parameters.endDate
    
    UNION ALL
    
    -- Sponsored Brands
    SELECT 
        'sponsored_brands' as ad_product_type,
        user_id,
        traffic_dt as event_dt,
        campaign_id,
        impressions,
        clicks,
        CASE WHEN include_cost_data THEN spend ELSE 0 END as cost
    FROM sponsored_ads_traffic, parameters
    WHERE ad_product_type = 'sponsored_brands'
        AND traffic_dt BETWEEN parameters.startDate AND parameters.endDate
),

-- Get conversions for all users
user_conversions AS (
    SELECT 
        attr.user_id,
        COUNT(DISTINCT attr.order_id) as orders,
        SUM(attr.revenue) as revenue
    FROM amazon_attributed_events_by_traffic_time attr
    INNER JOIN combined_traffic ct
        ON attr.user_id = ct.user_id
        AND attr.traffic_dt BETWEEN ct.event_dt AND ct.event_dt + INTERVAL '14' DAY
    WHERE attr.purchase_dt BETWEEN (SELECT startDate FROM parameters) 
        AND (SELECT endDate FROM parameters) + INTERVAL '14' DAY
    GROUP BY attr.user_id
),

-- Aggregate metrics by ad product and customer set
performance_by_segment AS (
    SELECT 
        ct.ad_product_type,
        CASE 
            WHEN fp.user_id IS NOT NULL THEN 'known'
            ELSE 'unknown'
        END as customer_set,
        COUNT(DISTINCT ct.user_id) as unique_reach,
        SUM(ct.impressions) as impressions,
        SUM(ct.clicks) as clicks,
        SUM(ct.cost) as spend,
        COUNT(DISTINCT uc.user_id) as users_that_purchased,
        SUM(uc.orders) as total_orders,
        SUM(uc.revenue) as total_revenue
    FROM combined_traffic ct
    LEFT JOIN first_party_users fp ON ct.user_id = fp.user_id
    LEFT JOIN user_conversions uc ON ct.user_id = uc.user_id
    GROUP BY ct.ad_product_type, customer_set
),

-- Calculate totals for percentage calculations
totals AS (
    SELECT 
        ad_product_type,
        SUM(spend) as total_spend,
        SUM(unique_reach) as total_reach
    FROM performance_by_segment
    GROUP BY ad_product_type
)

-- Final output with all metrics
SELECT 
    p.ad_product_type,
    p.customer_set,
    CASE 
        WHEN p.customer_set = 'known' THEN a.audience_size 
        ELSE NULL 
    END as audience_size,
    p.unique_reach,
    CASE 
        WHEN p.customer_set = 'known' AND a.audience_size > 0 
        THEN ROUND(CAST(p.unique_reach AS DECIMAL) / a.audience_size * 100, 2)
        ELSE NULL
    END as audience_reach_percent,
    ROUND(p.spend, 2) as spend,
    CASE 
        WHEN t.total_spend > 0 
        THEN ROUND(p.spend / t.total_spend * 100, 2)
        ELSE 0
    END as percent_of_spend,
    p.impressions,
    p.clicks,
    ROUND(CAST(p.clicks AS DECIMAL) / NULLIF(p.impressions, 0) * 100, 4) as ctr,
    p.users_that_purchased,
    ROUND(CAST(p.users_that_purchased AS DECIMAL) / NULLIF(p.unique_reach, 0) * 100, 2) as user_purchase_rate,
    p.total_orders,
    p.total_revenue,
    CASE 
        WHEN p.spend > 0 
        THEN ROUND(p.total_revenue / p.spend, 2)
        ELSE NULL
    END as roas
FROM performance_by_segment p
CROSS JOIN first_party_audience_size a
LEFT JOIN totals t ON p.ad_product_type = t.ad_product_type
ORDER BY p.ad_product_type, p.customer_set DESC;""",
            "parameters_schema": {
                "start_date": {
                    "type": "date",
                    "default": "CURRENT_DATE - 30",
                    "description": "Start date for analysis period"
                },
                "end_date": {
                    "type": "date",
                    "default": "CURRENT_DATE",
                    "description": "End date for analysis period"
                },
                "first_party_table_name": {
                    "type": "string",
                    "required": True,
                    "description": "Name of your first-party audience table"
                },
                "include_cost_data": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include spend metrics in analysis"
                }
            },
            "display_order": 2
        }
    ]
    
    query_ids = []
    for query in queries:
        result = supabase.table("build_guide_queries").upsert(query).execute()
        if result.data:
            query_ids.append(result.data[0]['id'])
    print(f"✅ Created {len(queries)} queries")
    
    # 4. Create examples (linked to the main analysis query)
    examples = [
        {
            "guide_query_id": query_ids[1] if len(query_ids) > 1 else query_ids[0],  # Link to main analysis query
            "example_name": "Sample Performance Comparison",
            "sample_data": {
                "rows": [
                    {
                        "ad_product_type": "amazon_dsp",
                        "customer_set": "known",
                        "audience_size": 1234567,
                        "unique_reach": 654321,
                        "audience_reach_percent": 53.00,
                        "spend": 4907.41,
                        "percent_of_spend": 21.81,
                        "impressions": 1635803,
                        "clicks": 7041,
                        "ctr": 0.43,
                        "users_that_purchased": 2814,
                        "user_purchase_rate": 0.43,
                        "total_orders": 3256,
                        "total_revenue": 98543.21,
                        "roas": 20.08
                    },
                    {
                        "ad_product_type": "amazon_dsp",
                        "customer_set": "unknown",
                        "audience_size": None,
                        "unique_reach": 2345678,
                        "audience_reach_percent": None,
                        "spend": 17592.59,
                        "percent_of_spend": 78.19,
                        "impressions": 5864195,
                        "clicks": 23457,
                        "ctr": 0.40,
                        "users_that_purchased": 4926,
                        "user_purchase_rate": 0.21,
                        "total_orders": 5432,
                        "total_revenue": 234567.89,
                        "roas": 13.33
                    },
                    {
                        "ad_product_type": "sponsored_products",
                        "customer_set": "known",
                        "audience_size": 1234567,
                        "unique_reach": 432210,
                        "audience_reach_percent": 35.01,
                        "spend": 3241.58,
                        "percent_of_spend": 11.11,
                        "impressions": 1080525,
                        "clicks": 54026,
                        "ctr": 5.00,
                        "users_that_purchased": 2809,
                        "user_purchase_rate": 0.65,
                        "total_orders": 3987,
                        "total_revenue": 87654.32,
                        "roas": 27.04
                    },
                    {
                        "ad_product_type": "sponsored_products",
                        "customer_set": "unknown",
                        "audience_size": None,
                        "unique_reach": 3456789,
                        "audience_reach_percent": None,
                        "spend": 25925.92,
                        "percent_of_spend": 88.89,
                        "impressions": 8641973,
                        "clicks": 345679,
                        "ctr": 4.00,
                        "users_that_purchased": 14864,
                        "user_purchase_rate": 0.43,
                        "total_orders": 18765,
                        "total_revenue": 567890.12,
                        "roas": 21.90
                    },
                    {
                        "ad_product_type": "sponsored_display",
                        "customer_set": "known",
                        "audience_size": 1234567,
                        "unique_reach": 321098,
                        "audience_reach_percent": 26.01,
                        "spend": 2134.56,
                        "percent_of_spend": 15.23,
                        "impressions": 890123,
                        "clicks": 8901,
                        "ctr": 1.00,
                        "users_that_purchased": 1605,
                        "user_purchase_rate": 0.50,
                        "total_orders": 2107,
                        "total_revenue": 45678.90,
                        "roas": 21.40
                    },
                    {
                        "ad_product_type": "sponsored_display",
                        "customer_set": "unknown",
                        "audience_size": None,
                        "unique_reach": 2987654,
                        "audience_reach_percent": None,
                        "spend": 11876.44,
                        "percent_of_spend": 84.77,
                        "impressions": 5938220,
                        "clicks": 47506,
                        "ctr": 0.80,
                        "users_that_purchased": 8963,
                        "user_purchase_rate": 0.30,
                        "total_orders": 10234,
                        "total_revenue": 234567.89,
                        "roas": 19.75
                    }
                ]
            },
            "interpretation_markdown": """## Key Insights from Results

### Performance Comparison
- **Known customers show 2x higher purchase rate on DSP** (0.43% vs 0.21%)
- **Sponsored Products most effective for known customers** (0.65% purchase rate)
- **78-94% of spend goes to unknown customers** across all channels

### Reach Analysis
- **DSP achieves highest known customer reach** (53% of 1P audience)
- **Sponsored Products reaches 35%** of known customers
- **Lower reach on Sponsored Display** (26%) and Brands (17%)

### ROI Differences
- **Known customers deliver higher ROAS on DSP** (20.08 vs 13.33)
- **Sponsored Products shows strong ROAS** for both segments (27.04 known, 21.90 unknown)
- **Consistent CTR advantage for known customers** across all channels

### Strategic Implications
1. **Current strategy favors growth** with 78-89% spend on unknown customers
2. **Opportunity to increase known customer targeting** for higher conversion rates
3. **DSP showing strong performance** for reaching known audience at scale
4. **Consider channel-specific strategies** based on segment performance""",
            "display_order": 1
        }
    ]
    
    for example in examples:
        result = supabase.table("build_guide_examples").upsert(example).execute()
    print(f"✅ Created {len(examples)} examples")
    
    # 5. Create metrics
    metrics = [
        {
            "guide_id": guide_uuid,
            "metric_name": "audience_size",
            "display_name": "Audience Size",
            "metric_type": "dimension",
            "definition": "Total number of users in your first-party data. Calculated as COUNT(DISTINCT user_id) from first-party table",
            "display_order": 1
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "unique_reach",
            "display_name": "Unique Reach",
            "metric_type": "metric",
            "definition": "Number of unique users reached by campaigns. Calculated as COUNT(DISTINCT user_id) from traffic events",
            "display_order": 2
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "audience_reach_percent",
            "display_name": "Audience Reach %",
            "metric_type": "metric",
            "definition": "Percentage of known customers reached. Calculated as (unique_reach / audience_size) * 100",
            "display_order": 3
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "percent_of_spend",
            "display_name": "Percent of Spend",
            "metric_type": "metric",
            "definition": "Share of total ad spend for each segment. Calculated as (segment_spend / total_spend) * 100",
            "display_order": 4
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "user_purchase_rate",
            "display_name": "User Purchase Rate",
            "metric_type": "metric",
            "definition": "Conversion rate from reached users to purchasers. Calculated as (users_that_purchased / unique_reach) * 100",
            "display_order": 5
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "customer_set",
            "display_name": "Customer Set",
            "metric_type": "dimension",
            "definition": "Segmentation of users into known (1P) or unknown. User exists in first-party table = 'known', else 'unknown'",
            "display_order": 6
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "roas",
            "display_name": "ROAS",
            "metric_type": "metric",
            "definition": "Return on ad spend. Calculated as total_revenue / spend",
            "display_order": 7
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "ctr",
            "display_name": "CTR",
            "metric_type": "metric",
            "definition": "Click-through rate. Calculated as (clicks / impressions) * 100",
            "display_order": 8
        }
    ]
    
    for metric in metrics:
        result = supabase.table("build_guide_metrics").upsert(metric).execute()
    print(f"✅ Created {len(metrics)} metrics")
    
    print(f"\n✨ Successfully seeded First-Party vs Unknown Customer Performance Analysis guide!")
    print(f"📊 Guide ID: {guide_id}")

if __name__ == "__main__":
    try:
        seed_first_party_performance_guide()
    except Exception as e:
        print(f"❌ Error seeding guide: {e}")
        raise