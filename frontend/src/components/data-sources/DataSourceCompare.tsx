import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  X,
  GitCompare,
  Check,
  Minus,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Hash,
  Type,
  TrendingUp,
  Database,
  Lock,
  Globe,
  Download,
  Share2
} from 'lucide-react';
import { dataSourceService } from '../../services/dataSourceService';
import type { DataSource } from '../../types/dataSource';

interface DataSourceCompareProps {
  isOpen: boolean;
  onClose: () => void;
  dataSourceIds: string[];
  dataSources: DataSource[];
}

interface ComparisonRow {
  property: string;
  category: string;
  values: (string | number | boolean | null)[];
  isDifferent: boolean;
}

export function DataSourceCompare({
  isOpen,
  onClose,
  dataSourceIds,
  dataSources
}: DataSourceCompareProps) {
  const [selectedSources, setSelectedSources] = useState<DataSource[]>([]);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));
  const [showOnlyDifferences, setShowOnlyDifferences] = useState(false);
  const [comparisonData, setComparisonData] = useState<ComparisonRow[]>([]);

  // Get the selected data sources
  useEffect(() => {
    const sources = dataSources.filter(ds => dataSourceIds.includes(ds.id));
    setSelectedSources(sources);
  }, [dataSourceIds, dataSources]);

  // Fetch fields for each selected data source
  const fieldQueries = selectedSources.map(source =>
    useQuery({
      queryKey: ['dataSourceFields', source.schema_id],
      queryFn: () => dataSourceService.getSchemaFields(source.schema_id),
      enabled: isOpen && !!source.schema_id,
      staleTime: 10 * 60 * 1000
    })
  );

  // Build comparison data
  useEffect(() => {
    if (selectedSources.length < 2) return;

    const rows: ComparisonRow[] = [];

    // Basic properties
    rows.push({
      property: 'Name',
      category: 'overview',
      values: selectedSources.map(s => s.name),
      isDifferent: new Set(selectedSources.map(s => s.name)).size > 1
    });

    rows.push({
      property: 'Category',
      category: 'overview',
      values: selectedSources.map(s => s.category),
      isDifferent: new Set(selectedSources.map(s => s.category)).size > 1
    });

    rows.push({
      property: 'Version',
      category: 'overview',
      values: selectedSources.map(s => s.version),
      isDifferent: new Set(selectedSources.map(s => s.version)).size > 1
    });

    rows.push({
      property: 'Paid Feature',
      category: 'overview',
      values: selectedSources.map(s => s.is_paid_feature),
      isDifferent: new Set(selectedSources.map(s => s.is_paid_feature)).size > 1
    });

    rows.push({
      property: 'Data Sources Count',
      category: 'overview',
      values: selectedSources.map(s => s.data_sources.length),
      isDifferent: new Set(selectedSources.map(s => s.data_sources.length)).size > 1
    });

    rows.push({
      property: 'Tags Count',
      category: 'overview',
      values: selectedSources.map(s => s.tags.length),
      isDifferent: new Set(selectedSources.map(s => s.tags.length)).size > 1
    });

    // Field statistics
    const allFieldsData = fieldQueries.map(q => q.data || []);
    if (allFieldsData.every(fields => fields.length > 0)) {
      rows.push({
        property: 'Total Fields',
        category: 'fields',
        values: allFieldsData.map(fields => fields.length),
        isDifferent: new Set(allFieldsData.map(fields => fields.length)).size > 1
      });

      rows.push({
        property: 'Dimensions',
        category: 'fields',
        values: allFieldsData.map(fields => 
          fields.filter(f => f.dimension_or_metric === 'Dimension').length
        ),
        isDifferent: new Set(allFieldsData.map(fields => 
          fields.filter(f => f.dimension_or_metric === 'Dimension').length
        )).size > 1
      });

      rows.push({
        property: 'Metrics',
        category: 'fields',
        values: allFieldsData.map(fields => 
          fields.filter(f => f.dimension_or_metric === 'Metric').length
        ),
        isDifferent: new Set(allFieldsData.map(fields => 
          fields.filter(f => f.dimension_or_metric === 'Metric').length
        )).size > 1
      });

      // Data types
      const dataTypes = ['STRING', 'LONG', 'INTEGER', 'DECIMAL', 'BOOLEAN', 'DATE', 'TIMESTAMP'];
      dataTypes.forEach(type => {
        const counts = allFieldsData.map(fields => 
          fields.filter(f => f.data_type === type).length
        );
        if (counts.some(c => c > 0)) {
          rows.push({
            property: `${type} Fields`,
            category: 'datatypes',
            values: counts,
            isDifferent: new Set(counts).size > 1
          });
        }
      });

      // Aggregation thresholds
      const thresholds = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH', 'INTERNAL'];
      thresholds.forEach(threshold => {
        const counts = allFieldsData.map(fields => 
          fields.filter(f => f.aggregation_threshold === threshold).length
        );
        if (counts.some(c => c > 0)) {
          rows.push({
            property: `${threshold} Threshold Fields`,
            category: 'thresholds',
            values: counts,
            isDifferent: new Set(counts).size > 1
          });
        }
      });
    }

    // Availability
    rows.push({
      property: 'Marketplace Count',
      category: 'availability',
      values: selectedSources.map(s => 
        s.availability?.marketplaces ? Object.keys(s.availability.marketplaces).length : 0
      ),
      isDifferent: new Set(selectedSources.map(s => 
        s.availability?.marketplaces ? Object.keys(s.availability.marketplaces).length : 0
      )).size > 1
    });

    setComparisonData(rows);
  }, [selectedSources, fieldQueries]);

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

  const getValueDisplay = (value: any) => {
    if (value === null || value === undefined) return <Minus className="h-4 w-4 text-gray-400" />;
    if (typeof value === 'boolean') {
      return value ? (
        <Check className="h-4 w-4 text-green-600" />
      ) : (
        <X className="h-4 w-4 text-red-600" />
      );
    }
    return value.toString();
  };

  const getValueColor = (isDifferent: boolean, index: number) => {
    if (!isDifferent) return 'text-gray-700';
    const colors = ['text-blue-600', 'text-green-600', 'text-purple-600', 'text-orange-600'];
    return colors[index % colors.length];
  };

  const exportComparison = () => {
    const csv = [
      ['Property', ...selectedSources.map(s => s.name)],
      ...comparisonData.map(row => [row.property, ...row.values])
    ];
    
    const csvContent = csv.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `data-source-comparison-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  const categories = [
    { id: 'overview', label: 'Overview', icon: Database },
    { id: 'fields', label: 'Field Statistics', icon: Hash },
    { id: 'datatypes', label: 'Data Types', icon: Type },
    { id: 'thresholds', label: 'Aggregation Thresholds', icon: TrendingUp },
    { id: 'availability', label: 'Availability', icon: Globe }
  ];

  const filteredData = showOnlyDifferences
    ? comparisonData.filter(row => row.isDifferent)
    : comparisonData;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-[90%] max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <GitCompare className="h-5 w-5 text-gray-700" />
              <h2 className="text-xl font-semibold">Compare Data Sources</h2>
              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-sm rounded-full">
                {selectedSources.length} schemas
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Options Bar */}
        <div className="px-6 py-3 border-b bg-gray-50 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={showOnlyDifferences}
                onChange={(e) => setShowOnlyDifferences(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              Show only differences
            </label>
            {showOnlyDifferences && (
              <span className="text-sm text-gray-500">
                ({comparisonData.filter(r => r.isDifferent).length} differences found)
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={exportComparison}
              className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </button>
            <button
              className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
            >
              <Share2 className="h-4 w-4" />
              Share
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {selectedSources.length < 2 ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <GitCompare className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>Select at least 2 data sources to compare</p>
              </div>
            </div>
          ) : (
            <div className="p-6">
              {/* Schema Headers */}
              <div className="grid grid-cols-[200px_repeat(auto-fit,minmax(200px,1fr))] gap-4 mb-6 pb-4 border-b">
                <div className="font-medium text-gray-500">Schema</div>
                {selectedSources.map((source) => (
                  <div key={source.id} className="space-y-1">
                    <div className="font-semibold text-gray-900 flex items-center gap-2">
                      {source.name}
                      {source.is_paid_feature && <Lock className="h-4 w-4 text-yellow-600" />}
                    </div>
                    <div className="text-sm text-gray-500">{source.category}</div>
                    <div className="text-xs text-gray-400">v{source.version}</div>
                  </div>
                ))}
              </div>

              {/* Comparison Sections */}
              {categories.map(category => {
                const Icon = category.icon;
                const categoryData = filteredData.filter(row => row.category === category.id);
                
                if (categoryData.length === 0) return null;

                return (
                  <div key={category.id} className="mb-6">
                    <button
                      onClick={() => toggleSection(category.id)}
                      className="w-full flex items-center gap-2 mb-3 text-left hover:text-gray-700"
                    >
                      {expandedSections.has(category.id) ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                      <Icon className="h-4 w-4" />
                      <h3 className="font-semibold text-gray-900">{category.label}</h3>
                      {showOnlyDifferences && (
                        <span className="text-xs text-gray-500">
                          ({categoryData.filter(r => r.isDifferent).length} differences)
                        </span>
                      )}
                    </button>

                    {expandedSections.has(category.id) && (
                      <div className="space-y-2">
                        {categoryData.map((row, rowIndex) => (
                          <div
                            key={`${category.id}-${rowIndex}`}
                            className={`grid grid-cols-[200px_repeat(auto-fit,minmax(200px,1fr))] gap-4 py-2 px-3 rounded-lg ${
                              row.isDifferent ? 'bg-yellow-50' : 'bg-gray-50'
                            }`}
                          >
                            <div className="text-sm font-medium text-gray-700 flex items-center gap-2">
                              {row.property}
                              {row.isDifferent && (
                                <AlertCircle className="h-3 w-3 text-yellow-600" />
                              )}
                            </div>
                            {row.values.map((value, valueIndex) => (
                              <div
                                key={valueIndex}
                                className={`text-sm font-medium ${getValueColor(row.isDifferent, valueIndex)}`}
                              >
                                {getValueDisplay(value)}
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Field-by-field comparison would go here if needed */}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {comparisonData.filter(r => r.isDifferent).length} total differences found
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Close Comparison
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}