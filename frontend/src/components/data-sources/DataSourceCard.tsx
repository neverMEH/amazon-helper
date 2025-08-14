import { memo } from 'react';
import type { MouseEvent } from 'react';
import {
  Database,
  Lock,
  Table,
  Code,
  BarChart3,
  Layers,
  TrendingUp
} from 'lucide-react';
import type { DataSource } from '../../types/dataSource';
import { highlightMatch } from './utils';

interface DataSourceCardProps {
  dataSource: DataSource;
  onClick: () => void;
  onPreview?: (dataSource: DataSource) => void;
  isSelected?: boolean;
  searchQuery?: string;
  onSelect?: (id: string, selected: boolean) => void;
  selectionMode?: boolean;
}

function getComplexityLevel(fieldCount: number): { label: string; color: string; icon: typeof Layers } {
  if (fieldCount < 20) return { label: 'Simple', color: 'text-green-600 bg-green-50', icon: Layers };
  if (fieldCount < 50) return { label: 'Medium', color: 'text-yellow-600 bg-yellow-50', icon: BarChart3 };
  return { label: 'Complex', color: 'text-red-600 bg-red-50', icon: TrendingUp };
}

export const DataSourceCard = memo(({ 
  dataSource, 
  onClick, 
  onPreview,
  isSelected = false,
  searchQuery = '',
  onSelect,
  selectionMode = false
}: DataSourceCardProps) => {
  
  // Mock field count - in real implementation, this would come from the API
  const fieldCount = Math.floor(Math.random() * 100) + 10;
  const exampleCount = Math.floor(Math.random() * 15) + 1;
  const complexity = getComplexityLevel(fieldCount);
  const ComplexityIcon = complexity.icon;

  const handleCheckboxClick = (e: MouseEvent) => {
    e.stopPropagation();
    onSelect?.(dataSource.id, !isSelected);
  };

  // Since we're only using list/compact view, return the table row directly
  return (
    <tr 
      className={`hover:bg-gray-50 cursor-pointer transition-colors ${isSelected ? 'bg-blue-50' : ''}`}
      onClick={(e) => {
        if (selectionMode && e.target instanceof HTMLInputElement && e.target.type === 'checkbox') {
          return;
        }
        onClick();
      }}
      onMouseEnter={() => {
        onPreview?.(dataSource);
      }}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {selectionMode && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onSelect?.(dataSource.id, !isSelected)}
              onClick={handleCheckboxClick}
              className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
          )}
          <Database className="h-4 w-4 text-gray-400" />
          <span className="font-medium text-gray-900">
            {searchQuery ? highlightMatch(dataSource.name, searchQuery) : dataSource.name}
          </span>
          {dataSource.is_paid_feature && (
            <Lock className="h-3 w-3 text-yellow-600" />
          )}
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
          {dataSource.category}
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-3 text-sm">
          <span className="flex items-center gap-1 text-gray-500">
            <Table className="h-3 w-3" />
            {fieldCount}
          </span>
          <span className="flex items-center gap-1 text-gray-500">
            <Code className="h-3 w-3" />
            {exampleCount}
          </span>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${complexity.color}`}>
          <ComplexityIcon className="h-3 w-3" />
          {complexity.label}
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex gap-1">
          {dataSource.tags.slice(0, 2).map(tag => (
            <span key={tag} className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
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