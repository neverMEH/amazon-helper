import api from './api';

// Types
export interface Brand {
  brand_tag: string;
  brand_name: string;
  source: string;
  asin_count?: number;
  campaign_count?: number;
}

export interface ASIN {
  asin: string;
  title?: string;
  brand: string;
  image_url?: string;
  last_known_price?: number;
  active: boolean;
}

export interface Campaign {
  campaign_id: number;
  campaign_name: string;
  campaign_type: string;
  marketplace_id: string;
  profile_id: string;
  status?: string;
  created_at?: string;
}

export interface InstanceMappings {
  instance_id: string;
  brands: string[];
  asins_by_brand: Record<string, string[]>;
  campaigns_by_brand: Record<string, number[]>;
  updated_at?: string;
}

export interface SaveMappingsRequest {
  brands: string[];
  asins_by_brand: Record<string, string[]>;
  campaigns_by_brand: Record<string, number[]>;
}

export interface SaveMappingsResponse {
  success: boolean;
  message: string;
  instance_id?: string;
  stats?: {
    brands_saved: number;
    asins_saved: number;
    campaigns_saved: number;
  };
  updated_at?: string;
}

export interface ParameterValues {
  instance_id: string;
  parameters: {
    brand_list: string;
    asin_list: string;
    campaign_ids: string;
    campaign_names: string;
  };
  has_mappings: boolean;
}

// Service methods
const instanceMappingService = {
  /**
   * Get all brands available to the user
   */
  getAvailableBrands: async (instanceId: string): Promise<{ brands: Brand[] }> => {
    const response = await api.get(`/instances/${instanceId}/available-brands`);
    return response.data;
  },

  /**
   * Get ASINs for a specific brand
   */
  getBrandASINs: async (
    instanceId: string,
    brandTag: string,
    options?: {
      search?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<{
    brand_tag: string;
    asins: ASIN[];
    total: number;
    limit: number;
    offset: number;
  }> => {
    const params = new URLSearchParams();
    if (options?.search) params.append('search', options.search);
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.offset) params.append('offset', options.offset.toString());

    const queryString = params.toString();
    const url = `/instances/${instanceId}/brands/${brandTag}/asins${
      queryString ? `?${queryString}` : ''
    }`;

    const response = await api.get(url);
    return response.data;
  },

  /**
   * Get campaigns for a specific brand
   */
  getBrandCampaigns: async (
    instanceId: string,
    brandTag: string,
    options?: {
      search?: string;
      campaign_type?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<{
    brand_tag: string;
    campaigns: Campaign[];
    total: number;
    limit: number;
    offset: number;
  }> => {
    const params = new URLSearchParams();
    if (options?.search) params.append('search', options.search);
    if (options?.campaign_type) params.append('campaign_type', options.campaign_type);
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.offset) params.append('offset', options.offset.toString());

    const queryString = params.toString();
    const url = `/instances/${instanceId}/brands/${brandTag}/campaigns${
      queryString ? `?${queryString}` : ''
    }`;

    const response = await api.get(url);
    return response.data;
  },

  /**
   * Get all mappings for an instance
   */
  getInstanceMappings: async (instanceId: string): Promise<InstanceMappings> => {
    const response = await api.get(`/instances/${instanceId}/mappings`);
    return response.data;
  },

  /**
   * Save/update instance mappings (transactional)
   */
  saveInstanceMappings: async (
    instanceId: string,
    mappings: SaveMappingsRequest
  ): Promise<SaveMappingsResponse> => {
    const response = await api.post(`/instances/${instanceId}/mappings`, mappings);
    return response.data;
  },

  /**
   * Get parameter values for auto-population
   */
  getParameterValues: async (instanceId: string): Promise<ParameterValues> => {
    const response = await api.get(`/instances/${instanceId}/parameter-values`);
    return response.data;
  },
};

export default instanceMappingService;
