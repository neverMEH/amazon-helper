import { useState, useEffect, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, X, Package } from 'lucide-react';
import api from '../../services/api';
import type { FC } from 'react';

interface ASINSelectorProps {
  instanceId?: string;  // Now optional
  brandId?: string;  // Now optional
  value: string[] | string | null;
  onChange: (value: string[]) => void;
  placeholder?: string;
  multiple?: boolean;
  showAll?: boolean;  // Show all ASINs without filtering
  className?: string;
}

interface ASIN {
  asin: string;
  product_title: string;
  brand_name: string;
}

/**
 * Component for selecting ASINs with optional filtering by instance and brand
 */
export const ASINSelector: FC<ASINSelectorProps> = ({
  instanceId,
  brandId,
  value,
  onChange,
  placeholder = 'Select ASINs...',
  multiple = true,
  showAll = false,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedASINs, setSelectedASINs] = useState<Set<string>>(new Set());

  // Convert value to Set for easier manipulation
  useEffect(() => {
    if (value) {
      const asins = Array.isArray(value) ? value : [value];
      setSelectedASINs(new Set(asins));
    } else {
      setSelectedASINs(new Set());
    }
  }, [value]);

  // Fetch ASINs from the API
  const { data, isLoading, error } = useQuery({
    queryKey: ['asins', instanceId, brandId, searchTerm, showAll],
    queryFn: async () => {
      // If showAll is true or no filters, use the regular ASINs endpoint
      if (showAll || (!instanceId && !brandId)) {
        const params = new URLSearchParams({
          page: '1',
          page_size: '200',  // Get more ASINs when showing all
        });
        
        if (searchTerm) {
          params.append('search', searchTerm);
        }
        
        const response = await api.get(`/asins/?${params.toString()}`);
        return response.data;
      } else {
        // Use the filtered endpoint when instance/brand are provided
        const params = new URLSearchParams({
          instance_id: instanceId || '',
          brand_id: brandId || '',
          limit: '100',
          offset: '0'
        });
        
        if (searchTerm) {
          params.append('search', searchTerm);
        }

        const response = await api.get(`/asins/by-instance-brand/list?${params.toString()}`);
        return response.data;
      }
    },
    enabled: isOpen && (showAll || (!!instanceId && !!brandId)),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  const asins = data?.asins || [];

  // Handle ASIN selection
  const handleToggleASIN = useCallback((asin: string) => {
    const newSelected = new Set(selectedASINs);
    
    if (multiple) {
      if (newSelected.has(asin)) {
        newSelected.delete(asin);
      } else {
        newSelected.add(asin);
      }
    } else {
      newSelected.clear();
      newSelected.add(asin);
      setIsOpen(false);
    }
    
    setSelectedASINs(newSelected);
    onChange(Array.from(newSelected));
  }, [selectedASINs, onChange, multiple]);

  // Handle select all
  const handleSelectAll = useCallback(() => {
    const allAsins = asins.map((a: ASIN) => a.asin);
    setSelectedASINs(new Set(allAsins));
    onChange(allAsins);
  }, [asins, onChange]);

  // Handle clear selection
  const handleClearSelection = useCallback(() => {
    setSelectedASINs(new Set());
    onChange([]);
  }, [onChange]);

  // Get display text for selected ASINs
  const displayText = useMemo(() => {
    if (!selectedASINs.size) {
      return placeholder;
    }
    
    if (selectedASINs.size === 1) {
      const asin = Array.from(selectedASINs)[0];
      const asinData = asins.find((a: ASIN) => a.asin === asin);
      return asinData ? `${asinData.asin} - ${asinData.product_title}` : asin;
    }
    
    return `${selectedASINs.size} ASINs selected`;
  }, [selectedASINs, asins, placeholder]);

  return (
    <div className={`relative ${className}`}>
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 hover:bg-gray-50"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Package className="h-4 w-4 text-gray-400 mr-2" />
            <span className={selectedASINs.size ? 'text-gray-900' : 'text-gray-500'}>
              {displayText}
            </span>
          </div>
          {selectedASINs.size > 0 && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleClearSelection();
              }}
              className="ml-2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </button>

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg">
          {/* Search input */}
          <div className="p-2 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Search ASINs or product titles..."
                autoFocus
              />
            </div>
          </div>

          {/* Action buttons */}
          {multiple && (
            <div className="p-2 border-b flex justify-between">
              <button
                type="button"
                onClick={handleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Select All ({asins.length})
              </button>
              <button
                type="button"
                onClick={handleClearSelection}
                className="text-sm text-gray-600 hover:text-gray-700"
              >
                Clear Selection
              </button>
            </div>
          )}

          {/* ASIN list */}
          <div className="max-h-60 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center text-gray-500">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                Loading ASINs...
              </div>
            ) : error ? (
              <div className="p-4 text-center text-red-600">
                Error loading ASINs. Please try again.
              </div>
            ) : asins.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No ASINs found{!showAll && brandId ? ' for this brand' : ''}
              </div>
            ) : (
              <div className="py-1">
                {asins.map((asin: ASIN) => (
                  <label
                    key={asin.asin}
                    className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type={multiple ? 'checkbox' : 'radio'}
                      checked={selectedASINs.has(asin.asin)}
                      onChange={() => handleToggleASIN(asin.asin)}
                      className="mr-3 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        {asin.asin}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {asin.product_title}
                        {showAll && asin.brand_name && (
                          <span className="ml-2">• {asin.brand_name}</span>
                        )}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Close button */}
          <div className="p-2 border-t">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="w-full px-3 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};