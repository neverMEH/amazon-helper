import React, { useState, useCallback, useMemo } from 'react';
import {
  CogIcon,
  PlusIcon,
  TrashIcon,
  CheckIcon,
  XMarkIcon,
  DocumentDuplicateIcon,
  BookmarkIcon,
} from '@heroicons/react/24/outline';
import type { DashboardConfig } from '../../services/reportDashboardService';

interface ChartConfigurationPanelProps {
  collectionId: string;
  availableMetrics: string[];
  savedConfigs: DashboardConfig[];
  onSave: (config: DashboardConfig) => void;
  onApply: (config: DashboardConfig) => void;
}

interface WidgetConfig {
  id: string;
  type: 'line' | 'bar' | 'pie' | 'area' | 'metric_card' | 'table' | 'text';
  title: string;
  metrics: string[];
  position: { x: number; y: number; w: number; h: number };
  options: {
    showLegend?: boolean;
    showGrid?: boolean;
    stacked?: boolean;
    tension?: number;
    aggregation?: 'sum' | 'avg' | 'min' | 'max';
  };
}

const ChartConfigurationPanel: React.FC<ChartConfigurationPanelProps> = ({
  collectionId,
  availableMetrics,
  savedConfigs,
  onSave,
  onApply,
}) => {
  const [configName, setConfigName] = useState('');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [widgets, setWidgets] = useState<WidgetConfig[]>([]);
  const [columns, setColumns] = useState(2);
  const [selectedConfig, setSelectedConfig] = useState<DashboardConfig | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingWidget, setEditingWidget] = useState<string | null>(null);

  // Widget templates
  const widgetTemplates = useMemo(
    () => [
      {
        type: 'line' as const,
        label: 'Line Chart',
        icon: '📈',
        defaultMetrics: ['impressions', 'clicks'],
      },
      {
        type: 'bar' as const,
        label: 'Bar Chart',
        icon: '📊',
        defaultMetrics: ['spend', 'conversions'],
      },
      {
        type: 'pie' as const,
        label: 'Pie Chart',
        icon: '🥧',
        defaultMetrics: ['impressions'],
      },
      {
        type: 'area' as const,
        label: 'Area Chart',
        icon: '📉',
        defaultMetrics: ['impressions', 'clicks', 'conversions'],
      },
      {
        type: 'metric_card' as const,
        label: 'Metric Card',
        icon: '🎯',
        defaultMetrics: ['spend'],
      },
      {
        type: 'table' as const,
        label: 'Data Table',
        icon: '📋',
        defaultMetrics: availableMetrics.slice(0, 5),
      },
    ],
    [availableMetrics]
  );

  // Add a new widget
  const handleAddWidget = useCallback((template: typeof widgetTemplates[0]) => {
    const newWidget: WidgetConfig = {
      id: `widget-${Date.now()}`,
      type: template.type,
      title: template.label,
      metrics: template.defaultMetrics.filter((m) => availableMetrics.includes(m)),
      position: {
        x: widgets.length % columns,
        y: Math.floor(widgets.length / columns),
        w: 1,
        h: 1,
      },
      options: {
        showLegend: true,
        showGrid: true,
        aggregation: 'sum',
      },
    };
    setWidgets([...widgets, newWidget]);
  }, [widgets, columns, availableMetrics]);

  // Remove a widget
  const handleRemoveWidget = useCallback((widgetId: string) => {
    setWidgets(widgets.filter((w) => w.id !== widgetId));
  }, [widgets]);

  // Update widget configuration
  const handleUpdateWidget = useCallback(
    (widgetId: string, updates: Partial<WidgetConfig>) => {
      setWidgets(
        widgets.map((w) => (w.id === widgetId ? { ...w, ...updates } : w))
      );
    },
    [widgets]
  );

  // Toggle metric selection
  const handleMetricToggle = useCallback((metric: string) => {
    setSelectedMetrics((prev) =>
      prev.includes(metric)
        ? prev.filter((m) => m !== metric)
        : [...prev, metric]
    );
  }, []);

  // Save configuration
  const handleSaveConfiguration = useCallback(() => {
    if (!configName.trim()) {
      alert('Please enter a configuration name');
      return;
    }

    const config: DashboardConfig = {
      name: configName,
      chartTypes: [...new Set(widgets.map((w) => w.type))],
      metrics: [...new Set(widgets.flatMap((w) => w.metrics))],
      layout: {
        columns,
        widgets: widgets.map((w) => ({
          type: w.type,
          position: w.position,
          config: {
            title: w.title,
            metrics: w.metrics,
            options: w.options,
          },
        })),
      },
    };

    onSave(config);
    setIsEditing(false);
  }, [configName, widgets, columns, onSave]);

  // Load a saved configuration
  const handleLoadConfiguration = useCallback((config: DashboardConfig) => {
    setSelectedConfig(config);
    setConfigName(config.name);
    setColumns(config.layout?.columns || 2);
    
    if (config.layout?.widgets) {
      const loadedWidgets: WidgetConfig[] = config.layout.widgets.map((w, index) => ({
        id: `widget-${Date.now()}-${index}`,
        type: w.type as WidgetConfig['type'],
        title: w.config.title || w.type,
        metrics: w.config.metrics || [],
        position: w.position,
        options: w.config.options || {},
      }));
      setWidgets(loadedWidgets);
    }
    
    onApply(config);
  }, [onApply]);

  // Duplicate configuration
  const handleDuplicateConfiguration = useCallback((config: DashboardConfig) => {
    const duplicatedConfig = {
      ...config,
      name: `${config.name} (Copy)`,
    };
    handleLoadConfiguration(duplicatedConfig);
    setIsEditing(true);
  }, [handleLoadConfiguration]);

  return (
    <div className="space-y-6">
      {/* Saved Configurations */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Saved Configurations
        </h3>
        {savedConfigs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {savedConfigs.map((config) => (
              <div
                key={config.id}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedConfig?.id === config.id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => handleLoadConfiguration(config)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center">
                    <BookmarkIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h4 className="font-medium text-gray-900">{config.name}</h4>
                  </div>
                  {selectedConfig?.id === config.id && (
                    <CheckIcon className="h-5 w-5 text-indigo-600" />
                  )}
                </div>
                <p className="text-sm text-gray-500 mb-2">
                  {config.chartTypes.length} chart types, {config.metrics.length} metrics
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDuplicateConfiguration(config);
                    }}
                    className="text-xs text-gray-500 hover:text-gray-700"
                  >
                    <DocumentDuplicateIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No saved configurations yet</p>
        )}
      </div>

      {/* Configuration Editor */}
      <div className="border-t pt-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {isEditing ? 'Edit Configuration' : 'Create New Configuration'}
          </h3>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="text-sm text-indigo-600 hover:text-indigo-700"
          >
            {isEditing ? 'Cancel' : 'New Configuration'}
          </button>
        </div>

        {isEditing && (
          <div className="space-y-4">
            {/* Configuration Name */}
            <div>
              <label htmlFor="config-name" className="block text-sm font-medium text-gray-700 mb-1">
                Configuration Name
              </label>
              <input
                type="text"
                id="config-name"
                value={configName}
                onChange={(e) => setConfigName(e.target.value)}
                className="w-full border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="Enter configuration name"
              />
            </div>

            {/* Layout Columns */}
            <div>
              <label htmlFor="columns" className="block text-sm font-medium text-gray-700 mb-1">
                Dashboard Columns
              </label>
              <select
                id="columns"
                value={columns}
                onChange={(e) => setColumns(Number(e.target.value))}
                className="border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              >
                <option value={1}>1 Column</option>
                <option value={2}>2 Columns</option>
                <option value={3}>3 Columns</option>
                <option value={4}>4 Columns</option>
              </select>
            </div>

            {/* Widget Templates */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Add Widgets
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
                {widgetTemplates.map((template) => (
                  <button
                    key={template.type}
                    onClick={() => handleAddWidget(template)}
                    className="flex flex-col items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300"
                  >
                    <span className="text-2xl mb-1">{template.icon}</span>
                    <span className="text-xs text-gray-600">{template.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Current Widgets */}
            {widgets.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dashboard Widgets
                </label>
                <div className="space-y-2">
                  {widgets.map((widget) => (
                    <div
                      key={widget.id}
                      className="border border-gray-200 rounded-lg p-3"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <CogIcon className="h-4 w-4 text-gray-400 mr-2" />
                          <input
                            type="text"
                            value={widget.title}
                            onChange={(e) =>
                              handleUpdateWidget(widget.id, { title: e.target.value })
                            }
                            className="text-sm font-medium border-0 focus:ring-0 p-0"
                          />
                        </div>
                        <button
                          onClick={() => handleRemoveWidget(widget.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>

                      {/* Widget Metrics */}
                      <div className="mb-2">
                        <label className="text-xs text-gray-500">Metrics:</label>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {availableMetrics.map((metric) => (
                            <button
                              key={metric}
                              onClick={() => {
                                const newMetrics = widget.metrics.includes(metric)
                                  ? widget.metrics.filter((m) => m !== metric)
                                  : [...widget.metrics, metric];
                                handleUpdateWidget(widget.id, { metrics: newMetrics });
                              }}
                              className={`px-2 py-1 text-xs rounded ${
                                widget.metrics.includes(metric)
                                  ? 'bg-indigo-100 text-indigo-700'
                                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                              }`}
                            >
                              {metric}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Widget Options */}
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={widget.options.showLegend}
                            onChange={(e) =>
                              handleUpdateWidget(widget.id, {
                                options: { ...widget.options, showLegend: e.target.checked },
                              })
                            }
                            className="mr-1"
                          />
                          Legend
                        </label>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={widget.options.showGrid}
                            onChange={(e) =>
                              handleUpdateWidget(widget.id, {
                                options: { ...widget.options, showGrid: e.target.checked },
                              })
                            }
                            className="mr-1"
                          />
                          Grid
                        </label>
                        <select
                          value={widget.options.aggregation}
                          onChange={(e) =>
                            handleUpdateWidget(widget.id, {
                              options: {
                                ...widget.options,
                                aggregation: e.target.value as 'sum' | 'avg' | 'min' | 'max',
                              },
                            })
                          }
                          className="text-xs border-gray-300 rounded"
                        >
                          <option value="sum">Sum</option>
                          <option value="avg">Avg</option>
                          <option value="min">Min</option>
                          <option value="max">Max</option>
                        </select>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Save Button */}
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveConfiguration}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Save Configuration
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChartConfigurationPanel;