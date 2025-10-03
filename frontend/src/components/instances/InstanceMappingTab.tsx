import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, Loader2, CheckCircle, XCircle, Settings, Search } from 'lucide-react';
import instanceMappingService from '../../services/instanceMappingService';

interface InstanceMappingTabProps {
  instanceId: string;
}

export default function InstanceMappingTab({ instanceId }: InstanceMappingTabProps) {
  const queryClient = useQueryClient();
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);
  const [selectedASINs, setSelectedASINs] = useState<Record<string, Set<string>>>({});
  const [selectedCampaigns, setSelectedCampaigns] = useState<Record<string, Set<string | number>>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [brandSearch, setBrandSearch] = useState('');

  // Fetch available brands
  const { data: brandsData, isLoading: brandsLoading } = useQuery({
    queryKey: ['availableBrands', instanceId],
    queryFn: () => instanceMappingService.getAvailableBrands(instanceId),
  });

  // Fetch current mappings
  const { data: mappings, isLoading: mappingsLoading } = useQuery({
    queryKey: ['instanceMappings', instanceId],
    queryFn: () => instanceMappingService.getInstanceMappings(instanceId),
  });

  // Fetch ASINs for selected brand
  const { data: asinsData, isLoading: asinsLoading } = useQuery({
    queryKey: ['brandASINs', instanceId, selectedBrand],
    queryFn: () => instanceMappingService.getBrandASINs(instanceId, selectedBrand!, { limit: 1000 }),
    enabled: !!selectedBrand,
  });

  // Fetch campaigns for selected brand
  const { data: campaignsData, isLoading: campaignsLoading } = useQuery({
    queryKey: ['brandCampaigns', instanceId, selectedBrand],
    queryFn: () => instanceMappingService.getBrandCampaigns(instanceId, selectedBrand!, { limit: 2000 }),
    enabled: !!selectedBrand,
  });

  // Initialize selections from mappings
  useEffect(() => {
    if (mappings) {
      const asinSelections: Record<string, Set<string>> = {};
      const campaignSelections: Record<string, Set<string | number>> = {};

      Object.entries(mappings.asins_by_brand).forEach(([brand, asins]) => {
        asinSelections[brand] = new Set(asins);
      });

      Object.entries(mappings.campaigns_by_brand).forEach(([brand, campaigns]) => {
        campaignSelections[brand] = new Set(campaigns);
      });

      setSelectedASINs(asinSelections);
      setSelectedCampaigns(campaignSelections);
    }
  }, [mappings]);

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: () => {
      const asinsByBrand: Record<string, string[]> = {};
      const campaignsByBrand: Record<string, (string | number)[]> = {};

      // Build the brands list from actual selections
      const brandsSet = new Set<string>();

      // Add brands that have ASINs selected
      Object.entries(selectedASINs).forEach(([brand, asins]) => {
        if (asins.size > 0) {
          brandsSet.add(brand);
          asinsByBrand[brand] = Array.from(asins);
        }
      });

      // Add brands that have campaigns selected
      Object.entries(selectedCampaigns).forEach(([brand, campaigns]) => {
        if (campaigns.size > 0) {
          brandsSet.add(brand);
          campaignsByBrand[brand] = Array.from(campaigns);
        }
      });

      const selectedBrandsList = Array.from(brandsSet);

      const payload = {
        brands: selectedBrandsList,
        asins_by_brand: asinsByBrand,
        campaigns_by_brand: campaignsByBrand,
      };

      console.log('Saving instance mappings:', payload);

      return instanceMappingService.saveInstanceMappings(instanceId, payload);
    },
    onSuccess: (data) => {
      setSaveMessage({ type: 'success', text: data.message });
      queryClient.invalidateQueries({ queryKey: ['instanceMappings', instanceId] });
      setTimeout(() => setSaveMessage(null), 3000);
    },
    onError: (error: any) => {
      console.error('Save mapping error:', error);
      let errorMessage = 'Failed to save mappings';

      if (error.response?.data?.detail) {
        // API returned a detailed error message
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          // Validation errors from Pydantic
          errorMessage = error.response.data.detail.map((e: any) =>
            `${e.loc?.join('.')}: ${e.msg}`
          ).join(', ');
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      setSaveMessage({
        type: 'error',
        text: errorMessage
      });
      setTimeout(() => setSaveMessage(null), 8000);
    },
  });

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await saveMutation.mutateAsync();
    } finally {
      setIsSaving(false);
    }
  };

  const toggleASIN = (brand: string, asin: string) => {
    setSelectedASINs(prev => {
      const newSelections = { ...prev };
      if (!newSelections[brand]) {
        newSelections[brand] = new Set();
      }
      const brandSet = new Set(newSelections[brand]);

      if (brandSet.has(asin)) {
        brandSet.delete(asin);
      } else {
        brandSet.add(asin);
      }

      newSelections[brand] = brandSet;
      return newSelections;
    });
  };

  const toggleCampaign = (brand: string, campaignId: string | number) => {
    setSelectedCampaigns(prev => {
      const newSelections = { ...prev };
      if (!newSelections[brand]) {
        newSelections[brand] = new Set();
      }
      const brandSet = new Set(newSelections[brand]);

      if (brandSet.has(campaignId)) {
        brandSet.delete(campaignId);
      } else {
        brandSet.add(campaignId);
      }

      newSelections[brand] = brandSet;
      return newSelections;
    });
  };

  const selectAllASINs = (brand: string) => {
    if (!asinsData) return;
    setSelectedASINs(prev => ({
      ...prev,
      [brand]: new Set(asinsData.asins.map(a => a.asin)),
    }));
  };

  const deselectAllASINs = (brand: string) => {
    setSelectedASINs(prev => ({
      ...prev,
      [brand]: new Set(),
    }));
  };

  const selectAllCampaigns = (brand: string) => {
    if (!campaignsData) return;
    setSelectedCampaigns(prev => ({
      ...prev,
      [brand]: new Set(campaignsData.campaigns.map(c => c.campaign_id)),
    }));
  };

  const deselectAllCampaigns = (brand: string) => {
    setSelectedCampaigns(prev => ({
      ...prev,
      [brand]: new Set(),
    }));
  };

  if (brandsLoading || mappingsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading mappings...</span>
      </div>
    );
  }

  const brands = brandsData?.brands || [];

  // Filter brands based on search
  const filteredBrands = brands.filter(brand =>
    brand.brand_name.toLowerCase().includes(brandSearch.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Parameter Mappings</h2>
          <p className="text-sm text-gray-600">
            Configure brand, ASIN, and campaign associations for this instance
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </>
          )}
        </button>
      </div>

      {/* Save notification */}
      {saveMessage && (
        <div className={`flex items-center p-3 rounded-md ${
          saveMessage.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        }`}>
          {saveMessage.type === 'success' ? (
            <CheckCircle className="h-5 w-5 mr-2" />
          ) : (
            <XCircle className="h-5 w-5 mr-2" />
          )}
          {saveMessage.text}
        </div>
      )}

      {/* Three-column layout */}
      <div className="grid grid-cols-3 gap-4 h-[600px]">
        {/* Column 1: Brand Selection */}
        <div className="border border-gray-200 rounded-lg overflow-hidden flex flex-col">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <h3 className="font-medium text-gray-900">Brands</h3>
            <p className="text-xs text-gray-500 mt-1">
              {brands.length} total brands
            </p>
          </div>
          {/* Search bar */}
          <div className="px-3 py-2 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search brands..."
                value={brandSearch}
                onChange={(e) => setBrandSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {brands.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-sm">
                No brands available
              </div>
            ) : filteredBrands.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-sm">
                No brands match "{brandSearch}"
              </div>
            ) : (
              <div className="space-y-1">
                {filteredBrands.map((brand) => (
                  <button
                    key={brand.brand_tag}
                    onClick={() => setSelectedBrand(brand.brand_tag)}
                    className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                      selectedBrand === brand.brand_tag
                        ? 'bg-blue-50 text-blue-900 border border-blue-200'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="font-medium text-sm">{brand.brand_name}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {brand.asin_count || 0} ASINs • {brand.campaign_count || 0} Campaigns
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Column 2: ASIN Manager */}
        <div className="border border-gray-200 rounded-lg overflow-hidden flex flex-col">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <h3 className="font-medium text-gray-900">ASINs</h3>
            {selectedBrand && (
              <div className="flex items-center justify-between mt-2">
                <p className="text-xs text-gray-500">
                  {selectedASINs[selectedBrand]?.size || 0} selected
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => selectAllASINs(selectedBrand)}
                    className="text-xs text-blue-600 hover:text-blue-700"
                  >
                    Select All
                  </button>
                  <button
                    onClick={() => deselectAllASINs(selectedBrand)}
                    className="text-xs text-gray-600 hover:text-gray-700"
                  >
                    Clear
                  </button>
                </div>
              </div>
            )}
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {!selectedBrand ? (
              <div className="text-center py-8 text-gray-500 text-sm">
                <Settings className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                Select a brand to view ASINs
              </div>
            ) : asinsLoading ? (
              <div className="text-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mx-auto text-gray-400" />
              </div>
            ) : asinsData && asinsData.asins.length > 0 ? (
              <div className="space-y-1">
                {asinsData.asins.map((asin) => (
                  <label
                    key={asin.asin}
                    className="flex items-start p-2 hover:bg-gray-50 rounded-md cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedASINs[selectedBrand]?.has(asin.asin) || false}
                      onChange={() => toggleASIN(selectedBrand, asin.asin)}
                      className="mt-1 mr-3"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {asin.asin}
                      </div>
                      {asin.title && (
                        <div className="text-xs text-gray-600 truncate">
                          {asin.title}
                        </div>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 text-sm">
                No ASINs found for this brand
              </div>
            )}
          </div>
        </div>

        {/* Column 3: Campaign Manager */}
        <div className="border border-gray-200 rounded-lg overflow-hidden flex flex-col">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <h3 className="font-medium text-gray-900">Campaigns</h3>
            {selectedBrand && (
              <div className="flex items-center justify-between mt-2">
                <p className="text-xs text-gray-500">
                  {selectedCampaigns[selectedBrand]?.size || 0} selected
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => selectAllCampaigns(selectedBrand)}
                    className="text-xs text-blue-600 hover:text-blue-700"
                  >
                    Select All
                  </button>
                  <button
                    onClick={() => deselectAllCampaigns(selectedBrand)}
                    className="text-xs text-gray-600 hover:text-gray-700"
                  >
                    Clear
                  </button>
                </div>
              </div>
            )}
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {!selectedBrand ? (
              <div className="text-center py-8 text-gray-500 text-sm">
                <Settings className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                Select a brand to view campaigns
              </div>
            ) : campaignsLoading ? (
              <div className="text-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mx-auto text-gray-400" />
              </div>
            ) : campaignsData && campaignsData.campaigns.length > 0 ? (
              <div className="space-y-1">
                {campaignsData.campaigns.map((campaign) => (
                  <label
                    key={campaign.campaign_id}
                    className="flex items-start p-2 hover:bg-gray-50 rounded-md cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedCampaigns[selectedBrand]?.has(campaign.campaign_id) || false}
                      onChange={() => toggleCampaign(selectedBrand, campaign.campaign_id)}
                      className="mt-1 mr-3"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {campaign.campaign_name}
                      </div>
                      <div className="text-xs text-gray-600">
                        {campaign.campaign_type} • ID: {campaign.campaign_id}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 text-sm">
                No campaigns found for this brand
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
