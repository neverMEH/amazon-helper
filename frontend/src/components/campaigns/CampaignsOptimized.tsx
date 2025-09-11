import { useState, useEffect, type ReactElement } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Search, 
  ChevronLeft, 
  ChevronRight,
  ArrowUpDown,
  Archive,
  PauseCircle,
  PlayCircle,
  Filter,
  ChevronUp,
  ChevronDown
} from 'lucide-react';
import api from '../../services/api';

interface Campaign {
  id: string;
  campaignId: string;
  name: string;
  brand: string;
  state: string;
  type: string;
  targetingType: string;
  biddingStrategy: string;
  portfolioId: string;
  createdAt: string;
  updatedAt: string;
}

interface CampaignsResponse {
  campaigns: Campaign[];
  pagination: {
    page: number;
    pageSize: number;
    totalCount: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

interface BrandInfo {
  brand: string;
  campaign_count: number;
  enabled_count?: number;
  paused_count?: number;
  archived_count?: number;
}

interface SortConfig {
  field: string;
  order: 'asc' | 'desc';
}

const stateIcons: Record<string, ReactElement> = {
  ENABLED: <PlayCircle className="h-4 w-4 text-green-500" />,
  PAUSED: <PauseCircle className="h-4 w-4 text-yellow-500" />,
  ARCHIVED: <Archive className="h-4 w-4 text-gray-400" />,
};

const stateColors: Record<string, string> = {
  ENABLED: 'bg-green-100 text-green-800',
  PAUSED: 'bg-yellow-100 text-yellow-800',
  ARCHIVED: 'bg-gray-100 text-gray-800',
};

// Skeleton loader component
const CampaignSkeleton = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4">
      <div className="h-4 bg-gray-200 rounded w-48"></div>
    </td>
    <td className="px-6 py-4">
      <div className="h-4 bg-gray-200 rounded w-20"></div>
    </td>
    <td className="px-6 py-4">
      <div className="h-4 bg-gray-200 rounded w-20"></div>
    </td>
    <td className="px-6 py-4">
      <div className="h-4 bg-gray-200 rounded w-16"></div>
    </td>
    <td className="px-6 py-4">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4">
      <div className="h-4 bg-gray-200 rounded w-32"></div>
    </td>
  </tr>
);

// Stats skeleton component
const StatsSkeleton = () => (
  <div className="mt-4 grid grid-cols-4 gap-4">
    {[1, 2, 3, 4].map((i) => (
      <div key={i} className="bg-white p-4 rounded-lg shadow animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
        <div className="h-8 bg-gray-200 rounded w-16"></div>
      </div>
    ))}
  </div>
);

// Filter storage key
const FILTER_STORAGE_KEY = 'campaign-filters-v1';

export default function CampaignsOptimized() {
  // Load saved filters from localStorage
  const loadSavedFilters = () => {
    try {
      const saved = localStorage.getItem(FILTER_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        return {
          search: parsed.search || '',
          brandFilter: parsed.brandFilter || '',
          stateFilter: parsed.stateFilter || 'ENABLED',
          typeFilter: parsed.typeFilter || '',
        };
      }
    } catch (e) {
      console.error('Failed to load saved filters:', e);
    }
    return {
      search: '',
      brandFilter: '',
      stateFilter: 'ENABLED',
      typeFilter: '',
    };
  };

  const savedFilters = loadSavedFilters();
  
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [search, setSearch] = useState(savedFilters.search);
  const [brandFilter, setBrandFilter] = useState(savedFilters.brandFilter);
  const [stateFilter, setStateFilter] = useState(savedFilters.stateFilter);
  const [typeFilter, setTypeFilter] = useState(savedFilters.typeFilter);
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'name',
    order: 'asc'
  });

  // Save filters to localStorage whenever they change
  useEffect(() => {
    const filters = { search, brandFilter, stateFilter, typeFilter };
    localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(filters));
  }, [search, brandFilter, stateFilter, typeFilter]);

  // Fetch campaigns with filters
  const { data, isLoading, isFetching } = useQuery<CampaignsResponse>({
    queryKey: ['campaigns', page, pageSize, search, brandFilter, stateFilter, typeFilter, sortConfig],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());
      if (search) params.append('search', search);
      if (brandFilter) params.append('brand', brandFilter);
      
      if (stateFilter === '') {
        params.append('show_all_states', 'true');
      } else if (stateFilter) {
        params.append('state', stateFilter);
      }
      
      if (typeFilter) params.append('type', typeFilter);
      params.append('sort_by', sortConfig.field);
      params.append('sort_order', sortConfig.order);
      
      const response = await api.get(`/campaigns/?${params}`);
      return response.data;
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: false,
  });

  // Fetch brands with aggressive caching - won't change often
  const { data: brands, isLoading: brandsLoading } = useQuery<BrandInfo[]>({
    queryKey: ['campaign-brands-optimized'],
    queryFn: async () => {
      const response = await api.get('/campaigns/brands');
      return response.data;
    },
    staleTime: 5 * 60 * 1000,    // 5 minutes
    gcTime: 30 * 60 * 1000,      // 30 minutes cache
    refetchOnWindowFocus: false,  // Don't refetch on focus
  });

  // Fetch stats with caching
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['campaign-stats-optimized'],
    queryFn: async () => {
      const response = await api.get('/campaigns/stats');
      return response.data;
    },
    staleTime: 60 * 1000,         // 1 minute
    refetchOnWindowFocus: false,
  });

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [search, brandFilter, stateFilter, typeFilter]);

  const handleSort = (field: string) => {
    setSortConfig(prev => {
      if (prev.field === field) {
        return { field, order: prev.order === 'asc' ? 'desc' : 'asc' };
      }
      return { field, order: 'asc' };
    });
  };

  const getSortIcon = (field: string) => {
    if (sortConfig.field !== field) {
      return <ArrowUpDown className="ml-1 h-3 w-3 text-gray-400" />;
    }
    return sortConfig.order === 'asc' 
      ? <ChevronUp className="ml-1 h-3 w-3 text-indigo-600" />
      : <ChevronDown className="ml-1 h-3 w-3 text-indigo-600" />;
  };

  const formatCampaignId = (id: string) => {
    if (id.length > 10) {
      return `${id.slice(0, 6)}...${id.slice(-4)}`;
    }
    return id;
  };

  const clearFilters = () => {
    setSearch('');
    setBrandFilter('');
    setStateFilter('ENABLED');
    setTypeFilter('');
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
        <p className="mt-1 text-sm text-gray-600">
          Manage and analyze your Amazon advertising campaigns
          {stateFilter === 'ENABLED' && (
            <span className="ml-2 text-green-600 font-medium">
              (Showing active campaigns only)
            </span>
          )}
          {isFetching && !isLoading && (
            <span className="ml-2 text-blue-600">
              Refreshing...
            </span>
          )}
        </p>
        
        {/* Stats */}
        {statsLoading ? (
          <StatsSkeleton />
        ) : stats ? (
          <div className="mt-4 grid grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm font-medium text-gray-500">Total Campaigns</div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">
                {stats.total_campaigns?.toLocaleString() || 0}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm font-medium text-gray-500">Active</div>
              <div className="mt-1 text-2xl font-semibold text-green-600">
                {stats.by_state?.ENABLED || 0}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm font-medium text-gray-500">Paused</div>
              <div className="mt-1 text-2xl font-semibold text-yellow-600">
                {stats.by_state?.PAUSED || 0}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm font-medium text-gray-500">Archived</div>
              <div className="mt-1 text-2xl font-semibold text-gray-600">
                {stats.by_state?.ARCHIVED || 0}
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Filters */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Filter className="h-5 w-5 text-gray-500 mr-2" />
            <span className="font-medium text-gray-700">Filters</span>
          </div>
          {(search || brandFilter || stateFilter !== 'ENABLED' || typeFilter) && (
            <button
              onClick={clearFilters}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              Clear filters
            </button>
          )}
        </div>
        
        <div className="grid grid-cols-5 gap-4">
          {/* Search */}
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Campaigns
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name..."
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Brand Filter with loading state */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Brand
            </label>
            <select
              value={brandFilter}
              onChange={(e) => setBrandFilter(e.target.value)}
              disabled={brandsLoading}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50 disabled:bg-gray-100"
            >
              <option value="">
                {brandsLoading ? 'Loading brands...' : 'All Brands'}
              </option>
              {brands?.map(brand => (
                <option key={brand.brand} value={brand.brand}>
                  {brand.brand} ({brand.campaign_count})
                </option>
              ))}
            </select>
          </div>

          {/* State Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              State
            </label>
            <select
              value={stateFilter}
              onChange={(e) => setStateFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="ENABLED">Enabled (Active)</option>
              <option value="">All States</option>
              <option value="PAUSED">Paused</option>
              <option value="ARCHIVED">Archived</option>
            </select>
          </div>

          {/* Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type
            </label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Types</option>
              <option value="sp">Sponsored Products</option>
              <option value="sb">Sponsored Brands</option>
              <option value="sd">Sponsored Display</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white shadow overflow-hidden rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th 
                onClick={() => handleSort('campaign_id')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
              >
                <div className="flex items-center">
                  Campaign ID
                  {getSortIcon('campaign_id')}
                </div>
              </th>
              <th 
                onClick={() => handleSort('name')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
              >
                <div className="flex items-center">
                  Name
                  {getSortIcon('name')}
                </div>
              </th>
              <th 
                onClick={() => handleSort('brand')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
              >
                <div className="flex items-center">
                  Brand
                  {getSortIcon('brand')}
                </div>
              </th>
              <th 
                onClick={() => handleSort('state')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
              >
                <div className="flex items-center">
                  State
                  {getSortIcon('state')}
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Targeting
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Strategy
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              // Show skeleton loaders while loading
              Array.from({ length: 10 }).map((_, i) => (
                <CampaignSkeleton key={i} />
              ))
            ) : data?.campaigns.length === 0 ? (
              // No campaigns found
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                  <div className="flex flex-col items-center">
                    <Archive className="h-12 w-12 text-gray-400 mb-3" />
                    <p className="text-lg font-medium">No campaigns found</p>
                    <p className="text-sm mt-1">Try adjusting your filters or search criteria</p>
                  </div>
                </td>
              </tr>
            ) : (
              // Display campaigns
              data?.campaigns.map((campaign) => (
                <tr key={campaign.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                    {formatCampaignId(campaign.campaignId)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="max-w-xs truncate" title={campaign.name}>
                      {campaign.name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full">
                      {campaign.brand}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="flex items-center">
                      {stateIcons[campaign.state]}
                      <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${stateColors[campaign.state] || 'bg-gray-100 text-gray-800'}`}>
                        {campaign.state}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {campaign.type ? (
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                        {campaign.type.toUpperCase()}
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {campaign.targetingType || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {campaign.biddingStrategy?.replace(/_/g, ' ') || '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {data?.pagination && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setPage(page - 1)}
                disabled={!data.pagination.hasPrev}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={!data.pagination.hasNext}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing{' '}
                  <span className="font-medium">
                    {(page - 1) * pageSize + 1}
                  </span>{' '}
                  to{' '}
                  <span className="font-medium">
                    {Math.min(page * pageSize, data.pagination.totalCount)}
                  </span>{' '}
                  of{' '}
                  <span className="font-medium">
                    {data.pagination.totalCount}
                  </span>{' '}
                  campaigns
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={!data.pagination.hasPrev}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                
                <div className="flex space-x-1">
                  {Array.from({ length: Math.min(5, data.pagination.totalPages) }, (_, i) => {
                    let pageNum;
                    if (data.pagination.totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (page <= 3) {
                      pageNum = i + 1;
                    } else if (page >= data.pagination.totalPages - 2) {
                      pageNum = data.pagination.totalPages - 4 + i;
                    } else {
                      pageNum = page - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          pageNum === page
                            ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  onClick={() => setPage(page + 1)}
                  disabled={!data.pagination.hasNext}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>

                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                  className="ml-4 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value={25}>25 per page</option>
                  <option value={50}>50 per page</option>
                  <option value={100}>100 per page</option>
                  <option value={250}>250 per page</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}