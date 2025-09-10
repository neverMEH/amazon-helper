# Dashboard System

## Overview

The Dashboard System provides comprehensive data visualization and reporting capabilities for RecomAMP users. It enables creation of interactive dashboards with multiple widget types, real-time data updates, sharing capabilities, and automated data collection integration.

## Key Components

### Backend Services
- `amc_manager/services/dashboard_service.py` - Dashboard CRUD and management
- `amc_manager/services/widget_service.py` - Widget configuration and data processing
- `amc_manager/services/chart_data_service.py` - Data transformation for charts
- `amc_manager/api/supabase/dashboards.py` - Dashboard API endpoints

### Frontend Components
- `frontend/src/pages/Dashboards.tsx` - Dashboard list and management
- `frontend/src/pages/DashboardDetail.tsx` - Individual dashboard view
- `frontend/src/components/DashboardBuilder.tsx` - Drag-and-drop dashboard editor
- `frontend/src/components/widgets/` - Various widget types
- `frontend/src/components/ChartRenderer.tsx` - Chart.js integration

### Database Tables
- `dashboards` - Dashboard metadata and configuration
- `dashboard_widgets` - Widget definitions and layout
- `dashboard_shares` - Sharing permissions
- `report_data_collections` - Data source integration

## Dashboard Data Model

### Dashboard Structure
```python
# dashboards table schema
class Dashboard:
    id: UUID                    # Dashboard identifier
    name: str                  # Dashboard name
    description: str           # Dashboard description
    
    # Ownership and Access
    user_id: UUID              # Dashboard creator
    organization_id: UUID      # Organization (for multi-tenant)
    
    # Layout Configuration
    layout_config: dict        # Grid layout settings
    theme: str                 # Color theme
    refresh_interval: int      # Auto-refresh in seconds
    
    # Data Sources
    default_instance_id: UUID  # Default AMC instance
    date_range_default: dict   # Default date range settings
    
    # Status and Sharing
    is_public: bool            # Public visibility
    is_archived: bool          # Archived status
    tags: List[str]           # Searchable tags
    
    # Analytics
    view_count: int           # Number of views
    last_viewed_at: datetime  # Last view timestamp
    
    # Audit Fields
    created_at: datetime
    updated_at: datetime
```

### Widget Structure
```python
# dashboard_widgets table schema
class DashboardWidget:
    id: UUID                   # Widget identifier
    dashboard_id: UUID         # FK to dashboards
    
    # Widget Configuration
    widget_type: str          # line, bar, pie, table, metric_card, etc.
    title: str               # Widget title
    description: str         # Widget description
    
    # Layout Properties
    position_x: int          # Grid X position
    position_y: int          # Grid Y position
    width: int               # Grid width units
    height: int              # Grid height units
    
    # Data Configuration
    data_source: str         # workflow, collection, manual
    data_source_id: UUID     # Reference to data source
    query_config: dict       # Query parameters and filters
    
    # Visualization Settings
    chart_config: dict       # Chart.js configuration
    color_scheme: str        # Color palette
    show_legend: bool        # Legend visibility
    show_labels: bool        # Data labels
    
    # Refresh Settings
    auto_refresh: bool       # Auto-refresh enabled
    refresh_interval: int    # Refresh interval in seconds
    cache_duration: int      # Cache data for N seconds
    
    # Status
    is_active: bool          # Widget enabled
    has_error: bool          # Error state
    error_message: str       # Last error message
    
    # Audit Fields
    created_at: datetime
    updated_at: datetime
    last_refreshed_at: datetime
```

## Dashboard Service Implementation

### Dashboard Management
```python
# dashboard_service.py
class DashboardService(DatabaseService):
    def __init__(self):
        super().__init__()
        self.widget_service = WidgetService()
        self.chart_data_service = ChartDataService()
    
    async def create_dashboard(self, user_id: str, dashboard_data: dict) -> dict:
        """Create new dashboard"""
        
        dashboard = self.db.table('dashboards').insert({
            'name': dashboard_data['name'],
            'description': dashboard_data.get('description'),
            'user_id': user_id,
            'organization_id': dashboard_data.get('organization_id'),
            'layout_config': dashboard_data.get('layout_config', {
                'columns': 12,
                'row_height': 60,
                'margin': [10, 10]
            }),
            'theme': dashboard_data.get('theme', 'default'),
            'refresh_interval': dashboard_data.get('refresh_interval', 300), # 5 minutes
            'default_instance_id': dashboard_data.get('default_instance_id'),
            'date_range_default': dashboard_data.get('date_range_default', {
                'type': 'relative',
                'value': '30d'
            }),
            'is_public': dashboard_data.get('is_public', False),
            'tags': dashboard_data.get('tags', []),
            'view_count': 0,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).execute()
        
        dashboard_id = dashboard.data[0]['id']
        
        # Create initial widgets if provided
        if 'widgets' in dashboard_data:
            for widget_data in dashboard_data['widgets']:
                await self.widget_service.create_widget(dashboard_id, widget_data)
        
        return dashboard.data[0]
    
    async def get_dashboard_with_widgets(self, dashboard_id: str, user_id: str) -> dict:
        """Get dashboard with all widgets and data"""
        
        # Verify access
        await self.verify_dashboard_access(dashboard_id, user_id)
        
        # Get dashboard
        dashboard = self.db.table('dashboards')\
            .select('*')\
            .eq('id', dashboard_id)\
            .execute()
        
        if not dashboard.data:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        dashboard_data = dashboard.data[0]
        
        # Get widgets
        widgets = self.db.table('dashboard_widgets')\
            .select('*')\
            .eq('dashboard_id', dashboard_id)\
            .eq('is_active', True)\
            .order('position_y, position_x')\
            .execute()
        
        # Get data for each widget
        widget_data = []
        for widget in widgets.data:
            try:
                data = await self.get_widget_data(widget['id'], user_id)
                widget_data.append({
                    **widget,
                    'data': data
                })
            except Exception as e:
                logger.error(f"Failed to load data for widget {widget['id']}: {e}")
                widget_data.append({
                    **widget,
                    'data': None,
                    'error': str(e)
                })
        
        # Update view count
        self.db.table('dashboards')\
            .update({
                'view_count': dashboard_data['view_count'] + 1,
                'last_viewed_at': datetime.utcnow().isoformat()
            })\
            .eq('id', dashboard_id)\
            .execute()
        
        return {
            **dashboard_data,
            'widgets': widget_data
        }
    
    async def verify_dashboard_access(self, dashboard_id: str, user_id: str):
        """Verify user has access to dashboard"""
        
        # Check ownership
        dashboard = self.db.table('dashboards')\
            .select('user_id, is_public')\
            .eq('id', dashboard_id)\
            .execute()
        
        if not dashboard.data:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        dashboard_info = dashboard.data[0]
        
        # Owner has access
        if dashboard_info['user_id'] == user_id:
            return True
        
        # Public dashboards are accessible
        if dashboard_info['is_public']:
            return True
        
        # Check if dashboard is shared with user
        shared_access = self.db.table('dashboard_shares')\
            .select('permission')\
            .eq('dashboard_id', dashboard_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if shared_access.data:
            return True
        
        raise HTTPException(status_code=403, detail="Access denied")
    
    async def update_dashboard_layout(self, dashboard_id: str, user_id: str, 
                                    layout_updates: List[dict]) -> dict:
        """Update widget positions and sizes"""
        
        await self.verify_dashboard_access(dashboard_id, user_id)
        
        # Update each widget's layout
        for update in layout_updates:
            widget_id = update['widget_id']
            
            self.db.table('dashboard_widgets')\
                .update({
                    'position_x': update['x'],
                    'position_y': update['y'],
                    'width': update['width'],
                    'height': update['height'],
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .eq('id', widget_id)\
                .eq('dashboard_id', dashboard_id)\
                .execute()
        
        # Update dashboard timestamp
        self.db.table('dashboards')\
            .update({'updated_at': datetime.utcnow().isoformat()})\
            .eq('id', dashboard_id)\
            .execute()
        
        return {'updated': len(layout_updates)}
```

## Widget System

### Widget Types and Configuration
```python
# widget_service.py
class WidgetService(DatabaseService):
    WIDGET_TYPES = {
        'line': {
            'name': 'Line Chart',
            'description': 'Time series data visualization',
            'required_fields': ['x_field', 'y_field'],
            'supports_multiple_series': True
        },
        'bar': {
            'name': 'Bar Chart', 
            'description': 'Categorical data comparison',
            'required_fields': ['category_field', 'value_field'],
            'supports_multiple_series': True
        },
        'pie': {
            'name': 'Pie Chart',
            'description': 'Part-to-whole relationships',
            'required_fields': ['label_field', 'value_field'],
            'supports_multiple_series': False
        },
        'area': {
            'name': 'Area Chart',
            'description': 'Stacked time series data',
            'required_fields': ['x_field', 'y_field'],
            'supports_multiple_series': True
        },
        'scatter': {
            'name': 'Scatter Plot',
            'description': 'Relationship between two variables',
            'required_fields': ['x_field', 'y_field'],
            'supports_bubble': True
        },
        'table': {
            'name': 'Data Table',
            'description': 'Tabular data display',
            'required_fields': ['columns'],
            'supports_pagination': True
        },
        'metric_card': {
            'name': 'Metric Card',
            'description': 'Single KPI display',
            'required_fields': ['value_field'],
            'supports_trend': True
        },
        'text': {
            'name': 'Text Widget',
            'description': 'Static text or markdown content',
            'required_fields': ['content'],
            'supports_markdown': True
        },
        'heatmap': {
            'name': 'Heat Map',
            'description': 'Data intensity visualization',
            'required_fields': ['x_field', 'y_field', 'intensity_field'],
            'supports_color_scale': True
        },
        'funnel': {
            'name': 'Funnel Chart',
            'description': 'Conversion funnel visualization',
            'required_fields': ['stage_field', 'value_field'],
            'supports_conversion_rates': True
        }
    }
    
    async def create_widget(self, dashboard_id: str, widget_data: dict) -> dict:
        """Create new dashboard widget"""
        
        # Validate widget type
        widget_type = widget_data.get('widget_type')
        if widget_type not in self.WIDGET_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid widget type: {widget_type}"
            )
        
        # Validate required fields
        type_config = self.WIDGET_TYPES[widget_type]
        required_fields = type_config.get('required_fields', [])
        chart_config = widget_data.get('chart_config', {})
        
        missing_fields = [field for field in required_fields if field not in chart_config]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields for {widget_type}: {missing_fields}"
            )
        
        # Create widget
        widget = self.db.table('dashboard_widgets').insert({
            'dashboard_id': dashboard_id,
            'widget_type': widget_type,
            'title': widget_data['title'],
            'description': widget_data.get('description'),
            'position_x': widget_data.get('position_x', 0),
            'position_y': widget_data.get('position_y', 0),
            'width': widget_data.get('width', 4),
            'height': widget_data.get('height', 4),
            'data_source': widget_data.get('data_source', 'workflow'),
            'data_source_id': widget_data.get('data_source_id'),
            'query_config': widget_data.get('query_config', {}),
            'chart_config': chart_config,
            'color_scheme': widget_data.get('color_scheme', 'default'),
            'show_legend': widget_data.get('show_legend', True),
            'show_labels': widget_data.get('show_labels', True),
            'auto_refresh': widget_data.get('auto_refresh', False),
            'refresh_interval': widget_data.get('refresh_interval', 300),
            'cache_duration': widget_data.get('cache_duration', 60),
            'is_active': True,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).execute()
        
        return widget.data[0]
    
    async def get_widget_data(self, widget_id: str, user_id: str) -> dict:
        """Get processed data for widget"""
        
        # Get widget configuration
        widget = self.db.table('dashboard_widgets')\
            .select('*')\
            .eq('id', widget_id)\
            .execute()
        
        if not widget.data:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        widget_config = widget.data[0]
        
        # Check cache first
        cached_data = await self.get_cached_widget_data(widget_id)
        if cached_data:
            return cached_data
        
        # Fetch fresh data based on data source
        data_source = widget_config['data_source']
        data_source_id = widget_config['data_source_id']
        
        if data_source == 'workflow':
            raw_data = await self.get_workflow_data(data_source_id, user_id)
        elif data_source == 'collection':
            raw_data = await self.get_collection_data(data_source_id, user_id)
        elif data_source == 'manual':
            raw_data = widget_config.get('manual_data', [])
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported data source: {data_source}"
            )
        
        # Transform data for chart
        chart_data = await self.transform_data_for_chart(
            raw_data,
            widget_config['widget_type'],
            widget_config['chart_config']
        )
        
        # Cache processed data
        await self.cache_widget_data(widget_id, chart_data, widget_config['cache_duration'])
        
        # Update last refresh time
        self.db.table('dashboard_widgets')\
            .update({'last_refreshed_at': datetime.utcnow().isoformat()})\
            .eq('id', widget_id)\
            .execute()
        
        return chart_data
```

### Data Transformation Service
```python
# chart_data_service.py
class ChartDataService:
    def __init__(self):
        self.color_palettes = {
            'default': ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6'],
            'blue': ['#1E40AF', '#3B82F6', '#60A5FA', '#93C5FD', '#DBEAFE'],
            'green': ['#065F46', '#10B981', '#34D399', '#6EE7B7', '#A7F3D0'],
            'warm': ['#DC2626', '#EA580C', '#D97706', '#CA8A04', '#65A30D']
        }
    
    async def transform_data_for_chart(self, raw_data: List[dict], 
                                     widget_type: str, chart_config: dict) -> dict:
        """Transform raw data into Chart.js format"""
        
        if widget_type == 'line':
            return await self.transform_for_line_chart(raw_data, chart_config)
        elif widget_type == 'bar':
            return await self.transform_for_bar_chart(raw_data, chart_config)
        elif widget_type == 'pie':
            return await self.transform_for_pie_chart(raw_data, chart_config)
        elif widget_type == 'table':
            return await self.transform_for_table(raw_data, chart_config)
        elif widget_type == 'metric_card':
            return await self.transform_for_metric_card(raw_data, chart_config)
        else:
            raise ValueError(f"Unsupported widget type: {widget_type}")
    
    async def transform_for_line_chart(self, raw_data: List[dict], 
                                     config: dict) -> dict:
        """Transform data for line chart"""
        
        x_field = config['x_field']
        y_field = config['y_field']
        series_field = config.get('series_field')
        
        if series_field:
            # Multiple series
            series_data = {}
            
            for row in raw_data:
                series_key = row[series_field]
                if series_key not in series_data:
                    series_data[series_key] = []
                
                series_data[series_key].append({
                    'x': row[x_field],
                    'y': row[y_field]
                })
            
            datasets = []
            colors = self.color_palettes['default']
            
            for i, (series_name, points) in enumerate(series_data.items()):
                datasets.append({
                    'label': series_name,
                    'data': points,
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': colors[i % len(colors)] + '20',  # 20% opacity
                    'tension': 0.1
                })
            
            return {
                'type': 'line',
                'data': {'datasets': datasets},
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {'display': config.get('show_legend', True)}
                    },
                    'scales': {
                        'x': {'type': 'time' if self.is_date_field(raw_data, x_field) else 'linear'},
                        'y': {'beginAtZero': config.get('begin_at_zero', False)}
                    }
                }
            }
        else:
            # Single series
            data_points = [{'x': row[x_field], 'y': row[y_field]} for row in raw_data]
            
            return {
                'type': 'line',
                'data': {
                    'datasets': [{
                        'label': config.get('label', y_field),
                        'data': data_points,
                        'borderColor': self.color_palettes['default'][0],
                        'backgroundColor': self.color_palettes['default'][0] + '20',
                        'tension': 0.1
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {'display': config.get('show_legend', True)}
                    },
                    'scales': {
                        'x': {'type': 'time' if self.is_date_field(raw_data, x_field) else 'linear'},
                        'y': {'beginAtZero': config.get('begin_at_zero', False)}
                    }
                }
            }
    
    async def transform_for_metric_card(self, raw_data: List[dict], 
                                      config: dict) -> dict:
        """Transform data for metric card widget"""
        
        value_field = config['value_field']
        
        if not raw_data:
            return {'value': 0, 'trend': None, 'status': 'no_data'}
        
        # Get latest value
        current_value = raw_data[-1][value_field] if raw_data else 0
        
        # Calculate trend if we have multiple data points
        trend = None
        if len(raw_data) >= 2:
            previous_value = raw_data[-2][value_field]
            if previous_value != 0:
                trend = ((current_value - previous_value) / previous_value) * 100
        
        # Format value based on field type
        formatted_value = self.format_metric_value(current_value, config)
        
        return {
            'value': formatted_value,
            'raw_value': current_value,
            'trend': trend,
            'trend_direction': 'up' if trend and trend > 0 else 'down' if trend and trend < 0 else 'flat',
            'status': 'good' if trend and trend > 0 else 'bad' if trend and trend < -5 else 'neutral',
            'label': config.get('label', value_field),
            'format': config.get('format', 'number')
        }
    
    def format_metric_value(self, value: float, config: dict) -> str:
        """Format metric value based on configuration"""
        
        format_type = config.get('format', 'number')
        
        if format_type == 'currency':
            return f"${value:,.2f}"
        elif format_type == 'percentage':
            return f"{value:.1f}%"
        elif format_type == 'integer':
            return f"{int(value):,}"
        elif format_type == 'decimal':
            return f"{value:,.2f}"
        else:
            return str(value)
    
    def is_date_field(self, data: List[dict], field: str) -> bool:
        """Check if field contains date values"""
        if not data or field not in data[0]:
            return False
        
        sample_value = data[0][field]
        
        # Try to parse as date
        try:
            datetime.fromisoformat(str(sample_value))
            return True
        except:
            return False
```

## Frontend Dashboard Implementation

### Dashboard Builder Component
```typescript
// DashboardBuilder.tsx - Drag-and-drop dashboard editor
import { Responsive, WidthProvider } from 'react-grid-layout';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);
const ResponsiveGridLayout = WidthProvider(Responsive);

interface DashboardBuilderProps {
  dashboard: Dashboard;
  onLayoutChange: (layout: Layout[]) => void;
  onWidgetUpdate: (widgetId: string, updates: Partial<Widget>) => void;
}

const DashboardBuilder: React.FC<DashboardBuilderProps> = ({
  dashboard,
  onLayoutChange,
  onWidgetUpdate
}) => {
  const [widgets, setWidgets] = useState(dashboard.widgets || []);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  
  // Convert widgets to grid layout format
  const layoutFromWidgets = widgets.map(widget => ({
    i: widget.id,
    x: widget.position_x,
    y: widget.position_y,
    w: widget.width,
    h: widget.height,
    minW: 2,
    minH: 2
  }));
  
  const handleLayoutChange = (layout: Layout[]) => {
    // Update widget positions
    const updatedWidgets = widgets.map(widget => {
      const layoutItem = layout.find(item => item.i === widget.id);
      if (layoutItem) {
        return {
          ...widget,
          position_x: layoutItem.x,
          position_y: layoutItem.y,
          width: layoutItem.w,
          height: layoutItem.h
        };
      }
      return widget;
    });
    
    setWidgets(updatedWidgets);
    onLayoutChange(layout);
  };
  
  const addWidget = (widgetType: string) => {
    const newWidget: Partial<Widget> = {
      id: `temp-${Date.now()}`,
      widget_type: widgetType,
      title: `New ${widgetType} Widget`,
      position_x: 0,
      position_y: 0,
      width: 4,
      height: 4,
      chart_config: getDefaultChartConfig(widgetType)
    };
    
    setWidgets([...widgets, newWidget as Widget]);
  };
  
  const removeWidget = (widgetId: string) => {
    setWidgets(widgets.filter(w => w.id !== widgetId));
  };
  
  return (
    <div className="dashboard-builder">
      {/* Dashboard Header */}
      <div className="flex justify-between items-center p-4 bg-white border-b">
        <div>
          <h1 className="text-2xl font-semibold">{dashboard.name}</h1>
          <p className="text-gray-600">{dashboard.description}</p>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className={`px-4 py-2 rounded-md ${
              isEditing 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            {isEditing ? 'Save Changes' : 'Edit Dashboard'}
          </button>
          
          {isEditing && (
            <WidgetTypeSelector onAddWidget={addWidget} />
          )}
        </div>
      </div>
      
      {/* Grid Layout */}
      <div className="p-4">
        <ResponsiveGridLayout
          className="layout"
          layouts={{ lg: layoutFromWidgets }}
          breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
          cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
          rowHeight={60}
          isDraggable={isEditing}
          isResizable={isEditing}
          onLayoutChange={handleLayoutChange}
          margin={[10, 10]}
        >
          {widgets.map((widget) => (
            <div key={widget.id} className="widget-container">
              <WidgetRenderer
                widget={widget}
                isEditing={isEditing}
                isSelected={selectedWidget === widget.id}
                onSelect={() => setSelectedWidget(widget.id)}
                onUpdate={(updates) => onWidgetUpdate(widget.id, updates)}
                onRemove={() => removeWidget(widget.id)}
              />
            </div>
          ))}
        </ResponsiveGridLayout>
      </div>
      
      {/* Widget Configuration Panel */}
      {isEditing && selectedWidget && (
        <WidgetConfigPanel
          widget={widgets.find(w => w.id === selectedWidget)!}
          onUpdate={(updates) => onWidgetUpdate(selectedWidget, updates)}
          onClose={() => setSelectedWidget(null)}
        />
      )}
    </div>
  );
};
```

### Widget Renderer Component
```typescript
// WidgetRenderer.tsx - Individual widget display
interface WidgetRendererProps {
  widget: Widget;
  isEditing: boolean;
  isSelected: boolean;
  onSelect: () => void;
  onUpdate: (updates: Partial<Widget>) => void;
  onRemove: () => void;
}

const WidgetRenderer: React.FC<WidgetRendererProps> = ({
  widget,
  isEditing,
  isSelected,
  onSelect,
  onUpdate,
  onRemove
}) => {
  const { data: widgetData, isLoading, error } = useQuery({
    queryKey: ['widget-data', widget.id],
    queryFn: () => dashboardService.getWidgetData(widget.id),
    refetchInterval: widget.auto_refresh ? widget.refresh_interval * 1000 : false,
    enabled: !isEditing // Don't fetch data while editing
  });
  
  const renderWidget = () => {
    if (isLoading) {
      return <WidgetSkeleton />;
    }
    
    if (error) {
      return (
        <div className="flex items-center justify-center h-full text-red-600">
          <div className="text-center">
            <div className="text-2xl mb-2">⚠️</div>
            <div>Failed to load widget data</div>
            <div className="text-sm text-gray-500">{error.message}</div>
          </div>
        </div>
      );
    }
    
    switch (widget.widget_type) {
      case 'line':
      case 'bar':
      case 'pie':
      case 'area':
        return <ChartWidget widget={widget} data={widgetData} />;
      
      case 'table':
        return <TableWidget widget={widget} data={widgetData} />;
      
      case 'metric_card':
        return <MetricCardWidget widget={widget} data={widgetData} />;
      
      case 'text':
        return <TextWidget widget={widget} />;
      
      default:
        return <div>Unsupported widget type: {widget.widget_type}</div>;
    }
  };
  
  return (
    <div
      className={`widget ${isSelected ? 'selected' : ''} ${isEditing ? 'editing' : ''}`}
      onClick={isEditing ? onSelect : undefined}
    >
      {/* Widget Header */}
      <div className="widget-header">
        <h3 className="widget-title">{widget.title}</h3>
        
        {isEditing && (
          <div className="widget-controls">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              className="text-red-600 hover:text-red-800"
            >
              ×
            </button>
          </div>
        )}
        
        {!isEditing && widget.last_refreshed_at && (
          <div className="text-xs text-gray-500">
            Updated {formatDistanceToNow(new Date(widget.last_refreshed_at))} ago
          </div>
        )}
      </div>
      
      {/* Widget Content */}
      <div className="widget-content">
        {renderWidget()}
      </div>
    </div>
  );
};
```

## Dashboard Sharing System

### Sharing Service
```python
async def share_dashboard(self, dashboard_id: str, owner_id: str, 
                        share_data: dict) -> dict:
    """Share dashboard with other users"""
    
    # Verify ownership
    dashboard = self.db.table('dashboards')\
        .select('user_id')\
        .eq('id', dashboard_id)\
        .execute()
    
    if not dashboard.data or dashboard.data[0]['user_id'] != owner_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create share record
    share = self.db.table('dashboard_shares').insert({
        'dashboard_id': dashboard_id,
        'user_id': share_data['user_id'],
        'permission': share_data.get('permission', 'view'), # view, edit
        'shared_by': owner_id,
        'expires_at': share_data.get('expires_at'),
        'created_at': datetime.utcnow().isoformat()
    }).execute()
    
    # Send notification (if enabled)
    if share_data.get('send_notification', True):
        await self.send_share_notification(share.data[0])
    
    return share.data[0]
```

## Performance Optimization

### Widget Caching Strategy
```python
async def cache_widget_data(self, widget_id: str, data: dict, 
                          cache_duration: int = 300):
    """Cache widget data for performance"""
    
    cache_key = f"widget_data:{widget_id}"
    cache_data = {
        'data': data,
        'cached_at': datetime.utcnow().isoformat(),
        'expires_at': (datetime.utcnow() + timedelta(seconds=cache_duration)).isoformat()
    }
    
    # Store in Redis or similar cache
    await self.redis_client.setex(
        cache_key, 
        cache_duration, 
        json.dumps(cache_data)
    )

async def get_cached_widget_data(self, widget_id: str) -> dict:
    """Retrieve cached widget data"""
    
    cache_key = f"widget_data:{widget_id}"
    cached = await self.redis_client.get(cache_key)
    
    if cached:
        cache_data = json.loads(cached)
        
        # Check if cache is still valid
        expires_at = datetime.fromisoformat(cache_data['expires_at'])
        if datetime.utcnow() < expires_at:
            return cache_data['data']
    
    return None
```