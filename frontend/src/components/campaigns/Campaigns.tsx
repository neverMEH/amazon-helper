import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Tag, RefreshCw } from 'lucide-react';
import api from '../../services/api';

interface Campaign {
  id: string;
  campaignId: string;
  name: string;
  brandTag?: string;
  campaignType: string;
  asins?: string[];
  createdAt: string;
}

export default function Campaigns() {
  const [brandFilter, setBrandFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  const { data: campaigns, isLoading, refetch } = useQuery<Campaign[]>({
    queryKey: ['campaigns', brandFilter, typeFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (brandFilter) params.append('brand_tag', brandFilter);
      if (typeFilter) params.append('campaign_type', typeFilter);
      
      const response = await api.get(`/campaigns/?${params}`);
      return response.data;
    },
  });

  const handleSync = async () => {
    try {
      await api.post('/campaigns/sync/');
      refetch();
    } catch (error) {
      console.error('Failed to sync campaigns:', error);
    }
  };

  // Get unique brands and types for filters
  const brands = Array.from(new Set(campaigns?.map(c => c.brandTag).filter(Boolean) || []));
  const types = Array.from(new Set(campaigns?.map(c => c.campaignType) || []));

  return (
    <div className="p-6">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage campaign mappings and brand tags
          </p>
        </div>
        <button
          onClick={handleSync}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Sync Campaigns
        </button>
      </div>

      {/* Filters */}
      <div className="mb-6 flex space-x-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Brand</label>
          <select
            value={brandFilter}
            onChange={(e) => setBrandFilter(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="">All Brands</option>
            {brands.map(brand => (
              <option key={brand} value={brand}>{brand}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Type</label>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="">All Types</option>
            {types.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading campaigns...</div>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {campaigns?.map((campaign) => (
              <li key={campaign.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Tag className="h-8 w-8 text-gray-400 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {campaign.name}
                        </p>
                        <p className="text-sm text-gray-500">
                          ID: {campaign.campaignId}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      {campaign.brandTag && (
                        <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full">
                          {campaign.brandTag}
                        </span>
                      )}
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        campaign.campaignType === 'DSP' ? 'bg-blue-100 text-blue-800' :
                        campaign.campaignType === 'SP' ? 'bg-green-100 text-green-800' :
                        campaign.campaignType === 'SD' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {campaign.campaignType}
                      </span>
                      {campaign.asins && campaign.asins.length > 0 && (
                        <span className="text-xs text-gray-500">
                          {campaign.asins.length} ASINs
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}