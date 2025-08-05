import { useState, useMemo, useRef, useEffect } from 'react';
import { Search, ChevronDown, Database, Tag } from 'lucide-react';

interface Instance {
  id: string;
  instanceId: string;
  instanceName: string;
  region?: string;
  accountName?: string;
  brands?: string[];
}

interface InstanceSelectorProps {
  instances: Instance[];
  value: string;
  onChange: (instanceId: string) => void;
  placeholder?: string;
  required?: boolean;
}

export default function InstanceSelector({
  instances,
  value,
  onChange,
  placeholder = "Select an instance...",
  required = false
}: InstanceSelectorProps) {
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

  // Get selected instance
  const selectedInstance = instances.find(i => i.instanceId === value || i.id === value);

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

  const handleSelect = (instanceId: string) => {
    onChange(instanceId);
    setIsOpen(false);
    setSearchQuery('');
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

  return (
    <div ref={dropdownRef} className="relative">
      {/* Selected Value Display */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full px-3 py-2 text-left border rounded-md 
          ${selectedInstance ? 'text-gray-900' : 'text-gray-500'}
          ${isOpen ? 'border-blue-500 ring-1 ring-blue-500' : 'border-gray-300'}
          hover:border-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500
          bg-white
        `}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            {selectedInstance ? (
              <div>
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-gray-400 flex-shrink-0" />
                  <span className="font-medium truncate">{selectedInstance.instanceName}</span>
                  {selectedInstance.brands && selectedInstance.brands.length > 0 && (
                    <>
                      <span className="text-gray-400">•</span>
                      <div className="flex items-center gap-1">
                        <Tag className="h-3 w-3 text-blue-500" />
                        <span className="text-sm text-blue-600">
                          {formatBrandDisplay(selectedInstance.brands)}
                        </span>
                      </div>
                    </>
                  )}
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {selectedInstance.instanceId} • {selectedInstance.region || 'N/A'}
                </div>
              </div>
            ) : (
              <span>{placeholder}</span>
            )}
          </div>
          <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-96 overflow-hidden">
          {/* Search Input */}
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search instances, brands, or accounts..."
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Instance List */}
          <div className="max-h-64 overflow-y-auto">
            {filteredInstances.length === 0 ? (
              <div className="px-3 py-4 text-sm text-gray-500 text-center">
                No instances found matching "{searchQuery}"
              </div>
            ) : (
              filteredInstances.map(instance => (
                <button
                  key={instance.id}
                  type="button"
                  onClick={() => handleSelect(instance.instanceId)}
                  className={`
                    w-full px-3 py-2 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none
                    ${instance.instanceId === value ? 'bg-blue-50' : ''}
                  `}
                >
                  <div className="flex items-start gap-2">
                    <Database className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">
                          {instance.instanceName}
                        </span>
                        {instance.instanceId?.includes('sandbox') && (
                          <span className="px-1.5 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded">
                            Sandbox
                          </span>
                        )}
                      </div>
                      
                      {/* Brands */}
                      {instance.brands && instance.brands.length > 0 && (
                        <div className="flex items-center gap-1 mt-1">
                          <Tag className="h-3 w-3 text-blue-500" />
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
                    
                    {/* Selection indicator */}
                    {instance.instanceId === value && (
                      <div className="text-blue-600">
                        <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>
              ))
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