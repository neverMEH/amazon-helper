import { useState, useEffect, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, X, Target } from 'lucide-react';
import api from '../../services/api';
import type { FC } from 'react';

interface CampaignSelectorProps {
  instanceId?: string;  // Now optional
  brandId?: string;  // Now optional
  value: string[] | string | null;
  onChange: (value: string[]) => void;
  placeholder?: string;
  multiple?: boolean;
  campaignType?: 'sp' | 'sb' | 'sd' | 'dsp';  // Specific campaign type filter
  valueType?: 'names' | 'ids';  // Whether to return names or IDs
  showAll?: boolean;  // Show all campaigns without filtering
  className?: string;
}

interface Campaign {
  campaign_id: string;
  campaign_name?: string;
  name?: string;  // Alternative field name from API
  brand?: string;  // Brand name for display
  campaign_type: string;
  status: string;
}

/**
 * Component for selecting campaigns with optional filtering by instance and brand
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
  showAll = false,
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
    queryKey: ['campaigns', instanceId, brandId, searchTerm, campaignType, showAll],
    queryFn: async () => {
      // Always fetch campaigns from the main campaigns table for report builder
      // This ensures we have access to all campaigns in the system
      if (true) {  // Always use main campaigns endpoint for better data access
        const params = new URLSearchParams({
          page: '1',
          page_size: '200',  // Get more campaigns when showing all
          show_all_states: 'false',  // Still only show ENABLED campaigns
        });
        
        if (searchTerm) {
          params.append('search', searchTerm);
        }
        
        if (campaignType) {
          // Map to the 'type' field used by main campaigns endpoint
          const typeMapping: Record<string, string> = {
            'sp': 'sp',
            'sb': 'sb', 
            'sd': 'sd',
            'dsp': 'dsp'
          };
          params.append('type', typeMapping[campaignType] || campaignType);
        }
        
        const response = await api.get(`/campaigns/?${params.toString()}`);
        // Transform response to match expected format
        return {
          campaigns: response.data.campaigns?.map((c: any) => ({
            campaign_id: c.campaignId || c.campaign_id,
            campaign_name: c.name || c.campaign_name || c.campaignName || '',
            name: c.name || c.campaign_name || c.campaignName || '',  // Add name field as fallback
            campaign_type: c.type || c.campaign_type || 'sp',
            status: c.state || c.status || 'ENABLED',
            brand: c.brand || 'Unknown'
          })) || []
        };
      } else {
        // Use the filtered endpoint when instance/brand are provided
        const params = new URLSearchParams({
          instance_id: instanceId || '',
          brand_id: brandId || '',
          limit: '100',
          offset: '0'
        });
        
        if (searchTerm) {
          params.append('search', searchTerm);
        }
        
        if (campaignType) {
          const typeMapping: Record<string, string> = {
            'sp': 'sponsored_products',
            'sb': 'sponsored_brands',
            'sd': 'sponsored_display',
            'dsp': 'dsp'
          };
          // Ensure campaignType is definitely defined for TypeScript
          const type = campaignType as string;
          const mappedType = typeMapping[type] || type;
          params.append('campaign_type', mappedType);
        }

        const response = await api.get(`/campaigns/by-instance-brand/list?${params.toString()}`);
        return response.data;
      }
    },
    enabled: isOpen,  // Always enable when open, don't require instance/brand
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  const campaigns = data?.campaigns || [];
  
  // Debug: Log what we're receiving
  useEffect(() => {
    if (campaigns.length > 0) {
      console.log('[CampaignSelector] Data received from API:', data);
      console.log('[CampaignSelector] Campaigns array:', campaigns);
      console.log('[CampaignSelector] First campaign:', campaigns[0]);
      console.log('[CampaignSelector] ValueType:', valueType);
      console.log('[CampaignSelector] CampaignType filter:', campaignType);
      console.log('[CampaignSelector] ShowAll:', showAll);
      // Check if names are missing
      const missingNames = campaigns.filter((c: Campaign) => !c.campaign_name && !c.name);
      if (missingNames.length > 0) {
        console.warn('[CampaignSelector] Campaigns missing names:', missingNames.length, 'out of', campaigns.length);
      }
    }
  }, [data, campaigns, valueType, campaignType, showAll]);

  // Handle campaign selection
  const handleToggleCampaign = useCallback((campaignId: string, campaignName: string) => {
    const valueToUse = valueType === 'names' ? (campaignName || '') : campaignId;
    console.log('[CampaignSelector] Toggle:', { campaignId, campaignName, valueType, valueToUse });
    
    if (multiple) {
      const newSelected = new Set(selectedCampaigns);
      if (newSelected.has(valueToUse)) {
        newSelected.delete(valueToUse);
      } else {
        newSelected.add(valueToUse);
      }
      setSelectedCampaigns(newSelected);
      onChange(Array.from(newSelected));
    } else {
      const newSelected = new Set([valueToUse]);
      setSelectedCampaigns(newSelected);
      onChange(Array.from(newSelected));
      setIsOpen(false);
    }
  }, [selectedCampaigns, onChange, multiple, valueType]);

  // Handle select all
  const handleSelectAll = useCallback(() => {
    const allCampaigns = campaigns.map((c: Campaign) => 
      valueType === 'names' ? (c.campaign_name || c.name || '') : c.campaign_id
    ).filter((v: string) => v); // Filter out empty values
    setSelectedCampaigns(new Set(allCampaigns));
    onChange(allCampaigns);
  }, [campaigns, onChange, valueType]);

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
      const selectedValue = Array.from(selectedCampaigns)[0];
      // If we're using names, find by name; if IDs, find by ID
      const campaign = campaigns.find((c: Campaign) => 
        valueType === 'names' 
          ? (c.campaign_name || c.name) === selectedValue
          : c.campaign_id === selectedValue
      );
      
      if (campaign) {
        return campaign.campaign_name || campaign.name || `Campaign ID: ${campaign.campaign_id}`;
      }
      return selectedValue;
    }
    
    return `${selectedCampaigns.size} campaigns selected`;
  }, [selectedCampaigns, campaigns, placeholder, valueType]);

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
                No campaigns found{!showAll && brandId ? ' for this brand' : ''}
              </div>
            ) : (
              <div className="py-1">
                {campaigns.map((campaign: Campaign) => {
                  const campaignName = campaign.campaign_name || campaign.name || '';
                  const displayName = campaignName || `Campaign ${campaign.campaign_id}`;
                  const valueToCheck = valueType === 'names' ? campaignName : campaign.campaign_id;
                  
                  return (
                  <label
                    key={campaign.campaign_id}
                    className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type={multiple ? 'checkbox' : 'radio'}
                      checked={selectedCampaigns.has(valueToCheck)}
                      onChange={() => handleToggleCampaign(campaign.campaign_id, campaignName)}
                      className="mr-3 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium text-gray-900">
                          {displayName}
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
                        {showAll && campaign.brand && (
                          <span className="ml-2">• Brand: {campaign.brand}</span>
                        )}
                      </div>
                    </div>
                  </label>
                  );
                })}
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