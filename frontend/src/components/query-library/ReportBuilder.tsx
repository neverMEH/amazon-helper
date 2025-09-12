import { useState, useCallback, useRef } from 'react';
import { 
  Plus, Save, X, Layout, BarChart3, LineChart, PieChart, 
  Table, Hash, Type, Grid3x3, Move,
  Trash2, Copy, Eye, EyeOff
} from 'lucide-react';
import { toast } from 'react-hot-toast';

interface Widget {
  id: string;
  type: 'chart' | 'metric' | 'table' | 'text';
  chartType?: 'line' | 'bar' | 'pie' | 'area' | 'scatter';
  title: string;
  dataSource: string;
  config: {
    x: number;
    y: number;
    w: number;
    h: number;
    minW?: number;
    minH?: number;
    maxW?: number;
    maxH?: number;
  };
  settings: {
    xAxis?: string;
    yAxis?: string;
    groupBy?: string;
    aggregation?: 'sum' | 'avg' | 'count' | 'min' | 'max';
    filters?: Array<{ field: string; operator: string; value: any }>;
    color?: string;
    showLegend?: boolean;
    showGrid?: boolean;
  };
  isVisible: boolean;
}

interface ReportBuilderProps {
  columns?: string[];
  templateId?: string;
  onSave?: (dashboard: DashboardConfig) => Promise<void>;
  onCancel?: () => void;
}

interface DashboardConfig {
  name: string;
  description?: string;
  widgets: Widget[];
  layout: {
    cols: number;
    rowHeight: number;
    margin: [number, number];
  };
}

const WIDGET_TYPES = [
  { id: 'line', label: 'Line Chart', icon: LineChart, type: 'chart', chartType: 'line' },
  { id: 'bar', label: 'Bar Chart', icon: BarChart3, type: 'chart', chartType: 'bar' },
  { id: 'pie', label: 'Pie Chart', icon: PieChart, type: 'chart', chartType: 'pie' },
  { id: 'metric', label: 'Metric Card', icon: Hash, type: 'metric' },
  { id: 'table', label: 'Data Table', icon: Table, type: 'table' },
  { id: 'text', label: 'Text Block', icon: Type, type: 'text' },
];

const GRID_COLS = 12;
const ROW_HEIGHT = 80;

export default function ReportBuilder({ 
  columns = [], 
  onSave, 
  onCancel 
}: ReportBuilderProps) {
  const [dashboardName, setDashboardName] = useState('');
  const [dashboardDescription, setDashboardDescription] = useState('');
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [draggedWidget, setDraggedWidget] = useState<Widget | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isPreview, setIsPreview] = useState(false);
  const gridRef = useRef<HTMLDivElement>(null);

  // Add new widget
  const addWidget = (widgetType: typeof WIDGET_TYPES[0]) => {
    const newWidget: Widget = {
      id: `widget-${Date.now()}`,
      type: widgetType.type as Widget['type'],
      chartType: widgetType.chartType as Widget['chartType'],
      title: `New ${widgetType.label}`,
      dataSource: 'query_results',
      config: {
        x: 0,
        y: findNextAvailableRow(),
        w: widgetType.type === 'metric' ? 3 : 6,
        h: widgetType.type === 'metric' ? 2 : 4,
        minW: widgetType.type === 'metric' ? 2 : 3,
        minH: widgetType.type === 'metric' ? 1 : 2,
      },
      settings: {
        aggregation: 'sum',
        showLegend: true,
        showGrid: true,
      },
      isVisible: true,
    };

    setWidgets([...widgets, newWidget]);
    setSelectedWidget(newWidget.id);
  };

  // Find next available row
  const findNextAvailableRow = (): number => {
    if (widgets.length === 0) return 0;
    const maxY = Math.max(...widgets.map(w => w.config.y + w.config.h));
    return maxY;
  };

  // Update widget config
  const updateWidget = (widgetId: string, updates: Partial<Widget>) => {
    setWidgets(widgets.map(w => 
      w.id === widgetId ? { ...w, ...updates } : w
    ));
  };

  // Delete widget
  const deleteWidget = (widgetId: string) => {
    setWidgets(widgets.filter(w => w.id !== widgetId));
    if (selectedWidget === widgetId) {
      setSelectedWidget(null);
    }
  };

  // Duplicate widget
  const duplicateWidget = (widgetId: string) => {
    const widget = widgets.find(w => w.id === widgetId);
    if (widget) {
      const newWidget: Widget = {
        ...widget,
        id: `widget-${Date.now()}`,
        title: `${widget.title} (Copy)`,
        config: {
          ...widget.config,
          x: (widget.config.x + widget.config.w) % GRID_COLS,
          y: widget.config.y,
        },
      };
      setWidgets([...widgets, newWidget]);
    }
  };

  // Handle drag start
  const handleDragStart = (e: React.MouseEvent, widget: Widget) => {
    if (!gridRef.current) return;
    
    const rect = gridRef.current.getBoundingClientRect();
    const cellWidth = rect.width / GRID_COLS;
    
    setIsDragging(true);
    setDraggedWidget(widget);
    setDragOffset({
      x: e.clientX - rect.left - (widget.config.x * cellWidth),
      y: e.clientY - rect.top - (widget.config.y * ROW_HEIGHT),
    });
  };

  // Handle drag move
  const handleDragMove = useCallback((e: MouseEvent) => {
    if (!isDragging || !draggedWidget || !gridRef.current) return;

    const rect = gridRef.current.getBoundingClientRect();
    const cellWidth = rect.width / GRID_COLS;
    
    const newX = Math.max(0, Math.min(
      GRID_COLS - draggedWidget.config.w,
      Math.round((e.clientX - rect.left - dragOffset.x) / cellWidth)
    ));
    
    const newY = Math.max(0, Math.round(
      (e.clientY - rect.top - dragOffset.y) / ROW_HEIGHT
    ));

    updateWidget(draggedWidget.id, {
      config: { ...draggedWidget.config, x: newX, y: newY }
    });
  }, [isDragging, draggedWidget, dragOffset]);

  // Handle drag end
  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
    setDraggedWidget(null);
  }, []);

  // Handle resize
  const handleResize = (widget: Widget, direction: 'right' | 'bottom', delta: number) => {
    const cellWidth = gridRef.current ? gridRef.current.getBoundingClientRect().width / GRID_COLS : 60;
    
    if (direction === 'right') {
      const newW = Math.max(
        widget.config.minW || 1,
        Math.min(
          GRID_COLS - widget.config.x,
          widget.config.w + Math.round(delta / cellWidth)
        )
      );
      updateWidget(widget.id, {
        config: { ...widget.config, w: newW }
      });
    } else {
      const newH = Math.max(
        widget.config.minH || 1,
        widget.config.h + Math.round(delta / ROW_HEIGHT)
      );
      updateWidget(widget.id, {
        config: { ...widget.config, h: newH }
      });
    }
  };

  // Save dashboard
  const handleSave = async () => {
    if (!dashboardName.trim()) {
      toast.error('Please enter a dashboard name');
      return;
    }

    if (widgets.length === 0) {
      toast.error('Please add at least one widget');
      return;
    }

    const dashboardConfig: DashboardConfig = {
      name: dashboardName,
      description: dashboardDescription,
      widgets,
      layout: {
        cols: GRID_COLS,
        rowHeight: ROW_HEIGHT,
        margin: [10, 10],
      },
    };

    if (onSave) {
      try {
        await onSave(dashboardConfig);
        toast.success('Dashboard saved successfully');
      } catch (error) {
        toast.error('Failed to save dashboard');
      }
    }
  };

  // Render widget content
  const renderWidgetContent = (widget: Widget) => {
    switch (widget.type) {
      case 'chart':
        return (
          <div className="flex items-center justify-center h-full text-gray-400">
            {widget.chartType === 'line' && <LineChart className="w-12 h-12" />}
            {widget.chartType === 'bar' && <BarChart3 className="w-12 h-12" />}
            {widget.chartType === 'pie' && <PieChart className="w-12 h-12" />}
            <span className="ml-2 text-sm">Chart Preview</span>
          </div>
        );
      case 'metric':
        return (
          <div className="flex flex-col items-center justify-center h-full">
            <Hash className="w-8 h-8 text-gray-400 mb-2" />
            <span className="text-2xl font-bold text-gray-700">42,350</span>
            <span className="text-sm text-gray-500">Sample Metric</span>
          </div>
        );
      case 'table':
        return (
          <div className="p-2">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b">
                  {columns.slice(0, 3).map(col => (
                    <th key={col} className="text-left p-1">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="p-1">Sample</td>
                  <td className="p-1">Data</td>
                  <td className="p-1">Preview</td>
                </tr>
              </tbody>
            </table>
          </div>
        );
      case 'text':
        return (
          <div className="p-2">
            <Type className="w-6 h-6 text-gray-400 mb-1" />
            <p className="text-sm text-gray-600">Text content goes here...</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <Layout className="w-6 h-6 text-gray-600" />
          <div>
            <input
              type="text"
              value={dashboardName}
              onChange={(e) => setDashboardName(e.target.value)}
              placeholder="Dashboard Name"
              className="text-lg font-semibold bg-transparent border-b border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none px-1"
            />
            <input
              type="text"
              value={dashboardDescription}
              onChange={(e) => setDashboardDescription(e.target.value)}
              placeholder="Add description..."
              className="block text-sm text-gray-600 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none px-1 mt-1"
            />
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsPreview(!isPreview)}
            className="px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors flex items-center space-x-2"
          >
            {isPreview ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            <span>{isPreview ? 'Edit' : 'Preview'}</span>
          </button>
          <button
            onClick={onCancel}
            className="px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>Save Dashboard</span>
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        {!isPreview && (
          <div className="w-64 bg-white border-r p-4 overflow-y-auto">
            <h3 className="font-medium text-gray-900 mb-3">Add Widget</h3>
            <div className="space-y-2">
              {WIDGET_TYPES.map(widgetType => (
                <button
                  key={widgetType.id}
                  onClick={() => addWidget(widgetType)}
                  className="w-full px-3 py-2 text-left hover:bg-gray-50 rounded-lg transition-colors flex items-center space-x-2"
                >
                  <widgetType.icon className="w-4 h-4 text-gray-600" />
                  <span className="text-sm">{widgetType.label}</span>
                </button>
              ))}
            </div>

            {selectedWidget && (
              <div className="mt-6 pt-6 border-t">
                <h3 className="font-medium text-gray-900 mb-3">Widget Settings</h3>
                {(() => {
                  const widget = widgets.find(w => w.id === selectedWidget);
                  if (!widget) return null;

                  return (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Title
                        </label>
                        <input
                          type="text"
                          value={widget.title}
                          onChange={(e) => updateWidget(widget.id, { title: e.target.value })}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                        />
                      </div>

                      {widget.type === 'chart' && columns.length > 0 && (
                        <>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              X Axis
                            </label>
                            <select
                              value={widget.settings.xAxis || ''}
                              onChange={(e) => updateWidget(widget.id, {
                                settings: { ...widget.settings, xAxis: e.target.value }
                              })}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            >
                              <option value="">Select field...</option>
                              {columns.map(col => (
                                <option key={col} value={col}>{col}</option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Y Axis
                            </label>
                            <select
                              value={widget.settings.yAxis || ''}
                              onChange={(e) => updateWidget(widget.id, {
                                settings: { ...widget.settings, yAxis: e.target.value }
                              })}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            >
                              <option value="">Select field...</option>
                              {columns.map(col => (
                                <option key={col} value={col}>{col}</option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Aggregation
                            </label>
                            <select
                              value={widget.settings.aggregation || 'sum'}
                              onChange={(e) => updateWidget(widget.id, {
                                settings: { ...widget.settings, aggregation: e.target.value as any }
                              })}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            >
                              <option value="sum">Sum</option>
                              <option value="avg">Average</option>
                              <option value="count">Count</option>
                              <option value="min">Min</option>
                              <option value="max">Max</option>
                            </select>
                          </div>
                        </>
                      )}

                      <div className="flex space-x-2 pt-3">
                        <button
                          onClick={() => duplicateWidget(widget.id)}
                          className="flex-1 px-2 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors flex items-center justify-center"
                        >
                          <Copy className="w-3 h-3 mr-1" />
                          Duplicate
                        </button>
                        <button
                          onClick={() => deleteWidget(widget.id)}
                          className="flex-1 px-2 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded transition-colors flex items-center justify-center"
                        >
                          <Trash2 className="w-3 h-3 mr-1" />
                          Delete
                        </button>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
        )}

        {/* Grid Area */}
        <div className="flex-1 p-6 overflow-auto">
          <div 
            ref={gridRef}
            className="relative bg-white rounded-lg shadow-sm border min-h-[600px]"
            style={{
              backgroundImage: !isPreview ? 
                `linear-gradient(to right, #f3f4f6 1px, transparent 1px),
                 linear-gradient(to bottom, #f3f4f6 1px, transparent 1px)` : 'none',
              backgroundSize: `${100 / GRID_COLS}% ${ROW_HEIGHT}px`,
            }}
            onMouseMove={handleDragMove as any}
            onMouseUp={handleDragEnd}
            onMouseLeave={handleDragEnd}
          >
            {widgets.map(widget => {
              const cellWidth = 100 / GRID_COLS;
              const style = {
                position: 'absolute' as const,
                left: `${widget.config.x * cellWidth}%`,
                top: `${widget.config.y * ROW_HEIGHT}px`,
                width: `${widget.config.w * cellWidth}%`,
                height: `${widget.config.h * ROW_HEIGHT}px`,
              };

              return (
                <div
                  key={widget.id}
                  className={`group ${
                    selectedWidget === widget.id ? 'ring-2 ring-blue-500' : ''
                  } ${isPreview ? '' : 'hover:ring-2 hover:ring-blue-300'} 
                  bg-white border rounded-lg shadow-sm transition-all`}
                  style={style}
                  onClick={() => !isPreview && setSelectedWidget(widget.id)}
                >
                  {/* Widget Header */}
                  {!isPreview && (
                    <div
                      className="absolute top-0 left-0 right-0 h-8 bg-gray-50 border-b rounded-t-lg cursor-move flex items-center justify-between px-2"
                      onMouseDown={(e) => handleDragStart(e, widget)}
                    >
                      <span className="text-xs font-medium text-gray-700 truncate">
                        {widget.title}
                      </span>
                      <Move className="w-3 h-3 text-gray-400" />
                    </div>
                  )}

                  {/* Widget Content */}
                  <div className={`${!isPreview ? 'pt-8' : ''} p-2 h-full`}>
                    {renderWidgetContent(widget)}
                  </div>

                  {/* Resize Handles */}
                  {!isPreview && selectedWidget === widget.id && (
                    <>
                      <div
                        className="absolute right-0 top-0 bottom-0 w-2 cursor-ew-resize bg-blue-500 opacity-0 hover:opacity-50"
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          const startX = e.clientX;
                          
                          const handleMouseMove = (e: MouseEvent) => {
                            handleResize(widget, 'right', e.clientX - startX);
                          };
                          
                          const handleMouseUp = () => {
                            document.removeEventListener('mousemove', handleMouseMove);
                            document.removeEventListener('mouseup', handleMouseUp);
                          };
                          
                          document.addEventListener('mousemove', handleMouseMove);
                          document.addEventListener('mouseup', handleMouseUp);
                        }}
                      />
                      <div
                        className="absolute bottom-0 left-0 right-0 h-2 cursor-ns-resize bg-blue-500 opacity-0 hover:opacity-50"
                        onMouseDown={(e) => {
                          e.stopPropagation();
                          const startY = e.clientY;
                          
                          const handleMouseMove = (e: MouseEvent) => {
                            handleResize(widget, 'bottom', e.clientY - startY);
                          };
                          
                          const handleMouseUp = () => {
                            document.removeEventListener('mousemove', handleMouseMove);
                            document.removeEventListener('mouseup', handleMouseUp);
                          };
                          
                          document.addEventListener('mousemove', handleMouseMove);
                          document.addEventListener('mouseup', handleMouseUp);
                        }}
                      />
                    </>
                  )}
                </div>
              );
            })}

            {/* Empty State */}
            {widgets.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <Grid3x3 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 mb-3">No widgets added yet</p>
                  <p className="text-sm text-gray-400">
                    Click a widget type in the sidebar to get started
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}