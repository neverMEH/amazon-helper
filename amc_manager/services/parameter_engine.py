"""
Parameter Engine for Query Flow Templates
Handles parameter validation, substitution, and SQL injection prevention
"""

import re
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta, date
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class ParameterValidationError(Exception):
    """Raised when parameter validation fails"""
    pass


class ParameterEngine:
    """Engine for processing and validating template parameters"""
    
    # Parameter type definitions with validation functions
    PARAMETER_TYPES = {
        'date': 'validate_date',
        'date_range': 'validate_date_range',
        'string': 'validate_string',
        'number': 'validate_number',
        'boolean': 'validate_boolean',
        'campaign_list': 'validate_campaign_list',
        'asin_list': 'validate_asin_list',
        'string_list': 'validate_string_list',
        'mapped_from_node': 'validate_mapped_from_node'
    }
    
    # SQL injection patterns to detect and prevent
    SQL_INJECTION_PATTERNS = [
        r';\s*(DROP|DELETE|TRUNCATE|UPDATE|INSERT|ALTER|CREATE)\s+',
        r'--\s*$',
        r'/\*.*\*/',
        r'UNION\s+SELECT',
        r'OR\s+1\s*=\s*1',
        r'AND\s+1\s*=\s*1',
        r"'\s*OR\s*'",
        r'EXEC\s*\(',
        r'EXECUTE\s*\(',
        r'xp_cmdshell',
        r'sp_executesql'
    ]
    
    def __init__(self):
        """Initialize the parameter engine"""
        self.validation_cache = {}
    
    def process_template(
        self,
        sql_template: str,
        parameters: List[Dict[str, Any]],
        parameter_values: Dict[str, Any]
    ) -> str:
        """
        Process a SQL template with parameter substitution
        
        Args:
            sql_template: SQL template with {{parameter}} placeholders
            parameters: List of parameter definitions from database
            parameter_values: User-provided parameter values
            
        Returns:
            Processed SQL with substituted parameters
            
        Raises:
            ParameterValidationError: If validation fails
        """
        # First validate all parameters
        validated_values = self.validate_parameters(parameters, parameter_values)
        
        # Then substitute in the template
        processed_sql = self.substitute_parameters(sql_template, validated_values)
        
        # Final SQL injection check
        self._check_sql_injection(processed_sql)
        
        return processed_sql
    
    def validate_parameters(
        self,
        parameter_definitions: List[Dict[str, Any]],
        parameter_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate parameter values against their definitions
        
        Args:
            parameter_definitions: List of parameter definitions
            parameter_values: User-provided values
            
        Returns:
            Validated and processed parameter values
            
        Raises:
            ParameterValidationError: If validation fails
        """
        validated = {}
        errors = []
        
        for param_def in parameter_definitions:
            param_name = param_def['parameter_name']
            param_type = param_def['parameter_type']
            required = param_def.get('required', False)
            default_value = param_def.get('default_value')
            validation_rules = param_def.get('validation_rules', {})
            
            # Get the value
            if param_name in parameter_values:
                value = parameter_values[param_name]
            elif default_value is not None:
                value = self._process_default_value(default_value, param_type)
            elif required:
                errors.append(f"Required parameter '{param_name}' is missing")
                continue
            else:
                continue
            
            # Validate based on type
            try:
                validator_method = getattr(self, f'validate_{param_type}')
                validated_value = validator_method(value, validation_rules)
                validated[param_name] = validated_value
            except AttributeError:
                errors.append(f"Unknown parameter type '{param_type}' for '{param_name}'")
            except Exception as e:
                errors.append(f"Validation failed for '{param_name}': {str(e)}")
        
        if errors:
            raise ParameterValidationError("\n".join(errors))
        
        return validated
    
    def substitute_parameters(
        self,
        sql_template: str,
        parameter_values: Dict[str, Any]
    ) -> str:
        """
        Substitute parameter placeholders in SQL template
        
        Args:
            sql_template: SQL with {{parameter}} placeholders
            parameter_values: Validated parameter values
            
        Returns:
            SQL with substituted values
        """
        def replace_parameter(match):
            param_name = match.group(1)
            if param_name not in parameter_values:
                # Leave placeholder as-is if parameter not provided
                return match.group(0)
            
            value = parameter_values[param_name]
            return self._format_sql_value(value)
        
        # Replace {{parameter_name}} with values
        pattern = r'\{\{(\w+)\}\}'
        processed_sql = re.sub(pattern, replace_parameter, sql_template)
        
        return processed_sql
    
    # Validation methods for each parameter type
    
    def validate_date(self, value: Union[str, date], rules: Dict[str, Any]) -> str:
        """Validate a date parameter"""
        # Parse the date
        if isinstance(value, str):
            try:
                date_obj = datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got '{value}'")
        elif isinstance(value, date):
            date_obj = value
        else:
            raise ValueError(f"Invalid date type: {type(value)}")
        
        # Check min/max constraints
        if 'min' in rules:
            min_date = datetime.strptime(rules['min'], '%Y-%m-%d').date()
            if date_obj < min_date:
                raise ValueError(f"Date {date_obj} is before minimum allowed date {min_date}")
        
        if 'max' in rules:
            max_date = datetime.strptime(rules['max'], '%Y-%m-%d').date()
            if date_obj > max_date:
                raise ValueError(f"Date {date_obj} is after maximum allowed date {max_date}")
        
        # Check if future dates are allowed
        if not rules.get('allow_future', True) and date_obj > datetime.now().date():
            raise ValueError(f"Future dates are not allowed")
        
        return date_obj.strftime('%Y-%m-%d')
    
    def validate_date_range(self, value: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, str]:
        """Validate a date range parameter"""
        if not isinstance(value, dict) or 'start' not in value or 'end' not in value:
            raise ValueError("Date range must have 'start' and 'end' fields")
        
        # Validate individual dates
        start_date = self.validate_date(value['start'], rules)
        end_date = self.validate_date(value['end'], rules)
        
        start_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Check range validity
        if end_obj < start_obj:
            raise ValueError(f"End date {end_date} is before start date {start_date}")
        
        # Check range constraints
        days_diff = (end_obj - start_obj).days
        
        if 'min_days' in rules and days_diff < rules['min_days']:
            raise ValueError(f"Date range must be at least {rules['min_days']} days")
        
        if 'max_days' in rules and days_diff > rules['max_days']:
            raise ValueError(f"Date range cannot exceed {rules['max_days']} days")
        
        return {'start': start_date, 'end': end_date}
    
    def validate_string(self, value: str, rules: Dict[str, Any]) -> str:
        """Validate a string parameter"""
        if not isinstance(value, str):
            value = str(value)
        
        # Check length constraints
        if 'min_length' in rules and len(value) < rules['min_length']:
            raise ValueError(f"String must be at least {rules['min_length']} characters")
        
        if 'max_length' in rules and len(value) > rules['max_length']:
            raise ValueError(f"String cannot exceed {rules['max_length']} characters")
        
        # Check pattern if specified
        if 'pattern' in rules:
            pattern = re.compile(rules['pattern'])
            if not pattern.match(value):
                raise ValueError(f"String does not match required pattern: {rules['pattern']}")
        
        # Check for SQL injection attempts
        self._check_string_injection(value)
        
        return value
    
    def validate_number(self, value: Union[int, float, str], rules: Dict[str, Any]) -> Union[int, float]:
        """Validate a number parameter"""
        try:
            # Convert to appropriate number type
            if rules.get('type') == 'integer':
                num_value = int(value)
            else:
                num_value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid number: {value}")
        
        # Check range constraints
        if 'min' in rules and num_value < rules['min']:
            raise ValueError(f"Number must be at least {rules['min']}")
        
        if 'max' in rules and num_value > rules['max']:
            raise ValueError(f"Number cannot exceed {rules['max']}")
        
        return num_value
    
    def validate_boolean(self, value: Union[bool, str, int], rules: Dict[str, Any]) -> bool:
        """Validate a boolean parameter"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            if value.lower() in ('true', 't', 'yes', 'y', '1'):
                return True
            elif value.lower() in ('false', 'f', 'no', 'n', '0'):
                return False
        
        if isinstance(value, int):
            return bool(value)
        
        raise ValueError(f"Invalid boolean value: {value}")
    
    def validate_campaign_list(self, value: List[str], rules: Dict[str, Any]) -> List[str]:
        """Validate a list of campaign IDs"""
        if not isinstance(value, list):
            raise ValueError("Campaign list must be an array")
        
        # Check count constraints
        if 'min_selections' in rules and len(value) < rules['min_selections']:
            raise ValueError(f"Must select at least {rules['min_selections']} campaigns")
        
        if 'max_selections' in rules and len(value) > rules['max_selections']:
            raise ValueError(f"Cannot select more than {rules['max_selections']} campaigns")
        
        # Validate each campaign ID
        validated = []
        for campaign_id in value:
            if not isinstance(campaign_id, str) or not campaign_id.strip():
                raise ValueError(f"Invalid campaign ID: {campaign_id}")
            
            # Check for injection attempts
            self._check_string_injection(campaign_id)
            validated.append(campaign_id.strip())
        
        return validated
    
    def validate_asin_list(self, value: List[str], rules: Dict[str, Any]) -> List[str]:
        """Validate a list of ASINs"""
        if not isinstance(value, list):
            raise ValueError("ASIN list must be an array")
        
        # Check count constraints
        if 'min_selections' in rules and len(value) < rules['min_selections']:
            raise ValueError(f"Must select at least {rules['min_selections']} ASINs")
        
        if 'max_selections' in rules and len(value) > rules['max_selections']:
            raise ValueError(f"Cannot select more than {rules['max_selections']} ASINs")
        
        # Validate each ASIN
        asin_pattern = re.compile(r'^B[0-9A-Z]{9}$')
        validated = []
        
        for asin in value:
            if not isinstance(asin, str):
                raise ValueError(f"Invalid ASIN type: {type(asin)}")
            
            asin = asin.strip().upper()
            
            if not asin_pattern.match(asin):
                raise ValueError(f"Invalid ASIN format: {asin}")
            
            validated.append(asin)
        
        return validated
    
    def validate_string_list(self, value: List[str], rules: Dict[str, Any]) -> List[str]:
        """Validate a list of strings"""
        if not isinstance(value, list):
            raise ValueError("String list must be an array")
        
        # Check count constraints
        if 'min_items' in rules and len(value) < rules['min_items']:
            raise ValueError(f"Must provide at least {rules['min_items']} items")
        
        if 'max_items' in rules and len(value) > rules['max_items']:
            raise ValueError(f"Cannot provide more than {rules['max_items']} items")
        
        # Validate each string
        validated = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"Invalid string item: {item}")
            
            # Check for injection attempts
            self._check_string_injection(item)
            validated.append(item.strip())
        
        return validated
    
    def validate_mapped_from_node(self, value: Any, rules: Dict[str, Any]) -> Any:
        """
        Validate mapped_from_node parameter type
        This is used in flow compositions to map values from upstream nodes
        
        Args:
            value: The value from the upstream node (already processed)
            rules: Validation rules (may include transform rules)
            
        Returns:
            Validated value (may be transformed based on rules)
        """
        # For mapped_from_node, the value comes from another node's output
        # so it's already been validated by that node's execution
        
        # Apply any transformations specified in rules
        transform = rules.get('transform', 'direct')
        
        if transform == 'direct':
            # Pass through as-is
            return value
        elif transform == 'to_array':
            # Convert single value to array
            if isinstance(value, list):
                return value
            return [value] if value is not None else []
        elif transform == 'to_string':
            # Convert to string
            return str(value) if value is not None else ''
        elif transform == 'to_number':
            # Convert to number
            try:
                return float(value)
            except (TypeError, ValueError):
                raise ValueError(f"Cannot convert {value} to number")
        elif transform == 'flatten':
            # Flatten nested arrays
            if isinstance(value, list):
                flattened = []
                for item in value:
                    if isinstance(item, list):
                        flattened.extend(item)
                    else:
                        flattened.append(item)
                return flattened
            return [value] if value is not None else []
        elif transform == 'distinct':
            # Get unique values
            if isinstance(value, list):
                return list(set(value))
            return [value] if value is not None else []
        elif transform == 'join':
            # Join array into string
            if isinstance(value, list):
                separator = rules.get('separator', ',')
                return separator.join(str(v) for v in value)
            return str(value) if value is not None else ''
        else:
            # Unknown transform, pass through
            logger.warning(f"Unknown transform type: {transform}")
            return value
    
    # Helper methods
    
    def _process_default_value(self, default_value: Any, param_type: str) -> Any:
        """Process default value based on parameter type"""
        if param_type == 'date_range' and isinstance(default_value, dict):
            # Handle preset date ranges
            if 'preset' in default_value:
                return self._get_preset_date_range(default_value['preset'])
        
        return default_value
    
    def _get_preset_date_range(self, preset: str) -> Dict[str, str]:
        """Get date range for preset values"""
        today = datetime.now().date()
        
        presets = {
            'last_7_days': {
                'start': (today - timedelta(days=7)).strftime('%Y-%m-%d'),
                'end': today.strftime('%Y-%m-%d')
            },
            'last_30_days': {
                'start': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
                'end': today.strftime('%Y-%m-%d')
            },
            'last_90_days': {
                'start': (today - timedelta(days=90)).strftime('%Y-%m-%d'),
                'end': today.strftime('%Y-%m-%d')
            },
            'last_365_days': {
                'start': (today - timedelta(days=365)).strftime('%Y-%m-%d'),
                'end': today.strftime('%Y-%m-%d')
            },
            'this_month': {
                'start': today.replace(day=1).strftime('%Y-%m-%d'),
                'end': today.strftime('%Y-%m-%d')
            },
            'last_month': {
                'start': (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d'),
                'end': (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
            }
        }
        
        return presets.get(preset, presets['last_30_days'])
    
    def _format_sql_value(self, value: Any) -> str:
        """Format a value for SQL substitution"""
        if value is None:
            return 'NULL'
        
        if isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        
        if isinstance(value, (int, float)):
            return str(value)
        
        if isinstance(value, str):
            # For regex patterns, don't escape
            if self._is_regex_pattern(value):
                return f"'{value}'"
            # Regular string - escape quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        
        if isinstance(value, list):
            # Format for IN clause
            if not value:
                return "('')"  # Empty list placeholder
            formatted_items = [self._format_sql_value(item) for item in value]
            return f"({', '.join(formatted_items)})"
        
        if isinstance(value, dict):
            # Handle date ranges
            if 'start' in value and 'end' in value:
                # Return as separate values for the template to use
                # The template should handle these appropriately
                return json.dumps(value)
        
        # Default: convert to string and escape
        return self._format_sql_value(str(value))
    
    def _is_regex_pattern(self, value: str) -> bool:
        """Check if a string looks like a regex pattern"""
        regex_indicators = ['(?i)', '.*', '.+', '^', '$', '\\d', '\\w', '\\s', '[', ']']
        return any(indicator in value for indicator in regex_indicators)
    
    def _check_string_injection(self, value: str) -> None:
        """Check a string for SQL injection attempts"""
        upper_value = value.upper()
        
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, upper_value, re.IGNORECASE):
                raise ParameterValidationError(f"Potential SQL injection detected in value: {value}")
    
    def _check_sql_injection(self, sql: str) -> None:
        """Final check for SQL injection in processed SQL"""
        # This is a final safety check after substitution
        # In production, you'd want more sophisticated checks
        
        # Count semicolons (multiple statements)
        semicolon_count = sql.count(';')
        if semicolon_count > 5:  # Arbitrary threshold
            logger.warning(f"Multiple semicolons detected in SQL ({semicolon_count})")
        
        # Check for dangerous keywords in comments
        if '--' in sql or '/*' in sql:
            logger.warning("SQL comments detected in processed query")
        
        # Log the query for audit
        logger.debug(f"Processed SQL length: {len(sql)} characters")