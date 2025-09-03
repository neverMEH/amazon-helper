#!/usr/bin/env python
"""
Script to create a sample Query Flow Template
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import get_supabase_client
import json

def create_sample_template():
    client = get_supabase_client()
    
    # 1. Create the main template
    template_data = {
        "template_id": "campaign_performance_analysis",
        "name": "Campaign Performance Analysis",
        "description": "Analyze campaign performance metrics including impressions, clicks, conversions, and ROAS",
        "category": "Performance",
        "sql_template": """
WITH campaign_metrics AS (
    SELECT 
        campaign,
        campaign_id,
        SUM(impressions) as total_impressions,
        SUM(clicks) as total_clicks,
        SUM(conversions) as total_conversions,
        SUM(cost) as total_cost,
        SUM(revenue) as total_revenue,
        CASE 
            WHEN SUM(impressions) > 0 
            THEN CAST(SUM(clicks) AS DOUBLE) / SUM(impressions) * 100
            ELSE 0 
        END as ctr,
        CASE 
            WHEN SUM(clicks) > 0 
            THEN CAST(SUM(conversions) AS DOUBLE) / SUM(clicks) * 100
            ELSE 0 
        END as conversion_rate,
        CASE 
            WHEN SUM(cost) > 0 
            THEN SUM(revenue) / SUM(cost)
            ELSE 0 
        END as roas
    FROM impressions_clicks_conversions
    WHERE 
        event_dt BETWEEN :start_date AND :end_date
        {% if campaign_ids %}
        AND campaign_id IN (:campaign_ids)
        {% endif %}
    GROUP BY campaign, campaign_id
)
SELECT * FROM campaign_metrics
ORDER BY total_revenue DESC
LIMIT :limit
        """,
        "is_active": True,
        "is_public": True,
        "tags": ["performance", "campaign", "roas", "metrics"]
    }
    
    result = client.table('query_flow_templates').insert(template_data).execute()
    template = result.data[0]
    print(f"Created template: {template['name']} (ID: {template['id']})")
    
    # 2. Add parameters
    parameters = [
        {
            "template_id": template['id'],
            "parameter_name": "start_date",
            "display_name": "Start Date",
            "parameter_type": "date",
            "required": True,
            "default_value": "2024-01-01",
            "validation_rules": {
                "min": "2023-01-01",
                "max": "2025-12-31"
            },
            "ui_component": "date_picker",
            "ui_config": {
                "placeholder": "Select start date",
                "help_text": "Beginning of the analysis period"
            },
            "order_index": 1
        },
        {
            "template_id": template['id'],
            "parameter_name": "end_date",
            "display_name": "End Date",
            "parameter_type": "date",
            "required": True,
            "default_value": "2024-12-31",
            "validation_rules": {
                "min": "2023-01-01",
                "max": "2025-12-31"
            },
            "ui_component": "date_picker",
            "ui_config": {
                "placeholder": "Select end date",
                "help_text": "End of the analysis period"
            },
            "order_index": 2
        },
        {
            "template_id": template['id'],
            "parameter_name": "campaign_ids",
            "display_name": "Campaigns",
            "parameter_type": "campaign_list",
            "required": False,
            "validation_rules": {
                "min_selections": 0,
                "max_selections": 100
            },
            "ui_component": "campaign_selector",
            "ui_config": {
                "placeholder": "Select campaigns (optional)",
                "help_text": "Leave empty to analyze all campaigns",
                "multi_select": True,
                "show_all_option": True
            },
            "order_index": 3
        },
        {
            "template_id": template['id'],
            "parameter_name": "limit",
            "display_name": "Results Limit",
            "parameter_type": "number",
            "required": True,
            "default_value": 100,
            "validation_rules": {
                "min_value": 1,
                "max_value": 10000,
                "type": "integer"
            },
            "ui_component": "number_input",
            "ui_config": {
                "placeholder": "Number of results",
                "help_text": "Maximum number of campaigns to return"
            },
            "order_index": 4
        }
    ]
    
    for param in parameters:
        client.table('template_parameters').insert(param).execute()
        print(f"  Added parameter: {param['display_name']}")
    
    # 3. Add chart configurations
    charts = [
        {
            "template_id": template['id'],
            "chart_name": "Campaign Performance Table",
            "chart_type": "table",
            "chart_config": {
                "responsive": True,
                "sortable": True,
                "filterable": True,
                "exportable": True,
                "pageSize": 25
            },
            "data_mapping": {
                "sort_by": "total_revenue",
                "sort_order": "desc"
            },
            "is_default": True,
            "order_index": 1
        },
        {
            "template_id": template['id'],
            "chart_name": "Revenue by Campaign",
            "chart_type": "bar",
            "chart_config": {
                "responsive": True,
                "maintainAspectRatio": False,
                "indexAxis": "y"
            },
            "data_mapping": {
                "x_field": "campaign",
                "y_field": "total_revenue",
                "value_format": "currency",
                "limit": 20,
                "sort_by": "total_revenue",
                "sort_order": "desc"
            },
            "is_default": False,
            "order_index": 2
        },
        {
            "template_id": template['id'],
            "chart_name": "ROAS Distribution",
            "chart_type": "scatter",
            "chart_config": {
                "responsive": True,
                "description": "Cost vs Revenue scatter plot"
            },
            "data_mapping": {
                "x_field": "total_cost",
                "y_field": "total_revenue",
                "value_format": "currency"
            },
            "is_default": False,
            "order_index": 3
        }
    ]
    
    for chart in charts:
        client.table('template_chart_configs').insert(chart).execute()
        print(f"  Added chart: {chart['chart_name']}")
    
    print(f"\nTemplate created successfully!")
    print(f"Template ID: {template['template_id']}")
    print(f"You can now use this template in the Query Flow Templates page")

if __name__ == "__main__":
    create_sample_template()