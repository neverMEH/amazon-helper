import { useState } from 'react';
import {
  Bookmark,
  Star,
  Check,
  Filter,
  Trash2,
  Edit2,
  Plus
} from 'lucide-react';

export interface FilterPreset {
  id: string;
  name: string;
  description?: string;
  filter: any; // This would be the FilterGroup type from AdvancedFilterBuilder
  isDefault?: boolean;
  icon?: string;
  color?: string;
}

interface FilterPresetsProps {
  presets: FilterPreset[];
  activePresetId?: string;
  onSelectPreset: (preset: FilterPreset) => void;
  onSavePreset?: (preset: FilterPreset) => void;
  onDeletePreset?: (id: string) => void;
  onEditPreset?: (preset: FilterPreset) => void;
  onCreateNew?: () => void;
}

// Default presets that can be used
export const DEFAULT_PRESETS: FilterPreset[] = [
  {
    id: 'all',
    name: 'All Data Sources',
    description: 'Show all data sources without any filters',
    filter: {
      id: 'all',
      logic: 'AND',
      conditions: [],
      groups: []
    },
    icon: 'Database',
    color: 'gray'
  },
  {
    id: 'paid-only',
    name: 'Paid Features',
    description: 'Show only data sources that require paid subscription',
    filter: {
      id: 'paid-only',
      logic: 'AND',
      conditions: [
        {
          id: '1',
          field: 'isPaid',
          operator: 'equals',
          value: true
        }
      ],
      groups: []
    },
    icon: 'Lock',
    color: 'yellow'
  },
  {
    id: 'free-only',
    name: 'Free Features',
    description: 'Show only free data sources',
    filter: {
      id: 'free-only',
      logic: 'AND',
      conditions: [
        {
          id: '1',
          field: 'isPaid',
          operator: 'equals',
          value: false
        }
      ],
      groups: []
    },
    icon: 'Unlock',
    color: 'green'
  },
  {
    id: 'complex-schemas',
    name: 'Complex Schemas',
    description: 'Show schemas with high field count (50+ fields)',
    filter: {
      id: 'complex-schemas',
      logic: 'AND',
      conditions: [
        {
          id: '1',
          field: 'fieldCount',
          operator: 'greaterThan',
          value: 50
        }
      ],
      groups: []
    },
    icon: 'Layers',
    color: 'red'
  },
  {
    id: 'simple-schemas',
    name: 'Simple Schemas',
    description: 'Show schemas with low field count (< 20 fields)',
    filter: {
      id: 'simple-schemas',
      logic: 'AND',
      conditions: [
        {
          id: '1',
          field: 'fieldCount',
          operator: 'lessThan',
          value: 20
        }
      ],
      groups: []
    },
    icon: 'Layers',
    color: 'green'
  },
  {
    id: 'attribution',
    name: 'Attribution Tables',
    description: 'Show only attribution-related data sources',
    filter: {
      id: 'attribution',
      logic: 'AND',
      conditions: [
        {
          id: '1',
          field: 'category',
          operator: 'contains',
          value: 'Attribution'
        }
      ],
      groups: []
    },
    icon: 'TrendingUp',
    color: 'blue'
  },
  {
    id: 'conversion',
    name: 'Conversion Tables',
    description: 'Show only conversion-related data sources',
    filter: {
      id: 'conversion',
      logic: 'AND',
      conditions: [
        {
          id: '1',
          field: 'category',
          operator: 'contains',
          value: 'Conversion'
        }
      ],
      groups: []
    },
    icon: 'Target',
    color: 'purple'
  }
];

export function FilterPresets({
  presets,
  activePresetId,
  onSelectPreset,
  onSavePreset,
  onDeletePreset,
  onEditPreset,
  onCreateNew
}: FilterPresetsProps) {
  const [showDropdown, setShowDropdown] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const activePreset = presets.find(p => p.id === activePresetId);

  const getPresetIcon = (preset: FilterPreset) => {
    if (preset.isDefault) return <Star className="h-3 w-3" />;
    if (preset.icon === 'Lock') return <Filter className="h-3 w-3" />;
    return <Bookmark className="h-3 w-3" />;
  };

  const getPresetColor = (preset: FilterPreset) => {
    const colors: Record<string, string> = {
      gray: 'bg-gray-100 text-gray-700 border-gray-300',
      yellow: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      green: 'bg-green-100 text-green-700 border-green-300',
      red: 'bg-red-100 text-red-700 border-red-300',
      blue: 'bg-blue-100 text-blue-700 border-blue-300',
      purple: 'bg-purple-100 text-purple-700 border-purple-300'
    };
    return colors[preset.color || 'gray'];
  };

  return (
    <div className="relative">
      {/* Preset Pills */}
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-sm font-medium text-gray-700">Quick Filters:</span>
        
        {/* Show first 5 presets as pills */}
        {presets.slice(0, 5).map(preset => (
          <button
            key={preset.id}
            onClick={() => onSelectPreset(preset)}
            className={`
              inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium
              border transition-all duration-200
              ${activePresetId === preset.id
                ? getPresetColor(preset) + ' ring-2 ring-offset-1'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }
            `}
            title={preset.description}
          >
            {getPresetIcon(preset)}
            {preset.name}
            {activePresetId === preset.id && (
              <Check className="h-3 w-3 ml-1" />
            )}
          </button>
        ))}

        {/* More button if there are more than 5 presets */}
        {presets.length > 5 && (
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium
                bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
            >
              More
              <span className="text-xs bg-gray-200 px-1.5 py-0.5 rounded-full">
                {presets.length - 5}
              </span>
            </button>

            {showDropdown && (
              <div className="absolute top-full mt-2 left-0 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                <div className="p-2">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wider px-2 py-1">
                    Additional Presets
                  </div>
                  {presets.slice(5).map(preset => (
                    <button
                      key={preset.id}
                      onClick={() => {
                        onSelectPreset(preset);
                        setShowDropdown(false);
                      }}
                      className={`
                        w-full flex items-center justify-between gap-2 px-3 py-2 rounded-md text-sm
                        transition-colors
                        ${activePresetId === preset.id
                          ? 'bg-blue-50 text-blue-700'
                          : 'hover:bg-gray-50 text-gray-700'
                        }
                      `}
                    >
                      <div className="flex items-center gap-2">
                        {getPresetIcon(preset)}
                        <div className="text-left">
                          <div className="font-medium">{preset.name}</div>
                          {preset.description && (
                            <div className="text-xs text-gray-500">{preset.description}</div>
                          )}
                        </div>
                      </div>
                      {activePresetId === preset.id && (
                        <Check className="h-4 w-4 text-blue-600" />
                      )}
                    </button>
                  ))}
                </div>

                {/* Actions */}
                {(onCreateNew || onEditPreset || onDeletePreset) && (
                  <div className="border-t p-2">
                    {onCreateNew && (
                      <button
                        onClick={() => {
                          onCreateNew();
                          setShowDropdown(false);
                        }}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm
                          text-blue-600 hover:bg-blue-50 transition-colors"
                      >
                        <Plus className="h-4 w-4" />
                        Create New Preset
                      </button>
                    )}
                    {activePreset && !activePreset.isDefault && onEditPreset && (
                      <button
                        onClick={() => {
                          onEditPreset(activePreset);
                          setShowDropdown(false);
                        }}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm
                          text-gray-600 hover:bg-gray-50 transition-colors"
                      >
                        <Edit2 className="h-4 w-4" />
                        Edit Current Preset
                      </button>
                    )}
                    {activePreset && !activePreset.isDefault && onDeletePreset && (
                      <button
                        onClick={() => {
                          if (confirm(`Delete preset "${activePreset.name}"?`)) {
                            onDeletePreset(activePreset.id);
                          }
                          setShowDropdown(false);
                        }}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm
                          text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                        Delete Current Preset
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Create new preset button */}
        {onCreateNew && (
          <button
            onClick={onCreateNew}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium
              bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-3 w-3" />
            New
          </button>
        )}
      </div>

      {/* Active Filter Description */}
      {activePreset && activePreset.description && (
        <div className="mt-2 text-sm text-gray-500 italic">
          {activePreset.description}
        </div>
      )}
    </div>
  );
}