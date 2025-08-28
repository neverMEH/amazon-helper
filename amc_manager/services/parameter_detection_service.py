"""
Parameter Detection Service
Detects and classifies parameters in SQL queries for AMC workflows
"""
import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class DetectedParameter:
    """Represents a detected parameter in a SQL query"""
    name: str
    type: str  # 'asin', 'date', 'campaign'
    placeholder: str
    position: int


class ParameterDetectionService:
    """Service for detecting and classifying parameters in SQL queries"""
    
    # Parameter patterns for different placeholder formats
    PLACEHOLDER_PATTERNS = [
        r'\{\{([^}]+)\}\}',  # {{parameter}}
        r':(\w+)',           # :parameter
        r'\$(\w+)',          # $parameter
    ]
    
    # Keywords that indicate parameter types (case-insensitive)
    ASIN_KEYWORDS = ['asin', 'product_asin', 'parent_asin', 'child_asin', 'asins', 'asin_list']
    DATE_KEYWORDS = ['date', 'start_date', 'end_date', 'date_from', 'date_to', 
                     'begin_date', 'finish_date', 'timestamp', 'start_time', 'end_time',
                     'date_start', 'date_end', 'from_date', 'to_date']
    CAMPAIGN_KEYWORDS = ['campaign', 'campaign_id', 'campaign_name', 'campaigns', 
                        'campaign_ids', 'campaign_list']
    
    def detect_parameters(self, query: str) -> List[Dict[str, Any]]:
        """
        Detect and classify parameters in a SQL query
        
        Args:
            query: SQL query string
            
        Returns:
            List of detected parameters with their types and positions
        """
        detected_params = []
        seen_params = set()  # Track unique parameters to avoid duplicates
        
        # Process each placeholder pattern
        for pattern in self.PLACEHOLDER_PATTERNS:
            for match in re.finditer(pattern, query, re.IGNORECASE):
                # Get the full placeholder and the parameter name
                if pattern == r'\{\{([^}]+)\}\}':
                    placeholder = match.group(0)  # {{parameter}}
                    param_name = match.group(1)   # parameter
                elif pattern == r':(\w+)':
                    placeholder = match.group(0)  # :parameter
                    param_name = match.group(1)   # parameter
                else:  # $parameter
                    placeholder = match.group(0)  # $parameter
                    param_name = match.group(1)   # parameter
                
                # Skip if we've already detected this parameter
                if param_name in seen_params:
                    continue
                
                # Skip if it's an escaped placeholder
                if self._is_escaped(query, match.start()):
                    continue
                
                # Classify the parameter type and get additional metadata
                param_info = self._classify_parameter(param_name, query, match.start())
                
                if param_info:
                    detected_params.append({
                        "name": param_name,
                        "type": param_info.get('type'),
                        "placeholder": placeholder,
                        "campaign_type": param_info.get('campaign_type'),  # sp, sb, sd, dsp
                        "value_type": param_info.get('value_type'),  # names, ids
                        "position": match.start()
                    })
                    seen_params.add(param_name)
        
        # Sort by position in query
        detected_params.sort(key=lambda x: x["position"])
        
        return detected_params
    
    def _classify_parameter(self, param_name: str, query: str, position: int) -> dict:
        """
        Classify the type of a parameter based on its name and context
        
        Args:
            param_name: The parameter name
            query: The full query string
            position: Position of the parameter in the query
            
        Returns:
            Dict with parameter info or None
        """
        param_lower = param_name.lower()
        
        # Check for ASIN parameters
        if any(keyword in param_lower for keyword in self.ASIN_KEYWORDS):
            return {'type': 'asin'}
        
        # Check for date parameters
        if any(keyword in param_lower for keyword in self.DATE_KEYWORDS):
            return {'type': 'date'}
        
        # Check for campaign parameters with specific types
        if any(keyword in param_lower for keyword in self.CAMPAIGN_KEYWORDS):
            # Determine campaign type and value type from parameter name
            campaign_info = self._parse_campaign_parameter(param_name)
            return {
                'type': 'campaign',
                'campaign_type': campaign_info.get('campaign_type'),
                'value_type': campaign_info.get('value_type', 'ids')
            }
        
        # Try to infer from context around the parameter
        context = self._get_context(query, position)
        context_lower = context.lower()
        
        # Check context for ASIN indicators
        if any(keyword in context_lower for keyword in ['asin', 'product']):
            return {'type': 'asin'}
        
        # Check context for date indicators
        if any(keyword in context_lower for keyword in ['date', 'time', 'between', 'from', 'to']):
            return {'type': 'date'}
        
        # Check context for campaign indicators
        if any(keyword in context_lower for keyword in ['campaign']):
            return {'type': 'campaign'}
        
        # Default to None if we can't classify
        return None
    
    def _parse_campaign_parameter(self, param_name: str) -> dict:
        """
        Parse campaign parameter name to determine campaign type and value type
        
        Examples:
        - 'sp_campaign_names' -> {'campaign_type': 'sp', 'value_type': 'names'}
        - 'display_campaign_ids' -> {'campaign_type': 'dsp', 'value_type': 'ids'}
        - 'sb_campaign_ids' -> {'campaign_type': 'sb', 'value_type': 'ids'}
        """
        param_lower = param_name.lower()
        result = {'campaign_type': None, 'value_type': 'ids'}  # Default to ids
        
        # Determine campaign type
        if 'sp_' in param_lower or 'sponsored_products' in param_lower:
            result['campaign_type'] = 'sp'
        elif 'sb_' in param_lower or 'sponsored_brands' in param_lower:
            result['campaign_type'] = 'sb'
        elif 'sd_' in param_lower or 'sponsored_display' in param_lower:
            result['campaign_type'] = 'sd'
        elif 'display_' in param_lower or 'dsp_' in param_lower:
            result['campaign_type'] = 'dsp'
        
        # Determine value type
        if 'name' in param_lower:
            result['value_type'] = 'names'
        elif 'id' in param_lower:
            result['value_type'] = 'ids'
        
        return result
    
    def _get_context(self, query: str, position: int, context_size: int = 30) -> str:
        """
        Get the context around a parameter position
        
        Args:
            query: The query string
            position: Position in the query
            context_size: Number of characters to include before the position
            
        Returns:
            Context string
        """
        start = max(0, position - context_size)
        end = min(len(query), position + context_size)
        return query[start:end]
    
    def _is_escaped(self, query: str, position: int) -> bool:
        """
        Check if a placeholder is escaped (preceded by backslash)
        
        Args:
            query: The query string
            position: Position of the placeholder
            
        Returns:
            True if escaped, False otherwise
        """
        if position == 0:
            return False
        return query[position - 1] == '\\'
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and format parameter values for SQL substitution
        
        Args:
            parameters: Dictionary of parameter names to values
            
        Returns:
            Dictionary with validation results and formatted values
        """
        errors = []
        formatted = {}
        
        for param_name, value in parameters.items():
            param_type = self._infer_type_from_value(param_name, value)
            
            if param_type == 'date':
                # Validate date format
                if isinstance(value, str):
                    # Ensure no timezone suffix
                    if value.endswith('Z'):
                        value = value[:-1]
                    formatted[param_name] = value
                else:
                    errors.append(f"Invalid date format for {param_name}")
            
            elif param_type == 'asin' or param_type == 'campaign':
                # Handle arrays for multi-select
                if isinstance(value, list):
                    # Format for SQL IN clause
                    formatted[param_name] = "'" + "','".join(str(v) for v in value) + "'"
                else:
                    formatted[param_name] = f"'{value}'"
            
            else:
                # Default handling
                formatted[param_name] = value
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "formatted_parameters": formatted
        }
    
    def _infer_type_from_value(self, param_name: str, value: Any) -> str:
        """
        Infer parameter type from its name and value
        
        Args:
            param_name: Parameter name
            value: Parameter value
            
        Returns:
            Inferred type
        """
        param_lower = param_name.lower()
        
        if any(keyword in param_lower for keyword in self.DATE_KEYWORDS):
            return 'date'
        elif any(keyword in param_lower for keyword in self.ASIN_KEYWORDS):
            return 'asin'
        elif any(keyword in param_lower for keyword in self.CAMPAIGN_KEYWORDS):
            return 'campaign'
        
        # Try to infer from value type
        if isinstance(value, str) and 'T' in value and ':' in value:
            return 'date'  # Likely a datetime string
        elif isinstance(value, list):
            return 'asin'  # Default array to ASIN
        
        return 'unknown'