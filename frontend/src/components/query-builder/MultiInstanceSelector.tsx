import { useState, useMemo, useRef, useEffect } from 'react';
import { Search, ChevronDown, Database, Tag, Check, X } from 'lucide-react';

interface Instance {
  id: string;
  instanceId: string;
  instanceName: string;
  region?: string;
  accountName?: string;
  brands?: string[];
}

interface MultiInstanceSelectorProps {
  instances: Instance[];
  value: string[];  // Array of selected instance IDs
  onChange: (instanceIds: string[]) => void;
  placeholder?: string;
  maxHeight?: string;
}

export default function MultiInstanceSelector({
  instances,
  value = [],
  onChange,
  placeholder = "Select instances...",
  maxHeight = "max-h-96"
}: MultiInstanceSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter instances based on search query
  const filteredInstances = useMemo(() => {
    if (!searchQuery) return instances;
    
    const query = searchQuery.toLowerCase();
    return instances.filter(instance => {
      // Search by instance name
      if (instance.instanceName?.toLowerCase().includes(query)) return true;
      
      // Search by instance ID
      if (instance.instanceId?.toLowerCase().includes(query)) return true;
      
      // Search by brand names
      if (instance.brands?.some(brand => brand.toLowerCase().includes(query))) return true;
      
      // Search by account name
      if (instance.accountName?.toLowerCase().includes(query)) return true;
      
      return false;
    });
  }, [instances, searchQuery]);

  // Get selected instances (support both instanceId and id)
  const selectedInstances = instances.filter(i => value.includes(i.instanceId) || value.includes(i.id));

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleToggleInstance = (instance: Instance) => {
    // Use id (UUID) for backend compatibility
    const instanceId = instance.id || instance.instanceId;
    const isSelected = value.includes(instanceId);
    if (isSelected) {
      onChange(value.filter(id => id !== instanceId));
    } else {
      onChange([...value, instanceId]);
    }
  };

  const handleSelectAll = () => {
    // Use id (UUID) for backend compatibility
    const visibleInstanceIds = filteredInstances.map(i => i.id || i.instanceId);
    const allSelected = visibleInstanceIds.every(id => value.includes(id));
    
    if (allSelected) {
      // Deselect all visible instances
      onChange(value.filter(id => !visibleInstanceIds.includes(id)));
    } else {
      // Select all visible instances
      const newSelection = new Set([...value, ...visibleInstanceIds]);
      onChange(Array.from(newSelection));
    }
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const handleRemoveInstance = (instance: Instance) => {
    const instanceId = instance.id || instance.instanceId;
    onChange(value.filter(id => id !== instanceId));
  };

  const formatBrandDisplay = (brands?: string[]) => {
    if (!brands || brands.length === 0) return null;
    
    if (brands.length === 1) {
      return brands[0];
    } else if (brands.length === 2) {
      return brands.join(' & ');
    } else {
      return `${brands[0]} & ${brands.length - 1} more`;
    }
  };

  const allVisibleSelected = filteredInstances.length > 0 && 
    filteredInstances.every(i => value.includes(i.id || i.instanceId));

  return (
    <div ref={dropdownRef} className="relative" role="combobox" aria-expanded={isOpen} aria-haspopup="listbox" aria-owns="instance-listbox">
      {/* Selected Value Display */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full px-3 py-2 text-left border rounded-md 
          ${selectedInstances.length > 0 ? 'text-gray-900' : 'text-gray-500'}
          ${isOpen ? 'border-blue-500 ring-1 ring-blue-500' : 'border-gray-300'}
          hover:border-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500
          bg-white
        `}
        aria-label={`Select instances. ${selectedInstances.length} instance${selectedInstances.length !== 1 ? 's' : ''} selected`}
        aria-controls="instance-listbox"
      >
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            {selectedInstances.length === 0 ? (
              <span>{placeholder}</span>
            ) : selectedInstances.length === 1 ? (
              <div>
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
                  <span className="font-medium truncate">{selectedInstances[0].instanceName}</span>
                  {selectedInstances[0].brands && selectedInstances[0].brands.length > 0 && (
                    <>
                      <span className="text-gray-400">•</span>
                      <div className="flex items-center gap-1">
                        <Tag className="h-3 w-3 text-blue-500" />
                        <span className="text-sm text-blue-600">
                          {formatBrandDisplay(selectedInstances[0].brands)}
                        </span>
                      </div>
                    </>
                  )}
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {selectedInstances[0].instanceId} • {selectedInstances[0].region || 'N/A'}
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 flex-wrap">
                <Database className="h-4 w-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
                <span className="font-medium">
                  {selectedInstances.length} instances selected
                </span>
                {/* Show first few instance names */}
                <div className="flex items-center gap-1 flex-wrap">
                  {selectedInstances.slice(0, 2).map((instance, idx) => (
                    <span key={instance.id} className="text-sm text-gray-600">
                      {idx > 0 && ', '}{instance.instanceName}
                    </span>
                  ))}
                  {selectedInstances.length > 2 && (
                    <span className="text-sm text-gray-500">
                      +{selectedInstances.length - 2} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {selectedInstances.length > 0 && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClearAll();
                }}
                className="text-gray-400 hover:text-gray-600"
                title="Clear all selections"
                aria-label="Clear all selected instances"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
          </div>
        </div>
      </button>

      {/* Selected Instance Pills (shown when multiple selected and dropdown closed) */}
      {!isOpen && selectedInstances.length > 1 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {selectedInstances.map(instance => (
            <div
              key={instance.id}
              className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded-md text-sm"
            >
              <span>{instance.instanceName}</span>
              <button
                type="button"
                onClick={() => handleRemoveInstance(instance)}
                className="hover:text-blue-900"
                aria-label={`Remove ${instance.instanceName} from selection`}
              >
                <X className="h-3 w-3" aria-hidden="true" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Dropdown */}
      {isOpen && (
        <div id="instance-listbox" role="listbox" aria-multiselectable="true" className={`absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg ${maxHeight} overflow-hidden`}>
          {/* Search Input */}
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search instances, brands, or accounts..."
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                aria-label="Search instances"
                aria-controls="instance-list"
                aria-autocomplete="list"
              />
            </div>
          </div>

          {/* Select All / Clear All */}
          <div className="px-3 py-2 border-b border-gray-200 flex items-center justify-between">
            <button
              type="button"
              onClick={handleSelectAll}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {allVisibleSelected ? 'Deselect All' : 'Select All'}
            </button>
            <div className="text-xs text-gray-500">
              {value.length} of {instances.length} selected
            </div>
          </div>

          {/* Instance List */}
          <div id="instance-list" className="max-h-64 overflow-y-auto" role="group" aria-label="Available instances">
            {filteredInstances.length === 0 ? (
              <div className="px-3 py-4 text-sm text-gray-500 text-center">
                No instances found matching "{searchQuery}"
              </div>
            ) : (
              filteredInstances.map(instance => {
                const instanceId = instance.id || instance.instanceId;
                const isSelected = value.includes(instanceId);
                return (
                  <button
                    key={instance.id}
                    type="button"
                    onClick={() => handleToggleInstance(instance)}
                    className={`
                      w-full px-3 py-2 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none
                      ${isSelected ? 'bg-blue-50' : ''}
                    `}
                    role="option"
                    aria-selected={isSelected}
                    aria-label={`${instance.instanceName}, ${instance.instanceId}, ${instance.region || 'N/A'}${instance.brands && instance.brands.length > 0 ? `, brands: ${instance.brands.join(', ')}` : ''}`}
                  >
                    <div className="flex items-start gap-2">
                      {/* Checkbox */}
                      <div className="mt-0.5">
                        <div className={`
                          w-4 h-4 border rounded flex items-center justify-center
                          ${isSelected ? 'bg-blue-600 border-blue-600' : 'border-gray-300'}
                        `}
                          role="checkbox"
                          aria-checked={isSelected}
                          aria-label={`Select ${instance.instanceName}`}
                        >
                          {isSelected && (
                            <Check className="h-3 w-3 text-white" aria-hidden="true" />
                          )}
                        </div>
                      </div>
                      
                      <Database className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" aria-hidden="true" />
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">
                            {instance.instanceName}
                          </span>
                        </div>
                        
                        {/* Brands */}
                        {instance.brands && instance.brands.length > 0 && (
                          <div className="flex items-center gap-1 mt-1">
                            <Tag className="h-3 w-3 text-blue-500" aria-hidden="true" />
                            <span className="text-xs text-blue-600">
                              {instance.brands.slice(0, 3).join(', ')}
                              {instance.brands.length > 3 && ` +${instance.brands.length - 3} more`}
                            </span>
                          </div>
                        )}
                        
                        {/* Instance details */}
                        <div className="text-xs text-gray-500 mt-0.5">
                          {instance.instanceId} • {instance.region || 'N/A'} 
                          {instance.accountName && ` • ${instance.accountName}`}
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Results count */}
          {searchQuery && filteredInstances.length > 0 && (
            <div className="px-3 py-2 text-xs text-gray-500 border-t border-gray-200">
              Showing {filteredInstances.length} of {instances.length} instances
            </div>
          )}
        </div>
      )}
    </div>
  );
}