import { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  Hash,
  Type,
  Calendar,
  ToggleLeft,
  List as ListIcon,
  Calculator,
  FileText,
  ChevronDown,
  ChevronRight,
  Info,
  Copy,
  Check
} from 'lucide-react';
import type { SchemaField } from '../../types/dataSource';
import { dataSourceService } from '../../services/dataSourceService';

interface FieldExplorerProps {
  fields: SchemaField[];
  searchQuery?: string;
}

export function FieldExplorer({ fields, searchQuery = '' }: FieldExplorerProps) {
  const [localSearch, setLocalSearch] = useState('');
  const [selectedType, setSelectedType] = useState<'all' | 'Dimension' | 'Metric'>('all');
  const [selectedDataType, setSelectedDataType] = useState<string>('all');
  const [selectedThreshold, setSelectedThreshold] = useState<string>('all');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState<string | null>(null);

  const search = localSearch || searchQuery;

  // Get unique data types
  const dataTypes = useMemo(() => {
    const types = new Set(fields.map(f => f.data_type));
    return Array.from(types).sort();
  }, [fields]);

  // Filter fields
  const filteredFields = useMemo(() => {
    return fields.filter(field => {
      const matchesSearch = !search || 
        field.field_name.toLowerCase().includes(search.toLowerCase()) ||
        field.description.toLowerCase().includes(search.toLowerCase());
      
      const matchesType = selectedType === 'all' || field.dimension_or_metric === selectedType;
      const matchesDataType = selectedDataType === 'all' || field.data_type === selectedDataType;
      const matchesThreshold = selectedThreshold === 'all' || field.aggregation_threshold === selectedThreshold;
      
      return matchesSearch && matchesType && matchesDataType && matchesThreshold;
    });
  }, [fields, search, selectedType, selectedDataType, selectedThreshold]);

  // Group fields by category
  const groupedFields = useMemo(() => {
    const groups: Record<string, SchemaField[]> = {};
    filteredFields.forEach(field => {
      const category = field.field_category || 'General';
      if (!groups[category]) groups[category] = [];
      groups[category].push(field);
    });
    return groups;
  }, [filteredFields]);

  // Stats
  const stats = useMemo(() => {
    const dimensions = filteredFields.filter(f => f.dimension_or_metric === 'Dimension').length;
    const metrics = filteredFields.filter(f => f.dimension_or_metric === 'Metric').length;
    return { dimensions, metrics, total: filteredFields.length };
  }, [filteredFields]);

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

  const copyFieldName = async (fieldName: string) => {
    try {
      await navigator.clipboard.writeText(fieldName);
      setCopiedField(fieldName);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getDataTypeIcon = (dataType: string) => {
    const upperType = dataType.toUpperCase();
    if (upperType.includes('STRING')) return Type;
    if (upperType.includes('LONG') || upperType.includes('INTEGER')) return Hash;
    if (upperType.includes('DECIMAL') || upperType.includes('FLOAT')) return Calculator;
    if (upperType.includes('BOOLEAN')) return ToggleLeft;
    if (upperType.includes('DATE') || upperType.includes('TIMESTAMP')) return Calendar;
    if (upperType.includes('ARRAY')) return ListIcon;
    return FileText;
  };

  return (
    <div className="space-y-4">
      {/* Search and Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="space-y-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              placeholder="Search fields by name or description..."
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Filter Row */}
          <div className="flex items-center gap-2 flex-wrap">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as 'all' | 'Dimension' | 'Metric')}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-1 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="Dimension">Dimensions Only</option>
              <option value="Metric">Metrics Only</option>
            </select>

            <select
              value={selectedDataType}
              onChange={(e) => setSelectedDataType(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-1 focus:ring-blue-500"
            >
              <option value="all">All Data Types</option>
              {dataTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>

            <select
              value={selectedThreshold}
              onChange={(e) => setSelectedThreshold(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-1 focus:ring-blue-500"
            >
              <option value="all">All Thresholds</option>
              <option value="NONE">None</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="VERY_HIGH">Very High</option>
              <option value="INTERNAL">Internal</option>
            </select>

            {/* Stats */}
            <div className="ml-auto flex items-center gap-3 text-sm">
              <span className="text-blue-600 font-medium">
                {stats.dimensions} Dimensions
              </span>
              <span className="text-gray-300">•</span>
              <span className="text-green-600 font-medium">
                {stats.metrics} Metrics
              </span>
              <span className="text-gray-300">•</span>
              <span className="text-gray-600">
                {stats.total} Total
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Fields by Category */}
      <div className="space-y-2">
        {Object.entries(groupedFields).map(([category, categoryFields]) => {
          const isExpanded = expandedCategories.has(category) || Object.keys(groupedFields).length === 1;
          
          return (
            <div key={category} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              {/* Category Header */}
              <button
                onClick={() => toggleCategory(category)}
                className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-gray-500" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-gray-500" />
                  )}
                  <h3 className="text-sm font-medium text-gray-700">
                    {category}
                  </h3>
                  <span className="text-xs text-gray-500">
                    ({categoryFields.length} fields)
                  </span>
                </div>
              </button>

              {/* Fields */}
              {isExpanded && (
                <div className="divide-y divide-gray-100">
                  {categoryFields.map(field => {
                    const Icon = getDataTypeIcon(field.data_type);
                    const isShowingDetails = showDetails === field.id;
                    
                    return (
                      <div key={field.id} className="p-3 hover:bg-gray-50 transition-colors">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className={`px-1.5 py-0.5 text-xs rounded font-medium ${
                                field.dimension_or_metric === 'Dimension' 
                                  ? 'bg-blue-100 text-blue-700' 
                                  : 'bg-green-100 text-green-700'
                              }`}>
                                {field.dimension_or_metric === 'Dimension' ? 'D' : 'M'}
                              </span>
                              <code className="text-sm font-mono text-gray-900 font-medium">
                                {field.field_name}
                              </code>
                              <button
                                onClick={() => copyFieldName(field.field_name)}
                                className="p-1 hover:bg-gray-200 rounded transition-colors"
                                title="Copy field name"
                              >
                                {copiedField === field.field_name ? (
                                  <Check className="h-3 w-3 text-green-600" />
                                ) : (
                                  <Copy className="h-3 w-3 text-gray-400" />
                                )}
                              </button>
                            </div>
                            
                            <div className="flex items-center gap-3 text-xs text-gray-500 mb-1">
                              <span className="flex items-center gap-1">
                                <Icon className="h-3 w-3" />
                                {field.data_type}
                              </span>
                              <span className={`px-1.5 py-0.5 rounded ${
                                dataSourceService.getThresholdColor(field.aggregation_threshold)
                              }`}>
                                {field.aggregation_threshold}
                              </span>
                              {field.is_nullable && (
                                <span className="text-gray-400">Nullable</span>
                              )}
                              {field.is_array && (
                                <span className="text-gray-400">Array</span>
                              )}
                            </div>
                            
                            <p className="text-sm text-gray-600">
                              {field.description}
                            </p>

                            {/* Examples and Details */}
                            {field.examples && field.examples.length > 0 && (
                              <button
                                onClick={() => setShowDetails(isShowingDetails ? null : field.id)}
                                className="mt-2 text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
                              >
                                <Info className="h-3 w-3" />
                                {isShowingDetails ? 'Hide' : 'Show'} examples
                              </button>
                            )}
                            
                            {isShowingDetails && field.examples && (
                              <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                                <span className="font-medium text-gray-700">Examples: </span>
                                <span className="text-gray-600">
                                  {field.examples.join(', ')}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* No Results */}
      {filteredFields.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Filter className="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-500">No fields match your filters</p>
          <button
            onClick={() => {
              setLocalSearch('');
              setSelectedType('all');
              setSelectedDataType('all');
              setSelectedThreshold('all');
            }}
            className="mt-3 text-sm text-blue-600 hover:text-blue-700"
          >
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
}