#!/usr/bin/env python3
"""Create Customer Journey Analytics (CJA) workflow in AMC"""

import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Customer Journey Analytics SQL query template
CJA_WORKFLOW = {
    "customer_journey_analysis": {
        "name": "Customer Journey Analytics (CJA)",
        "description": "Comprehensive analysis of customer journeys, touchpoints, and conversion paths across all advertising channels",
        "sql_query": """
-- Customer Journey Analytics Query
-- Analyzes the complete customer journey from first touch to conversion
WITH user_touchpoints AS (
    -- Collect all touchpoints from different channels
    SELECT 
        user_id,
        event_dt as touchpoint_time,
        CASE 
            WHEN source_table = 'dsp_impressions' THEN 'Display'
            WHEN source_table = 'dsp_clicks' THEN 'Display Click'
            WHEN source_table = 'sponsored_ads_impressions' THEN 'Sponsored Ads'
            WHEN source_table = 'sponsored_ads_clicks' THEN 'Sponsored Ads Click'
            WHEN source_table = 'sb_impressions' THEN 'Sponsored Brands'
            WHEN source_table = 'sb_clicks' THEN 'Sponsored Brands Click'
            WHEN source_table = 'sd_impressions' THEN 'Sponsored Display'
            WHEN source_table = 'sd_clicks' THEN 'Sponsored Display Click'
            ELSE 'Other'
        END as channel,
        campaign_id,
        creative_id,
        placement_id,
        CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END as is_conversion,
        CASE WHEN event_type = 'click' THEN 1 ELSE 0 END as is_click,
        order_id,
        product_id
    FROM (
        -- Union all touchpoint sources
        SELECT user_id, impression_dt as event_dt, 'impression' as event_type, 
               campaign_id, creative_id, placement_id, null as order_id, null as product_id,
               'dsp_impressions' as source_table
        FROM dsp_impressions
        WHERE impression_dt >= '{{start_date}}' AND impression_dt <= '{{end_date}}'
        
        UNION ALL
        
        SELECT user_id, click_dt as event_dt, 'click' as event_type,
               campaign_id, creative_id, placement_id, null as order_id, null as product_id,
               'dsp_clicks' as source_table  
        FROM dsp_clicks
        WHERE click_dt >= '{{start_date}}' AND click_dt <= '{{end_date}}'
        
        UNION ALL
        
        SELECT user_id, impression_dt as event_dt, 'impression' as event_type,
               campaign_id, null as creative_id, null as placement_id, null as order_id, asin as product_id,
               'sponsored_ads_impressions' as source_table
        FROM sponsored_ads_impressions
        WHERE impression_dt >= '{{start_date}}' AND impression_dt <= '{{end_date}}'
        
        UNION ALL
        
        SELECT user_id, click_dt as event_dt, 'click' as event_type,
               campaign_id, null as creative_id, null as placement_id, null as order_id, asin as product_id,
               'sponsored_ads_clicks' as source_table
        FROM sponsored_ads_clicks
        WHERE click_dt >= '{{start_date}}' AND click_dt <= '{{end_date}}'
        
        UNION ALL
        
        SELECT user_id, conversion_dt as event_dt, 'conversion' as event_type,
               null as campaign_id, null as creative_id, null as placement_id, 
               order_id, purchased_asin as product_id,
               'conversions' as source_table
        FROM conversions
        WHERE conversion_dt >= '{{start_date}}' AND conversion_dt <= '{{end_date}}'
    )
),
user_journeys AS (
    -- Build complete journey for each user
    SELECT 
        user_id,
        ARRAY_AGG(
            STRUCT(
                touchpoint_time,
                channel,
                campaign_id,
                is_click,
                is_conversion
            ) ORDER BY touchpoint_time
        ) as journey,
        MAX(CASE WHEN is_conversion = 1 THEN touchpoint_time END) as conversion_time,
        COUNT(*) as total_touchpoints,
        COUNT(DISTINCT channel) as unique_channels,
        SUM(is_click) as total_clicks,
        SUM(is_conversion) as total_conversions,
        MIN(touchpoint_time) as first_touch_time,
        MAX(touchpoint_time) as last_touch_time
    FROM user_touchpoints
    GROUP BY user_id
),
journey_metrics AS (
    -- Calculate journey-level metrics
    SELECT
        user_id,
        journey,
        conversion_time,
        total_touchpoints,
        unique_channels,
        total_clicks,
        total_conversions,
        TIMESTAMP_DIFF(last_touch_time, first_touch_time, DAY) as journey_duration_days,
        -- Extract first and last touch channels
        journey[OFFSET(0)].channel as first_touch_channel,
        journey[ARRAY_LENGTH(journey) - 1].channel as last_touch_channel,
        -- Check if journey resulted in conversion
        CASE WHEN total_conversions > 0 THEN 1 ELSE 0 END as converted
    FROM user_journeys
),
-- Aggregate journey patterns
journey_patterns AS (
    SELECT
        CASE 
            WHEN converted = 1 THEN 'Converted'
            ELSE 'Non-Converted'
        END as journey_type,
        first_touch_channel,
        last_touch_channel,
        unique_channels,
        CASE 
            WHEN total_touchpoints <= 3 THEN '1-3 touchpoints'
            WHEN total_touchpoints <= 7 THEN '4-7 touchpoints'
            WHEN total_touchpoints <= 15 THEN '8-15 touchpoints'
            ELSE '16+ touchpoints'
        END as touchpoint_bucket,
        COUNT(DISTINCT user_id) as user_count,
        AVG(journey_duration_days) as avg_journey_days,
        AVG(total_touchpoints) as avg_touchpoints,
        AVG(total_clicks) as avg_clicks
    FROM journey_metrics
    GROUP BY 1, 2, 3, 4, 5
)
-- Final output
SELECT 
    journey_type,
    first_touch_channel,
    last_touch_channel,
    unique_channels,
    touchpoint_bucket,
    user_count,
    ROUND(avg_journey_days, 2) as avg_journey_days,
    ROUND(avg_touchpoints, 2) as avg_touchpoints,
    ROUND(avg_clicks, 2) as avg_clicks,
    ROUND(100.0 * user_count / SUM(user_count) OVER(), 2) as percentage_of_users
FROM journey_patterns
ORDER BY user_count DESC
LIMIT 100
        """,
        "parameters": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "conversion_window_days": 30
        },
        "tags": ["customer_journey", "multi_touch", "attribution", "analysis"]
    },
    "conversion_path_analysis": {
        "name": "Conversion Path Analysis",
        "description": "Detailed analysis of the most common paths that lead to conversions",
        "sql_query": """
-- Conversion Path Analysis
-- Identifies the most common sequences of touchpoints that lead to conversions
WITH conversion_users AS (
    -- First identify users who converted
    SELECT DISTINCT user_id, conversion_dt, order_id
    FROM conversions
    WHERE conversion_dt >= '{{start_date}}' 
    AND conversion_dt <= '{{end_date}}'
),
user_touchpoints AS (
    -- Get all touchpoints for converting users within the lookback window
    SELECT 
        t.user_id,
        t.touchpoint_time,
        t.channel_type,
        t.campaign_id,
        t.interaction_type,
        c.conversion_dt,
        c.order_id
    FROM (
        -- Combine all touchpoint sources
        SELECT user_id, impression_dt as touchpoint_time, 'DSP' as channel_type,
               campaign_id, 'impression' as interaction_type
        FROM dsp_impressions
        WHERE impression_dt >= DATE_SUB('{{start_date}}', INTERVAL {{lookback_days}} DAY)
        AND impression_dt <= '{{end_date}}'
        
        UNION ALL
        
        SELECT user_id, click_dt as touchpoint_time, 'DSP' as channel_type,
               campaign_id, 'click' as interaction_type
        FROM dsp_clicks
        WHERE click_dt >= DATE_SUB('{{start_date}}', INTERVAL {{lookback_days}} DAY)
        AND click_dt <= '{{end_date}}'
        
        UNION ALL
        
        SELECT user_id, impression_dt as touchpoint_time, 'SP' as channel_type,
               campaign_id, 'impression' as interaction_type
        FROM sponsored_ads_impressions
        WHERE impression_dt >= DATE_SUB('{{start_date}}', INTERVAL {{lookback_days}} DAY)
        AND impression_dt <= '{{end_date}}'
        
        UNION ALL
        
        SELECT user_id, click_dt as touchpoint_time, 'SP' as channel_type,
               campaign_id, 'click' as interaction_type
        FROM sponsored_ads_clicks
        WHERE click_dt >= DATE_SUB('{{start_date}}', INTERVAL {{lookback_days}} DAY)
        AND click_dt <= '{{end_date}}'
    ) t
    INNER JOIN conversion_users c ON t.user_id = c.user_id
    WHERE t.touchpoint_time <= c.conversion_dt
    AND t.touchpoint_time >= DATE_SUB(c.conversion_dt, INTERVAL {{lookback_days}} DAY)
),
conversion_paths AS (
    -- Build the path for each conversion
    SELECT 
        user_id,
        order_id,
        conversion_dt,
        ARRAY_TO_STRING(
            ARRAY_AGG(
                CONCAT(channel_type, ':', interaction_type)
                ORDER BY touchpoint_time
            ), 
            ' > '
        ) as path_string,
        ARRAY_AGG(
            STRUCT(
                touchpoint_time,
                channel_type,
                campaign_id,
                interaction_type
            )
            ORDER BY touchpoint_time
        ) as path_details,
        COUNT(*) as path_length
    FROM user_touchpoints
    GROUP BY user_id, order_id, conversion_dt
),
path_summary AS (
    -- Aggregate paths to find most common patterns
    SELECT 
        path_string,
        path_length,
        COUNT(*) as conversion_count,
        COUNT(DISTINCT user_id) as unique_users,
        AVG(TIMESTAMP_DIFF(conversion_dt, path_details[OFFSET(0)].touchpoint_time, HOUR)) as avg_hours_to_convert
    FROM conversion_paths
    GROUP BY path_string, path_length
    HAVING COUNT(*) >= {{min_path_frequency}}
)
-- Final output with path rankings
SELECT 
    ROW_NUMBER() OVER (ORDER BY conversion_count DESC) as path_rank,
    path_string,
    path_length,
    conversion_count,
    unique_users,
    ROUND(avg_hours_to_convert, 2) as avg_hours_to_convert,
    ROUND(100.0 * conversion_count / SUM(conversion_count) OVER(), 2) as pct_of_conversions
FROM path_summary
ORDER BY conversion_count DESC
LIMIT 50
        """,
        "parameters": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "lookback_days": 30,
            "min_path_frequency": 10
        },
        "tags": ["conversion", "path_analysis", "attribution"]
    }
}

def get_user_and_instance():
    """Get user ID and a sandbox AMC instance"""
    logger.info("Fetching user and AMC instance...")
    
    # Get user
    user_response = supabase.table('users').select('*').limit(1).execute()
    if not user_response.data:
        logger.error("No user found!")
        return None, None
    
    user_id = user_response.data[0]['id']
    logger.info(f"✓ Found user: {user_response.data[0]['email']}")
    
    # Get AMC instances (prefer sandbox for testing)
    instances_response = supabase.table('amc_instances').select('*, amc_accounts(*)').execute()
    if not instances_response.data:
        logger.error("No AMC instances found!")
        return user_id, None
    
    # Try to find a sandbox instance first
    sandbox_instances = [i for i in instances_response.data if 'sandbox' in i['instance_name'].lower()]
    instance = sandbox_instances[0] if sandbox_instances else instances_response.data[0]
    
    logger.info(f"✓ Using instance: {instance['instance_name']} ({instance['instance_id']})")
    
    return user_id, instance

def create_cja_workflows(user_id, instance):
    """Create CJA workflows and templates"""
    logger.info("\nCreating Customer Journey Analytics workflows...")
    
    created_count = 0
    
    for workflow_key, workflow_data in CJA_WORKFLOW.items():
        # Create workflow
        workflow_record = {
            'id': str(uuid.uuid4()),
            'workflow_id': f"wf_cja_{workflow_key}_{uuid.uuid4().hex[:8]}",
            'name': workflow_data['name'],
            'description': workflow_data['description'],
            'instance_id': instance['id'],
            'sql_query': workflow_data['sql_query'],
            'parameters': workflow_data['parameters'],
            'user_id': user_id,
            'status': 'active',
            'is_template': True,
            'tags': workflow_data['tags']
        }
        
        try:
            response = supabase.table('workflows').insert(workflow_record).execute()
            logger.info(f"  ✓ Created workflow: {workflow_data['name']}")
            created_count += 1
        except Exception as e:
            logger.error(f"  ✗ Error creating workflow {workflow_data['name']}: {str(e)}")
        
        # Also create as a query template
        template_record = {
            'id': str(uuid.uuid4()),
            'template_id': f"tpl_cja_{workflow_key}",
            'name': workflow_data['name'],
            'description': workflow_data['description'],
            'category': 'Customer Journey',
            'sql_template': workflow_data['sql_query'],
            'parameters_schema': {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "lookback_days": {"type": "integer", "minimum": 1, "maximum": 90},
                    "conversion_window_days": {"type": "integer", "minimum": 1, "maximum": 90},
                    "min_path_frequency": {"type": "integer", "minimum": 1}
                },
                "required": ["start_date", "end_date"]
            },
            'default_parameters': workflow_data['parameters'],
            'user_id': user_id,
            'is_public': True,
            'tags': workflow_data['tags'],
            'usage_count': 0
        }
        
        try:
            response = supabase.table('query_templates').insert(template_record).execute()
            logger.info(f"  ✓ Created template: {workflow_data['name']}")
        except Exception as e:
            logger.error(f"  ✗ Error creating template {workflow_data['name']}: {str(e)}")
    
    logger.info(f"\n✓ Created {created_count} CJA workflows")
    return created_count

def main():
    """Main function"""
    logger.info("Creating Customer Journey Analytics Workflows")
    logger.info("=" * 60)
    
    # Get user and instance
    user_id, instance = get_user_and_instance()
    if not user_id or not instance:
        logger.error("Failed to get required data")
        return
    
    # Create CJA workflows
    created = create_cja_workflows(user_id, instance)
    
    if created > 0:
        logger.info("\n✅ CJA workflow creation completed!")
        logger.info("\nNext steps:")
        logger.info("1. View the workflows in the UI at /workflows")
        logger.info("2. Customize the SQL queries with your specific requirements")
        logger.info("3. Execute the workflows to analyze customer journeys")
        logger.info("4. Schedule regular executions for ongoing analysis")
    else:
        logger.error("\n❌ No workflows were created")

if __name__ == "__main__":
    main()