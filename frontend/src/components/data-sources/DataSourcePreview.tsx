import { useEffect, useState } from 'react';
import { X, Database, Tag, Lock, Globe, Table, Code, ExternalLink, TrendingUp, Hash, Loader2, AlertCircle, Link2, Users, Clock, GitBranch, Filter } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { dataSourceService } from '../../services/dataSourceService';
import type { DataSource, SchemaField } from '../../types/dataSource';
import { ErrorBoundary } from '../common/ErrorBoundary';

interface DataSourcePreviewProps {
  dataSource: DataSource | null;
  onClose?: () => void;
  onOpenDetail: (dataSource: DataSource) => void;
}

function DataSourcePreviewContent({ dataSource, onClose, onOpenDetail }: DataSourcePreviewProps) {
  const [topFields, setTopFields] = useState<SchemaField[]>([]);

  // Fetch fields when a data source is selected
  const { data: fields, isLoading: fieldsLoading, error: fieldsError } = useQuery({
    queryKey: ['dataSourceFields', dataSource?.schema_id],
    queryFn: () => dataSourceService.getSchemaFields(dataSource!.schema_id),
    enabled: !!dataSource,
    staleTime: 10 * 60 * 1000,
    retry: 1
  });

  // Fetch examples
  const { data: examples, isLoading: examplesLoading, error: examplesError } = useQuery({
    queryKey: ['dataSourceExamples', dataSource?.schema_id],
    queryFn: () => dataSourceService.getQueryExamples(dataSource!.schema_id),
    enabled: !!dataSource,
    staleTime: 10 * 60 * 1000,
    retry: 1
  });

  // Fetch relationships
  const { data: relationships } = useQuery({
    queryKey: ['dataSourceRelationships', dataSource?.schema_id],
    queryFn: () => dataSourceService.getSchemaRelationships(dataSource!.schema_id),
    enabled: !!dataSource,
    staleTime: 10 * 60 * 1000,
    retry: 1
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

  const dimensionCount = fields?.filter(f => f.dimension_or_metric === 'Dimension').length ?? null;
  const metricCount = fields?.filter(f => f.dimension_or_metric === 'Metric').length ?? null;
  const hasError = fieldsError || examplesError;

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
                <p className="text-lg font-semibold text-gray-900 mt-1">
                  {fieldsLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : fields?.length ?? (
                    <span className="text-gray-400">—</span>
                  )}
                </p>
              </div>
              <div className="bg-gray-50 rounded p-2">
                <div className="flex items-center gap-1.5">
                  <Code className="h-3.5 w-3.5 text-gray-400" />
                  <span className="text-xs text-gray-500">Examples</span>
                </div>
                <p className="text-lg font-semibold text-gray-900 mt-1">
                  {examplesLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : examples?.length ?? (
                    <span className="text-gray-400">—</span>
                  )}
                </p>
              </div>
              <div className="bg-blue-50 rounded p-2">
                <div className="flex items-center gap-1.5">
                  <Hash className="h-3.5 w-3.5 text-blue-400" />
                  <span className="text-xs text-blue-600">Dimensions</span>
                </div>
                <p className="text-lg font-semibold text-blue-900 mt-1">
                  {dimensionCount ?? <span className="text-gray-400">—</span>}
                </p>
              </div>
              <div className="bg-green-50 rounded p-2">
                <div className="flex items-center gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5 text-green-400" />
                  <span className="text-xs text-green-600">Metrics</span>
                </div>
                <p className="text-lg font-semibold text-green-900 mt-1">
                  {metricCount ?? <span className="text-gray-400">—</span>}
                </p>
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

          {/* Audience Capabilities */}
          {dataSource.audience_capabilities && dataSource.audience_capabilities.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Users className="h-3 w-3" />
                Audience Capabilities
              </h4>
              <div className="flex flex-wrap gap-1">
                {dataSource.audience_capabilities.map((capability, idx) => (
                  <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                    {capability}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Joinable Data Sources */}
          {dataSource.joinable_sources && dataSource.joinable_sources.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Link2 className="h-3 w-3" />
                Can Join With
              </h4>
              <div className="space-y-1">
                {dataSource.joinable_sources.slice(0, 5).map((source, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <GitBranch className="h-3 w-3 text-blue-500" />
                    <span className="text-gray-700">{source.name}</span>
                  </div>
                ))}
                {dataSource.joinable_sources.length > 5 && (
                  <span className="text-xs text-gray-500">+{dataSource.joinable_sources.length - 5} more</span>
                )}
              </div>
            </div>
          )}

          {/* Data Freshness */}
          <div>
            <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Data Freshness
            </h4>
            <div className="bg-gray-50 rounded p-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Data Lag</span>
                <span className={`text-sm font-medium ${
                  dataSource.data_lag_days === 0 ? 'text-green-600' :
                  dataSource.data_lag_days && dataSource.data_lag_days <= 7 ? 'text-blue-600' :
                  dataSource.data_lag_days && dataSource.data_lag_days <= 14 ? 'text-yellow-600' :
                  'text-orange-600'
                }`}>
                  {dataSource.data_lag_days === 0 ? 'Real-time' : 
                   dataSource.data_lag_days ? `${dataSource.data_lag_days} days` : '—'}
                </span>
              </div>
              {dataSource.update_frequency && (
                <div className="flex items-center justify-between mt-1">
                  <span className="text-sm text-gray-600">Update Frequency</span>
                  <span className="text-sm font-medium text-gray-900">{dataSource.update_frequency}</span>
                </div>
              )}
            </div>
          </div>

          {/* Common JOIN Patterns */}
          {relationships && relationships.from && relationships.from.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Filter className="h-3 w-3" />
                Common JOIN Patterns
              </h4>
              <div className="bg-gray-50 rounded p-2 space-y-2">
                {relationships.from.slice(0, 2).map((rel: any, idx: number) => (
                  <div key={idx} className="text-xs font-mono text-gray-700">
                    <div className="text-blue-600">-- Join with {rel.target?.name}</div>
                    <div>LEFT JOIN {rel.target?.schema_id}</div>
                    <div className="pl-2">ON {rel.join_condition || 'matching_field'}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Message */}
          {hasError && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-amber-800 font-medium">Unable to load complete data</p>
                  <p className="text-xs text-amber-600 mt-1">Some information may be unavailable</p>
                </div>
              </div>
            </div>
          )}

          {/* Top Fields */}
          {!fieldsLoading && topFields.length > 0 && (
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

// Export wrapped component with error boundary
export function DataSourcePreview(props: DataSourcePreviewProps) {
  return (
    <ErrorBoundary fallbackMessage="Unable to display data source preview">
      <DataSourcePreviewContent {...props} />
    </ErrorBoundary>
  );
}