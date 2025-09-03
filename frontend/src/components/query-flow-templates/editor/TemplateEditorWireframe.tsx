import React, { useState } from 'react';
import { 
  ArrowLeft, 
  Save, 
  Play, 
  AlertCircle, 
  Check, 
  Plus, 
  Settings, 
  Trash2, 
  ChevronUp, 
  ChevronDown,
  Code,
  Eye,
  Database
} from 'lucide-react';

/**
 * Wireframe/Mockup for the Query Flow Template Editor
 * This demonstrates the UI layout and interaction patterns
 */
const TemplateEditorWireframe: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'metadata' | 'sql' | 'parameters' | 'visualizations' | 'preview'>('metadata');
  const [autoSave, setAutoSave] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  
  // Mock detected parameters
  const detectedParameters = ['start_date', 'end_date', 'campaign_ids', 'limit'];

  const tabs = [
    { id: 'metadata', label: 'Metadata', icon: null },
    { id: 'sql', label: 'SQL Template', icon: <Code className="h-4 w-4" /> },
    { id: 'parameters', label: 'Parameters', icon: null },
    { id: 'visualizations', label: 'Visualizations', icon: null },
    { id: 'preview', label: 'Preview & Test', icon: <Eye className="h-4 w-4" /> }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button className="flex items-center text-gray-600 hover:text-gray-900">
              <ArrowLeft className="h-5 w-5 mr-2" />
              Back
            </button>
            <h1 className="text-xl font-semibold text-gray-900">Query Flow Template Editor</h1>
          </div>
          <div className="flex items-center space-x-3">
            <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
              Save Draft
            </button>
            <button className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">
              <Play className="h-4 w-4 inline mr-1" />
              Test
            </button>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="bg-blue-50 border-b border-blue-200 px-6 py-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <span className="flex items-center">
              <div className="h-2 w-2 bg-yellow-400 rounded-full mr-2"></div>
              Unsaved changes
            </span>
            <span className="text-gray-600">Last saved: 2 minutes ago</span>
          </div>
          <div className="flex items-center">
            <span className="text-gray-600 mr-2">Auto-save:</span>
            <button 
              onClick={() => setAutoSave(!autoSave)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full ${autoSave ? 'bg-indigo-600' : 'bg-gray-200'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${autoSave ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2
                  ${activeTab === tab.id 
                    ? 'border-indigo-500 text-indigo-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                `}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="px-6 py-6">
        {activeTab === 'metadata' && <MetadataTab />}
        {activeTab === 'sql' && <SQLTemplateTab detectedParameters={detectedParameters} />}
        {activeTab === 'parameters' && <ParametersTab parameters={detectedParameters} />}
        {activeTab === 'visualizations' && <VisualizationsTab />}
        {activeTab === 'preview' && <PreviewTab />}
      </div>
    </div>
  );
};

// Metadata Tab Component
const MetadataTab: React.FC = () => (
  <div className="max-w-4xl mx-auto">
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-6">Template Information</h2>
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Template ID <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="campaign_performance"
          />
          <p className="mt-1 text-sm text-gray-500">Must be unique, lowercase, underscores only</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="Campaign Performance Analysis"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Category <span className="text-red-500">*</span>
          </label>
          <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
            <option>Performance</option>
            <option>Attribution</option>
            <option>Audience</option>
            <option>Custom</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Description</label>
          <textarea
            rows={4}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="Analyze campaign metrics including impressions, clicks, conversions, and ROAS"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800">
              performance
              <button className="ml-2 text-indigo-600 hover:text-indigo-800">×</button>
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800">
              campaign
              <button className="ml-2 text-indigo-600 hover:text-indigo-800">×</button>
            </span>
            <button className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border-2 border-dashed border-gray-300 text-gray-600 hover:border-gray-400">
              <Plus className="h-4 w-4 mr-1" />
              Add Tag
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Visibility</label>
          <div className="space-x-6">
            <label className="inline-flex items-center">
              <input type="radio" name="visibility" className="form-radio" defaultChecked />
              <span className="ml-2">Public</span>
            </label>
            <label className="inline-flex items-center">
              <input type="radio" name="visibility" className="form-radio" />
              <span className="ml-2">Private</span>
            </label>
            <label className="inline-flex items-center">
              <input type="radio" name="visibility" className="form-radio" />
              <span className="ml-2">Team</span>
            </label>
          </div>
        </div>

        <div className="flex items-center space-x-6">
          <label className="inline-flex items-center">
            <input type="checkbox" className="form-checkbox" defaultChecked />
            <span className="ml-2">Active</span>
          </label>
          <label className="inline-flex items-center">
            <input type="checkbox" className="form-checkbox" />
            <span className="ml-2">Featured</span>
          </label>
        </div>
      </div>
    </div>
  </div>
);

// SQL Template Tab Component
const SQLTemplateTab: React.FC<{ detectedParameters: string[] }> = ({ detectedParameters }) => (
  <div className="max-w-7xl mx-auto">
    <div className="bg-white rounded-lg shadow">
      {/* Toolbar */}
      <div className="border-b border-gray-200 px-6 py-3 flex items-center space-x-4">
        <button className="text-sm font-medium text-gray-700 hover:text-gray-900">Format SQL</button>
        <button className="text-sm font-medium text-gray-700 hover:text-gray-900">Validate</button>
        <button className="text-sm font-medium text-gray-700 hover:text-gray-900">Insert Parameter</button>
      </div>
      
      {/* Split View */}
      <div className="flex">
        {/* SQL Editor */}
        <div className="flex-1 p-6 border-r border-gray-200">
          <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm" style={{ minHeight: '400px' }}>
            <pre>{`WITH campaign_metrics AS (
  SELECT 
    campaign,
    campaign_id,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    SUM(conversions) as total_conversions,
    CAST(SUM(clicks) AS DOUBLE) / SUM(impressions) as ctr
  FROM impressions_clicks_conversions
  WHERE 
    event_dt BETWEEN :start_date AND :end_date
    {% if campaign_ids %}
    AND campaign_id IN (:campaign_ids)
    {% endif %}
  GROUP BY campaign, campaign_id
)
SELECT * FROM campaign_metrics
ORDER BY total_clicks DESC
LIMIT :limit`}</pre>
          </div>
        </div>
        
        {/* Helper Panel */}
        <div className="w-80 p-6 bg-gray-50">
          {/* Parameter Detection */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
              <AlertCircle className="h-4 w-4 mr-2 text-green-500" />
              Detected Parameters
            </h3>
            <div className="bg-white rounded-lg p-3 space-y-2">
              {detectedParameters.map(param => (
                <div key={param} className="text-sm text-gray-600">
                  • :{param}
                </div>
              ))}
              <div className="text-sm text-gray-500 italic">
                • {'{% if campaign_ids %}'}
              </div>
            </div>
          </div>
          
          {/* Available Tables */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
              <Database className="h-4 w-4 mr-2" />
              Available Tables
            </h3>
            <div className="bg-white rounded-lg p-3 space-y-1">
              <div className="text-sm text-gray-600">• impressions</div>
              <div className="text-sm text-gray-600">• clicks</div>
              <div className="text-sm text-gray-600">• conversions</div>
              <div className="text-sm text-gray-600">• impressions_clicks_conversions</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Validation Status */}
      <div className="border-t border-gray-200 px-6 py-3 flex items-center text-sm">
        <Check className="h-4 w-4 text-green-500 mr-2" />
        <span className="text-green-700">SQL is valid</span>
        <span className="mx-2 text-gray-400">|</span>
        <span className="text-gray-600">{detectedParameters.length} parameters detected</span>
      </div>
    </div>
  </div>
);

// Parameters Tab Component
const ParametersTab: React.FC<{ parameters: string[] }> = ({ parameters }) => (
  <div className="max-w-4xl mx-auto">
    <div className="space-y-4">
      {parameters.map((param, index) => (
        <ParameterCard key={param} name={param} index={index} />
      ))}
      
      <button className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-700 flex items-center justify-center">
        <Plus className="h-5 w-5 mr-2" />
        Add Parameter Manually
      </button>
    </div>
  </div>
);

// Parameter Card Component
const ParameterCard: React.FC<{ name: string; index: number }> = ({ name, index }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-medium text-gray-900">Parameter: {name}</h3>
      <div className="flex items-center space-x-2">
        <button className="text-gray-400 hover:text-gray-600">
          <ChevronUp className="h-5 w-5" />
        </button>
        <button className="text-gray-400 hover:text-gray-600">
          <ChevronDown className="h-5 w-5" />
        </button>
        <button className="text-red-400 hover:text-red-600">
          <Trash2 className="h-5 w-5" />
        </button>
      </div>
    </div>
    
    <div className="grid grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">Display Name</label>
        <input
          type="text"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          defaultValue={name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700">Type</label>
        <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
          <option>Date</option>
          <option>Date Range</option>
          <option>String</option>
          <option>Number</option>
          <option>Campaign List</option>
          <option>ASIN List</option>
        </select>
      </div>
      
      <div className="col-span-2 flex items-center space-x-6">
        <label className="inline-flex items-center">
          <input type="checkbox" className="form-checkbox" defaultChecked />
          <span className="ml-2 text-sm">Required</span>
        </label>
        {name.includes('ids') && (
          <label className="inline-flex items-center">
            <input type="checkbox" className="form-checkbox" defaultChecked />
            <span className="ml-2 text-sm">Multi-select</span>
          </label>
        )}
      </div>
    </div>
  </div>
);

// Visualizations Tab Component
const VisualizationsTab: React.FC = () => (
  <div className="max-w-4xl mx-auto">
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Performance Table</h3>
            <p className="text-sm text-gray-500">Type: Table | Default: Yes</p>
          </div>
          <div className="flex items-center space-x-2">
            <button className="text-green-500">
              <Check className="h-5 w-5" />
            </button>
            <button className="text-gray-400 hover:text-gray-600">
              <Settings className="h-5 w-5" />
            </button>
            <button className="text-red-400 hover:text-red-600">
              <Trash2 className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Revenue by Campaign</h3>
            <p className="text-sm text-gray-500">Type: Bar Chart | X: campaign | Y: revenue</p>
          </div>
          <div className="flex items-center space-x-2">
            <button className="text-green-500">
              <Check className="h-5 w-5" />
            </button>
            <button className="text-gray-400 hover:text-gray-600">
              <Settings className="h-5 w-5" />
            </button>
            <button className="text-red-400 hover:text-red-600">
              <Trash2 className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
      
      <button className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-700 flex items-center justify-center">
        <Plus className="h-5 w-5 mr-2" />
        Add Visualization
      </button>
    </div>
  </div>
);

// Preview Tab Component
const PreviewTab: React.FC = () => (
  <div className="max-w-6xl mx-auto">
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-6">Test Your Template</h2>
      
      <div className="space-y-6">
        {/* Test Parameters */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Start Date</label>
            <input
              type="date"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              defaultValue="2024-01-01"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">End Date</label>
            <input
              type="date"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              defaultValue="2024-12-31"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Campaigns</label>
            <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
              <option>All Campaigns</option>
              <option>Selected Campaigns...</option>
            </select>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex space-x-4">
          <button className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
            Generate Preview
          </button>
          <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
            Run Test Query
          </button>
        </div>
        
        {/* Generated SQL */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Generated SQL:</h3>
          <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm">
            <pre>{`WITH campaign_metrics AS (
  SELECT 
    campaign,
    campaign_id,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    SUM(conversions) as total_conversions
  FROM impressions_clicks_conversions
  WHERE 
    event_dt BETWEEN '2024-01-01' AND '2024-12-31'
  GROUP BY campaign, campaign_id
)
SELECT * FROM campaign_metrics
ORDER BY total_clicks DESC
LIMIT 100`}</pre>
          </div>
        </div>
        
        {/* Cost Estimate */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900">Estimated Cost: $0.0234</span>
            <span className="text-sm text-blue-700">Estimated Time: ~45 seconds</span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default TemplateEditorWireframe;