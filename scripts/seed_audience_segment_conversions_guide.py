#!/usr/bin/env python
"""
Seed script for Audience Segment Conversions Build Guide
Creates a comprehensive guide for analyzing conversion performance by audience segments
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Dict, Any, List

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)

supabase: Client = create_client(url, key)

def create_guide():
    """Create the main guide entry"""
    guide_data = {
        "guide_id": "guide_audience_segment_conversions",
        "name": "Conversions by Audience Segment with Impressions",
        "category": "Audience Analytics",
        "short_description": "Analyze the performance of audience segments in driving conversions, comparing targeted vs. untargeted segments to optimize audience strategy",
        "difficulty_level": "advanced",
        "estimated_time_minutes": 30,
        "tags": ["audience", "segments", "conversions", "performance", "targeting", "attribution"],
        "prerequisites": [
            "Understanding of AMC data structure",
            "Knowledge of audience segments",
            "Familiarity with conversion attribution"
        ],
        "is_published": True,
        "display_order": 8,
        "icon": "Users"
    }
    
    result = supabase.table("build_guides").upsert(guide_data).execute()
    guide_record = result.data[0] if result.data else None
    if not guide_record:
        raise Exception("Failed to create guide")
    return guide_record["id"]

def create_sections(guide_uuid: str):
    """Create all guide sections"""
    sections = [
        {
            "guide_id": guide_uuid,
            "section_id": "introduction",
            "title": "Introduction",
            "display_order": 1,
            "content_markdown": """## Purpose and Overview

This instructional query analyzes the performance of audience segments in driving conversions on Amazon. It compares targeted segments (those you specifically selected in your campaign) versus untargeted segments (users who saw your ads but weren't explicitly targeted) to help optimize your audience strategy.

### Benefits of Analyzing Audience Segment Performance

- **Identify High-Value Segments**: Discover which audience segments drive the most conversions and revenue
- **Optimize Targeting Strategy**: Understand whether targeted or untargeted segments perform better
- **Budget Allocation**: Allocate more budget to segments with higher conversion rates
- **Audience Expansion**: Find new segments to target based on untargeted performance
- **Performance Benchmarking**: Compare segment performance across campaigns

### Key Use Cases

1. **Segment Performance Analysis**: Evaluate which audience segments generate the highest purchase rates
2. **Targeted vs Untargeted Comparison**: Understand the value of your targeting strategy
3. **Cross-Campaign Analysis**: Compare segment performance across different campaigns
4. **ROI Optimization**: Focus spend on segments with the best return on investment
5. **Audience Discovery**: Identify high-performing untargeted segments for future campaigns"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "data_query_instructions",
            "title": "Data Query Instructions",
            "display_order": 2,
            "content_markdown": """## Data Query Setup

### Data Returned

This query returns a comprehensive view of audience segment performance including:
- Segment identification (ID and name)
- Impression metrics (total and matched)
- Reach metrics (unique users)
- Conversion metrics (users, purchases, units, revenue)
- Campaign context (advertiser and campaign details)

### Tables Used

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `dsp_impressions_by_user_segments` | User segments from DSP | user_id, segment_id, campaign_id |
| `dsp_impressions_by_matched_segments` | Matched/targeted segments | user_id, segment_id, campaign_id |
| `amazon_attributed_events_by_traffic_time` | Conversion events | user_id, purchase metrics |

### Required Updates

Before running this query, you must update the following:

1. **Campaign IDs** (Line marked with `-- UPDATE 1`):
   - Replace with your specific campaign IDs
   - Format: `('campaign_id_1', 'campaign_id_2', ...)`

2. **Date Range** (Lines marked with `-- UPDATE 2` and `-- UPDATE 3`):
   - Update start_date and end_date
   - Format: `YYYY-MM-DD`
   - Consider 14-day conversion window

3. **Segment Filters** (Optional - Line marked with `-- UPDATE 4`):
   - Filter to specific segment types if needed
   - Example: `WHERE segment_name LIKE 'IM%'` for in-market segments

4. **Matched Filter** (Optional - Line marked with `-- UPDATE 5`):
   - Filter to only matched (1) or unmatched (0) segments
   - Remove WHERE clause to see both

### Performance Optimization Tips

- **Date Range**: Keep to 30-90 days for optimal performance
- **Campaign Selection**: Limit to 10-20 campaigns per query
- **Segment Filtering**: Use segment prefixes to reduce data volume
- **Aggregation**: Pre-aggregate in CTEs to improve join performance"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "data_interpretation",
            "title": "Data Interpretation Instructions",
            "display_order": 3,
            "content_markdown": """## Understanding Your Results

### Matched vs Unmatched Segments

**Matched Segments (matched = 1)**:
- Segments you explicitly targeted in your campaign
- These users were intentionally reached based on your targeting strategy
- Higher impressions here indicate successful targeting execution

**Unmatched Segments (matched = 0)**:
- Users who saw your ads but weren't in your targeted segments
- Often reached through contextual targeting or broad reach
- Can reveal unexpected high-performing audiences

### How to Read the Results

1. **Impression Distribution**:
   - Compare `impressions` vs `matched_impressions`
   - High matched ratio = precise targeting
   - High unmatched ratio = broad reach beyond targeting

2. **Conversion Performance**:
   - Calculate purchase rate: `users_that_purchased / impression_reach`
   - Higher rates indicate more effective segments
   - Compare rates between matched and unmatched

3. **Revenue Impact**:
   - Look at `total_product_sales` for revenue contribution
   - Calculate revenue per user: `total_product_sales / users_that_purchased`
   - Identify segments with high average order values

### Important Notes About Data

⚠️ **Data Duplication Warning**:
- Users can belong to multiple segments
- Impressions may be counted multiple times across segments
- Sum of segment impressions may exceed campaign totals
- Focus on relative performance rather than absolute totals

📊 **Statistical Significance**:
- Segments with <100 impressions may not be statistically reliable
- Look for patterns across multiple campaigns
- Consider confidence intervals for small segments

🔄 **Attribution Window**:
- Standard 14-day attribution window applies
- Purchases beyond this window won't be captured
- Consider seasonality and purchase cycles"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "example_results",
            "title": "Example Query Results",
            "display_order": 4,
            "content_markdown": """## Sample Results

Below is an example of typical query results showing audience segment performance:

### Column Definitions

| Column | Description |
|--------|-------------|
| advertiser_id | Unique identifier for the advertiser |
| advertiser | Advertiser name |
| campaign_id | Campaign identifier |
| campaign | Campaign name |
| segment_id | Unique segment identifier |
| segment_name | Human-readable segment name |
| matched | 1 if targeted segment, 0 if untargeted |
| impressions | Total impressions for the segment |
| matched_impressions | Impressions from targeted users |
| impression_reach | Unique users reached |
| users_that_purchased | Count of users who made purchases |
| total_purchases | Total number of purchase events |
| total_units_sold | Sum of units sold |
| total_product_sales | Total revenue generated |

### Insights from Example Data

The example data reveals several key patterns:

1. **High-Performance Segments**:
   - "IM - Eye Makeup" shows strong conversion with 15 purchasers from 17,892 impressions
   - "IM - Eyes Makeup Sets" has excellent conversion rate (10 purchasers from 11,993 impressions)

2. **Volume Leaders**:
   - "IM - Makeup" drives highest volume with 59,435 impressions and 27 purchasers
   - Large reach but lower conversion rate suggests broad appeal

3. **Optimization Opportunities**:
   - "IM - Lip Care" shows lower performance (7 purchasers from 20,967 impressions)
   - Consider reducing investment or improving creative for this segment"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "segment_reference",
            "title": "Segment Name Reference",
            "display_order": 5,
            "content_markdown": """## Understanding Segment Names

### Common Segment Prefixes

| Prefix | Segment Type | Description | Example |
|--------|--------------|-------------|---------|
| IM | In-Market | Users actively shopping in category | IM - Makeup |
| LS | Lifestyle | Based on browsing and purchase behavior | LS - Beauty Enthusiast |
| Demo | Demographic | Age, gender, income segments | Demo - Female 25-34 |
| B | Behavioral | Based on shopping patterns | B - Frequent Shoppers |
| RL | Remarketing List | Users who previously interacted | RL - Cart Abandoners |
| LAL | Lookalike | Similar to seed audience | LAL - High Value Customers |
| GEO | Geographic | Location-based segments | GEO - Urban Professionals |
| INT | Interest | Based on content consumption | INT - Fashion & Style |

### Segment Hierarchy

Many segments follow a hierarchical structure:
- **Level 1**: Broad category (e.g., "IM - Beauty")
- **Level 2**: Subcategory (e.g., "IM - Makeup")
- **Level 3**: Specific product (e.g., "IM - Eye Makeup")

### Amazon-Specific Segments

| Segment Type | Description | Value Proposition |
|--------------|-------------|-------------------|
| Amazon Shoppers | Users with purchase history | High intent, proven buyers |
| Prime Members | Active Prime subscribers | Higher AOV, frequent purchases |
| Brand Followers | Users who follow your brand | High engagement, loyalty |
| Category Browsers | Recent category visitors | Active consideration phase |
| Competitor Shoppers | Viewed competitor products | Conquest opportunity |

### Custom vs Prebuilt Segments

**Prebuilt Segments**:
- Created and maintained by Amazon
- Updated regularly with fresh data
- Broad reach and scale

**Custom Segments**:
- Created using your first-party data
- More precise targeting
- Often show as "Custom_" prefix"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "metrics_definitions",
            "title": "Metrics Definitions",
            "display_order": 6,
            "content_markdown": """## Detailed Metrics Explanations

### Impression Metrics

**impressions**
- Total number of ad impressions served to users in this segment
- Includes both matched and unmatched impressions
- One user can generate multiple impressions

**matched_impressions**
- Impressions served to users you explicitly targeted
- Subset of total impressions
- Indicates targeting precision

**impression_reach**
- Count of unique users who saw your ads
- Deduplicated user count
- Better metric for audience size than impressions

### Conversion Metrics

**users_that_purchased**
- Unique count of users who made at least one purchase
- Attributed within the conversion window
- Key metric for conversion rate calculation

**total_purchases**
- Total number of purchase transactions
- Can be multiple per user
- Indicates repeat purchase behavior

**total_units_sold**
- Sum of all units purchased
- Useful for volume-based analysis
- Can indicate bulk buying patterns

**total_product_sales**
- Total revenue generated (in advertiser's currency)
- Most important for ROI calculation
- Includes all attributed sales

### Derived Metrics (Calculate These)

**Purchase Rate**
```
purchase_rate = users_that_purchased / impression_reach * 100
```
- Percentage of reached users who purchased
- Key efficiency metric
- Compare across segments

**Average Order Value (AOV)**
```
aov = total_product_sales / total_purchases
```
- Revenue per transaction
- Indicates purchase quality
- Varies by segment demographics

**Units Per Purchase**
```
units_per_purchase = total_units_sold / total_purchases
```
- Average basket size
- Indicates bulk buying
- Useful for inventory planning

**Revenue Per User**
```
revenue_per_user = total_product_sales / users_that_purchased
```
- Value of converting users
- Includes multiple purchases
- Key for LTV estimation

**Cost Per Acquisition (if cost data available)**
```
cpa = segment_cost / users_that_purchased
```
- Efficiency of segment targeting
- Compare to revenue per user
- Determines profitability"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "insights_interpretation",
            "title": "Insights and Data Interpretation",
            "display_order": 7,
            "content_markdown": """## Actionable Insights from Your Data

### Identifying High-Performing Segments

Look for segments with:
- **High Purchase Rate** (>2% is typically strong)
- **High AOV** (above campaign average)
- **Low CPA** (if cost data available)
- **Consistent Performance** across time periods

**Action Items for High Performers**:
1. Increase bid multipliers for these segments
2. Create segment-specific creative
3. Expand budget allocation
4. Find similar segments to test
5. Use for lookalike audience seeds

### Identifying Low-Performing Segments

Watch for segments with:
- **Low Purchase Rate** (<0.5%)
- **High Impressions but Low Conversions**
- **Below-Average AOV**
- **Declining Performance** over time

**Optimization Strategies for Low Performers**:
1. Reduce bids or pause targeting
2. Test different creative messages
3. Narrow targeting with additional filters
4. Check frequency caps (may be oversaturated)
5. Evaluate product-market fit

### Optimization Recommendations

#### 1. Portfolio Approach
- **Core Segments** (40-50% budget): Proven performers with consistent ROAS
- **Growth Segments** (30-40% budget): Showing improvement, scaling potential
- **Test Segments** (10-20% budget): New segments, experimental targeting

#### 2. Matched vs Unmatched Strategy
If unmatched segments perform well:
- Consider broader targeting strategies
- Test contextual and behavioral targeting
- Reduce segment restrictions

If matched segments dominate:
- Double down on precision targeting
- Create more granular segments
- Test segment combinations

#### 3. Segment Combination Tactics
- **Layering**: Combine high-intent segments (e.g., IM + Brand Followers)
- **Exclusions**: Remove poor performers from broad campaigns
- **Sequential**: Target awareness → consideration → purchase segments

#### 4. Creative Optimization by Segment
- **In-Market**: Focus on competitive advantages and urgency
- **Lifestyle**: Emphasize brand values and lifestyle fit
- **Demographic**: Tailor imagery and messaging to audience
- **Behavioral**: Highlight relevant use cases

### Advanced Analysis Techniques

**Cohort Analysis**:
- Track segment performance over time
- Identify seasonal patterns
- Measure segment fatigue

**Incrementality Testing**:
- Run holdout tests by segment
- Measure true incremental impact
- Optimize for incremental ROAS

**Cross-Device Attribution**:
- Understand multi-device journey
- Segment by device preference
- Optimize creative by device

**Competitive Intelligence**:
- Analyze segment overlap with competitors
- Identify conquest opportunities
- Protect high-value segments"""
        }
    ]
    
    for section in sections:
        supabase.table("build_guide_sections").upsert(section).execute()

def create_queries(guide_uuid: str):
    """Create query templates for the guide"""
    queries = [
        {
            "guide_id": guide_uuid,
            "query_type": "main_analysis",
            "title": "Audience Segment Conversion Analysis",
            "description": "Comprehensive query analyzing conversion performance by audience segment with matched/unmatched breakdown",
            "display_order": 1,
            "sql_query": """-- Audience Segment Conversion Analysis
-- Analyzes the performance of different audience segments in driving conversions
-- Compares targeted (matched) vs untargeted (unmatched) segment performance

WITH impressions_by_segment AS (
    -- Get all impressions by user segments
    SELECT 
        advertiser_id,
        advertiser,
        campaign_id,
        campaign,
        segment_id,
        segment_name,
        user_id,
        COUNT(*) as impressions,
        0 as matched  -- These are all user segments (not necessarily matched)
    FROM dsp_impressions_by_user_segments
    WHERE campaign_id IN (
        -- UPDATE 1: Add your campaign IDs here
        'campaign_id_1',
        'campaign_id_2',
        'campaign_id_3'
    )
    -- UPDATE 2: Set your date range
    AND impression_dt >= DATE('2024-01-01')  -- Start date
    AND impression_dt <= DATE('2024-03-31')  -- End date
    GROUP BY 1, 2, 3, 4, 5, 6, 7
),

matched_impressions AS (
    -- Get impressions from matched/targeted segments
    SELECT 
        advertiser_id,
        advertiser,
        campaign_id,
        campaign,
        segment_id,
        segment_name,
        user_id,
        COUNT(*) as matched_impressions,
        1 as matched  -- These are matched segments
    FROM dsp_impressions_by_matched_segments
    WHERE campaign_id IN (
        -- Should match UPDATE 1 campaign IDs
        'campaign_id_1',
        'campaign_id_2',
        'campaign_id_3'
    )
    -- Should match UPDATE 2 date range
    AND impression_dt >= DATE('2024-01-01')
    AND impression_dt <= DATE('2024-03-31')
    GROUP BY 1, 2, 3, 4, 5, 6, 7
),

all_segments AS (
    -- Combine matched and unmatched segments
    SELECT * FROM impressions_by_segment
    UNION ALL
    SELECT 
        advertiser_id,
        advertiser,
        campaign_id,
        campaign,
        segment_id,
        segment_name,
        user_id,
        matched_impressions as impressions,
        matched
    FROM matched_impressions
),

segment_metrics AS (
    -- Aggregate metrics by segment
    SELECT 
        advertiser_id,
        advertiser,
        campaign_id,
        campaign,
        segment_id,
        segment_name,
        MAX(matched) as matched,  -- Will be 1 if segment was targeted
        SUM(impressions) as impressions,
        SUM(CASE WHEN matched = 1 THEN impressions ELSE 0 END) as matched_impressions,
        COUNT(DISTINCT user_id) as impression_reach
    FROM all_segments
    -- UPDATE 4: Optional - Filter to specific segment types
    -- WHERE segment_name LIKE 'IM%'  -- Example: only In-Market segments
    GROUP BY 1, 2, 3, 4, 5, 6
),

conversions AS (
    -- Get conversion data for users
    SELECT 
        user_id,
        COUNT(DISTINCT purchase_id) as purchases,
        SUM(units) as units_sold,
        SUM(product_sales) as product_sales
    FROM amazon_attributed_events_by_traffic_time
    WHERE conversion_event = 'purchase'
    -- UPDATE 3: Should match or be slightly after impression date range
    -- to account for conversion window
    AND conversion_dt >= DATE('2024-01-01')
    AND conversion_dt <= DATE('2024-04-14')  -- End date + 14 day window
    GROUP BY 1
),

user_conversions AS (
    -- Join users with their conversion data
    SELECT DISTINCT
        s.advertiser_id,
        s.advertiser,
        s.campaign_id,
        s.campaign,
        s.segment_id,
        s.segment_name,
        s.matched,
        s.user_id,
        COALESCE(c.purchases, 0) as purchases,
        COALESCE(c.units_sold, 0) as units_sold,
        COALESCE(c.product_sales, 0) as product_sales,
        CASE WHEN c.user_id IS NOT NULL THEN 1 ELSE 0 END as purchased_flag
    FROM all_segments s
    LEFT JOIN conversions c ON s.user_id = c.user_id
)

-- Final aggregation
SELECT 
    m.advertiser_id,
    m.advertiser,
    m.campaign_id,
    m.campaign,
    m.segment_id,
    m.segment_name,
    m.matched,
    m.impressions,
    m.matched_impressions,
    m.impression_reach,
    COALESCE(SUM(uc.purchased_flag), 0) as users_that_purchased,
    COALESCE(SUM(uc.purchases), 0) as total_purchases,
    COALESCE(SUM(uc.units_sold), 0) as total_units_sold,
    COALESCE(ROUND(SUM(uc.product_sales), 2), 0) as total_product_sales,
    -- Calculate purchase rate
    CASE 
        WHEN m.impression_reach > 0 
        THEN ROUND(100.0 * SUM(uc.purchased_flag) / m.impression_reach, 2)
        ELSE 0 
    END as purchase_rate_pct
FROM segment_metrics m
LEFT JOIN user_conversions uc 
    ON m.advertiser_id = uc.advertiser_id
    AND m.campaign_id = uc.campaign_id
    AND m.segment_id = uc.segment_id
-- UPDATE 5: Optional - Filter to only matched or unmatched
-- WHERE m.matched = 1  -- Only targeted segments
-- WHERE m.matched = 0  -- Only untargeted segments
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
HAVING m.impressions > 100  -- Filter out very small segments
ORDER BY total_product_sales DESC
LIMIT 500;""",
            "parameters_schema": {
                "campaign_ids": {"type": "array", "description": "List of campaign IDs to analyze"},
                "start_date": {"type": "date", "description": "Start date for analysis period"},
                "end_date": {"type": "date", "description": "End date for analysis period"},
                "segment_filter": {"type": "string", "description": "Optional filter for segment names", "required": False},
                "matched_filter": {"type": "integer", "description": "Filter for matched (1) or unmatched (0) segments", "required": False}
            }
        },
        {
            "guide_id": guide_uuid,
            "query_type": "exploratory",
            "title": "High Purchase Rate Segments",
            "description": "Identifies segments with the highest purchase rates for optimization",
            "display_order": 2,
            "sql_query": """-- High Purchase Rate Segment Analysis
-- Identifies top-performing segments by purchase rate

WITH segment_performance AS (
    SELECT 
        segment_id,
        segment_name,
        matched,
        COUNT(DISTINCT user_id) as users_reached,
        COUNT(DISTINCT CASE WHEN purchased = 1 THEN user_id END) as purchasers,
        SUM(product_sales) as revenue
    FROM (
        SELECT 
            i.segment_id,
            i.segment_name,
            i.user_id,
            MAX(CASE WHEN m.user_id IS NOT NULL THEN 1 ELSE 0 END) as matched,
            MAX(CASE WHEN c.user_id IS NOT NULL THEN 1 ELSE 0 END) as purchased,
            COALESCE(SUM(c.product_sales), 0) as product_sales
        FROM dsp_impressions_by_user_segments i
        LEFT JOIN dsp_impressions_by_matched_segments m
            ON i.user_id = m.user_id 
            AND i.segment_id = m.segment_id
            AND i.campaign_id = m.campaign_id
        LEFT JOIN amazon_attributed_events_by_traffic_time c
            ON i.user_id = c.user_id
            AND c.conversion_event = 'purchase'
        WHERE i.campaign_id IN ('campaign_id_1', 'campaign_id_2')  -- UPDATE
        GROUP BY 1, 2, 3
    ) user_level
    GROUP BY 1, 2, 3
)

SELECT 
    segment_name,
    CASE WHEN matched = 1 THEN 'Targeted' ELSE 'Untargeted' END as segment_type,
    users_reached,
    purchasers,
    ROUND(100.0 * purchasers / NULLIF(users_reached, 0), 2) as purchase_rate_pct,
    ROUND(revenue, 2) as total_revenue,
    ROUND(revenue / NULLIF(purchasers, 0), 2) as revenue_per_purchaser
FROM segment_performance
WHERE users_reached >= 100  -- Minimum sample size
ORDER BY purchase_rate_pct DESC
LIMIT 50;""",
            "parameters_schema": {
                "campaign_ids": {"type": "array", "description": "Campaign IDs to analyze"},
                "min_users": {"type": "integer", "description": "Minimum users for statistical significance", "default": 100}
            }
        },
        {
            "guide_id": guide_uuid,
            "query_type": "exploratory",
            "title": "Segment Overlap Analysis",
            "description": "Analyzes overlap between segments and untargeted reach",
            "display_order": 3,
            "sql_query": """-- Segment Overlap and Untargeted Reach Analysis
-- Understand how much of your reach comes from targeted vs untargeted segments

WITH targeted_users AS (
    -- Users in your targeted segments
    SELECT DISTINCT
        campaign_id,
        user_id,
        COUNT(DISTINCT segment_id) as targeted_segment_count
    FROM dsp_impressions_by_matched_segments
    WHERE campaign_id IN ('campaign_id_1', 'campaign_id_2')  -- UPDATE
    GROUP BY 1, 2
),

all_users AS (
    -- All users who saw impressions
    SELECT DISTINCT
        campaign_id,
        user_id,
        COUNT(DISTINCT segment_id) as total_segment_count
    FROM dsp_impressions_by_user_segments
    WHERE campaign_id IN ('campaign_id_1', 'campaign_id_2')  -- UPDATE
    GROUP BY 1, 2
),

user_classification AS (
    SELECT 
        a.campaign_id,
        a.user_id,
        a.total_segment_count,
        COALESCE(t.targeted_segment_count, 0) as targeted_segment_count,
        CASE 
            WHEN t.user_id IS NOT NULL THEN 'Targeted'
            ELSE 'Untargeted'
        END as user_type
    FROM all_users a
    LEFT JOIN targeted_users t
        ON a.campaign_id = t.campaign_id
        AND a.user_id = t.user_id
)

SELECT 
    campaign_id,
    user_type,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(total_segment_count) as avg_segments_per_user,
    AVG(targeted_segment_count) as avg_targeted_segments,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_segment_count) as median_segments
FROM user_classification
GROUP BY 1, 2

UNION ALL

SELECT 
    campaign_id,
    'Total' as user_type,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(total_segment_count) as avg_segments_per_user,
    AVG(targeted_segment_count) as avg_targeted_segments,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_segment_count) as median_segments
FROM user_classification
GROUP BY 1
ORDER BY campaign_id, user_type;""",
            "parameters_schema": {
                "campaign_ids": {"type": "array", "description": "Campaign IDs to analyze"}
            }
        }
    ]
    
    query_ids = []
    for query in queries:
        # Convert parameters_schema to JSON string
        query['parameters_schema'] = json.dumps(query['parameters_schema'])
        result = supabase.table("build_guide_queries").upsert(query).execute()
        if result.data:
            query_ids.append(result.data[0]['id'])
    return query_ids

def create_examples(guide_uuid: str, query_ids: list):
    """Create example results for the guide"""
    examples = [
        {
            "guide_query_id": query_ids[0] if query_ids else None,  # Link to main analysis query
            "example_name": "Segment Performance Results",
            "sample_data": {
                "rows": [
                    {
                        "advertiser_id": "ADV123456",
                        "advertiser": "Beauty Brand Co",
                        "campaign_id": "CAMP789012",
                        "campaign": "Q1 2024 Beauty Campaign",
                        "segment_id": "SEG_IM_001",
                        "segment_name": "IM - Makeup",
                        "matched": 1,
                        "impressions": 59435,
                        "matched_impressions": 59435,
                        "impression_reach": 42318,
                        "users_that_purchased": 27,
                        "total_purchases": 31,
                        "total_units_sold": 47,
                        "total_product_sales": 1245.67,
                        "purchase_rate_pct": 0.06
                    },
                    {
                        "advertiser_id": "ADV123456",
                        "advertiser": "Beauty Brand Co",
                        "campaign_id": "CAMP789012",
                        "campaign": "Q1 2024 Beauty Campaign",
                        "segment_id": "SEG_IM_002",
                        "segment_name": "IM - Eye Makeup",
                        "matched": 1,
                        "impressions": 17892,
                        "matched_impressions": 17892,
                        "impression_reach": 14234,
                        "users_that_purchased": 15,
                        "total_purchases": 18,
                        "total_units_sold": 22,
                        "total_product_sales": 687.90,
                        "purchase_rate_pct": 0.11
                    },
                    {
                        "advertiser_id": "ADV123456",
                        "advertiser": "Beauty Brand Co",
                        "campaign_id": "CAMP789012",
                        "campaign": "Q1 2024 Beauty Campaign",
                        "segment_id": "SEG_IM_003",
                        "segment_name": "IM - Eyes Makeup Sets",
                        "matched": 1,
                        "impressions": 11993,
                        "matched_impressions": 11993,
                        "impression_reach": 9875,
                        "users_that_purchased": 10,
                        "total_purchases": 12,
                        "total_units_sold": 15,
                        "total_product_sales": 524.85,
                        "purchase_rate_pct": 0.10
                    },
                    {
                        "advertiser_id": "ADV123456",
                        "advertiser": "Beauty Brand Co",
                        "campaign_id": "CAMP789012",
                        "campaign": "Q1 2024 Beauty Campaign",
                        "segment_id": "SEG_IM_004",
                        "segment_name": "IM - Lip Care",
                        "matched": 1,
                        "impressions": 20967,
                        "matched_impressions": 20967,
                        "impression_reach": 17234,
                        "users_that_purchased": 7,
                        "total_purchases": 8,
                        "total_units_sold": 11,
                        "total_product_sales": 234.56,
                        "purchase_rate_pct": 0.04
                    },
                    {
                        "advertiser_id": "ADV123456",
                        "advertiser": "Beauty Brand Co",
                        "campaign_id": "CAMP789012",
                        "campaign": "Q1 2024 Beauty Campaign",
                        "segment_id": "SEG_LS_001",
                        "segment_name": "LS - Beauty Enthusiast",
                        "matched": 0,
                        "impressions": 8456,
                        "matched_impressions": 0,
                        "impression_reach": 7123,
                        "users_that_purchased": 12,
                        "total_purchases": 14,
                        "total_units_sold": 19,
                        "total_product_sales": 456.78,
                        "purchase_rate_pct": 0.17
                    }
                ]
            },
            "interpretation_markdown": """### Key Insights from Example Data

1. **Untargeted Outperformance**: The "LS - Beauty Enthusiast" segment (untargeted) shows the highest purchase rate at 0.17%, suggesting an opportunity to add this segment to targeting.

2. **Volume vs Efficiency Trade-off**: "IM - Makeup" drives the highest volume but has lower efficiency (0.06% purchase rate) compared to more specific segments.

3. **Niche Segment Success**: "IM - Eye Makeup" and "IM - Eyes Makeup Sets" show strong performance with purchase rates above 0.10%, indicating value in granular targeting.

4. **Optimization Opportunity**: "IM - Lip Care" underperforms with only 0.04% purchase rate despite significant impressions, suggesting need for creative optimization or bid reduction."""
        }
    ]
    
    for example in examples:
        # Convert sample_data to JSON string
        example['sample_data'] = json.dumps(example['sample_data'])
        supabase.table("build_guide_examples").upsert(example).execute()

def create_metrics(guide_uuid: str):
    """Create metric definitions for the guide"""
    metrics = [
        {
            "guide_id": guide_uuid,
            "metric_name": "impressions",
            "display_name": "Total Impressions",
            "metric_type": "metric",
            "definition": "Total number of ad impressions served to users in this segment. Calculated as COUNT(*) from impression events. Indicates reach and frequency of segment exposure",
            "display_order": 1
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "matched_impressions",
            "display_name": "Matched Impressions",
            "metric_type": "metric",
            "definition": "Impressions served to explicitly targeted segment users. Calculated as COUNT(*) from matched segment impression events. Shows precision of targeting strategy",
            "display_order": 2
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "impression_reach",
            "display_name": "Unique Users Reached",
            "metric_type": "metric",
            "definition": "Count of unique users who received at least one impression. Calculated as COUNT(DISTINCT user_id). True audience size, deduplicated",
            "display_order": 3
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "users_that_purchased",
            "display_name": "Converting Users",
            "metric_type": "metric",
            "definition": "Count of unique users who made at least one purchase. Calculated as COUNT(DISTINCT user_id) WHERE purchase occurred. Core conversion metric for segment effectiveness",
            "display_order": 4
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "total_purchases",
            "display_name": "Total Purchases",
            "metric_type": "metric",
            "definition": "Total number of purchase transactions. Calculated as COUNT(DISTINCT purchase_id). Indicates repeat purchase behavior",
            "display_order": 5
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "total_units_sold",
            "display_name": "Units Sold",
            "metric_type": "metric",
            "definition": "Sum of all units purchased. Calculated as SUM(units). Volume metric for inventory and fulfillment",
            "display_order": 6
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "total_product_sales",
            "display_name": "Revenue",
            "metric_type": "metric",
            "definition": "Total revenue generated in advertiser currency. Calculated as SUM(product_sales). Financial impact of segment performance",
            "display_order": 7
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "purchase_rate",
            "display_name": "Purchase Rate",
            "metric_type": "metric",
            "definition": "Percentage of reached users who made a purchase. Calculated as (users_that_purchased / impression_reach) * 100. Key efficiency metric for segment targeting",
            "display_order": 8
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "segment_id",
            "display_name": "Segment ID",
            "metric_type": "dimension",
            "definition": "Unique identifier for the audience segment. Direct from source table. Used for joining and exact matching",
            "display_order": 9
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "segment_name",
            "display_name": "Segment Name",
            "metric_type": "dimension",
            "definition": "Human-readable name of the audience segment. Direct from source table. Used for reporting and analysis",
            "display_order": 10
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "matched",
            "display_name": "Matched Flag",
            "metric_type": "dimension",
            "definition": "Indicates if segment was explicitly targeted (1) or not (0). 1 if in matched_segments table, 0 otherwise. Distinguishes intentional vs incidental reach",
            "display_order": 11
        }
    ]
    
    for metric in metrics:
        supabase.table("build_guide_metrics").upsert(metric).execute()

def main():
    """Main execution function"""
    try:
        print("Creating Audience Segment Conversions Build Guide...")
        
        # Delete existing guide if it exists (should cascade to related tables)
        existing = supabase.table("build_guides").select("id").eq("guide_id", "guide_audience_segment_conversions").execute()
        if existing.data:
            guide_uuid = existing.data[0]["id"]
            supabase.table("build_guides").delete().eq("id", guide_uuid).execute()
            print("✓ Deleted existing guide")
        
        # Create main guide
        guide_uuid = create_guide()
        print(f"✓ Created guide with ID: {guide_uuid}")
        
        # Create sections
        create_sections(guide_uuid)
        print("✓ Created guide sections")
        
        # Create queries
        query_ids = create_queries(guide_uuid)
        print("✓ Created query templates")
        
        # Create examples
        create_examples(guide_uuid, query_ids)
        print("✓ Created example results")
        
        # Create metrics
        create_metrics(guide_uuid)
        print("✓ Created metric definitions")
        
        print("\n✅ Successfully created Audience Segment Conversions Build Guide!")
        print(f"Guide ID: guide_audience_segment_conversions")
        
    except Exception as e:
        print(f"\n❌ Error creating guide: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()