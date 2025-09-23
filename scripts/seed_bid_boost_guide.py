#!/usr/bin/env python3
"""
Seed script for Sponsored Products and Sponsored Brands Bid Boost Performance Analysis Build Guide
This script creates the initial guide content in the database
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

def create_bid_boost_guide():
    """Create the Sponsored Products and Sponsored Brands Bid Boost Performance Analysis guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_bid_boost_performance',
            'name': 'Sponsored Products and Brands Bid Boost Analysis',
            'category': 'Performance Analysis',
            'short_description': 'Analyze the performance impact of bid boosts in Sponsored Products and Sponsored Brands campaigns to optimize bidding strategies.',
            'tags': ['Bidding strategy', 'Performance optimization', 'Sponsored Products', 'Sponsored Brands', 'Bid management'],
            'icon': 'TrendingUp',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 30,
            'prerequisites': [
                'Sponsored Products or Sponsored Brands campaigns with bid boost enabled',
                'At least 30 days of campaign data',
                'Understanding of Amazon\'s bidding strategies'
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

This analysis helps advertisers understand the impact of bid boosts (placement adjustments and bidding strategies) on their Sponsored Products and Sponsored Brands campaigns. By analyzing performance metrics with and without bid boosts, you can optimize your bidding strategies for better ROI.

## 1.2 What You'll Learn

- How bid boosts affect campaign performance metrics
- Which placement adjustments drive the most value
- Optimal bid boost percentages for different campaign types
- Cost-benefit analysis of aggressive bidding strategies

## 1.3 Requirements

- Active Sponsored Products or Sponsored Brands campaigns
- Campaigns using placement bid adjustments or dynamic bidding
- Sufficient data volume for statistical significance""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Data Returned

This analysis provides two main queries:

**Bid Boost Performance Analysis** - Compares campaign performance with different bid boost levels:
- Impressions, clicks, and conversions by bid boost percentage
- Cost metrics (CPC, ACOS) at different boost levels
- ROAS comparison across placement adjustments

**Placement Performance Breakdown** - Analyzes performance by placement type:
- Top of search vs product pages vs rest of search
- Conversion rates by placement
- Optimal bid adjustments per placement

## 2.2 Tables Used

- **sponsored_ads_traffic**: Campaign traffic data including bid information
- **amazon_attributed_events_by_traffic_time**: Conversion events for attribution""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': '3. Data Interpretation',
                'content_markdown': """## 3.1 Example Query Results

*This data is for instructional purposes only. Your results will differ.*

### Query: Bid Boost Performance Analysis

| campaign_name | bid_boost_range | impressions | clicks | conversions | spend | revenue | cpc | acos | roas |
|--------------|-----------------|-------------|--------|-------------|--------|---------|-----|------|------|
| Summer Sale SP | 0-25% | 50000 | 500 | 25 | 250.00 | 1250.00 | 0.50 | 20.0% | 5.00 |
| Summer Sale SP | 26-50% | 75000 | 900 | 50 | 540.00 | 2700.00 | 0.60 | 20.0% | 5.00 |
| Summer Sale SP | 51-100% | 100000 | 1400 | 65 | 980.00 | 3900.00 | 0.70 | 25.1% | 3.98 |
| Summer Sale SP | >100% | 120000 | 1800 | 70 | 1440.00 | 4200.00 | 0.80 | 34.3% | 2.92 |

## 3.2 Insights and Recommendations

**Optimal Bid Boost Range:**
- 26-50% boost maintains ROAS while increasing volume
- >100% boosts decrease efficiency significantly
- Consider placement-specific adjustments instead of blanket increases

**Key Findings:**
- Moderate bid boosts (26-50%) doubled conversions while maintaining ROAS
- Aggressive boosts (>100%) show diminishing returns
- Top of search placements justify higher boosts than product pages

**Sample Recommendation:** Focus on moderate bid boosts (26-50%) for optimal balance of volume and efficiency. Test placement-specific adjustments rather than blanket campaign-level increases.""",
                'display_order': 3,
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
                'title': 'Exploratory query for campaigns with bid adjustments',
                'description': 'Explore available campaigns with bid adjustments to understand data availability.',
                'sql_query': """-- Exploratory query to understand bid boost usage across campaigns
WITH campaign_bid_summary AS (
    SELECT 
        campaign_id,
        campaign_name,
        campaign_type,
        placement,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(*) as total_impressions,
        SUM(clicks) as total_clicks,
        AVG(bid_plus_multiplier) as avg_bid_multiplier,
        MIN(bid_plus_multiplier) as min_bid_multiplier,
        MAX(bid_plus_multiplier) as max_bid_multiplier,
        MIN(event_dt) as first_impression,
        MAX(event_dt) as last_impression
    FROM sponsored_ads_traffic
    WHERE 
        event_dt >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
        AND bid_plus_multiplier IS NOT NULL
        AND campaign_type IN ({{campaign_types}})
    GROUP BY 
        campaign_id,
        campaign_name,
        campaign_type,
        placement
)
SELECT 
    campaign_name,
    campaign_type,
    placement,
    unique_users,
    total_impressions,
    total_clicks,
    ROUND(avg_bid_multiplier, 2) as avg_bid_multiplier,
    ROUND(min_bid_multiplier, 2) as min_bid_multiplier,
    ROUND(max_bid_multiplier, 2) as max_bid_multiplier,
    first_impression,
    last_impression,
    DATEDIFF('day', first_impression, last_impression) + 1 as campaign_duration_days
FROM campaign_bid_summary
WHERE total_impressions >= {{min_impressions}}
ORDER BY total_impressions DESC
LIMIT 50""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for campaign data'
                    },
                    'campaign_types': {
                        'type': 'array',
                        'default': ['Sponsored Products', 'Sponsored Brands'],
                        'description': 'Campaign types to include in analysis'
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'default': 1000,
                        'description': 'Minimum impressions threshold for inclusion'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'campaign_types': ['Sponsored Products', 'Sponsored Brands'],
                    'min_impressions': 1000
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query helps identify campaigns using bid adjustments and their ranges. Use this to understand which campaigns have sufficient data for bid boost analysis.'
            },
            {
                'guide_id': guide_id,
                'title': 'Bid Boost Performance Analysis',
                'description': 'Analyze campaign performance across different bid boost levels to optimize bidding strategy.',
                'sql_query': """-- Bid Boost Performance Analysis for Sponsored Products and Sponsored Brands
WITH campaign_traffic AS (
    -- Get campaign traffic with bid boost information
    SELECT 
        campaign_id,
        campaign_name,
        campaign_type,
        placement,
        bid_plus_multiplier,
        CASE 
            WHEN bid_plus_multiplier <= 1.25 THEN '0-25%'
            WHEN bid_plus_multiplier <= 1.50 THEN '26-50%'
            WHEN bid_plus_multiplier <= 2.00 THEN '51-100%'
            ELSE '>100%'
        END as bid_boost_range,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(*) as impressions,
        SUM(clicks) as clicks,
        SUM(cost) as spend
    FROM sponsored_ads_traffic
    WHERE 
        campaign_type IN ({{campaign_types}})
        AND event_dt >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
        AND bid_plus_multiplier IS NOT NULL
    GROUP BY 
        campaign_id,
        campaign_name,
        campaign_type,
        placement,
        bid_plus_multiplier,
        bid_boost_range
),
conversions AS (
    -- Get conversion data
    SELECT 
        sat.campaign_id,
        sat.bid_plus_multiplier,
        COUNT(DISTINCT aae.order_id) as conversions,
        SUM(aae.purchase_value) as revenue
    FROM sponsored_ads_traffic sat
    INNER JOIN amazon_attributed_events_by_traffic_time aae
        ON sat.user_id = aae.user_id
        AND aae.event_dt >= sat.event_dt
        AND aae.event_dt <= (sat.event_dt + INTERVAL '{{attribution_window}}' DAY)
    WHERE 
        sat.campaign_type IN ({{campaign_types}})
        AND sat.event_dt >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
        AND aae.purchase_flag = 1
    GROUP BY 
        sat.campaign_id,
        sat.bid_plus_multiplier
),
performance_summary AS (
    -- Combine traffic and conversion data
    SELECT 
        ct.campaign_name,
        ct.campaign_type,
        ct.bid_boost_range,
        ct.placement,
        SUM(ct.impressions) as impressions,
        SUM(ct.clicks) as clicks,
        SUM(ct.spend) as spend,
        SUM(c.conversions) as conversions,
        SUM(c.revenue) as revenue
    FROM campaign_traffic ct
    LEFT JOIN conversions c
        ON ct.campaign_id = c.campaign_id
        AND ct.bid_plus_multiplier = c.bid_plus_multiplier
    GROUP BY 
        ct.campaign_name,
        ct.campaign_type,
        ct.bid_boost_range,
        ct.placement
)
-- Final output with calculated metrics
SELECT 
    campaign_name,
    campaign_type,
    bid_boost_range,
    placement,
    impressions,
    clicks,
    conversions,
    spend,
    revenue,
    ROUND(CAST(clicks AS DOUBLE) / NULLIF(impressions, 0) * 100, 2) as ctr,
    ROUND(CAST(conversions AS DOUBLE) / NULLIF(clicks, 0) * 100, 2) as cvr,
    ROUND(spend / NULLIF(clicks, 0), 2) as cpc,
    ROUND(spend / NULLIF(revenue, 0) * 100, 2) as acos,
    ROUND(revenue / NULLIF(spend, 0), 2) as roas
FROM performance_summary
WHERE 
    impressions >= {{min_impressions}}
ORDER BY 
    campaign_name,
    bid_boost_range""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to analyze'
                    },
                    'attribution_window': {
                        'type': 'integer',
                        'default': 14,
                        'description': 'Attribution window in days'
                    },
                    'campaign_types': {
                        'type': 'array',
                        'default': ['Sponsored Products', 'Sponsored Brands'],
                        'description': 'Campaign types to include'
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'default': 1000,
                        'description': 'Minimum impressions threshold'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'attribution_window': 14,
                    'campaign_types': ['Sponsored Products', 'Sponsored Brands'],
                    'min_impressions': 1000
                },
                'display_order': 2,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Focus on the ROAS and ACOS trends across bid boost ranges. Identify the optimal boost level where efficiency starts to decline significantly.'
            },
            {
                'guide_id': guide_id,
                'title': 'Placement-Specific Bid Performance',
                'description': 'Analyze performance by placement type to optimize placement-specific bid adjustments.',
                'sql_query': """-- Placement-Specific Bid Performance Analysis
WITH placement_performance AS (
    SELECT 
        sat.placement,
        sat.campaign_type,
        CASE 
            WHEN sat.bid_plus_multiplier <= 1.25 THEN '0-25%'
            WHEN sat.bid_plus_multiplier <= 1.50 THEN '26-50%'
            WHEN sat.bid_plus_multiplier <= 2.00 THEN '51-100%'
            ELSE '>100%'
        END as bid_boost_range,
        COUNT(DISTINCT sat.user_id) as unique_users,
        COUNT(*) as impressions,
        SUM(sat.clicks) as clicks,
        SUM(sat.cost) as spend,
        COUNT(DISTINCT aae.order_id) as conversions,
        SUM(aae.purchase_value) as revenue
    FROM sponsored_ads_traffic sat
    LEFT JOIN amazon_attributed_events_by_traffic_time aae
        ON sat.user_id = aae.user_id
        AND aae.event_dt >= sat.event_dt
        AND aae.event_dt <= (sat.event_dt + INTERVAL '{{attribution_window}}' DAY)
        AND aae.purchase_flag = 1
    WHERE 
        sat.campaign_type IN ({{campaign_types}})
        AND sat.event_dt >= (CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY)
        AND sat.bid_plus_multiplier IS NOT NULL
        AND sat.placement IS NOT NULL
    GROUP BY 
        sat.placement,
        sat.campaign_type,
        bid_boost_range
)
SELECT 
    placement,
    campaign_type,
    bid_boost_range,
    impressions,
    clicks,
    conversions,
    spend,
    revenue,
    ROUND(CAST(clicks AS DOUBLE) / NULLIF(impressions, 0) * 100, 2) as ctr,
    ROUND(CAST(conversions AS DOUBLE) / NULLIF(clicks, 0) * 100, 2) as cvr,
    ROUND(spend / NULLIF(clicks, 0), 2) as cpc,
    ROUND(spend / NULLIF(revenue, 0) * 100, 2) as acos,
    ROUND(revenue / NULLIF(spend, 0), 2) as roas,
    ROUND(revenue / NULLIF(impressions, 0) * 1000, 2) as revenue_per_thousand_impressions
FROM placement_performance
WHERE 
    impressions >= {{min_impressions}}
ORDER BY 
    placement,
    campaign_type,
    bid_boost_range""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to analyze'
                    },
                    'attribution_window': {
                        'type': 'integer',
                        'default': 14,
                        'description': 'Attribution window in days'
                    },
                    'campaign_types': {
                        'type': 'array',
                        'default': ['Sponsored Products', 'Sponsored Brands'],
                        'description': 'Campaign types to include'
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'default': 500,
                        'description': 'Minimum impressions threshold per placement'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'attribution_window': 14,
                    'campaign_types': ['Sponsored Products', 'Sponsored Brands'],
                    'min_impressions': 500
                },
                'display_order': 3,
                'query_type': 'supplementary',
                'interpretation_notes': 'Compare performance across placements to identify which justify higher bid adjustments. Top of search typically has higher conversion rates but also higher CPCs.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results for the main analysis query
                if query['query_type'] == 'main_analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Bid Boost Analysis Results',
                        'sample_data': {
                            'rows': [
                                {
                                    'campaign_name': 'Summer Sale SP',
                                    'campaign_type': 'Sponsored Products',
                                    'bid_boost_range': '0-25%',
                                    'placement': 'Top of Search',
                                    'impressions': 50000,
                                    'clicks': 500,
                                    'conversions': 25,
                                    'spend': 250.00,
                                    'revenue': 1250.00,
                                    'ctr': 1.00,
                                    'cvr': 5.00,
                                    'cpc': 0.50,
                                    'acos': 20.0,
                                    'roas': 5.00
                                },
                                {
                                    'campaign_name': 'Summer Sale SP',
                                    'campaign_type': 'Sponsored Products',
                                    'bid_boost_range': '26-50%',
                                    'placement': 'Top of Search',
                                    'impressions': 75000,
                                    'clicks': 900,
                                    'conversions': 50,
                                    'spend': 540.00,
                                    'revenue': 2700.00,
                                    'ctr': 1.20,
                                    'cvr': 5.56,
                                    'cpc': 0.60,
                                    'acos': 20.0,
                                    'roas': 5.00
                                },
                                {
                                    'campaign_name': 'Summer Sale SP',
                                    'campaign_type': 'Sponsored Products',
                                    'bid_boost_range': '51-100%',
                                    'placement': 'Top of Search',
                                    'impressions': 100000,
                                    'clicks': 1400,
                                    'conversions': 65,
                                    'spend': 980.00,
                                    'revenue': 3900.00,
                                    'ctr': 1.40,
                                    'cvr': 4.64,
                                    'cpc': 0.70,
                                    'acos': 25.1,
                                    'roas': 3.98
                                },
                                {
                                    'campaign_name': 'Summer Sale SP',
                                    'campaign_type': 'Sponsored Products',
                                    'bid_boost_range': '>100%',
                                    'placement': 'Top of Search',
                                    'impressions': 120000,
                                    'clicks': 1800,
                                    'conversions': 70,
                                    'spend': 1440.00,
                                    'revenue': 4200.00,
                                    'ctr': 1.50,
                                    'cvr': 3.89,
                                    'cpc': 0.80,
                                    'acos': 34.3,
                                    'roas': 2.92
                                }
                            ]
                        },
                        'interpretation_markdown': """Based on these results:

**Optimal Performance Range:** The 26-50% bid boost range shows the best balance:
- Doubled conversions (50 vs 25) compared to 0-25% range
- Maintained strong ROAS of 5.00 and ACOS of 20%
- Increased traffic volume significantly

**Diminishing Returns:** Higher boost ranges show efficiency decline:
- 51-100% range: ROAS drops to 3.98, ACOS increases to 25.1%
- >100% range: ROAS further declines to 2.92, ACOS jumps to 34.3%
- Conversion rate decreases as bid boosts increase

**Key Insights:**
- Moderate bid boosts (26-50%) maximize volume while maintaining efficiency
- Aggressive bidding (>100%) significantly impacts profitability
- CTR increases with bid boosts, but CVR decreases, suggesting lower-intent traffic

**Recommendations:**
1. Focus budget on the 26-50% bid boost range for optimal performance
2. Test placement-specific adjustments rather than blanket increases
3. Monitor CVR trends closely when increasing bid boosts
4. Consider separate strategies for volume vs efficiency goals""",
                        'insights': [
                            '26-50% bid boost range delivers optimal balance of volume and efficiency',
                            'Bid boosts >100% reduce ROAS by 42% compared to moderate levels',
                            'Conversion rates decline as bid boosts increase, indicating lower-quality traffic',
                            'CTR improvements plateau around 50% bid boost level'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example results")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'bid_boost_range',
                'display_name': 'Bid Boost Range',
                'definition': 'Categorized ranges of bid adjustment percentages (0-25%, 26-50%, 51-100%, >100%)',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'placement',
                'display_name': 'Placement',
                'definition': 'Ad placement location (Top of Search, Product Pages, Rest of Search)',
                'metric_type': 'dimension',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'impressions',
                'display_name': 'Impressions',
                'definition': 'Total number of times ads were displayed to users',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'clicks',
                'display_name': 'Clicks',
                'definition': 'Total number of clicks on sponsored ads',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversions',
                'display_name': 'Conversions',
                'definition': 'Number of purchase events attributed to ad exposure',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'spend',
                'display_name': 'Spend',
                'definition': 'Total advertising spend across the analyzed period',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'revenue',
                'display_name': 'Revenue',
                'definition': 'Total attributed purchase value from ad-exposed customers',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'ctr',
                'display_name': 'Click-Through Rate (CTR)',
                'definition': 'Percentage of impressions that resulted in clicks (clicks/impressions * 100)',
                'metric_type': 'metric',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'cvr',
                'display_name': 'Conversion Rate (CVR)',
                'definition': 'Percentage of clicks that resulted in conversions (conversions/clicks * 100)',
                'metric_type': 'metric',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'cpc',
                'display_name': 'Cost Per Click (CPC)',
                'definition': 'Average cost paid for each click (spend/clicks)',
                'metric_type': 'metric',
                'display_order': 10
            },
            {
                'guide_id': guide_id,
                'metric_name': 'acos',
                'display_name': 'Advertising Cost of Sale (ACOS)',
                'definition': 'Advertising spend as a percentage of attributed revenue (spend/revenue * 100)',
                'metric_type': 'metric',
                'display_order': 11
            },
            {
                'guide_id': guide_id,
                'metric_name': 'roas',
                'display_name': 'Return on Ad Spend (ROAS)',
                'definition': 'Revenue generated per dollar of ad spend (revenue/spend)',
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
        
        logger.info("✅ Successfully created Sponsored Products and Brands Bid Boost Analysis guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_bid_boost_guide()
    sys.exit(0 if success else 1)