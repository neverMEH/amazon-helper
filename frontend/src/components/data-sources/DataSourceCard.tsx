import { memo, useState } from 'react';
import type { MouseEvent } from 'react';
import {
  Database,
  Lock,
  Hash,
  TrendingUp,
  ChevronDown,
  ChevronRight,
  Clock,
  Users,
  Link2
} from 'lucide-react';
import type { DataSource } from '../../types/dataSource';
import { highlightMatch } from './utils';

interface DataSourceCardProps {
  dataSource: DataSource;
  onClick: (event: React.MouseEvent) => void;
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
        onClick(e);
      }}
      title="Click to open details • ⌘/Ctrl+Click to select"
    >
      {/* Data Source Name & Description */}
      <td className="px-4 py-3 w-[25%]">
        <div className="flex items-start gap-2">
          {selectionMode && (
            <input
              type="checkbox"
              checked={isChecked}
              onChange={() => onSelect?.(dataSource.id, !isChecked)}
              onClick={handleCheckboxClick}
              className="h-4 w-4 mt-0.5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 flex-shrink-0"
            />
          )}
          <div className="flex-1 overflow-hidden">
            <div className="flex items-start gap-1.5">
              <Database className="h-4 w-4 text-gray-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div 
                  className="font-medium text-gray-900 break-words"
                  title={dataSource.name}
                >
                  {searchQuery ? highlightMatch(dataSource.name, searchQuery) : dataSource.name}
                </div>
                {dataSource.is_paid_feature && (
                  <span title="Premium Feature" className="inline-block mt-1">
                    <Lock className="h-3 w-3 text-yellow-600" />
                  </span>
                )}
              </div>
            </div>
            {dataSource.description && (
              <p className="text-xs text-gray-500 mt-1 line-clamp-2" title={dataSource.description}>
                {dataSource.description}
              </p>
            )}
          </div>
        </div>
      </td>

      {/* Tables */}
      <td className="px-4 py-3 w-[20%]">
        {dataSource.data_sources && dataSource.data_sources.length > 0 ? (
          <div className="text-sm">
            {dataSource.data_sources.length <= 2 ? (
              <div className="space-y-0.5">
                {dataSource.data_sources.map((table, idx) => (
                  <div key={idx} className="text-gray-600 text-xs font-mono break-all">
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
                  <div className="mt-1 space-y-0.5 max-h-32 overflow-y-auto">
                    {dataSource.data_sources.map((table, idx) => (
                      <div key={idx} className="text-gray-600 text-xs font-mono pl-4 break-all">
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
      <td className="px-4 py-3 w-[8%]">
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
      <td className="px-4 py-3 w-[12%]">
        {dataSource.audience_capabilities && dataSource.audience_capabilities.length > 0 ? (
          <div className="space-y-1">
            {dataSource.audience_capabilities.slice(0, 2).map((capability, idx) => (
              <div 
                key={idx} 
                className="text-xs text-purple-700"
                title={capability}
              >
                <Users className="h-3 w-3 inline mr-1" />
                <span>{capability.length > 20 ? capability.substring(0, 20) + '...' : capability}</span>
              </div>
            ))}
            {dataSource.audience_capabilities.length > 2 && (
              <span className="text-xs text-gray-500">
                +{dataSource.audience_capabilities.length - 2} more
              </span>
            )}
          </div>
        ) : (
          <span className="text-xs text-gray-400">—</span>
        )}
      </td>

      {/* Joins With */}
      <td className="px-4 py-3 w-[10%]">
        {dataSource.joinable_sources && dataSource.joinable_sources.length > 0 ? (
          <div className="space-y-0.5">
            {dataSource.joinable_sources.slice(0, 2).map((source, idx) => (
              <div 
                key={idx} 
                className="text-xs text-blue-700"
                title={`Joins with ${source.name}`}
              >
                <Link2 className="h-3 w-3 inline mr-1" />
                <span>{source.name.length > 15 ? source.name.substring(0, 15) + '...' : source.name}</span>
              </div>
            ))}
            {dataSource.joinable_sources.length > 2 && (
              <span className="text-xs text-gray-500">
                +{dataSource.joinable_sources.length - 2}
              </span>
            )}
          </div>
        ) : (
          <span className="text-xs text-gray-400">No joins</span>
        )}
      </td>

      {/* Data Freshness */}
      <td className="px-4 py-3 w-[10%]">
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
      <td className="px-4 py-3 w-[15%]">
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
    </tr>
  );
});

DataSourceCard.displayName = 'DataSourceCard';