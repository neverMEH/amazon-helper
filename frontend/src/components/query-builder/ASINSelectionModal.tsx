import React, { useState, useEffect, useMemo } from 'react';
import { X, Search, Package, CheckSquare, Square } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import asinService, { type ASINSearchResponse } from '../../services/asinService';
import LoadingSpinner from '../LoadingSpinner';

interface ASINSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (asins: string[]) => void;
  currentValue?: string[] | string;
  multiple?: boolean;
  title?: string;
  defaultBrand?: string;
  brandLocked?: boolean;
}

const ASINSelectionModal: React.FC<ASINSelectionModalProps> = ({
  isOpen,
  onClose,
  onSelect,
  currentValue = [],
  multiple = true,
  title = 'Select ASINs',
  defaultBrand = '',
  brandLocked = false
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBrand, setSelectedBrand] = useState<string>(defaultBrand);
  const [selectedAsins, setSelectedAsins] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const pageSize = 100;

  // Initialize selected ASINs from current value
  useEffect(() => {
    if (currentValue) {
      const asins = Array.isArray(currentValue) 
        ? currentValue 
        : currentValue.split(',').map(a => a.trim()).filter(Boolean);
      setSelectedAsins(new Set(asins));
    }
    // Set default brand when modal opens
    if (isOpen && defaultBrand) {
      setSelectedBrand(defaultBrand);
    }
  }, [currentValue, isOpen, defaultBrand]);

  // Fetch brands
  const { data: brandsData } = useQuery({
    queryKey: ['asin-brands'],
    queryFn: () => asinService.getBrands(),
    enabled: isOpen,
    staleTime: 10 * 60 * 1000
  });

  // Search ASINs
  const { data: searchResults, isLoading } = useQuery<ASINSearchResponse>({
    queryKey: ['asin-search', selectedBrand, searchQuery, page],
    queryFn: async () => {
      // Use the list endpoint for pagination
      const response = await asinService.listASINs({
        page,
        page_size: pageSize,
        brand: selectedBrand || undefined,
        search: searchQuery || undefined,
        active: true
      });
      
      // Transform to match search response format
      return {
        asins: response.items.map(item => ({
          asin: item.asin,
          title: item.title,
          brand: item.brand
        })),
        total: response.total
      };
    },
    enabled: isOpen
  });

  // Filter results based on search
  const filteredAsins = useMemo(() => {
    if (!searchResults) return [];
    
    return searchResults.asins.filter(asin => {
      const query = searchQuery.toLowerCase();
      return !query || 
        asin.asin.toLowerCase().includes(query) ||
        (asin.title && asin.title.toLowerCase().includes(query));
    });
  }, [searchResults, searchQuery]);

  const handleToggleAsin = (asin: string) => {
    const newSelection = new Set(selectedAsins);
    if (newSelection.has(asin)) {
      newSelection.delete(asin);
    } else {
      if (multiple) {
        newSelection.add(asin);
      } else {
        // Single selection mode
        newSelection.clear();
        newSelection.add(asin);
      }
    }
    setSelectedAsins(newSelection);
  };

  const handleSelectAll = () => {
    if (filteredAsins.length === 0) return;
    
    const allSelected = filteredAsins.every(a => selectedAsins.has(a.asin));
    const newSelection = new Set(selectedAsins);
    
    filteredAsins.forEach(asin => {
      if (allSelected) {
        newSelection.delete(asin.asin);
      } else {
        newSelection.add(asin.asin);
      }
    });
    
    setSelectedAsins(newSelection);
  };

  const handleSelectByBrand = () => {
    if (!selectedBrand || !filteredAsins.length) return;
    
    const brandAsins = filteredAsins.filter(a => a.brand === selectedBrand);
    const allBrandSelected = brandAsins.every(a => selectedAsins.has(a.asin));
    const newSelection = new Set(selectedAsins);
    
    brandAsins.forEach(asin => {
      if (allBrandSelected) {
        newSelection.delete(asin.asin);
      } else {
        newSelection.add(asin.asin);
      }
    });
    
    setSelectedAsins(newSelection);
  };

  const handleConfirm = () => {
    onSelect(Array.from(selectedAsins));
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center">
            <Package className="w-6 h-6 text-blue-600 mr-3" />
            <div>
              <h2 className="text-xl font-semibold">{title}</h2>
              <p className="text-sm text-gray-600">
                {multiple 
                  ? `Select multiple ASINs (${selectedAsins.size} selected)`
                  : 'Select an ASIN'
                }
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Filters */}
        <div className="p-4 border-b bg-gray-50">
          <div className="flex gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by ASIN or title..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Brand Filter */}
            <div className="w-64">
              <select
                value={selectedBrand}
                onChange={(e) => setSelectedBrand(e.target.value)}
                disabled={brandLocked}
                className={`w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  brandLocked ? 'bg-gray-100 cursor-not-allowed' : ''
                }`}
                title={brandLocked ? `Brand filter is locked to ${selectedBrand}` : 'Filter by brand'}
              >
                <option value="">All Brands</option>
                {brandsData?.brands.map(brand => (
                  <option key={brand} value={brand}>{brand}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Bulk Actions */}
          {multiple && (
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleSelectAll}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                {filteredAsins.every(a => selectedAsins.has(a.asin)) 
                  ? 'Deselect All' 
                  : 'Select All Visible'
                }
              </button>
              {selectedBrand && (
                <button
                  onClick={handleSelectByBrand}
                  className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  {filteredAsins
                    .filter(a => a.brand === selectedBrand)
                    .every(a => selectedAsins.has(a.asin))
                    ? `Deselect All ${selectedBrand}`
                    : `Select All ${selectedBrand}`
                  }
                </button>
              )}
            </div>
          )}
        </div>

        {/* ASIN List */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : filteredAsins.length === 0 ? (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No ASINs found</p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredAsins.map(asin => (
                <div
                  key={asin.asin}
                  onClick={() => handleToggleAsin(asin.asin)}
                  className={`
                    flex items-center p-3 rounded-lg border cursor-pointer transition-colors
                    ${selectedAsins.has(asin.asin) 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:bg-gray-50'
                    }
                  `}
                >
                  <div className="mr-3">
                    {selectedAsins.has(asin.asin) ? (
                      <CheckSquare className="w-5 h-5 text-blue-600" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-medium">{asin.asin}</span>
                      {asin.brand && (
                        <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                          {asin.brand}
                        </span>
                      )}
                    </div>
                    {asin.title && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-1">{asin.title}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {searchResults && searchResults.total > pageSize && (
            <div className="mt-6 flex justify-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-3 py-1">
                Page {page} of {Math.ceil(searchResults.total / pageSize)}
              </span>
              <button
                onClick={() => setPage(p => Math.min(Math.ceil(searchResults.total / pageSize), p + 1))}
                disabled={page >= Math.ceil(searchResults.total / pageSize)}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center px-6 py-4 bg-gray-50 border-t">
          <div className="text-sm text-gray-600">
            {selectedAsins.size} ASIN{selectedAsins.size !== 1 ? 's' : ''} selected
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={selectedAsins.size === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Confirm Selection
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ASINSelectionModal;