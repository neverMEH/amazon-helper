"""
Shared parameter processing utility for AMC SQL queries
Handles parameter substitution, LIKE pattern detection, and array formatting
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import logging
from .query_logger import QueryLogger

logger = logging.getLogger(__name__)


class ParameterProcessor:
    """
    Unified parameter processing for AMC SQL queries
    Ensures consistent handling between frontend preview and backend execution
    """

    # Dangerous SQL keywords to check for injection prevention
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'INSERT INTO', 'UPDATE', 'ALTER',
        'CREATE', 'EXEC', 'EXECUTE', 'TRUNCATE', 'GRANT', 'REVOKE'
    ]

    # AMC API limits
    AMC_MAX_IN_CLAUSE_ITEMS = 1000  # Maximum items in an IN clause
    AMC_MAX_QUERY_LENGTH = 102400  # Maximum query length in bytes (100KB)

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
                             validate_all: bool = True, query_id: Optional[str] = None) -> str:
        """
        Process SQL template with parameter substitution

        Args:
            sql_template: SQL query with parameter placeholders
            parameters: Parameter values to substitute
            validate_all: If True, validate all required params are present.
                         If False, only substitute provided params (useful for partial processing)
            query_id: Optional query ID for tracking through logging

        Returns:
            SQL query with substituted values

        Raises:
            ValueError: If required parameters are missing (when validate_all=True) or dangerous SQL detected
        """
        # Generate query ID if not provided
        if not query_id:
            query_id = QueryLogger.generate_query_id(sql_template)

        # Log template stage
        QueryLogger.log_query_stage(
            query_id,
            QueryLogger.STAGE_TEMPLATE,
            sql_template,
            parameters,
            metadata={"validate_all": validate_all}
        )

        # Find all required parameters
        required_params = cls._find_required_parameters(sql_template)

        # Log parameter extraction
        QueryLogger.log_query_stage(
            query_id,
            QueryLogger.STAGE_PARAMETER_EXTRACTION,
            sql_template,
            parameters,
            metadata={"required_params": required_params}
        )

        # Validate required parameters are present (only if validate_all is True)
        if validate_all:
            cls._validate_parameters(required_params, parameters)
            QueryLogger.log_validation_result(
                query_id,
                "parameter_presence",
                True,
                {"all_params_present": True}
            )

        # Substitute parameters
        query = cls._substitute_parameters(sql_template, parameters, query_id)

        # Log final substitution
        QueryLogger.log_query_stage(
            query_id,
            QueryLogger.STAGE_PARAMETER_SUBSTITUTION,
            query,
            parameters,
            metadata={"final_length": len(query)}
        )

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
    def _substitute_parameters(cls, sql_template: str, parameters: Dict[str, Any],
                             query_id: Optional[str] = None) -> str:
        """Substitute all parameters in SQL template"""
        query = sql_template

        for param_name, value in parameters.items():
            # Format the value based on its type and context
            formatted_value = cls._format_parameter_value(
                param_name, value, sql_template
            )

            # Log parameter processing if query_id provided
            if query_id:
                is_large = isinstance(value, list) and len(value) > cls.AMC_MAX_IN_CLAUSE_ITEMS
                QueryLogger.log_parameter_processing(
                    query_id,
                    param_name,
                    value,
                    formatted_value,
                    is_large_list=is_large
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
        - None: Convert to SQL NULL
        """
        if value is None:
            return 'NULL'
        elif isinstance(value, (list, tuple)):
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
        """
        Format array parameter as SQL IN clause
        Handles large lists by using VALUES clause approach if needed
        """
        # Check if this is a large list that needs special handling
        if len(values) > cls.AMC_MAX_IN_CLAUSE_ITEMS:
            logger.warning(
                f"Parameter '{param_name}' has {len(values)} items, "
                f"exceeding AMC limit of {cls.AMC_MAX_IN_CLAUSE_ITEMS}. "
                "Consider using VALUES clause approach or batching."
            )

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

        # Check if this parameter is used in a LIKE context (but not for empty strings)
        if value and cls._is_like_parameter(param_name, sql_template):
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

    @classmethod
    def format_as_values_clause(cls, values: List[Any], column_name: str = "column1") -> str:
        """
        Format a list of values as a VALUES clause for use in CTEs
        This is useful for large lists that exceed IN clause limits

        Args:
            values: List of values to format
            column_name: Name for the column in VALUES clause

        Returns:
            VALUES clause formatted string

        Example:
            Input: ["val1", "val2"], "campaign_id"
            Output: "(VALUES ('val1'), ('val2')) AS t(campaign_id)"
        """
        if not values:
            # Return empty VALUES clause
            return f"(VALUES (NULL)) AS t({column_name}) WHERE 1=0"

        formatted_values = []
        for val in values:
            if isinstance(val, str):
                # Escape single quotes
                escaped = val.replace("'", "''")
                formatted_values.append(f"('{escaped}')")
            elif val is None:
                formatted_values.append("(NULL)")
            else:
                formatted_values.append(f"({val})")

        values_clause = f"(VALUES {', '.join(formatted_values)}) AS t({column_name})"
        return values_clause

    @classmethod
    def default_values_for(cls, param_name: str) -> List[Any]:
        """Provide sensible default values for parameters when none are supplied."""
        lower = param_name.lower()
        if 'asin' in lower:
            return ['B00DUMMY01']
        if 'campaign' in lower:
            return ['dummy_campaign']
        if 'brand' in lower:
            return ['dummy_brand']
        if 'date' in lower or 'time' in lower:
            if 'start' in lower:
                return [(datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')]
            return [(datetime.utcnow() - timedelta(days=15)).strftime('%Y-%m-%d')]
        return ['dummy_value']

    @classmethod
    def _quote_sql_literal(cls, param_name: str, value: Any) -> str:
        """Quote and escape a Python value for inclusion in a SQL VALUES clause."""
        if value is None:
            return 'NULL'
        if isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        if isinstance(value, (int, float)):
            return str(value)
        return f"'{cls._escape_string_value(str(value), param_name)}'"

    @classmethod
    def _infer_placeholder_column_count(cls, sql_template: str, param_name: str) -> int:
        """Best-effort detection of how many columns a VALUES placeholder feeds."""
        escaped = re.escape(param_name)

        patterns = [
            # Alias defined before VALUES: foo(col1, col2) AS (VALUES {{param}})
            re.compile(
                rf"[A-Za-z0-9_]+\s*\(([^)]+)\)\s*AS\s*\(\s*VALUES\s*\{{\{{{escaped}\}}\}}",
                re.IGNORECASE | re.DOTALL,
            ),
            # Alias defined after VALUES: VALUES {{param}} AS t(col1,col2)
            re.compile(
                rf"VALUES\s*\{{\{{{escaped}\}}\}}\s*AS\s+[^()]+\(([^)]+)\)",
                re.IGNORECASE | re.DOTALL,
            ),
            # Closing parenthesis before alias
            re.compile(
                rf"VALUES\s*\{{\{{{escaped}\}}\}}\s*\)\s*AS\s+[^()]+\(([^)]+)\)",
                re.IGNORECASE | re.DOTALL,
            ),
            # Tuple IN clause e.g. (col1,col2) IN {{param}}
            re.compile(
                rf"\(([^)]+)\)\s*IN\s*\{{\{{{escaped}\}}\}}",
                re.IGNORECASE,
            ),
        ]

        for pattern in patterns:
            match = pattern.search(sql_template)
            if match:
                columns = [c.strip() for c in match.group(1).split(',') if c.strip()]
                if columns:
                    return len(columns)

        return 1

    @classmethod
    def build_values_clause(
        cls,
        sql_template: str,
        param_name: str,
        values: Optional[List[Any]] = None,
    ) -> str:
        """Construct a VALUES clause body aligned with the placeholder's expected column count."""
        candidate_values: List[Any]
        if values is None:
            candidate_values = cls.default_values_for(param_name)
        else:
            candidate_values = list(values) if isinstance(values, list) else [values]

        if not candidate_values:
            candidate_values = cls.default_values_for(param_name)

        column_count = max(1, cls._infer_placeholder_column_count(sql_template, param_name))

        rows: List[str] = []
        for raw in candidate_values:
            if isinstance(raw, (list, tuple)):
                row_values = list(raw)
            else:
                row_values = [raw]

            if column_count > len(row_values):
                base = str(row_values[0]) if row_values else param_name
                for idx in range(len(row_values), column_count):
                    row_values.append(f"{base}_col{idx + 1}")
            elif column_count < len(row_values):
                row_values = row_values[:column_count]

            quoted_values = [cls._quote_sql_literal(param_name, value) for value in row_values]
            rows.append(f"({', '.join(quoted_values)})")

        clause = ',\n'.join(f"    {row}" for row in rows)
        logger.debug(
            "Built VALUES clause for %s: %d rows, %d columns",
            param_name,
            len(rows),
            column_count,
        )
        sample = '\n'.join(clause.splitlines()[:3])
        logger.debug("VALUES clause sample:\n%s", sample)
        return clause

    @classmethod
    def create_large_list_cte(cls, param_name: str, values: List[Any],
                            column_name: Optional[str] = None) -> str:
        """
        Create a CTE (Common Table Expression) for handling large lists

        Args:
            param_name: Parameter name (e.g., "campaign_ids")
            values: List of values
            column_name: Column name for the CTE (defaults to param_name without 's')

        Returns:
            CTE definition string

        Example:
            Input: "campaign_ids", ["c1", "c2", "c3"]
            Output: "WITH campaign_ids_filter AS (SELECT column1 as campaign_id FROM (VALUES ('c1'), ('c2'), ('c3')) AS t(column1))"
        """
        if not column_name:
            # Try to infer column name from param name
            if param_name.endswith('_ids'):
                column_name = param_name[:-1]  # Remove 's' from ids
            elif param_name.endswith('_list'):
                column_name = param_name[:-5]  # Remove '_list'
            elif param_name.endswith('s') and len(param_name) > 1 and param_name != 'status':
                # Only remove plural 's' if it makes sense (not for words like "status")
                column_name = param_name[:-1]  # Remove plural 's'
            else:
                column_name = param_name

        cte_name = f"{param_name}_filter"
        values_clause = cls.format_as_values_clause(values, "column1")

        cte = f"WITH {cte_name} AS (SELECT column1 as {column_name} FROM {values_clause})"
        return cte

    @classmethod
    def check_query_length(cls, query: str, query_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if query length is within AMC limits

        Args:
            query: SQL query to check
            query_id: Optional query ID for tracking

        Returns:
            Dict with length info and warnings
        """
        query_bytes = len(query.encode('utf-8'))

        result = {
            'length_bytes': query_bytes,
            'length_chars': len(query),
            'within_limits': query_bytes <= cls.AMC_MAX_QUERY_LENGTH,
            'limit_bytes': cls.AMC_MAX_QUERY_LENGTH
        }

        # Log validation result if query_id provided
        if query_id:
            QueryLogger.log_validation_result(
                query_id,
                "query_length",
                result['within_limits'],
                result,
                error_message=result.get('warning')
            )

        if not result['within_limits']:
            result['warning'] = (
                f"Query exceeds AMC limit: {query_bytes} bytes "
                f"(limit: {cls.AMC_MAX_QUERY_LENGTH} bytes). "
                "Consider using VALUES clause approach or reducing parameters."
            )
            logger.warning(result['warning'])

        return result
