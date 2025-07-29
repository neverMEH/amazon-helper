#!/usr/bin/env python3
"""Create sample AMC workflows in Supabase"""

import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Sample AMC SQL queries
SAMPLE_QUERIES = {
    "path_to_conversion": {
        "name": "Path to Conversion Analysis",
        "description": "Analyze the customer journey and touchpoints leading to conversions",
        "sql_query": """
WITH conversion_paths AS (
    SELECT 
        user_id,
        MAX(CASE WHEN event_type = 'conversion' THEN event_dt END) as conversion_time,
        ARRAY_AGG(
            STRUCT(
                event_dt, 
                event_type, 
                campaign_id, 
                placement_id
            ) ORDER BY event_dt
        ) as touchpoints
    FROM impressions_clicks_conversions
    WHERE event_dt >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY user_id
    HAVING MAX(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) = 1
)
SELECT 
    touchpoints,
    COUNT(DISTINCT user_id) as user_count,
    AVG(ARRAY_LENGTH(touchpoints)) as avg_touchpoints
FROM conversion_paths
GROUP BY touchpoints
ORDER BY user_count DESC
LIMIT 100
        """,
        "parameters": {
            "lookback_days": 30,
            "conversion_type": "purchase"
        }
    },
    "new_to_brand": {
        "name": "New-to-Brand Customer Analysis",
        "description": "Identify and analyze customers who are new to the brand",
        "sql_query": """
WITH first_purchases AS (
    SELECT 
        user_id,
        MIN(order_date) as first_order_date,
        campaign_id
    FROM conversions
    WHERE order_date >= CURRENT_DATE - INTERVAL '90' DAY
    GROUP BY user_id, campaign_id
)
SELECT 
    DATE_TRUNC('week', first_order_date) as week,
    campaign_id,
    COUNT(DISTINCT user_id) as new_customers,
    SUM(order_value) as total_revenue
FROM first_purchases
JOIN conversions USING (user_id, campaign_id)
WHERE first_order_date = order_date
GROUP BY DATE_TRUNC('week', first_order_date), campaign_id
ORDER BY week DESC
        """,
        "parameters": {
            "lookback_days": 90,
            "brand_asin_list": []
        }
    },
    "audience_overlap": {
        "name": "Audience Overlap Analysis",
        "description": "Analyze overlap between different campaign audiences",
        "sql_query": """
WITH campaign_audiences AS (
    SELECT 
        campaign_id,
        ARRAY_AGG(DISTINCT user_id) as audience_users
    FROM impressions
    WHERE impression_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
    GROUP BY campaign_id
)
SELECT 
    c1.campaign_id as campaign_1,
    c2.campaign_id as campaign_2,
    CARDINALITY(ARRAY_INTERSECT(c1.audience_users, c2.audience_users)) as overlap_count,
    CARDINALITY(c1.audience_users) as campaign_1_size,
    CARDINALITY(c2.audience_users) as campaign_2_size,
    CAST(CARDINALITY(ARRAY_INTERSECT(c1.audience_users, c2.audience_users)) AS FLOAT) / 
        CARDINALITY(c1.audience_users) as overlap_percentage
FROM campaign_audiences c1
CROSS JOIN campaign_audiences c2
WHERE c1.campaign_id < c2.campaign_id
ORDER BY overlap_count DESC
LIMIT 50
        """,
        "parameters": {
            "lookback_days": 30
        }
    }
}

def get_user_and_instances():
    """Get user ID and AMC instances from Supabase"""
    print("Fetching user and AMC instances...")
    
    # Get user
    user_response = supabase.table('users').select('*').limit(1).execute()
    if not user_response.data:
        print("✗ No user found!")
        return None, None
    
    user_id = user_response.data[0]['id']
    print(f"✓ Found user: {user_response.data[0]['email']}")
    
    # Get AMC instances
    instances_response = supabase.table('amc_instances').select('*, amc_accounts(*)').execute()
    if not instances_response.data:
        print("✗ No AMC instances found!")
        return user_id, None
    
    print(f"✓ Found {len(instances_response.data)} AMC instances")
    
    # Filter for sandbox instances for testing
    sandbox_instances = [i for i in instances_response.data if 'sandbox' in i['instance_name'].lower()]
    print(f"✓ Found {len(sandbox_instances)} sandbox instances for testing")
    
    return user_id, sandbox_instances

def create_workflows(user_id, instances):
    """Create sample workflows"""
    print("\nCreating sample workflows...")
    
    workflow_count = 0
    
    # Use the first sandbox instance for all workflows
    if not instances:
        print("✗ No instances available for workflows")
        return
    
    instance = instances[0]
    print(f"\nUsing instance: {instance['instance_name']} ({instance['instance_id']})")
    
    for query_key, query_data in SAMPLE_QUERIES.items():
        workflow_data = {
            'id': str(uuid.uuid4()),
            'workflow_id': f"wf_{query_key}_{uuid.uuid4().hex[:8]}",
            'name': query_data['name'],
            'description': query_data['description'],
            'instance_id': instance['id'],
            'sql_query': query_data['sql_query'],
            'parameters': query_data['parameters'],
            'user_id': user_id,
            'status': 'active',
            'is_template': True,
            'tags': ['sample', 'template', query_key]
        }
        
        try:
            response = supabase.table('workflows').insert(workflow_data).execute()
            print(f"  ✓ Created workflow: {query_data['name']}")
            workflow_count += 1
        except Exception as e:
            print(f"  ✗ Error creating workflow {query_data['name']}: {str(e)}")
    
    print(f"\n✓ Total workflows created: {workflow_count}")

def create_query_templates(user_id):
    """Create query templates"""
    print("\nCreating query templates...")
    
    template_count = 0
    
    for query_key, query_data in SAMPLE_QUERIES.items():
        template_data = {
            'id': str(uuid.uuid4()),
            'template_id': f"tpl_{query_key}",
            'name': query_data['name'],
            'description': query_data['description'],
            'category': 'Analysis',
            'sql_template': query_data['sql_query'],
            'parameters_schema': {
                "type": "object",
                "properties": {
                    param: {"type": "number" if "days" in param else "array"} 
                    for param in query_data['parameters'].keys()
                }
            },
            'default_parameters': query_data['parameters'],
            'user_id': user_id,
            'is_public': True,
            'tags': ['sample', 'analysis', query_key],
            'usage_count': 0
        }
        
        try:
            response = supabase.table('query_templates').insert(template_data).execute()
            print(f"  ✓ Created template: {query_data['name']}")
            template_count += 1
        except Exception as e:
            print(f"  ✗ Error creating template {query_data['name']}: {str(e)}")
    
    print(f"\n✓ Total templates created: {template_count}")

def main():
    """Main function"""
    print("Creating Sample AMC Workflows")
    print("=" * 50)
    
    # Get user and instances
    user_id, instances = get_user_and_instances()
    if not user_id:
        return
    
    # Create workflows
    create_workflows(user_id, instances)
    
    # Create query templates
    create_query_templates(user_id)
    
    print("\n✅ Sample workflow creation completed!")
    print("\nNext steps:")
    print("1. Start the API server to execute workflows")
    print("2. Use the sandbox instances to test query execution")
    print("3. Monitor execution status in the workflow_executions table")

if __name__ == "__main__":
    main()