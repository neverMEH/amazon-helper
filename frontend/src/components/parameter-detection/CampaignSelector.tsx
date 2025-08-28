import { useState, useEffect, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, X, Target } from 'lucide-react';
import api from '../../services/api';
import type { FC } from 'react';

interface CampaignSelectorProps {
  instanceId: string;
  brandId: string;
  value: string[] | string | null;
  onChange: (value: string[]) => void;
  placeholder?: string;
  multiple?: boolean;
  campaignType?: 'sp' | 'sb' | 'sd' | 'dsp';  // Specific campaign type filter
  valueType?: 'names' | 'ids';  // Whether to return names or IDs
  className?: string;
}

interface Campaign {
  campaign_id: string;
  campaign_name: string;
  campaign_type: string;
  status: string;
}

/**
 * Component for selecting campaigns filtered by instance and brand
 */
export const CampaignSelector: FC<CampaignSelectorProps> = ({
  instanceId,
  brandId,
  value,
  onChange,
  placeholder = 'Select campaigns...',
  multiple = true,
  campaignType,
  valueType = 'ids',
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCampaigns, setSelectedCampaigns] = useState<Set<string>>(new Set());

  // Convert value to Set for easier manipulation
  useEffect(() => {
    if (value) {
      const campaigns = Array.isArray(value) ? value : [value];
      setSelectedCampaigns(new Set(campaigns));
    } else {
      setSelectedCampaigns(new Set());
    }
  }, [value]);

  // Fetch campaigns from the API
  const { data, isLoading, error } = useQuery({
    queryKey: ['campaigns', instanceId, brandId, searchTerm, campaignType],
    queryFn: async () => {
      const params = new URLSearchParams({
        instance_id: instanceId,
        brand_id: brandId,
        limit: '100',
        offset: '0'
      });
      
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      
      if (campaignType) {
        // Map campaign type to API format
        const typeMapping: Record<string, string> = {
          'sp': 'sponsored_products',
          'sb': 'sponsored_brands', 
          'sd': 'sponsored_display',
          'dsp': 'dsp'  // DSP campaigns (not implemented yet)
        };
        params.append('campaign_type', typeMapping[campaignType] || campaignType);
      }

      const response = await api.get(`/campaigns/by-instance-brand/list?${params.toString()}`);
      return response.data;
    },
    enabled: !!instanceId && !!brandId && isOpen,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  const campaigns = data?.campaigns || [];

  // Handle campaign selection
  const handleToggleCampaign = useCallback((campaignId: string, campaignName: string) => {
    const newSelected = new Set(selectedCampaigns);
    const valueToUse = valueType === 'names' ? campaignName : campaignId;
    
    if (multiple) {
      if (newSelected.has(valueToUse)) {
        newSelected.delete(valueToUse);
      } else {
        newSelected.add(valueToUse);
      }
    } else {
      newSelected.clear();
      newSelected.add(valueToUse);
      setIsOpen(false);
    }
    
    setSelectedCampaigns(newSelected);
    onChange(Array.from(newSelected));
  }, [selectedCampaigns, onChange, multiple, valueType]);

  // Handle select all
  const handleSelectAll = useCallback(() => {
    const allCampaigns = campaigns.map((c: Campaign) => 
      valueType === 'names' ? c.campaign_name : c.campaign_id
    );
    setSelectedCampaigns(new Set(allCampaigns));
    onChange(allCampaigns);
  }, [campaigns, onChange]);

  // Handle clear selection
  const handleClearSelection = useCallback(() => {
    setSelectedCampaigns(new Set());
    onChange([]);
  }, [onChange]);

  // Get display text for selected campaigns
  const displayText = useMemo(() => {
    if (!selectedCampaigns.size) {
      return placeholder;
    }
    
    if (selectedCampaigns.size === 1) {
      const campaignId = Array.from(selectedCampaigns)[0];
      const campaign = campaigns.find((c: Campaign) => c.campaign_id === campaignId);
      return campaign ? `${campaign.campaign_name}` : campaignId;
    }
    
    return `${selectedCampaigns.size} campaigns selected`;
  }, [selectedCampaigns, campaigns, placeholder]);

  // Get campaign type badge color
  const getTypeColor = (type: string): string => {
    switch (type?.toLowerCase()) {
      case 'sponsored_products':
        return 'bg-blue-100 text-blue-800';
      case 'sponsored_brands':
        return 'bg-purple-100 text-purple-800';
      case 'sponsored_display':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className={`relative ${className}`}>
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 hover:bg-gray-50"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Target className="h-4 w-4 text-gray-400 mr-2" />
            <span className={selectedCampaigns.size ? 'text-gray-900' : 'text-gray-500'}>
              {displayText}
            </span>
          </div>
          {selectedCampaigns.size > 0 && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleClearSelection();
              }}
              className="ml-2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </button>

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg">
          {/* Search input */}
          <div className="p-2 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Search campaigns..."
                autoFocus
              />
            </div>
          </div>

          {/* Action buttons */}
          {multiple && (
            <div className="p-2 border-b flex justify-between">
              <button
                type="button"
                onClick={handleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Select All ({campaigns.length})
              </button>
              <button
                type="button"
                onClick={handleClearSelection}
                className="text-sm text-gray-600 hover:text-gray-700"
              >
                Clear Selection
              </button>
            </div>
          )}

          {/* Campaign list */}
          <div className="max-h-60 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center text-gray-500">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                Loading campaigns...
              </div>
            ) : error ? (
              <div className="p-4 text-center text-red-600">
                Error loading campaigns. Please try again.
              </div>
            ) : campaigns.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No campaigns found for this brand
              </div>
            ) : (
              <div className="py-1">
                {campaigns.map((campaign: Campaign) => (
                  <label
                    key={campaign.campaign_id}
                    className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type={multiple ? 'checkbox' : 'radio'}
                      checked={selectedCampaigns.has(
                        valueType === 'names' ? campaign.campaign_name : campaign.campaign_id
                      )}
                      onChange={() => handleToggleCampaign(campaign.campaign_id, campaign.campaign_name)}
                      className="mr-3 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium text-gray-900">
                          {campaign.campaign_name}
                        </div>
                        <span
                          className={`ml-2 px-2 py-1 text-xs rounded-full ${getTypeColor(
                            campaign.campaign_type
                          )}`}
                        >
                          {campaign.campaign_type?.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        ID: {campaign.campaign_id}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Close button */}
          <div className="p-2 border-t">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="w-full px-3 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};