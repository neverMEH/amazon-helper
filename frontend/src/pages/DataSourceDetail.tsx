/**
 * Data Source Detail Page
 * Display complete schema documentation with fields, examples, and sections
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import {
  ArrowLeft,
  Database,
  Code,
  Table,
  BookOpen,
  Link2,
  Tag,
  Lock,
  Globe,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  Hash,
  Type,
  Calendar,
  ToggleLeft,
  List,
  Calculator,
  FileText,
  Search,
  ExternalLink
} from 'lucide-react';
import { dataSourceService } from '../services/dataSourceService';
import SQLHighlight from '../components/common/SQLHighlight';
import type { SchemaField, QueryExample } from '../types/dataSource';

export default function DataSourceDetail() {
  const { schemaId } = useParams<{ schemaId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [activeSection, setActiveSection] = useState('overview');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));
  const [copiedExample, setCopiedExample] = useState<string | null>(null);
  const [fieldSearch, setFieldSearch] = useState('');
  const [fieldTypeFilter, setFieldTypeFilter] = useState<'all' | 'Dimension' | 'Metric'>('all');
  const [thresholdFilter, setThresholdFilter] = useState<string>('all');

  // Fetch complete schema
  const { data: schema, isLoading, error } = useQuery({
    queryKey: ['dataSource', schemaId],
    queryFn: () => dataSourceService.getCompleteSchema(schemaId!),
    enabled: !!schemaId,
    staleTime: 10 * 60 * 1000
  });

  // Handle deep linking
  useEffect(() => {
    const hash = location.hash.replace('#', '');
    if (hash) {
      setActiveSection(hash);
      setExpandedSections(new Set([hash]));
      // Scroll to section after a short delay
      setTimeout(() => {
        const element = document.getElementById(hash);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    }
  }, [location.hash]);

  // Filter fields
  const filteredFields = schema?.fields.filter(field => {
    const matchesSearch = !fieldSearch || 
      field.field_name.toLowerCase().includes(fieldSearch.toLowerCase()) ||
      field.description.toLowerCase().includes(fieldSearch.toLowerCase());
    
    const matchesType = fieldTypeFilter === 'all' || field.dimension_or_metric === fieldTypeFilter;
    
    const matchesThreshold = thresholdFilter === 'all' || field.aggregation_threshold === thresholdFilter;
    
    return matchesSearch && matchesType && matchesThreshold;
  }) || [];

  // Group fields by category
  const groupedFields = filteredFields.reduce((acc, field) => {
    const category = field.field_category || 'General';
    if (!acc[category]) acc[category] = [];
    acc[category].push(field);
    return acc;
  }, {} as Record<string, SchemaField[]>);

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  const copyExample = async (example: QueryExample) => {
    try {
      await dataSourceService.copyToClipboard(example.sql_query);
      setCopiedExample(example.id);
      setTimeout(() => setCopiedExample(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const navigateToQueryBuilder = (example: QueryExample) => {
    // Store the example in session storage
    sessionStorage.setItem('queryBuilderDraft', JSON.stringify({
      name: example.title,
      description: example.description,
      sql_query: example.sql_query,
      parameters: example.parameters || {},
      fromDataSource: schema?.schema.schema_id
    }));
    navigate('/query-builder/new');
  };

  const getDataTypeIcon = (dataType: string) => {
    const icons: Record<string, any> = {
      'STRING': Type,
      'LONG': Hash,
      'INTEGER': Hash,
      'DECIMAL': Calculator,
      'FLOAT': Calculator,
      'BOOLEAN': ToggleLeft,
      'DATE': Calendar,
      'TIMESTAMP': Calendar,
      'ARRAY': List
    };
    const Icon = icons[dataType.toUpperCase()] || FileText;
    return <Icon className="h-4 w-4" />;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !schema) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Schema not found</h3>
          <button
            onClick={() => navigate('/data-sources')}
            className="text-blue-600 hover:text-blue-700"
          >
            Return to data sources
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => navigate('/data-sources')}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <ArrowLeft className="h-5 w-5" />
                </button>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-xl font-bold text-gray-900">
                      {schema.schema.name}
                    </h1>
                    {schema.schema.is_paid_feature && (
                      <Lock className="h-4 w-4 text-yellow-600" />
                    )}
                  </div>
                  <p className="text-sm text-gray-500">
                    {schema.schema.category} • v{schema.schema.version}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {schema.schema.availability?.marketplaces && (
                  <span className="flex items-center gap-1 text-sm text-gray-500">
                    <Globe className="h-4 w-4" />
                    {Object.keys(schema.schema.availability.marketplaces).length} regions
                  </span>
                )}
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="mt-4 flex gap-1 border-b">
              {[
                { id: 'overview', label: 'Overview', icon: BookOpen },
                { id: 'schema', label: `Fields (${schema.fields.length})`, icon: Table },
                { id: 'examples', label: `Examples (${schema.examples.length})`, icon: Code },
                { id: 'relationships', label: 'Relationships', icon: Link2 }
              ].map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveSection(tab.id);
                      window.location.hash = tab.id;
                    }}
                    className={`flex items-center gap-2 px-4 py-2 border-b-2 font-medium text-sm transition-colors ${
                      activeSection === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Section */}
        {activeSection === 'overview' && (
          <div className="space-y-6">
            {/* Description */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Description</h2>
              <p className="text-gray-600">{schema.schema.description}</p>
              
              {/* Data Sources */}
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">AMC Tables</h3>
                <div className="flex flex-wrap gap-2">
                  {schema.schema.data_sources.map(source => (
                    <code
                      key={source}
                      className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-sm"
                    >
                      {source}
                    </code>
                  ))}
                </div>
              </div>

              {/* Tags */}
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {schema.schema.tags.map(tag => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded text-sm"
                    >
                      <Tag className="h-3 w-3" />
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Documentation Sections */}
            {schema.sections.map(section => (
              <div key={section.id} className="bg-white rounded-lg shadow">
                <button
                  onClick={() => toggleSection(section.id)}
                  className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50"
                >
                  <h2 className="text-lg font-semibold capitalize">
                    {section.section_type.replace(/_/g, ' ')}
                  </h2>
                  {expandedSections.has(section.id) ? (
                    <ChevronDown className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  )}
                </button>
                {expandedSections.has(section.id) && (
                  <div className="px-6 pb-6 prose prose-sm max-w-none">
                    <ReactMarkdown>{section.content_markdown}</ReactMarkdown>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Schema Fields Section */}
        {activeSection === 'schema' && (
          <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex flex-wrap gap-4">
                <div className="flex-1 min-w-[200px]">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      value={fieldSearch}
                      onChange={(e) => setFieldSearch(e.target.value)}
                      placeholder="Search fields..."
                      className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <select
                  value={fieldTypeFilter}
                  onChange={(e) => setFieldTypeFilter(e.target.value as any)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-1 focus:ring-blue-500"
                >
                  <option value="all">All Types</option>
                  <option value="Dimension">Dimensions</option>
                  <option value="Metric">Metrics</option>
                </select>
                
                <select
                  value={thresholdFilter}
                  onChange={(e) => setThresholdFilter(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-1 focus:ring-blue-500"
                >
                  <option value="all">All Thresholds</option>
                  <option value="NONE">None</option>
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="VERY_HIGH">Very High</option>
                  <option value="INTERNAL">Internal</option>
                </select>
              </div>
            </div>

            {/* Fields Table */}
            {Object.entries(groupedFields).map(([category, fields]) => (
              <div key={category} className="bg-white rounded-lg shadow overflow-hidden">
                <div className="px-6 py-3 bg-gray-50 border-b">
                  <h3 className="text-sm font-medium text-gray-700">
                    {category} ({fields.length} fields)
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Field Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          D/M
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Description
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Threshold
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {fields.map(field => (
                        <tr key={field.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <code className="text-sm font-mono text-gray-900">
                              {field.field_name}
                            </code>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-1 text-sm text-gray-600">
                              {getDataTypeIcon(field.data_type)}
                              <span>{field.data_type}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              field.dimension_or_metric === 'Dimension'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-green-100 text-green-700'
                            }`}>
                              {field.dimension_or_metric}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600">
                            <div className="max-w-md">
                              {field.description}
                              {field.examples && field.examples.length > 0 && (
                                <div className="mt-1">
                                  <span className="text-xs text-gray-500">Examples: </span>
                                  <span className="text-xs text-gray-700">
                                    {field.examples.join(', ')}
                                  </span>
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded ${
                              dataSourceService.getThresholdColor(field.aggregation_threshold)
                            }`}>
                              {field.aggregation_threshold}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Query Examples Section */}
        {activeSection === 'examples' && (
          <div className="space-y-6">
            {schema.examples.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <Code className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No query examples available yet</p>
              </div>
            ) : (
              schema.examples.map(example => (
                <div key={example.id} className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {example.title}
                        </h3>
                        {example.description && (
                          <p className="mt-1 text-sm text-gray-600">
                            {example.description}
                          </p>
                        )}
                        <span className="inline-block mt-2 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          {example.category || 'General'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => copyExample(example)}
                          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                          title="Copy SQL"
                        >
                          {copiedExample === example.id ? (
                            <Check className="h-4 w-4 text-green-600" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          onClick={() => navigateToQueryBuilder(example)}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                        >
                          Open in Query Builder
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="p-6">
                    <SQLHighlight sql={example.sql_query} />
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Relationships Section */}
        {activeSection === 'relationships' && (
          <div className="space-y-6">
            {/* Outgoing Relationships */}
            {schema.relationships.from.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Related Schemas</h2>
                <div className="space-y-3">
                  {schema.relationships.from.map(rel => (
                    <div
                      key={rel.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-3">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                          {rel.relationship_type}
                        </span>
                        <div>
                          <button
                            onClick={() => navigate(`/data-sources/${rel.target?.schema_id}`)}
                            className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                          >
                            {rel.target?.name}
                            <ExternalLink className="h-3 w-3" />
                          </button>
                          {rel.description && (
                            <p className="text-sm text-gray-600 mt-1">{rel.description}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Incoming Relationships */}
            {schema.relationships.to.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Referenced By</h2>
                <div className="space-y-3">
                  {schema.relationships.to.map(rel => (
                    <div
                      key={rel.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-3">
                        <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                          {rel.relationship_type}
                        </span>
                        <div>
                          <button
                            onClick={() => navigate(`/data-sources/${rel.source?.schema_id}`)}
                            className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                          >
                            {rel.source?.name}
                            <ExternalLink className="h-3 w-3" />
                          </button>
                          {rel.description && (
                            <p className="text-sm text-gray-600 mt-1">{rel.description}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {schema.relationships.from.length === 0 && schema.relationships.to.length === 0 && (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <Link2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No relationships defined for this schema</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}