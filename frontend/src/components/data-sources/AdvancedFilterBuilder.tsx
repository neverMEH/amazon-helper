import { useState, useEffect } from 'react';
import {
  Filter,
  X,
  Plus,
  Save,
  Trash2,
  ChevronDown,
  ChevronRight,
  Hash,
  Type,
  ToggleLeft,
  TrendingUp,
  Layers
} from 'lucide-react';

interface FilterCondition {
  id: string;
  field: 'name' | 'category' | 'tags' | 'fieldCount' | 'complexity' | 'version' | 'isPaid';
  operator: 'contains' | 'equals' | 'startsWith' | 'endsWith' | 'greaterThan' | 'lessThan' | 'includes' | 'excludes';
  value: string | number | boolean | string[];
}

interface FilterGroup {
  id: string;
  logic: 'AND' | 'OR';
  conditions: FilterCondition[];
  groups: FilterGroup[];
}

interface FilterPreset {
  id: string;
  name: string;
  description?: string;
  filter: FilterGroup;
  isDefault?: boolean;
}

interface AdvancedFilterBuilderProps {
  isOpen: boolean;
  onClose: () => void;
  onApply: (filter: FilterGroup) => void;
  currentFilter?: FilterGroup;
  presets?: FilterPreset[];
  onSavePreset?: (preset: FilterPreset) => void;
}

const FIELD_OPTIONS = [
  { value: 'name', label: 'Name', icon: Type, type: 'string' },
  { value: 'category', label: 'Category', icon: Layers, type: 'string' },
  { value: 'tags', label: 'Tags', icon: Hash, type: 'array' },
  { value: 'fieldCount', label: 'Field Count', icon: TrendingUp, type: 'number' },
  { value: 'complexity', label: 'Complexity', icon: Layers, type: 'string' },
  { value: 'version', label: 'Version', icon: Hash, type: 'string' },
  { value: 'isPaid', label: 'Is Paid Feature', icon: ToggleLeft, type: 'boolean' }
];

const STRING_OPERATORS = [
  { value: 'contains', label: 'Contains' },
  { value: 'equals', label: 'Equals' },
  { value: 'startsWith', label: 'Starts with' },
  { value: 'endsWith', label: 'Ends with' }
];

const NUMBER_OPERATORS = [
  { value: 'equals', label: 'Equals' },
  { value: 'greaterThan', label: 'Greater than' },
  { value: 'lessThan', label: 'Less than' }
];

const ARRAY_OPERATORS = [
  { value: 'includes', label: 'Includes' },
  { value: 'excludes', label: 'Excludes' }
];

const BOOLEAN_OPERATORS = [
  { value: 'equals', label: 'Is' }
];

export function AdvancedFilterBuilder({
  isOpen,
  onClose,
  onApply,
  currentFilter,
  presets = [],
  onSavePreset
}: AdvancedFilterBuilderProps) {
  const [filter, setFilter] = useState<FilterGroup>(
    currentFilter || {
      id: crypto.randomUUID(),
      logic: 'AND',
      conditions: [],
      groups: []
    }
  );
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [showPresetModal, setShowPresetModal] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [presetDescription, setPresetDescription] = useState('');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (currentFilter) {
      setFilter(currentFilter);
    }
  }, [currentFilter]);

  const getOperatorsForField = (field: string) => {
    const fieldOption = FIELD_OPTIONS.find(f => f.value === field);
    if (!fieldOption) return STRING_OPERATORS;

    switch (fieldOption.type) {
      case 'number':
        return NUMBER_OPERATORS;
      case 'array':
        return ARRAY_OPERATORS;
      case 'boolean':
        return BOOLEAN_OPERATORS;
      default:
        return STRING_OPERATORS;
    }
  };

  const addCondition = (groupId?: string) => {
    const newCondition: FilterCondition = {
      id: crypto.randomUUID(),
      field: 'name',
      operator: 'contains',
      value: ''
    };

    if (groupId) {
      // Add to specific group
      const updateGroup = (group: FilterGroup): FilterGroup => {
        if (group.id === groupId) {
          return {
            ...group,
            conditions: [...group.conditions, newCondition]
          };
        }
        return {
          ...group,
          groups: group.groups.map(updateGroup)
        };
      };
      setFilter(updateGroup(filter));
    } else {
      // Add to root
      setFilter({
        ...filter,
        conditions: [...filter.conditions, newCondition]
      });
    }
  };

  const updateCondition = (conditionId: string, updates: Partial<FilterCondition>) => {
    const updateGroup = (group: FilterGroup): FilterGroup => {
      return {
        ...group,
        conditions: group.conditions.map(c =>
          c.id === conditionId ? { ...c, ...updates } : c
        ),
        groups: group.groups.map(updateGroup)
      };
    };
    setFilter(updateGroup(filter));
  };

  const removeCondition = (conditionId: string) => {
    const updateGroup = (group: FilterGroup): FilterGroup => {
      return {
        ...group,
        conditions: group.conditions.filter(c => c.id !== conditionId),
        groups: group.groups.map(updateGroup)
      };
    };
    setFilter(updateGroup(filter));
  };

  const addGroup = (parentGroupId?: string) => {
    const newGroup: FilterGroup = {
      id: crypto.randomUUID(),
      logic: 'AND',
      conditions: [],
      groups: []
    };

    if (parentGroupId) {
      const updateGroup = (group: FilterGroup): FilterGroup => {
        if (group.id === parentGroupId) {
          return {
            ...group,
            groups: [...group.groups, newGroup]
          };
        }
        return {
          ...group,
          groups: group.groups.map(updateGroup)
        };
      };
      setFilter(updateGroup(filter));
    } else {
      setFilter({
        ...filter,
        groups: [...filter.groups, newGroup]
      });
    }

    // Auto-expand the new group
    setExpandedGroups(prev => new Set(prev).add(newGroup.id));
  };

  const removeGroup = (groupId: string) => {
    const updateGroup = (group: FilterGroup): FilterGroup => {
      return {
        ...group,
        groups: group.groups.filter(g => g.id !== groupId).map(updateGroup)
      };
    };
    setFilter(updateGroup(filter));
  };

  const toggleGroupLogic = (groupId: string) => {
    const updateGroup = (group: FilterGroup): FilterGroup => {
      if (group.id === groupId) {
        return {
          ...group,
          logic: group.logic === 'AND' ? 'OR' : 'AND'
        };
      }
      return {
        ...group,
        groups: group.groups.map(updateGroup)
      };
    };
    setFilter(updateGroup(filter));
  };

  const applyPreset = (presetId: string) => {
    const preset = presets.find(p => p.id === presetId);
    if (preset) {
      setFilter(preset.filter);
      setSelectedPreset(presetId);
    }
  };

  const saveAsPreset = () => {
    if (onSavePreset && presetName) {
      const newPreset: FilterPreset = {
        id: crypto.randomUUID(),
        name: presetName,
        description: presetDescription,
        filter: filter
      };
      onSavePreset(newPreset);
      setShowPresetModal(false);
      setPresetName('');
      setPresetDescription('');
    }
  };

  const renderCondition = (condition: FilterCondition, depth: number = 0) => {
    const field = FIELD_OPTIONS.find(f => f.value === condition.field);
    const Icon = field?.icon || Type;
    const operators = getOperatorsForField(condition.field);

    return (
      <div
        key={condition.id}
        className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg"
        style={{ marginLeft: `${depth * 20}px` }}
      >
        <Icon className="h-4 w-4 text-gray-400" />
        
        <select
          value={condition.field}
          onChange={(e) => updateCondition(condition.id, { 
            field: e.target.value as any,
            operator: getOperatorsForField(e.target.value)[0].value as any,
            value: ''
          })}
          className="px-2 py-1 border border-gray-300 rounded text-sm"
        >
          {FIELD_OPTIONS.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <select
          value={condition.operator}
          onChange={(e) => updateCondition(condition.id, { operator: e.target.value as any })}
          className="px-2 py-1 border border-gray-300 rounded text-sm"
        >
          {operators.map(op => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </select>

        {field?.type === 'boolean' ? (
          <select
            value={String(condition.value)}
            onChange={(e) => updateCondition(condition.id, { value: e.target.value === 'true' })}
            className="px-2 py-1 border border-gray-300 rounded text-sm flex-1"
          >
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        ) : field?.type === 'array' ? (
          <input
            type="text"
            value={Array.isArray(condition.value) ? condition.value.join(', ') : String(condition.value || '')}
            onChange={(e) => updateCondition(condition.id, { 
              value: e.target.value.split(',').map(v => v.trim()).filter(Boolean)
            })}
            placeholder="Enter values separated by commas"
            className="px-2 py-1 border border-gray-300 rounded text-sm flex-1"
          />
        ) : (
          <input
            type={field?.type === 'number' ? 'number' : 'text'}
            value={condition.value as string | number}
            onChange={(e) => updateCondition(condition.id, { 
              value: field?.type === 'number' ? Number(e.target.value) : e.target.value
            })}
            placeholder="Enter value"
            className="px-2 py-1 border border-gray-300 rounded text-sm flex-1"
          />
        )}

        <button
          onClick={() => removeCondition(condition.id)}
          className="p-1 text-red-500 hover:bg-red-50 rounded"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  };

  const renderGroup = (group: FilterGroup, depth: number = 0) => {
    const isExpanded = expandedGroups.has(group.id);

    return (
      <div
        key={group.id}
        className="border border-gray-200 rounded-lg p-3 space-y-2"
        style={{ marginLeft: `${depth * 20}px` }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setExpandedGroups(prev => {
                const newSet = new Set(prev);
                if (isExpanded) {
                  newSet.delete(group.id);
                } else {
                  newSet.add(group.id);
                }
                return newSet;
              })}
              className="p-1 hover:bg-gray-100 rounded"
            >
              {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </button>
            
            <button
              onClick={() => toggleGroupLogic(group.id)}
              className={`px-2 py-1 rounded text-xs font-medium ${
                group.logic === 'AND'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-purple-100 text-purple-700'
              }`}
            >
              {group.logic}
            </button>
            
            <span className="text-sm text-gray-500">
              {group.conditions.length} conditions, {group.groups.length} groups
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => addCondition(group.id)}
              className="p-1 text-blue-600 hover:bg-blue-50 rounded"
              title="Add condition"
            >
              <Plus className="h-4 w-4" />
            </button>
            <button
              onClick={() => addGroup(group.id)}
              className="p-1 text-green-600 hover:bg-green-50 rounded"
              title="Add group"
            >
              <Filter className="h-4 w-4" />
            </button>
            {depth > 0 && (
              <button
                onClick={() => removeGroup(group.id)}
                className="p-1 text-red-500 hover:bg-red-50 rounded"
                title="Remove group"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>

        {isExpanded && (
          <div className="space-y-2">
            {group.conditions.map(condition => renderCondition(condition, depth + 1))}
            {group.groups.map(subGroup => renderGroup(subGroup, depth + 1))}
            
            {group.conditions.length === 0 && group.groups.length === 0 && (
              <div className="text-sm text-gray-400 italic px-2">
                No conditions yet. Click + to add a condition.
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-4/5 max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Advanced Filter Builder
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Presets */}
        {presets.length > 0 && (
          <div className="px-6 py-3 border-b bg-gray-50">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Presets:</span>
              {presets.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => applyPreset(preset.id)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    selectedPreset === preset.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {preset.name}
                  {preset.isDefault && ' ⭐'}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Filter Builder */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {/* Root Logic Toggle */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Match</span>
              <button
                onClick={() => setFilter({ ...filter, logic: filter.logic === 'AND' ? 'OR' : 'AND' })}
                className={`px-3 py-1 rounded text-sm font-medium ${
                  filter.logic === 'AND'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-purple-100 text-purple-700'
                }`}
              >
                {filter.logic === 'AND' ? 'All' : 'Any'}
              </button>
              <span className="text-sm text-gray-500">of the following conditions:</span>
            </div>

            {/* Conditions and Groups */}
            <div className="space-y-2">
              {filter.conditions.map(condition => renderCondition(condition))}
              {filter.groups.map(group => renderGroup(group))}
              
              {filter.conditions.length === 0 && filter.groups.length === 0 && (
                <div className="text-center py-8 text-gray-400">
                  <Filter className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>No filter conditions yet.</p>
                  <p className="text-sm">Click the buttons below to add conditions or groups.</p>
                </div>
              )}
            </div>

            {/* Add Actions */}
            <div className="flex gap-2 pt-4 border-t">
              <button
                onClick={() => addCondition()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Condition
              </button>
              <button
                onClick={() => addGroup()}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
              >
                <Filter className="h-4 w-4" />
                Add Group
              </button>
              {onSavePreset && (
                <button
                  onClick={() => setShowPresetModal(true)}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
                >
                  <Save className="h-4 w-4" />
                  Save as Preset
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex items-center justify-between">
          <button
            onClick={() => setFilter({
              id: crypto.randomUUID(),
              logic: 'AND',
              conditions: [],
              groups: []
            })}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Clear All
          </button>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                onApply(filter);
                onClose();
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Apply Filter
            </button>
          </div>
        </div>

        {/* Save Preset Modal */}
        {showPresetModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60">
            <div className="bg-white rounded-lg p-6 w-96">
              <h3 className="text-lg font-semibold mb-4">Save Filter Preset</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Preset Name
                  </label>
                  <input
                    type="text"
                    value={presetName}
                    onChange={(e) => setPresetName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="e.g., High-value schemas"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description (optional)
                  </label>
                  <textarea
                    value={presetDescription}
                    onChange={(e) => setPresetDescription(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    rows={3}
                    placeholder="Describe what this filter does..."
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  onClick={() => setShowPresetModal(false)}
                  className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={saveAsPreset}
                  disabled={!presetName}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Save Preset
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}