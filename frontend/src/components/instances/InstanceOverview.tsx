import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Globe, Calendar, Shield, Settings, Activity, Edit2, Save, X } from 'lucide-react';
import BrandTag from '../common/BrandTag';
import BrandSelector from '../common/BrandSelector';
import api from '../../services/api';

interface InstanceOverviewProps {
  instance: {
    id: string;
    instanceId: string;
    instanceName: string;
    type: string;
    region: string;
    status: string;
    isActive: boolean;
    account: {
      accountId: string;
      accountName: string;
      marketplaceId: string;
    };
    endpointUrl: string;
    dataUploadAccountId: string;
    capabilities: Record<string, any>;
    createdAt: string;
    updatedAt: string;
    brands: string[];
    stats: {
      totalCampaigns: number;
      totalWorkflows: number;
      activeWorkflows: number;
    };
  };
}

export default function InstanceOverview({ instance }: InstanceOverviewProps) {
  const [isEditingBrands, setIsEditingBrands] = useState(false);
  const [selectedBrands, setSelectedBrands] = useState<string[]>(instance.brands);
  const queryClient = useQueryClient();

  // Fetch available brands
  const { data: availableBrands = [] } = useQuery({
    queryKey: ['brands'],
    queryFn: async () => {
      const response = await api.get('/campaigns/brands');
      return response.data.map((item: any) => item.brand_tag);
    },
  });

  // Update brands mutation
  const updateBrandsMutation = useMutation({
    mutationFn: async (brands: string[]) => {
      const response = await api.put(`/instances/${instance.instanceId}/brands`, brands);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instance', instance.instanceId] });
      queryClient.invalidateQueries({ queryKey: ['instances'] });
      setIsEditingBrands(false);
    },
  });

  const handleStartEditingBrands = () => {
    setSelectedBrands(instance.brands);
    setIsEditingBrands(true);
  };

  const handleCancelEditingBrands = () => {
    setSelectedBrands(instance.brands);
    setIsEditingBrands(false);
  };

  const handleSaveBrands = () => {
    updateBrandsMutation.mutate(selectedBrands);
  };

  const handleAddBrand = (brand: string) => {
    if (!selectedBrands.includes(brand)) {
      setSelectedBrands([...selectedBrands, brand]);
    }
  };

  const handleRemoveBrand = (brand: string) => {
    setSelectedBrands(selectedBrands.filter(b => b !== brand));
  };

  return (
    <div className="p-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Workflows</p>
              <p className="text-2xl font-semibold text-gray-900">
                {instance.stats.totalWorkflows}
              </p>
            </div>
            <Settings className="h-8 w-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Workflows</p>
              <p className="text-2xl font-semibold text-gray-900">
                {instance.stats.activeWorkflows}
              </p>
            </div>
            <Activity className="h-8 w-8 text-green-400" />
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Associated Brands</p>
              <p className="text-2xl font-semibold text-gray-900">
                {instance.brands.length}
              </p>
            </div>
            <Shield className="h-8 w-8 text-indigo-400" />
          </div>
        </div>
      </div>

      {/* Instance Details */}
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Instance Information</h3>
          <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Instance ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{instance.instanceId}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Instance Name</dt>
              <dd className="mt-1 text-sm text-gray-900">{instance.instanceName}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Type</dt>
              <dd className="mt-1">
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                  instance.type === 'SANDBOX' 
                    ? 'bg-yellow-100 text-yellow-800' 
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {instance.type}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Region</dt>
              <dd className="mt-1 text-sm text-gray-900 flex items-center">
                <Globe className="h-4 w-4 mr-1 text-gray-400" />
                {instance.region}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1">
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                  instance.isActive
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {instance.isActive ? 'Active' : 'Inactive'}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Created</dt>
              <dd className="mt-1 text-sm text-gray-900 flex items-center">
                <Calendar className="h-4 w-4 mr-1 text-gray-400" />
                {new Date(instance.createdAt).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        </div>

        <div className="border-t pt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Account Information</h3>
          <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Account Name</dt>
              <dd className="mt-1 text-sm text-gray-900">{instance.account.accountName}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Account ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{instance.account.accountId}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Marketplace ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{instance.account.marketplaceId}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Data Upload Account ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{instance.dataUploadAccountId}</dd>
            </div>
          </dl>
        </div>

        <div className="border-t pt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Associated Brands</h3>
            {!isEditingBrands ? (
              <button
                onClick={handleStartEditingBrands}
                className="flex items-center text-sm text-indigo-600 hover:text-indigo-800"
              >
                <Edit2 className="h-4 w-4 mr-1" />
                Edit
              </button>
            ) : (
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleSaveBrands}
                  disabled={updateBrandsMutation.isPending}
                  className="flex items-center px-3 py-1 text-sm text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  <Save className="h-4 w-4 mr-1" />
                  Save
                </button>
                <button
                  onClick={handleCancelEditingBrands}
                  disabled={updateBrandsMutation.isPending}
                  className="flex items-center px-3 py-1 text-sm text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50"
                >
                  <X className="h-4 w-4 mr-1" />
                  Cancel
                </button>
              </div>
            )}
          </div>

          {!isEditingBrands ? (
            <div className="flex flex-wrap gap-2">
              {instance.brands.length > 0 ? (
                instance.brands.map((brand, idx) => (
                  <BrandTag key={idx} brand={brand} />
                ))
              ) : (
                <p className="text-sm text-gray-500">No brands associated</p>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {selectedBrands.map((brand, idx) => (
                  <BrandTag
                    key={idx}
                    brand={brand}
                    isEditable={true}
                    onRemove={handleRemoveBrand}
                  />
                ))}
                {selectedBrands.length === 0 && (
                  <p className="text-sm text-gray-500">No brands selected</p>
                )}
              </div>
              <BrandSelector
                availableBrands={availableBrands}
                selectedBrands={selectedBrands}
                onAddBrand={handleAddBrand}
                placeholder="Search and add brands..."
              />
              {updateBrandsMutation.isError && (
                <p className="text-sm text-red-600">
                  Failed to update brands. Please try again.
                </p>
              )}
            </div>
          )}
        </div>

        {instance.endpointUrl && (
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Technical Details</h3>
            <dl className="space-y-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">API Endpoint</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono break-all">
                  {instance.endpointUrl}
                </dd>
              </div>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}