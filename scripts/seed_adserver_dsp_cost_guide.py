#!/usr/bin/env python3
"""
Seed script for Amazon Ad Server - DSP Media Cost for Attributed Conversions Build Guide
This script creates the comprehensive guide content for analyzing DSP media costs and conversion attribution
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def create_adserver_dsp_cost_guide():
    """Create the Amazon Ad Server - DSP Media Cost for Attributed Conversions guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_adserver_dsp_cost',
            'name': 'Amazon Ad Server - DSP Media Cost for Attributed Conversions',
            'category': 'Cost Analysis',
            'short_description': 'Analyze Amazon DSP media cost and effective bidding prices based on conversions measured by Amazon Ad Server to optimize bid strategies and improve ROI.',
            'tags': ['ad server', 'DSP media cost', 'conversion attribution', 'bid optimization', 'cost analysis', 'ROI', 'winning bid'],
            'icon': 'DollarSign',
            'difficulty_level': 'advanced',
            'estimated_time_minutes': 35,
            'prerequisites': [
                'Amazon DSP campaigns measured in Amazon Ad Server',
                'Amazon Ad Server conversion tracking (Tag Manager or Conversion Activity)',
                'Understanding of bid pricing and media costs',
                'Knowledge of attribution windows'
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
                'title': '1. Introduction',
                'content_markdown': """## 1.1 Purpose

Use this instructional query to analyze Amazon DSP (Amazon DSP) media cost and the effective bidding and winning bid price based on the conversions measured by Amazon Ad Server. It helps to surface total cost per conversion as well as average bid and win price for line items that led to the highest conversion rates. These insights can be used to adjust bidding and targeting tactics in ADSP to win more bids that will result in additional brand site conversions.

## 1.2 Requirements

To use this query template, the AMC instance must have at least one Amazon DSP campaign measured in the Amazon Ad Server and represented in the adserver_traffic data view. The advertiser also needs to use the Amazon Ad Server conversion tracking solutions: Tag Manager or/and Conversion Activity.

## 1.3 Key Benefits

- **Cost Optimization**: Identify the most cost-effective line items and campaigns
- **Bid Strategy Refinement**: Understand the relationship between bid prices and conversion success
- **Attribution Insights**: Track both post-click and post-view conversions with customizable attribution windows
- **Performance Benchmarking**: Compare conversion rates and costs across different line items
- **Budget Allocation**: Make data-driven decisions about budget distribution""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Tables Used

| Table | Description | Key Fields |
|-------|-------------|------------|
| **dsp_impressions** | Contains bid price, winning bid cost and total cost information along with Amazon DSP campaign information | `bid_price`, `winning_bid_cost`, `total_cost`, `campaign_id`, `line_item_id` |
| **adserver_traffic** | Contains all impressions and clicks measured by Amazon Ad Server | `advertiser_id`, `campaign_id`, `user_id`, `request_tag`, `impressions`, `clicks` |
| **adserver_conversions** | Contains unattributed Amazon Ad Server conversion activities | `conversion_id`, `conversion_activity_id`, `user_id`, `conversions` |

## 2.2 Data Returned

This query will return post-click and post-view conversions, conversion rate, average bid price, average winning bid cost, and total media cost for Amazon Ad Server conversions attributed to Amazon DSP media measured in Amazon Ad Server. 

**Important Privacy Considerations:**
- Since bid price and winning bid cost have medium sensitivity, they require **100 minimal distinct users** for these metrics to return
- You can reduce the data being queried by filtering to specific advertisers or campaigns
- This allows you to query for a longer time window, which will decrease the chance of metrics being filtered out due to privacy constraints

## 2.3 Query Templates

This guide provides three query templates:

1. **Advertiser and Campaign Exploratory Query** - Identify eligible campaigns with Amazon Ad Server tags
2. **Conversion Activity Exploratory Query** - Identify conversion activities for each advertiser
3. **Main Analysis Query** - Analyze DSP media costs and conversion attribution

Use the exploratory queries first to make informed decisions about the filters to add to the main analysis query.""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': '3. Data Interpretation Instructions',
                'content_markdown': """## 3.1 Example Query Results

Below is a sample output showing DSP campaigns with their line items, conversions, and cost metrics:

| ADSP_campaign | ADSP_line_item | impressions | clicks | post_impression_conversions | post_click_conversions | total_conversions | conversion_rate | dsp_total_cost | avg_bid_price | avg_winning_bid_cost | cost_per_conversion |
|---------------|----------------|-------------|--------|---------------------------|----------------------|------------------|----------------|----------------|---------------|---------------------|-------------------|
| Summer Sale 2024 | Line Item 1 - Retargeting | 350,000 | 2,800 | 3,500 | 1,500 | 5,000 | 1.43% | $2,900.00 | $0.0095 | $0.0082 | $0.58 |
| Summer Sale 2024 | Line Item 2 - Prospecting | 500,000 | 1,200 | 800 | 700 | 1,500 | 0.30% | $2,835.00 | $0.0062 | $0.0055 | $1.89 |
| Summer Sale 2024 | Line Item 3 - Lookalike | 400,000 | 900 | 600 | 400 | 1,000 | 0.25% | $7,880.00 | $0.0210 | $0.0195 | $7.88 |

## 3.2 Metrics Defined

### Key Metrics

| Metric | Description | Calculation/Notes |
|--------|-------------|-------------------|
| **campaign** | Amazon DSP campaign configured with Amazon Ad Server placement | Direct from `dsp_impressions` table |
| **line_item** | Amazon DSP line item configured with Amazon Ad Server placement | Direct from `dsp_impressions` table |
| **impressions** | Number of impressions measured by Amazon Ad Server | Sum of impression events |
| **clicks** | Number of clicks measured by Amazon Ad Server | Sum of click events |
| **post_impression_conversions** | Conversions after viewing an ad (no click) | Attributed within lookback window |
| **post_click_conversions** | Conversions after clicking an ad | Attributed within lookback window |
| **total_conversions** | Total number of conversions | post_impression + post_click |
| **conversion_rate** | Total conversions-to-impressions ratio | (total_conversions / impressions) × 100 |
| **dsp_total_cost** | Total DSP cost for running the campaign | In dollars (converted from millicents) |
| **avg_bid_price** | Average bid price for ads resulting in conversions | In dollars (converted from microcents) |
| **avg_winning_bid_cost** | Average bid winning price for ads resulting in conversions | In dollars (converted from microcents) |
| **cost_per_conversion** | Cost efficiency metric | dsp_total_cost / total_conversions |

### Attribution Logic

- **Attribution Model**: Last touch attribution with customizable lookback window (default 30 days)
- **Post-Campaign Conversions**: Includes conversions that occur after campaign ends, within lookback period
- **Cross-DSP Attribution**: Only returns conversions attributed to Amazon DSP media; non-Amazon DSP conversions are considered but not returned
- **User Journey Tracking**: Matches user IDs between traffic and conversion events to establish attribution

### Currency Conversions

| Field | Original Unit | Conversion Factor | Final Unit |
|-------|--------------|-------------------|------------|
| `total_cost` | Millicents | ÷ 100,000 | Dollars |
| `bid_price` | Microcents | ÷ 100,000,000 | Dollars |
| `winning_bid_cost` | Microcents | ÷ 100,000,000 | Dollars |

## 3.3 Insights and Data Interpretation

### Performance Analysis

Based on the example data above:

**Line Item 1 (Retargeting):**
- **Highest conversion rate**: 1.43%
- **Lowest cost per conversion**: $0.58
- **Insight**: Retargeting audiences show strong performance with efficient cost structure
- **Recommendation**: Increase budget allocation to this line item

**Line Item 2 (Prospecting):**
- **Moderate conversion rate**: 0.30%
- **Reasonable cost per conversion**: $1.89
- **Insight**: Lower bid prices correlate with lower conversion rates but acceptable efficiency
- **Recommendation**: Test incremental bid increases to improve win rate

**Line Item 3 (Lookalike):**
- **Lowest conversion rate**: 0.25%
- **Highest cost per conversion**: $7.88
- **Insight**: Higher bid prices aren't translating to better performance
- **Recommendation**: Review targeting criteria and creative relevance

### Strategic Recommendations

1. **Bid Optimization Strategy**
   - Monitor the relationship between `avg_winning_bid_cost` and `conversion_rate`
   - Line items with win/bid ratio > 0.85 may benefit from higher bids
   - Line items with win/bid ratio < 0.70 may be overbidding

2. **Budget Allocation Framework**
   - Prioritize line items with cost per conversion below target CPA
   - Shift budget from underperforming segments to high-converting ones
   - Consider dayparting based on conversion patterns

3. **Attribution Window Considerations**
   - Post-impression conversions typically require longer windows (7-30 days)
   - Post-click conversions often convert within 1-7 days
   - Adjust windows based on your product purchase cycle""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'implementation',
                'title': '4. Implementation Guide',
                'content_markdown': """## 4.1 Step-by-Step Implementation

### Step 1: Run Exploratory Queries

Before running the main analysis, use the exploratory queries to:
1. Identify eligible campaigns with Amazon Ad Server tags
2. Verify conversion activity IDs for your advertiser
3. Determine appropriate date ranges based on campaign activity

### Step 2: Configure Main Query Parameters

Update the following sections in the main query:

```sql
-- REQUIRED: Update advertiser ID(s)
WITH advertiser_ids (advertiser_id) AS (
  VALUES
    (11111111)  -- Replace with your advertiser ID
),

-- OPTIONAL: Update campaign ID(s)
campaign_ids (campaign_id) AS (
  VALUES
    (22222222),  -- Replace with your campaign IDs
    (3333333),
    (4444444)
),

-- OPTIONAL: Update conversion activity ID(s)
conversion_activity_ids (conversion_activity_id) AS (
  VALUES
    (55555555)  -- Replace with your conversion activity IDs
)
```

### Step 3: Customize Attribution Settings

Modify the attribution window if needed (default is 30 days):

```sql
-- Change the attribution window (default 30 days)
-- Update both occurrences in the query
FROM TABLE(EXTEND_TIME_WINDOW('adserver_traffic', 'P0D', 'P30D'))
FROM TABLE(EXTEND_TIME_WINDOW('adserver_conversions', 'P0D', 'P30D'))

-- And update the lookback window calculation
match_age BETWEEN 0 AND 30 * 24 * 60 * 60  -- Change 30 to desired days
```

### Step 4: Execute and Validate Results

1. Run the query with a recent time window (last 30-60 days)
2. Verify that bid metrics are returned (requires 100+ distinct users)
3. Check for reasonable conversion rates (typically 0.1% - 5%)
4. Validate cost calculations against known campaign spend

## 4.2 Troubleshooting Common Issues

### Issue: Bid Metrics Not Returning

**Problem**: `avg_bid_price` and `avg_winning_bid_cost` show as NULL

**Solution**:
- Extend the time window to capture more users
- Filter to specific high-traffic campaigns
- Verify minimum 100 distinct users requirement is met

### Issue: No Conversions Found

**Problem**: Query returns zero conversions

**Solutions**:
1. Verify conversion tracking is properly implemented
2. Check that conversion activity IDs are correct
3. Extend the attribution window
4. Confirm advertiser_id matches between tables

### Issue: Unexpected High Costs

**Problem**: Cost per conversion seems unrealistically high

**Solutions**:
1. Verify currency conversion calculations
2. Check for proper filtering (may be including wrong campaigns)
3. Validate that conversion events are being captured correctly
4. Review attribution window settings

## 4.3 Optimization Tips

### Query Performance

- **Filter Early**: Apply advertiser and campaign filters as early as possible
- **Limit Time Range**: Start with shorter periods (30 days) then expand
- **Use Indexes**: Ensure proper indexes on `user_id`, `advertiser_id`, and `request_tag`

### Data Quality

- **Regular Validation**: Compare AMC results with Amazon Ad Server reports
- **Monitor Discrepancies**: Track differences between attributed and total conversions
- **Test Attribution**: Validate attribution logic with known conversion paths""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            }
        ]
        
        # Insert sections
        for section in sections:
            section_response = client.table('build_guide_sections').insert(section).execute()
            if not section_response.data:
                logger.error(f"Failed to create section: {section['section_id']}")
            else:
                logger.info(f"Created section: {section['title']}")
        
        # Create queries
        queries = [
            {
                'guide_id': guide_id,
                'query_type': 'exploratory',
                'title': 'Advertiser and Campaign Exploratory Query',
                'description': 'Explore Amazon Ad Server campaigns eligible for this analysis (campaigns that have Amazon Ad Server tags implemented for serving or measurement in Amazon DSP). Returns start and end dates to help define date range.',
                'sql_query': """-- Instructional query: Advertiser and Campaign Exploratory Query for 'Amazon Ad Server - Amazon DSP Media Cost for Amazon Ad Server Attributed Conversions'
SELECT
  adserver.advertiser,
  adserver.advertiser_id,
  adserver.campaign,
  adserver.campaign_id,
  adserver.campaign_start_date,
  adserver.campaign_end_date,
  dsp.campaign,
  dsp.campaign_id,
  SUM(adserver.impressions) AS adserver_imps,
  SUM(dsp.impressions) AS dsp_imps
FROM
  adserver_traffic adserver
  JOIN dsp_impressions dsp ON adserver.request_tag = dsp.request_tag
GROUP BY
  1, 2, 3, 4, 5, 6, 7, 8""",
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'query_type': 'exploratory',
                'title': 'Conversion Activity Exploratory Query',
                'description': 'Use this query to identify conversion activity IDs relevant to each advertiser in the instance.',
                'sql_query': """-- Instructional query: Conversion Activity Exploratory Query for 'Amazon Ad Server - Amazon DSP Media Cost for Amazon Ad Server Attributed Conversions'
SELECT
  advertiser,
  advertiser_id,
  conversion_activity,
  conversion_activity_id,
  SUM(conversions) AS total_conversions
FROM
  adserver_conversions
GROUP BY
  1, 2, 3, 4""",
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'query_type': 'main_analysis',
                'title': 'DSP Media Cost for Ad Server Attributed Conversions',
                'description': 'Main query returning post-click and post-view conversions, conversion rate, average bid price, average winning bid cost, and total media cost for Amazon Ad Server conversions attributed to Amazon DSP media.',
                'sql_query': """-- Instructional Query: Amazon Ad Server - Amazon DSP Media Cost for Amazon Ad Server Attributed Conversions
/*This query will return post-click and post-view conversions, conversion rate, 
 average bid price, average winning bid cost, and total media cost for Amazon Ad Server conversions
 attributed to Amazon DSP media measured in Amazon Ad Server.*/
 
/* REQUIRED UPDATE advertiser ID(s) */
WITH advertiser_ids (advertiser_id) AS (
  VALUES
    (11111111)
),

/*OPTIONAL UPDATE campaign ID(s).
 If you update this section, you must uncomment the campaign_id WHERE clause 
 in two sections. Search 'UPDATE campaign_id' */
campaign_ids (campaign_id) AS (
  VALUES
    (22222222),
    (3333333),
    (4444444)
),

/* OPTIONAL UPDATE conversion activity ID(s).
 If you update this section, you must uncomment the conversion_activity_ids 
 WHERE clause. Search 'UPDATE conversion_activity_id' */
conversion_activity_ids (conversion_activity_id) AS (
  VALUES
    (55555555)
),

-- gather impressions and clicks --
traffic_cost AS (
  SELECT
    t.advertiser_id,
    t.advertiser,
    t.campaign_id,
    t.campaign,
    d.line_item,
    d.line_item_id,
    t.user_id AS user_reach_id,
    t.request_tag,
    d.total_cost,
    t.impressions,
    t.clicks
  FROM
    adserver_traffic t -- will drop all rows without a match
    JOIN dsp_impressions d ON t.request_tag = d.request_tag
  WHERE
    t.advertiser_id IN (
      SELECT advertiser_id FROM advertiser_ids
    )
    AND (t.impressions = 1 OR t.clicks = 1)
),

/* Calculating conversions. Prepare traffic data set that include an extra 30 
 days of traffic post report end date to be used later to filter out conversions 
 that attributed to traffic that is not within the reporting period */
traffic AS (
  -- Read impression or clicks events.
  SELECT
    advertiser_id,
    advertiser,
    campaign_id,
    campaign,
    clicks,
    event_dt_utc AS traffic_dt,
    event_date_utc,
    impressions,
    user_id,
    request_tag
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
    TABLE(EXTEND_TIME_WINDOW('adserver_traffic', 'P0D', 'P30D'))
  WHERE
    advertiser_id IN (SELECT advertiser_id FROM advertiser_ids)
    AND (clicks = 1 OR impressions = 1)
),

matched AS (
  SELECT
    t.advertiser_id,
    t.advertiser,
    t.campaign_id,
    t.campaign,
    c.conversion_id,
    c.conversion_activity_id,
    c.conversion_activity,
    c.conversions,
    c.user_id,
    t.request_tag,
    t.traffic_dt,
    t.impressions,
    t.clicks,
    -- Determine a match age between the traffic event and conversion event
    SECONDS_BETWEEN(t.traffic_dt, c.event_dt) AS match_age
    /* Conversion events that occurred up to 30 days after the reporting end date 
     will be attributed to the traffic within the reporting date range */
    /* OPTIONAL UPDATE: Change the attribution window from the following default 30 days 
     to another, and update the same value to 'adserver_traffic' extended time period above */
  FROM
    TABLE(EXTEND_TIME_WINDOW('adserver_conversions', 'P0D', 'P30D')) c
    INNER JOIN traffic t ON c.user_id = t.user_id
    AND c.advertiser_id = t.advertiser_id
  WHERE
    t.advertiser_id IN (SELECT advertiser_id FROM advertiser_ids)
    /* OPTIONAL UPDATE conversion_activity_id: 
     Uncomment the line below if you used conversion_activity filter 
     in the beginning of the query */
    -- AND conversion_activity_id IN (SELECT conversion_activity_id FROM conversion_activity_ids)
),

ranked AS (
  SELECT
    conversion_activity_id,
    conversion_activity,
    advertiser_id,
    advertiser,
    campaign_id,
    campaign,
    conversion_id,
    user_id,
    request_tag,
    traffic_dt,
    impressions,
    clicks,
    -- Rank the match based on match type and then age.
    ROW_NUMBER() OVER(
      PARTITION BY conversion_id
      ORDER BY match_age
    ) AS match_rank
  FROM
    matched
  WHERE
    -- Define look back window for impressions and clicks
    match_age BETWEEN 0 AND 30 * 24 * 60 * 60 -- [* First number X of the expression 'X * 24 * 60 * 60' can be changed to a desired number. In this example, lookback window is 30 days *]
),

attributed_conversions AS (
  SELECT
    advertiser_id,
    advertiser,
    campaign_id,
    campaign,
    user_id,
    impressions,
    clicks,
    request_tag
  FROM
    ranked
  WHERE
    -- keep only conversions with winners that happened in the report time range.
    traffic_dt > BUILT_IN_PARAMETER('TIME_WINDOW_START')
    AND traffic_dt < BUILT_IN_PARAMETER('TIME_WINDOW_END')
    AND
    /*OPTIONAL UPDATE campaign_id: Uncomment the line below if you used campaign filter in the 
     beginning of the query */
    -- campaign_id IN (SELECT campaign_id FROM campaign_ids) and
    -- Filter to the last touch event
    match_rank = 1
),

conversions_bid AS (
  SELECT
    c.advertiser_id,
    c.advertiser,
    c.campaign_id,
    c.campaign,
    d.line_item_id,
    d.line_item,
    c.user_id,
    c.request_tag,
    d.bid_price,
    d.winning_bid_cost,
    c.impressions AS post_impression_conversions,
    c.clicks AS post_click_conversions
  FROM
    attributed_conversions c
    JOIN dsp_impressions d ON c.request_tag = d.request_tag
),

combined AS (
  SELECT
    t.advertiser_id,
    t.advertiser,
    t.campaign_id,
    t.campaign,
    t.line_item,
    t.line_item_id,
    c.bid_price,
    c.winning_bid_cost,
    t.total_cost,
    t.impressions,
    t.clicks,
    c.post_impression_conversions,
    c.post_click_conversions
  FROM
    traffic_cost t
    LEFT JOIN conversions_bid c ON t.request_tag = c.request_tag
    AND t.campaign_id = c.campaign_id
)

SELECT
  campaign AS ADSP_campaign,
  line_item AS ADSP_line_item,
  SUM(impressions) impressions,
  SUM(clicks) clicks,
  SUM(post_impression_conversions) AS post_impression_conversions,
  SUM(post_click_conversions) AS post_click_conversions,
  (SUM(post_impression_conversions) + SUM(post_click_conversions)) AS total_conversions,
  (SUM(post_impression_conversions + post_click_conversions) / SUM(impressions)) * 100 AS conversion_rate,
  ---- total_cost is reported in millicents. Divide by 100,000 to get the cost in dollars/your currency
  SUM(total_cost / 100000) dsp_total_cost,
  ---- bid_price and winning_bid_cost are reported in microcents. Divide by 100,000,000 to get the cost in dollars/your currency.
  AVG(bid_price / 100000000) avg_bid_price,
  AVG(winning_bid_cost / 100000000) avg_winning_bid_cost,
  (SUM(total_cost / 100000) / (SUM(post_impression_conversions) + SUM(post_click_conversions))) AS cost_per_conversion
FROM
  combined
GROUP BY
  1, 2""",
                'display_order': 3
            }
        ]
        
        # Insert queries
        for query in queries:
            query_response = client.table('build_guide_queries').insert(query).execute()
            if not query_response.data:
                logger.error(f"Failed to create query: {query['title']}")
            else:
                logger.info(f"Created query: {query['title']}")
        
        # Create example data
        # First, get the main query ID for the example
        query_response = client.table('build_guide_queries').select('id').eq('guide_id', guide_id).eq('query_type', 'main_analysis').execute()
        if query_response.data and len(query_response.data) > 0:
            main_query_id = query_response.data[0]['id']
        else:
            logger.error("Could not find main query ID for examples")
            main_query_id = None
        
        examples = [
            {
                'guide_query_id': main_query_id,
                'example_name': 'Campaign Performance Analysis',
                'sample_data': json.dumps({
                    'rows': [
                        {
                            'ADSP_campaign': 'Summer Sale 2024',
                            'ADSP_line_item': 'Line Item 1 - Retargeting',
                            'impressions': 350000,
                            'clicks': 2800,
                            'post_impression_conversions': 3500,
                            'post_click_conversions': 1500,
                            'total_conversions': 5000,
                            'conversion_rate': 1.43,
                            'dsp_total_cost': 2900.00,
                            'avg_bid_price': 0.0095,
                            'avg_winning_bid_cost': 0.0082,
                            'cost_per_conversion': 0.58
                        },
                        {
                            'ADSP_campaign': 'Summer Sale 2024',
                            'ADSP_line_item': 'Line Item 2 - Prospecting',
                            'impressions': 500000,
                            'clicks': 1200,
                            'post_impression_conversions': 800,
                            'post_click_conversions': 700,
                            'total_conversions': 1500,
                            'conversion_rate': 0.30,
                            'dsp_total_cost': 2835.00,
                            'avg_bid_price': 0.0062,
                            'avg_winning_bid_cost': 0.0055,
                            'cost_per_conversion': 1.89
                        },
                        {
                            'ADSP_campaign': 'Summer Sale 2024',
                            'ADSP_line_item': 'Line Item 3 - Lookalike',
                            'impressions': 400000,
                            'clicks': 900,
                            'post_impression_conversions': 600,
                            'post_click_conversions': 400,
                            'total_conversions': 1000,
                            'conversion_rate': 0.25,
                            'dsp_total_cost': 7880.00,
                            'avg_bid_price': 0.0210,
                            'avg_winning_bid_cost': 0.0195,
                            'cost_per_conversion': 7.88
                        }
                    ]
                }),
                'interpretation_markdown': """### Key Insights from the Analysis:

**Line Item 1 - Retargeting Performance:**
- **Highest conversion rate** at 1.43%, indicating strong audience relevance
- **Lowest cost per conversion** at $0.58, demonstrating excellent efficiency
- Win/bid ratio of 0.86 (0.0082/0.0095) suggests competitive but efficient bidding
- **Recommendation**: Increase budget allocation to maximize high-performing segment

**Line Item 2 - Prospecting Performance:**
- Moderate conversion rate of 0.30% typical for prospecting audiences
- Reasonable cost per conversion at $1.89
- Lower bid prices correlating with lower conversion rates
- Win/bid ratio of 0.89 indicates good bid efficiency
- **Recommendation**: Test 10-15% bid increases to improve win rate while monitoring CPA

**Line Item 3 - Lookalike Performance:**
- Lowest conversion rate at 0.25% despite highest bid prices
- Highest cost per conversion at $7.88, above typical target CPA
- Win/bid ratio of 0.93 suggests potential overbidding
- **Recommendation**: Review audience quality and creative relevance; consider reducing bids

### Strategic Optimization Recommendations:

1. **Budget Reallocation**: Shift 30% of Line Item 3 budget to Line Item 1
2. **Bid Optimization**: Implement dayparting based on conversion patterns
3. **Attribution Review**: Consider extending window for high-consideration products
4. **Testing Framework**: A/B test bid adjustments in 10% increments""",
                'display_order': 1
            }
        ]
        
        # Insert examples
        for example in examples:
            example_response = client.table('build_guide_examples').insert(example).execute()
            if not example_response.data:
                logger.error(f"Failed to create example: {example['example_name']}")
            else:
                logger.info(f"Created example: {example['example_name']}")
        
        # Create metrics
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'campaign',
                'display_name': 'Campaign',
                'metric_type': 'dimension',
                'definition': 'Amazon DSP campaign configured with Amazon Ad Server placement. Direct from dsp_impressions table.',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'line_item',
                'display_name': 'Line Item',
                'metric_type': 'dimension',
                'definition': 'Amazon DSP line item configured with Amazon Ad Server placement. Direct from dsp_impressions table.',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'impressions',
                'display_name': 'Impressions',
                'metric_type': 'metric',
                'definition': 'Number of impressions measured by Amazon Ad Server. Calculated as SUM(impressions).',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'clicks',
                'display_name': 'Clicks',
                'metric_type': 'metric',
                'definition': 'Number of clicks measured by Amazon Ad Server. Calculated as SUM(clicks).',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'post_impression_conversions',
                'display_name': 'Post-Impression Conversions',
                'metric_type': 'metric',
                'definition': 'Conversions after viewing an ad without clicking. Calculated as SUM(post_impression_conversions).',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'post_click_conversions',
                'display_name': 'Post-Click Conversions',
                'metric_type': 'metric',
                'definition': 'Conversions after clicking an ad. Calculated as SUM(post_click_conversions).',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_conversions',
                'display_name': 'Total Conversions',
                'metric_type': 'metric',
                'definition': 'Total number of conversions. Calculated as post_impression_conversions + post_click_conversions.',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate',
                'display_name': 'Conversion Rate',
                'metric_type': 'metric',
                'definition': 'Total conversions-to-impressions ratio as percentage. Calculated as (total_conversions / impressions) × 100.',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'dsp_total_cost',
                'display_name': 'DSP Total Cost',
                'metric_type': 'metric',
                'definition': 'Total DSP cost for running the campaign in dollars. Calculated as SUM(total_cost / 100000) to convert from millicents.',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'avg_bid_price',
                'display_name': 'Average Bid Price',
                'metric_type': 'metric',
                'definition': 'Average bid price for ads resulting in conversions. Calculated as AVG(bid_price / 100000000) to convert from microcents to dollars.',
                'display_order': 10
            },
            {
                'guide_id': guide_id,
                'metric_name': 'avg_winning_bid_cost',
                'display_name': 'Average Winning Bid Cost',
                'metric_type': 'metric',
                'definition': 'Average winning bid price for ads resulting in conversions. Calculated as AVG(winning_bid_cost / 100000000) to convert from microcents to dollars.',
                'display_order': 11
            },
            {
                'guide_id': guide_id,
                'metric_name': 'cost_per_conversion',
                'display_name': 'Cost Per Conversion',
                'metric_type': 'metric',
                'definition': 'Cost efficiency metric showing spend per conversion. Calculated as dsp_total_cost / total_conversions.',
                'display_order': 12
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            metric_response = client.table('build_guide_metrics').insert(metric).execute()
            if not metric_response.data:
                logger.error(f"Failed to create metric: {metric['metric_name']}")
            else:
                logger.info(f"Created metric: {metric['metric_name']}")
        
        logger.info("Successfully created Amazon Ad Server - DSP Media Cost guide")
        return True
        
    except Exception as e:
        logger.error(f"Error creating guide: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_adserver_dsp_cost_guide()
    if success:
        print("✅ Successfully created Amazon Ad Server - DSP Media Cost for Attributed Conversions guide")
    else:
        print("❌ Failed to create guide")
        sys.exit(1)