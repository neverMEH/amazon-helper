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
  title?: string;
  product_title?: string;  // Some endpoints use product_title
  brand?: string;
  brand_name?: string;  // Some endpoints use brand_name
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
  const [selectedBrand, setSelectedBrand] = useState<string>('');
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

  // Fetch ASINs from the API - don't include searchTerm in query to get all ASINs for client-side filtering
  const { data, isLoading, error } = useQuery({
    queryKey: ['asins', instanceId, brandId, showAll],
    queryFn: async () => {
      // If showAll is true or no filters, use the regular ASINs endpoint
      if (showAll || (!instanceId && !brandId)) {
        const params = new URLSearchParams({
          page: '1',
          page_size: '999999',  // Load all ASINs - effectively no limit
        });

        // Note: We don't send searchTerm to backend anymore for better brand filtering
        // Backend search might not include brand name search

        const response = await api.get(`/asins/?${params.toString()}`);
        return response.data;
      } else {
        // Use the filtered endpoint when instance/brand are provided
        const params = new URLSearchParams({
          instance_id: instanceId || '',
          brand_id: brandId || '',
          limit: '999999',  // Load all ASINs - effectively no limit
          offset: '0'
        });

        const response = await api.get(`/asins/by-instance-brand/list?${params.toString()}`);
        return response.data;
      }
    },
    enabled: isOpen,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Handle different response structures
  const rawAsins = data?.asins || data?.items || [];

  // Extract unique brands for dropdown
  const uniqueBrands = useMemo(() => {
    const brands = new Set<string>();
    rawAsins.forEach((asin: ASIN) => {
      const brand = asin.brand || asin.brand_name;
      if (brand) brands.add(brand);
    });
    return Array.from(brands).sort();
  }, [rawAsins]);

  // Filter ASINs client-side to include brand name matching
  const asins = useMemo(() => {
    let filtered = rawAsins;

    // Filter by selected brand first
    if (selectedBrand) {
      filtered = filtered.filter((asin: ASIN) => {
        const brand = asin.brand || asin.brand_name;
        return brand === selectedBrand;
      });
    }

    // Then filter by search term
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase().trim();
      filtered = filtered.filter((asin: ASIN) => {
        // Check ASIN code
        if (asin.asin?.toLowerCase().includes(searchLower)) return true;
        // Check product title (handle both field names)
        const title = asin.title || asin.product_title;
        if (title?.toLowerCase().includes(searchLower)) return true;
        // Check brand name (handle both field names)
        const brand = asin.brand || asin.brand_name;
        if (brand?.toLowerCase().includes(searchLower)) return true;

        // Also check if brand matches with spaces removed (e.g., "supergoop" matches "Super Goop")
        if (brand) {
          const brandNoSpaces = brand.toLowerCase().replace(/\s+/g, '');
          const searchNoSpaces = searchLower.replace(/\s+/g, '');
          if (brandNoSpaces.includes(searchNoSpaces)) return true;
        }

        return false;
      });
    }

    return filtered;
  }, [rawAsins, searchTerm, selectedBrand]);

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
      const title = asinData?.title || asinData?.product_title || 'No title';
      return asinData ? `${asinData.asin} - ${title}` : asin;
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

      {/* Dropdown panel - Made bigger */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full min-w-[600px] bg-white border border-gray-300 rounded-md shadow-lg">
          {/* Search and filter inputs */}
          <div className="p-3 border-b space-y-2">
            {/* Brand dropdown filter */}
            <div className="flex gap-2">
              <select
                value={selectedBrand}
                onChange={(e) => setSelectedBrand(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Brands ({uniqueBrands.length})</option>
                {uniqueBrands.map(brand => (
                  <option key={brand} value={brand}>
                    {brand} ({rawAsins.filter((a: ASIN) => (a.brand || a.brand_name) === brand).length} ASINs)
                  </option>
                ))}
              </select>
              {selectedBrand && (
                <button
                  type="button"
                  onClick={() => setSelectedBrand('')}
                  className="px-3 py-2 text-sm text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Clear Filter
                </button>
              )}
            </div>

            {/* Search input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Search by ASIN or title..."
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
                Select All ({asins.length}{rawAsins.length > asins.length ? ` of ${rawAsins.length}` : ''})
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

          {/* ASIN list - Made taller */}
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center text-gray-500">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                Loading all ASINs from database...
              </div>
            ) : error ? (
              <div className="p-4 text-center text-red-600">
                Error loading ASINs: {(error as any)?.message || 'Please try again.'}
                {console.error('ASIN Load Error:', error)}
              </div>
            ) : asins.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No ASINs found{!showAll && brandId ? ' for this brand' : ''}
                {rawAsins.length > 0 && searchTerm && (
                  <div className="text-xs mt-1">
                    ({rawAsins.length} ASINs available, none match "{searchTerm}")
                  </div>
                )}
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
                        {asin.title || asin.product_title || 'No title available'}
                        {(asin.brand || asin.brand_name) && (
                          <span className="ml-2 font-medium">• {asin.brand || asin.brand_name}</span>
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