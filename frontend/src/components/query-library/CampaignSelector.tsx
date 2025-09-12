import { useState, useEffect, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, X, Target, Asterisk, Info } from 'lucide-react';
import api from '../../services/api';
import type { FC } from 'react';

interface CampaignSelectorProps {
  instanceId?: string;
  brandId?: string;
  value: string[] | string | null;
  onChange: (value: string[]) => void;
  placeholder?: string;
  multiple?: boolean;
  campaignType?: 'sp' | 'sb' | 'sd' | 'dsp';
  valueType?: 'names' | 'ids';
  showAll?: boolean;
  className?: string;
  enableWildcards?: boolean;
  maxSelections?: number;
}

interface Campaign {
  campaign_id: string;
  campaign_name?: string;
  name?: string;
  brand?: string;
  campaign_type: string;
  status: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Component for selecting campaigns with wildcard pattern support
 */
export const CampaignSelector: FC<CampaignSelectorProps> = ({
  instanceId,
  brandId,
  value,
  onChange,
  placeholder = 'Select campaigns or use wildcards...',
  multiple = true,
  campaignType,
  valueType = 'ids',
  showAll = false,
  className = '',
  enableWildcards = true,
  maxSelections
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCampaigns, setSelectedCampaigns] = useState<Set<string>>(new Set());
  const [wildcardPatterns, setWildcardPatterns] = useState<Set<string>>(new Set());
  const [showWildcardHelp, setShowWildcardHelp] = useState(false);

  // Convert value to Set for easier manipulation
  useEffect(() => {
    if (value) {
      const campaigns = Array.isArray(value) ? value : [value];
      
      // Separate wildcard patterns from regular campaigns
      const patterns = new Set<string>();
      const regular = new Set<string>();
      
      campaigns.forEach(item => {
        if (enableWildcards && item.includes('*')) {
          patterns.add(item);
        } else {
          regular.add(item);
        }
      });
      
      setWildcardPatterns(patterns);
      setSelectedCampaigns(regular);
    } else {
      setSelectedCampaigns(new Set());
      setWildcardPatterns(new Set());
    }
  }, [value, enableWildcards]);

  // Fetch campaigns from the API
  const { data, isLoading, error } = useQuery({
    queryKey: ['campaigns', instanceId, brandId, searchTerm, campaignType, showAll],
    queryFn: async () => {
      if (showAll || (!instanceId && !brandId)) {
        const params = new URLSearchParams({
          page: '1',
          page_size: '200',
          show_all_states: 'false',
        });
        
        if (searchTerm && !searchTerm.includes('*')) {
          params.append('search', searchTerm);
        }
        
        if (campaignType) {
          const typeMapping: Record<string, string> = {
            'sp': 'sp',
            'sb': 'sb', 
            'sd': 'sd',
            'dsp': 'dsp'
          };
          params.append('type', typeMapping[campaignType] || campaignType);
        }
        
        const response = await api.get(`/campaigns/?${params.toString()}`);
        return {
          campaigns: response.data.campaigns?.map((c: any) => ({
            campaign_id: c.campaignId || c.campaign_id,
            campaign_name: c.name || c.campaign_name || c.campaignName || '',
            name: c.name || c.campaign_name || c.campaignName || '',
            campaign_type: c.type || c.campaign_type || 'sp',
            status: c.state || c.status || 'ENABLED',
            brand: c.brand || 'Unknown',
            created_at: c.created_at,
            updated_at: c.updated_at
          })) || []
        };
      } else {
        const params = new URLSearchParams({
          instance_id: instanceId || '',
          brand_id: brandId || '',
          limit: '100',
          offset: '0'
        });
        
        if (searchTerm && !searchTerm.includes('*')) {
          params.append('search', searchTerm);
        }
        
        if (campaignType) {
          const typeMapping: Record<string, string> = {
            'sp': 'sponsored_products',
            'sb': 'sponsored_brands', 
            'sd': 'sponsored_display',
            'dsp': 'dsp'
          };
          params.append('campaign_type', typeMapping[campaignType] || campaignType);
        }

        const response = await api.get(`/campaigns/by-instance-brand/list?${params.toString()}`);
        return response.data;
      }
    },
    enabled: isOpen && (showAll || (!!instanceId && !!brandId)),
    staleTime: 5 * 60 * 1000,
  });

  const campaigns = data?.campaigns || [];
  
  // Function to convert wildcard pattern to regex
  const wildcardToRegex = (pattern: string): RegExp => {
    const escaped = pattern
      .replace(/[.+?^${}()|[\]\\]/g, '\\$&')  // Escape special regex characters
      .replace(/\*/g, '.*');  // Replace * with .*
    return new RegExp(`^${escaped}$`, 'i');  // Case insensitive
  };
  
  // Filter campaigns based on wildcard patterns
  const matchesWildcardPattern = useCallback((campaignName: string): boolean => {
    if (!enableWildcards || wildcardPatterns.size === 0) return false;
    
    for (const pattern of wildcardPatterns) {
      const regex = wildcardToRegex(pattern);
      if (regex.test(campaignName)) {
        return true;
      }
    }
    return false;
  }, [wildcardPatterns, enableWildcards]);
  
  // Filter campaigns based on search term (including wildcard support)
  const filteredCampaigns = useMemo(() => {
    if (!searchTerm) return campaigns;
    
    if (enableWildcards && searchTerm.includes('*')) {
      const regex = wildcardToRegex(searchTerm);
      return campaigns.filter((c: Campaign) => {
        const name = c.campaign_name || c.name || '';
        return regex.test(name);
      });
    }
    
    // Regular search
    const term = searchTerm.toLowerCase();
    return campaigns.filter((c: Campaign) => {
      const name = (c.campaign_name || c.name || '').toLowerCase();
      const id = c.campaign_id.toLowerCase();
      return name.includes(term) || id.includes(term);
    });
  }, [campaigns, searchTerm, enableWildcards]);

  // Handle adding wildcard pattern
  const handleAddWildcardPattern = useCallback(() => {
    if (!enableWildcards || !searchTerm.includes('*')) return;
    
    const newPatterns = new Set(wildcardPatterns);
    newPatterns.add(searchTerm);
    setWildcardPatterns(newPatterns);
    
    // Update the parent component
    const allSelected = [
      ...Array.from(selectedCampaigns),
      ...Array.from(newPatterns)
    ];
    onChange(allSelected);
    setSearchTerm('');
  }, [searchTerm, wildcardPatterns, selectedCampaigns, onChange, enableWildcards]);

  // Handle removing wildcard pattern
  const handleRemoveWildcardPattern = useCallback((pattern: string) => {
    const newPatterns = new Set(wildcardPatterns);
    newPatterns.delete(pattern);
    setWildcardPatterns(newPatterns);
    
    // Update the parent component
    const allSelected = [
      ...Array.from(selectedCampaigns),
      ...Array.from(newPatterns)
    ];
    onChange(allSelected);
  }, [wildcardPatterns, selectedCampaigns, onChange]);

  // Handle campaign selection
  const handleToggleCampaign = useCallback((campaignId: string, campaignName: string) => {
    const valueToUse = valueType === 'names' ? (campaignName || '') : campaignId;
    
    if (multiple) {
      const newSelected = new Set(selectedCampaigns);
      if (newSelected.has(valueToUse)) {
        newSelected.delete(valueToUse);
      } else {
        // Check max selections
        if (maxSelections && newSelected.size >= maxSelections) {
          return;
        }
        newSelected.add(valueToUse);
      }
      setSelectedCampaigns(newSelected);
      
      // Combine with wildcard patterns
      const allSelected = [
        ...Array.from(newSelected),
        ...Array.from(wildcardPatterns)
      ];
      onChange(allSelected);
    } else {
      const newSelected = new Set([valueToUse]);
      setSelectedCampaigns(newSelected);
      onChange([valueToUse]);
      setIsOpen(false);
    }
  }, [selectedCampaigns, onChange, multiple, valueType, wildcardPatterns, maxSelections]);

  // Handle select all matching
  const handleSelectAllMatching = useCallback(() => {
    const matchingValues = filteredCampaigns
      .slice(0, maxSelections || filteredCampaigns.length)
      .map((c: Campaign) => 
        valueType === 'names' ? (c.campaign_name || c.name || '') : c.campaign_id
      )
      .filter((v: string) => v);
    
    setSelectedCampaigns(new Set(matchingValues));
    
    // Combine with wildcard patterns
    const allSelected = [
      ...matchingValues,
      ...Array.from(wildcardPatterns)
    ];
    onChange(allSelected);
  }, [filteredCampaigns, onChange, valueType, wildcardPatterns, maxSelections]);

  // Handle clear selection
  const handleClearSelection = useCallback(() => {
    setSelectedCampaigns(new Set());
    setWildcardPatterns(new Set());
    onChange([]);
  }, [onChange]);

  // Get display text for selected campaigns
  const displayText = useMemo(() => {
    const totalSelected = selectedCampaigns.size + wildcardPatterns.size;
    
    if (!totalSelected) {
      return placeholder;
    }
    
    if (totalSelected === 1) {
      if (wildcardPatterns.size === 1) {
        return `Pattern: ${Array.from(wildcardPatterns)[0]}`;
      }
      
      const selectedValue = Array.from(selectedCampaigns)[0];
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
    
    const parts = [];
    if (selectedCampaigns.size > 0) {
      parts.push(`${selectedCampaigns.size} campaigns`);
    }
    if (wildcardPatterns.size > 0) {
      parts.push(`${wildcardPatterns.size} patterns`);
    }
    
    return parts.join(', ');
  }, [selectedCampaigns, wildcardPatterns, campaigns, placeholder, valueType]);

  // Count campaigns matching wildcard patterns
  const wildcardMatchCount = useMemo(() => {
    if (!enableWildcards || wildcardPatterns.size === 0) return 0;
    
    return campaigns.filter((c: Campaign) => {
      const name = c.campaign_name || c.name || '';
      return matchesWildcardPattern(name);
    }).length;
  }, [campaigns, wildcardPatterns, matchesWildcardPattern, enableWildcards]);

  // Get campaign type badge color
  const getTypeColor = (type: string): string => {
    switch (type?.toLowerCase()) {
      case 'sponsored_products':
      case 'sp':
        return 'bg-blue-100 text-blue-800';
      case 'sponsored_brands':
      case 'sb':
        return 'bg-purple-100 text-purple-800';
      case 'sponsored_display':
      case 'sd':
        return 'bg-green-100 text-green-800';
      case 'dsp':
        return 'bg-orange-100 text-orange-800';
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
            <span className={selectedCampaigns.size || wildcardPatterns.size ? 'text-gray-900' : 'text-gray-500'}>
              {displayText}
            </span>
          </div>
          {(selectedCampaigns.size > 0 || wildcardPatterns.size > 0) && (
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
          {/* Search input with wildcard support */}
          <div className="p-2 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-20 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder={enableWildcards ? "Search or use wildcards (*)" : "Search campaigns..."}
                autoFocus
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && enableWildcards && searchTerm.includes('*')) {
                    handleAddWildcardPattern();
                  }
                }}
              />
              {enableWildcards && (
                <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
                  {searchTerm.includes('*') && (
                    <button
                      type="button"
                      onClick={handleAddWildcardPattern}
                      className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Add Pattern
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setShowWildcardHelp(!showWildcardHelp)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <Info className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>
            
            {/* Wildcard help */}
            {enableWildcards && showWildcardHelp && (
              <div className="mt-2 p-2 bg-blue-50 rounded text-xs text-blue-700">
                <div className="font-semibold mb-1">Wildcard Pattern Examples:</div>
                <div className="space-y-1">
                  <div>• <code>Brand_*</code> - All campaigns starting with "Brand_"</div>
                  <div>• <code>*_2025</code> - All campaigns ending with "_2025"</div>
                  <div>• <code>*Holiday*</code> - All campaigns containing "Holiday"</div>
                  <div>• <code>Brand_*_Q4</code> - Pattern matching multiple parts</div>
                </div>
              </div>
            )}
          </div>

          {/* Selected wildcard patterns */}
          {enableWildcards && wildcardPatterns.size > 0 && (
            <div className="p-2 border-b bg-gray-50">
              <div className="text-xs text-gray-600 mb-1">Active Patterns ({wildcardMatchCount} matches):</div>
              <div className="flex flex-wrap gap-1">
                {Array.from(wildcardPatterns).map(pattern => (
                  <span
                    key={pattern}
                    className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                  >
                    <Asterisk className="h-3 w-3 mr-1" />
                    {pattern}
                    <button
                      type="button"
                      onClick={() => handleRemoveWildcardPattern(pattern)}
                      className="ml-1 text-blue-600 hover:text-blue-800"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Action buttons */}
          {multiple && (
            <div className="p-2 border-b flex justify-between">
              <button
                type="button"
                onClick={handleSelectAllMatching}
                className="text-sm text-blue-600 hover:text-blue-700"
                disabled={maxSelections && selectedCampaigns.size >= maxSelections}
              >
                Select All Matching ({filteredCampaigns.length})
                {maxSelections && ` (max ${maxSelections})`}
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
            ) : filteredCampaigns.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                {searchTerm 
                  ? `No campaigns matching "${searchTerm}"`
                  : 'No campaigns found'
                }
                {!showAll && brandId && ' for this brand'}
              </div>
            ) : (
              <div className="py-1">
                {filteredCampaigns.map((campaign: Campaign) => {
                  const campaignName = campaign.campaign_name || campaign.name || '';
                  const displayName = campaignName || `Campaign ${campaign.campaign_id}`;
                  const valueToCheck = valueType === 'names' ? campaignName : campaign.campaign_id;
                  const isMatchingPattern = matchesWildcardPattern(campaignName);
                  const isDisabled = maxSelections && 
                    selectedCampaigns.size >= maxSelections && 
                    !selectedCampaigns.has(valueToCheck);
                  
                  return (
                    <label
                      key={campaign.campaign_id}
                      className={`flex items-center px-3 py-2 cursor-pointer ${
                        isMatchingPattern ? 'bg-blue-50' : 'hover:bg-gray-50'
                      } ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <input
                        type={multiple ? 'checkbox' : 'radio'}
                        checked={selectedCampaigns.has(valueToCheck)}
                        onChange={() => handleToggleCampaign(campaign.campaign_id, campaignName)}
                        disabled={isDisabled}
                        className="mr-3 text-blue-600 focus:ring-blue-500"
                      />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-gray-900">
                              {displayName}
                            </span>
                            {isMatchingPattern && (
                              <Asterisk className="ml-1 h-3 w-3 text-blue-600" />
                            )}
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

          {/* Summary and close */}
          <div className="p-2 border-t bg-gray-50">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs text-gray-600">
                {selectedCampaigns.size} selected
                {wildcardPatterns.size > 0 && `, ${wildcardMatchCount} matching patterns`}
                {maxSelections && ` (max ${maxSelections})`}
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="px-3 py-1 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CampaignSelector;