import { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, Hash, Calendar, DollarSign, Copy, Plus, Server, FileText, Package } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import SQLEditor from '../common/SQLEditor';
import { dataSourceService } from '../../services/dataSourceService';
import type { DataSource, SchemaField } from '../../types/dataSource';
import { toast } from 'react-hot-toast';

interface QueryEditorStepProps {
  state: any;
  setState: (state: any) => void;
  instances?: any[];
  onNavigateToStep?: (step: number) => void;
  currentStep?: number;
}

export default function QueryEditorStep({ state, setState }: QueryEditorStepProps) {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [expandedDataSources, setExpandedDataSources] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [detectedParams, setDetectedParams] = useState<string[]>([]);

  // Fetch data sources from API
  const { data: dataSources = [], isLoading: dataSourcesLoading } = useQuery({
    queryKey: ['data-sources'],
    queryFn: () => dataSourceService.listDataSources(),
  });

  // Fetch fields for expanded data sources
  const [dataSourceFields, setDataSourceFields] = useState<Record<string, SchemaField[]>>({});
  
  // Load fields when a data source is expanded
  const loadDataSourceFields = async (schemaId: string) => {
    if (!dataSourceFields[schemaId]) {
      try {
        const fields = await dataSourceService.getSchemaFields(schemaId);
        setDataSourceFields(prev => ({ ...prev, [schemaId]: fields }));
      } catch (error) {
        console.error('Failed to load fields for', schemaId, error);
      }
    }
  };

  // Detect parameters in SQL query
  useEffect(() => {
    const paramPattern = /\{\{(\w+)\}\}/g;
    const matches = state.sqlQuery.matchAll(paramPattern);
    const params = Array.from(matches, (m: RegExpMatchArray) => m[1]);
    setDetectedParams([...new Set(params)]);
    
    // Update parameters with defaults if new ones detected
    const newParams = { ...state.parameters };
    params.forEach(param => {
      if (!(param in newParams)) {
        // Set default values based on parameter name
        if (param.includes('date') || param.includes('start') || param.includes('end')) {
          newParams[param] = new Date().toISOString().split('T')[0];
        } else if (param.includes('days') || param.includes('window')) {
          newParams[param] = 30;
        } else if (param.includes('campaign')) {
          newParams[param] = [];
        } else {
          newParams[param] = '';
        }
      }
    });
    
    if (JSON.stringify(newParams) !== JSON.stringify(state.parameters)) {
      setState((prev: any) => ({ ...prev, parameters: newParams }));
    }
  }, [state.sqlQuery]);

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(category)) {
        newSet.delete(category);
      } else {
        newSet.add(category);
      }
      return newSet;
    });
  };

  const toggleDataSource = async (schemaId: string) => {
    setExpandedDataSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(schemaId)) {
        newSet.delete(schemaId);
      } else {
        newSet.add(schemaId);
        // Load fields when expanding
        loadDataSourceFields(schemaId);
      }
      return newSet;
    });
  };

  const handleAddToQuery = (text: string) => {
    // Insert at cursor position in SQL editor
    const currentQuery = state.sqlQuery;
    const newQuery = currentQuery ? `${currentQuery}\n${text}` : text;
    setState((prev: any) => ({ ...prev, sqlQuery: newQuery }));
    toast.success('Added to query');
  };

  const handleCopyField = (fieldName: string) => {
    navigator.clipboard.writeText(fieldName);
    toast.success('Copied to clipboard');
  };

  // Group data sources by category
  const dataSourcesByCategory = dataSources.reduce((acc, ds) => {
    if (!acc[ds.category]) {
      acc[ds.category] = [];
    }
    acc[ds.category].push(ds);
    return acc;
  }, {} as Record<string, DataSource[]>);

  // Filter data sources based on search
  const getFilteredDataSources = (category: string) => {
    const sources = dataSourcesByCategory[category] || [];
    if (!searchQuery) return sources;
    
    const lowerSearch = searchQuery.toLowerCase();
    return sources.filter(ds => 
      ds.name.toLowerCase().includes(lowerSearch) ||
      ds.description?.toLowerCase().includes(lowerSearch) ||
      ds.schema_id.toLowerCase().includes(lowerSearch)
    );
  };

  // Get icon for field type
  const getFieldIcon = (dataType: string) => {
    const upperType = dataType.toUpperCase();
    if (upperType.includes('STRING')) return Hash;
    if (upperType.includes('LONG') || upperType.includes('INTEGER')) return Hash;
    if (upperType.includes('DECIMAL') || upperType.includes('FLOAT')) return DollarSign;
    if (upperType.includes('DATE') || upperType.includes('TIMESTAMP')) return Calendar;
    if (upperType.includes('ARRAY')) return Package;
    return Hash;
  };

  return (
    <div className="flex h-full">
      {/* Left Panel - Schema Explorer */}
      <div className="w-96 bg-gray-50 border-r border-gray-200 overflow-y-auto">
        <div className="p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">AMC Data Sources</h3>
          
          {/* Search */}
          <input
            type="text"
            placeholder="Search schemas and fields..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-4"
          />

          {/* Data Sources */}
          <div className="space-y-2">
            {dataSourcesLoading ? (
              <div className="text-sm text-gray-500 text-center py-4">Loading data sources...</div>
            ) : Object.keys(dataSourcesByCategory).length === 0 ? (
              <div className="text-sm text-gray-500 text-center py-4">No data sources available</div>
            ) : (
              Object.entries(dataSourcesByCategory).map(([category]) => {
                const isExpanded = expandedCategories.has(category);
                const filteredSources = getFilteredDataSources(category);
                
                if (filteredSources.length === 0 && searchQuery) return null;

                return (
                  <div key={category}>
                    <button
                      onClick={() => toggleCategory(category)}
                      className="w-full text-left px-2 py-1 hover:bg-gray-100 rounded flex items-center"
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-3 w-3 mr-1" />
                      ) : (
                        <ChevronRight className="h-3 w-3 mr-1" />
                      )}
                      <Server className="h-3 w-3 mr-2 text-gray-500" />
                      <span className="text-sm font-medium">{category}</span>
                      <span className="ml-auto text-xs text-gray-500">{filteredSources.length}</span>
                    </button>

                    {isExpanded && (
                      <div className="ml-4 mt-1 space-y-1">
                        {filteredSources.map(ds => {
                          const isDataSourceExpanded = expandedDataSources.has(ds.schema_id);
                          const fields = dataSourceFields[ds.schema_id] || [];

                          return (
                            <div key={ds.schema_id}>
                              <div className="flex items-center group">
                                <button
                                  onClick={() => toggleDataSource(ds.schema_id)}
                                  className="flex-1 text-left px-2 py-1 hover:bg-gray-100 rounded flex items-center"
                                  title={ds.description}
                                >
                                  {isDataSourceExpanded ? (
                                    <ChevronDown className="h-3 w-3 mr-1" />
                                  ) : (
                                    <ChevronRight className="h-3 w-3 mr-1" />
                                  )}
                                  <FileText className="h-3 w-3 mr-2 text-gray-400" />
                                  <span className="text-xs font-mono truncate">{ds.name}</span>
                                </button>
                                <button
                                  onClick={() => handleAddToQuery(ds.schema_id)}
                                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 rounded"
                                  title="Add to query"
                                >
                                  <Plus className="h-3 w-3 text-gray-500" />
                                </button>
                              </div>

                              {isDataSourceExpanded && (
                                <div className="ml-6 mt-1 space-y-0.5">
                                  {fields.length === 0 ? (
                                    <div className="text-xs text-gray-400 px-2 py-1">Loading fields...</div>
                                  ) : (
                                    fields.map(field => {
                                      const FieldIcon = getFieldIcon(field.data_type);
                                      
                                      return (
                                        <div
                                          key={field.id}
                                          className="flex items-center group px-2 py-0.5 hover:bg-gray-100 rounded"
                                          title={field.description}
                                        >
                                          <FieldIcon className="h-3 w-3 mr-2 text-gray-400" />
                                          <span className="text-xs font-mono text-gray-700 flex-1 truncate">
                                            {field.field_name}
                                          </span>
                                          <span className="text-xs text-gray-500 mr-2">
                                            {field.dimension_or_metric === 'Dimension' ? 'D' : 'M'}
                                          </span>
                                          <button
                                            onClick={() => handleCopyField(`${ds.schema_id}.${field.field_name}`)}
                                            className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-gray-200 rounded"
                                            title="Copy field name"
                                          >
                                            <Copy className="h-3 w-3 text-gray-500" />
                                          </button>
                                        </div>
                                      );
                                    })
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Right Panel - SQL Editor */}
      <div className="flex-1 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-sm font-semibold text-gray-900">SQL Query</h3>
              <p className="text-xs text-gray-500 mt-1">
                Use {'{{parameter}}'} syntax for dynamic parameters
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(state.sqlQuery);
                  toast.success('Query copied to clipboard');
                }}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <Copy className="h-4 w-4 inline mr-1" />
                Copy
              </button>
            </div>
          </div>
          
          {/* Show detected parameters */}
          {detectedParams.length > 0 && (
            <div className="mt-2">
              <span className="text-xs text-gray-500">Detected parameters: </span>
              {detectedParams.map(param => (
                <span
                  key={param}
                  className="inline-block px-2 py-0.5 ml-1 text-xs bg-blue-100 text-blue-700 rounded"
                >
                  {`{{${param}}}`}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex-1 min-h-0 p-6">
          <SQLEditor
            value={state.sqlQuery || `-- Enter your AMC SQL query here
-- Example:
SELECT 
    campaign_id,
    COUNT(DISTINCT user_id) as unique_users,
    SUM(conversion_value) as total_value
FROM amazon_attributed_events
WHERE 
    event_dt >= '{{start_date}}'
    AND event_dt <= '{{end_date}}'
GROUP BY campaign_id`}
            onChange={(value) => setState((prev: any) => ({ ...prev, sqlQuery: value }))}
            height="450px"
          />
        </div>

        {/* Query Metadata */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center space-x-4">
              <span>{state.sqlQuery.split('\n').length} lines</span>
              <span>{state.sqlQuery.length} characters</span>
              <span>{detectedParams.length} parameters</span>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                placeholder="Query name..."
                value={state.name}
                onChange={(e) => setState((prev: any) => ({ ...prev, name: e.target.value }))}
                className="px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}