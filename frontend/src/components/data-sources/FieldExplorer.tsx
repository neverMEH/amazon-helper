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
  Check,
  Code
} from 'lucide-react';
import type { SchemaField } from '../../types/dataSource';
import { dataSourceService } from '../../services/dataSourceService';

interface FieldExplorerProps {
  fields: SchemaField[];
  searchQuery?: string;
  onShowExample?: (fieldName: string) => void;
}

export function FieldExplorer({ fields, searchQuery = '', onShowExample }: FieldExplorerProps) {
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

      {/* Fields Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
        <table className="w-full table-fixed">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="w-[5%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="w-[25%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Field Name
              </th>
              <th className="w-[15%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Data Type
              </th>
              <th className="w-[10%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Threshold
              </th>
              <th className="w-[35%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="w-[10%] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {Object.entries(groupedFields).map(([category, categoryFields]) => {
              const isExpanded = expandedCategories.has(category) || Object.keys(groupedFields).length === 1;
              
              return (
                <>
                  {/* Category Header Row */}
                  <tr key={`category-${category}`} className="bg-gray-50">
                    <td colSpan={6} className="px-4 py-2">
                      <button
                        onClick={() => toggleCategory(category)}
                        className="w-full flex items-center gap-2 text-left"
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4 text-gray-500" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-gray-500" />
                        )}
                        <span className="text-sm font-medium text-gray-700">
                          {category}
                        </span>
                        <span className="text-xs text-gray-500">
                          ({categoryFields.length} fields)
                        </span>
                      </button>
                    </td>
                  </tr>
                  
                  {/* Field Rows */}
                  {isExpanded && categoryFields.map(field => {
                    const Icon = getDataTypeIcon(field.data_type);
                    
                    return (
                      <tr key={field.id} className="hover:bg-gray-50">
                        {/* Type Column */}
                        <td className="px-4 py-3 w-[5%]">
                          <span className={`px-1.5 py-0.5 text-xs rounded font-medium ${
                            field.dimension_or_metric === 'Dimension' 
                              ? 'bg-blue-100 text-blue-700' 
                              : 'bg-green-100 text-green-700'
                          }`}>
                            {field.dimension_or_metric === 'Dimension' ? 'D' : 'M'}
                          </span>
                        </td>
                        
                        {/* Field Name Column */}
                        <td className="px-4 py-3 w-[25%]">
                          <div className="flex items-center gap-2">
                            <code className="text-sm font-mono text-gray-900 font-medium break-all">
                              {field.field_name}
                            </code>
                            <button
                              onClick={() => copyFieldName(field.field_name)}
                              className="p-1 hover:bg-gray-200 rounded transition-colors flex-shrink-0"
                              title="Copy field name"
                            >
                              {copiedField === field.field_name ? (
                                <Check className="h-3 w-3 text-green-600" />
                              ) : (
                                <Copy className="h-3 w-3 text-gray-400" />
                              )}
                            </button>
                          </div>
                        </td>
                        
                        {/* Data Type Column */}
                        <td className="px-4 py-3 w-[15%]">
                          <div className="flex items-center gap-1 text-xs text-gray-600">
                            <Icon className="h-3 w-3" />
                            <span>{field.data_type}</span>
                          </div>
                          {field.is_nullable && (
                            <span className="text-xs text-gray-400">Nullable</span>
                          )}
                          {field.is_array && (
                            <span className="text-xs text-gray-400 ml-1">Array</span>
                          )}
                        </td>
                        
                        {/* Threshold Column */}
                        <td className="px-4 py-3 w-[10%]">
                          <span className={`px-1.5 py-0.5 text-xs rounded ${
                            dataSourceService.getThresholdColor(field.aggregation_threshold)
                          }`}>
                            {field.aggregation_threshold}
                          </span>
                        </td>
                        
                        {/* Description Column */}
                        <td className="px-4 py-3 w-[35%]">
                          <p className="text-sm text-gray-600 line-clamp-2">
                            {field.description}
                          </p>
                          {field.examples && field.examples.length > 0 && (
                            <div className="mt-1">
                              <span className="text-xs text-gray-500">Examples: </span>
                              <span className="text-xs text-gray-600">
                                {field.examples.slice(0, 2).join(', ')}
                                {field.examples.length > 2 && '...'}
                              </span>
                            </div>
                          )}
                        </td>
                        
                        {/* Actions Column */}
                        <td className="px-4 py-3 w-[10%]">
                          <div className="flex items-center gap-0.5">
                            {field.examples && field.examples.length > 0 && onShowExample && (
                              <button
                                onClick={() => onShowExample(field.field_name)}
                                className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                title="View examples using this field"
                              >
                                <Code className="h-3.5 w-3.5" />
                              </button>
                            )}
                            <button
                              onClick={() => setShowDetails(showDetails === field.id ? null : field.id)}
                              className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                              title="View field details"
                            >
                              <Info className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </>
              );
            })}
          </tbody>
        </table>
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