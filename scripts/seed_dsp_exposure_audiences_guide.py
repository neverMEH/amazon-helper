#!/usr/bin/env python3
"""
Seed script for Audiences exposed to Amazon DSP campaigns Build Guide
This script creates the comprehensive guide for building audiences based on DSP exposure
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def create_dsp_exposure_audiences_guide():
    """Create the Audiences exposed to Amazon DSP campaigns guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_dsp_exposure_audiences',
            'name': 'Audiences exposed to Amazon DSP campaigns',
            'category': 'Audience Building',
            'short_description': 'Learn how to create audiences based on their exposure to your ads, enabling tactics to reduce creative fatigue, implement sequential messaging, and optimize to best-performing paths to conversion.',
            'tags': ['Audience Building', 'DSP', 'Creative Fatigue', 'Sequential Messaging', 'Path Optimization', 'Remarketing'],
            'icon': 'Users',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 45,
            'prerequisites': [
                'Access to Amazon DSP campaigns',
                'Understanding of AMC audience queries and _for_audiences tables',
                'Basic knowledge of SQL and AMC query structure',
                'Campaign IDs from your Amazon DSP account'
            ],
            'is_published': True,
            'display_order': 8,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
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

Use this instructional query (IQ) to learn how to create audiences based on their exposure to your ads. This IQ is a collection of lightweight templates that can help you implement tactics to reduce creative fatigue, implement sequential messaging, and optimize to best-performing paths to conversion. These tactics can help you minimize wasted media dollars, deliver logical narratives to your audience through media, and recreate paths to purchase with the most effective purchase rates.

Note that each query template by itself is not specific to a single use case (i.e. no one audience is a creative fatigue audience, for example). Each query simply assembles a cohort on the basis of certain exposure criteria, and the AMC user must tailor it based on the measurement insights reviewed above.

For instance, a query template that assembles an audience on the basis of exposure to a certain campaign could be used for both suppression (creative fatigue) and remarketing (sequential messaging, path optimization) use cases. How you configure the template and how you apply the audience to your campaign (include/exclude) will dictate the use case.

## 1.2 Requirements

It is recommended that you first analyze your Amazon Ads media delivery and performance. Use insights from AMC to inform the specific criteria for your audiences.

## 1.3 Use cases

| Use Case | Measurement Question | Measurement IQ | Action Question |
|----------|---------------------|----------------|-----------------|
| **Reduce creative fatigue** | After how many impressions does performance start to drop? | DSP Impression Frequency and Conversions | How can I create an audience that helps me reduce media waste and exclude those unlikely to convert? |
| **Implement sequential messaging** | - | - | How can I show my audience creative in a specific logical order? |
| **Optimize to best-performing paths to conversion** | Which order of exposure across devices is most effective? | DSP Path to Conversion by Device | How can I recreate the best-performing path to conversion at the device level? |
| **Optimize to best-performing paths to conversion** | Which order of exposure across Amazon DSP campaigns is most effective? | Path to Conversion by Campaign Groups | How can I recreate the best-performing path to conversion at the campaign level? |
| **Optimize to best-performing paths to conversion** | Which order of exposure across Amazon Ads ad products is most effective? | Path to Conversion by Campaign Groups | How can I recreate the best-performing path to conversion at the Amazon Ads ad product level? |""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'dsp_campaign_exposure',
                'title': '2. DSP Campaign Exposure Queries',
                'content_markdown': """## 2.1 Exposure to specific Amazon DSP campaign

This query creates an audience of all those exposed to X+ impressions from a specific Amazon DSP campaign or list of campaigns. For example, remarketing to those exposed to Streaming TV campaigns.

### Instructions and customization ideas:
- Define the campaign(s) that you want to include in the audience (e.g. all prospecting campaigns, or all women's campaigns)
- If your campaigns have a set naming convention, consider filtering by campaign (campaign name) logic instead; e.g. `WHERE campaign SIMILAR TO 'REM'`
- Specify the number of impressions that the cohort should be exposed to before being included in the audience (e.g. has received 3+ impressions from the specific campaign(s))

## 2.2 Exposure to specific Amazon DSP line item

This query creates an audience of all those exposed to X+ impressions from a specific Amazon DSP line item or list of line items.

### Instructions and customization ideas:
- Define the line item(s) that you want to include in the audience (e.g. all line items that leverage a specific supply source, specific audiences, or other logical criteria)
- If your line items have a set naming convention, consider filtering by line_item (line item name) logic instead; e.g. `WHERE line_item SIMILAR TO '3P Audience'`
- Specify the number of impressions that the cohort should be exposed to before being included in the audience (e.g. has received 3+ impressions from the specific line item(s))

## 2.3 Exposure to specific Amazon DSP creative

This query creates an audience of all those exposed to X+ impressions from a specific Amazon DSP creative or list of creatives.

### Instructions and customization ideas:
- Define the creative(s) that you want to include in the audience (e.g. all Prime Day messaging creative)
- If your creatives have a set naming convention, consider filtering by creative (creative name) logic instead; e.g. `WHERE creative SIMILAR TO 'Summer24'`
- Specify the number of impressions that the cohort should be exposed to before being included in the audience (e.g. has received 3+ impressions from the specific creative(s))

## 2.4 Exposure to Amazon DSP + segment membership

This query creates an audience of all those exposed to your Amazon DSP campaigns that are associated a specific audience segment.

### Instructions and customization ideas:
- Define the segment ID value(s) that you want to include in the audience; these can include Amazon Ads and third-party audiences, as well as custom AMC audiences or audiences you've created in Amazon DSP
- To determine relevant segment IDs, you can pull distinct segment name and ID values from the dsp_impressions_by_user_segments table or copy the IDs directly from Amazon DSP""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'sponsored_ads_exposure',
                'title': '3. Sponsored Ads Exposure Queries',
                'content_markdown': """## 3.1 Exposure to specific sponsored ads ad product type

This query creates an audience of all those exposed to a specific type of sponsored ads campaign. For example, remarketing to those exposed to Sponsored Brands campaigns.

### Instructions and customization ideas:
- Define the ad product type(s) that you want to include in the audience
- Possible ad_product_type values that can be leveraged for this filter include 'sponsored_products', 'sponsored_brands', 'sponsored_display', or 'sponsored_television'
- Specify the number of impressions that the cohort should be exposed to before being included in the audience (e.g. has received 3+ impressions from the specific ad product type(s))

## 3.2 Exposure to specific sponsored ads campaign

This query creates an audience of all those exposed to X+ impressions from a specific sponsored ads campaign or list of campaigns.

### Instructions and customization ideas:
- If your campaigns have a set naming convention, consider filtering by campaign (campaign name) logic instead; e.g. `WHERE campaign SIMILAR TO 'Kitchen'`
- Specify the number of impressions that the cohort should be exposed to before being included in the audience (e.g. has received 3+ impressions from the specific campaign(s))

## 3.3 Exposure to specific sponsored ads ad group

This query creates an audience of all those exposed to X+ impressions from a specific sponsored ads ad group or list of ad groups.

### Instructions and customization ideas:
- If your campaigns have a set naming convention, consider filtering by campaign (campaign name) logic instead; e.g. `WHERE ad_group SIMILAR TO 'Kitchen'`
- Specify the number of impressions that the cohort should be exposed to before being included in the audience (e.g. has received 3+ impressions from the specific campaign(s))""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': False
            },
            {
                'guide_id': guide_id,
                'section_id': 'advanced_use_cases',
                'title': '4. Advanced Use Cases',
                'content_markdown': """## 4.1 Creative Fatigue Suppression

Create audiences of users who have been overexposed to your ads to exclude them from future campaigns. This helps prevent wasted impressions on users who are unlikely to convert after excessive exposure.

### Key considerations:
- Monitor performance drop-off after specific impression thresholds
- Exclude over-exposed users from campaigns
- Rotate creative regularly for high-frequency users
- Consider time decay in exposure calculations

## 4.2 Sequential Messaging

Build audiences for sequential messaging campaigns to guide users through a logical narrative journey.

### Sequential messaging stages:
- **Stage 1**: Broad awareness messaging
- **Stage 2**: Product benefits and features
- **Stage 3**: Offers and calls-to-action
- Ensure adequate time between stages (3-7 days)

## 4.3 Path Optimization

Create audiences based on optimal conversion paths to recreate successful customer journeys.

### Path optimization techniques:
- Analyze historical conversion paths
- Identify high-performing sequences
- Create audiences matching optimal paths
- Test different path variations""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': False
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': '5. Best Practices and Implementation Tips',
                'content_markdown': """## 5.1 Frequency Capping Strategy

- **1-3 impressions**: Awareness building phase
- **4-6 impressions**: Consideration phase
- **7-10 impressions**: Decision phase
- **10+ impressions**: Risk of creative fatigue

## 5.2 Creative Fatigue Management

- Monitor performance drop-off after specific impression thresholds
- Exclude over-exposed users from campaigns
- Rotate creative regularly for high-frequency users
- Consider time decay in exposure calculations

## 5.3 Sequential Messaging Best Practices

- **Stage 1**: Broad awareness messaging
- **Stage 2**: Product benefits and features
- **Stage 3**: Offers and calls-to-action
- Ensure adequate time between stages (3-7 days)

## 5.4 Path Optimization Techniques

- Analyze historical conversion paths
- Identify high-performing sequences
- Create audiences matching optimal paths
- Test different path variations

## 5.5 Audience Application Strategies

- **Include targeting**: For remarketing and sequential messaging
- **Exclude targeting**: For creative fatigue suppression
- **Lookalike audiences**: Scale successful exposure patterns
- **Combination audiences**: Layer multiple exposure criteria

## 5.6 Performance Monitoring

- Track audience size over time
- Monitor conversion rates by exposure level
- Analyze cost efficiency at different frequencies
- A/B test different exposure thresholds

## 5.7 Common Use Cases by Industry

- **Retail**: Exclude high-frequency non-converters
- **Automotive**: Sequential messaging for consideration journey
- **CPG**: Frequency capping for brand awareness
- **B2B**: Path optimization for longer sales cycles""",
                'display_order': 5,
                'is_collapsible': True,
                'default_expanded': False
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
                'query_type': 'audience_creation',
                'title': 'DSP Campaign Exposure',
                'description': 'Create an audience of users exposed to specific DSP campaigns',
                'sql_query': """SELECT
  user_id
FROM
  dsp_impressions_for_audiences
WHERE
  user_id IS NOT NULL
  AND campaign_id_string IN (
    '123456789',
    '345678910'
    /* Required Update: Add campaign_id_string value(s) here separated by commas, e.g. '123456789', '345678910' */
  )
GROUP BY
  1
HAVING
  SUM(impressions) >= 3
  /* Required Update: Specify impression number here */""",
                'parameters_schema': json.dumps({
                    'campaign_ids': {
                        'type': 'array',
                        'description': 'List of campaign IDs to include',
                        'required': True,
                        'example': ['123456789', '345678910']
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'description': 'Minimum number of impressions',
                        'required': True,
                        'default': 3
                    }
                }),
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'query_type': 'audience_creation',
                'title': 'DSP Line Item Exposure',
                'description': 'Create an audience of users exposed to specific DSP line items',
                'sql_query': """SELECT
  user_id
FROM
  dsp_impressions_for_audiences
WHERE
  user_id IS NOT NULL
  AND line_item_id IN (
    '123456789',
    '345678910'
    /* Required Update: Add line_item_id value(s) here separated by commas, e.g. '123456789', '345678910' */
  )
GROUP BY
  1
HAVING
  SUM(impressions) >= 3
  /* Required Update: Specify impression number here, e.g. 3 */""",
                'parameters_schema': json.dumps({
                    'line_item_ids': {
                        'type': 'array',
                        'description': 'List of line item IDs to include',
                        'required': True,
                        'example': ['123456789', '345678910']
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'description': 'Minimum number of impressions',
                        'required': True,
                        'default': 3
                    }
                }),
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'query_type': 'audience_creation',
                'title': 'DSP Creative Exposure',
                'description': 'Create an audience of users exposed to specific DSP creatives',
                'sql_query': """SELECT
  user_id
FROM
  dsp_impressions_for_audiences
WHERE
  user_id IS NOT NULL
  AND creative_id IN (
    '123456789',
    '345678910'
    /* Required Update: Add creative_id value(s) here separated by commas, e.g. '123456789', '345678910' */
  )
GROUP BY
  1
HAVING
  SUM(impressions) >= 3
  /* Required Update: Specify impression number here, e.g. 3 */""",
                'parameters_schema': json.dumps({
                    'creative_ids': {
                        'type': 'array',
                        'description': 'List of creative IDs to include',
                        'required': True,
                        'example': ['123456789', '345678910']
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'description': 'Minimum number of impressions',
                        'required': True,
                        'default': 3
                    }
                }),
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'query_type': 'audience_creation',
                'title': 'DSP Segment Membership',
                'description': 'Create an audience based on DSP segment membership',
                'sql_query': """SELECT
  user_id
FROM
  dsp_impressions_by_user_segments_for_audiences
WHERE
  user_id IS NOT NULL
  AND impressions = 1
  AND behavior_segment_id IN ('123456')
  /* Required Update: Add behavioral segment ID value here, e.g. 123456 */
GROUP BY
  1""",
                'parameters_schema': json.dumps({
                    'segment_ids': {
                        'type': 'array',
                        'description': 'List of behavioral segment IDs',
                        'required': True,
                        'example': ['123456']
                    }
                }),
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'query_type': 'audience_creation',
                'title': 'Sponsored Ads Product Type',
                'description': 'Create an audience exposed to specific sponsored ads product types',
                'sql_query': """SELECT
  user_id
FROM
  sponsored_ads_traffic_for_audiences
WHERE
  user_id IS NOT NULL
  AND ad_product_type = 'sponsored_products'
  /* Required Update: Specify one or more ad_product_type value(s) here, e.g. 'sponsored_television', 'sponsored_display' */
GROUP BY
  1
HAVING
  SUM(impressions) >= 3
  /* Required Update: Specify impression number here, e.g. 3 */""",
                'parameters_schema': json.dumps({
                    'ad_product_types': {
                        'type': 'array',
                        'description': 'Ad product types to include',
                        'required': True,
                        'enum': ['sponsored_products', 'sponsored_brands', 'sponsored_display', 'sponsored_television'],
                        'example': ['sponsored_products']
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'description': 'Minimum number of impressions',
                        'required': True,
                        'default': 3
                    }
                }),
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'query_type': 'audience_creation',
                'title': 'Sponsored Ads Campaign',
                'description': 'Create an audience exposed to specific sponsored ads campaigns',
                'sql_query': """SELECT
  user_id
FROM
  sponsored_ads_traffic_for_audiences
WHERE
  user_id IS NOT NULL
  AND campaign_id_string IN (
    '123456789',
    '344565677'
    /* Required Update: Add campaign_id_string value(s) here, e.g.'123456789' */
  )
GROUP BY
  1
HAVING
  SUM(impressions) >= 3
  /* Required Update: Specify impression number here, e.g. 3 */""",
                'parameters_schema': json.dumps({
                    'campaign_ids': {
                        'type': 'array',
                        'description': 'List of campaign IDs to include',
                        'required': True,
                        'example': ['123456789', '344565677']
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'description': 'Minimum number of impressions',
                        'required': True,
                        'default': 3
                    }
                }),
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'query_type': 'audience_creation',
                'title': 'Sponsored Ads Ad Group',
                'description': 'Create an audience exposed to specific sponsored ads ad groups',
                'sql_query': """SELECT
  user_id
FROM
  sponsored_ads_traffic_for_audiences
WHERE
  user_id IS NOT NULL
  AND ad_group IN (
    'Ad Group Name A',
    'Ad Group Name B'
    /* Required Update: Add ad group name(s) here, e.g. 'Ad Group Name A' */
  )
GROUP BY
  1
HAVING
  SUM(impressions) >= 3
  /* Required Update: Specify impression number here, e.g. 3 */""",
                'parameters_schema': json.dumps({
                    'ad_group_names': {
                        'type': 'array',
                        'description': 'List of ad group names to include',
                        'required': True,
                        'example': ['Ad Group Name A', 'Ad Group Name B']
                    },
                    'min_impressions': {
                        'type': 'integer',
                        'description': 'Minimum number of impressions',
                        'required': True,
                        'default': 3
                    }
                }),
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'query_type': 'advanced',
                'title': 'Creative Fatigue Suppression',
                'description': 'Identify users overexposed to ads for exclusion',
                'sql_query': """-- Audience for Creative Fatigue Suppression
SELECT
  user_id
FROM
  dsp_impressions_for_audiences
WHERE
  user_id IS NOT NULL
  AND campaign_id_string IN (
    /* Add your campaign IDs */
    '123456789'
  )
GROUP BY
  1
HAVING
  SUM(impressions) >= 10  -- Users with 10+ impressions
  AND MAX(event_dt_utc) < CURRENT_DATE - INTERVAL '7' DAY  -- No impression in last 7 days""",
                'parameters_schema': json.dumps({
                    'campaign_ids': {
                        'type': 'array',
                        'description': 'Campaign IDs to check for overexposure',
                        'required': True
                    },
                    'max_impressions': {
                        'type': 'integer',
                        'description': 'Threshold for overexposure',
                        'default': 10
                    },
                    'days_since_last': {
                        'type': 'integer',
                        'description': 'Days since last impression',
                        'default': 7
                    }
                }),
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'query_type': 'advanced',
                'title': 'Sequential Messaging',
                'description': 'Build audiences for sequential messaging campaigns',
                'sql_query': """-- Audience for Sequential Messaging - Stage 2
WITH stage_1_exposed AS (
  SELECT
    user_id,
    MAX(event_dt_utc) as last_exposure
  FROM
    dsp_impressions_for_audiences
  WHERE
    creative_id IN ('creative_1_id')  -- Stage 1 creative
  GROUP BY
    1
  HAVING
    SUM(impressions) >= 2
)
SELECT
  user_id
FROM
  stage_1_exposed
WHERE
  last_exposure >= CURRENT_DATE - INTERVAL '30' DAY  -- Exposed within last 30 days""",
                'parameters_schema': json.dumps({
                    'stage_1_creative_ids': {
                        'type': 'array',
                        'description': 'Creative IDs from previous stage',
                        'required': True
                    },
                    'min_stage_1_impressions': {
                        'type': 'integer',
                        'description': 'Minimum impressions from stage 1',
                        'default': 2
                    },
                    'recency_days': {
                        'type': 'integer',
                        'description': 'Days since last stage 1 exposure',
                        'default': 30
                    }
                }),
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'query_type': 'advanced',
                'title': 'Path Optimization',
                'description': 'Create audiences based on optimal conversion paths',
                'sql_query': """-- Audience based on high-converting path
WITH path_users AS (
  SELECT
    user_id,
    ARRAY_AGG(campaign_id_string ORDER BY event_dt_utc) as campaign_path
  FROM
    dsp_impressions_for_audiences
  WHERE
    user_id IS NOT NULL
  GROUP BY
    1
)
SELECT
  user_id
FROM
  path_users
WHERE
  campaign_path[1] = 'prospecting_campaign_id'
  AND campaign_path[2] = 'retargeting_campaign_id'""",
                'parameters_schema': json.dumps({
                    'path_sequence': {
                        'type': 'array',
                        'description': 'Ordered sequence of campaign IDs',
                        'required': True,
                        'example': ['prospecting_campaign_id', 'retargeting_campaign_id']
                    }
                }),
                'display_order': 10
            }
        ]
        
        # Insert queries and collect their IDs for examples
        query_ids = {}
        for query in queries:
            query_response = client.table('build_guide_queries').insert(query).execute()
            if not query_response.data:
                logger.error(f"Failed to create query: {query['title']}")
            else:
                query_ids[query['title']] = query_response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
        
        # Create examples linked to the first query
        if 'DSP Campaign Exposure' in query_ids:
            examples = [
                {
                    'guide_query_id': query_ids['DSP Campaign Exposure'],
                    'example_name': 'Campaign Exposure Distribution',
                    'sample_data': json.dumps({
                        'rows': [
                            {'campaign_id': '123456789', 'exposure_level': '1-3 impressions', 'user_count': 450000},
                            {'campaign_id': '123456789', 'exposure_level': '4-6 impressions', 'user_count': 125000},
                            {'campaign_id': '123456789', 'exposure_level': '7-10 impressions', 'user_count': 45000},
                            {'campaign_id': '123456789', 'exposure_level': '10+ impressions', 'user_count': 15000}
                        ]
                    }),
                    'interpretation_markdown': """This distribution shows a typical exposure pattern:
- **450,000 users** with light exposure (1-3 impressions) - good for initial remarketing
- **125,000 users** with moderate exposure (4-6 impressions) - ideal for consideration messaging
- **45,000 users** with high exposure (7-10 impressions) - may benefit from creative refresh
- **15,000 users** with very high exposure (10+ impressions) - candidates for suppression to avoid fatigue""",
                    'display_order': 1
                }
            ]
            
            for example in examples:
                example_response = client.table('build_guide_examples').insert(example).execute()
                if not example_response.data:
                    logger.error(f"Failed to create example: {example['example_name']}")
                else:
                    logger.info(f"Created example: {example['example_name']}")
        
        # Create examples for Line Item query
        if 'DSP Line Item Exposure' in query_ids:
            examples = [
                {
                    'guide_query_id': query_ids['DSP Line Item Exposure'],
                    'example_name': 'Line Item Performance by Exposure',
                    'sample_data': json.dumps({
                        'rows': [
                            {'line_item_id': '987654321', 'impressions_threshold': '>= 1', 'audience_size': 500000, 'conversion_rate': 0.5},
                            {'line_item_id': '987654321', 'impressions_threshold': '>= 3', 'audience_size': 200000, 'conversion_rate': 0.8},
                            {'line_item_id': '987654321', 'impressions_threshold': '>= 5', 'audience_size': 75000, 'conversion_rate': 0.6},
                            {'line_item_id': '987654321', 'impressions_threshold': '>= 10', 'audience_size': 25000, 'conversion_rate': 0.3}
                        ]
                    }),
                    'interpretation_markdown': """This analysis reveals an optimal exposure window:
- Conversion rate **peaks at 3+ impressions** (0.8%)
- Performance **drops after 5 impressions** (0.6%)
- **Significant decline at 10+ impressions** (0.3%)

**Recommendation**: Target users with 3-5 impressions for optimal conversion rates while excluding those with 10+ impressions.""",
                    'display_order': 1
                }
            ]
            
            for example in examples:
                example_response = client.table('build_guide_examples').insert(example).execute()
                if not example_response.data:
                    logger.error(f"Failed to create example: {example['example_name']}")
                else:
                    logger.info(f"Created example: {example['example_name']}")
        
        # Create examples for Sponsored Ads Product Type query
        if 'Sponsored Ads Product Type' in query_ids:
            examples = [
                {
                    'guide_query_id': query_ids['Sponsored Ads Product Type'],
                    'example_name': 'Ad Product Type Exposure',
                    'sample_data': json.dumps({
                        'rows': [
                            {'ad_product_type': 'sponsored_products', 'user_count': 1250000, 'avg_impressions': 4.5},
                            {'ad_product_type': 'sponsored_brands', 'user_count': 850000, 'avg_impressions': 3.2},
                            {'ad_product_type': 'sponsored_display', 'user_count': 650000, 'avg_impressions': 5.8},
                            {'ad_product_type': 'sponsored_television', 'user_count': 125000, 'avg_impressions': 2.1}
                        ]
                    }),
                    'interpretation_markdown': """Cross-product exposure analysis shows:
- **Sponsored Products** has the highest reach (1.25M users)
- **Sponsored Display** shows highest frequency (5.8 avg impressions)
- **Sponsored Television** users have low frequency (2.1) - good for awareness campaigns
- Consider sequential messaging from STV → SP for purchase intent""",
                    'display_order': 1
                }
            ]
            
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
                'metric_name': 'impressions',
                'display_name': 'Impressions',
                'definition': 'Total number of ad impressions per user',
                'metric_type': 'metric',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_count',
                'display_name': 'User Count',
                'definition': 'Count of unique users in the audience',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'exposure_level',
                'display_name': 'Exposure Level',
                'definition': 'Categorization of impression frequency (1-3, 4-6, 7-10, 10+)',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate',
                'display_name': 'Conversion Rate',
                'definition': 'Rate of conversion at different exposure levels',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'last_exposure',
                'display_name': 'Last Exposure Date',
                'definition': 'Most recent date of ad exposure',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'campaign_path',
                'display_name': 'Campaign Path',
                'definition': 'Sequence of campaign exposures',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_id',
                'display_name': 'User ID',
                'definition': 'Unique identifier for users',
                'metric_type': 'dimension',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'campaign_id_string',
                'display_name': 'Campaign ID',
                'definition': 'Campaign identifier',
                'metric_type': 'dimension',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'line_item_id',
                'display_name': 'Line Item ID',
                'definition': 'Line item identifier',
                'metric_type': 'dimension',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'creative_id',
                'display_name': 'Creative ID',
                'definition': 'Creative identifier',
                'metric_type': 'dimension',
                'display_order': 10
            },
            {
                'guide_id': guide_id,
                'metric_name': 'ad_product_type',
                'display_name': 'Ad Product Type',
                'definition': 'Type of sponsored ad (sponsored_products, sponsored_brands, etc.)',
                'metric_type': 'dimension',
                'display_order': 11
            },
            {
                'guide_id': guide_id,
                'metric_name': 'behavior_segment_id',
                'display_name': 'Segment ID',
                'definition': 'Audience segment identifier',
                'metric_type': 'dimension',
                'display_order': 12
            },
            {
                'guide_id': guide_id,
                'metric_name': 'campaign',
                'display_name': 'Campaign Name',
                'definition': 'Campaign name',
                'metric_type': 'dimension',
                'display_order': 13
            },
            {
                'guide_id': guide_id,
                'metric_name': 'ad_group',
                'display_name': 'Ad Group',
                'definition': 'Ad group name',
                'metric_type': 'dimension',
                'display_order': 14
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            metric_response = client.table('build_guide_metrics').insert(metric).execute()
            if not metric_response.data:
                logger.error(f"Failed to create metric: {metric['metric_name']}")
            else:
                logger.info(f"Created metric: {metric['metric_name']}")
        
        logger.info("Successfully created DSP Exposure Audiences Build Guide")
        return True
        
    except Exception as e:
        logger.error(f"Error creating guide: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_dsp_exposure_audiences_guide()
    if success:
        print("Success! DSP Exposure Audiences guide created successfully!")
        print("Guide ID: guide_dsp_exposure_audiences")
    else:
        print("Failed to create DSP Exposure Audiences guide")
        sys.exit(1)