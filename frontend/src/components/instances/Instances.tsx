import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Database, CheckCircle, XCircle, ChevronRight, RefreshCw, Search, Filter, X, ChevronDown } from 'lucide-react';
import { useState, useMemo, useCallback } from 'react';
import api from '../../services/api';

interface AMCInstance {
  id: string;
  instanceId: string;
  instanceName: string;
  region: string;
  accountId: string;
  accountName: string;
  isActive: boolean;
  type: string;
  createdAt: string;
  brands: string[];
  stats: {
    totalCampaigns: number;
    totalWorkflows: number;
    activeWorkflows: number;
  };
}

export default function Instances() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [syncStatus, setSyncStatus] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  
  // Filter states
  const [selectedAccount, setSelectedAccount] = useState<string>('all');
  const [selectedRegion, setSelectedRegion] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedBrand, setSelectedBrand] = useState<string>('all');
  
  const { data: instances, isLoading, isFetching } = useQuery<AMCInstance[]>({
    queryKey: ['instances'],
    queryFn: async () => {
      const response = await api.get('/instances', {
        params: {
          limit: 100,  // Load up to 100 instances
          offset: 0
        }
      });
      return response.data;
    },
    staleTime: 5 * 60 * 1000,  // Consider data stale after 5 minutes
    gcTime: 10 * 60 * 1000,    // Keep in cache for 10 minutes
  });

  const syncMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/instances/sync');
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate and refetch instances
      queryClient.invalidateQueries({ queryKey: ['instances'] });
      setSyncStatus(`Synced ${data.instances_synced} instances from ${data.accounts_synced} accounts`);
      setTimeout(() => setSyncStatus(null), 5000);
    },
    onError: (error: any) => {
      setSyncStatus(error.response?.data?.detail || 'Failed to sync instances');
      setTimeout(() => setSyncStatus(null), 5000);
    }
  });

  // Extract unique values for filters
  const filterOptions = useMemo(() => {
    if (!instances) return { accounts: [], regions: [], types: [], brands: [] };
    
    const accounts = [...new Set(instances.map(i => i.accountName))].sort();
    const regions = [...new Set(instances.map(i => i.region))].sort();
    const types = [...new Set(instances.map(i => i.type))].sort();
    const brands = [...new Set(instances.flatMap(i => i.brands))].sort();
    
    return { accounts, regions, types, brands };
  }, [instances]);

  // Filter instances based on search and filters
  const filteredInstances = useMemo(() => {
    if (!instances) return [];
    
    return instances.filter(instance => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesSearch = 
          instance.instanceName.toLowerCase().includes(query) ||
          instance.instanceId.toLowerCase().includes(query) ||
          instance.accountName.toLowerCase().includes(query) ||
          instance.accountId.toLowerCase().includes(query) ||
          instance.region.toLowerCase().includes(query) ||
          instance.brands.some(brand => brand.toLowerCase().includes(query));
        
        if (!matchesSearch) return false;
      }
      
      // Account filter
      if (selectedAccount !== 'all' && instance.accountName !== selectedAccount) {
        return false;
      }
      
      // Region filter
      if (selectedRegion !== 'all' && instance.region !== selectedRegion) {
        return false;
      }
      
      // Type filter
      if (selectedType !== 'all' && instance.type !== selectedType) {
        return false;
      }
      
      // Status filter
      if (selectedStatus !== 'all') {
        if (selectedStatus === 'active' && !instance.isActive) return false;
        if (selectedStatus === 'inactive' && instance.isActive) return false;
      }
      
      // Brand filter
      if (selectedBrand !== 'all' && !instance.brands.includes(selectedBrand)) {
        return false;
      }
      
      return true;
    });
  }, [instances, searchQuery, selectedAccount, selectedRegion, selectedType, selectedStatus, selectedBrand]);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (selectedAccount !== 'all') count++;
    if (selectedRegion !== 'all') count++;
    if (selectedType !== 'all') count++;
    if (selectedStatus !== 'all') count++;
    if (selectedBrand !== 'all') count++;
    return count;
  }, [selectedAccount, selectedRegion, selectedType, selectedStatus, selectedBrand]);

  const clearFilters = () => {
    setSelectedAccount('all');
    setSelectedRegion('all');
    setSelectedType('all');
    setSelectedStatus('all');
    setSelectedBrand('all');
    setSearchQuery('');
  };

  // Prefetch instance details on hover for faster navigation
  const handleInstanceHover = useCallback((instanceId: string) => {
    queryClient.prefetchQuery({
      queryKey: ['instance', instanceId],
      queryFn: async () => {
        const response = await api.get(`/instances/${instanceId}`);
        return response.data;
      },
      staleTime: 60000, // Cache for 1 minute
    });
  }, [queryClient]);

  return (
    <div className="p-6">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AMC Instances</h1>
            <p className="mt-1 text-sm text-gray-600">
              Manage your Amazon Marketing Cloud instances
            </p>
          </div>
          <div className="flex items-center gap-4">
            {(isFetching && !isLoading) || syncMutation.isPending ? (
              <div className="text-sm text-gray-500">
                {syncMutation.isPending ? 'Syncing with Amazon...' : 'Refreshing...'}
              </div>
            ) : null}
            {syncStatus && (
              <div className={`text-sm ${syncStatus.includes('Failed') ? 'text-red-600' : 'text-green-600'}`}>
                {syncStatus}
              </div>
            )}
            <button
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
              Sync from Amazon
            </button>
          </div>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="mb-6 space-y-4">
        <div className="flex gap-4">
          {/* Search Input */}
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Search by name, ID, account, region, or brand..."
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              </button>
            )}
          </div>
          
          {/* Filter Toggle Button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`inline-flex items-center px-4 py-2 border text-sm font-medium rounded-md ${
              activeFilterCount > 0 
                ? 'border-indigo-500 text-indigo-700 bg-indigo-50'
                : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
            }`}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
            {activeFilterCount > 0 && (
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-600 text-white">
                {activeFilterCount}
              </span>
            )}
            <ChevronDown className={`ml-2 h-4 w-4 transform transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Filter Options */}
        {showFilters && (
          <div className="bg-gray-50 rounded-lg p-4 space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {/* Account Filter */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Account</label>
                <select
                  value={selectedAccount}
                  onChange={(e) => setSelectedAccount(e.target.value)}
                  className="block w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Accounts</option>
                  {filterOptions.accounts.map(account => (
                    <option key={account} value={account}>{account}</option>
                  ))}
                </select>
              </div>

              {/* Region Filter */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Region</label>
                <select
                  value={selectedRegion}
                  onChange={(e) => setSelectedRegion(e.target.value)}
                  className="block w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Regions</option>
                  {filterOptions.regions.map(region => (
                    <option key={region} value={region}>{region}</option>
                  ))}
                </select>
              </div>

              {/* Type Filter */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="block w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Types</option>
                  {filterOptions.types.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="block w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              {/* Brand Filter */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Brand</label>
                <select
                  value={selectedBrand}
                  onChange={(e) => setSelectedBrand(e.target.value)}
                  className="block w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Brands</option>
                  {filterOptions.brands.map(brand => (
                    <option key={brand} value={brand}>{brand}</option>
                  ))}
                </select>
              </div>

              {/* Clear Filters Button */}
              <div className="flex items-end">
                <button
                  onClick={clearFilters}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white text-gray-700 hover:bg-gray-50"
                >
                  Clear All
                </button>
              </div>
            </div>

            {/* Results Count */}
            <div className="text-sm text-gray-600">
              Showing {filteredInstances.length} of {instances?.length || 0} instances
            </div>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading instances...</div>
        </div>
      ) : filteredInstances.length === 0 ? (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg p-12">
          <div className="text-center">
            <Database className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              {searchQuery || activeFilterCount > 0 ? 'No instances match your search' : 'No AMC instances found'}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchQuery || activeFilterCount > 0 
                ? 'Try adjusting your search or filters'
                : 'Click "Sync from Amazon" to fetch your AMC instances.'}
            </p>
            <div className="mt-6">
              {searchQuery || activeFilterCount > 0 ? (
                <button
                  onClick={clearFilters}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Clear Search & Filters
                </button>
              ) : (
                <button
                  onClick={() => syncMutation.mutate()}
                  disabled={syncMutation.isPending}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                  Sync from Amazon
                </button>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Instance Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Instance ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Account
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Brands
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Queries
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">View</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredInstances.map((instance) => (
                <tr
                  key={instance.id}
                  onClick={() => navigate(`/instances/${instance.instanceId}`)}
                  onMouseEnter={() => handleInstanceHover(instance.instanceId)}
                  className="hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Database className="h-8 w-8 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {instance.instanceName}
                        </div>
                        <div className="text-sm text-gray-500">
                          {instance.region}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{instance.instanceId}</div>
                    <div className="text-sm text-gray-500">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        instance.type === 'SANDBOX' 
                          ? 'bg-yellow-100 text-yellow-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {instance.type}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{instance.accountName}</div>
                    <div className="text-sm text-gray-500">{instance.accountId}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {instance.brands.length > 0 ? (
                        instance.brands.map((brand, idx) => (
                          <span
                            key={idx}
                            className="inline-flex px-2 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full"
                          >
                            {brand}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-gray-500">No brands</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {instance.stats.activeWorkflows} active
                    </div>
                    <div className="text-sm text-gray-500">
                      {instance.stats.totalWorkflows} total
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    {instance.isActive ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <XCircle className="h-4 w-4 mr-1" />
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}