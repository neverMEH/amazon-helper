#!/usr/bin/env python3
"""
Seed script for 'Audience with multiple detail page views' Build Guide
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

def create_multiple_dpv_audience_guide():
    """Create the Audience with multiple detail page views guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_multiple_dpv_audience',
            'name': 'Audience with multiple detail page views',
            'category': 'Audience Building',
            'short_description': 'Learn how to identify and target high-intent shoppers who have viewed product detail pages multiple times, enabling remarketing to users showing strong purchase intent.',
            'tags': ['Audience building', 'Detail page views', 'Remarketing', 'High-intent shoppers', 'Conversion optimization'],
            'icon': 'Eye',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 30,
            'prerequisites': [
                'Access to AMC with audience creation capabilities',
                'Amazon DSP account for audience activation',
                'Understanding of AMC rule-based audience queries',
                'Basic knowledge of SQL and audience segmentation'
            ],
            'is_published': True,
            'display_order': 11,
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
                'section_id': 'audience_query_instructions',
                'title': '1. Audience Query Instructions',
                'content_markdown': """## 1.1 About rule-based audience queries

Unlike standard AMC queries, AMC Audience queries do not return visible results that you can download. Instead, the audience defined by the query is pushed directly to Amazon DSP. AMC rule-based audience queries require selecting a set of user_id values to create the Amazon DSP audience.

## 1.2 Tables used

**Note:** AMC rule-based queries use a unique set of tables that contain the `_for_audiences` suffix in the names.

### Key Table:

**conversions_for_audiences**: This is a copy of the conversions table designed for use with AMC Audiences. More information about the conversions tables can be found in the Instructional Query: Documentation - Custom Attribution Overview.

This table contains:
- User interactions with product detail pages
- Purchase events for attribution
- Event timestamps for recency filtering
- ASIN-level tracking for product-specific audiences""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'complementary_measurement',
                'title': '2. Complementary Measurement Query',
                'content_markdown': """## 2.1 Assess your opportunity

A starting point to building this audience is assessing the number of audience members with multiple detail page views by querying in the AMC measurement query editor.

This query creates "buckets" that represent the number of detail page views (dpv). The query calculates the total number of shoppers that viewed the detail page exactly one time (dpv_1), two times (dpv_2), and so on, up to five times or more. For example, if a shopper viewed a detail page 3 times, that user_id will be "placed" in the dpv_3 bucket. Note that you can configure up to 5 buckets.

The configurable portion of the query is an ASIN filter. If you have many different ASINs, you may wish to constrain the query to a certain appropriate set. Based on this, the query will build a table of detailPageView buckets for each ASIN included in the filter.

## 2.2 Understanding the buckets

- **Lower detail page view buckets (dpv_1 and dpv_2)**: May have larger numbers of shoppers (users_in_bucket), but may not present as great of an opportunity due to the lower number of detail page views, which may indicate less interest in the product.

- **High dpv buckets (dpv_4 and dpv_5+)**: Shoppers may be more likely to purchase when exposed to an ad for the product. These shoppers are excellent candidates to include in an audience. However, these buckets may not contain as many shoppers and it may not be worthwhile to create an audience focused only on those shoppers. Additionally, there may be too few shoppers to reach the Amazon DSP audience limit of 2,000.

- **Mid-range buckets (dpv_3)**: You may want to also include the shoppers in the mid-range of detail page views. If you do, then you will want to build an audience with the "dpv floor" set to 3 (that is, an audience of shoppers that viewed the detail page 3 or more times).""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'create_audience',
                'title': '3. Create Audiences',
                'content_markdown': """## 3.1 Basic audience: Shoppers with multiple detail page views

Once we have identified a reasonable dpv floor (that is, the minimum number of detailPageViews for our audience), we can continue by creating the audience.

For example, the following query creates an audience of shoppers that viewed the detail more than twice (as indicated by `HAVING SUM(conversions) > 2`). This query does not filter by ASINs.

**Key configuration options:**
- Modify the dpv floor by changing the value in the HAVING clause
- Add ASIN filters to focus on specific products
- Adjust the event_subtype to build different kinds of audiences

## 3.2 Advanced audience: Shoppers with multiple detail page views that have not purchased

While the prior query illustrates how to create an audience of shoppers that viewed the detail page three times or more, a more effective audience excludes shoppers that already purchased. We can add to the query an additional set of parameters to eliminate from the audience the shoppers that completed their order after the most recent detail page view. 

The result is an audience that is only shoppers that viewed the detail page three or more times but did not complete the purchase process.

**This approach:**
- Maximizes remarketing efficiency by excluding converters
- Focuses budget on true opportunities
- Prevents oversaturation of recent purchasers
- Improves ROAS by targeting only non-converters""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'advanced_variations',
                'title': '4. Advanced Query Variations',
                'content_markdown': """## 4.1 Time-Bounded Multiple Views

Create audiences based on multiple views within a specific timeframe. This approach helps you:
- Focus on users with recent interest
- Avoid stale audiences
- Improve conversion rates with timely remarketing
- Manage audience size more effectively

**Best practices:**
- Use 14-day windows for most categories
- Shorten to 7 days for seasonal or trending products
- Extend to 30 days for high-consideration purchases

## 4.2 Category-Level Multiple Views

Target users with multiple views across products in a category rather than individual ASINs. This strategy:
- Captures category-interested shoppers
- Enables cross-sell opportunities
- Builds larger, more stable audiences
- Reduces dependency on single product performance

**Implementation tips:**
- Group ASINs by category or brand
- Require views of multiple different products
- Set total view thresholds across the category
- Consider product price points when setting thresholds

## 4.3 High-Frequency Recent Viewers

Identify users with accelerating viewing behavior - those whose view frequency is increasing over time. These users often indicate:
- Rising purchase intent
- Active comparison shopping
- Nearing purchase decision
- Response to recent marketing efforts

**Segmentation approach:**
- Compare views in last 7 days vs prior 7 days
- Identify acceleration patterns
- Prioritize users with increasing frequency
- Apply urgency messaging to capitalize on momentum""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'exploratory_analysis',
                'title': '5. Exploratory Analysis Queries',
                'content_markdown': """## 5.1 View-to-Purchase Conversion Analysis

Understanding conversion rates by view frequency helps you:
- Set optimal view thresholds for audiences
- Identify the point of diminishing returns
- Understand your conversion funnel
- Benchmark performance expectations

**Key metrics to track:**
- Conversion rate by view count
- Average views before purchase
- Drop-off rates between view counts
- Time between views and purchase

## 5.2 ASIN-Level Opportunity Assessment

Identify products with high repeat viewing but low conversion to prioritize remarketing efforts. This analysis reveals:
- Products with consideration challenges
- High-interest but low-conversion items
- Price sensitivity indicators
- Competitive pressure points

**Action items from this analysis:**
- Focus remarketing on high-opportunity ASINs
- Adjust messaging for specific product challenges
- Consider pricing or promotional strategies
- Develop product-specific creative""",
                'display_order': 5,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': '6. Best Practices and Implementation Tips',
                'content_markdown': """## 6.1 Determining Optimal View Thresholds

Setting the right view threshold is crucial for audience effectiveness:

- **2 views**: Baseline interest indicator - largest audience but lowest intent
- **3-4 views**: Strong purchase intent - optimal balance of size and quality
- **5+ views**: May indicate comparison shopping or hesitation - smallest but highest intent
- Balance audience size with intent level based on your campaign goals

## 6.2 Audience Segmentation Strategies

Create multiple audiences for different messaging approaches:

- **By recency**: Prioritize recent viewers (last 7-14 days) for immediate remarketing
- **By intensity**: Separate moderate (2-3 views) from high (4+ views) frequency for different offers
- **By product**: Create ASIN-specific audiences for targeted messaging
- **By behavior pattern**: Identify accelerating vs. steady viewing patterns

## 6.3 Remarketing Tactics

Optimize your remarketing approach based on viewing behavior:

- **Immediate retargeting**: Within 24-48 hours of last view for maximum recall
- **Progressive messaging**: Different creative based on view count (benefits → social proof → offers)
- **Incentive testing**: Offer discounts to high-view non-purchasers (5+ views)
- **Cross-sell opportunities**: Target category-level viewers with complementary products

## 6.4 Exclusion Strategies

Improve efficiency by excluding certain users:

- Exclude recent purchasers (last 30-60 days) to avoid redundant messaging
- Remove users with very high view counts (10+) who may be researchers or competitors
- Filter out competitor product viewers to maintain brand focus
- Exclude low-value product viewers to optimize for profitability

## 6.5 Performance Optimization

Continuously improve your audience strategy:

- Monitor audience size vs. performance trade-offs weekly
- Test different view thresholds by product category
- Track time between last view and purchase to optimize timing
- Measure incremental lift from remarketing using holdout groups

## 6.6 Common Use Cases by Industry

Apply industry-specific strategies:

- **Electronics**: Target comparison shoppers (3-5 views) with feature comparisons
- **Fashion**: Quick remarketing for seasonal items (2+ views) with urgency messaging
- **Home & Garden**: Focus on consideration phase (4+ views) with visualization tools
- **Books/Media**: Cross-sell to series viewers with related content

## 6.7 Measurement Recommendations

Track success with proper measurement:

- Run frequency analysis before setting thresholds to understand your baseline
- Compare conversion rates across view buckets to identify sweet spots
- Monitor audience overlap with other campaigns to prevent fatigue
- Track view-to-purchase time windows to optimize remarketing timing
- Measure incremental ROAS vs. standard campaigns""",
                'display_order': 6,
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
                'title': 'Detail Page View Frequency Analysis',
                'description': 'Analyze the distribution of detail page views to determine optimal audience thresholds',
                'sql_query': """/* Audience Measurement Query: Detail Page View Frequency */
/* Optional update: If you want to filter by ASINs, add one or more ASIN(s) to the list below
 and uncomment line [1 of 1] */
WITH asins (asin) AS (
  VALUES
    {{asin_list}}
),
dpvs AS (
  SELECT
    tracked_asin,
    user_id,
    SUM(conversions) AS dpv
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'detailPageView'
    {{asin_filter}}
  GROUP BY
    1,
    2
)
SELECT
  tracked_asin,
  /* Optional update: Modify the number of dpv_buckets, if necessary. 
   The default maximum is 5, which will result in 5 buckets. */
  IF(dpv < 5, CONCAT('dpv_', dpv), 'dpv_5+') AS dpv_buckets,
  COUNT(DISTINCT user_id) AS users_in_bucket,
  SUM(dpv) AS dpv_in_bucket
FROM
  dpvs
GROUP BY
  1,
  2
ORDER BY
  tracked_asin,
  dpv_buckets""",
                'parameters_schema': {
                    'asin_list': {
                        'type': 'string',
                        'default': '(1111111111), (2222222222)',
                        'description': 'List of ASINs in SQL VALUES format'
                    },
                    'asin_filter': {
                        'type': 'string',
                        'default': '-- AND tracked_item IN (SELECT asin FROM asins)',
                        'description': 'Optional ASIN filter (uncomment to use)'
                    }
                },
                'default_parameters': {
                    'asin_list': '(1111111111), (2222222222)',
                    'asin_filter': '-- AND tracked_item IN (SELECT asin FROM asins)'
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'Use this query to understand the distribution of detail page views across your products. Focus on buckets with sufficient user counts (>1000) for effective audience creation.'
            },
            {
                'guide_id': guide_id,
                'title': 'Basic Multiple DPV Audience',
                'description': 'Create an audience of shoppers with multiple detail page views',
                'sql_query': """/* Audience Instructional Query: Multiple detailPageView */
SELECT
  user_id
FROM
  conversions_for_audiences
  /* Optional update: replace 'detailPageView' with other event_subtypes to build different kinds of audiences. */
WHERE
  event_subtype = 'detailPageView'
GROUP BY
  1
  /* Optional update: To modify the dpv floor, set '{{min_dpv}}' to another integer value (between 0 and 4) */
HAVING
  SUM(conversions) > {{min_dpv}}""",
                'parameters_schema': {
                    'min_dpv': {
                        'type': 'integer',
                        'default': 2,
                        'description': 'Minimum number of detail page views (dpv floor)'
                    }
                },
                'default_parameters': {
                    'min_dpv': 2
                },
                'display_order': 2,
                'query_type': 'main_analysis',
                'interpretation_notes': 'This creates a basic audience of users who have viewed detail pages more than the specified threshold. Start with 2 views and adjust based on audience size.'
            },
            {
                'guide_id': guide_id,
                'title': 'Multiple DPV Without Purchase',
                'description': 'Create an audience of shoppers with multiple detail page views who have not purchased',
                'sql_query': """/* Audience Instructional Query: Multiple detailPageView but did not purchase */
/* Update: If you want to filter by ASINs, add one or more ASIN(s) to the list below
 and uncomment lines [1 of 2] and [2 of 2] */
WITH asins (asin) AS (
  VALUES
    {{asin_list}}
),
dpv_user AS(
  SELECT
    user_id,
    MAX(event_dt_utc) AS dpv_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'detailPageView'
    {{dpv_asin_filter}}
  GROUP BY
    1
    /* Optional update: To modify the dpv floor, set '{{min_dpv}}' to another integer value (between 0 and 4) */
  HAVING
    SUM(conversions) > {{min_dpv}}
),
purchase_user AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS pur_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'order'
    {{purchase_asin_filter}}
  GROUP BY
    1
)
SELECT
  dpv_user.user_id
FROM
  dpv_user
  LEFT JOIN purchase_user ON dpv_user.user_id = purchase_user.user_id
WHERE
  /* Remove user_ids with purchases more recent than the most recent detailPageView */
  dpv_dt_max > pur_dt_max
  OR pur_dt_max IS NULL""",
                'parameters_schema': {
                    'asin_list': {
                        'type': 'string',
                        'default': '(1111111111), (2222222222)',
                        'description': 'List of ASINs in SQL VALUES format'
                    },
                    'min_dpv': {
                        'type': 'integer',
                        'default': 2,
                        'description': 'Minimum number of detail page views'
                    },
                    'dpv_asin_filter': {
                        'type': 'string',
                        'default': '-- AND tracked_item IN (SELECT asin FROM asins)',
                        'description': 'Optional ASIN filter for detail page views'
                    },
                    'purchase_asin_filter': {
                        'type': 'string',
                        'default': '-- AND tracked_asin IN (SELECT asin FROM asins)',
                        'description': 'Optional ASIN filter for purchases'
                    }
                },
                'default_parameters': {
                    'asin_list': '(1111111111), (2222222222)',
                    'min_dpv': 2,
                    'dpv_asin_filter': '-- AND tracked_item IN (SELECT asin FROM asins)',
                    'purchase_asin_filter': '-- AND tracked_asin IN (SELECT asin FROM asins)'
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': 'This is the recommended audience query as it excludes users who have already purchased, maximizing remarketing efficiency.'
            },
            {
                'guide_id': guide_id,
                'title': 'Time-Bounded Multiple Views',
                'description': 'Create audiences based on multiple views within a specific timeframe',
                'sql_query': """/* Audience: Multiple Detail Page Views in Last N Days */
WITH recent_dpv AS (
  SELECT
    user_id,
    SUM(conversions) AS dpv_count,
    MAX(event_dt_utc) AS last_dpv_date
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'detailPageView'
    AND event_dt_utc >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
  GROUP BY
    1
  HAVING
    SUM(conversions) >= {{min_dpv}}
)
SELECT
  user_id
FROM
  recent_dpv
WHERE
  last_dpv_date >= CURRENT_DATE - INTERVAL '{{recency_days}}' DAY  -- At least one view in last N days""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 14,
                        'description': 'Days to look back for all views'
                    },
                    'recency_days': {
                        'type': 'integer',
                        'default': 7,
                        'description': 'Days for most recent view requirement'
                    },
                    'min_dpv': {
                        'type': 'integer',
                        'default': 3,
                        'description': 'Minimum number of views required'
                    }
                },
                'default_parameters': {
                    'lookback_days': 14,
                    'recency_days': 7,
                    'min_dpv': 3
                },
                'display_order': 4,
                'query_type': 'variation',
                'interpretation_notes': 'Focus on recent viewers for better conversion rates. Adjust timeframes based on your product consideration cycle.'
            },
            {
                'guide_id': guide_id,
                'title': 'Category-Level Multiple Views',
                'description': 'Target users with multiple views across products in a category',
                'sql_query': """/* Audience: Multiple Views Across Category */
WITH category_dpv AS (
  SELECT
    user_id,
    COUNT(DISTINCT tracked_asin) AS unique_products_viewed,
    SUM(conversions) AS total_dpv
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'detailPageView'
    AND tracked_asin IN (
      SELECT DISTINCT tracked_asin 
      FROM conversions_for_audiences
      WHERE brand = '{{brand_name}}'  -- Replace with your brand or use category filter
    )
  GROUP BY
    1
  HAVING
    COUNT(DISTINCT tracked_asin) >= {{min_products}}  -- Viewed at least N different products
    AND SUM(conversions) >= {{min_total_views}}  -- Total views across products
)
SELECT user_id FROM category_dpv""",
                'parameters_schema': {
                    'brand_name': {
                        'type': 'string',
                        'default': 'YourBrand',
                        'description': 'Brand name for filtering products'
                    },
                    'min_products': {
                        'type': 'integer',
                        'default': 2,
                        'description': 'Minimum number of different products viewed'
                    },
                    'min_total_views': {
                        'type': 'integer',
                        'default': 5,
                        'description': 'Minimum total views across all products'
                    }
                },
                'default_parameters': {
                    'brand_name': 'YourBrand',
                    'min_products': 2,
                    'min_total_views': 5
                },
                'display_order': 5,
                'query_type': 'variation',
                'interpretation_notes': 'Captures users interested in your category or brand, not just individual products. Great for cross-selling.'
            },
            {
                'guide_id': guide_id,
                'title': 'High-Frequency Recent Viewers',
                'description': 'Identify users with accelerating viewing behavior',
                'sql_query': """/* Audience: Accelerating View Frequency */
WITH view_velocity AS (
  SELECT
    user_id,
    COUNT(CASE WHEN event_dt_utc >= CURRENT_DATE - INTERVAL '{{recent_days}}' DAY THEN 1 END) AS views_last_period,
    COUNT(CASE WHEN event_dt_utc >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY 
               AND event_dt_utc < CURRENT_DATE - INTERVAL '{{recent_days}}' DAY THEN 1 END) AS views_prior_period
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'detailPageView'
    AND event_dt_utc >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
  GROUP BY
    1
)
SELECT
  user_id
FROM
  view_velocity
WHERE
  views_last_period > views_prior_period  -- Increasing view frequency
  AND views_last_period >= {{min_recent_views}}""",
                'parameters_schema': {
                    'recent_days': {
                        'type': 'integer',
                        'default': 7,
                        'description': 'Days for recent period'
                    },
                    'lookback_days': {
                        'type': 'integer',
                        'default': 14,
                        'description': 'Total days to look back'
                    },
                    'min_recent_views': {
                        'type': 'integer',
                        'default': 2,
                        'description': 'Minimum views in recent period'
                    }
                },
                'default_parameters': {
                    'recent_days': 7,
                    'lookback_days': 14,
                    'min_recent_views': 2
                },
                'display_order': 6,
                'query_type': 'variation',
                'interpretation_notes': 'Users with accelerating view frequency often indicate rising purchase intent. Target with urgency messaging.'
            },
            {
                'guide_id': guide_id,
                'title': 'View-to-Purchase Conversion Analysis',
                'description': 'Understand conversion rates by view frequency',
                'sql_query': """/* Exploratory: Conversion Rate by View Frequency */
WITH view_counts AS (
  SELECT
    user_id,
    SUM(conversions) AS dpv_count
  FROM
    conversions
  WHERE
    event_subtype = 'detailPageView'
    AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
  GROUP BY
    1
),
purchases AS (
  SELECT
    DISTINCT user_id
  FROM
    conversions
  WHERE
    event_subtype = 'order'
    AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
),
analysis AS (
  SELECT
    v.dpv_count,
    COUNT(DISTINCT v.user_id) AS total_users,
    COUNT(DISTINCT p.user_id) AS purchasers
  FROM
    view_counts v
    LEFT JOIN purchases p ON v.user_id = p.user_id
  GROUP BY
    1
)
SELECT
  dpv_count,
  total_users,
  purchasers,
  ROUND((purchasers::FLOAT / total_users) * 100, 2) AS conversion_rate
FROM
  analysis
WHERE
  dpv_count <= {{max_dpv_display}}
ORDER BY
  dpv_count""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Days to look back for analysis'
                    },
                    'max_dpv_display': {
                        'type': 'integer',
                        'default': 10,
                        'description': 'Maximum DPV count to display'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'max_dpv_display': 10
                },
                'display_order': 7,
                'query_type': 'exploratory',
                'interpretation_notes': 'Analyze how conversion rate changes with view frequency to set optimal audience thresholds.'
            },
            {
                'guide_id': guide_id,
                'title': 'ASIN Opportunity Assessment',
                'description': 'Identify products with high repeat viewing but low conversion',
                'sql_query': """/* Exploratory: ASIN Opportunity Assessment */
WITH asin_metrics AS (
  SELECT
    tracked_asin,
    COUNT(DISTINCT user_id) AS unique_viewers,
    SUM(conversions) AS total_views,
    AVG(conversions) AS avg_views_per_user
  FROM
    conversions
  WHERE
    event_subtype = 'detailPageView'
    AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
  GROUP BY
    1
),
asin_purchases AS (
  SELECT
    tracked_asin,
    COUNT(DISTINCT user_id) AS purchasers
  FROM
    conversions
  WHERE
    event_subtype = 'order'
    AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
  GROUP BY
    1
)
SELECT
  m.tracked_asin,
  m.unique_viewers,
  ROUND(m.avg_views_per_user, 2) AS avg_views_per_user,
  COALESCE(p.purchasers, 0) AS purchasers,
  m.unique_viewers - COALESCE(p.purchasers, 0) AS opportunity_size,
  ROUND((COALESCE(p.purchasers, 0)::FLOAT / m.unique_viewers) * 100, 2) AS conversion_rate
FROM
  asin_metrics m
  LEFT JOIN asin_purchases p ON m.tracked_asin = p.tracked_asin
WHERE
  m.avg_views_per_user >= {{min_avg_views}}  -- Focus on products with repeat viewing
ORDER BY
  opportunity_size DESC
LIMIT {{limit}}""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Days to look back for analysis'
                    },
                    'min_avg_views': {
                        'type': 'float',
                        'default': 2.0,
                        'description': 'Minimum average views per user'
                    },
                    'limit': {
                        'type': 'integer',
                        'default': 20,
                        'description': 'Number of ASINs to return'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'min_avg_views': 2.0,
                    'limit': 20
                },
                'display_order': 8,
                'query_type': 'exploratory',
                'interpretation_notes': 'Focus remarketing efforts on ASINs with large opportunity sizes and low conversion rates.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results for key queries
                if query['title'] == 'Detail Page View Frequency Analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Detail Page View Distribution',
                        'sample_data': {
                            'rows': [
                                {'tracked_asin': '1111111', 'dpv_buckets': 'dpv_1', 'users_in_bucket': 24095, 'dpv_in_bucket': 24095},
                                {'tracked_asin': '1111111', 'dpv_buckets': 'dpv_2', 'users_in_bucket': 6008, 'dpv_in_bucket': 12016},
                                {'tracked_asin': '1111111', 'dpv_buckets': 'dpv_3', 'users_in_bucket': 1809, 'dpv_in_bucket': 5427},
                                {'tracked_asin': '1111111', 'dpv_buckets': 'dpv_4', 'users_in_bucket': 805, 'dpv_in_bucket': 3220},
                                {'tracked_asin': '1111111', 'dpv_buckets': 'dpv_5+', 'users_in_bucket': 854, 'dpv_in_bucket': 5952},
                                {'tracked_asin': '2222222', 'dpv_buckets': 'dpv_1', 'users_in_bucket': 14035, 'dpv_in_bucket': 14035},
                                {'tracked_asin': '2222222', 'dpv_buckets': 'dpv_2', 'users_in_bucket': 2108, 'dpv_in_bucket': 4216},
                                {'tracked_asin': '2222222', 'dpv_buckets': 'dpv_3', 'users_in_bucket': 609, 'dpv_in_bucket': 1827},
                                {'tracked_asin': '2222222', 'dpv_buckets': 'dpv_4', 'users_in_bucket': 305, 'dpv_in_bucket': 1220},
                                {'tracked_asin': '2222222', 'dpv_buckets': 'dpv_5+', 'users_in_bucket': 458, 'dpv_in_bucket': 2595}
                            ]
                        },
                        'interpretation_markdown': """**Key Insights:**

- **Single view dominance**: Most users (70-80%) only view once, indicating low initial engagement
- **Sharp drop-off**: User counts decrease dramatically with each additional view
- **Sweet spot at dpv_3**: Users with 3 views show strong interest while maintaining decent audience size
- **High-intent segment**: Users with 5+ views represent highly engaged shoppers

**Recommendations:**
1. Set minimum threshold at 3 views for balanced audience size and intent
2. Create separate campaigns for 3-4 views (moderate intent) and 5+ views (high intent)
3. ASIN 1111111 has better engagement with more multi-viewers than ASIN 2222222""",
                        'insights': [
                            'Only 25-30% of viewers look at products multiple times',
                            'Users with 3+ views represent strong remarketing opportunity',
                            'Different ASINs show varying engagement patterns'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example for Detail Page View Frequency Analysis")
                
                elif query['title'] == 'View-to-Purchase Conversion Analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Conversion Rate by View Frequency',
                        'sample_data': {
                            'rows': [
                                {'dpv_count': 1, 'total_users': 450000, 'purchasers': 13500, 'conversion_rate': 3.00},
                                {'dpv_count': 2, 'total_users': 125000, 'purchasers': 6250, 'conversion_rate': 5.00},
                                {'dpv_count': 3, 'total_users': 45000, 'purchasers': 3600, 'conversion_rate': 8.00},
                                {'dpv_count': 4, 'total_users': 18000, 'purchasers': 2160, 'conversion_rate': 12.00},
                                {'dpv_count': 5, 'total_users': 8500, 'purchasers': 1105, 'conversion_rate': 13.00},
                                {'dpv_count': 6, 'total_users': 4200, 'purchasers': 504, 'conversion_rate': 12.00},
                                {'dpv_count': 7, 'total_users': 2100, 'purchasers': 231, 'conversion_rate': 11.00},
                                {'dpv_count': 8, 'total_users': 1050, 'purchasers': 105, 'conversion_rate': 10.00},
                                {'dpv_count': 9, 'total_users': 520, 'purchasers': 47, 'conversion_rate': 9.04},
                                {'dpv_count': 10, 'total_users': 280, 'purchasers': 25, 'conversion_rate': 8.93}
                            ]
                        },
                        'interpretation_markdown': """**Conversion Pattern Analysis:**

- **Progressive improvement**: Conversion rate increases from 3% to 13% as views increase from 1 to 5
- **Peak conversion**: Optimal conversion at 4-5 views (12-13%)
- **Plateau effect**: Conversion rate stabilizes or slightly decreases after 5 views
- **Diminishing returns**: Users with 6+ views may be stuck in consideration

**Strategic Implications:**
1. **Priority segment**: Focus on users with 3-5 views for maximum ROI
2. **Different messaging needed**:
   - 1-2 views: Educational content about product benefits
   - 3-4 views: Social proof and reviews
   - 5+ views: Incentives or addressing specific concerns
3. **Audience sizing**: 188,000 users with 2-5 views represent prime remarketing opportunity""",
                        'insights': [
                            'Users with 4 views are 4x more likely to convert than single viewers',
                            'Conversion rate plateaus after 5 views, suggesting decision paralysis',
                            'Focus remarketing on 3-5 view segment for best results'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example for View-to-Purchase Conversion Analysis")
                
                elif query['title'] == 'ASIN Opportunity Assessment':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'ASIN-Level Remarketing Opportunities',
                        'sample_data': {
                            'rows': [
                                {'tracked_asin': 'ASIN001', 'unique_viewers': 12500, 'avg_views_per_user': 3.2, 'purchasers': 875, 'opportunity_size': 11625, 'conversion_rate': 7.00},
                                {'tracked_asin': 'ASIN002', 'unique_viewers': 9800, 'avg_views_per_user': 2.8, 'purchasers': 490, 'opportunity_size': 9310, 'conversion_rate': 5.00},
                                {'tracked_asin': 'ASIN003', 'unique_viewers': 7200, 'avg_views_per_user': 4.1, 'purchasers': 720, 'opportunity_size': 6480, 'conversion_rate': 10.00},
                                {'tracked_asin': 'ASIN004', 'unique_viewers': 6500, 'avg_views_per_user': 2.5, 'purchasers': 845, 'opportunity_size': 5655, 'conversion_rate': 13.00},
                                {'tracked_asin': 'ASIN005', 'unique_viewers': 5200, 'avg_views_per_user': 3.8, 'purchasers': 312, 'opportunity_size': 4888, 'conversion_rate': 6.00}
                            ]
                        },
                        'interpretation_markdown': """**ASIN Performance Insights:**

- **ASIN001**: Largest opportunity (11,625 users) with moderate conversion (7%)
- **ASIN002**: Low conversion (5%) despite decent engagement - needs attention
- **ASIN003**: Highest engagement (4.1 views/user) but only 10% conversion
- **ASIN004**: Best conversion (13%) but lower repeat viewing
- **ASIN005**: High engagement (3.8 views) with poor conversion (6%)

**Action Plan:**
1. **Immediate focus**: ASIN001 and ASIN002 for large audience sizes
2. **Messaging strategy**:
   - ASIN003: Address hesitation factors (price, features)
   - ASIN002 & ASIN005: Test incentives to boost conversion
3. **Budget allocation**: Prioritize top 3 ASINs representing 27,415 potential customers""",
                        'insights': [
                            'Products with high view rates don\'t always convert well',
                            'ASIN003 users are highly engaged but need convincing',
                            'Combined opportunity of 37,958 non-purchasers across top 5 ASINs'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example for ASIN Opportunity Assessment")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'dpv_count',
                'display_name': 'Detail Page View Count',
                'definition': 'Number of detail page views per user',
                'metric_type': 'metric',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'users_in_bucket',
                'display_name': 'Users in Bucket',
                'definition': 'Count of users in each view frequency bucket',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'dpv_in_bucket',
                'display_name': 'Total Views in Bucket',
                'definition': 'Total page views in each frequency bucket',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'dpv_dt_max',
                'display_name': 'Most Recent View Date',
                'definition': 'Most recent detail page view date for a user',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'pur_dt_max',
                'display_name': 'Most Recent Purchase Date',
                'definition': 'Most recent purchase date for a user',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate',
                'display_name': 'Conversion Rate',
                'definition': 'Percentage of viewers who purchase',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'avg_views_per_user',
                'display_name': 'Average Views per User',
                'definition': 'Average number of detail page views per unique viewer',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'opportunity_size',
                'display_name': 'Opportunity Size',
                'definition': 'Number of viewers who have not purchased',
                'metric_type': 'metric',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'unique_viewers',
                'display_name': 'Unique Viewers',
                'definition': 'Count of distinct users who viewed detail pages',
                'metric_type': 'metric',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_views',
                'display_name': 'Total Views',
                'definition': 'Sum of all detail page views',
                'metric_type': 'metric',
                'display_order': 10
            },
            {
                'guide_id': guide_id,
                'metric_name': 'purchasers',
                'display_name': 'Purchasers',
                'definition': 'Count of users who completed a purchase',
                'metric_type': 'metric',
                'display_order': 11
            },
            {
                'guide_id': guide_id,
                'metric_name': 'views_last_period',
                'display_name': 'Recent Period Views',
                'definition': 'Number of views in the most recent time period',
                'metric_type': 'metric',
                'display_order': 12
            },
            {
                'guide_id': guide_id,
                'metric_name': 'views_prior_period',
                'display_name': 'Prior Period Views',
                'definition': 'Number of views in the previous time period',
                'metric_type': 'metric',
                'display_order': 13
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_id',
                'display_name': 'User ID',
                'definition': 'Unique identifier for users in AMC',
                'metric_type': 'dimension',
                'display_order': 14
            },
            {
                'guide_id': guide_id,
                'metric_name': 'tracked_asin',
                'display_name': 'Tracked ASIN',
                'definition': 'ASIN of the viewed product',
                'metric_type': 'dimension',
                'display_order': 15
            },
            {
                'guide_id': guide_id,
                'metric_name': 'event_subtype',
                'display_name': 'Event Subtype',
                'definition': 'Type of conversion event (detailPageView, order)',
                'metric_type': 'dimension',
                'display_order': 16
            },
            {
                'guide_id': guide_id,
                'metric_name': 'event_dt_utc',
                'display_name': 'Event Date UTC',
                'definition': 'Date and time of the event in UTC',
                'metric_type': 'dimension',
                'display_order': 17
            },
            {
                'guide_id': guide_id,
                'metric_name': 'dpv_buckets',
                'display_name': 'DPV Buckets',
                'definition': 'Categorized view frequency ranges (dpv_1, dpv_2, etc.)',
                'metric_type': 'dimension',
                'display_order': 18
            },
            {
                'guide_id': guide_id,
                'metric_name': 'brand',
                'display_name': 'Brand',
                'definition': 'Product brand name',
                'metric_type': 'dimension',
                'display_order': 19
            },
            {
                'guide_id': guide_id,
                'metric_name': 'unique_products_viewed',
                'display_name': 'Unique Products Viewed',
                'definition': 'Count of different ASINs viewed by a user',
                'metric_type': 'metric',
                'display_order': 20
            },
            {
                'guide_id': guide_id,
                'metric_name': 'last_dpv_date',
                'display_name': 'Last Detail Page View Date',
                'definition': 'Most recent date a user viewed a detail page',
                'metric_type': 'dimension',
                'display_order': 21
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created 'Audience with multiple detail page views' guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_multiple_dpv_audience_guide()
    sys.exit(0 if success else 1)