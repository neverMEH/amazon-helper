#!/usr/bin/env python3
"""
Seed script for Amazon Ad Server - DCO and Target Audience Signals Build Guide
This script creates the DCO and Target Audience signals guide content in the database
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

def create_dco_target_audience_guide():
    """Create the Amazon Ad Server - DCO and Target Audience Signals guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_dco_target_audience_signals',
            'name': 'Amazon Ad Server - DCO and Target Audience Signals',
            'category': 'Creative Optimization',
            'short_description': 'Learn how to query Dynamic Creative Optimization (DCO) and Target Audience (TA) signals in Amazon Ad Server tables to optimize creative personalization and version performance.',
            'tags': ['ad server', 'DCO', 'dynamic creative', 'target audience', 'creative personalization', 'version performance', 'smart items'],
            'icon': 'Layers',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 30,
            'prerequisites': [
                'DCO campaigns or Target Audiences configured in Amazon Ad Server',
                'Understanding of dynamic creative optimization concepts',
                'Basic knowledge of creative versioning',
                'Familiarity with audience targeting'
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

This Instructional Query (IQ) will help you understand how to query Dynamic Creative Optimization (DCO) and Target Audience (TA) signals in Amazon Ad Server tables.

DCO is a creative personalization capability available to Amazon Ad Server advertisers. DCO allows advertisers to create multiple versions of the same ad by dynamically modifying elements in the creative (e.g. copy text, images) and automatically selecting the best-performing versions to show to specific Target Audiences (rule-based creative selection segments defined in the ad server).

You can use DCO and TA insights for a variety of purposes, including:
- Granular performance evaluation of the impact of each version on your ASIN or brand site conversions
- Version-level analysis of Amazon DSP spend
- Version-level engagement of Amazon Audiences

Note that TA insights are also available to advertisers who use delivery groups in Amazon Ad Server, and are not dependent on DCO usage.

## 1.2 Requirements

Advertisers must run DCO campaigns and/or use TAs to target their delivery groups or versions in Amazon Ad Server to use this IQ.

## 1.3 Backfill and Data Availability

DCO and TA signals are available to query from adserver_traffic and adserver_traffic_by_user_segment starting on May 01, 2023 or the instance creation date, whichever is later. Before this date, there are no DCO or TA signals in either table.""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Tables Used

- **adserver_traffic**: This table includes impressions, clicks and interactions (video and viewability) measured by Amazon Ad Server. The events in this table now contain dimensions related to DCO versions and TAs.

- **adserver_traffic_by_user_segment**: This table includes Amazon audience segment-level information for impressions and clicks that are measured by the Amazon Ad Server and matched to the Amazon user ID value. The events in this table now contain dimensions related to DCO versions and TAs.

## 2.2 Key Fields for DCO/TA Analysis

The following new fields enable DCO and TA analysis:

| Field | Description | Example |
|-------|-------------|---------|
| `is_dco_ad` | Boolean flag indicating if the ad uses DCO | TRUE/FALSE |
| `version_id` | Unique internal identifier of a DCO ad version | 12345 |
| `version_name` | Advertiser-defined display name of a DCO version | "Spanish_v1" |
| `smart_items_list` | Dynamic elements in the version | "headline:Oferta Especial\|,cta:Comprar Ahora" |
| `target_audience_id` | Unique identifier of Target Audience | 67890 |
| `target_audience_name` | Display name of Target Audience | "High Value Customers" |

## 2.3 Query Patterns

When querying DCO data, follow these patterns:
1. Always filter by `is_dco_ad = TRUE` to get only DCO ads
2. Group by `version_id` for consistent results (version names can change)
3. Use SIMILAR TO operator for smart item filtering
4. Join with conversion tables for performance analysis""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': '3. Data Interpretation Instructions',
                'content_markdown': """## 3.1 Example Query Results

### 3.1.1 DCO Ad Metadata Query Output

*This data is for instructional purposes only. Your results will differ.*

| advertiser | campaign | ad | version_name | version_id | target_audience_name | smart_items_list |
|------------|----------|-----|--------------|------------|---------------------|------------------|
| BrandX | Summer Sale | Display_300x250 | Spanish_v1 | 12345 | Spanish Speakers | headline:Oferta de Verano\|,cta:Comprar Ahora\|,image:summer_es.jpg |
| BrandX | Summer Sale | Display_300x250 | German_v1 | 12346 | German Market | headline:Sommerangebot\|,cta:Jetzt Kaufen\|,image:summer_de.jpg |
| BrandX | Summer Sale | Display_300x250 | English_v1 | 12347 | US Market | headline:Summer Sale\|,cta:Shop Now\|,image:summer_en.jpg |

### 3.1.2 DCO Version Performance Query Output

*Daily performance breakdown by version:*

| day_of_month | campaign | version_name | impressions | clicks | total_conversions | CTR | conversion_revenue |
|--------------|----------|--------------|-------------|--------|-------------------|-----|-------------------|
| 2024-01-15 | Summer Sale | Spanish_v1 | 50000 | 1500 | 150 | 3.00% | $4,500 |
| 2024-01-15 | Summer Sale | German_v1 | 30000 | 750 | 60 | 2.50% | $2,100 |
| 2024-01-15 | Summer Sale | English_v1 | 80000 | 2000 | 180 | 2.50% | $5,400 |

### 3.1.3 DCO Impressions by Amazon DSP Audience Segment Query Output

*Version performance across behavioral segments:*

| version_name | behavior_segment_name | impressions |
|--------------|----------------------|-------------|
| Spanish_v1 | IM - Home and Garden | 15000 |
| Spanish_v1 | IM - Health, Beauty or Fashion | 20000 |
| German_v1 | IM - Electronics | 12000 |
| German_v1 | IM - Home and Garden | 8000 |
| English_v1 | IM - Health, Beauty or Fashion | 35000 |

### 3.1.4 DCO Impressions by Specific Smart Item Value Query Output

*Filtering by specific creative elements:*

| ad | version_name | smart_items_list | impressions |
|----|--------------|------------------|-------------|
| Display_300x250 | Discount_v1 | headline:50% Off Today\|,cta:Shop Now | 45000 |
| Display_300x250 | Discount_v2 | headline:Limited Time Sale\|,cta:Shop Now | 38000 |
| Display_728x90 | Premium_v1 | headline:Premium Collection\|,cta:Explore | 22000 |

## 3.2 Dimensions and Metrics Defined

### New DCO/TA Dimensions:

| Dimension | Type | Description |
|-----------|------|-------------|
| **version_id** | INTEGER | Unique internal identifier of an Amazon Ad Server DCO ad version |
| **version_name** | STRING | Advertiser-defined display name of an Amazon Ad Server DCO ad version at the time of serving |
| **smart_items_list** | STRING | List of names and values of all dynamic elements in a particular Amazon Ad Server ad version, separated by pipe and comma ("\|,") |
| **target_audience_id** | INTEGER | Unique internal identifier of an Amazon Ad Server Target Audience |
| **target_audience_name** | STRING | Advertiser-defined display name of an Amazon Ad Server Target Audience |
| **is_dco_ad** | BOOLEAN | Boolean field that indicates if the ad uses DCO |

## 3.3 Insights and Data Interpretation

### Key Considerations When Analyzing DCO Signals:

**Version Metadata Tracking:**
- Version metadata (version_name and smart_items_list) is recorded at event serving time
- If you alter version names or dynamic items after campaign starts, group by version_id or combine results
- Versions are unique to each master ad and shared with placement ads

**Data Filtering Best Practices:**
- Non-DCO events will have null values in version_id and target_audience_id
- Use `is_dco_ad` column to filter for DCO ads only (don't rely on version_id as it may be null for default ads)
- Amazon Ad Server Target Audiences are different from Amazon DSP behavioral audiences

**Performance Analysis Tips:**
- Compare CTR and conversion rates across versions to identify top performers
- Analyze performance by Target Audience to understand segment-specific preferences
- Use smart items filtering to isolate the impact of specific creative elements
- Monitor version performance over time to identify trends and optimization opportunities

### Sample Insights from Example Data:

**Language Localization Impact:**
- Spanish version shows highest CTR (3.00%) indicating strong resonance with Spanish-speaking audience
- German version has lower volume but decent engagement (2.50% CTR)
- English version drives highest volume and revenue despite average CTR

**Audience Segment Preferences:**
- Spanish speakers over-index in "Health, Beauty or Fashion" category
- German market shows interest in "Electronics" category
- Consider tailoring creative elements to match segment preferences

**Recommendations:**
1. Increase budget allocation to Spanish_v1 given superior CTR performance
2. Test additional smart item variations for underperforming versions
3. Create segment-specific versions based on behavioral audience insights
4. Monitor version fatigue and refresh creative elements periodically""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'related_queries',
                'title': '4. Related Instructional Queries',
                'content_markdown': """## 4.1 Extended IQs for DCO and TA Analysis

The following Instructional Queries have been extended to allow DCO and TA insights extraction:

### Amazon Ad Server - Daily Performance With ASIN Conversions
- Now includes version-level ASIN conversion tracking
- Enables ROI analysis per creative version
- Supports Target Audience conversion attribution

### Amazon Ad Server - Custom Attribution of ASIN Conversions
- Extended with DCO version attribution capabilities
- Allows custom attribution windows per version
- Tracks cross-version influence on conversions

### Amazon Ad Server - Audiences with ASIN Conversions
- Combines behavioral audience data with DCO versions
- Analyzes how different audiences respond to creative variations
- Supports Target Audience overlap analysis

## 4.2 Best Practices for Combined Analysis

When using DCO signals with other IQs:
1. Maintain consistent date ranges across queries
2. Use the same grouping dimensions (version_id) for accurate comparisons
3. Consider multi-touch attribution when users see multiple versions
4. Account for Target Audience overlap in conversion attribution""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': False
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
                'title': 'DCO Ad Metadata',
                'description': 'Extract metadata from DCO campaign traffic events including version-level information. Useful for getting input data for subsequent queries.',
                'sql_query': """-- Instructional Query: Exploratory Query for Querying DCO and Target Audience signals for Amazon Ad Server
-- Extract metadata from DCO campaign traffic events.
SELECT
  DISTINCT advertiser,
  advertiser_id,
  campaign,
  campaign_id,
  ad,
  ad_id,
  version_name,
  version_id,
  smart_items_list,
  target_audience_name,
  target_audience_id
FROM
  adserver_traffic
WHERE
  is_dco_ad = TRUE
  AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
  {% if campaign_ids %}
  AND campaign_id IN ({{campaign_ids}})
  {% endif %}
ORDER BY
  advertiser,
  campaign,
  ad,
  version_name""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for DCO data'
                    },
                    'campaign_ids': {
                        'type': 'array',
                        'default': None,
                        'description': 'Optional list of campaign IDs to filter (leave empty for all campaigns)',
                        'required': False
                    }
                },
                'default_parameters': {
                    'lookback_days': 30
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query helps you discover all DCO campaigns and their versions in your account. Use the metadata to understand what creative variations are being tested and which Target Audiences are configured.'
            },
            {
                'guide_id': guide_id,
                'title': 'DCO Version Performance',
                'description': 'Understand the performance of different DCO versions including impressions, CTR, and conversion impact broken down daily.',
                'sql_query': """-- Instructional Query: Exploratory Query for Querying DCO version performance
/* Query Template: DCO Version Performance */
WITH dco_traffic AS (
  SELECT
    event_day_utc AS day_of_month,
    campaign,
    campaign_id,
    adserver_site AS site_name,
    ad AS ad_name,
    ad_id,
    version_name,
    version_id,
    user_id,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks
  FROM
    adserver_traffic
  WHERE
    is_dco_ad = TRUE
    AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
    {% if campaign_ids %}
    AND campaign_id IN ({{campaign_ids}})
    {% endif %}
  GROUP BY
    1, 2, 3, 4, 5, 6, 7, 8, 9
),
conversions AS (
  SELECT
    user_id,
    COUNT(*) AS conversions,
    SUM(revenue) AS revenue
  FROM
    adserver_conversions
  WHERE
    event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
    AND conversion_type IN ({{conversion_types}})
  GROUP BY
    user_id
)
SELECT
  t.day_of_month,
  t.campaign,
  t.campaign_id,
  t.site_name,
  t.ad_name,
  t.ad_id,
  t.version_name,
  t.version_id,
  SUM(t.impressions) AS impressions,
  SUM(t.clicks) AS clicks,
  SUM(COALESCE(c.conversions, 0)) AS total_conversions,
  CASE 
    WHEN SUM(t.impressions) > 0 
    THEN ROUND(CAST(SUM(t.clicks) AS DOUBLE) / CAST(SUM(t.impressions) AS DOUBLE) * 100, 2)
    ELSE 0 
  END AS ctr_pct,
  SUM(COALESCE(c.revenue, 0)) AS conversion_revenue
FROM
  dco_traffic t
  LEFT JOIN conversions c ON t.user_id = c.user_id
GROUP BY
  1, 2, 3, 4, 5, 6, 7, 8
HAVING
  SUM(t.impressions) >= {{min_impressions}}
ORDER BY
  t.day_of_month DESC,
  t.campaign,
  SUM(t.impressions) DESC""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for performance data'
                    },
                    'campaign_ids': {
                        'type': 'array',
                        'default': None,
                        'description': 'Optional list of campaign IDs to filter',
                        'required': False
                    },
                    'conversion_types': {
                        'type': 'array',
                        'default': ['purchase', 'add_to_cart', 'detail_page_view'],
                        'description': 'Types of conversions to include'
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'default': 1000,
                        'description': 'Minimum impressions threshold for inclusion'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'conversion_types': ['purchase', 'add_to_cart', 'detail_page_view'],
                    'min_impressions': 1000
                },
                'display_order': 2,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Focus on versions with statistically significant impression volumes. Compare CTR and conversion rates to identify winning variations. Consider both immediate conversions and revenue impact.'
            },
            {
                'guide_id': guide_id,
                'title': 'DCO Traffic by Audience Segment',
                'description': 'Understand how many impressions for each DCO version have been served to users in Amazon DSP behavioral audiences.',
                'sql_query': """-- Query Template: DCO Traffic by Amazon DSP Audience Segment
SELECT
  advertiser,
  advertiser_id,
  campaign,
  campaign_id,
  ad,
  ad_id,
  version_name,
  version_id,
  behavior_segment_name,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  CASE 
    WHEN SUM(impressions) > 0 
    THEN ROUND(CAST(SUM(clicks) AS DOUBLE) / CAST(SUM(impressions) AS DOUBLE) * 100, 2)
    ELSE 0 
  END AS ctr_pct
FROM
  adserver_traffic_by_user_segments
WHERE
  is_dco_ad = TRUE
  AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
  {% if segment_categories %}
  AND behavior_segment_category IN ({{segment_categories}})
  {% endif %}
  {% if campaign_ids %}
  AND campaign_id IN ({{campaign_ids}})
  {% endif %}
GROUP BY
  1, 2, 3, 4, 5, 6, 7, 8, 9
HAVING
  SUM(impressions) >= {{min_impressions}}
ORDER BY
  campaign,
  version_name,
  SUM(impressions) DESC""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back'
                    },
                    'segment_categories': {
                        'type': 'array',
                        'default': None,
                        'description': 'Optional behavioral segment categories to filter',
                        'required': False
                    },
                    'campaign_ids': {
                        'type': 'array',
                        'default': None,
                        'description': 'Optional campaign IDs to filter',
                        'required': False
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'default': 100,
                        'description': 'Minimum impressions per segment'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'min_impressions': 100
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Analyze which behavioral segments respond best to different creative versions. Use these insights to create segment-specific creative strategies.'
            },
            {
                'guide_id': guide_id,
                'title': 'Filter DCO by Smart Item Values',
                'description': 'Filter Amazon Ad Server DCO impressions based on specific smart item values like text copy or image sources.',
                'sql_query': """-- Query Template: DCO Impressions by a Specific Smart Item Value
SELECT
  ad,
  version_name,
  version_id,
  smart_items_list,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  CASE 
    WHEN SUM(impressions) > 0 
    THEN ROUND(CAST(SUM(clicks) AS DOUBLE) / CAST(SUM(impressions) AS DOUBLE) * 100, 2)
    ELSE 0 
  END AS ctr_pct
FROM
  adserver_traffic
WHERE
  is_dco_ad = TRUE
  AND event_dt >= DATE_ADD('day', -{{lookback_days}}, CURRENT_DATE)
  /*UPDATE: Replace 'SMART_ITEM_KEY' in the line below with your chosen 
   smart item key and 'SMART_ITEM_VALUE' with your chosen smart item value */
  AND smart_items_list SIMILAR TO '^(|.*\\|,){{smart_item_key}}:{{smart_item_value}}(\\|,.*|$)'
GROUP BY
  1, 2, 3, 4
HAVING
  SUM(impressions) >= {{min_impressions}}
ORDER BY
  SUM(impressions) DESC""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back'
                    },
                    'smart_item_key': {
                        'type': 'string',
                        'default': 'headline',
                        'description': 'Smart item key to filter (e.g., headline, cta, image)'
                    },
                    'smart_item_value': {
                        'type': 'string',
                        'default': 'Shop Now',
                        'description': 'Smart item value to search for'
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'default': 100,
                        'description': 'Minimum impressions threshold'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'smart_item_key': 'headline',
                    'smart_item_value': 'Shop Now',
                    'min_impressions': 100
                },
                'display_order': 4,
                'query_type': 'exploratory',
                'interpretation_notes': 'Use this query to isolate the impact of specific creative elements. Compare performance of versions with the same smart item value to understand its effectiveness.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results based on query type
                if query['title'] == 'DCO Ad Metadata':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample DCO Ad Metadata',
                        'sample_data': {
                            'rows': [
                                {
                                    'advertiser': 'BrandX',
                                    'advertiser_id': 1001,
                                    'campaign': 'Summer Sale 2024',
                                    'campaign_id': 5001,
                                    'ad': 'Display_300x250',
                                    'ad_id': 7001,
                                    'version_name': 'Spanish_v1',
                                    'version_id': 12345,
                                    'smart_items_list': 'headline:Oferta de Verano|,cta:Comprar Ahora|,image:summer_es.jpg',
                                    'target_audience_name': 'Spanish Speakers',
                                    'target_audience_id': 67890
                                },
                                {
                                    'advertiser': 'BrandX',
                                    'advertiser_id': 1001,
                                    'campaign': 'Summer Sale 2024',
                                    'campaign_id': 5001,
                                    'ad': 'Display_300x250',
                                    'ad_id': 7001,
                                    'version_name': 'German_v1',
                                    'version_id': 12346,
                                    'smart_items_list': 'headline:Sommerangebot|,cta:Jetzt Kaufen|,image:summer_de.jpg',
                                    'target_audience_name': 'German Market',
                                    'target_audience_id': 67891
                                },
                                {
                                    'advertiser': 'BrandX',
                                    'advertiser_id': 1001,
                                    'campaign': 'Summer Sale 2024',
                                    'campaign_id': 5001,
                                    'ad': 'Display_300x250',
                                    'ad_id': 7001,
                                    'version_name': 'English_v1',
                                    'version_id': 12347,
                                    'smart_items_list': 'headline:Summer Sale|,cta:Shop Now|,image:summer_en.jpg',
                                    'target_audience_name': 'US Market',
                                    'target_audience_id': 67892
                                }
                            ]
                        },
                        'interpretation_markdown': """This metadata shows three language-specific versions of the same ad:
- **Spanish_v1**: Targeted to Spanish speakers with localized copy and imagery
- **German_v1**: Customized for German market with translated elements
- **English_v1**: Default version for US market

Each version has unique smart items (headline, CTA, image) and is associated with a specific Target Audience.""",
                        'insights': [
                            'Three distinct language versions are running for the same campaign',
                            'Each version has customized headline, CTA, and image assets',
                            'Target Audiences are configured for language-based segmentation'
                        ],
                        'display_order': 1
                    }
                    
                elif query['title'] == 'DCO Version Performance':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Version Performance Analysis',
                        'sample_data': {
                            'rows': [
                                {
                                    'day_of_month': '2024-01-15',
                                    'campaign': 'Summer Sale 2024',
                                    'campaign_id': 5001,
                                    'site_name': 'Amazon.com',
                                    'ad_name': 'Display_300x250',
                                    'ad_id': 7001,
                                    'version_name': 'Spanish_v1',
                                    'version_id': 12345,
                                    'impressions': 50000,
                                    'clicks': 1500,
                                    'total_conversions': 150,
                                    'ctr_pct': 3.00,
                                    'conversion_revenue': 4500.00
                                },
                                {
                                    'day_of_month': '2024-01-15',
                                    'campaign': 'Summer Sale 2024',
                                    'campaign_id': 5001,
                                    'site_name': 'Amazon.com',
                                    'ad_name': 'Display_300x250',
                                    'ad_id': 7001,
                                    'version_name': 'German_v1',
                                    'version_id': 12346,
                                    'impressions': 30000,
                                    'clicks': 750,
                                    'total_conversions': 60,
                                    'ctr_pct': 2.50,
                                    'conversion_revenue': 2100.00
                                },
                                {
                                    'day_of_month': '2024-01-15',
                                    'campaign': 'Summer Sale 2024',
                                    'campaign_id': 5001,
                                    'site_name': 'Amazon.com',
                                    'ad_name': 'Display_300x250',
                                    'ad_id': 7001,
                                    'version_name': 'English_v1',
                                    'version_id': 12347,
                                    'impressions': 80000,
                                    'clicks': 2000,
                                    'total_conversions': 180,
                                    'ctr_pct': 2.50,
                                    'conversion_revenue': 5400.00
                                }
                            ]
                        },
                        'interpretation_markdown': """Performance analysis reveals significant differences between versions:

**Top Performer - Spanish_v1:**
- Highest CTR at 3.00% (20% better than other versions)
- Strong conversion rate with 10% of clicks converting
- $30 average order value

**Volume Leader - English_v1:**
- Highest impression volume (80,000)
- Most total conversions (180)
- Highest revenue generation ($5,400)

**Efficiency Opportunity - German_v1:**
- Lowest volume but decent engagement
- Highest average order value ($35)
- Potential for scaling with increased budget""",
                        'insights': [
                            'Spanish version shows 20% higher CTR than English/German versions',
                            'English version drives highest absolute revenue despite lower CTR',
                            'German market shows highest average order value per conversion',
                            'Consider increasing budget allocation to Spanish version given superior engagement'
                        ],
                        'display_order': 1
                    }
                    
                elif query['title'] == 'DCO Traffic by Audience Segment':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Audience Segment Performance',
                        'sample_data': {
                            'rows': [
                                {
                                    'advertiser': 'BrandX',
                                    'advertiser_id': 1001,
                                    'campaign': 'Summer Sale 2024',
                                    'campaign_id': 5001,
                                    'ad': 'Display_300x250',
                                    'ad_id': 7001,
                                    'version_name': 'Spanish_v1',
                                    'version_id': 12345,
                                    'behavior_segment_name': 'IM - Home and Garden',
                                    'impressions': 15000,
                                    'clicks': 525,
                                    'ctr_pct': 3.50
                                },
                                {
                                    'advertiser': 'BrandX',
                                    'advertiser_id': 1001,
                                    'campaign': 'Summer Sale 2024',
                                    'campaign_id': 5001,
                                    'ad': 'Display_300x250',
                                    'ad_id': 7001,
                                    'version_name': 'Spanish_v1',
                                    'version_id': 12345,
                                    'behavior_segment_name': 'IM - Health, Beauty or Fashion',
                                    'impressions': 20000,
                                    'clicks': 600,
                                    'ctr_pct': 3.00
                                },
                                {
                                    'advertiser': 'BrandX',
                                    'advertiser_id': 1001,
                                    'campaign': 'Summer Sale 2024',
                                    'campaign_id': 5001,
                                    'ad': 'Display_300x250',
                                    'ad_id': 7001,
                                    'version_name': 'German_v1',
                                    'version_id': 12346,
                                    'behavior_segment_name': 'IM - Electronics',
                                    'impressions': 12000,
                                    'clicks': 360,
                                    'ctr_pct': 3.00
                                },
                                {
                                    'advertiser': 'BrandX',
                                    'advertiser_id': 1001,
                                    'campaign': 'Summer Sale 2024',
                                    'campaign_id': 5001,
                                    'ad': 'Display_300x250',
                                    'ad_id': 7001,
                                    'version_name': 'English_v1',
                                    'version_id': 12347,
                                    'behavior_segment_name': 'IM - Health, Beauty or Fashion',
                                    'impressions': 35000,
                                    'clicks': 875,
                                    'ctr_pct': 2.50
                                }
                            ]
                        },
                        'interpretation_markdown': """Audience segment analysis reveals version-specific preferences:

**Spanish Version Performance:**
- Strongest engagement with Home and Garden segment (3.50% CTR)
- High volume in Health, Beauty or Fashion category

**German Version Focus:**
- Concentrated in Electronics segment
- Maintaining 3.00% CTR with tech-interested audience

**English Version Reach:**
- Largest volume in Health, Beauty or Fashion
- Lower CTR suggests opportunity for creative optimization""",
                        'insights': [
                            'Spanish version resonates particularly well with Home and Garden audiences',
                            'German audience shows strong interest in Electronics category',
                            'Health, Beauty or Fashion is the highest volume segment across versions',
                            'Consider creating segment-specific creative variations for better performance'
                        ],
                        'display_order': 1
                    }
                    
                elif query['title'] == 'Filter DCO by Smart Item Values':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Smart Item Filtering',
                        'sample_data': {
                            'rows': [
                                {
                                    'ad': 'Display_300x250',
                                    'version_name': 'Discount_v1',
                                    'version_id': 12350,
                                    'smart_items_list': 'headline:50% Off Today|,cta:Shop Now|,badge:Limited Time',
                                    'impressions': 45000,
                                    'clicks': 1800,
                                    'ctr_pct': 4.00
                                },
                                {
                                    'ad': 'Display_300x250',
                                    'version_name': 'Discount_v2',
                                    'version_id': 12351,
                                    'smart_items_list': 'headline:Limited Time Sale|,cta:Shop Now|,badge:Today Only',
                                    'impressions': 38000,
                                    'clicks': 1140,
                                    'ctr_pct': 3.00
                                },
                                {
                                    'ad': 'Display_728x90',
                                    'version_name': 'Premium_v1',
                                    'version_id': 12352,
                                    'smart_items_list': 'headline:Premium Collection|,cta:Shop Now|,badge:Exclusive',
                                    'impressions': 22000,
                                    'clicks': 550,
                                    'ctr_pct': 2.50
                                }
                            ]
                        },
                        'interpretation_markdown': """Analysis of versions containing 'Shop Now' CTA:

**Performance by Headline Type:**
- Direct discount messaging ('50% Off Today') drives highest CTR at 4.00%
- Urgency-based messaging ('Limited Time Sale') achieves 3.00% CTR
- Premium positioning shows lower engagement at 2.50% CTR

**Key Findings:**
- All versions use consistent 'Shop Now' CTA
- Discount-focused headlines outperform premium messaging
- Badge elements ('Limited Time', 'Today Only') reinforce urgency""",
                        'insights': [
                            'Shop Now CTA works best with discount-focused headlines',
                            '50% Off messaging drives 60% higher CTR than premium positioning',
                            'Urgency badges complement discount messaging effectively',
                            'Consider testing alternative CTAs with premium positioning'
                        ],
                        'display_order': 1
                    }
                else:
                    continue
                
                example_response = client.table('build_guide_examples').insert(example_data).execute()
                if example_response.data:
                    logger.info(f"Created example for: {query['title']}")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'is_dco_ad',
                'display_name': 'Is DCO Ad',
                'definition': 'Boolean field that indicates if the ad uses Dynamic Creative Optimization',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'version_id',
                'display_name': 'Version ID',
                'definition': 'Unique internal identifier of an Amazon Ad Server DCO ad version',
                'metric_type': 'dimension',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'version_name',
                'display_name': 'Version Name',
                'definition': 'Advertiser-defined display name of an Amazon Ad Server DCO ad version at the time of serving',
                'metric_type': 'dimension',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'smart_items_list',
                'display_name': 'Smart Items List',
                'definition': 'List of names and values of all dynamic elements in a particular Amazon Ad Server ad version, separated by pipe and comma ("|,")',
                'metric_type': 'dimension',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'target_audience_id',
                'display_name': 'Target Audience ID',
                'definition': 'Unique internal identifier of an Amazon Ad Server Target Audience',
                'metric_type': 'dimension',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'target_audience_name',
                'display_name': 'Target Audience Name',
                'definition': 'Advertiser-defined display name of an Amazon Ad Server Target Audience',
                'metric_type': 'dimension',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'impressions',
                'display_name': 'Impressions',
                'definition': 'Number of times the ad version was displayed',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'clicks',
                'display_name': 'Clicks',
                'definition': 'Number of clicks on the ad version',
                'metric_type': 'metric',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'ctr_pct',
                'display_name': 'Click-Through Rate %',
                'definition': 'Percentage of impressions that resulted in clicks (clicks / impressions * 100)',
                'metric_type': 'metric',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_conversions',
                'display_name': 'Total Conversions',
                'definition': 'Number of conversions attributed to the ad version',
                'metric_type': 'metric',
                'display_order': 10
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_revenue',
                'display_name': 'Conversion Revenue',
                'definition': 'Total revenue from conversions attributed to the ad version',
                'metric_type': 'metric',
                'display_order': 11
            },
            {
                'guide_id': guide_id,
                'metric_name': 'behavior_segment_name',
                'display_name': 'Behavior Segment Name',
                'definition': 'Name of the Amazon DSP behavioral audience segment',
                'metric_type': 'dimension',
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
        
        logger.info("✅ Successfully created Amazon Ad Server - DCO and Target Audience Signals guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_dco_target_audience_guide()
    sys.exit(0 if success else 1)