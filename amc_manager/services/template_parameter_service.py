"""Template Parameter Management Service"""

from typing import List, Dict, Any, Optional, Set
import re
import json
from datetime import datetime

from ..core.logger_simple import get_logger
from .db_service import DatabaseService, with_connection_retry
from .parameter_detection_service import ParameterDetectionService

logger = get_logger(__name__)


class TemplateParameterService(DatabaseService):
    """Service for managing query template parameters"""
    
    def __init__(self):
        """Initialize the template parameter service"""
        super().__init__()
        self.detection_service = ParameterDetectionService()
        
        # Extended parameter types for query library
        self.PARAMETER_TYPES = {
            'date': 'Date selector',
            'date_range': 'Date range picker',
            'date_expression': 'Dynamic date expression (last_7_days, this_month, etc.)',
            'string': 'Text input',
            'number': 'Numeric input',
            'boolean': 'Boolean toggle',
            'campaign_list': 'Campaign multi-select',
            'campaign_filter': 'Campaign pattern filter (wildcards)',
            'asin_list': 'ASIN multi-select with bulk paste',
            'string_list': 'String list input',
            'threshold_numeric': 'Numeric threshold with min/max',
            'percentage': 'Percentage input (0-100)',
            'enum_select': 'Single/multi select from options',
            'mapped_from_node': 'Mapped from workflow node'
        }
    
    @with_connection_retry
    def create_parameter(self, parameter_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new template parameter"""
        try:
            # Validate parameter type
            if parameter_data.get('parameter_type') not in self.PARAMETER_TYPES:
                logger.error(f"Invalid parameter type: {parameter_data.get('parameter_type')}")
                return None
            
            response = self.client.table('query_template_parameters').insert(parameter_data).execute()
            
            if response.data:
                logger.info(f"Created parameter {parameter_data['parameter_name']} for template {parameter_data['template_id']}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating template parameter: {e}")
            return None
    
    @with_connection_retry
    def get_template_parameters(self, template_id: str) -> List[Dict[str, Any]]:
        """Get all parameters for a template"""
        try:
            response = self.client.table('query_template_parameters')\
                .select('*')\
                .eq('template_id', template_id)\
                .order('display_order', desc=False)\
                .execute()
            
            parameters = response.data or []
            logger.info(f"Retrieved {len(parameters)} parameters for template {template_id}")
            return parameters
        except Exception as e:
            logger.error(f"Error getting template parameters: {e}")
            return []
    
    @with_connection_retry
    def update_parameter(self, parameter_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a template parameter"""
        try:
            # Don't allow changing parameter_type after creation
            if 'parameter_type' in updates:
                del updates['parameter_type']
            
            response = self.client.table('query_template_parameters')\
                .update(updates)\
                .eq('id', parameter_id)\
                .execute()
            
            if response.data:
                logger.info(f"Updated parameter {parameter_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating parameter {parameter_id}: {e}")
            return None
    
    @with_connection_retry
    def delete_parameter(self, parameter_id: str) -> bool:
        """Delete a template parameter"""
        try:
            response = self.client.table('query_template_parameters')\
                .delete()\
                .eq('id', parameter_id)\
                .execute()
            
            logger.info(f"Deleted parameter {parameter_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting parameter {parameter_id}: {e}")
            return False
    
    @with_connection_retry
    def bulk_create_parameters(self, template_id: str, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple parameters at once"""
        try:
            # Add template_id to each parameter
            for param in parameters:
                param['template_id'] = template_id
                # Validate parameter type
                if param.get('parameter_type') not in self.PARAMETER_TYPES:
                    logger.warning(f"Skipping invalid parameter type: {param.get('parameter_type')}")
                    continue
            
            # Filter valid parameters
            valid_params = [p for p in parameters if p.get('parameter_type') in self.PARAMETER_TYPES]
            
            if not valid_params:
                logger.warning("No valid parameters to create")
                return []
            
            response = self.client.table('query_template_parameters').insert(valid_params).execute()
            
            if response.data:
                logger.info(f"Created {len(response.data)} parameters for template {template_id}")
                return response.data
            return []
        except Exception as e:
            logger.error(f"Error bulk creating parameters: {e}")
            return []
    
    def detect_parameters_from_sql(self, sql_template: str) -> Dict[str, Dict[str, Any]]:
        """Detect parameters from SQL template and infer types"""
        try:
            # Find all {{parameter}} placeholders
            pattern = r'\{\{(\w+)\}\}'
            matches = re.findall(pattern, sql_template)
            
            if not matches:
                return {}
            
            # Use existing parameter detection service for type inference
            detected = {}
            for param_name in set(matches):
                # Infer type based on naming patterns
                param_type = self._infer_parameter_type(param_name, sql_template)
                
                detected[param_name] = {
                    'parameter_name': param_name,
                    'parameter_type': param_type,
                    'display_name': self._format_display_name(param_name),
                    'required': True,
                    'display_order': len(detected) + 1
                }
            
            # Use detection service for campaign type classification if applicable
            if any(p['parameter_type'] in ['campaign_list', 'campaign_filter'] for p in detected.values()):
                campaign_types = self.detection_service.detect_campaign_types_from_sql(sql_template)
                for param_name, param_info in detected.items():
                    if param_info['parameter_type'] in ['campaign_list', 'campaign_filter']:
                        param_info['validation_rules'] = {'campaign_types': campaign_types}
            
            return detected
        except Exception as e:
            logger.error(f"Error detecting parameters from SQL: {e}")
            return {}
    
    def _infer_parameter_type(self, param_name: str, sql_context: str) -> str:
        """Infer parameter type from name and SQL context"""
        param_lower = param_name.lower()
        
        # Check for specific patterns
        if 'date' in param_lower:
            if 'start' in param_lower or 'end' in param_lower or 'range' in param_lower:
                return 'date_range'
            elif 'expression' in param_lower or 'period' in param_lower:
                return 'date_expression'
            else:
                return 'date'
        
        if 'asin' in param_lower:
            return 'asin_list'
        
        if 'campaign' in param_lower:
            if 'filter' in param_lower or 'pattern' in param_lower:
                return 'campaign_filter'
            else:
                return 'campaign_list'
        
        if 'threshold' in param_lower or 'limit' in param_lower:
            return 'threshold_numeric'
        
        if 'percent' in param_lower or 'rate' in param_lower:
            return 'percentage'
        
        if param_lower in ['enabled', 'active', 'include', 'exclude']:
            return 'boolean'
        
        if 'count' in param_lower or 'number' in param_lower or 'qty' in param_lower:
            return 'number'
        
        if 'list' in param_lower:
            return 'string_list'
        
        # Check SQL context for additional hints
        if f"IN ({{{{{param_name}}}}}" in sql_context:
            if 'asin' in sql_context.lower():
                return 'asin_list'
            elif 'campaign' in sql_context.lower():
                return 'campaign_list'
            else:
                return 'string_list'
        
        # Default to string
        return 'string'
    
    def _format_display_name(self, param_name: str) -> str:
        """Format parameter name for display"""
        # Convert snake_case to Title Case
        words = param_name.replace('_', ' ').split()
        return ' '.join(word.capitalize() for word in words)
    
    def validate_parameter_value(self, param_def: Dict[str, Any], value: Any) -> bool:
        """Validate a parameter value against its definition"""
        try:
            param_type = param_def.get('parameter_type')
            required = param_def.get('required', False)
            validation_rules = param_def.get('validation_rules', {})
            
            # Check required
            if required and (value is None or value == '' or (isinstance(value, list) and len(value) == 0)):
                return False
            
            # Skip validation if not required and value is empty
            if not required and (value is None or value == ''):
                return True
            
            # Type-specific validation
            if param_type == 'asin_list':
                if not isinstance(value, list):
                    return False
                min_items = validation_rules.get('minItems', 0)
                max_items = validation_rules.get('maxItems', 1000)
                if len(value) < min_items or len(value) > max_items:
                    return False
                # Validate ASIN format
                asin_pattern = r'^[A-Z0-9]{10}$'
                return all(re.match(asin_pattern, str(asin)) for asin in value)
            
            elif param_type == 'campaign_filter':
                if not isinstance(value, str):
                    return False
                # Check for SQL injection attempts
                dangerous_patterns = ['--', ';', 'DROP', 'DELETE', 'TRUNCATE', 'UPDATE', 'INSERT']
                return not any(pattern in value.upper() for pattern in dangerous_patterns)
            
            elif param_type == 'threshold_numeric':
                if not isinstance(value, (int, float)):
                    return False
                min_val = validation_rules.get('min', float('-inf'))
                max_val = validation_rules.get('max', float('inf'))
                return min_val <= value <= max_val
            
            elif param_type == 'percentage':
                if not isinstance(value, (int, float)):
                    return False
                return 0 <= value <= 100
            
            elif param_type == 'enum_select':
                options = validation_rules.get('options', [])
                if validation_rules.get('multiple', False):
                    if not isinstance(value, list):
                        return False
                    return all(v in options for v in value)
                else:
                    return value in options
            
            elif param_type == 'date_expression':
                valid_expressions = [
                    'today', 'yesterday', 
                    'last_7_days', 'last_14_days', 'last_30_days', 'last_90_days',
                    'this_week', 'last_week',
                    'this_month', 'last_month',
                    'this_quarter', 'last_quarter',
                    'this_year', 'last_year'
                ]
                return value in valid_expressions
            
            # For other types, assume valid if we got this far
            return True
            
        except Exception as e:
            logger.error(f"Error validating parameter value: {e}")
            return False
    
    @with_connection_retry
    def get_parameter_groups(self, template_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get parameters organized by groups"""
        try:
            parameters = self.get_template_parameters(template_id)
            
            # Group parameters
            groups = {}
            ungrouped = []
            
            for param in parameters:
                group_name = param.get('group_name')
                if group_name:
                    if group_name not in groups:
                        groups[group_name] = []
                    groups[group_name].append(param)
                else:
                    ungrouped.append(param)
            
            # Add ungrouped parameters if any
            if ungrouped:
                groups['General'] = ungrouped
            
            return groups
        except Exception as e:
            logger.error(f"Error getting parameter groups: {e}")
            return {}
    
    @with_connection_retry
    def reorder_parameters(self, template_id: str, parameter_order: List[str]) -> bool:
        """Reorder parameters for a template"""
        try:
            # Update display_order for each parameter
            for index, param_id in enumerate(parameter_order):
                self.client.table('query_template_parameters')\
                    .update({'display_order': index + 1})\
                    .eq('id', param_id)\
                    .eq('template_id', template_id)\
                    .execute()
            
            logger.info(f"Reordered parameters for template {template_id}")
            return True
        except Exception as e:
            logger.error(f"Error reordering parameters: {e}")
            return False
    
    def get_ui_config_for_type(self, parameter_type: str) -> Dict[str, Any]:
        """Get default UI configuration for a parameter type"""
        ui_configs = {
            'date': {
                'component': 'DatePicker',
                'format': 'YYYY-MM-DD'
            },
            'date_range': {
                'component': 'DateRangePicker',
                'format': 'YYYY-MM-DD',
                'presets': True
            },
            'date_expression': {
                'component': 'DateExpressionSelect',
                'showPreview': True
            },
            'string': {
                'component': 'TextInput',
                'placeholder': 'Enter value...'
            },
            'number': {
                'component': 'NumberInput',
                'step': 1
            },
            'boolean': {
                'component': 'Switch',
                'labelOn': 'Yes',
                'labelOff': 'No'
            },
            'campaign_list': {
                'component': 'CampaignMultiSelect',
                'searchable': True,
                'showTypes': True
            },
            'campaign_filter': {
                'component': 'CampaignFilterInput',
                'wildcardHelp': True,
                'showPreview': True
            },
            'asin_list': {
                'component': 'AsinMultiSelect',
                'bulkPaste': True,
                'maxItems': 1000,
                'showCount': True
            },
            'string_list': {
                'component': 'TagInput',
                'delimiter': ','
            },
            'threshold_numeric': {
                'component': 'ThresholdInput',
                'showSlider': True
            },
            'percentage': {
                'component': 'PercentageInput',
                'showSlider': True,
                'suffix': '%'
            },
            'enum_select': {
                'component': 'SelectDropdown',
                'searchable': False
            },
            'mapped_from_node': {
                'component': 'NodeMapper',
                'readonly': True
            }
        }
        
        return ui_configs.get(parameter_type, {'component': 'TextInput'})


# Create singleton instance
template_parameter_service = TemplateParameterService()