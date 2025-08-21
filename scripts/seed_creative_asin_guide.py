#!/usr/bin/env python3
"""
Seed script for Creative ASIN Impact Analysis Build Guide
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

def create_creative_asin_guide():
    """Create the Creative ASIN Impact Analysis guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_creative_asin_impact',
            'name': 'Creative ASIN Impact Analysis',
            'category': 'ASIN Analysis',
            'short_description': 'Understand how creative ASINs in sponsored ads influence purchase behaviors and optimize creative selections for better campaign performance.',
            'tags': ['ASIN analysis', 'Performance deep dive', 'On-Amazon conversions', 'Creative optimization'],
            'icon': 'Package',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 45,
            'prerequisites': [
                'Relevant campaign data (Sponsored Products or Sponsored Display) in a single AMC instance',
                'Note: Only ASIN conversions will be counted as purchases'
            ],
            'is_published': True,
            'display_order': 1,
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

This guide helps you better understand how creative ASINs (that is, ASINs featured in sponsored ads creative) influence purchase behaviors. By identifying which creative ASINs contribute most effectively to purchases, you can better optimize creative selections in sponsored ads campaigns.

## 1.2 Requirements

To use this query, advertisers need:
- Relevant campaign data (Sponsored Products or Sponsored Display) in a single AMC instance
- **Note:** Only ASIN conversions will be counted as purchases""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Data Returned

This guide provides one query:

**Creative ASIN Impact Analysis** – Returns the ASINs featured in your campaign creatives, the number of unique customers exposed to each creative ASIN, and the associated ASINs they went on to purchase.

For each pair of creative ASIN and purchased ASIN, the analysis includes:
- The number of distinct purchasers
- The total number of purchases
- Purchase behavior patterns following exposure to specific creative ASINs

## 2.2 Tables Used

- **sponsored_ads_traffic**: This table provides sponsored ads traffic data, capturing user_id to identify exposed audiences segmented by creative_asin
- **amazon_attributed_events_by_traffic_time**: This table is used to track all ASIN conversions from the exposed audience during the analysis period, enabling measurement of purchase behaviors""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': '3. Data Interpretation Instructions',
                'content_markdown': """## 3.1 Example Query Results

*This data is for instructional purposes only. Your results will differ.*

### Query: Creative ASIN Impact Analysis

| asin_in_creative | unique_customers_exposed | asin_purchased | occurrences | total_purchases |
|------------------|-------------------------|----------------|-------------|-----------------|
| B00000000B | 6000 | B0000000D | 50 | 60 |
| B00000000B | 6000 | B0000000E | 200 | 220 |
| B00000000B | 6000 | B0000000F | 100 | 140 |
| B00000000C | 3000 | B0000000E | 20 | 30 |
| B00000000C | 3000 | B0000000F | 10 | 20 |

## 3.2 Metrics and Dimensions

See the Metrics & Dimensions section below for detailed definitions.

## 3.3 Insights and Data Interpretation

### What products are users purchasing after seeing the creative?

By analyzing the output, it's possible to determine which ASINs led to most purchases, and how many unique users converted.

**For example, in the sample result:**
- Creative ASIN B00000000B led to 350 unique users (5.8%) purchasing products B0000000D, B0000000E or B0000000F, out of 6000 unique customers exposed to creative featuring B00000000B
- In contrast, creative ASIN B00000000C resulted in 30 unique users (1%) purchasing products B0000000E or B0000000F, out of 3000 unique customers exposed to the creative featuring B00000000C

**Sample Recommendation:** The advertiser should consider prioritizing creative ASIN B00000000B or testing a different ASIN in the creative going forward. If the campaign is still running, it may also be worth increasing the budget for high-performing creative ASINs.

### Key Considerations

**Note:** The metrics for occurrences and total_purchases may differ from standard reporting, because the same customer may appear multiple times if they were exposed to multiple creative ASINs that are being evaluated. This helps capture the impact of each creative ASIN independently, but may lead to duplicated counts across creative ASIN and purchased ASIN pair scenarios.""",
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
                'title': 'Exploratory query for campaigns and creative ASINs',
                'description': 'Explore available campaigns and creative ASINs in your AMC instance to identify what data is available for analysis.',
                'sql_query': """-- Exploratory query to understand available creative ASINs
WITH creative_asin_summary AS (
    SELECT 
        campaign_id,
        campaign_name,
        creative_asin,
        COUNT(DISTINCT user_id) as unique_impressions,
        COUNT(*) as total_impressions,
        MIN(event_dt) as first_impression,
        MAX(event_dt) as last_impression
    FROM sponsored_ads_traffic
    WHERE 
        creative_asin IS NOT NULL
        AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
    GROUP BY 
        campaign_id,
        campaign_name,
        creative_asin
)
SELECT 
    campaign_name,
    creative_asin,
    unique_impressions,
    total_impressions,
    first_impression,
    last_impression,
    DATEDIFF('day', first_impression, last_impression) + 1 as campaign_duration_days
FROM creative_asin_summary
ORDER BY unique_impressions DESC
LIMIT 100""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for campaign data'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query helps you understand which creative ASINs are being used in your campaigns and their exposure levels. Use this to identify high-volume creative ASINs for deeper analysis.'
            },
            {
                'guide_id': guide_id,
                'title': 'Creative ASIN Impact Analysis',
                'description': 'Analyze the purchase behavior of customers exposed to specific creative ASINs to understand their effectiveness.',
                'sql_query': """-- Creative ASIN Impact Analysis
-- Analyzes purchase behavior following exposure to creative ASINs
WITH exposed_users AS (
    -- Get users exposed to each creative ASIN
    SELECT DISTINCT
        creative_asin as asin_in_creative,
        user_id,
        MIN(event_dt) as first_exposure_date
    FROM sponsored_ads_traffic
    WHERE 
        creative_asin IS NOT NULL
        AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
        AND campaign_type IN ({{campaign_types}})
    GROUP BY 
        creative_asin,
        user_id
),
exposure_summary AS (
    -- Count unique exposed customers per creative ASIN
    SELECT 
        asin_in_creative,
        COUNT(DISTINCT user_id) as unique_customers_exposed
    FROM exposed_users
    GROUP BY asin_in_creative
),
purchase_behavior AS (
    -- Track purchases by exposed users
    SELECT 
        eu.asin_in_creative,
        aae.conversion_asin as asin_purchased,
        COUNT(DISTINCT eu.user_id) as occurrences,
        COUNT(*) as total_purchases
    FROM exposed_users eu
    INNER JOIN amazon_attributed_events_by_traffic_time aae
        ON eu.user_id = aae.user_id
        AND aae.event_dt >= eu.first_exposure_date
        AND aae.event_dt <= DATE_ADD('day', {{attribution_window}}, eu.first_exposure_date)
    WHERE 
        aae.conversion_asin IS NOT NULL
        AND aae.purchase_flag = 1
    GROUP BY 
        eu.asin_in_creative,
        aae.conversion_asin
)
-- Final output combining exposure and purchase data
SELECT 
    pb.asin_in_creative,
    es.unique_customers_exposed,
    pb.asin_purchased,
    pb.occurrences,
    pb.total_purchases,
    ROUND(CAST(pb.occurrences AS DOUBLE) / CAST(es.unique_customers_exposed AS DOUBLE) * 100, 2) as conversion_rate_pct
FROM purchase_behavior pb
JOIN exposure_summary es
    ON pb.asin_in_creative = es.asin_in_creative
WHERE 
    pb.occurrences >= {{min_occurrences}}
ORDER BY 
    pb.asin_in_creative,
    pb.total_purchases DESC""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for exposure data'
                    },
                    'attribution_window': {
                        'type': 'integer',
                        'default': 14,
                        'description': 'Attribution window in days after exposure'
                    },
                    'campaign_types': {
                        'type': 'array',
                        'default': ['Sponsored Products', 'Sponsored Display'],
                        'description': 'Campaign types to include in analysis'
                    },
                    'min_occurrences': {
                        'type': 'integer',
                        'default': 5,
                        'description': 'Minimum number of purchasers to include in results'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'attribution_window': 14,
                    'campaign_types': ['Sponsored Products', 'Sponsored Display'],
                    'min_occurrences': 5
                },
                'display_order': 2,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Focus on creative ASINs with high conversion rates and significant purchase volumes. Compare the performance across different purchased ASINs to understand cross-selling opportunities.'
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
                        'example_name': 'Sample Analysis Results',
                        'sample_data': {
                            'rows': [
                                {'asin_in_creative': 'B00000000B', 'unique_customers_exposed': 6000, 'asin_purchased': 'B0000000D', 'occurrences': 50, 'total_purchases': 60, 'conversion_rate_pct': 0.83},
                                {'asin_in_creative': 'B00000000B', 'unique_customers_exposed': 6000, 'asin_purchased': 'B0000000E', 'occurrences': 200, 'total_purchases': 220, 'conversion_rate_pct': 3.33},
                                {'asin_in_creative': 'B00000000B', 'unique_customers_exposed': 6000, 'asin_purchased': 'B0000000F', 'occurrences': 100, 'total_purchases': 140, 'conversion_rate_pct': 1.67},
                                {'asin_in_creative': 'B00000000C', 'unique_customers_exposed': 3000, 'asin_purchased': 'B0000000E', 'occurrences': 20, 'total_purchases': 30, 'conversion_rate_pct': 0.67},
                                {'asin_in_creative': 'B00000000C', 'unique_customers_exposed': 3000, 'asin_purchased': 'B0000000F', 'occurrences': 10, 'total_purchases': 20, 'conversion_rate_pct': 0.33}
                            ]
                        },
                        'interpretation_markdown': """Based on these results:

**High Performer:** Creative ASIN B00000000B shows strong performance with:
- 5.8% overall conversion rate (350 unique purchasers from 6000 exposed)
- Strong cross-selling to product B0000000E (3.33% conversion rate)
- Moderate performance for products B0000000F and B0000000D

**Low Performer:** Creative ASIN B00000000C underperforms with:
- 1% overall conversion rate (30 unique purchasers from 3000 exposed)
- Weak conversion across all purchased ASINs

**Recommendation:** Focus budget on creative ASIN B00000000B and consider testing new creative ASINs to replace B00000000C.""",
                        'insights': [
                            'Creative ASIN B00000000B drives 5.8x higher conversion rate than B00000000C',
                            'Product B0000000E shows the strongest affinity with creative ASIN B00000000B',
                            'Consider bundling or cross-promotion strategies for high-affinity product pairs',
                            'Test new creative ASINs to replace underperforming B00000000C'
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
                'metric_name': 'asin_in_creative',
                'display_name': 'ASIN in Creative',
                'definition': 'ASINs featured in your campaign creatives',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'unique_customers_exposed',
                'display_name': 'Unique Customers Exposed',
                'definition': 'Number of unique users exposed to the campaign creative',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'asin_purchased',
                'display_name': 'ASIN Purchased',
                'definition': 'ASINs purchased by users who were exposed to the creative',
                'metric_type': 'dimension',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'occurrences',
                'display_name': 'Occurrences',
                'definition': 'Number of unique users who purchased a given ASIN (asin_purchased) after being exposed to a specific creative ASIN (asin_in_creative)',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_purchases',
                'display_name': 'Total Purchases',
                'definition': 'Total ad-attributed purchases of a given ASIN (asin_purchased) after exposure to a specific creative ASIN (asin_in_creative). This includes purchases related to both promoted ASINs and brand halo ASINs.',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate_pct',
                'display_name': 'Conversion Rate %',
                'definition': 'Percentage of exposed users who made a purchase (occurrences / unique_customers_exposed * 100)',
                'metric_type': 'metric',
                'display_order': 6
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created Creative ASIN Impact Analysis guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_creative_asin_guide()
    sys.exit(0 if success else 1)