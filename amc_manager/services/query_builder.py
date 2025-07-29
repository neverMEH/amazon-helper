"""AMC SQL Query Builder with templates and YAML parameter support"""

import yaml
import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum

from ..core import get_logger
from ..core.exceptions import ValidationError, AMCQueryError


logger = get_logger(__name__)


class QueryTemplate(Enum):
    """Pre-defined query templates"""
    PATH_TO_CONVERSION = "path_to_conversion"
    NEW_TO_BRAND = "new_to_brand"
    CART_ABANDONMENT = "cart_abandonment"
    ATTRIBUTION_COMPARISON = "attribution_comparison"
    SEARCH_TERM_ANALYSIS = "search_term_analysis"
    CROSS_CHANNEL = "cross_channel"
    AUDIENCE_OVERLAP = "audience_overlap"
    FREQUENCY_ANALYSIS = "frequency_analysis"


class AMCQueryBuilder:
    """Builder for creating AMC SQL queries with templates and parameters"""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.saved_queries = {}
        
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load pre-defined query templates"""
        return {
            QueryTemplate.PATH_TO_CONVERSION.value: {
                'name': 'Path to Conversion Analysis',
                'description': 'Analyze customer journey and touchpoints leading to conversion',
                'sql_template': """
                WITH conversion_paths AS (
                    SELECT
                        user_id,
                        conversion_event_dt,
                        ARRAY_AGG(
                            STRUCT(
                                impression_dt,
                                campaign,
                                ad_product_type
                            ) ORDER BY impression_dt
                        ) AS touchpoints
                    FROM (
                        SELECT DISTINCT
                            c.user_id,
                            c.conversion_event_dt,
                            i.impression_dt,
                            i.campaign,
                            i.ad_product_type
                        FROM amazon_attributed_events_by_conversion_time c
                        INNER JOIN (
                            SELECT user_id, impression_dt, campaign, ad_product_type
                            FROM amazon_ads_impressions
                            WHERE campaign IN ({{campaign_list}})
                                AND impression_dt >= '{{start_date}}'
                                AND impression_dt <= '{{end_date}}'
                        ) i ON c.user_id = i.user_id
                        WHERE c.conversion_event_dt >= '{{start_date}}'
                            AND c.conversion_event_dt <= '{{end_date}}'
                            AND i.impression_dt <= c.conversion_event_dt
                    )
                    GROUP BY user_id, conversion_event_dt
                )
                SELECT
                    CARDINALITY(touchpoints) AS path_length,
                    touchpoints[1].ad_product_type AS first_touch,
                    touchpoints[CARDINALITY(touchpoints)].ad_product_type AS last_touch,
                    COUNT(DISTINCT user_id) AS unique_converters,
                    COUNT(*) AS total_conversions
                FROM conversion_paths
                GROUP BY 1, 2, 3
                ORDER BY total_conversions DESC
                """,
                'parameters': {
                    'campaign_list': {'type': 'list', 'required': True, 'description': 'List of campaign names'},
                    'start_date': {'type': 'date', 'required': True, 'description': 'Start date (YYYY-MM-DD)'},
                    'end_date': {'type': 'date', 'required': True, 'description': 'End date (YYYY-MM-DD)'}
                }
            },
            
            QueryTemplate.NEW_TO_BRAND.value: {
                'name': 'New-to-Brand Analysis',
                'description': 'Identify customers who are new to the brand within the last 365 days',
                'sql_template': """
                WITH new_to_brand_users AS (
                    SELECT DISTINCT
                        c.user_id,
                        c.conversion_event_dt,
                        c.order_id,
                        c.asin,
                        CASE 
                            WHEN COUNT(p.order_id) = 0 THEN TRUE
                            ELSE FALSE
                        END AS is_new_to_brand
                    FROM amazon_attributed_events_by_conversion_time c
                    LEFT JOIN (
                        SELECT user_id, order_id, conversion_event_dt
                        FROM amazon_attributed_events_by_conversion_time
                        WHERE conversion_event_dt < DATE_ADD('day', -365, CURRENT_DATE)
                            AND brand = '{{brand_name}}'
                    ) p ON c.user_id = p.user_id
                    WHERE c.conversion_event_dt >= '{{start_date}}'
                        AND c.conversion_event_dt <= '{{end_date}}'
                        AND c.brand = '{{brand_name}}'
                    GROUP BY c.user_id, c.conversion_event_dt, c.order_id, c.asin
                )
                SELECT
                    DATE_TRUNC('{{aggregation_level}}', conversion_event_dt) AS period,
                    COUNT(DISTINCT CASE WHEN is_new_to_brand THEN user_id END) AS new_to_brand_customers,
                    COUNT(DISTINCT user_id) AS total_customers,
                    CAST(COUNT(DISTINCT CASE WHEN is_new_to_brand THEN user_id END) AS DOUBLE) / 
                        NULLIF(COUNT(DISTINCT user_id), 0) * 100 AS ntb_percentage,
                    SUM(CASE WHEN is_new_to_brand THEN 1 ELSE 0 END) AS ntb_orders,
                    COUNT(*) AS total_orders
                FROM new_to_brand_users
                GROUP BY 1
                ORDER BY 1
                """,
                'parameters': {
                    'brand_name': {'type': 'string', 'required': True, 'description': 'Brand name'},
                    'start_date': {'type': 'date', 'required': True, 'description': 'Start date (YYYY-MM-DD)'},
                    'end_date': {'type': 'date', 'required': True, 'description': 'End date (YYYY-MM-DD)'},
                    'aggregation_level': {'type': 'enum', 'required': False, 'default': 'day', 
                                         'values': ['day', 'week', 'month'], 'description': 'Time aggregation level'}
                }
            },
            
            QueryTemplate.CART_ABANDONMENT.value: {
                'name': 'Cart Abandonment Analysis',
                'description': 'Find users who added items to cart but did not purchase',
                'sql_template': """
                WITH cart_events AS (
                    SELECT DISTINCT
                        user_id,
                        asin,
                        add_to_cart_event_dt,
                        DATE_ADD('day', {{attribution_window}}, add_to_cart_event_dt) AS attribution_end
                    FROM amazon_ads_add_to_cart
                    WHERE add_to_cart_event_dt >= '{{start_date}}'
                        AND add_to_cart_event_dt <= '{{end_date}}'
                        AND asin IN ({{asin_list}})
                ),
                purchases AS (
                    SELECT DISTINCT
                        user_id,
                        asin,
                        conversion_event_dt
                    FROM amazon_attributed_events_by_conversion_time
                    WHERE conversion_event_dt >= '{{start_date}}'
                        AND conversion_event_dt <= DATE_ADD('day', {{attribution_window}}, '{{end_date}}')
                )
                SELECT
                    ce.asin,
                    COUNT(DISTINCT ce.user_id) AS users_added_to_cart,
                    COUNT(DISTINCT p.user_id) AS users_purchased,
                    COUNT(DISTINCT ce.user_id) - COUNT(DISTINCT p.user_id) AS cart_abandoners,
                    CAST(COUNT(DISTINCT p.user_id) AS DOUBLE) / 
                        NULLIF(COUNT(DISTINCT ce.user_id), 0) * 100 AS conversion_rate
                FROM cart_events ce
                LEFT JOIN purchases p
                    ON ce.user_id = p.user_id
                    AND ce.asin = p.asin
                    AND p.conversion_event_dt >= ce.add_to_cart_event_dt
                    AND p.conversion_event_dt <= ce.attribution_end
                GROUP BY ce.asin
                ORDER BY users_added_to_cart DESC
                """,
                'parameters': {
                    'asin_list': {'type': 'list', 'required': True, 'description': 'List of ASINs to analyze'},
                    'start_date': {'type': 'date', 'required': True, 'description': 'Start date (YYYY-MM-DD)'},
                    'end_date': {'type': 'date', 'required': True, 'description': 'End date (YYYY-MM-DD)'},
                    'attribution_window': {'type': 'integer', 'required': False, 'default': 14, 
                                         'description': 'Attribution window in days'}
                }
            },
            
            QueryTemplate.CROSS_CHANNEL.value: {
                'name': 'Cross-Channel Performance',
                'description': 'Analyze performance across DSP and Sponsored Ads channels',
                'sql_template': """
                SELECT
                    ad_product_type,
                    campaign_type,
                    COUNT(DISTINCT user_id) AS unique_users,
                    SUM(impressions) AS total_impressions,
                    SUM(clicks) AS total_clicks,
                    SUM(conversions_within_{{attribution_days}}_days) AS conversions,
                    SUM(total_cost) AS spend,
                    CAST(SUM(clicks) AS DOUBLE) / NULLIF(SUM(impressions), 0) * 100 AS ctr,
                    CAST(SUM(conversions_within_{{attribution_days}}_days) AS DOUBLE) / 
                        NULLIF(SUM(clicks), 0) * 100 AS conversion_rate,
                    SUM(total_cost) / NULLIF(SUM(conversions_within_{{attribution_days}}_days), 0) AS cpa
                FROM (
                    SELECT
                        ad_product_type,
                        CASE 
                            WHEN ad_product_type = 'dsp' THEN 'DSP'
                            WHEN ad_product_type LIKE 'sponsored%' THEN 'Sponsored Ads'
                            ELSE 'Other'
                        END AS campaign_type,
                        user_id,
                        COUNT(*) AS impressions,
                        SUM(CASE WHEN is_click_through THEN 1 ELSE 0 END) AS clicks,
                        MAX(conversions_within_{{attribution_days}}_days) AS conversions_within_{{attribution_days}}_days,
                        SUM(total_cost) AS total_cost
                    FROM unified_ad_events
                    WHERE event_dt >= '{{start_date}}'
                        AND event_dt <= '{{end_date}}'
                    GROUP BY ad_product_type, campaign_type, user_id
                )
                GROUP BY ad_product_type, campaign_type
                ORDER BY conversions DESC
                """,
                'parameters': {
                    'start_date': {'type': 'date', 'required': True, 'description': 'Start date (YYYY-MM-DD)'},
                    'end_date': {'type': 'date', 'required': True, 'description': 'End date (YYYY-MM-DD)'},
                    'attribution_days': {'type': 'integer', 'required': False, 'default': 14, 
                                       'description': 'Attribution window in days'}
                }
            }
        }
        
    def build_from_template(
        self,
        template_name: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Build SQL query from template with parameters
        
        Args:
            template_name: Name of the template to use
            parameters: Parameter values for the template
            
        Returns:
            Generated SQL query
        """
        if template_name not in self.templates:
            raise ValidationError(f"Unknown template: {template_name}")
            
        template = self.templates[template_name]
        sql_template = template['sql_template']
        
        # Validate required parameters
        self._validate_template_parameters(template, parameters)
        
        # Apply default values
        params = self._apply_defaults(template, parameters)
        
        # Process parameters
        processed_params = self._process_parameters(params)
        
        # Replace placeholders in template
        sql = self._replace_placeholders(sql_template, processed_params)
        
        logger.info(f"Built query from template '{template_name}'")
        return sql
        
    def build_custom_query(
        self,
        base_query: str,
        parameters: Optional[Dict[str, Any]] = None,
        yaml_config: Optional[str] = None
    ) -> str:
        """
        Build custom query with optional YAML configuration
        
        Args:
            base_query: Base SQL query with placeholders
            parameters: Direct parameter values
            yaml_config: YAML configuration string
            
        Returns:
            Generated SQL query
        """
        # Parse YAML config if provided
        if yaml_config:
            yaml_params = yaml.safe_load(yaml_config)
            parameters = {**(parameters or {}), **yaml_params}
            
        if not parameters:
            return base_query
            
        # Process parameters
        processed_params = self._process_parameters(parameters)
        
        # Replace placeholders
        sql = self._replace_placeholders(base_query, processed_params)
        
        logger.info("Built custom query with parameters")
        return sql
        
    def validate_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Validate AMC SQL query syntax and structure
        
        Args:
            sql_query: SQL query to validate
            
        Returns:
            Validation results with any warnings or errors
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        sql_lower = sql_query.lower().strip()
        
        # Basic structure validation
        if not sql_lower.startswith('select') and not sql_lower.startswith('with'):
            results['valid'] = False
            results['errors'].append("Query must start with SELECT or WITH")
            
        if 'from' not in sql_lower:
            results['valid'] = False
            results['errors'].append("Query must include a FROM clause")
            
        # Check for AMC-specific tables
        amc_tables = [
            'amazon_ads_impressions',
            'amazon_ads_clicks',
            'amazon_attributed_events_by_conversion_time',
            'amazon_ads_add_to_cart',
            'unified_ad_events'
        ]
        
        has_amc_table = any(table in sql_lower for table in amc_tables)
        if not has_amc_table:
            results['warnings'].append("Query doesn't reference any standard AMC tables")
            
        # Check for common issues
        if 'campaign_id' in sql_lower:
            results['warnings'].append(
                "AMC doesn't provide campaign IDs for Sponsored Ads. Use campaign name instead."
            )
            
        if re.search(r'date[_\s]+add|date[_\s]+sub', sql_lower):
            results['suggestions'].append(
                "Consider using AMC's dynamic date functions for scheduled queries"
            )
            
        # Check for optimization opportunities
        if 'select *' in sql_lower:
            results['warnings'].append(
                "Avoid SELECT * for better performance. Specify only needed columns."
            )
            
        logger.info(f"Validated query: {results['valid']}")
        return results
        
    def save_query_template(
        self,
        name: str,
        query: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Save a query as a reusable template
        
        Args:
            name: Template name
            query: SQL query
            description: Template description
            parameters: Parameter definitions
            tags: Optional tags for categorization
            
        Returns:
            Saved template information
        """
        template = {
            'name': name,
            'query': query,
            'description': description,
            'parameters': parameters or {},
            'tags': tags or [],
            'created_at': datetime.utcnow().isoformat(),
            'version': 1
        }
        
        # Validate the query
        validation = self.validate_query(query)
        if not validation['valid']:
            raise AMCQueryError(f"Invalid query: {validation['errors']}")
            
        self.saved_queries[name] = template
        logger.info(f"Saved query template: {name}")
        
        return template
        
    def _validate_template_parameters(
        self,
        template: Dict[str, Any],
        parameters: Dict[str, Any]
    ):
        """Validate parameters against template requirements"""
        template_params = template.get('parameters', {})
        
        for param_name, param_config in template_params.items():
            if param_config.get('required', False) and param_name not in parameters:
                raise ValidationError(f"Required parameter missing: {param_name}")
                
            if param_name in parameters and 'type' in param_config:
                self._validate_parameter_type(
                    param_name,
                    parameters[param_name],
                    param_config['type']
                )
                
    def _validate_parameter_type(self, name: str, value: Any, expected_type: str):
        """Validate parameter type"""
        type_validators = {
            'string': lambda v: isinstance(v, str),
            'integer': lambda v: isinstance(v, int),
            'date': lambda v: self._is_valid_date(v),
            'list': lambda v: isinstance(v, list),
            'enum': lambda v: True  # Enum validation handled separately
        }
        
        validator = type_validators.get(expected_type)
        if validator and not validator(value):
            raise ValidationError(
                f"Parameter '{name}' must be of type {expected_type}"
            )
            
    def _is_valid_date(self, value: str) -> bool:
        """Check if value is a valid date string"""
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            return False
            
    def _apply_defaults(
        self,
        template: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply default values for missing parameters"""
        result = parameters.copy()
        
        for param_name, param_config in template.get('parameters', {}).items():
            if param_name not in result and 'default' in param_config:
                result[param_name] = param_config['default']
                
        return result
        
    def _process_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process parameters for SQL insertion"""
        processed = {}
        
        for key, value in parameters.items():
            if isinstance(value, list):
                # Convert list to SQL format: 'item1', 'item2', ...
                processed[key] = ', '.join(f"'{v}'" for v in value)
            elif isinstance(value, datetime):
                processed[key] = value.strftime('%Y-%m-%d')
            else:
                processed[key] = value
                
        return processed
        
    def _replace_placeholders(self, template: str, parameters: Dict[str, Any]) -> str:
        """Replace template placeholders with parameter values"""
        result = template
        
        for key, value in parameters.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
            
        # Check for any remaining placeholders
        remaining = re.findall(r'{{(\w+)}}', result)
        if remaining:
            logger.warning(f"Unresolved placeholders in query: {remaining}")
            
        return result