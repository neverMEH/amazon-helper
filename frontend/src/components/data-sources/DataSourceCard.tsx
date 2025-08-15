import { memo, useState } from 'react';
import type { MouseEvent } from 'react';
import {
  Database,
  Lock,
  Hash,
  TrendingUp,
  Eye,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Clock,
  Users,
  Link2,
  Code
} from 'lucide-react';
import type { DataSource } from '../../types/dataSource';
import { highlightMatch } from './utils';

interface DataSourceCardProps {
  dataSource: DataSource;
  onClick: () => void;
  onDoubleClick?: () => void;
  onPreview?: () => void;
  onViewDetails?: () => void;
  isSelected?: boolean;  // Visual selection highlight
  isChecked?: boolean;    // Checkbox selection for bulk actions
  searchQuery?: string;
  onSelect?: (id: string, selected: boolean) => void;
  selectionMode?: boolean;
}

export const DataSourceCard = memo(({ 
  dataSource, 
  onClick,
  onDoubleClick,
  onPreview,
  onViewDetails,
  isSelected = false,
  isChecked = false,
  searchQuery = '',
  onSelect,
  selectionMode = false
}: DataSourceCardProps) => {
  const [showAllTables, setShowAllTables] = useState(false);
  
  const handleCheckboxClick = (e: MouseEvent) => {
    e.stopPropagation();
    onSelect?.(dataSource.id, !isChecked);
  };

  const handlePreviewClick = (e: MouseEvent) => {
    e.stopPropagation();
    onPreview?.();
  };

  const handleDetailsClick = (e: MouseEvent) => {
    e.stopPropagation();
    console.log('DataSourceCard - Viewing details for:', dataSource.name, 'with schema_id:', dataSource.schema_id);
    onViewDetails?.();
  };

  const handleExamplesClick = (e: MouseEvent) => {
    e.stopPropagation();
    // Navigate to examples or show examples modal
    onViewDetails?.();
  };

  const toggleTables = (e: MouseEvent) => {
    e.stopPropagation();
    setShowAllTables(!showAllTables);
  };

  // Get data freshness color
  const getFreshnessColor = (days?: number) => {
    if (days === undefined) return 'text-gray-500';
    if (days === 0) return 'text-green-600';
    if (days <= 7) return 'text-blue-600';
    if (days <= 14) return 'text-yellow-600';
    return 'text-orange-600';
  };

  // Table row with master-detail selection pattern
  return (
    <tr 
      className={`
        hover:bg-gray-50 cursor-pointer transition-colors
        ${isSelected ? 'bg-blue-50 hover:bg-blue-100' : ''}
      `}
      onClick={(e) => {
        if (selectionMode && e.target instanceof HTMLInputElement && e.target.type === 'checkbox') {
          return;
        }
        onClick();
      }}
      onDoubleClick={onDoubleClick}
      title="Click to select • Double-click to open details"
    >
      {/* Data Source Name & Description */}
      <td className="px-4 py-3">
        <div className="flex items-start gap-2">
          {selectionMode && (
            <input
              type="checkbox"
              checked={isChecked}
              onChange={() => onSelect?.(dataSource.id, !isChecked)}
              onClick={handleCheckboxClick}
              className="h-4 w-4 mt-0.5 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <Database className="h-4 w-4 text-gray-400 flex-shrink-0" />
              <span 
                className="font-medium text-gray-900 truncate"
                title={dataSource.name}
              >
                {searchQuery ? highlightMatch(dataSource.name, searchQuery) : dataSource.name}
              </span>
              {dataSource.is_paid_feature && (
                <span title="Premium Feature">
                  <Lock className="h-3 w-3 text-yellow-600 flex-shrink-0" />
                </span>
              )}
            </div>
            {dataSource.description && (
              <p className="text-xs text-gray-500 truncate mt-0.5" title={dataSource.description}>
                {dataSource.description}
              </p>
            )}
          </div>
        </div>
      </td>

      {/* Tables */}
      <td className="px-4 py-3">
        {dataSource.data_sources && dataSource.data_sources.length > 0 ? (
          <div className="text-sm">
            {dataSource.data_sources.length <= 2 ? (
              <div className="space-y-0.5">
                {dataSource.data_sources.map((table, idx) => (
                  <div key={idx} className="text-gray-600 text-xs font-mono">
                    {table}
                  </div>
                ))}
              </div>
            ) : (
              <div>
                <button 
                  onClick={toggleTables}
                  className="flex items-center gap-1 text-gray-600 hover:text-gray-900 transition-colors"
                >
                  {showAllTables ? (
                    <ChevronDown className="h-3 w-3" />
                  ) : (
                    <ChevronRight className="h-3 w-3" />
                  )}
                  <span className="text-xs font-medium">
                    {dataSource.data_sources.length} tables
                  </span>
                </button>
                {showAllTables && (
                  <div className="mt-1 space-y-0.5">
                    {dataSource.data_sources.map((table, idx) => (
                      <div key={idx} className="text-gray-600 text-xs font-mono pl-4">
                        {table}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <span className="text-xs text-gray-400">—</span>
        )}
      </td>

      {/* Fields (Dimensions & Metrics) */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2 text-sm">
          {dataSource.dimension_count !== undefined || dataSource.metric_count !== undefined ? (
            <>
              <span className="flex items-center gap-1 text-gray-600" title="Dimensions">
                <Hash className="h-3 w-3 text-blue-500" />
                <span className="text-xs">{dataSource.dimension_count || 0}D</span>
              </span>
              <span className="text-gray-300">•</span>
              <span className="flex items-center gap-1 text-gray-600" title="Metrics">
                <TrendingUp className="h-3 w-3 text-green-500" />
                <span className="text-xs">{dataSource.metric_count || 0}M</span>
              </span>
            </>
          ) : (
            <span className="text-xs text-gray-400">—</span>
          )}
        </div>
      </td>

      {/* Audience Types */}
      <td className="px-4 py-3">
        {dataSource.audience_capabilities && dataSource.audience_capabilities.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {dataSource.audience_capabilities.slice(0, 3).map((capability, idx) => (
              <span 
                key={idx} 
                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-purple-100 text-purple-700"
                title={capability}
              >
                <Users className="h-3 w-3" />
                <span className="truncate max-w-[100px]">{capability}</span>
              </span>
            ))}
            {dataSource.audience_capabilities.length > 3 && (
              <span className="text-xs text-gray-500">
                +{dataSource.audience_capabilities.length - 3}
              </span>
            )}
          </div>
        ) : (
          <span className="text-xs text-gray-400">—</span>
        )}
      </td>

      {/* Joins With */}
      <td className="px-4 py-3">
        {dataSource.joinable_sources && dataSource.joinable_sources.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {dataSource.joinable_sources.slice(0, 3).map((source, idx) => (
              <span 
                key={idx} 
                className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors cursor-pointer"
                title={`Joins with ${source.name}`}
              >
                <Link2 className="h-3 w-3" />
                <span className="truncate max-w-[80px]">{source.name}</span>
              </span>
            ))}
            {dataSource.joinable_sources.length > 3 && (
              <span className="text-xs text-gray-500">
                +{dataSource.joinable_sources.length - 3}
              </span>
            )}
          </div>
        ) : (
          <span className="text-xs text-gray-400">No joins</span>
        )}
      </td>

      {/* Data Freshness */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <Clock className={`h-3 w-3 ${getFreshnessColor(dataSource.data_lag_days)}`} />
          <div>
            {dataSource.data_lag_days !== undefined ? (
              <>
                <span className={`text-xs font-medium ${getFreshnessColor(dataSource.data_lag_days)}`}>
                  {dataSource.data_lag_days === 0 ? 'Real-time' : `${dataSource.data_lag_days}d lag`}
                </span>
                {dataSource.update_frequency && (
                  <span className="text-xs text-gray-500 ml-1">
                    ({dataSource.update_frequency})
                  </span>
                )}
              </>
            ) : (
              <span className="text-xs text-gray-400">—</span>
            )}
          </div>
        </div>
      </td>

      {/* Use Cases (Tags) */}
      <td className="px-4 py-3">
        <div className="flex flex-wrap gap-1">
          {dataSource.tags.slice(0, 2).map(tag => (
            <span 
              key={tag} 
              className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-600"
            >
              {tag}
            </span>
          ))}
          {dataSource.tags.length > 2 && (
            <span className="text-xs text-gray-400">+{dataSource.tags.length - 2}</span>
          )}
        </div>
      </td>

      {/* Actions */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <button
            onClick={handlePreviewClick}
            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
            title="Preview"
          >
            <Eye className="h-4 w-4" />
          </button>
          <button
            onClick={handleExamplesClick}
            className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
            title="View Examples"
          >
            <Code className="h-4 w-4" />
          </button>
          <button
            onClick={handleDetailsClick}
            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
            title="View Full Details"
          >
            <ExternalLink className="h-4 w-4" />
          </button>
        </div>
      </td>
    </tr>
  );
});

DataSourceCard.displayName = 'DataSourceCard';