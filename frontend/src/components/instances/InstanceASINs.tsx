import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, Package, ExternalLink, X } from 'lucide-react';
import instanceMappingService from '../../services/instanceMappingService';
import asinService, { type ASINDetail } from '../../services/asinService';

interface InstanceASINsProps {
  instanceId: string;
}

export default function InstanceASINs({ instanceId }: InstanceASINsProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBrand, setSelectedBrand] = useState<string>('');
  const [selectedProductGroup, setSelectedProductGroup] = useState<string>('');
  const [selectedProductType, setSelectedProductType] = useState<string>('');

  // Fetch instance mappings to get mapped ASIN IDs
  const { data: mappings, isLoading: mappingsLoading } = useQuery({
    queryKey: ['instanceMappings', instanceId],
    queryFn: () => instanceMappingService.getInstanceMappings(instanceId),
  });

  // Get all mapped ASIN IDs
  const mappedASINIds = useMemo(() => {
    const asinIds: string[] = [];
    if (mappings?.asins_by_brand) {
      Object.values(mappings.asins_by_brand).forEach((asins) => {
        asinIds.push(...asins);
      });
    }
    return asinIds;
  }, [mappings]);

  // Fetch full ASIN details for all mapped ASINs
  const { data: asinsData, isLoading: asinsLoading } = useQuery<ASINDetail[]>({
    queryKey: ['instance-asins-details', mappedASINIds],
    queryFn: async () => {
      if (mappedASINIds.length === 0) return [];

      // Fetch ASINs in batches to get full details
      const asinPromises = mappedASINIds.map(asinId =>
        asinService.getASIN(asinId).catch((): ASINDetail => ({
          id: asinId,
          asin: asinId,
          active: true,
          brand: 'Unknown',
          title: undefined,
          last_known_price: undefined,
          monthly_estimated_units: undefined,
          marketplace: 'US',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }))
      );

      return Promise.all(asinPromises);
    },
    enabled: mappedASINIds.length > 0,
  });

  // Filter ASINs based on search and filters
  const filteredASINs = useMemo(() => {
    if (!asinsData) return [];

    return asinsData.filter((asin) => {
      const matchesSearch =
        asin.asin.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (asin.title && asin.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (asin.brand && asin.brand.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (asin.description && asin.description.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesBrand = !selectedBrand || asin.brand === selectedBrand;
      const matchesProductGroup = !selectedProductGroup || asin.product_group === selectedProductGroup;
      const matchesProductType = !selectedProductType || asin.product_type === selectedProductType;

      return matchesSearch && matchesBrand && matchesProductGroup && matchesProductType;
    });
  }, [asinsData, searchTerm, selectedBrand, selectedProductGroup, selectedProductType]);

  // Get unique values for filters
  const filterOptions = useMemo(() => {
    if (!asinsData) return { brands: [], productGroups: [], productTypes: [] };

    const brands = new Set(asinsData.map(a => a.brand).filter(Boolean));
    const productGroups = new Set(asinsData.map(a => a.product_group).filter(Boolean));
    const productTypes = new Set(asinsData.map(a => a.product_type).filter(Boolean));

    return {
      brands: Array.from(brands).sort(),
      productGroups: Array.from(productGroups).sort(),
      productTypes: Array.from(productTypes).sort()
    };
  }, [asinsData]);

  // Check if any filters are active
  const hasActiveFilters = selectedBrand || selectedProductGroup || selectedProductType;

  // Clear all filters
  const clearFilters = () => {
    setSelectedBrand('');
    setSelectedProductGroup('');
    setSelectedProductType('');
  };

  const isLoading = mappingsLoading || asinsLoading;

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">Loading ASINs...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
              <Package className="h-5 w-5" />
              Mapped ASINs
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              {mappedASINIds.length} ASINs configured for this instance
            </p>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search ASINs, titles, brands, or descriptions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Filter Row */}
        <div className="flex flex-wrap items-center gap-3">
          <Filter className="h-4 w-4 text-gray-400" />

          {/* Brand Filter */}
          <select
            value={selectedBrand}
            onChange={(e) => setSelectedBrand(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          >
            <option value="">All Brands</option>
            {filterOptions.brands.map((brand) => (
              <option key={brand} value={brand}>
                {brand}
              </option>
            ))}
          </select>

          {/* Product Group Filter */}
          <select
            value={selectedProductGroup}
            onChange={(e) => setSelectedProductGroup(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          >
            <option value="">All Product Groups</option>
            {filterOptions.productGroups.map((group) => (
              <option key={group} value={group}>
                {group}
              </option>
            ))}
          </select>

          {/* Product Type Filter */}
          <select
            value={selectedProductType}
            onChange={(e) => setSelectedProductType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          >
            <option value="">All Product Types</option>
            {filterOptions.productTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>

          {/* Clear Filters Button */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="inline-flex items-center px-3 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              <X className="h-4 w-4 mr-1" />
              Clear Filters
            </button>
          )}
        </div>

        {/* Active Filters Display */}
        {hasActiveFilters && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>Active filters:</span>
            {selectedBrand && (
              <span className="inline-flex items-center px-2 py-1 bg-indigo-100 text-indigo-800 rounded-full">
                Brand: {selectedBrand}
              </span>
            )}
            {selectedProductGroup && (
              <span className="inline-flex items-center px-2 py-1 bg-green-100 text-green-800 rounded-full">
                Group: {selectedProductGroup}
              </span>
            )}
            {selectedProductType && (
              <span className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                Type: {selectedProductType}
              </span>
            )}
          </div>
        )}
      </div>

      {/* ASINs Table */}
      {filteredASINs.length === 0 ? (
        <div className="text-center py-12">
          <Package className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No ASINs found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {mappedASINIds.length === 0
              ? 'No ASINs have been mapped to this instance yet. Go to the Mappings tab to configure ASINs.'
              : 'No ASINs match your search criteria.'}
          </p>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="mt-4 inline-flex items-center px-4 py-2 text-sm text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
            >
              Clear All Filters
            </button>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ASIN
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product Title
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Brand
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product Group
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Est. Units/Mo
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredASINs.map((asin) => (
                <tr key={asin.asin} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <a
                      href={`https://www.amazon.com/dp/${asin.asin}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-mono text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      {asin.asin}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900 max-w-xs truncate" title={asin.title}>
                      {asin.title || <span className="text-gray-400 italic">No title</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full">
                      {asin.brand || 'Unknown'}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="text-sm text-gray-900">
                      {asin.product_group || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="text-sm text-gray-900">
                      {asin.product_type || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {asin.last_known_price ? `$${asin.last_known_price.toFixed(2)}` : '-'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {asin.monthly_estimated_units ? asin.monthly_estimated_units.toLocaleString() : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-600 max-w-md truncate" title={asin.description}>
                      {asin.description || '-'}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary */}
      {filteredASINs.length > 0 && (
        <div className="mt-4 text-sm text-gray-500">
          Showing {filteredASINs.length} of {mappedASINIds.length} ASINs
          {hasActiveFilters && ' (filtered)'}
        </div>
      )}
    </div>
  );
}
