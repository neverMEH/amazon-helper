import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, Package } from 'lucide-react';
import instanceMappingService from '../../services/instanceMappingService';

interface ASIN {
  asin: string;
  title?: string;
  brand?: string;
  image_url?: string;
  last_known_price?: number;
  active: boolean;
}

interface InstanceASINsProps {
  instanceId: string;
}

export default function InstanceASINs({ instanceId }: InstanceASINsProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBrand, setSelectedBrand] = useState<string>('');

  // Fetch instance mappings to get all ASINs
  const { data: mappings, isLoading: mappingsLoading } = useQuery({
    queryKey: ['instanceMappings', instanceId],
    queryFn: () => instanceMappingService.getInstanceMappings(instanceId),
  });

  // Get all ASINs from mappings grouped by brand
  const allASINs: Array<ASIN & { brand: string }> = [];
  if (mappings?.asins_by_brand) {
    Object.entries(mappings.asins_by_brand).forEach(([brand, asins]) => {
      asins.forEach((asin) => {
        allASINs.push({
          asin,
          brand,
          active: true,
        });
      });
    });
  }

  // Filter ASINs based on search and brand
  const filteredASINs = allASINs.filter((asin) => {
    const matchesSearch =
      asin.asin.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (asin.title && asin.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
      asin.brand.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesBrand = !selectedBrand || asin.brand === selectedBrand;

    return matchesSearch && matchesBrand;
  });

  // Get unique brands from mappings
  const uniqueBrands = mappings?.brands || [];

  if (mappingsLoading) {
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
        <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
          <Package className="h-5 w-5" />
          Mapped ASINs
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          ASINs configured for this instance ({allASINs.length} total)
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search ASINs..."
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

      {/* ASINs Table */}
      {filteredASINs.length === 0 ? (
        <div className="text-center py-12">
          <Package className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No ASINs found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {allASINs.length === 0
              ? 'No ASINs have been mapped to this instance yet. Go to the Mappings tab to configure ASINs.'
              : 'No ASINs match your search criteria.'}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ASIN
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Brand
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Title
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredASINs.map((asin, idx) => (
                <tr key={`${asin.asin}-${idx}`} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm font-medium text-gray-900">
                        {asin.asin}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full">
                      {asin.brand}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">
                      {asin.title || <span className="text-gray-400 italic">No title available</span>}
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
          Showing {filteredASINs.length} of {allASINs.length} ASINs
        </div>
      )}
    </div>
  );
}
