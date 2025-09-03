import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Play, 
  AlertCircle, 
  Plus, 
  Settings, 
  Trash2, 
  Code,
  Eye,
  Save,
  RefreshCw,
  Info,
  FileText,
  BarChart3,
  PieChart,
  LineChart,
  Table,
  Copy,
  X,
  Tag
} from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import SQLEditor from '../../common/SQLEditor';
import { queryFlowTemplateService } from '../../../services/queryFlowTemplateService';
import toast from 'react-hot-toast';

/**
 * Dynamic, responsive Query Flow Template Editor
 * Handles custom parameters in SQL and visualization configuration
 */

interface DetectedParameter {
  name: string;
  type: 'detected' | 'custom';
  dataType?: string;
  defaultValue?: any;
  required?: boolean;
}

interface VisualizationConfig {
  id: string;
  name: string;
  type: 'table' | 'bar' | 'line' | 'pie' | 'scatter' | 'heatmap' | 'funnel' | 'area' | 'combo';
  dataMapping: {
    x_field?: string;
    y_field?: string;
    y_fields?: string[];
    group_by?: string;
    aggregation?: string;
    filters?: any[];
  };
  config: {
    title?: string;
    subtitle?: string;
    showLegend?: boolean;
    showTooltips?: boolean;
    colors?: string[];
    stacked?: boolean;
    orientation?: 'horizontal' | 'vertical';
  };
  isDefault: boolean;
}

const TemplateEditor: React.FC = () => {
  const navigate = useNavigate();
  const { id: templateId } = useParams();
  const [activeTab, setActiveTab] = useState<'metadata' | 'sql' | 'parameters' | 'visualizations' | 'preview'>('metadata');
  const [autoSave, setAutoSave] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [sqlContent, setSqlContent] = useState(`-- Example SQL with parameters
WITH campaign_metrics AS (
  SELECT 
    campaign,
    campaign_id,
    :metric_type as metric_name,  -- Custom parameter
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    SUM(conversions) as total_conversions,
    CAST(SUM(clicks) AS DOUBLE) / NULLIF(SUM(impressions), 0) * 100 as ctr,
    CAST(SUM(conversions) AS DOUBLE) / NULLIF(SUM(clicks), 0) * 100 as conversion_rate
  FROM impressions_clicks_conversions
  WHERE 
    event_dt BETWEEN :start_date AND :end_date
    {% if campaign_ids %}
    AND campaign_id IN (:campaign_ids)
    {% endif %}
    {% if min_impressions %}
    AND impressions >= :min_impressions
    {% endif %}
  GROUP BY campaign, campaign_id
  HAVING SUM(impressions) > :threshold
)
SELECT * FROM campaign_metrics
WHERE ctr > :min_ctr
ORDER BY :order_by :order_direction
LIMIT :limit`);
  
  const [detectedParameters, setDetectedParameters] = useState<DetectedParameter[]>([]);
  const [visualizations, setVisualizations] = useState<VisualizationConfig[]>([
    {
      id: '1',
      name: 'Results Table',
      type: 'table',
      dataMapping: {},
      config: { showTooltips: true },
      isDefault: true
    }
  ]);
  
  const [templateMetadata, setTemplateMetadata] = useState({
    template_id: '',
    name: '',
    category: 'Performance',
    description: '',
    tags: [] as string[],
    visibility: 'public',
    status: 'active'
  });

  // Detect parameters from SQL
  useEffect(() => {
    const paramRegex = /:(\w+)/g;
    const jinjaRegex = /{%\s*if\s+(\w+)\s*%}/g;
    const detected = new Map<string, DetectedParameter>();
    
    // Find :parameter style
    let match;
    while ((match = paramRegex.exec(sqlContent)) !== null) {
      const paramName = match[1];
      if (!detected.has(paramName)) {
        detected.set(paramName, {
          name: paramName,
          type: 'detected',
          dataType: guessParameterType(paramName),
          required: !sqlContent.includes(`{% if ${paramName} %}`),
          defaultValue: getDefaultValue(paramName)
        });
      }
    }
    
    // Find Jinja conditional parameters
    while ((match = jinjaRegex.exec(sqlContent)) !== null) {
      const paramName = match[1];
      if (!detected.has(paramName)) {
        detected.set(paramName, {
          name: paramName,
          type: 'detected',
          dataType: guessParameterType(paramName),
          required: false,
          defaultValue: null
        });
      }
    }
    
    setDetectedParameters(Array.from(detected.values()));
  }, [sqlContent]);

  // Guess parameter type from name
  const guessParameterType = (name: string): string => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('date')) return 'date';
    if (lowerName.includes('time')) return 'datetime';
    if (lowerName.includes('ids') || lowerName.includes('list')) return 'array';
    if (lowerName.includes('count') || lowerName.includes('limit') || lowerName.includes('threshold')) return 'number';
    if (lowerName.includes('flag') || lowerName.includes('is_') || lowerName.includes('has_')) return 'boolean';
    if (lowerName === 'order_by' || lowerName === 'metric_type') return 'select';
    if (lowerName === 'order_direction') return 'select';
    return 'string';
  };

  // Get default value based on parameter name
  const getDefaultValue = (name: string): any => {
    const lowerName = name.toLowerCase();
    if (lowerName === 'start_date') return '2024-01-01';
    if (lowerName === 'end_date') return '2024-12-31';
    if (lowerName === 'limit') return 100;
    if (lowerName === 'threshold') return 0;
    if (lowerName === 'min_ctr') return 0;
    if (lowerName === 'min_impressions') return 1000;
    if (lowerName === 'order_by') return 'total_impressions';
    if (lowerName === 'order_direction') return 'DESC';
    if (lowerName === 'metric_type') return 'performance';
    return null;
  };

  const tabs = [
    { id: 'metadata', label: 'Metadata', icon: <FileText className="h-4 w-4" /> },
    { id: 'sql', label: 'SQL Template', icon: <Code className="h-4 w-4" /> },
    { id: 'parameters', label: 'Parameters', icon: <Settings className="h-4 w-4" /> },
    { id: 'visualizations', label: 'Visualizations', icon: <BarChart3 className="h-4 w-4" /> },
    { id: 'preview', label: 'Preview & Test', icon: <Eye className="h-4 w-4" /> }
  ];

  const addVisualization = () => {
    const newViz: VisualizationConfig = {
      id: Date.now().toString(),
      name: `Chart ${visualizations.length + 1}`,
      type: 'bar',
      dataMapping: {},
      config: {},
      isDefault: visualizations.length === 0
    };
    setVisualizations([...visualizations, newViz]);
  };

  const updateVisualization = (id: string, updates: Partial<VisualizationConfig>) => {
    setVisualizations(visualizations.map(viz => 
      viz.id === id ? { ...viz, ...updates } : viz
    ));
  };

  const removeVisualization = (id: string) => {
    setVisualizations(visualizations.filter(viz => viz.id !== id));
  };

  const queryClient = useQueryClient();

  // Load existing template if editing
  const { data: existingTemplate, isLoading: loadingTemplate } = useQuery({
    queryKey: ['queryFlowTemplate', templateId],
    queryFn: () => queryFlowTemplateService.getTemplate(templateId!),
    enabled: !!templateId
  });

  // Populate form when template is loaded
  useEffect(() => {
    if (existingTemplate) {
      setTemplateMetadata({
        template_id: existingTemplate.template_id,
        name: existingTemplate.name,
        category: existingTemplate.category,
        description: existingTemplate.description || '',
        tags: existingTemplate.tags || [],
        visibility: existingTemplate.is_public ? 'public' : 'private',
        status: existingTemplate.is_active ? 'active' : 'inactive'
      });
      setSqlContent(existingTemplate.sql_template || '');
      // TODO: Load parameters and visualizations from existingTemplate
    }
  }, [existingTemplate]);

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async () => {
      const templateData = {
        template_id: templateMetadata.template_id,
        name: templateMetadata.name,
        description: templateMetadata.description,
        category: templateMetadata.category,
        sql_template: sqlContent,
        tags: templateMetadata.tags,
        is_public: templateMetadata.visibility === 'public',
        is_active: templateMetadata.status === 'active',
        parameters: detectedParameters.map(param => ({
          parameter_name: param.name,
          display_name: param.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          parameter_type: param.dataType || 'string',
          required: param.required || false,
          default_value: param.defaultValue,
          validation_rules: {},
          ui_component: param.dataType === 'date' ? 'date_picker' : 'text_input',
          ui_config: {},
          order_index: 0
        })),
        chart_configs: visualizations.map((viz, idx) => ({
          chart_name: viz.name,
          chart_type: viz.type,
          chart_config: viz.config,
          data_mapping: viz.dataMapping,
          is_default: viz.isDefault,
          order_index: idx
        }))
      };

      if (templateId) {
        return queryFlowTemplateService.updateTemplate(templateId, templateData);
      } else {
        return queryFlowTemplateService.createTemplate(templateData);
      }
    },
    onSuccess: (data) => {
      toast.success(templateId ? 'Template updated successfully!' : 'Template created successfully!');
      queryClient.invalidateQueries({ queryKey: ['queryFlowTemplates'] });
      if (!templateId) {
        // Navigate to edit mode after creation
        navigate(`/query-flow-templates/edit/${data.template_id}`, { replace: true });
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to save template');
    }
  });

  const handleSave = async () => {
    // Validate required fields
    if (!templateMetadata.template_id || !templateMetadata.name || !sqlContent) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Validate template_id format
    if (!/^[a-z0-9_]+$/.test(templateMetadata.template_id)) {
      toast.error('Template ID must contain only lowercase letters, numbers, and underscores');
      return;
    }

    setIsSaving(true);
    await saveMutation.mutateAsync();
    setIsSaving(false);
  };

  if (loadingTemplate) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading template...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header Bar - Responsive */}
      <div className="bg-white border-b border-gray-200 px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 sm:space-x-4">
            <button 
              onClick={() => navigate('/query-flow-templates')}
              className="flex items-center text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="h-4 sm:h-5 w-4 sm:w-5 mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Back</span>
            </button>
            <h1 className="text-lg sm:text-xl font-semibold text-gray-900">Template Editor</h1>
          </div>
          <div className="flex items-center space-x-2 sm:space-x-3">
            <button 
              onClick={handleSave}
              disabled={isSaving}
              className="px-3 sm:px-4 py-1.5 sm:py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              {isSaving ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Save className="h-4 w-4 inline mr-1" />
                  <span className="hidden sm:inline">Save</span>
                </>
              )}
            </button>
            <button className="px-3 sm:px-4 py-1.5 sm:py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">
              <Play className="h-4 w-4 inline sm:mr-1" />
              <span className="hidden sm:inline">Test</span>
            </button>
          </div>
        </div>
      </div>

      {/* Status Bar - Responsive */}
      <div className="bg-blue-50 border-b border-blue-200 px-4 sm:px-6 py-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-sm">
          <div className="flex items-center space-x-2 sm:space-x-4">
            <span className="flex items-center">
              <div className="h-2 w-2 bg-yellow-400 rounded-full mr-2"></div>
              <span className="text-xs sm:text-sm">Unsaved changes</span>
            </span>
            <span className="text-gray-600 text-xs sm:text-sm">Last saved: 2 mins ago</span>
          </div>
          <div className="flex items-center mt-1 sm:mt-0">
            <span className="text-gray-600 mr-2 text-xs sm:text-sm">Auto-save:</span>
            <button 
              onClick={() => setAutoSave(!autoSave)}
              className={`relative inline-flex h-5 sm:h-6 w-10 sm:w-11 items-center rounded-full ${autoSave ? 'bg-indigo-600' : 'bg-gray-200'}`}
            >
              <span className={`inline-block h-3 sm:h-4 w-3 sm:w-4 transform rounded-full bg-white transition ${autoSave ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation - Scrollable on mobile */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-4 sm:px-6">
          <nav className="flex space-x-4 sm:space-x-8 overflow-x-auto" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  whitespace-nowrap py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm flex items-center space-x-1 sm:space-x-2
                  ${activeTab === tab.id 
                    ? 'border-indigo-500 text-indigo-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                `}
              >
                <span className="hidden sm:inline">{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content - Responsive padding */}
      <div className="flex-1 px-4 sm:px-6 py-4 sm:py-6 overflow-y-auto">
        {activeTab === 'metadata' && <MetadataTab metadata={templateMetadata} setMetadata={setTemplateMetadata} />}
        {activeTab === 'sql' && <SQLTemplateTab sqlContent={sqlContent} setSqlContent={setSqlContent} detectedParameters={detectedParameters} />}
        {activeTab === 'parameters' && <ParametersTab parameters={detectedParameters} />}
        {activeTab === 'visualizations' && (
          <VisualizationsTab 
            visualizations={visualizations}
            onAdd={addVisualization}
            onUpdate={updateVisualization}
            onRemove={removeVisualization}
            availableFields={detectedParameters.map(p => p.name)}
          />
        )}
        {activeTab === 'preview' && <PreviewTab sqlContent={sqlContent} parameters={detectedParameters} />}
      </div>
    </div>
  );
};

// Metadata Tab Component
const MetadataTab: React.FC<{ metadata: any; setMetadata: (m: any) => void }> = ({ metadata, setMetadata }) => {
  const [tagInput, setTagInput] = React.useState('');
  const [showTagInput, setShowTagInput] = React.useState(false);
  const tagInputRef = React.useRef<HTMLInputElement>(null);
  
  return (
  <div className="max-w-4xl mx-auto">
    <div className="bg-white rounded-lg shadow p-4 sm:p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4 sm:mb-6">Template Information</h2>
      
      <div className="space-y-4 sm:space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Template ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={metadata.template_id}
              onChange={(e) => setMetadata({...metadata, template_id: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
              placeholder="campaign_performance"
            />
            <p className="mt-1 text-xs text-gray-500">Unique, lowercase, underscores only</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Category <span className="text-red-500">*</span>
            </label>
            <select 
              value={metadata.category}
              onChange={(e) => setMetadata({...metadata, category: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            >
              <option>Performance</option>
              <option>Attribution</option>
              <option>Audience</option>
              <option>Custom</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={metadata.name}
            onChange={(e) => setMetadata({...metadata, name: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            placeholder="Campaign Performance Analysis"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Description</label>
          <textarea
            rows={4}
            value={metadata.description}
            onChange={(e) => setMetadata({...metadata, description: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            placeholder="Analyze campaign metrics including impressions, clicks, conversions, and ROAS"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
          <div className="flex flex-wrap gap-2">
            {metadata.tags.map((tag: string, index: number) => (
              <span key={index} className="inline-flex items-center px-3 py-1 rounded-full text-xs sm:text-sm font-medium bg-indigo-100 text-indigo-800">
                <Tag className="h-3 w-3 mr-1" />
                {tag}
                <button 
                  onClick={() => setMetadata({
                    ...metadata, 
                    tags: metadata.tags.filter((_: string, i: number) => i !== index)
                  })}
                  className="ml-2 text-indigo-600 hover:text-indigo-800"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            {showTagInput ? (
              <input
                ref={tagInputRef}
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && tagInput.trim()) {
                    setMetadata({
                      ...metadata,
                      tags: [...metadata.tags, tagInput.trim()]
                    });
                    setTagInput('');
                    setShowTagInput(false);
                  }
                }}
                onBlur={() => {
                  if (tagInput.trim()) {
                    setMetadata({
                      ...metadata,
                      tags: [...metadata.tags, tagInput.trim()]
                    });
                  }
                  setTagInput('');
                  setShowTagInput(false);
                }}
                className="px-3 py-1 text-sm border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Enter tag..."
                autoFocus
              />
            ) : (
              <button 
                onClick={() => {
                  setShowTagInput(true);
                  setTimeout(() => tagInputRef.current?.focus(), 0);
                }}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs sm:text-sm font-medium border-2 border-dashed border-gray-300 text-gray-600 hover:border-gray-400"
              >
                <Plus className="h-3 sm:h-4 w-3 sm:w-4 mr-1" />
                Add Tag
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  </div>
  );
};

// SQL Template Tab - Responsive
const SQLTemplateTab: React.FC<{ 
  sqlContent: string; 
  setSqlContent: (content: string) => void; 
  detectedParameters: DetectedParameter[] 
}> = ({ sqlContent, setSqlContent, detectedParameters }) => (
  <div className="max-w-full">
    <div className="bg-white rounded-lg shadow">
      {/* Toolbar */}
      <div className="border-b border-gray-200 px-4 sm:px-6 py-2 sm:py-3 flex items-center space-x-2 sm:space-x-4 overflow-x-auto">
        <button className="text-xs sm:text-sm font-medium text-gray-700 hover:text-gray-900 whitespace-nowrap">Format SQL</button>
        <button className="text-xs sm:text-sm font-medium text-gray-700 hover:text-gray-900 whitespace-nowrap">Validate</button>
        <button className="text-xs sm:text-sm font-medium text-gray-700 hover:text-gray-900 whitespace-nowrap">Insert Parameter</button>
      </div>
      
      {/* Responsive Layout - Stack on mobile, side-by-side on desktop */}
      <div className="flex flex-col lg:flex-row">
        {/* SQL Editor */}
        <div className="flex-1 p-4 sm:p-6 lg:border-r border-gray-200">
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <SQLEditor
              value={sqlContent}
              onChange={(value) => setSqlContent(value || '')}
              height="500px"
            />
          </div>
        </div>
        
        {/* Helper Panel - Below on mobile, beside on desktop */}
        <div className="w-full lg:w-80 p-4 sm:p-6 bg-gray-50 border-t lg:border-t-0 border-gray-200">
          {/* Parameter Detection */}
          <div className="mb-4 sm:mb-6">
            <h3 className="text-xs sm:text-sm font-medium text-gray-700 mb-2 sm:mb-3 flex items-center">
              <AlertCircle className="h-3 sm:h-4 w-3 sm:w-4 mr-1 sm:mr-2 text-green-500" />
              Detected Parameters ({detectedParameters.length})
            </h3>
            <div className="bg-white rounded-lg p-2 sm:p-3 space-y-1 sm:space-y-2 max-h-48 overflow-y-auto">
              {detectedParameters.map(param => (
                <div key={param.name} className="text-xs sm:text-sm">
                  <span className="text-gray-600">• :{param.name}</span>
                  <span className="text-gray-400 ml-2">({param.dataType})</span>
                  {param.required && <span className="text-red-400 ml-1 text-xs">*</span>}
                </div>
              ))}
            </div>
          </div>
          
          {/* Tips */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 sm:p-3">
            <div className="flex items-start">
              <Info className="h-4 sm:h-5 w-4 sm:w-5 text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="ml-2 text-xs sm:text-sm text-blue-800">
                <p className="font-medium">Tips:</p>
                <ul className="mt-1 space-y-1">
                  <li>• Use :param_name for parameters</li>
                  <li>• Use {`{% if param %}`} for optional</li>
                  <li>• Parameters auto-detect type</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Parameters Tab - Custom input configuration
const ParametersTab: React.FC<{ parameters: DetectedParameter[] }> = ({ parameters }) => (
  <div className="max-w-4xl mx-auto">
    <div className="space-y-3 sm:space-y-4">
      {parameters.map((param) => (
        <ParameterCard key={param.name} parameter={param} />
      ))}
      
      {parameters.length === 0 && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <Code className="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">No parameters detected in your SQL template.</p>
          <p className="text-sm text-gray-500 mt-2">Add parameters using :parameter_name syntax</p>
        </div>
      )}
    </div>
  </div>
);

// Parameter Card with custom input types
const ParameterCard: React.FC<{ parameter: DetectedParameter }> = ({ parameter }) => {
  const [config, setConfig] = useState({
    display_name: parameter.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    type: parameter.dataType || 'string',
    required: parameter.required || false,
    default_value: parameter.defaultValue,
    help_text: '',
    validation: {} as any
  });

  const inputTypes = [
    { value: 'string', label: 'Text Input' },
    { value: 'number', label: 'Number' },
    { value: 'date', label: 'Date Picker' },
    { value: 'datetime', label: 'Date & Time' },
    { value: 'select', label: 'Dropdown Select' },
    { value: 'multi-select', label: 'Multi-Select' },
    { value: 'boolean', label: 'Checkbox' },
    { value: 'array', label: 'List/Array' },
    { value: 'campaign_list', label: 'Campaign Selector' },
    { value: 'asin_list', label: 'ASIN Selector' },
    { value: 'custom', label: 'Custom Component' }
  ];

  return (
    <div className="bg-white rounded-lg shadow p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-3 sm:mb-4">
        <h3 className="text-base sm:text-lg font-medium text-gray-900">:{parameter.name}</h3>
        <div className="flex items-center space-x-2 mt-2 sm:mt-0">
          {parameter.required && (
            <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded">Required</span>
          )}
          <button className="text-gray-400 hover:text-gray-600">
            <Settings className="h-4 sm:h-5 w-4 sm:w-5" />
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <div>
          <label className="block text-xs sm:text-sm font-medium text-gray-700">Display Name</label>
          <input
            type="text"
            value={config.display_name}
            onChange={(e) => setConfig({...config, display_name: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          />
        </div>
        
        <div>
          <label className="block text-xs sm:text-sm font-medium text-gray-700">Input Type</label>
          <select 
            value={config.type}
            onChange={(e) => setConfig({...config, type: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          >
            {inputTypes.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
        </div>

        {/* Show options based on type */}
        {config.type === 'select' && (
          <div className="sm:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-gray-700">Options (one per line)</label>
            <textarea
              rows={3}
              placeholder="option1&#10;option2&#10;option3"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            />
          </div>
        )}

        {config.type === 'number' && (
          <>
            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-700">Min Value</label>
              <input
                type="number"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-700">Max Value</label>
              <input
                type="number"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
              />
            </div>
          </>
        )}

        <div className="sm:col-span-2">
          <label className="block text-xs sm:text-sm font-medium text-gray-700">Default Value</label>
          <input
            type="text"
            value={config.default_value || ''}
            onChange={(e) => setConfig({...config, default_value: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            placeholder="Enter default value"
          />
        </div>

        <div className="sm:col-span-2">
          <label className="block text-xs sm:text-sm font-medium text-gray-700">Help Text</label>
          <input
            type="text"
            value={config.help_text}
            onChange={(e) => setConfig({...config, help_text: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            placeholder="Helpful description for users"
          />
        </div>
      </div>
    </div>
  );
};

// Visualizations Tab - Configure how results are displayed
const VisualizationsTab: React.FC<{ 
  visualizations: VisualizationConfig[];
  onAdd: () => void;
  onUpdate: (id: string, updates: Partial<VisualizationConfig>) => void;
  onRemove: (id: string) => void;
  availableFields: string[];
}> = ({ visualizations, onAdd, onUpdate, onRemove, availableFields }) => {
  const [selectedViz, setSelectedViz] = useState<string | null>(visualizations[0]?.id || null);
  const selected = visualizations.find(v => v.id === selectedViz);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Visualization List */}
        <div className="w-full lg:w-1/3">
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-sm font-medium text-gray-700">Visualizations</h3>
            </div>
            <div className="p-4 space-y-2">
              {visualizations.map((viz) => (
                <div
                  key={viz.id}
                  onClick={() => setSelectedViz(viz.id)}
                  className={`p-3 rounded-lg cursor-pointer transition ${
                    selectedViz === viz.id 
                      ? 'bg-indigo-50 border border-indigo-300' 
                      : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {viz.type === 'table' && <Table className="h-4 w-4 text-gray-600" />}
                      {viz.type === 'bar' && <BarChart3 className="h-4 w-4 text-gray-600" />}
                      {viz.type === 'line' && <LineChart className="h-4 w-4 text-gray-600" />}
                      {viz.type === 'pie' && <PieChart className="h-4 w-4 text-gray-600" />}
                      <span className="text-sm font-medium">{viz.name}</span>
                    </div>
                    {viz.isDefault && (
                      <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">Default</span>
                    )}
                  </div>
                </div>
              ))}
              
              <button 
                onClick={onAdd}
                className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-700 flex items-center justify-center text-sm"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Visualization
              </button>
            </div>
          </div>
        </div>

        {/* Visualization Configuration */}
        {selected && (
          <div className="flex-1">
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Configure: {selected.name}</h3>
                <button 
                  onClick={() => onRemove(selected.id)}
                  className="text-red-400 hover:text-red-600"
                >
                  <Trash2 className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Visualization Name</label>
                  <input
                    type="text"
                    value={selected.name}
                    onChange={(e) => onUpdate(selected.id, { name: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Chart Type</label>
                  <div className="mt-2 grid grid-cols-3 sm:grid-cols-4 gap-2">
                    {[
                      { type: 'table', icon: <Table className="h-5 w-5" /> },
                      { type: 'bar', icon: <BarChart3 className="h-5 w-5" /> },
                      { type: 'line', icon: <LineChart className="h-5 w-5" /> },
                      { type: 'pie', icon: <PieChart className="h-5 w-5" /> },
                    ].map(({ type, icon }) => (
                      <button
                        key={type}
                        onClick={() => onUpdate(selected.id, { type: type as any })}
                        className={`p-3 rounded-lg border ${
                          selected.type === type
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-gray-300 hover:bg-gray-50'
                        } flex flex-col items-center justify-center`}
                      >
                        {icon}
                        <span className="text-xs mt-1 capitalize">{type}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Data Mapping based on chart type */}
                {selected.type !== 'table' && (
                  <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">X-Axis Field</label>
                        <select 
                          value={selected.dataMapping.x_field || ''}
                          onChange={(e) => onUpdate(selected.id, {
                            dataMapping: { ...selected.dataMapping, x_field: e.target.value }
                          })}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                        >
                          <option value="">Select field...</option>
                          {availableFields.map(field => (
                            <option key={field} value={field}>{field}</option>
                          ))}
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Y-Axis Field</label>
                        <select 
                          value={selected.dataMapping.y_field || ''}
                          onChange={(e) => onUpdate(selected.id, {
                            dataMapping: { ...selected.dataMapping, y_field: e.target.value }
                          })}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                        >
                          <option value="">Select field...</option>
                          {availableFields.map(field => (
                            <option key={field} value={field}>{field}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Aggregation</label>
                      <select 
                        value={selected.dataMapping.aggregation || 'none'}
                        onChange={(e) => onUpdate(selected.id, {
                          dataMapping: { ...selected.dataMapping, aggregation: e.target.value }
                        })}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                      >
                        <option value="none">None</option>
                        <option value="sum">Sum</option>
                        <option value="avg">Average</option>
                        <option value="count">Count</option>
                        <option value="min">Min</option>
                        <option value="max">Max</option>
                      </select>
                    </div>
                  </>
                )}

                {/* Chart Options */}
                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Display Options</h4>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selected.config.showLegend ?? true}
                        onChange={(e) => onUpdate(selected.id, {
                          config: { ...selected.config, showLegend: e.target.checked }
                        })}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Show Legend</span>
                    </label>
                    
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selected.config.showTooltips ?? true}
                        onChange={(e) => onUpdate(selected.id, {
                          config: { ...selected.config, showTooltips: e.target.checked }
                        })}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Show Tooltips</span>
                    </label>
                    
                    {selected.type === 'bar' && (
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selected.config.stacked ?? false}
                          onChange={(e) => onUpdate(selected.id, {
                            config: { ...selected.config, stacked: e.target.checked }
                          })}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Stacked Bars</span>
                      </label>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Preview Tab Component
const PreviewTab: React.FC<{ sqlContent: string; parameters: DetectedParameter[] }> = ({ sqlContent, parameters }) => {
  const [testValues, setTestValues] = useState<Record<string, any>>({});
  const [generatedSQL, setGeneratedSQL] = useState('');

  useEffect(() => {
    // Initialize test values
    const initial: Record<string, any> = {};
    parameters.forEach(param => {
      initial[param.name] = param.defaultValue || '';
    });
    setTestValues(initial);
  }, [parameters]);

  const generatePreview = () => {
    let sql = sqlContent;
    
    // Replace parameters
    parameters.forEach(param => {
      const value = testValues[param.name];
      if (value !== null && value !== undefined) {
        // Handle different value types
        if (typeof value === 'string' && !value.match(/^\d+$/)) {
          sql = sql.replace(new RegExp(`:${param.name}`, 'g'), `'${value}'`);
        } else if (Array.isArray(value)) {
          sql = sql.replace(new RegExp(`:${param.name}`, 'g'), `(${value.map(v => `'${v}'`).join(', ')})`);
        } else {
          sql = sql.replace(new RegExp(`:${param.name}`, 'g'), value.toString());
        }
      }
    });
    
    // Remove Jinja blocks for preview
    sql = sql.replace(/{%\s*if\s+\w+\s*%}[\s\S]*?{%\s*endif\s*%}/g, '');
    
    setGeneratedSQL(sql);
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-lg shadow p-4 sm:p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 sm:mb-6">Test Your Template</h2>
        
        <div className="space-y-6">
          {/* Test Parameters */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Test Parameters</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {parameters.map(param => (
                <div key={param.name}>
                  <label className="block text-xs sm:text-sm font-medium text-gray-700">
                    {param.name}
                    {param.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <input
                    type={param.dataType === 'number' ? 'number' : param.dataType === 'date' ? 'date' : 'text'}
                    value={testValues[param.name] || ''}
                    onChange={(e) => setTestValues({...testValues, [param.name]: e.target.value})}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                  />
                </div>
              ))}
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex space-x-4">
            <button 
              onClick={generatePreview}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
            >
              Generate Preview
            </button>
            <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm">
              Run Test Query
            </button>
          </div>
          
          {/* Generated SQL */}
          {generatedSQL && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-700">Generated SQL:</h3>
                <button className="text-gray-400 hover:text-gray-600">
                  <Copy className="h-4 w-4" />
                </button>
              </div>
              <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-xs sm:text-sm overflow-x-auto">
                <pre className="whitespace-pre-wrap">{generatedSQL}</pre>
              </div>
            </div>
          )}
          
          {/* Cost Estimate */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <span className="text-sm font-medium text-blue-900">Estimated Cost: $0.0234</span>
              <span className="text-sm text-blue-700">Estimated Time: ~45 seconds</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplateEditor;