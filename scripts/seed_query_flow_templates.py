#!/usr/bin/env python
"""
Seed script for Query Flow Templates
Creates the Supergoop Branded Search Trends template with all configurations
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.services.query_flow_template_service import QueryFlowTemplateService
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


def get_supergoop_template():
    """Get the Supergoop Branded Search Trends template configuration"""
    
    # Main template SQL
    sql_template = """-- AMC SQL: Branded Search Trend Analysis
-- Dynamic parameters: date range, brand keywords, optional campaign filtering

WITH daily_metrics AS (
  SELECT
    impression_date AS event_date,
    campaign_id,
    campaign,
    SUM(impressions) AS daily_impressions,
    0 AS daily_branded_searches,
    COUNT(DISTINCT user_id) AS unique_users
  FROM
    dsp_impressions
  WHERE
    impression_date >= '{{start_date}}'
    AND impression_date <= '{{end_date}}'
    {{campaign_filter}}
  GROUP BY
    impression_date, campaign_id, campaign
    
  UNION ALL
  
  SELECT
    conversion_event_date AS event_date,
    campaign_id,
    campaign,
    0 AS daily_impressions,
    SUM(conversions) AS daily_branded_searches,
    COUNT(DISTINCT user_id) AS unique_users
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    tracked_item SIMILAR TO '^keyword.*'
    AND (
      {{brand_keyword_conditions}}
    )
    AND conversion_event_date >= '{{start_date}}'
    AND conversion_event_date <= '{{end_date}}'
    {{campaign_filter}}
  GROUP BY
    conversion_event_date, campaign_id, campaign
),
aggregated AS (
  SELECT
    event_date,
    campaign_id,
    campaign,
    SUM(daily_impressions) AS impressions,
    SUM(daily_branded_searches) AS branded_searches,
    SUM(unique_users) AS total_unique_users,
    CAST(SUM(daily_branded_searches) AS DOUBLE) / 
    NULLIF(CAST(SUM(daily_impressions) AS DOUBLE), 0) AS search_rate
  FROM
    daily_metrics
  GROUP BY
    event_date, campaign_id, campaign
)
SELECT
  DATE_TRUNC('week', event_date) AS week_start,
  campaign,
  SUM(impressions) AS total_impressions,
  SUM(branded_searches) AS total_branded_searches,
  COUNT(DISTINCT campaign_id) AS campaign_count,
  SUM(total_unique_users) AS weekly_unique_users,
  ROUND(
    CAST(SUM(branded_searches) AS DOUBLE) / 
    NULLIF(CAST(SUM(impressions) AS DOUBLE), 0), 
    6
  ) AS weekly_search_rate,
  ROUND(STDDEV(search_rate), 6) AS search_rate_volatility
FROM
  aggregated
WHERE
  total_unique_users >= 100  -- Privacy compliance threshold
GROUP BY
  DATE_TRUNC('week', event_date), campaign
HAVING 
  SUM(total_unique_users) >= 100  -- Additional privacy compliance"""

    template_data = {
        'template_id': 'supergoop_branded_search_trends',
        'name': 'Supergoop Branded Search Trend Analysis',
        'description': 'Analyze branded search trends over time with campaign performance metrics. Track how DSP impressions drive branded searches on Amazon with customizable date ranges and brand keyword variations.',
        'category': 'Brand Analysis',
        'sql_template': sql_template,
        'is_active': True,
        'is_public': True,
        'version': 1,
        'tags': ['brand', 'search', 'trends', 'dsp', 'attribution'],
        'metadata': {
            'author': 'RecomAMP Team',
            'use_case': 'Brand search trend analysis',
            'data_sources': ['dsp_impressions', 'amazon_attributed_events_by_conversion_time'],
            'min_lookback_days': 7,
            'max_lookback_days': 365
        }
    }
    
    return template_data


def get_template_parameters():
    """Get parameter definitions for the Supergoop template"""
    
    parameters = [
        {
            'parameter_name': 'start_date',
            'display_name': 'Start Date',
            'parameter_type': 'date',
            'required': True,
            'default_value': None,  # Will be computed from date_range
            'validation_rules': {
                'min': '2024-01-01',
                'max': '2025-12-31',
                'allow_future': False
            },
            'ui_component': 'DateParameter',
            'ui_config': {
                'placeholder': 'Select start date',
                'help_text': 'Beginning of the analysis period'
            },
            'dependencies': ['date_range'],
            'order_index': 1
        },
        {
            'parameter_name': 'end_date',
            'display_name': 'End Date',
            'parameter_type': 'date',
            'required': True,
            'default_value': None,  # Will be computed from date_range
            'validation_rules': {
                'min': '2024-01-01',
                'max': '2025-12-31',
                'allow_future': False
            },
            'ui_component': 'DateParameter',
            'ui_config': {
                'placeholder': 'Select end date',
                'help_text': 'End of the analysis period'
            },
            'dependencies': ['date_range'],
            'order_index': 2
        },
        {
            'parameter_name': 'date_range',
            'display_name': 'Quick Date Range',
            'parameter_type': 'date_range',
            'required': False,
            'default_value': {'preset': 'last_90_days'},
            'validation_rules': {
                'min_days': 7,
                'max_days': 365,
                'allow_future': False
            },
            'ui_component': 'DateRangeParameter',
            'ui_config': {
                'show_presets': True,
                'presets': [
                    {'label': 'Last 7 Days', 'value': 'last_7_days'},
                    {'label': 'Last 30 Days', 'value': 'last_30_days'},
                    {'label': 'Last 90 Days', 'value': 'last_90_days'},
                    {'label': 'Last 365 Days', 'value': 'last_365_days'},
                    {'label': 'This Month', 'value': 'this_month'},
                    {'label': 'Last Month', 'value': 'last_month'}
                ],
                'help_text': 'Select a preset or custom date range'
            },
            'order_index': 0
        },
        {
            'parameter_name': 'brand_keywords',
            'display_name': 'Brand Keywords',
            'parameter_type': 'string_list',
            'required': True,
            'default_value': ['supergoop', 'super goop', 'super.?goop'],
            'validation_rules': {
                'min_items': 1,
                'max_items': 10,
                'pattern': '^[a-zA-Z0-9\\s\\-\\.\\?\\*]+$',
                'max_length': 50
            },
            'ui_component': 'StringListParameter',
            'ui_config': {
                'placeholder': 'Enter brand variations (e.g., supergoop, super goop)',
                'allow_add': True,
                'allow_remove': True,
                'help_text': 'Add variations of your brand name to track. Supports basic pattern matching.'
            },
            'order_index': 3
        },
        {
            'parameter_name': 'brand_keyword_conditions',
            'display_name': 'Brand Keyword SQL Conditions',
            'parameter_type': 'string',
            'required': False,
            'default_value': None,  # Generated from brand_keywords
            'validation_rules': {},
            'ui_component': 'HiddenParameter',  # Not shown to user
            'ui_config': {},
            'dependencies': ['brand_keywords'],
            'order_index': 4
        },
        {
            'parameter_name': 'campaigns',
            'display_name': 'Filter by Campaigns (Optional)',
            'parameter_type': 'campaign_list',
            'required': False,
            'default_value': [],
            'validation_rules': {
                'min_selections': 0,
                'max_selections': 50,
                'allow_all': True
            },
            'ui_component': 'CampaignParameter',
            'ui_config': {
                'multi_select': True,
                'show_all_option': True,
                'placeholder': 'Select campaigns to filter (leave empty for all)',
                'help_text': 'Optionally filter results to specific campaigns'
            },
            'order_index': 5
        },
        {
            'parameter_name': 'campaign_filter',
            'display_name': 'Campaign Filter SQL',
            'parameter_type': 'string',
            'required': False,
            'default_value': '',  # Generated from campaigns selection
            'validation_rules': {},
            'ui_component': 'HiddenParameter',  # Not shown to user
            'ui_config': {},
            'dependencies': ['campaigns'],
            'order_index': 6
        }
    ]
    
    return parameters


def get_chart_configs():
    """Get chart configurations for the Supergoop template"""
    
    chart_configs = [
        {
            'chart_name': 'Weekly Search Rate Trends',
            'chart_type': 'line',
            'is_default': True,
            'order_index': 1,
            'chart_config': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': True,
                        'position': 'bottom'
                    },
                    'title': {
                        'display': True,
                        'text': 'Weekly Search Rate Trends by Campaign'
                    },
                    'tooltip': {
                        'mode': 'index',
                        'intersect': False
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Search Rate (%)'
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Week Starting'
                        }
                    }
                }
            },
            'data_mapping': {
                'x_field': 'week_start',
                'y_field': 'weekly_search_rate',
                'series_field': 'campaign',
                'value_format': 'percentage',
                'date_format': 'MMM DD',
                'aggregation': None
            }
        },
        {
            'chart_name': 'Campaign Performance Overview',
            'chart_type': 'bar',
            'is_default': False,
            'order_index': 2,
            'chart_config': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': True,
                        'position': 'top'
                    },
                    'title': {
                        'display': True,
                        'text': 'Total Impressions vs Branded Searches by Campaign'
                    }
                },
                'scales': {
                    'y': {
                        'type': 'linear',
                        'display': True,
                        'position': 'left',
                        'title': {
                            'display': True,
                            'text': 'Impressions'
                        }
                    },
                    'y1': {
                        'type': 'linear',
                        'display': True,
                        'position': 'right',
                        'title': {
                            'display': True,
                            'text': 'Branded Searches'
                        },
                        'grid': {
                            'drawOnChartArea': False
                        }
                    }
                }
            },
            'data_mapping': {
                'x_field': 'campaign',
                'y_fields': ['total_impressions', 'total_branded_searches'],
                'y_axes': ['y', 'y1'],
                'aggregation': 'sum',
                'sort_by': 'total_branded_searches',
                'sort_order': 'desc',
                'limit': 20
            }
        },
        {
            'chart_name': 'Detailed Campaign Metrics',
            'chart_type': 'table',
            'is_default': False,
            'order_index': 3,
            'chart_config': {
                'columns': [
                    {'field': 'week_start', 'header': 'Week', 'format': 'date'},
                    {'field': 'campaign', 'header': 'Campaign', 'format': 'string'},
                    {'field': 'total_impressions', 'header': 'Impressions', 'format': 'number'},
                    {'field': 'total_branded_searches', 'header': 'Searches', 'format': 'number'},
                    {'field': 'weekly_search_rate', 'header': 'Search Rate', 'format': 'percentage'},
                    {'field': 'weekly_unique_users', 'header': 'Unique Users', 'format': 'number'},
                    {'field': 'search_rate_volatility', 'header': 'Volatility', 'format': 'decimal'}
                ],
                'pagination': True,
                'pageSize': 50,
                'sortable': True,
                'filterable': True,
                'exportable': True
            },
            'data_mapping': {
                'sort_by': 'week_start',
                'sort_order': 'desc'
            }
        },
        {
            'chart_name': 'Search Rate Volatility Analysis',
            'chart_type': 'bar',
            'is_default': False,
            'order_index': 4,
            'chart_config': {
                'indexAxis': 'y',
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': False
                    },
                    'title': {
                        'display': True,
                        'text': 'Campaign Search Rate Volatility (Lower = More Stable)'
                    }
                },
                'scales': {
                    'x': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Volatility Index'
                        }
                    }
                }
            },
            'data_mapping': {
                'x_field': 'search_rate_volatility',
                'y_field': 'campaign',
                'aggregation': 'avg',
                'sort_by': 'search_rate_volatility',
                'sort_order': 'asc',
                'limit': 15,
                'color_scheme': 'gradient'
            }
        }
    ]
    
    return chart_configs


async def seed_templates():
    """Main function to seed the query flow templates"""
    
    try:
        service = QueryFlowTemplateService()
        
        # Check if template already exists
        logger.info("Checking for existing Supergoop template...")
        existing = service.get_template('supergoop_branded_search_trends')
        
        if existing:
            logger.info("Template already exists. Updating...")
            # You might want to update it or skip
            logger.info("Skipping update to preserve existing template")
            return
        
        # Get template configurations
        template_data = get_supergoop_template()
        parameters = get_template_parameters()
        chart_configs = get_chart_configs()
        
        # Create template
        # Note: In a real scenario, you'd get the user_id from authentication
        # For seeding, we'll use a system user ID or admin ID
        # You might need to create a system user first or use an existing admin
        
        logger.info("Creating Supergoop Branded Search Trends template...")
        
        # For now, we'll insert directly since we're seeding
        # In production, use the service method with proper user ID
        from amc_manager.core.supabase_client import SupabaseManager
        
        client = SupabaseManager.get_client()
        
        # Insert template
        template_result = client.table('query_flow_templates').insert(template_data).execute()
        
        if not template_result.data:
            logger.error("Failed to create template")
            return
        
        template = template_result.data[0]
        template_id = template['id']
        
        logger.info(f"Created template with ID: {template_id}")
        
        # Insert parameters
        for param in parameters:
            param['template_id'] = template_id
        
        param_result = client.table('template_parameters').insert(parameters).execute()
        logger.info(f"Inserted {len(param_result.data)} parameters")
        
        # Insert chart configs
        for chart in chart_configs:
            chart['template_id'] = template_id
        
        chart_result = client.table('template_chart_configs').insert(chart_configs).execute()
        logger.info(f"Inserted {len(chart_result.data)} chart configurations")
        
        logger.info("Successfully seeded Supergoop Branded Search Trends template!")
        
        # Display summary
        print("\n" + "="*60)
        print("TEMPLATE SEEDING COMPLETE")
        print("="*60)
        print(f"Template Name: {template_data['name']}")
        print(f"Template ID: {template_data['template_id']}")
        print(f"Category: {template_data['category']}")
        print(f"Parameters: {len(parameters)}")
        print(f"Chart Types: {len(chart_configs)}")
        print(f"Tags: {', '.join(template_data['tags'])}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error seeding templates: {e}")
        raise


if __name__ == "__main__":
    # Run the seeding script
    asyncio.run(seed_templates())