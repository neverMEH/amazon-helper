import React, { useState, useEffect, useMemo } from 'react';
import { X, Search, Megaphone, CheckSquare, Square } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import campaignService, { type Campaign, type CampaignListResponse, type CampaignSearchParams } from '../../services/campaignService';
import LoadingSpinner from '../LoadingSpinner';

interface CampaignSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (campaignIds: string[]) => void;
  instanceId?: string;
  currentValue?: string[] | string;
  multiple?: boolean;
  title?: string;
}

const CampaignSelectionModal: React.FC<CampaignSelectionModalProps> = ({
  isOpen,
  onClose,
  onSelect,
  instanceId,
  currentValue = [],
  multiple = true,
  title = 'Select Campaigns'
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBrand, setSelectedBrand] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedCampaigns, setSelectedCampaigns] = useState<Set<string>>(new Set());
  const [page] = useState(1);
  const pageSize = 100;

  // Initialize selected campaigns from current value
  useEffect(() => {
    if (currentValue) {
      const campaigns = Array.isArray(currentValue) 
        ? currentValue 
        : currentValue.split(',').map(c => c.trim().replace(/'/g, '')).filter(Boolean);
      setSelectedCampaigns(new Set(campaigns));
    }
  }, [currentValue, isOpen]);

  // Fetch campaigns for the instance
  const { data: campaignsData, isLoading } = useQuery<CampaignListResponse>({
    queryKey: ['instance-campaigns', instanceId, selectedBrand, selectedStatus, searchQuery, page],
    queryFn: async () => {
      if (!instanceId) {
        return { campaigns: [], total: 0 };
      }
      
      // Call the campaigns API with filters
      const params: CampaignSearchParams = {
        instance_id: instanceId,
        brand_name: selectedBrand || undefined,
        status: selectedStatus || undefined,
        search: searchQuery || undefined,
        page,
        page_size: pageSize
      };
      const response = await campaignService.getCampaigns(params);
      
      return response;
    },
    enabled: isOpen && !!instanceId,
    staleTime: 5 * 60 * 1000
  });

  // Get unique brands from campaigns
  const brands = useMemo(() => {
    if (!campaignsData?.campaigns) return [];
    const brandSet = new Set<string>();
    campaignsData.campaigns.forEach((campaign: Campaign) => {
      if (campaign.brand_name) {
        brandSet.add(campaign.brand_name);
      }
    });
    return Array.from(brandSet).sort();
  }, [campaignsData]);

  // Filter campaigns based on search
  const filteredCampaigns = useMemo((): Campaign[] => {
    if (!campaignsData?.campaigns) return [];
    
    return campaignsData.campaigns.filter((campaign: Campaign) => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        campaign.campaign_id?.toLowerCase().includes(query) ||
        campaign.campaign_name?.toLowerCase().includes(query) ||
        campaign.brand_name?.toLowerCase().includes(query)
      );
    });
  }, [campaignsData, searchQuery]);

  const handleToggleCampaign = (campaignId: string) => {
    const newSelection = new Set(selectedCampaigns);
    if (newSelection.has(campaignId)) {
      newSelection.delete(campaignId);
    } else {
      if (multiple) {
        newSelection.add(campaignId);
      } else {
        // Single selection mode
        newSelection.clear();
        newSelection.add(campaignId);
      }
    }
    setSelectedCampaigns(newSelection);
  };

  const handleSelectAll = () => {
    const allVisible = filteredCampaigns.map((c: Campaign) => c.campaign_id);
    const allSelected = allVisible.every((id: string) => selectedCampaigns.has(id));
    
    if (allSelected) {
      // Deselect all visible
      const newSelection = new Set(selectedCampaigns);
      allVisible.forEach((id: string) => newSelection.delete(id));
      setSelectedCampaigns(newSelection);
    } else {
      // Select all visible
      const newSelection = new Set(selectedCampaigns);
      allVisible.forEach((id: string) => newSelection.add(id));
      setSelectedCampaigns(newSelection);
    }
  };

  const handleConfirm = () => {
    onSelect(Array.from(selectedCampaigns));
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full mx-4 max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center">
            <Megaphone className="w-6 h-6 text-blue-600 mr-3" />
            <div>
              <h2 className="text-xl font-semibold">{title}</h2>
              <p className="text-sm text-gray-600">
                {multiple 
                  ? `Select multiple campaigns (${selectedCampaigns.size} selected)`
                  : 'Select a campaign'
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
                  placeholder="Search by campaign ID or name..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Brand Filter */}
            <div className="w-48">
              <select
                value={selectedBrand}
                onChange={(e) => setSelectedBrand(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Brands</option>
                {brands.map(brand => (
                  <option key={brand} value={brand}>{brand}</option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div className="w-40">
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Status</option>
                <option value="ENABLED">Enabled</option>
                <option value="PAUSED">Paused</option>
                <option value="ARCHIVED">Archived</option>
              </select>
            </div>
          </div>

          {/* Bulk Actions */}
          {multiple && filteredCampaigns.length > 0 && (
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleSelectAll}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                {filteredCampaigns.every((c: Campaign) => selectedCampaigns.has(c.campaign_id)) 
                  ? 'Deselect All' 
                  : 'Select All Visible'
                }
              </button>
              <span className="text-sm text-gray-600 py-1">
                {filteredCampaigns.length} campaigns visible
              </span>
            </div>
          )}
        </div>

        {/* Campaign List */}
        <div className="flex-1 overflow-y-auto p-4">
          {!instanceId ? (
            <div className="text-center py-12">
              <Megaphone className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Please select an instance first</p>
              <p className="text-sm text-gray-500 mt-2">
                Campaigns are specific to each AMC instance
              </p>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : filteredCampaigns.length === 0 ? (
            <div className="text-center py-12">
              <Megaphone className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No campaigns found</p>
              {searchQuery && (
                <p className="text-sm text-gray-500 mt-2">
                  Try adjusting your search or filters
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredCampaigns.map((campaign: Campaign) => (
                <div
                  key={campaign.campaign_id}
                  className={`flex items-center p-3 border rounded-lg hover:bg-gray-50 cursor-pointer ${
                    selectedCampaigns.has(campaign.campaign_id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                  onClick={() => handleToggleCampaign(campaign.campaign_id)}
                >
                  <div className="mr-3">
                    {selectedCampaigns.has(campaign.campaign_id) ? (
                      <CheckSquare className="w-5 h-5 text-blue-600" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-gray-900">
                        {campaign.campaign_id}
                      </span>
                      {campaign.status && (
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          campaign.status === 'ENABLED' 
                            ? 'bg-green-100 text-green-700' 
                            : campaign.status === 'PAUSED'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {campaign.status}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-700 mt-1">
                      {campaign.campaign_name || 'Unnamed Campaign'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {campaign.brand_name && (
                        <span>Brand: {campaign.brand_name}</span>
                      )}
                      {campaign.brand_name && campaign.campaign_type && ' • '}
                      {campaign.campaign_type && (
                        <span>Type: {campaign.campaign_type}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t">
          <div className="text-sm text-gray-600">
            {selectedCampaigns.size > 0 && (
              <span>{selectedCampaigns.size} campaign{selectedCampaigns.size !== 1 ? 's' : ''} selected</span>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={selectedCampaigns.size === 0}
              className={`px-4 py-2 rounded-md ${
                selectedCampaigns.size > 0
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Select
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CampaignSelectionModal;