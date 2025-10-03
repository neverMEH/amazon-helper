import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, Package, Grid, List, ExternalLink } from 'lucide-react';
import instanceMappingService from '../../services/instanceMappingService';
import asinService, { type ASIN } from '../../services/asinService';

interface InstanceASINsProps {
  instanceId: string;
}

export default function InstanceASINs({ instanceId }: InstanceASINsProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBrand, setSelectedBrand] = useState<string>('');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

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
  const { data: asinsData, isLoading: asinsLoading } = useQuery({
    queryKey: ['instance-asins-details', mappedASINIds],
    queryFn: async () => {
      if (mappedASINIds.length === 0) return [];

      // Fetch ASINs in batches to get full details
      const asinPromises = mappedASINIds.map(asinId =>
        asinService.getASIN(asinId).catch(() => ({
          asin: asinId,
          active: true,
          brand: 'Unknown'
        }))
      );

      return Promise.all(asinPromises);
    },
    enabled: mappedASINIds.length > 0,
  });

  // Filter ASINs based on search and brand
  const filteredASINs = useMemo(() => {
    if (!asinsData) return [];

    return asinsData.filter((asin) => {
      const matchesSearch =
        asin.asin.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (asin.title && asin.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (asin.brand && asin.brand.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesBrand = !selectedBrand || asin.brand === selectedBrand;

      return matchesSearch && matchesBrand;
    });
  }, [asinsData, searchTerm, selectedBrand]);

  // Get unique brands from ASINs
  const uniqueBrands = useMemo(() => {
    if (!asinsData) return [];
    const brands = new Set(asinsData.map(a => a.brand).filter(Boolean));
    return Array.from(brands).sort();
  }, [asinsData]);

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

          {/* View Toggle */}
          <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-white shadow' : 'text-gray-600'}`}
              title="Grid view"
            >
              <Grid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-2 rounded ${viewMode === 'table' ? 'bg-white shadow' : 'text-gray-600'}`}
              title="Table view"
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search ASINs, titles, or brands..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <select
            value={selectedBrand}
            onChange={(e) => setSelectedBrand(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Brands</option>
            {uniqueBrands.map((brand) => (
              <option key={brand} value={brand}>
                {brand}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* ASINs Content */}
      {filteredASINs.length === 0 ? (
        <div className="text-center py-12">
          <Package className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No ASINs found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {mappedASINIds.length === 0
              ? 'No ASINs have been mapped to this instance yet. Go to the Mappings tab to configure ASINs.'
              : 'No ASINs match your search criteria.'}
          </p>
        </div>
      ) : viewMode === 'grid' ? (
        /* Grid View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredASINs.map((asin) => (
            <div
              key={asin.asin}
              className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
            >
              {/* Image */}
              <div className="aspect-square bg-gray-100 flex items-center justify-center">
                {asin.image_url ? (
                  <img
                    src={asin.image_url}
                    alt={asin.title || asin.asin}
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <Package className="h-16 w-16 text-gray-400" />
                )}
              </div>

              {/* Content */}
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <a
                    href={`https://www.amazon.com/dp/${asin.asin}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-mono text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    {asin.asin}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>

                <h4 className="text-sm font-medium text-gray-900 line-clamp-2 min-h-[40px] mb-2">
                  {asin.title || <span className="text-gray-400 italic">No title</span>}
                </h4>

                <div className="flex items-center justify-between text-sm">
                  <span className="inline-flex px-2 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full">
                    {asin.brand || 'Unknown'}
                  </span>
                  {asin.last_known_price && (
                    <span className="font-semibold text-gray-900">
                      ${asin.last_known_price.toFixed(2)}
                    </span>
                  )}
                </div>

                {asin.monthly_estimated_units && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-500">
                      Est. {asin.monthly_estimated_units.toLocaleString()} units/mo
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Table View */
        <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ASIN
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Product Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Brand
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Est. Units/Month
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredASINs.map((asin) => (
                <tr key={asin.asin} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
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
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 max-w-md truncate" title={asin.title}>
                      {asin.title || <span className="text-gray-400 italic">No title</span>}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full">
                      {asin.brand || 'Unknown'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {asin.last_known_price ? `$${asin.last_known_price.toFixed(2)}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {asin.monthly_estimated_units ? asin.monthly_estimated_units.toLocaleString() : '-'}
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
          Showing {filteredASINs.length} of {mappedASINs.length} ASINs
        </div>
      )}
    </div>
  );
}
