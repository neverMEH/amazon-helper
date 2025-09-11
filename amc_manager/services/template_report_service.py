"""Template Report Management Service for Dashboard Generation"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from ..core.logger_simple import get_logger
from .db_service import DatabaseService, with_connection_retry

logger = get_logger(__name__)


class TemplateReportService(DatabaseService):
    """Service for managing query template report configurations and dashboard generation"""
    
    def __init__(self):
        """Initialize the template report service"""
        super().__init__()
        
        # Available widget types for dashboards
        self.WIDGET_TYPES = {
            'line_chart': {
                'name': 'Line Chart',
                'required_fields': ['x_field', 'y_field'],
                'optional_fields': ['series_field', 'title', 'description']
            },
            'bar_chart': {
                'name': 'Bar Chart',
                'required_fields': ['x_field', 'y_field'],
                'optional_fields': ['series_field', 'title', 'description', 'horizontal']
            },
            'pie_chart': {
                'name': 'Pie Chart',
                'required_fields': ['label_field', 'value_field'],
                'optional_fields': ['title', 'description', 'show_legend']
            },
            'area_chart': {
                'name': 'Area Chart',
                'required_fields': ['x_field', 'y_field'],
                'optional_fields': ['series_field', 'title', 'description', 'stacked']
            },
            'scatter_plot': {
                'name': 'Scatter Plot',
                'required_fields': ['x_field', 'y_field'],
                'optional_fields': ['size_field', 'color_field', 'title', 'description']
            },
            'table': {
                'name': 'Data Table',
                'required_fields': ['columns'],
                'optional_fields': ['title', 'description', 'sortable', 'paginated', 'page_size']
            },
            'metric_card': {
                'name': 'Metric Card',
                'required_fields': ['value_field'],
                'optional_fields': ['title', 'description', 'format', 'trend_field', 'comparison_field']
            },
            'text': {
                'name': 'Text Widget',
                'required_fields': ['content'],
                'optional_fields': ['title', 'markdown']
            },
            'heatmap': {
                'name': 'Heatmap',
                'required_fields': ['x_field', 'y_field', 'value_field'],
                'optional_fields': ['title', 'description', 'color_scheme']
            },
            'funnel': {
                'name': 'Funnel Chart',
                'required_fields': ['stages'],
                'optional_fields': ['title', 'description', 'show_percentages']
            }
        }
    
    @with_connection_retry
    def create_report_config(self, report_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new report configuration for a template"""
        try:
            # Validate dashboard config
            if not self._validate_dashboard_config(report_data.get('dashboard_config', {})):
                logger.error("Invalid dashboard configuration")
                return None
            
            response = self.client.table('query_template_reports').insert(report_data).execute()
            
            if response.data:
                logger.info(f"Created report config for template {report_data['template_id']}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating report config: {e}")
            return None
    
    @with_connection_retry
    def get_template_reports(self, template_id: str) -> List[Dict[str, Any]]:
        """Get all report configurations for a template"""
        try:
            response = self.client.table('query_template_reports')\
                .select('*')\
                .eq('template_id', template_id)\
                .execute()
            
            reports = response.data or []
            logger.info(f"Retrieved {len(reports)} report configs for template {template_id}")
            return reports
        except Exception as e:
            logger.error(f"Error getting template reports: {e}")
            return []
    
    @with_connection_retry
    def update_report_config(self, report_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a report configuration"""
        try:
            # Validate dashboard config if being updated
            if 'dashboard_config' in updates:
                if not self._validate_dashboard_config(updates['dashboard_config']):
                    logger.error("Invalid dashboard configuration")
                    return None
            
            response = self.client.table('query_template_reports')\
                .update(updates)\
                .eq('id', report_id)\
                .execute()
            
            if response.data:
                logger.info(f"Updated report config {report_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating report config {report_id}: {e}")
            return None
    
    @with_connection_retry
    def delete_report_config(self, report_id: str) -> bool:
        """Delete a report configuration"""
        try:
            response = self.client.table('query_template_reports')\
                .delete()\
                .eq('id', report_id)\
                .execute()
            
            logger.info(f"Deleted report config {report_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting report config {report_id}: {e}")
            return False
    
    def generate_dashboard_from_results(
        self, 
        query_results: List[Dict[str, Any]], 
        report_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a dashboard from query results using report configuration"""
        try:
            dashboard_config = report_config.get('dashboard_config', {})
            field_mappings = report_config.get('field_mappings', {})
            default_filters = report_config.get('default_filters', {})
            widget_order = report_config.get('widget_order', [])
            
            # Apply field mappings to results
            mapped_results = self._apply_field_mappings(query_results, field_mappings)
            
            # Generate widgets
            widgets = []
            for widget_config in dashboard_config.get('widgets', []):
                widget = self._generate_widget(mapped_results, widget_config)
                if widget:
                    widgets.append(widget)
            
            # Apply widget ordering if specified
            if widget_order:
                widgets = self._order_widgets(widgets, widget_order)
            
            dashboard = {
                'title': report_config.get('report_name', 'Query Results Dashboard'),
                'widgets': widgets,
                'filters': default_filters,
                'generated_at': datetime.utcnow().isoformat(),
                'row_count': len(query_results),
                'metadata': {
                    'template_id': report_config.get('template_id'),
                    'report_id': report_config.get('id')
                }
            }
            
            return dashboard
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return {
                'error': str(e),
                'widgets': [],
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def _apply_field_mappings(
        self, 
        results: List[Dict[str, Any]], 
        mappings: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Apply field mappings to transform result field names"""
        if not mappings:
            return results
        
        mapped_results = []
        for row in results:
            mapped_row = {}
            for key, value in row.items():
                # Use mapping if exists, otherwise keep original key
                mapped_key = mappings.get(key, key)
                mapped_row[mapped_key] = value
            mapped_results.append(mapped_row)
        
        return mapped_results
    
    def _generate_widget(
        self, 
        data: List[Dict[str, Any]], 
        widget_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a single widget from data and configuration"""
        try:
            widget_type = widget_config.get('type')
            if widget_type not in self.WIDGET_TYPES:
                logger.warning(f"Unknown widget type: {widget_type}")
                return None
            
            widget_def = self.WIDGET_TYPES[widget_type]
            
            # Validate required fields
            for field in widget_def['required_fields']:
                if field not in widget_config:
                    logger.warning(f"Missing required field '{field}' for {widget_type}")
                    return None
            
            # Generate widget based on type
            if widget_type == 'line_chart':
                return self._generate_line_chart(data, widget_config)
            elif widget_type == 'bar_chart':
                return self._generate_bar_chart(data, widget_config)
            elif widget_type == 'pie_chart':
                return self._generate_pie_chart(data, widget_config)
            elif widget_type == 'metric_card':
                return self._generate_metric_card(data, widget_config)
            elif widget_type == 'table':
                return self._generate_table(data, widget_config)
            elif widget_type == 'heatmap':
                return self._generate_heatmap(data, widget_config)
            elif widget_type == 'area_chart':
                return self._generate_area_chart(data, widget_config)
            elif widget_type == 'scatter_plot':
                return self._generate_scatter_plot(data, widget_config)
            elif widget_type == 'funnel':
                return self._generate_funnel(data, widget_config)
            elif widget_type == 'text':
                return self._generate_text_widget(widget_config)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error generating widget: {e}")
            return None
    
    def _generate_line_chart(self, data: List[Dict], config: Dict) -> Dict:
        """Generate line chart widget"""
        x_field = config['x_field']
        y_field = config['y_field']
        series_field = config.get('series_field')
        
        if series_field:
            # Group by series
            series_data = {}
            for row in data:
                series = row.get(series_field, 'default')
                if series not in series_data:
                    series_data[series] = {'x': [], 'y': []}
                series_data[series]['x'].append(row.get(x_field))
                series_data[series]['y'].append(row.get(y_field))
            
            chart_data = {
                'datasets': [
                    {
                        'label': series,
                        'data': [{'x': x, 'y': y} for x, y in zip(values['x'], values['y'])]
                    }
                    for series, values in series_data.items()
                ]
            }
        else:
            # Single series
            chart_data = {
                'labels': [row.get(x_field) for row in data],
                'datasets': [{
                    'label': config.get('title', y_field),
                    'data': [row.get(y_field) for row in data]
                }]
            }
        
        return {
            'type': 'line_chart',
            'title': config.get('title', 'Line Chart'),
            'description': config.get('description'),
            'data': chart_data,
            'options': {
                'responsive': True,
                'maintainAspectRatio': False
            }
        }
    
    def _generate_bar_chart(self, data: List[Dict], config: Dict) -> Dict:
        """Generate bar chart widget"""
        x_field = config['x_field']
        y_field = config['y_field']
        horizontal = config.get('horizontal', False)
        
        chart_data = {
            'labels': [row.get(x_field) for row in data],
            'datasets': [{
                'label': config.get('title', y_field),
                'data': [row.get(y_field) for row in data]
            }]
        }
        
        return {
            'type': 'bar_chart',
            'title': config.get('title', 'Bar Chart'),
            'description': config.get('description'),
            'data': chart_data,
            'options': {
                'indexAxis': 'y' if horizontal else 'x',
                'responsive': True,
                'maintainAspectRatio': False
            }
        }
    
    def _generate_pie_chart(self, data: List[Dict], config: Dict) -> Dict:
        """Generate pie chart widget"""
        label_field = config['label_field']
        value_field = config['value_field']
        
        chart_data = {
            'labels': [row.get(label_field) for row in data],
            'datasets': [{
                'data': [row.get(value_field) for row in data]
            }]
        }
        
        return {
            'type': 'pie_chart',
            'title': config.get('title', 'Pie Chart'),
            'description': config.get('description'),
            'data': chart_data,
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': config.get('show_legend', True)
                    }
                }
            }
        }
    
    def _generate_metric_card(self, data: List[Dict], config: Dict) -> Dict:
        """Generate metric card widget"""
        value_field = config['value_field']
        format_type = config.get('format', 'number')
        
        # Calculate metric value
        if data:
            values = [row.get(value_field, 0) for row in data]
            value = sum(values) if len(values) > 1 else values[0]
        else:
            value = 0
        
        # Format value based on type
        if format_type == 'currency':
            formatted_value = f"${value:,.2f}"
        elif format_type == 'percentage':
            formatted_value = f"{value:.2f}%"
        else:
            formatted_value = f"{value:,.0f}"
        
        # Calculate trend if specified
        trend = None
        if config.get('trend_field') and len(data) > 1:
            trend_values = [row.get(config['trend_field'], 0) for row in data]
            if len(trend_values) >= 2:
                change = trend_values[-1] - trend_values[-2]
                trend = {
                    'direction': 'up' if change > 0 else 'down' if change < 0 else 'flat',
                    'value': abs(change),
                    'percentage': (change / trend_values[-2] * 100) if trend_values[-2] != 0 else 0
                }
        
        return {
            'type': 'metric_card',
            'title': config.get('title', value_field),
            'description': config.get('description'),
            'value': formatted_value,
            'raw_value': value,
            'trend': trend
        }
    
    def _generate_table(self, data: List[Dict], config: Dict) -> Dict:
        """Generate table widget"""
        columns = config['columns']
        
        # If columns is a list of strings, convert to column definitions
        if columns and isinstance(columns[0], str):
            columns = [{'field': col, 'header': col} for col in columns]
        
        return {
            'type': 'table',
            'title': config.get('title', 'Data Table'),
            'description': config.get('description'),
            'columns': columns,
            'data': data,
            'options': {
                'sortable': config.get('sortable', True),
                'paginated': config.get('paginated', True),
                'pageSize': config.get('page_size', 10)
            }
        }
    
    def _generate_heatmap(self, data: List[Dict], config: Dict) -> Dict:
        """Generate heatmap widget"""
        x_field = config['x_field']
        y_field = config['y_field']
        value_field = config['value_field']
        
        # Create matrix data
        x_values = list(set(row.get(x_field) for row in data))
        y_values = list(set(row.get(y_field) for row in data))
        
        matrix = []
        for y in y_values:
            row_data = []
            for x in x_values:
                # Find value for this x,y combination
                value = 0
                for row in data:
                    if row.get(x_field) == x and row.get(y_field) == y:
                        value = row.get(value_field, 0)
                        break
                row_data.append(value)
            matrix.append(row_data)
        
        return {
            'type': 'heatmap',
            'title': config.get('title', 'Heatmap'),
            'description': config.get('description'),
            'data': {
                'x_labels': x_values,
                'y_labels': y_values,
                'values': matrix
            },
            'options': {
                'colorScheme': config.get('color_scheme', 'blues')
            }
        }
    
    def _generate_area_chart(self, data: List[Dict], config: Dict) -> Dict:
        """Generate area chart widget"""
        # Similar to line chart but with area fill
        line_chart = self._generate_line_chart(data, config)
        line_chart['type'] = 'area_chart'
        line_chart['options']['fill'] = True
        line_chart['options']['stacked'] = config.get('stacked', False)
        return line_chart
    
    def _generate_scatter_plot(self, data: List[Dict], config: Dict) -> Dict:
        """Generate scatter plot widget"""
        x_field = config['x_field']
        y_field = config['y_field']
        size_field = config.get('size_field')
        color_field = config.get('color_field')
        
        points = []
        for row in data:
            point = {
                'x': row.get(x_field),
                'y': row.get(y_field)
            }
            if size_field:
                point['r'] = row.get(size_field, 5)
            if color_field:
                point['color'] = row.get(color_field)
            points.append(point)
        
        return {
            'type': 'scatter_plot',
            'title': config.get('title', 'Scatter Plot'),
            'description': config.get('description'),
            'data': {
                'datasets': [{
                    'label': config.get('title', 'Data'),
                    'data': points
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False
            }
        }
    
    def _generate_funnel(self, data: List[Dict], config: Dict) -> Dict:
        """Generate funnel chart widget"""
        stages = config['stages']
        
        # If stages is a list of field names, extract values
        if isinstance(stages[0], str):
            funnel_data = []
            for stage in stages:
                value = sum(row.get(stage, 0) for row in data)
                funnel_data.append({'stage': stage, 'value': value})
        else:
            funnel_data = stages
        
        # Calculate percentages
        if funnel_data and config.get('show_percentages', True):
            max_value = funnel_data[0]['value']
            for item in funnel_data:
                item['percentage'] = (item['value'] / max_value * 100) if max_value > 0 else 0
        
        return {
            'type': 'funnel',
            'title': config.get('title', 'Funnel Chart'),
            'description': config.get('description'),
            'data': funnel_data,
            'options': {
                'showPercentages': config.get('show_percentages', True)
            }
        }
    
    def _generate_text_widget(self, config: Dict) -> Dict:
        """Generate text widget"""
        return {
            'type': 'text',
            'title': config.get('title'),
            'content': config['content'],
            'markdown': config.get('markdown', False)
        }
    
    def _order_widgets(self, widgets: List[Dict], order: List[str]) -> List[Dict]:
        """Order widgets according to specified order"""
        ordered = []
        widget_map = {w.get('id', w.get('title')): w for w in widgets}
        
        for widget_id in order:
            if widget_id in widget_map:
                ordered.append(widget_map[widget_id])
                del widget_map[widget_id]
        
        # Add any remaining widgets not in order
        ordered.extend(widget_map.values())
        
        return ordered
    
    def _validate_dashboard_config(self, config: Dict) -> bool:
        """Validate dashboard configuration"""
        if not config:
            return True  # Empty config is valid
        
        widgets = config.get('widgets', [])
        if not isinstance(widgets, list):
            return False
        
        for widget in widgets:
            if not isinstance(widget, dict):
                return False
            if 'type' not in widget:
                return False
            if widget['type'] not in self.WIDGET_TYPES:
                return False
        
        return True
    
    def validate_field_mappings(
        self, 
        query_results: List[Dict[str, Any]], 
        field_mappings: Dict[str, str]
    ) -> Dict[str, str]:
        """Validate field mappings against actual query results"""
        if not query_results or not field_mappings:
            return {}
        
        # Get available fields from first result row
        available_fields = set(query_results[0].keys())
        
        # Filter mappings to only include available fields
        valid_mappings = {}
        for source_field, target_field in field_mappings.items():
            if source_field in available_fields:
                valid_mappings[source_field] = target_field
            else:
                logger.warning(f"Field '{source_field}' not found in query results")
        
        return valid_mappings
    
    def get_widget_types(self) -> Dict[str, Dict[str, Any]]:
        """Get available widget types and their configurations"""
        return self.WIDGET_TYPES
    
    def suggest_widgets_from_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest appropriate widgets based on data structure"""
        if not data:
            return []
        
        suggestions = []
        fields = list(data[0].keys())
        
        # Analyze field types
        numeric_fields = []
        date_fields = []
        text_fields = []
        
        for field in fields:
            sample_value = data[0][field]
            if isinstance(sample_value, (int, float)):
                numeric_fields.append(field)
            elif isinstance(sample_value, str):
                if any(date_pattern in field.lower() for date_pattern in ['date', 'time', 'day', 'month', 'year']):
                    date_fields.append(field)
                else:
                    text_fields.append(field)
        
        # Suggest widgets based on field analysis
        
        # Line chart for time series
        if date_fields and numeric_fields:
            suggestions.append({
                'type': 'line_chart',
                'config': {
                    'x_field': date_fields[0],
                    'y_field': numeric_fields[0],
                    'title': f'{numeric_fields[0]} Over Time'
                }
            })
        
        # Bar chart for categories
        if text_fields and numeric_fields:
            suggestions.append({
                'type': 'bar_chart',
                'config': {
                    'x_field': text_fields[0],
                    'y_field': numeric_fields[0],
                    'title': f'{numeric_fields[0]} by {text_fields[0]}'
                }
            })
        
        # Metric cards for numeric summaries
        for field in numeric_fields[:3]:  # Limit to 3 metric cards
            suggestions.append({
                'type': 'metric_card',
                'config': {
                    'value_field': field,
                    'title': field.replace('_', ' ').title()
                }
            })
        
        # Table for detailed view
        suggestions.append({
            'type': 'table',
            'config': {
                'columns': fields[:10],  # Limit to 10 columns
                'title': 'Data Table',
                'paginated': True
            }
        })
        
        return suggestions


# Create singleton instance
template_report_service = TemplateReportService()