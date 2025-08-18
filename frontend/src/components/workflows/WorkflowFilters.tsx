import { useState, useEffect } from 'react';
import { X, Filter, Calendar, Tag, Database, CloudOff, Cloud, Hash } from 'lucide-react';
import { format } from 'date-fns';

export interface WorkflowFiltersConfig {
  status: string[];
  instanceIds: string[];
  syncStatus: 'all' | 'synced' | 'not_synced';
  tags: string[];
  dateRange: {
    field: 'createdAt' | 'updatedAt' | 'lastExecutedAt';
    from: string | null;
    to: string | null;
  };
  executionCountRange: {
    min: number | null;
    max: number | null;
  };
}

interface WorkflowFiltersProps {
  filters: WorkflowFiltersConfig;
  onChange: (filters: WorkflowFiltersConfig) => void;
  availableInstances: Array<{ id: string; name: string; instanceId: string }>;
  availableTags: string[];
  isOpen: boolean;
  onClose: () => void;
}

export default function WorkflowFilters({
  filters,
  onChange,
  availableInstances,
  availableTags,
  isOpen,
  onClose
}: WorkflowFiltersProps) {
  const [localFilters, setLocalFilters] = useState<WorkflowFiltersConfig>(filters);

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleApply = () => {
    onChange(localFilters);
    onClose();
  };

  const handleReset = () => {
    const resetFilters: WorkflowFiltersConfig = {
      status: [],
      instanceIds: [],
      syncStatus: 'all',
      tags: [],
      dateRange: {
        field: 'createdAt',
        from: null,
        to: null
      },
      executionCountRange: {
        min: null,
        max: null
      }
    };
    setLocalFilters(resetFilters);
    onChange(resetFilters);
  };

  const handleStatusToggle = (status: string) => {
    setLocalFilters(prev => ({
      ...prev,
      status: prev.status.includes(status)
        ? prev.status.filter(s => s !== status)
        : [...prev.status, status]
    }));
  };

  const handleInstanceToggle = (instanceId: string) => {
    setLocalFilters(prev => ({
      ...prev,
      instanceIds: prev.instanceIds.includes(instanceId)
        ? prev.instanceIds.filter(id => id !== instanceId)
        : [...prev.instanceIds, instanceId]
    }));
  };

  const handleTagToggle = (tag: string) => {
    setLocalFilters(prev => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter(t => t !== tag)
        : [...prev.tags, tag]
    }));
  };

  const setDatePreset = (preset: string) => {
    const now = new Date();
    let from: Date | null = null;

    switch (preset) {
      case 'today':
        from = new Date(now.setHours(0, 0, 0, 0));
        break;
      case 'week':
        from = new Date(now.setDate(now.getDate() - 7));
        break;
      case 'month':
        from = new Date(now.setMonth(now.getMonth() - 1));
        break;
      case 'quarter':
        from = new Date(now.setMonth(now.getMonth() - 3));
        break;
    }

    setLocalFilters(prev => ({
      ...prev,
      dateRange: {
        ...prev.dateRange,
        from: from ? format(from, 'yyyy-MM-dd') : null,
        to: format(new Date(), 'yyyy-MM-dd')
      }
    }));
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-25 z-40 lg:hidden"
        onClick={onClose}
      />

      {/* Sidebar */}
      <div className={`fixed right-0 top-0 h-full w-80 bg-white shadow-xl z-50 transform transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      } lg:relative lg:translate-x-0 lg:shadow-none lg:border-l lg:border-gray-200`}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Filter className="h-5 w-5 mr-2" />
              Filters
            </h3>
            <button
              onClick={onClose}
              className="lg:hidden text-gray-400 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Filter Sections */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
            {/* Status Filter */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Status</h4>
              <div className="space-y-2">
                {['active', 'draft', 'archived'].map(status => (
                  <label key={status} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={localFilters.status.includes(status)}
                      onChange={() => handleStatusToggle(status)}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 capitalize">{status}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Instance Filter */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
                <Database className="h-4 w-4 mr-1" />
                Instances
              </h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {availableInstances.map(instance => (
                  <label key={instance.id} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={localFilters.instanceIds.includes(instance.instanceId)}
                      onChange={() => handleInstanceToggle(instance.instanceId)}
                      className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 truncate" title={instance.name}>
                      {instance.name}
                    </span>
                  </label>
                ))}
                {availableInstances.length === 0 && (
                  <p className="text-sm text-gray-500">No instances available</p>
                )}
              </div>
            </div>

            {/* Sync Status Filter */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
                <Cloud className="h-4 w-4 mr-1" />
                AMC Sync Status
              </h4>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="syncStatus"
                    checked={localFilters.syncStatus === 'all'}
                    onChange={() => setLocalFilters(prev => ({ ...prev, syncStatus: 'all' }))}
                    className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">All</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="syncStatus"
                    checked={localFilters.syncStatus === 'synced'}
                    onChange={() => setLocalFilters(prev => ({ ...prev, syncStatus: 'synced' }))}
                    className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 flex items-center">
                    <Cloud className="h-3 w-3 mr-1 text-blue-500" />
                    Synced
                  </span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="syncStatus"
                    checked={localFilters.syncStatus === 'not_synced'}
                    onChange={() => setLocalFilters(prev => ({ ...prev, syncStatus: 'not_synced' }))}
                    className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 flex items-center">
                    <CloudOff className="h-3 w-3 mr-1 text-gray-400" />
                    Not Synced
                  </span>
                </label>
              </div>
            </div>

            {/* Tags Filter */}
            {availableTags.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
                  <Tag className="h-4 w-4 mr-1" />
                  Tags
                </h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {availableTags.map(tag => (
                    <label key={tag} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={localFilters.tags.includes(tag)}
                        onChange={() => handleTagToggle(tag)}
                        className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{tag}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Date Range Filter */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
                <Calendar className="h-4 w-4 mr-1" />
                Date Range
              </h4>
              <div className="space-y-2">
                <select
                  value={localFilters.dateRange.field}
                  onChange={(e) => setLocalFilters(prev => ({
                    ...prev,
                    dateRange: { ...prev.dateRange, field: e.target.value as any }
                  }))}
                  className="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="createdAt">Created Date</option>
                  <option value="updatedAt">Updated Date</option>
                  <option value="lastExecutedAt">Last Executed</option>
                </select>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => setDatePreset('today')}
                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    Today
                  </button>
                  <button
                    onClick={() => setDatePreset('week')}
                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    7 Days
                  </button>
                  <button
                    onClick={() => setDatePreset('month')}
                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    30 Days
                  </button>
                  <button
                    onClick={() => setDatePreset('quarter')}
                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    90 Days
                  </button>
                </div>

                <div className="space-y-2">
                  <input
                    type="date"
                    value={localFilters.dateRange.from || ''}
                    onChange={(e) => setLocalFilters(prev => ({
                      ...prev,
                      dateRange: { ...prev.dateRange, from: e.target.value || null }
                    }))}
                    className="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="From"
                  />
                  <input
                    type="date"
                    value={localFilters.dateRange.to || ''}
                    onChange={(e) => setLocalFilters(prev => ({
                      ...prev,
                      dateRange: { ...prev.dateRange, to: e.target.value || null }
                    }))}
                    className="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="To"
                  />
                </div>
              </div>
            </div>

            {/* Execution Count Range */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
                <Hash className="h-4 w-4 mr-1" />
                Execution Count
              </h4>
              <div className="flex gap-2">
                <input
                  type="number"
                  min="0"
                  placeholder="Min"
                  value={localFilters.executionCountRange.min || ''}
                  onChange={(e) => setLocalFilters(prev => ({
                    ...prev,
                    executionCountRange: {
                      ...prev.executionCountRange,
                      min: e.target.value ? parseInt(e.target.value) : null
                    }
                  }))}
                  className="w-1/2 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
                <input
                  type="number"
                  min="0"
                  placeholder="Max"
                  value={localFilters.executionCountRange.max || ''}
                  onChange={(e) => setLocalFilters(prev => ({
                    ...prev,
                    executionCountRange: {
                      ...prev.executionCountRange,
                      max: e.target.value ? parseInt(e.target.value) : null
                    }
                  }))}
                  className="w-1/2 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="px-4 py-3 border-t border-gray-200 flex justify-between">
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Reset All
            </button>
            <div className="flex gap-2">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleApply}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}