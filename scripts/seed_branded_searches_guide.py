#!/usr/bin/env python3
"""
Seed script for Ad-attributed Branded Searches Analysis Build Guide
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

def create_branded_searches_guide():
    """Create the Ad-attributed Branded Searches Analysis guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_branded_searches_analysis',
            'name': 'Ad-attributed Branded Searches Analysis',
            'category': 'Brand Measurement',
            'short_description': 'Analyze how DSP advertising campaigns influence branded search behavior on Amazon, measuring the impact of ads on brand awareness and consideration.',
            'tags': ['Brand awareness', 'DSP campaigns', 'Search behavior', 'Attribution analysis', 'Brand measurement'],
            'icon': 'Search',
            'difficulty_level': 'beginner',
            'estimated_time_minutes': 25,
            'prerequisites': [
                'DSP campaigns only - Branded search keywords are exclusive to DSP campaigns',
                'ASIN tracking required - Campaigns must have ASINs tracked',
                'Feature enablement - Must be enabled via entity settings in advertiser\'s DSP user account',
                'Contact your Amazon point of contact to learn more about enabling this feature'
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

Branded searches is an ad-attributed metric that provides insight into how your DSP advertising campaigns affect customer behavior for branded search terms. It measures the number of times a branded keyword was searched on Amazon based on keywords generated from the featured ASINs in your campaign, attributed to both ad impressions and clicks.

**How it works:**
- Keywords are determined from the brands of all ASINs tracked by your campaign
- Variants of brand keywords are automatically generated (e.g., "Kitchen Smart Inc." → "Kitchen Smart")
- Using the standard 14-day last-touch attribution model, shopper's search queries are recorded as ad-attributed branded searches
- Note: Significant misspellings and sub-brands aren't captured

**Availability:**
- Available to all DSP advertisers
- Also found in DSP performance reports, audience segmentation, and downloadable reports

## 1.2 Requirements

- **DSP campaigns only** - Branded search keywords are exclusive to DSP campaigns
- **ASIN tracking required** - Campaigns must have ASINs tracked
- **Feature enablement** - Must be enabled via entity settings in advertiser's DSP user account
- Contact your Amazon point of contact to learn more about enabling this feature""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'understanding',
                'title': '2. Understanding Branded Searches',
                'content_markdown': """## 2.1 What are Ad-attributed Branded Searches?

Ad-attributed branded searches represent a powerful signal of brand interest and consideration. When shoppers see your ads and then search for your brand on Amazon, it indicates:
- **Increased brand awareness** - Your ads successfully communicated your brand
- **Active consideration** - Shoppers are actively seeking your products
- **Purchase intent** - Branded searches often lead to higher conversion rates

## 2.2 Attribution Model

| Component | Description |
|-----------|------------|
| **Attribution Window** | 14 days last-touch |
| **Attribution Types** | Both impressions and clicks |
| **Keyword Matching** | Brand variants with minimal transformations |
| **Data Source** | `amazon_attributed_events_by_conversion_time` |

The attribution model captures both direct responses (clicks) and view-through impact (impressions), providing a comprehensive view of how your ads drive brand interest.""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'key_metrics',
                'title': '3. Key Metrics',
                'content_markdown': """## 3.1 Core Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Branded Searches** | Count of attributed searches | Volume of brand interest generated |
| **Branded Search Rate** | Branded Searches / Impressions | Efficiency of ads at driving brand searches |
| **Cost per Branded Search** | Impression Cost / Branded Searches | Investment required per brand search |

## 3.2 Benchmark Guidance

**Typical Performance Ranges:**
- **Branded Search Rate**: 0.01% - 0.5% (varies by category)
- **Cost per Branded Search**: $0.50 - $5.00 (depends on competition)

Higher rates indicate stronger brand resonance and ad effectiveness.

### Industry Benchmarks by Category

| Category | Typical Search Rate | Typical Cost per Search |
|----------|-------------------|------------------------|
| Electronics | 0.05% - 0.3% | $1.00 - $3.00 |
| Beauty & Personal Care | 0.08% - 0.5% | $0.50 - $2.00 |
| Home & Kitchen | 0.03% - 0.2% | $0.75 - $2.50 |
| Fashion | 0.02% - 0.15% | $1.50 - $4.00 |
| Grocery | 0.01% - 0.1% | $0.25 - $1.50 |

*Note: These are general ranges and can vary significantly based on brand maturity, campaign quality, and competitive landscape.*""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'query_implementation',
                'title': '4. Query Implementation',
                'content_markdown': """## 4.1 Basic Branded Keywords Query

This query extracts branded search keywords and their volumes:

```sql
-- Instructional Query: Ad-attributed Branded Searches
SELECT
  campaign_id,
  campaign,
  -- The keyword is stored under 'tracked_item'. 
  -- The substring function removes the leading string 'keyword#'
  SUBSTRING(tracked_item, 9, 250) AS keyword,
  SUM(conversions) AS number_of_branded_searches
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  tracked_item SIMILAR TO '^keyword.*'
GROUP BY
  1, 2, 3
```

**Query Explanation:**
- `tracked_item` contains the branded keyword prefixed with "keyword#"
- `SUBSTRING(tracked_item, 9, 250)` extracts the actual keyword
- `conversions` represents the count of branded searches
- The `SIMILAR TO '^keyword.*'` filter ensures we only get keyword events

## 4.2 Advanced Metrics Query

This query calculates branded search rate and cost per branded search:

```sql
-- Instructional Query: Branded Search Rate and Cost Analysis
WITH imp_branded AS (
  SELECT
    campaign_id,
    campaign,
    SUM(impressions) AS impressions,
    -- impression_cost and total_cost are reported in millicents
    -- Divide by 100,000 to get the cost in dollars/your currency
    SUM(impression_cost / 100000) AS impression_cost,
    0 AS number_of_branded_searches
  FROM
    dsp_impressions
  GROUP BY
    1, 2
  UNION ALL
  SELECT
    campaign_id,
    campaign,
    0 AS impressions,
    0 AS impression_cost,
    SUM(conversions) AS number_of_branded_searches
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    tracked_item SIMILAR TO '^keyword.*'
  GROUP BY
    1, 2
)
SELECT
  campaign_id,
  campaign,
  SUM(impressions) AS impressions,
  SUM(impression_cost) AS impression_cost,
  SUM(number_of_branded_searches) AS number_of_branded_searches,
  SUM(number_of_branded_searches) / SUM(impressions) AS branded_search_rate,
  SUM(impression_cost) / SUM(number_of_branded_searches) AS cost_per_branded_search
FROM
  imp_branded
GROUP BY
  1, 2
```

**Query Explanation:**
- Uses a CTE to combine impression data with branded search data
- Calculates efficiency metrics by dividing searches by impressions
- Converts millicents to dollars for cost calculations
- Groups by campaign for campaign-level analysis""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_interpretation',
                'title': '5. Data Interpretation',
                'content_markdown': """## 5.1 Example Results

**Sample Output - Basic Query:**

| campaign_id | campaign | keyword | number_of_branded_searches |
|------------|----------|---------|----------------------------|
| 12345 | Summer Launch | kitchen smart | 1,250 |
| 12345 | Summer Launch | kitchen smart inc | 875 |
| 12345 | Summer Launch | kitchensmart | 425 |
| 67890 | Holiday Push | kitchen smart | 3,200 |
| 67890 | Holiday Push | smart kitchen | 1,100 |

**Sample Output - Advanced Query:**

| campaign_id | campaign | impressions | impression_cost | number_of_branded_searches | branded_search_rate | cost_per_branded_search |
|------------|----------|-------------|-----------------|---------------------------|--------------------|-----------------------|
| 12345 | Summer Launch | 1,000,000 | $5,000 | 2,550 | 0.00255 | $1.96 |
| 67890 | Holiday Push | 2,500,000 | $12,500 | 8,750 | 0.00350 | $1.43 |
| 78901 | Brand Awareness | 1,800,000 | $7,200 | 3,600 | 0.00200 | $2.00 |

## 5.2 Analysis Insights

**Strong Performance Indicators:**
- Branded search rate above category average (see benchmarks in Section 3)
- Decreasing cost per branded search over time
- High volume of unique brand variants searched
- Consistent growth in branded searches month-over-month

**Optimization Opportunities:**
- **Low branded search rate** → Review creative messaging for brand prominence
- **High cost per search** → Consider audience targeting refinement
- **Limited keyword variants** → Evaluate product diversity in campaigns
- **Declining search volume** → Refresh creative or adjust frequency caps

### Interpreting Keyword Variations

The variety of keyword variations provides insights into brand perception:
- **Exact brand matches** ("kitchen smart") indicate strong brand recall
- **Partial matches** ("smart") suggest brand elements are memorable
- **Combined variations** ("kitchen smart inc") show full brand awareness
- **Misspellings** (if captured) can indicate brand pronunciation challenges""",
                'display_order': 5,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': '6. Best Practices',
                'content_markdown': """## 6.1 Campaign Setup

1. **Enable branded search tracking** before campaign launch
   - No retroactive data available if not enabled from the start
   - Work with your Amazon account team to enable the feature
   
2. **Include multiple ASINs** to capture broader brand interest
   - More ASINs = more comprehensive brand keyword generation
   - Include flagship products and new launches
   
3. **Use brand-focused creative** to reinforce brand messaging
   - Prominent logo placement
   - Clear brand name in headlines
   - Consistent brand voice and visual identity
   
4. **Set appropriate frequency caps** to avoid oversaturation
   - Balance between awareness and annoyance
   - Typically 3-5 impressions per day per user

## 6.2 Analysis Recommendations

1. **Compare across campaigns** to identify top performers
   - Segment by campaign objective (awareness vs. consideration)
   - Analyze by creative format (video vs. display)
   
2. **Track trends over time** to measure brand building progress
   - Weekly or monthly trending reports
   - Seasonal pattern identification
   
3. **Segment by audience** to understand which segments show highest brand affinity
   - New-to-brand vs. existing customers
   - Demographic and behavioral segments
   
4. **Correlate with sales** to validate branded search quality
   - Compare branded search lift with sales lift
   - Calculate branded search to purchase conversion rates

## 6.3 Common Pitfalls to Avoid

❌ **Don't:**
- Launch campaigns without enabling branded search tracking first
- Ignore seasonal variations in branded search behavior
- Compare across categories without normalization
- Over-optimize for branded searches at expense of conversions
- Rely solely on branded searches without considering other KPIs

✅ **Do:**
- Enable tracking before campaign launch
- Account for seasonality in analysis
- Use category benchmarks for comparison
- Balance brand building with performance goals
- Consider branded searches as part of full-funnel strategy

## 6.4 Optimization Strategies

### Creative Optimization
- Test brand prominence in different positions
- A/B test with and without brand messaging
- Use dynamic creative to personalize brand presentation

### Audience Optimization
- Focus on high-value segments showing brand affinity
- Expand to lookalike audiences of brand searchers
- Exclude recent purchasers to find new brand considerers

### Budget Optimization
- Allocate more budget to campaigns with efficient branded search generation
- Daypart optimization based on branded search patterns
- Seasonal budget adjustments for brand moments""",
                'display_order': 6,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'advanced_use_cases',
                'title': '7. Advanced Use Cases',
                'content_markdown': """## 7.1 Brand Launch Measurement

Track branded search lift during new product or brand launches to measure awareness building.

**Key Metrics to Track:**
- Week-over-week branded search growth
- Share of voice vs. competitors
- New-to-brand searcher percentage
- Geographic distribution of branded searches

**Success Indicators:**
- Exponential growth in first 4 weeks
- Sustained search volume post-launch
- Increasing keyword variety over time

## 7.2 Competitive Analysis

Compare your branded search rates against category benchmarks to assess relative brand strength.

**Analysis Framework:**
1. Calculate your branded search rate
2. Compare to category benchmarks (Section 3.2)
3. Identify gap to category leaders
4. Set realistic improvement targets

**Competitive Intelligence:**
- High branded search rate = strong brand differentiation
- Growing rate over time = increasing brand equity
- Rate stability = consistent brand presence

## 7.3 Creative Testing

Use branded search rate as a KPI for creative A/B tests to identify messaging that drives brand interest.

**Test Variables:**
- Brand logo size and placement
- Brand name in headline vs. body copy
- Brand story vs. product features
- Celebrity endorsement impact

**Measurement Approach:**
- Run tests for minimum 2 weeks
- Ensure statistical significance (>1000 impressions per variant)
- Control for audience and placement variables
- Measure both immediate and delayed impact

## 7.4 Full-Funnel Attribution

Connect branded searches to downstream metrics for complete performance picture.

**Attribution Chain:**
1. **Impression** → Branded Search (this guide)
2. **Branded Search** → Product Page View
3. **Product Page View** → Add to Cart
4. **Add to Cart** → Purchase

**Insights:**
- Calculate branded search to purchase conversion rate
- Identify drop-off points in the funnel
- Optimize for high-value branded searchers
- Measure lifetime value of branded search converters

## 7.5 Seasonal Strategy

Leverage branded searches for seasonal campaigns and tentpole events.

**Pre-Season (4-6 weeks before):**
- Build brand awareness with broad targeting
- Focus on branded search volume growth

**Peak Season:**
- Maximize branded search efficiency
- Convert brand interest to sales

**Post-Season:**
- Maintain brand presence
- Retarget branded searchers who didn't convert

## 7.6 Cross-Channel Integration

Use branded search data to inform broader marketing strategy.

**Applications:**
- Inform SEO keyword strategy
- Guide content marketing topics
- Identify brand partnership opportunities
- Validate offline campaign impact""",
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
                'title': 'Basic Branded Keywords Query',
                'description': 'Extract branded search keywords and their volumes from your DSP campaigns.',
                'sql_query': """-- Instructional Query: Ad-attributed Branded Searches
SELECT
  campaign_id,
  campaign,
  -- The keyword is stored under 'tracked_item'. 
  -- The substring function removes the leading string 'keyword#'
  SUBSTRING(tracked_item, 9, 250) AS keyword,
  SUM(conversions) AS number_of_branded_searches
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  tracked_item SIMILAR TO '^keyword.*'
  AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
GROUP BY
  1, 2, 3
ORDER BY
  number_of_branded_searches DESC
LIMIT {{result_limit}}""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for branded search data'
                    },
                    'result_limit': {
                        'type': 'integer',
                        'default': 100,
                        'description': 'Maximum number of results to return'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'result_limit': 100
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query shows which brand keywords are being searched and their volumes. Focus on the variety of keywords to understand brand perception.'
            },
            {
                'guide_id': guide_id,
                'title': 'Branded Search Rate and Cost Analysis',
                'description': 'Calculate branded search rate and cost per branded search to measure efficiency.',
                'sql_query': """-- Instructional Query: Branded Search Rate and Cost Analysis
WITH imp_branded AS (
  SELECT
    campaign_id,
    campaign,
    SUM(impressions) AS impressions,
    -- impression_cost and total_cost are reported in millicents
    -- Divide by 100,000 to get the cost in dollars/your currency
    SUM(impression_cost / 100000) AS impression_cost,
    0 AS number_of_branded_searches
  FROM
    dsp_impressions
  WHERE
    event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
  GROUP BY
    1, 2
  UNION ALL
  SELECT
    campaign_id,
    campaign,
    0 AS impressions,
    0 AS impression_cost,
    SUM(conversions) AS number_of_branded_searches
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    tracked_item SIMILAR TO '^keyword.*'
    AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
  GROUP BY
    1, 2
)
SELECT
  campaign_id,
  campaign,
  SUM(impressions) AS impressions,
  ROUND(SUM(impression_cost), 2) AS impression_cost,
  SUM(number_of_branded_searches) AS number_of_branded_searches,
  ROUND(CAST(SUM(number_of_branded_searches) AS DOUBLE) / CAST(SUM(impressions) AS DOUBLE), 6) AS branded_search_rate,
  ROUND(SUM(impression_cost) / NULLIF(SUM(number_of_branded_searches), 0), 2) AS cost_per_branded_search
FROM
  imp_branded
GROUP BY
  1, 2
HAVING
  SUM(impressions) > {{min_impressions}}
ORDER BY
  branded_search_rate DESC""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for data'
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'default': 10000,
                        'description': 'Minimum impressions threshold for campaigns to include'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'min_impressions': 10000
                },
                'display_order': 2,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Compare branded search rates across campaigns. Rates above 0.002 (0.2%) are generally strong. Monitor cost per branded search for efficiency.'
            },
            {
                'guide_id': guide_id,
                'title': 'Branded Search Trend Analysis',
                'description': 'Analyze branded search trends over time to understand momentum and seasonality.',
                'sql_query': """-- Instructional Query: Branded Search Trend Analysis
WITH daily_metrics AS (
  SELECT
    event_dt,
    campaign_id,
    campaign,
    SUM(impressions) AS daily_impressions,
    0 AS daily_branded_searches
  FROM
    dsp_impressions
  WHERE
    event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
  GROUP BY
    1, 2, 3
  UNION ALL
  SELECT
    event_dt,
    campaign_id,
    campaign,
    0 AS daily_impressions,
    SUM(conversions) AS daily_branded_searches
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    tracked_item SIMILAR TO '^keyword.*'
    AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
  GROUP BY
    1, 2, 3
),
aggregated AS (
  SELECT
    event_dt,
    campaign_id,
    campaign,
    SUM(daily_impressions) AS impressions,
    SUM(daily_branded_searches) AS branded_searches,
    CASE 
      WHEN SUM(daily_impressions) > 0 
      THEN CAST(SUM(daily_branded_searches) AS DOUBLE) / CAST(SUM(daily_impressions) AS DOUBLE)
      ELSE 0 
    END AS search_rate
  FROM
    daily_metrics
  GROUP BY
    1, 2, 3
)
SELECT
  DATE_TRUNC('{{time_granularity}}', event_dt) AS period,
  campaign,
  SUM(impressions) AS total_impressions,
  SUM(branded_searches) AS total_branded_searches,
  ROUND(AVG(search_rate), 6) AS avg_search_rate,
  ROUND(STDDEV(search_rate), 6) AS search_rate_volatility
FROM
  aggregated
GROUP BY
  1, 2
ORDER BY
  1 DESC, 2""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 90,
                        'description': 'Number of days to look back for trend analysis'
                    },
                    'time_granularity': {
                        'type': 'string',
                        'default': 'week',
                        'description': 'Time granularity for aggregation (day, week, month)',
                        'enum': ['day', 'week', 'month']
                    }
                },
                'default_parameters': {
                    'lookback_days': 90,
                    'time_granularity': 'week'
                },
                'display_order': 3,
                'query_type': 'trend_analysis',
                'interpretation_notes': 'Look for consistent growth in branded searches over time. High volatility may indicate inconsistent campaign delivery or creative rotation.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results
                if query['query_type'] == 'exploratory':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Branded Keywords Results',
                        'sample_data': {
                            'rows': [
                                {'campaign_id': '12345', 'campaign': 'Summer Launch', 'keyword': 'kitchen smart', 'number_of_branded_searches': 1250},
                                {'campaign_id': '12345', 'campaign': 'Summer Launch', 'keyword': 'kitchen smart inc', 'number_of_branded_searches': 875},
                                {'campaign_id': '12345', 'campaign': 'Summer Launch', 'keyword': 'kitchensmart', 'number_of_branded_searches': 425},
                                {'campaign_id': '67890', 'campaign': 'Holiday Push', 'keyword': 'kitchen smart', 'number_of_branded_searches': 3200},
                                {'campaign_id': '67890', 'campaign': 'Holiday Push', 'keyword': 'smart kitchen', 'number_of_branded_searches': 1100}
                            ]
                        },
                        'interpretation_markdown': """**Key Observations:**

1. **Brand Variant Recognition**: Multiple variations of "Kitchen Smart" are being searched, indicating strong brand recall
2. **Campaign Performance**: Holiday Push campaign generates 2.5x more branded searches than Summer Launch
3. **Keyword Patterns**: Users search both exact brand name and variations, showing different levels of brand familiarity

**Recommendations:**
- The variety of keyword variations (5 different forms) shows healthy brand awareness
- "kitchen smart" is the dominant search term - ensure this exact match is prominent in creative
- Consider testing creative that reinforces the full brand name "Kitchen Smart Inc" to increase searches for the complete brand""",
                        'insights': [
                            'Holiday Push campaign drives 2.5x more branded searches',
                            'Core brand term "kitchen smart" accounts for 55% of all searches',
                            'Users remember brand in multiple variations, indicating strong recall',
                            'Consider reinforcing exact brand spelling in creative'
                        ],
                        'display_order': 1
                    }
                elif query['query_type'] == 'main_analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Efficiency Analysis Results',
                        'sample_data': {
                            'rows': [
                                {'campaign_id': '12345', 'campaign': 'Summer Launch', 'impressions': 1000000, 'impression_cost': 5000.00, 'number_of_branded_searches': 2550, 'branded_search_rate': 0.00255, 'cost_per_branded_search': 1.96},
                                {'campaign_id': '67890', 'campaign': 'Holiday Push', 'impressions': 2500000, 'impression_cost': 12500.00, 'number_of_branded_searches': 8750, 'branded_search_rate': 0.00350, 'cost_per_branded_search': 1.43},
                                {'campaign_id': '78901', 'campaign': 'Brand Awareness', 'impressions': 1800000, 'impression_cost': 7200.00, 'number_of_branded_searches': 3600, 'branded_search_rate': 0.00200, 'cost_per_branded_search': 2.00},
                                {'campaign_id': '89012', 'campaign': 'Product Launch', 'impressions': 500000, 'impression_cost': 3000.00, 'number_of_branded_searches': 1750, 'branded_search_rate': 0.00350, 'cost_per_branded_search': 1.71}
                            ]
                        },
                        'interpretation_markdown': """**Performance Analysis:**

**Top Performers:**
- **Holiday Push**: Best branded search rate (0.35%) and lowest cost per search ($1.43)
- **Product Launch**: Matching top search rate (0.35%) despite smaller scale

**Optimization Opportunities:**
- **Brand Awareness**: Below-average search rate (0.20%) - review creative for brand prominence
- **Summer Launch**: Mid-range performance - consider applying learnings from Holiday Push

**Efficiency Insights:**
- Average branded search rate: 0.29% (above typical benchmark of 0.10-0.30%)
- Average cost per branded search: $1.78 (within healthy range of $0.50-$5.00)
- Holiday campaigns show 37% better efficiency than always-on campaigns

**Recommendations:**
1. Scale Holiday Push approach - it's 27% more cost-efficient than average
2. Refresh Brand Awareness creative to improve the 0.20% search rate
3. Product Launch shows promise - consider increasing budget given strong efficiency""",
                        'insights': [
                            'Holiday Push achieves 37% better cost efficiency than other campaigns',
                            'Average search rate of 0.29% exceeds industry benchmarks',
                            'Product Launch campaign shows highest efficiency potential at small scale',
                            '$1.78 average cost per branded search is highly competitive'
                        ],
                        'display_order': 2
                    }
                elif query['query_type'] == 'trend_analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Trend Analysis Results',
                        'sample_data': {
                            'rows': [
                                {'period': '2024-12-01', 'campaign': 'Holiday Push', 'total_impressions': 625000, 'total_branded_searches': 2500, 'avg_search_rate': 0.00400, 'search_rate_volatility': 0.00045},
                                {'period': '2024-11-24', 'campaign': 'Holiday Push', 'total_impressions': 625000, 'total_branded_searches': 2300, 'avg_search_rate': 0.00368, 'search_rate_volatility': 0.00038},
                                {'period': '2024-11-17', 'campaign': 'Holiday Push', 'total_impressions': 625000, 'total_branded_searches': 2100, 'avg_search_rate': 0.00336, 'search_rate_volatility': 0.00042},
                                {'period': '2024-11-10', 'campaign': 'Holiday Push', 'total_impressions': 625000, 'total_branded_searches': 1850, 'avg_search_rate': 0.00296, 'search_rate_volatility': 0.00051}
                            ]
                        },
                        'interpretation_markdown': """**Trend Analysis:**

**Growth Pattern:**
- Week-over-week branded search growth: +10.8% average
- Search rate improved from 0.296% to 0.400% (+35% over 4 weeks)
- Consistent impression delivery with stable 625K weekly impressions

**Volatility Analysis:**
- Low search rate volatility (0.00038-0.00051) indicates consistent performance
- Decreasing volatility over time suggests campaign optimization is working

**Seasonal Impact:**
- Clear upward trend approaching December (holiday season)
- 35% lift in search rate from mid-November to December

**Recommendations:**
1. Maintain current strategy - consistent growth trend is strong
2. Plan for continued seasonal lift through December
3. Low volatility suggests creative and targeting are well-optimized
4. Consider increasing budget to capitalize on improving efficiency""",
                        'insights': [
                            '35% improvement in branded search rate over 4 weeks',
                            'Consistent week-over-week growth averaging 10.8%',
                            'Low volatility indicates stable, predictable performance',
                            'Holiday seasonality driving increased brand interest'
                        ],
                        'display_order': 3
                    }
                    
                example_response = client.table('build_guide_examples').insert(example_data).execute()
                if example_response.data:
                    logger.info(f"Created example results for {query['title']}")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'number_of_branded_searches',
                'display_name': 'Number of Branded Searches',
                'definition': 'Count of times a branded keyword was searched on Amazon, attributed to your DSP campaign within a 14-day window',
                'metric_type': 'metric',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'keyword',
                'display_name': 'Branded Keyword',
                'definition': 'The actual brand term or variation that was searched by users (extracted from tracked_item field)',
                'metric_type': 'dimension',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'branded_search_rate',
                'display_name': 'Branded Search Rate',
                'definition': 'Efficiency metric calculated as branded searches divided by impressions, indicating the percentage of ad views that result in brand searches',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'cost_per_branded_search',
                'display_name': 'Cost per Branded Search',
                'definition': 'Investment required to generate one branded search, calculated as impression cost divided by number of branded searches',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'impressions',
                'display_name': 'Impressions',
                'definition': 'Total number of times your DSP ads were displayed to users',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'impression_cost',
                'display_name': 'Impression Cost',
                'definition': 'Total cost of impressions in your currency (converted from millicents by dividing by 100,000)',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'campaign_id',
                'display_name': 'Campaign ID',
                'definition': 'Unique identifier for the DSP campaign',
                'metric_type': 'dimension',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'campaign',
                'display_name': 'Campaign Name',
                'definition': 'Human-readable name of the DSP campaign',
                'metric_type': 'dimension',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'search_rate_volatility',
                'display_name': 'Search Rate Volatility',
                'definition': 'Standard deviation of the branded search rate, indicating consistency of performance',
                'metric_type': 'metric',
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
        
        logger.info("✅ Successfully created Ad-attributed Branded Searches Analysis guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_branded_searches_guide()
    sys.exit(0 if success else 1)