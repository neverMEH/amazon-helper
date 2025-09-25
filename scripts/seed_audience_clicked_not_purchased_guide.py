#!/usr/bin/env python3
"""
Seed script for 'Audience that clicked sponsored ads but did not purchase' Build Guide
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

def create_audience_clicked_not_purchased_guide():
    """Create the Audience that clicked sponsored ads but did not purchase guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_audience_clicked_not_purchased',
            'name': 'Audience that clicked sponsored ads but did not purchase',
            'category': 'Audience Building',
            'short_description': 'Learn how to create audiences of users who clicked on sponsored ads but haven\'t made a purchase, enabling targeted remarketing campaigns to convert interested shoppers.',
            'tags': ['Audience building', 'Remarketing', 'Sponsored ads', 'Conversion optimization', 'Non-converters'],
            'icon': 'Users',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 30,
            'prerequisites': [
                'Access to AMC with audience creation capabilities',
                'Active Sponsored Products, Sponsored Brands, or Sponsored Display campaigns',
                'Connected Amazon DSP account for audience activation',
                'Understanding of AMC rule-based audience queries'
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
                'section_id': 'audience_query_instructions',
                'title': '1. Audience Query Instructions',
                'content_markdown': """## 1.1 About rule-based audience queries

Unlike standard AMC queries, AMC Audience queries do not return visible results that you can download. Instead, the audience defined by the query is pushed directly to Amazon DSP. AMC rule-based audience queries require selecting a set of user_id values to create the Amazon DSP audience.

## 1.2 Tables used

**Note:** AMC rule-based queries use a unique set of tables that contain the `_for_audiences` suffix in the names.

### Key Tables:

**sponsored_ads_traffic_for_audiences**: While this example demonstrates querying data using the filter `ad_product_type = 'sponsored_products'` to get Sponsored Products traffic, alternately, you can query Sponsored Brands traffic `ad_product_type = 'sponsored_brands'` or omit the filter entirely to retrieve all Sponsored Ads traffic.

**amazon_attributed_events_by_traffic_time_for_audiences**: Contains attribution data for conversion events associated with sponsored ads traffic.""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'queries',
                'title': '2. Queries',
                'content_markdown': """## 2.1 Complementary Measurement Query

You can use the following two Instructional Queries to investigate if users exposed to Sponsored Products (or Sponsored Ads) and Amazon DSP are more likely to purchase and to determine if this use case is valid for your campaigns before you create the audience:
- Instructional Query: Sponsored Products and DSP Display Overlap
- Instructional Query: Sponsored Ads and DSP Overlap

## 2.2 Audience creation

The following query creates an audience of consumers who clicked Sponsored Products ads, but did not purchase. It does this by:
1. Identifying the Sponsored Product campaigns (you can use the campaigns from the overlap analysis from the exploratory queries above)
2. Creating a list of user_id's that clicked (clicks) the ads from the campaigns
3. Creating a list of user_id's that purchased (purchases) from that campaign
4. Removing the list of purchases from the list of clicks and creating an audience from those remaining user_id's

There are many possible variations for this genre of query:
- Instead of adding Sponsored Products campaign filters, you can include all Sponsored Ads campaigns
- `clicks` could be replaced with `impressions`
- `ad_product_type` can be any combination of `sponsored_products`, `sponsored_brands`, and `sponsored_display`
- Completely omit `AND ad_product_type = 'sponsored_products'` to get all Sponsored Ads
- `total_purchases` could be replaced with other metrics""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'query_variations',
                'title': '3. Query Variations',
                'content_markdown': """## 3.1 All Sponsored Ads Types - Clicked but Not Purchased

This variation includes all sponsored ads types (Products, Brands, Display). Use this when you want to capture the broadest audience of interested but non-converting users.

## 3.2 Sponsored Brands - Viewed but Not Purchased

This variation focuses on Sponsored Brands impressions without purchases. Ideal for brand awareness campaigns where you want to re-engage users who have seen your brand but haven't converted.

## 3.3 High-Intent Non-Converters (Multiple Clicks)

Target users who clicked multiple times but haven't purchased. These users show high intent and may need just a small nudge (like a discount or special offer) to convert.

## 3.4 Recent Clickers Without Purchase

Focus on users who clicked recently but haven't purchased. Recency is key for remarketing effectiveness - users who clicked within the last 7 days are more likely to remember your product.""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'exploratory_analysis',
                'title': '4. Exploratory Analysis',
                'content_markdown': """## 4.1 Understanding Click-to-Purchase Behavior

Before creating your audience, analyze the gap between clicks and purchases. This helps you understand the size of your remarketing opportunity and conversion rates by ad type.

## 4.2 Campaign-Level Opportunity Assessment

Identify which campaigns have the highest non-converting clicker opportunity. Focus your remarketing efforts on campaigns with large audiences of interested but non-converting users.""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': '5. Best Practices and Implementation Tips',
                'content_markdown': """## 5.1 Audience Sizing Strategy
- **Minimum size**: Ensure audience has at least 1,000 users for effective targeting
- **Maximum size**: Consider splitting large audiences (>1M users) for better targeting precision
- **Refresh frequency**: Update audiences weekly for optimal freshness and relevance

## 5.2 Segmentation Approaches
- **By recency**: Prioritize users who clicked in last 7-14 days for highest conversion potential
- **By intensity**: Separate single-click from multi-click users for different messaging strategies
- **By product type**: Create separate audiences for each ad type (SP, SB, SD) for tailored campaigns
- **By campaign**: Focus on high-value product campaigns with strong margins

## 5.3 Remarketing Tactics
- **Immediate follow-up**: Target within 24-48 hours of click for maximum impact
- **Progressive messaging**: Show different creative based on time since click
- **Cross-channel**: Use DSP to reach clickers from Sponsored Ads across Amazon properties
- **Incentive testing**: Test offers for high-intent non-converters (3+ clicks)

## 5.4 Exclusion Strategies
- Exclude recent purchasers (last 30-60 days) to avoid wasted impressions
- Remove users who clicked competitor products to maintain brand focus
- Filter out low-value product clickers to optimize ROAS
- Exclude users with high return rates if available in your data

## 5.5 Performance Optimization
- Monitor audience size trends over time to identify growth opportunities
- Track conversion rates by click recency to optimize timing
- Analyze optimal click-to-remarketing windows for your category
- Test different creative messages for non-converters vs general audience

## 5.6 Common Use Cases
- **E-commerce**: Recover abandoned consideration with targeted offers
- **Consumer Electronics**: Re-engage comparison shoppers with feature highlights
- **Fashion**: Seasonal product remarketing with urgency messaging
- **Books**: Series and author recommendations based on browsing behavior

## 5.7 Measurement Recommendations
- Run exploratory queries before audience creation to validate opportunity size
- Compare conversion rates across ad types to prioritize efforts
- Monitor audience overlap with other campaigns to avoid oversaturation
- Track incremental lift from remarketing campaigns using holdout groups""",
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
        
        # Create queries
        queries = [
            {
                'guide_id': guide_id,
                'title': 'Click-to-Purchase Analysis',
                'description': 'Analyze the gap between clicks and purchases to understand your remarketing opportunity',
                'sql_query': """/* Exploratory Query: Click-to-Purchase Analysis */
WITH click_stats AS (
  SELECT
    ad_product_type,
    COUNT(DISTINCT user_id) as clickers
  FROM
    sponsored_ads_traffic
  WHERE
    clicks > 0
    AND event_dt >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
  GROUP BY
    ad_product_type
),
purchase_stats AS (
  SELECT
    ad_product_type,
    COUNT(DISTINCT user_id) as purchasers
  FROM
    amazon_attributed_events_by_traffic_time
  WHERE
    total_purchases > 0
    AND event_dt >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
  GROUP BY
    ad_product_type
)
SELECT
  c.ad_product_type,
  c.clickers,
  COALESCE(p.purchasers, 0) as purchasers,
  c.clickers - COALESCE(p.purchasers, 0) as non_purchasers,
  ROUND((COALESCE(p.purchasers, 0)::FLOAT / c.clickers) * 100, 2) as conversion_rate
FROM
  click_stats c
  LEFT JOIN purchase_stats p ON c.ad_product_type = p.ad_product_type
ORDER BY
  c.clickers DESC""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for click and purchase data'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'Use this query to understand the size of your non-converting clicker audience by ad type. Focus on ad types with low conversion rates but high click volumes for remarketing opportunities.'
            },
            {
                'guide_id': guide_id,
                'title': 'Campaign Opportunity Assessment',
                'description': 'Identify campaigns with the highest non-converting clicker opportunity',
                'sql_query': """/* Exploratory Query: Campaign Opportunity Assessment */
WITH campaign_clicks AS (
  SELECT
    campaign,
    COUNT(DISTINCT user_id) as clickers
  FROM
    sponsored_ads_traffic
  WHERE
    clicks > 0
    AND ad_product_type = '{{ad_product_type}}'
    AND event_dt >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
  GROUP BY
    campaign
),
campaign_purchases AS (
  SELECT
    campaign,
    COUNT(DISTINCT user_id) as purchasers
  FROM
    amazon_attributed_events_by_traffic_time
  WHERE
    total_purchases > 0
    AND ad_product_type = '{{ad_product_type}}'
    AND event_dt >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
  GROUP BY
    campaign
)
SELECT
  c.campaign,
  c.clickers,
  COALESCE(p.purchasers, 0) as purchasers,
  c.clickers - COALESCE(p.purchasers, 0) as opportunity_size,
  ROUND((COALESCE(p.purchasers, 0)::FLOAT / c.clickers) * 100, 2) as conversion_rate
FROM
  campaign_clicks c
  LEFT JOIN campaign_purchases p ON c.campaign = p.campaign
WHERE
  c.clickers - COALESCE(p.purchasers, 0) >= {{min_opportunity_size}}
ORDER BY
  opportunity_size DESC
LIMIT 20""",
                'parameters_schema': {
                    'ad_product_type': {
                        'type': 'string',
                        'default': 'sponsored_products',
                        'description': 'Type of sponsored ad (sponsored_products, sponsored_brands, sponsored_display)'
                    },
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back'
                    },
                    'min_opportunity_size': {
                        'type': 'integer',
                        'default': 100,
                        'description': 'Minimum number of non-converting clickers to include'
                    }
                },
                'default_parameters': {
                    'ad_product_type': 'sponsored_products',
                    'lookback_days': 30,
                    'min_opportunity_size': 100
                },
                'display_order': 2,
                'query_type': 'exploratory',
                'interpretation_notes': 'Identify campaigns with large audiences of non-converting clickers. These represent your best remarketing opportunities.'
            },
            {
                'guide_id': guide_id,
                'title': 'Main Audience Creation - Clicked but Not Purchased',
                'description': 'Create an audience of users who clicked Sponsored Products ads but did not purchase',
                'sql_query': """/* Audience Instructional Query: Audiences who clicked Sponsored Products ads but have not purchased */
-- Optional update: To add Sponsored Products (SP) campaign filters, add the campaign names to campaign CTE and uncomment lines [1 of 2] and [2 of 2] below.
-- Note that you must use the campaign name, as we do not have a customer-facing campaign_id available for Sponsored Ads.
WITH SP (campaign) AS (
  VALUES
    {{campaign_list}}
),
clicks AS (
  SELECT
    user_id
  FROM
    sponsored_ads_traffic_for_audiences
  WHERE
    clicks > 0
    AND ad_product_type = '{{ad_product_type}}'
    {{campaign_filter_clicks}}
),
purchases AS (
  SELECT
    user_id
  FROM
    amazon_attributed_events_by_traffic_time_for_audiences
  WHERE
    total_purchases > 0
    AND ad_product_type = '{{ad_product_type}}'
    {{campaign_filter_purchases}}
)
SELECT
  user_id
FROM
  clicks
WHERE
  user_id NOT IN (
    SELECT
      user_id
    FROM
      purchases
  )""",
                'parameters_schema': {
                    'ad_product_type': {
                        'type': 'string',
                        'default': 'sponsored_products',
                        'description': 'Type of sponsored ad to target'
                    },
                    'campaign_list': {
                        'type': 'string',
                        'default': "('SP_campaign_name1'), ('SP_campaign_name2')",
                        'description': 'List of campaign names in SQL VALUES format'
                    },
                    'campaign_filter_clicks': {
                        'type': 'string',
                        'default': '-- AND campaign IN (SELECT campaign FROM SP)',
                        'description': 'Optional campaign filter for clicks CTE'
                    },
                    'campaign_filter_purchases': {
                        'type': 'string',
                        'default': '-- AND campaign IN (SELECT campaign FROM SP)',
                        'description': 'Optional campaign filter for purchases CTE'
                    }
                },
                'default_parameters': {
                    'ad_product_type': 'sponsored_products',
                    'campaign_list': "('SP_campaign_name1'), ('SP_campaign_name2')",
                    'campaign_filter_clicks': '-- AND campaign IN (SELECT campaign FROM SP)',
                    'campaign_filter_purchases': '-- AND campaign IN (SELECT campaign FROM SP)'
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': 'This audience query creates a targetable audience in Amazon DSP. Remember to uncomment the campaign filters if you want to focus on specific campaigns.'
            },
            {
                'guide_id': guide_id,
                'title': 'All Sponsored Ads - Clicked but Not Purchased',
                'description': 'Create an audience including all sponsored ads types',
                'sql_query': """/* Audience: All Sponsored Ads - Clicked but Not Purchased */
WITH clicks AS (
  SELECT
    user_id
  FROM
    sponsored_ads_traffic_for_audiences
  WHERE
    clicks > 0
    -- No ad_product_type filter - includes all sponsored ads
),
purchases AS (
  SELECT
    user_id
  FROM
    amazon_attributed_events_by_traffic_time_for_audiences
  WHERE
    total_purchases > 0
    -- No ad_product_type filter - includes all sponsored ads
)
SELECT
  user_id
FROM
  clicks
WHERE
  user_id NOT IN (
    SELECT
      user_id
    FROM
      purchases
  )""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 4,
                'query_type': 'variation',
                'interpretation_notes': 'Use this broader audience when you want to capture all users who showed interest across any sponsored ad type.'
            },
            {
                'guide_id': guide_id,
                'title': 'High-Intent Non-Converters',
                'description': 'Target users who clicked multiple times but have not purchased',
                'sql_query': """/* Audience: High-Intent Non-Converters */
WITH multiple_clicks AS (
  SELECT
    user_id,
    SUM(clicks) as total_clicks
  FROM
    sponsored_ads_traffic_for_audiences
  WHERE
    ad_product_type = '{{ad_product_type}}'
  GROUP BY
    user_id
  HAVING
    SUM(clicks) >= {{min_clicks}}
),
purchases AS (
  SELECT
    user_id
  FROM
    amazon_attributed_events_by_traffic_time_for_audiences
  WHERE
    total_purchases > 0
    AND ad_product_type = '{{ad_product_type}}'
)
SELECT
  user_id
FROM
  multiple_clicks
WHERE
  user_id NOT IN (
    SELECT
      user_id
    FROM
      purchases
  )""",
                'parameters_schema': {
                    'ad_product_type': {
                        'type': 'string',
                        'default': 'sponsored_products',
                        'description': 'Type of sponsored ad'
                    },
                    'min_clicks': {
                        'type': 'integer',
                        'default': 3,
                        'description': 'Minimum number of clicks to qualify as high-intent'
                    }
                },
                'default_parameters': {
                    'ad_product_type': 'sponsored_products',
                    'min_clicks': 3
                },
                'display_order': 5,
                'query_type': 'variation',
                'interpretation_notes': 'These users show high purchase intent. Consider special offers or incentives for this audience.'
            },
            {
                'guide_id': guide_id,
                'title': 'Recent Clickers Without Purchase',
                'description': 'Focus on users who clicked recently but have not purchased',
                'sql_query': """/* Audience: Recent Clickers Without Purchase */
WITH recent_clicks AS (
  SELECT
    user_id,
    MAX(event_dt_utc) as last_click_date
  FROM
    sponsored_ads_traffic_for_audiences
  WHERE
    clicks > 0
    AND ad_product_type = '{{ad_product_type}}'
  GROUP BY
    user_id
  HAVING
    MAX(event_dt_utc) >= CURRENT_DATE - INTERVAL '{{recency_days}}' DAY
),
purchases AS (
  SELECT
    user_id
  FROM
    amazon_attributed_events_by_traffic_time_for_audiences
  WHERE
    total_purchases > 0
    AND ad_product_type = '{{ad_product_type}}'
)
SELECT
  user_id
FROM
  recent_clicks
WHERE
  user_id NOT IN (
    SELECT
      user_id
    FROM
      purchases
  )""",
                'parameters_schema': {
                    'ad_product_type': {
                        'type': 'string',
                        'default': 'sponsored_products',
                        'description': 'Type of sponsored ad'
                    },
                    'recency_days': {
                        'type': 'integer',
                        'default': 7,
                        'description': 'Number of days to look back for recent clicks'
                    }
                },
                'default_parameters': {
                    'ad_product_type': 'sponsored_products',
                    'recency_days': 7
                },
                'display_order': 6,
                'query_type': 'variation',
                'interpretation_notes': 'Recent clickers are more likely to remember your product and convert with remarketing.'
            },
            {
                'guide_id': guide_id,
                'title': 'Click Intensity Distribution',
                'description': 'Analyze how click frequency relates to purchase behavior',
                'sql_query': """/* Exploratory Query: Click Intensity Distribution */
WITH user_clicks AS (
  SELECT
    user_id,
    SUM(clicks) as total_clicks
  FROM
    sponsored_ads_traffic
  WHERE
    ad_product_type = '{{ad_product_type}}'
    AND event_dt >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
  GROUP BY
    user_id
),
user_purchases AS (
  SELECT
    user_id,
    SUM(total_purchases) as total_purchases
  FROM
    amazon_attributed_events_by_traffic_time
  WHERE
    ad_product_type = '{{ad_product_type}}'
    AND event_dt >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
  GROUP BY
    user_id
),
click_buckets AS (
  SELECT
    uc.user_id,
    CASE 
      WHEN uc.total_clicks = 1 THEN '1 click'
      WHEN uc.total_clicks BETWEEN 2 AND 3 THEN '2-3 clicks'
      WHEN uc.total_clicks BETWEEN 4 AND 5 THEN '4-5 clicks'
      ELSE '6+ clicks'
    END as click_count,
    CASE WHEN up.total_purchases > 0 THEN 1 ELSE 0 END as purchased
  FROM
    user_clicks uc
    LEFT JOIN user_purchases up ON uc.user_id = up.user_id
)
SELECT
  click_count,
  COUNT(*) as user_count,
  SUM(purchased) as purchasers,
  ROUND((SUM(purchased)::FLOAT / COUNT(*)) * 100, 2) as purchase_rate
FROM
  click_buckets
GROUP BY
  click_count
ORDER BY
  CASE 
    WHEN click_count = '1 click' THEN 1
    WHEN click_count = '2-3 clicks' THEN 2
    WHEN click_count = '4-5 clicks' THEN 3
    ELSE 4
  END""",
                'parameters_schema': {
                    'ad_product_type': {
                        'type': 'string',
                        'default': 'sponsored_products',
                        'description': 'Type of sponsored ad'
                    },
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to analyze'
                    }
                },
                'default_parameters': {
                    'ad_product_type': 'sponsored_products',
                    'lookback_days': 30
                },
                'display_order': 7,
                'query_type': 'exploratory',
                'interpretation_notes': 'Understand how click frequency correlates with purchase likelihood to optimize your audience segmentation strategy.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results for key queries
                if query['title'] == 'Click-to-Purchase Analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Click-to-Purchase Funnel Analysis',
                        'sample_data': {
                            'rows': [
                                {'ad_product_type': 'sponsored_products', 'clickers': 500000, 'purchasers': 25000, 'non_purchasers': 475000, 'conversion_rate': 5.00},
                                {'ad_product_type': 'sponsored_brands', 'clickers': 350000, 'purchasers': 14000, 'non_purchasers': 336000, 'conversion_rate': 4.00},
                                {'ad_product_type': 'sponsored_display', 'clickers': 250000, 'purchasers': 7500, 'non_purchasers': 242500, 'conversion_rate': 3.00}
                            ]
                        },
                        'interpretation_markdown': """**Key Insights:**

- **Sponsored Products** has the largest opportunity with 475,000 non-converting clickers
- **Conversion rates** are low across all ad types (3-5%), indicating significant remarketing potential
- **Total opportunity**: Over 1 million users clicked but didn't purchase across all ad types

**Recommendation:** Start with Sponsored Products remarketing due to the large audience size and slightly better baseline conversion rate.""",
                        'insights': [
                            '95% of Sponsored Products clickers don\'t convert - huge remarketing opportunity',
                            'Sponsored Display has the lowest conversion rate, may benefit most from remarketing',
                            'Combined audience of 1M+ non-converters available for targeting'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example for Click-to-Purchase Analysis")
                
                elif query['title'] == 'Campaign Opportunity Assessment':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Top Campaigns for Remarketing',
                        'sample_data': {
                            'rows': [
                                {'campaign': 'SP_BrandName_Category', 'clickers': 45000, 'purchasers': 2250, 'opportunity_size': 42750, 'conversion_rate': 5.00},
                                {'campaign': 'SP_NewProduct_Launch', 'clickers': 38000, 'purchasers': 1520, 'opportunity_size': 36480, 'conversion_rate': 4.00},
                                {'campaign': 'SP_Competitor_Conquest', 'clickers': 32000, 'purchasers': 960, 'opportunity_size': 31040, 'conversion_rate': 3.00},
                                {'campaign': 'SP_Seasonal_Promotion', 'clickers': 28000, 'purchasers': 2800, 'opportunity_size': 25200, 'conversion_rate': 10.00},
                                {'campaign': 'SP_Bestseller_Always_On', 'clickers': 25000, 'purchasers': 3750, 'opportunity_size': 21250, 'conversion_rate': 15.00}
                            ]
                        },
                        'interpretation_markdown': """**Campaign Performance Analysis:**

- **SP_BrandName_Category**: Largest opportunity with 42,750 non-converters
- **SP_Competitor_Conquest**: Lowest conversion rate (3%), needs aggressive remarketing
- **SP_Seasonal_Promotion**: Despite 10% conversion, still has 25,200 non-converters
- **SP_Bestseller_Always_On**: Best conversion rate (15%) but smaller opportunity

**Strategy Recommendations:**
1. **Immediate focus**: SP_BrandName_Category and SP_NewProduct_Launch campaigns
2. **Test incentives**: For SP_Competitor_Conquest due to low conversion
3. **Seasonal urgency**: Add time-limited offers for SP_Seasonal_Promotion non-converters""",
                        'insights': [
                            'Top 3 campaigns represent 110,270 non-converting clickers',
                            'Competitor conquest campaigns need special attention with 97% non-conversion',
                            'Even high-performing campaigns have significant remarketing opportunities'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example for Campaign Opportunity Assessment")
                
                elif query['title'] == 'Click Intensity Distribution':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Click Frequency Analysis',
                        'sample_data': {
                            'rows': [
                                {'click_count': '1 click', 'user_count': 400000, 'purchasers': 14000, 'purchase_rate': 3.50},
                                {'click_count': '2-3 clicks', 'user_count': 75000, 'purchasers': 6150, 'purchase_rate': 8.20},
                                {'click_count': '4-5 clicks', 'user_count': 20000, 'purchasers': 2500, 'purchase_rate': 12.50},
                                {'click_count': '6+ clicks', 'user_count': 5000, 'purchasers': 390, 'purchase_rate': 7.80}
                            ]
                        },
                        'interpretation_markdown': """**Click Behavior Insights:**

- **Single clickers**: Largest segment (400K users) but lowest conversion (3.5%)
- **2-3 clicks**: Sweet spot with 8.2% conversion, showing increased interest
- **4-5 clicks**: Highest conversion rate (12.5%), indicating strong intent
- **6+ clicks**: Conversion drops to 7.8%, possible comparison shoppers or price-sensitive users

**Segmentation Strategy:**
1. **Single clickers**: Use broad remarketing with product benefits
2. **2-3 clickers**: Target with social proof and reviews
3. **4-5 clickers**: Offer incentives or limited-time discounts
4. **6+ clickers**: Address specific concerns or offer personalized support""",
                        'insights': [
                            'Users with 4-5 clicks are 3.5x more likely to convert than single clickers',
                            '80% of all clickers only click once - need different messaging',
                            'Over-clickers (6+) may need different approach - possibly stuck in consideration'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example for Click Intensity Distribution")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'clicks',
                'display_name': 'Clicks',
                'definition': 'Number of clicks on sponsored ads',
                'metric_type': 'metric',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'impressions',
                'display_name': 'Impressions',
                'definition': 'Number of ad impressions shown to users',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_purchases',
                'display_name': 'Total Purchases',
                'definition': 'Number of purchases attributed to ads',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'clickers',
                'display_name': 'Clickers',
                'definition': 'Count of unique users who clicked on ads',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'purchasers',
                'display_name': 'Purchasers',
                'definition': 'Count of unique users who made a purchase',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'non_purchasers',
                'display_name': 'Non-Purchasers',
                'definition': 'Count of clickers who have not made a purchase',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'opportunity_size',
                'display_name': 'Opportunity Size',
                'definition': 'Number of clickers who haven\'t purchased (potential audience size)',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate',
                'display_name': 'Conversion Rate',
                'definition': 'Percentage of clickers who make a purchase',
                'metric_type': 'metric',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_id',
                'display_name': 'User ID',
                'definition': 'Unique identifier for users in AMC',
                'metric_type': 'dimension',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'ad_product_type',
                'display_name': 'Ad Product Type',
                'definition': 'Type of sponsored ad (sponsored_products, sponsored_brands, sponsored_display)',
                'metric_type': 'dimension',
                'display_order': 10
            },
            {
                'guide_id': guide_id,
                'metric_name': 'campaign',
                'display_name': 'Campaign',
                'definition': 'Campaign name from sponsored ads',
                'metric_type': 'dimension',
                'display_order': 11
            },
            {
                'guide_id': guide_id,
                'metric_name': 'event_dt_utc',
                'display_name': 'Event Date UTC',
                'definition': 'Date and time of the event in UTC',
                'metric_type': 'dimension',
                'display_order': 12
            },
            {
                'guide_id': guide_id,
                'metric_name': 'last_click_date',
                'display_name': 'Last Click Date',
                'definition': 'Most recent click date for a user',
                'metric_type': 'dimension',
                'display_order': 13
            },
            {
                'guide_id': guide_id,
                'metric_name': 'click_count',
                'display_name': 'Click Count Bucket',
                'definition': 'Grouping of users by number of clicks (1, 2-3, 4-5, 6+)',
                'metric_type': 'dimension',
                'display_order': 14
            },
            {
                'guide_id': guide_id,
                'metric_name': 'purchase_rate',
                'display_name': 'Purchase Rate',
                'definition': 'Percentage of users in a segment who made a purchase',
                'metric_type': 'metric',
                'display_order': 15
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created 'Audience that clicked sponsored ads but did not purchase' guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_audience_clicked_not_purchased_guide()
    sys.exit(0 if success else 1)