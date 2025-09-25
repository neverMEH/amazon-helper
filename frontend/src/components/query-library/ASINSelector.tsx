import { useState } from 'react';
import { Package, Search, X, Plus } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import asinService from '../../services/asinService';

interface ASINSelectorProps {
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  className?: string;
  instanceId?: string;
  maxItems?: number;
}

export function ASINSelector({
  value = [],
  onChange,
  placeholder = 'Select ASINs',
  className = '',
  instanceId,
  maxItems = 50
}: ASINSelectorProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [manualInput, setManualInput] = useState('');
  const [showManualInput, setShowManualInput] = useState(false);

  // Fetch available ASINs
  const { data: asinData, isLoading } = useQuery({
    queryKey: ['asins', instanceId],
    queryFn: () => asinService.listASINs({ page_size: 100, active: true }),
    enabled: true
  });

  // Extract ASINs from response
  const asins = asinData?.items || [];

  // Filter ASINs based on search
  const filteredAsins = asins.filter((asin: any) => {
    const search = searchTerm.toLowerCase();
    return (
      asin.asin?.toLowerCase().includes(search) ||
      asin.title?.toLowerCase().includes(search) ||
      asin.brand?.toLowerCase().includes(search)
    );
  });

  const handleSelect = (asin: string) => {
    if (!value.includes(asin)) {
      if (value.length < maxItems) {
        onChange([...value, asin]);
      } else {
        alert(`Maximum ${maxItems} ASINs allowed`);
      }
    } else {
      onChange(value.filter(v => v !== asin));
    }
  };

  const handleRemove = (asin: string) => {
    onChange(value.filter(v => v !== asin));
  };

  const handleManualAdd = () => {
    const asinsToAdd = manualInput
      .split(/[\s,]+/)
      .map(s => s.trim())
      .filter(s => s && !value.includes(s));

    if (asinsToAdd.length + value.length > maxItems) {
      alert(`Maximum ${maxItems} ASINs allowed`);
      return;
    }

    if (asinsToAdd.length > 0) {
      onChange([...value, ...asinsToAdd]);
      setManualInput('');
      setShowManualInput(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && manualInput.trim()) {
      e.preventDefault();
      handleManualAdd();
    }
  };

  return (
    <div className={`relative ${className}`}>
      {/* Selected ASINs display */}
      <div className="mb-2">
        {value.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {value.map(asin => (
              <span
                key={asin}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
              >
                {asin}
                <button
                  onClick={() => handleRemove(asin)}
                  className="ml-1 text-indigo-600 hover:text-indigo-800"
                  type="button"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">{placeholder}</p>
        )}
      </div>

      {/* Search/Select dropdown */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-left bg-white hover:bg-gray-50
                   focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Package className="h-4 w-4 mr-2 text-gray-400" />
              <span className="text-sm text-gray-700">
                {value.length > 0 ? `${value.length} ASINs selected` : 'Click to select ASINs'}
              </span>
            </div>
            <Search className="h-4 w-4 text-gray-400" />
          </div>
        </button>

        {/* Dropdown */}
        {isOpen && (
          <div className="absolute z-50 mt-1 w-full bg-white rounded-md shadow-lg border border-gray-200">
            {/* Search input */}
            <div className="p-2 border-b">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search ASINs..."
                className="w-full px-3 py-1 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-1 focus:ring-indigo-500"
                onClick={(e) => e.stopPropagation()}
              />
            </div>

            {/* Manual input option */}
            <div className="p-2 border-b">
              {!showManualInput ? (
                <button
                  type="button"
                  onClick={() => setShowManualInput(true)}
                  className="w-full text-left px-3 py-1 text-sm text-indigo-600 hover:bg-indigo-50 rounded"
                >
                  <Plus className="h-4 w-4 inline mr-1" />
                  Add ASINs manually
                </button>
              ) : (
                <div className="space-y-2">
                  <input
                    type="text"
                    value={manualInput}
                    onChange={(e) => setManualInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Enter ASINs (comma or space separated)"
                    className="w-full px-3 py-1 border border-gray-300 rounded-md text-sm
                             focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    autoFocus
                  />
                  <div className="flex justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => {
                        setShowManualInput(false);
                        setManualInput('');
                      }}
                      className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleManualAdd}
                      className="px-2 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700"
                    >
                      Add
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* ASIN list */}
            <div className="max-h-60 overflow-y-auto">
              {isLoading ? (
                <div className="p-3 text-sm text-gray-500 text-center">Loading ASINs...</div>
              ) : filteredAsins.length === 0 ? (
                <div className="p-3 text-sm text-gray-500 text-center">
                  No ASINs found
                </div>
              ) : (
                <div className="py-1">
                  {filteredAsins.map((asin: any) => (
                    <label
                      key={asin.asin}
                      className="flex items-start px-3 py-2 hover:bg-gray-50 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={value.includes(asin.asin)}
                        onChange={() => handleSelect(asin.asin)}
                        className="mt-0.5 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <div className="ml-3 flex-1">
                        <div className="text-sm font-medium text-gray-900">
                          {asin.asin}
                        </div>
                        {asin.product_name && (
                          <div className="text-xs text-gray-500 line-clamp-1">
                            {asin.product_name}
                          </div>
                        )}
                        {asin.brand && (
                          <div className="text-xs text-gray-400">
                            Brand: {asin.brand}
                          </div>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-2 border-t bg-gray-50 text-xs text-gray-500 flex justify-between">
              <span>{value.length} of {maxItems} selected</span>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-indigo-600 hover:text-indigo-800 font-medium"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}