"""
Shared parameter processing utility for AMC SQL queries
Handles parameter substitution, LIKE pattern detection, and array formatting
"""
import re
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ParameterProcessor:
    """
    Unified parameter processing for AMC SQL queries
    Ensures consistent handling between frontend preview and backend execution
    """

    # Dangerous SQL keywords to check for injection prevention
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE FROM', 'INSERT INTO', 'UPDATE', 'ALTER',
        'CREATE', 'EXEC', 'EXECUTE', 'TRUNCATE', 'GRANT', 'REVOKE'
    ]

    # Parameter patterns we need to identify
    PARAM_PATTERNS = {
        'mustache': r'\{\{(\w+)\}\}',      # {{parameter}}
        'colon': r':(\w+)\b',              # :parameter
        'dollar': r'\$(\w+)\b'             # $parameter
    }

    # Keywords that indicate campaign or ASIN parameters
    CAMPAIGN_KEYWORDS = [
        'campaign', 'campaign_id', 'campaign_name', 'campaigns',
        'campaign_ids', 'campaign_list', 'campaign_brand'
    ]

    ASIN_KEYWORDS = [
        'asin', 'product_asin', 'parent_asin', 'child_asin', 'asins',
        'asin_list', 'tracked_asins', 'target_asins', 'promoted_asins',
        'competitor_asins', 'purchased_asins', 'viewed_asins'
    ]

    @classmethod
    def process_sql_parameters(cls, sql_template: str, parameters: Dict[str, Any],
                             validate_all: bool = True) -> str:
        """
        Process SQL template with parameter substitution

        Args:
            sql_template: SQL query with parameter placeholders
            parameters: Parameter values to substitute
            validate_all: If True, validate all required params are present.
                         If False, only substitute provided params (useful for partial processing)

        Returns:
            SQL query with substituted values

        Raises:
            ValueError: If required parameters are missing (when validate_all=True) or dangerous SQL detected
        """
        # Find all required parameters
        required_params = cls._find_required_parameters(sql_template)

        # Validate required parameters are present (only if validate_all is True)
        if validate_all:
            cls._validate_parameters(required_params, parameters)

        # Substitute parameters
        query = cls._substitute_parameters(sql_template, parameters)

        logger.debug(f"Processed SQL query: {query[:500]}...")
        return query

    @classmethod
    def _find_required_parameters(cls, sql_template: str) -> List[str]:
        """Extract all parameter names from SQL template"""
        required_params = set()

        for pattern_name, pattern in cls.PARAM_PATTERNS.items():
            matches = re.findall(pattern, sql_template)
            required_params.update(matches)

        return list(required_params)

    @classmethod
    def _validate_parameters(cls, required_params: List[str], provided_params: Dict[str, Any]):
        """Validate that all required parameters are provided"""
        missing_params = [p for p in required_params if p not in provided_params]

        if missing_params:
            logger.error(f"Missing required parameters: {', '.join(missing_params)}")
            logger.error(f"Available parameters: {list(provided_params.keys())}")
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

    @classmethod
    def _substitute_parameters(cls, sql_template: str, parameters: Dict[str, Any]) -> str:
        """Substitute all parameters in SQL template"""
        query = sql_template

        for param_name, value in parameters.items():
            # Format the value based on its type and context
            formatted_value = cls._format_parameter_value(
                param_name, value, sql_template
            )

            # Replace all parameter formats
            query = cls._replace_parameter_formats(query, param_name, formatted_value)

        return query

    @classmethod
    def _format_parameter_value(cls, param_name: str, value: Any, sql_template: str) -> str:
        """
        Format parameter value based on type and context

        Handles:
        - Arrays/lists: Format as SQL IN clause ('item1','item2')
        - Strings in LIKE context: Add wildcards %value%
        - Regular strings: Escape and quote
        - Numbers/booleans: Convert to string
        """
        if isinstance(value, (list, tuple)):
            return cls._format_array_parameter(param_name, value)
        elif isinstance(value, str):
            return cls._format_string_parameter(param_name, value, sql_template)
        elif isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        else:
            # Numbers and other types
            return str(value)

    @classmethod
    def _format_array_parameter(cls, param_name: str, values: List[Any]) -> str:
        """Format array parameter as SQL IN clause"""
        escaped_values = []

        for val in values:
            if isinstance(val, str):
                # Escape single quotes and check for injection
                escaped_val = cls._escape_string_value(val, param_name)
                escaped_values.append(f"'{escaped_val}'")
            else:
                escaped_values.append(str(val))

        # Return formatted as SQL array
        return "({})".format(','.join(escaped_values))

    @classmethod
    def _format_string_parameter(cls, param_name: str, value: str, sql_template: str) -> str:
        """Format string parameter with proper escaping and wildcard detection"""
        # Escape the value first
        escaped_value = cls._escape_string_value(value, param_name)

        # Check if this parameter is used in a LIKE context
        if cls._is_like_parameter(param_name, sql_template):
            # Add wildcards for LIKE pattern matching
            logger.info(f"✓ Parameter '{param_name}' formatted with wildcards for LIKE clause")
            return f"'%{escaped_value}%'"
        else:
            return f"'{escaped_value}'"

    @classmethod
    def _escape_string_value(cls, value: str, param_name: str) -> str:
        """Escape string value and check for SQL injection"""
        # Escape single quotes
        escaped = value.replace("'", "''")

        # Check for dangerous SQL keywords
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in escaped.upper():
                raise ValueError(
                    f"Dangerous SQL keyword '{keyword}' detected in parameter '{param_name}'"
                )

        return escaped

    @classmethod
    def _is_like_parameter(cls, param_name: str, sql_template: str) -> bool:
        """
        Detect if parameter is used in a LIKE context

        Checks:
        1. Parameter name contains 'pattern' or 'like'
        2. Parameter appears directly after LIKE keyword
        3. LIKE keyword appears near the parameter
        """
        param_lower = param_name.lower()

        # Check if parameter name suggests it's a pattern
        if 'pattern' in param_lower or 'like' in param_lower:
            logger.debug(f"Parameter '{param_name}' identified as LIKE pattern by name")
            return True

        # Check for campaign brand parameters (often used with LIKE)
        if 'campaign_brand' in param_lower or 'brand' in param_lower:
            logger.debug(f"Parameter '{param_name}' identified as brand pattern")
            return True

        # Check for LIKE keyword near parameter in various formats
        patterns_to_check = [
            # Direct LIKE patterns
            rf'\bLIKE\s+[\'"]?\s*\{{\{{{param_name}\}}\}}',  # LIKE {{param}}
            rf'\bLIKE\s+[\'"]?\s*:{param_name}\b',           # LIKE :param
            rf'\bLIKE\s+[\'"]?\s*\${param_name}\b',          # LIKE $param

            # LIKE anywhere near parameter (within 50 chars)
            rf'\bLIKE\s+.{{0,50}}\{{\{{{param_name}\}}\}}',
            rf'\bLIKE\s+.{{0,50}}:{param_name}\b',
            rf'\bLIKE\s+.{{0,50}}\${param_name}\b',
        ]

        for pattern in patterns_to_check:
            if re.search(pattern, sql_template, re.IGNORECASE):
                logger.debug(f"Parameter '{param_name}' found in LIKE context by regex")
                return True

        return False

    @classmethod
    def _replace_parameter_formats(cls, query: str, param_name: str, formatted_value: str) -> str:
        """Replace all parameter format variations with the formatted value"""
        # Replace {{param}} format
        query = query.replace(f"{{{{{param_name}}}}}", formatted_value)

        # Replace :param format
        query = re.sub(rf':{param_name}\b', formatted_value, query)

        # Replace $param format
        query = re.sub(rf'\${param_name}\b', formatted_value, query)

        return query

    @classmethod
    def is_campaign_parameter(cls, param_name: str) -> bool:
        """Check if parameter name indicates it's a campaign parameter"""
        param_lower = param_name.lower()
        return any(keyword in param_lower for keyword in cls.CAMPAIGN_KEYWORDS)

    @classmethod
    def is_asin_parameter(cls, param_name: str) -> bool:
        """Check if parameter name indicates it's an ASIN parameter"""
        param_lower = param_name.lower()
        return any(keyword in param_lower for keyword in cls.ASIN_KEYWORDS)

    @classmethod
    def validate_parameter_types(cls, parameters: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate and convert parameter types
        Returns dict of warnings for any issues found
        """
        warnings = {}

        for param_name, value in parameters.items():
            # Check for None values
            if value is None:
                warnings[param_name] = f"Parameter '{param_name}' has null value"

            # Check for empty arrays
            elif isinstance(value, (list, tuple)) and len(value) == 0:
                warnings[param_name] = f"Parameter '{param_name}' is an empty list"

            # Check for extremely long strings (potential issues)
            elif isinstance(value, str) and len(value) > 1000:
                warnings[param_name] = f"Parameter '{param_name}' is very long ({len(value)} chars)"

        return warnings

    @classmethod
    def get_parameter_info(cls, sql_template: str) -> Dict[str, Dict[str, Any]]:
        """
        Analyze SQL template and return information about each parameter

        Returns dict with parameter details:
        - type: Expected type (string/array/number)
        - context: How it's used (LIKE/IN/EQUALS)
        - is_campaign: If it's a campaign parameter
        - is_asin: If it's an ASIN parameter
        """
        params = cls._find_required_parameters(sql_template)
        param_info = {}

        for param in params:
            info = {
                'is_like': cls._is_like_parameter(param, sql_template),
                'is_campaign': cls.is_campaign_parameter(param),
                'is_asin': cls.is_asin_parameter(param),
                'context': 'LIKE' if cls._is_like_parameter(param, sql_template) else 'EQUALS'
            }

            # Infer expected type
            if info['is_campaign'] or info['is_asin']:
                info['expected_type'] = 'array'
            else:
                info['expected_type'] = 'string'

            param_info[param] = info

        return param_info