"""Widget Configuration Service for dashboard widgets validation and management"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import uuid
from enum import Enum

from .reporting_database_service import ReportingDatabaseService
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class WidgetType(str, Enum):
    """Supported widget types"""
    LINE_CHART = 'line_chart'
    BAR_CHART = 'bar_chart'
    PIE_CHART = 'pie_chart'
    AREA_CHART = 'area_chart'
    SCATTER_CHART = 'scatter_chart'
    TABLE = 'table'
    METRIC_CARD = 'metric_card'
    TEXT = 'text'
    HEATMAP = 'heatmap'
    FUNNEL = 'funnel'


class MetricType(str, Enum):
    """Standard AMC metrics"""
    IMPRESSIONS = 'impressions'
    CLICKS = 'clicks'
    CONVERSIONS = 'conversions'
    SPEND = 'spend'
    SALES = 'sales'
    ROAS = 'roas'
    ACOS = 'acos'
    CTR = 'ctr'
    CVR = 'cvr'
    CPC = 'cpc'
    CPM = 'cpm'
    NTB_PERCENTAGE = 'ntb_percentage'
    REACH = 'reach'
    FREQUENCY = 'frequency'
    VIEW_THROUGH_RATE = 'view_through_rate'
    CLICK_THROUGH_RATE = 'click_through_rate'


class AggregationLevel(str, Enum):
    """Data aggregation levels"""
    HOURLY = 'hourly'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'


class WidgetConfigurationService:
    """Service for managing and validating widget configurations"""
    
    def __init__(self):
        self.db_service = ReportingDatabaseService()
        
        # Widget type constraints
        self.widget_constraints = {
            WidgetType.LINE_CHART: {
                'min_data_points': 2,
                'max_series': 10,
                'required_axes': ['x', 'y'],
                'supports_multiple_metrics': True
            },
            WidgetType.BAR_CHART: {
                'min_data_points': 1,
                'max_series': 10,
                'required_axes': ['x', 'y'],
                'supports_multiple_metrics': True
            },
            WidgetType.PIE_CHART: {
                'min_data_points': 1,
                'max_segments': 20,
                'required_axes': [],
                'supports_multiple_metrics': False
            },
            WidgetType.AREA_CHART: {
                'min_data_points': 2,
                'max_series': 5,
                'required_axes': ['x', 'y'],
                'supports_multiple_metrics': True
            },
            WidgetType.SCATTER_CHART: {
                'min_data_points': 1,
                'max_series': 5,
                'required_axes': ['x', 'y'],
                'supports_multiple_metrics': False
            },
            WidgetType.TABLE: {
                'min_data_points': 1,
                'max_rows': 1000,
                'required_axes': [],
                'supports_multiple_metrics': True
            },
            WidgetType.METRIC_CARD: {
                'min_data_points': 1,
                'max_metrics': 1,
                'required_axes': [],
                'supports_multiple_metrics': False
            },
            WidgetType.TEXT: {
                'min_data_points': 0,
                'max_length': 5000,
                'required_axes': [],
                'supports_multiple_metrics': False
            },
            WidgetType.HEATMAP: {
                'min_data_points': 1,
                'max_series': 100,
                'required_axes': ['x', 'y'],
                'supports_multiple_metrics': False
            },
            WidgetType.FUNNEL: {
                'min_data_points': 2,
                'max_steps': 10,
                'required_axes': [],
                'supports_multiple_metrics': False
            }
        }
    
    def validate_widget_configuration(
        self, 
        widget_config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a widget configuration
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Required fields
            if 'widget_type' not in widget_config:
                return False, 'Widget type is required'
            
            if 'name' not in widget_config:
                return False, 'Widget name is required'
            
            widget_type = widget_config.get('widget_type')
            
            # Validate widget type
            if widget_type not in [wt.value for wt in WidgetType]:
                return False, f'Invalid widget type: {widget_type}'
            
            # Validate data source for non-text widgets
            if widget_type != WidgetType.TEXT.value:
                if 'data_source' not in widget_config:
                    return False, 'Data source configuration is required'
                
                is_valid, error = self.validate_data_source(widget_config['data_source'])
                if not is_valid:
                    return False, f'Data source validation failed: {error}'
            
            # Validate widget-specific constraints
            is_valid, error = self._validate_widget_constraints(widget_config)
            if not is_valid:
                return False, error
            
            # Validate layout configuration
            if 'layout' in widget_config:
                is_valid, error = self.validate_layout_configuration(widget_config['layout'])
                if not is_valid:
                    return False, f'Layout validation failed: {error}'
            
            # Validate styling configuration
            if 'styling' in widget_config:
                is_valid, error = self._validate_styling_configuration(widget_config['styling'])
                if not is_valid:
                    return False, f'Styling validation failed: {error}'
            
            return True, None
            
        except Exception as e:
            logger.error(f'Error validating widget configuration: {e}')
            return False, str(e)
    
    def validate_data_source(self, data_source: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate widget data source configuration
        """
        try:
            # Check for required fields
            if 'type' not in data_source:
                return False, 'Data source type is required'
            
            source_type = data_source.get('type')
            
            if source_type == 'workflow':
                # Validate workflow data source
                if 'workflow_id' not in data_source:
                    return False, 'Workflow ID is required for workflow data source'
                
                if 'instance_id' not in data_source:
                    return False, 'Instance ID is required for workflow data source'
                
            elif source_type == 'aggregate':
                # Validate aggregate data source
                if 'aggregation_type' not in data_source:
                    return False, 'Aggregation type is required'
                
                if 'metrics' not in data_source or not data_source['metrics']:
                    return False, 'At least one metric is required'
                
                # Validate metrics
                for metric in data_source['metrics']:
                    if metric not in [m.value for m in MetricType]:
                        return False, f'Invalid metric: {metric}'
            
            elif source_type == 'custom':
                # Custom data source - minimal validation
                if 'query' not in data_source:
                    return False, 'Query is required for custom data source'
            
            else:
                return False, f'Invalid data source type: {source_type}'
            
            # Validate filters if present
            if 'filters' in data_source:
                is_valid, error = self._validate_filters(data_source['filters'])
                if not is_valid:
                    return False, error
            
            # Validate date range if present
            if 'date_range' in data_source:
                is_valid, error = self._validate_date_range(data_source['date_range'])
                if not is_valid:
                    return False, error
            
            return True, None
            
        except Exception as e:
            logger.error(f'Error validating data source: {e}')
            return False, str(e)
    
    def validate_layout_configuration(self, layout: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate widget layout configuration
        """
        try:
            # Validate grid position
            if 'x' in layout:
                if not isinstance(layout['x'], (int, float)) or layout['x'] < 0:
                    return False, 'Invalid x position'
            
            if 'y' in layout:
                if not isinstance(layout['y'], (int, float)) or layout['y'] < 0:
                    return False, 'Invalid y position'
            
            # Validate dimensions
            if 'width' in layout:
                if not isinstance(layout['width'], (int, float)) or layout['width'] <= 0:
                    return False, 'Invalid width'
                if layout['width'] > 12:  # Assuming 12-column grid
                    return False, 'Width exceeds maximum grid columns (12)'
            
            if 'height' in layout:
                if not isinstance(layout['height'], (int, float)) or layout['height'] <= 0:
                    return False, 'Invalid height'
                if layout['height'] > 100:  # Reasonable max height
                    return False, 'Height exceeds maximum allowed (100)'
            
            # Validate z-index if present
            if 'z_index' in layout:
                if not isinstance(layout['z_index'], int):
                    return False, 'Z-index must be an integer'
            
            return True, None
            
        except Exception as e:
            logger.error(f'Error validating layout configuration: {e}')
            return False, str(e)
    
    def create_widget_template(self, widget_type: str, template_name: str) -> Dict[str, Any]:
        """
        Create a template configuration for a specific widget type
        """
        templates = {
            WidgetType.LINE_CHART: {
                'widget_type': WidgetType.LINE_CHART.value,
                'name': template_name or 'Line Chart',
                'data_source': {
                    'type': 'aggregate',
                    'metrics': ['impressions', 'clicks'],
                    'aggregation_type': 'daily',
                    'date_range': {
                        'type': 'relative',
                        'value': 'last_30_days'
                    }
                },
                'config': {
                    'chart': {
                        'type': 'line',
                        'smooth': True,
                        'show_points': True,
                        'tension': 0.4
                    },
                    'axes': {
                        'x': {
                            'type': 'time',
                            'label': 'Date'
                        },
                        'y': {
                            'type': 'linear',
                            'label': 'Value'
                        }
                    },
                    'legend': {
                        'display': True,
                        'position': 'top'
                    }
                },
                'layout': {
                    'x': 0,
                    'y': 0,
                    'width': 6,
                    'height': 4
                }
            },
            WidgetType.BAR_CHART: {
                'widget_type': WidgetType.BAR_CHART.value,
                'name': template_name or 'Bar Chart',
                'data_source': {
                    'type': 'aggregate',
                    'metrics': ['sales', 'spend'],
                    'aggregation_type': 'weekly',
                    'date_range': {
                        'type': 'relative',
                        'value': 'last_12_weeks'
                    }
                },
                'config': {
                    'chart': {
                        'type': 'bar',
                        'stacked': False,
                        'horizontal': False
                    },
                    'axes': {
                        'x': {
                            'type': 'category',
                            'label': 'Week'
                        },
                        'y': {
                            'type': 'linear',
                            'label': 'Amount ($)'
                        }
                    },
                    'legend': {
                        'display': True,
                        'position': 'top'
                    }
                },
                'layout': {
                    'x': 0,
                    'y': 0,
                    'width': 6,
                    'height': 4
                }
            },
            WidgetType.PIE_CHART: {
                'widget_type': WidgetType.PIE_CHART.value,
                'name': template_name or 'Pie Chart',
                'data_source': {
                    'type': 'aggregate',
                    'metrics': ['spend'],
                    'aggregation_type': 'total',
                    'group_by': 'campaign',
                    'date_range': {
                        'type': 'relative',
                        'value': 'last_30_days'
                    }
                },
                'config': {
                    'chart': {
                        'type': 'pie',
                        'show_labels': True,
                        'show_percentages': True
                    },
                    'legend': {
                        'display': True,
                        'position': 'right'
                    }
                },
                'layout': {
                    'x': 0,
                    'y': 0,
                    'width': 4,
                    'height': 4
                }
            },
            WidgetType.METRIC_CARD: {
                'widget_type': WidgetType.METRIC_CARD.value,
                'name': template_name or 'Metric Card',
                'data_source': {
                    'type': 'aggregate',
                    'metrics': ['roas'],
                    'aggregation_type': 'average',
                    'date_range': {
                        'type': 'relative',
                        'value': 'last_7_days'
                    }
                },
                'config': {
                    'display': {
                        'format': 'number',
                        'decimals': 2,
                        'prefix': '',
                        'suffix': 'x',
                        'show_trend': True,
                        'compare_to': 'previous_period'
                    },
                    'thresholds': {
                        'good': 3.0,
                        'warning': 2.0,
                        'critical': 1.5
                    }
                },
                'layout': {
                    'x': 0,
                    'y': 0,
                    'width': 2,
                    'height': 2
                }
            },
            WidgetType.TABLE: {
                'widget_type': WidgetType.TABLE.value,
                'name': template_name or 'Data Table',
                'data_source': {
                    'type': 'workflow',
                    'workflow_id': '',
                    'instance_id': '',
                    'date_range': {
                        'type': 'relative',
                        'value': 'last_30_days'
                    }
                },
                'config': {
                    'table': {
                        'sortable': True,
                        'filterable': True,
                        'paginated': True,
                        'page_size': 25,
                        'striped': True,
                        'hover': True
                    },
                    'columns': [
                        {
                            'field': 'campaign_name',
                            'header': 'Campaign',
                            'sortable': True,
                            'width': 200
                        },
                        {
                            'field': 'impressions',
                            'header': 'Impressions',
                            'sortable': True,
                            'format': 'number'
                        },
                        {
                            'field': 'clicks',
                            'header': 'Clicks',
                            'sortable': True,
                            'format': 'number'
                        },
                        {
                            'field': 'ctr',
                            'header': 'CTR',
                            'sortable': True,
                            'format': 'percentage'
                        }
                    ]
                },
                'layout': {
                    'x': 0,
                    'y': 0,
                    'width': 12,
                    'height': 6
                }
            },
            WidgetType.TEXT: {
                'widget_type': WidgetType.TEXT.value,
                'name': template_name or 'Text Widget',
                'content': {
                    'text': 'Enter your text content here...',
                    'markdown': False
                },
                'styling': {
                    'font_size': 14,
                    'text_align': 'left',
                    'font_weight': 'normal'
                },
                'layout': {
                    'x': 0,
                    'y': 0,
                    'width': 4,
                    'height': 2
                }
            }
        }
        
        widget_type_enum = WidgetType(widget_type) if isinstance(widget_type, str) else widget_type
        return templates.get(widget_type_enum, templates[WidgetType.LINE_CHART])
    
    def map_data_source_to_aggregates(
        self,
        data_source: Dict[str, Any],
        dashboard_id: str,
        date_range: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Map widget data source configuration to aggregated data
        """
        try:
            source_type = data_source.get('type')
            
            if source_type == 'aggregate':
                # Get aggregated data from database
                aggregates = self.db_service.get_aggregates_for_dashboard(
                    dashboard_id=dashboard_id,
                    date_range=date_range or data_source.get('date_range'),
                    metrics=data_source.get('metrics', [])
                )
                
                return {
                    'data': aggregates,
                    'source_type': 'aggregate',
                    'metrics': data_source.get('metrics'),
                    'aggregation_level': data_source.get('aggregation_type')
                }
            
            elif source_type == 'workflow':
                # Get workflow execution results
                # This would be implemented when workflow data is available
                return {
                    'data': [],
                    'source_type': 'workflow',
                    'workflow_id': data_source.get('workflow_id'),
                    'instance_id': data_source.get('instance_id')
                }
            
            elif source_type == 'custom':
                # Custom query execution
                # This would be implemented based on custom query requirements
                return {
                    'data': [],
                    'source_type': 'custom',
                    'query': data_source.get('query')
                }
            
            else:
                logger.warning(f'Unknown data source type: {source_type}')
                return {'data': [], 'source_type': 'unknown'}
            
        except Exception as e:
            logger.error(f'Error mapping data source to aggregates: {e}')
            return {'data': [], 'error': str(e)}
    
    def update_widget_configuration(
        self,
        widget_id: str,
        dashboard_id: str,
        updates: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Update widget configuration with validation
        """
        try:
            # Validate the updated configuration
            is_valid, error = self.validate_widget_configuration(updates)
            if not is_valid:
                return False, error
            
            # Update widget in database
            updated = self.db_service.update_widget(widget_id, dashboard_id, updates)
            
            if updated:
                return True, None
            else:
                return False, 'Failed to update widget in database'
            
        except Exception as e:
            logger.error(f'Error updating widget configuration: {e}')
            return False, str(e)
    
    def validate_widget_positioning(
        self,
        dashboard_id: str,
        new_widget_layout: Dict[str, Any],
        exclude_widget_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that widget positioning doesn't overlap with existing widgets
        """
        try:
            # Get existing dashboard with widgets
            dashboard = self.db_service.get_dashboard_with_widgets(dashboard_id)
            if not dashboard:
                return False, 'Dashboard not found'
            
            existing_widgets = dashboard.get('dashboard_widgets', [])
            
            new_x = new_widget_layout.get('x', 0)
            new_y = new_widget_layout.get('y', 0)
            new_width = new_widget_layout.get('width', 1)
            new_height = new_widget_layout.get('height', 1)
            
            # Check for overlaps
            for widget in existing_widgets:
                # Skip if this is the widget being updated
                if exclude_widget_id and widget.get('id') == exclude_widget_id:
                    continue
                
                widget_layout = widget.get('layout', {})
                wx = widget_layout.get('x', 0)
                wy = widget_layout.get('y', 0)
                wwidth = widget_layout.get('width', 1)
                wheight = widget_layout.get('height', 1)
                
                # Check if rectangles overlap
                if (new_x < wx + wwidth and 
                    new_x + new_width > wx and
                    new_y < wy + wheight and
                    new_y + new_height > wy):
                    return False, f"Widget overlaps with existing widget: {widget.get('name', 'Unnamed')}"
            
            return True, None
            
        except Exception as e:
            logger.error(f'Error validating widget positioning: {e}')
            return False, str(e)
    
    # Private helper methods
    
    def _validate_widget_constraints(self, widget_config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate widget-specific constraints"""
        widget_type = WidgetType(widget_config['widget_type'])
        constraints = self.widget_constraints.get(widget_type, {})
        
        # Check metric count constraints
        if 'data_source' in widget_config and 'metrics' in widget_config['data_source']:
            metrics = widget_config['data_source']['metrics']
            
            if not constraints.get('supports_multiple_metrics', True) and len(metrics) > 1:
                return False, f'{widget_type.value} does not support multiple metrics'
            
            if 'max_metrics' in constraints and len(metrics) > constraints['max_metrics']:
                return False, f'{widget_type.value} supports maximum {constraints["max_metrics"]} metrics'
        
        # Check text widget constraints
        if widget_type == WidgetType.TEXT:
            content = widget_config.get('content', {})
            text = content.get('text', '')
            max_length = constraints.get('max_length', 5000)
            
            if len(text) > max_length:
                return False, f'Text content exceeds maximum length of {max_length} characters'
        
        return True, None
    
    def _validate_filters(self, filters: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate filter configuration"""
        valid_filter_keys = [
            'campaigns', 'asins', 'keywords', 'placements', 
            'audiences', 'brands', 'categories'
        ]
        
        for key in filters.keys():
            if key not in valid_filter_keys:
                return False, f'Invalid filter key: {key}'
            
            if not isinstance(filters[key], list):
                return False, f'Filter {key} must be a list'
        
        return True, None
    
    def _validate_date_range(self, date_range: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate date range configuration"""
        if 'type' not in date_range:
            return False, 'Date range type is required'
        
        range_type = date_range['type']
        
        if range_type == 'relative':
            valid_relative_values = [
                'today', 'yesterday', 'last_7_days', 'last_14_days',
                'last_30_days', 'last_90_days', 'last_12_weeks',
                'last_6_months', 'last_year', 'this_week', 'this_month',
                'this_quarter', 'this_year'
            ]
            
            if 'value' not in date_range:
                return False, 'Relative date range value is required'
            
            if date_range['value'] not in valid_relative_values:
                return False, f'Invalid relative date range: {date_range["value"]}'
        
        elif range_type == 'absolute':
            if 'start_date' not in date_range or 'end_date' not in date_range:
                return False, 'Start and end dates are required for absolute date range'
            
            # TODO: Validate date format
        
        else:
            return False, f'Invalid date range type: {range_type}'
        
        return True, None
    
    def _validate_styling_configuration(self, styling: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate widget styling configuration"""
        # Basic validation for common styling properties
        if 'colors' in styling:
            if not isinstance(styling['colors'], (list, dict)):
                return False, 'Colors must be a list or dictionary'
        
        if 'font_size' in styling:
            if not isinstance(styling['font_size'], (int, float)) or styling['font_size'] <= 0:
                return False, 'Invalid font size'
        
        if 'opacity' in styling:
            if not isinstance(styling['opacity'], (int, float)) or not (0 <= styling['opacity'] <= 1):
                return False, 'Opacity must be between 0 and 1'
        
        return True, None