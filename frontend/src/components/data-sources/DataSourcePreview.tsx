import { useEffect, useState } from 'react';
import { X, Database, Tag, Lock, Globe, Table, Code, ExternalLink, TrendingUp, Hash } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { dataSourceService } from '../../services/dataSourceService';
import type { DataSource, SchemaField } from '../../types/dataSource';

interface DataSourcePreviewProps {
  dataSource: DataSource | null;
  onClose?: () => void;
  onOpenDetail: (dataSource: DataSource) => void;
}

export function DataSourcePreview({ dataSource, onClose, onOpenDetail }: DataSourcePreviewProps) {
  const [topFields, setTopFields] = useState<SchemaField[]>([]);

  // Fetch fields when a data source is selected
  const { data: fields } = useQuery({
    queryKey: ['dataSourceFields', dataSource?.schema_id],
    queryFn: () => dataSourceService.getSchemaFields(dataSource!.schema_id),
    enabled: !!dataSource,
    staleTime: 10 * 60 * 1000
  });

  // Fetch examples
  const { data: examples } = useQuery({
    queryKey: ['dataSourceExamples', dataSource?.schema_id],
    queryFn: () => dataSourceService.getQueryExamples(dataSource!.schema_id),
    enabled: !!dataSource,
    staleTime: 10 * 60 * 1000
  });

  useEffect(() => {
    if (fields) {
      setTopFields(fields.slice(0, 10));
    }
  }, [fields]);

  if (!dataSource) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <div className="text-center">
          <Database className="h-12 w-12 mx-auto mb-3" />
          <p className="text-sm">Select a data source to preview</p>
        </div>
      </div>
    );
  }

  const dimensionCount = fields?.filter(f => f.dimension_or_metric === 'Dimension').length || 0;
  const metricCount = fields?.filter(f => f.dimension_or_metric === 'Metric').length || 0;

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="px-4 py-3 border-b bg-gray-50">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900">{dataSource.name}</h3>
              {dataSource.is_paid_feature && (
                <Lock className="h-4 w-4 text-yellow-600" />
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5">{dataSource.category}</p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
            >
              <X className="h-4 w-4 text-gray-500" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-4">
          {/* Description */}
          <div>
            <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">Description</h4>
            <p className="text-sm text-gray-600">{dataSource.description}</p>
          </div>

          {/* Statistics */}
          <div>
            <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">Statistics</h4>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-gray-50 rounded p-2">
                <div className="flex items-center gap-1.5">
                  <Table className="h-3.5 w-3.5 text-gray-400" />
                  <span className="text-xs text-gray-500">Total Fields</span>
                </div>
                <p className="text-lg font-semibold text-gray-900 mt-1">{fields?.length || 0}</p>
              </div>
              <div className="bg-gray-50 rounded p-2">
                <div className="flex items-center gap-1.5">
                  <Code className="h-3.5 w-3.5 text-gray-400" />
                  <span className="text-xs text-gray-500">Examples</span>
                </div>
                <p className="text-lg font-semibold text-gray-900 mt-1">{examples?.length || 0}</p>
              </div>
              <div className="bg-blue-50 rounded p-2">
                <div className="flex items-center gap-1.5">
                  <Hash className="h-3.5 w-3.5 text-blue-400" />
                  <span className="text-xs text-blue-600">Dimensions</span>
                </div>
                <p className="text-lg font-semibold text-blue-900 mt-1">{dimensionCount}</p>
              </div>
              <div className="bg-green-50 rounded p-2">
                <div className="flex items-center gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5 text-green-400" />
                  <span className="text-xs text-green-600">Metrics</span>
                </div>
                <p className="text-lg font-semibold text-green-900 mt-1">{metricCount}</p>
              </div>
            </div>
          </div>

          {/* AMC Tables */}
          <div>
            <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">AMC Tables</h4>
            <div className="flex flex-wrap gap-1">
              {dataSource.data_sources.map(source => (
                <code key={source} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-mono">
                  {source}
                </code>
              ))}
            </div>
          </div>

          {/* Top Fields */}
          {topFields.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Top Fields ({topFields.length} of {fields?.length || 0})
              </h4>
              <div className="space-y-1">
                {topFields.map(field => (
                  <div key={field.id} className="flex items-center justify-between py-1.5 px-2 hover:bg-gray-50 rounded">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <span className={`px-1.5 py-0.5 text-xs rounded font-medium ${
                        field.dimension_or_metric === 'Dimension' 
                          ? 'bg-blue-100 text-blue-700' 
                          : 'bg-green-100 text-green-700'
                      }`}>
                        {field.dimension_or_metric === 'Dimension' ? 'D' : 'M'}
                      </span>
                      <code className="text-xs font-mono text-gray-800 truncate">
                        {field.field_name}
                      </code>
                    </div>
                    <span className="text-xs text-gray-500 ml-2">
                      {field.data_type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          <div>
            <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">Tags</h4>
            <div className="flex flex-wrap gap-1">
              {dataSource.tags.map(tag => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs"
                >
                  <Tag className="h-3 w-3" />
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Availability */}
          {dataSource.availability?.marketplaces && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                <Globe className="h-3.5 w-3.5 inline mr-1" />
                Available in {Object.keys(dataSource.availability.marketplaces).length} Regions
              </h4>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t bg-gray-50">
        <button
          onClick={() => onOpenDetail(dataSource)}
          className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
        >
          View Full Details
          <ExternalLink className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}