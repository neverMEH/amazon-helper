import api from './api';

export interface Campaign {
  campaign_id: string;
  campaign_name?: string;
  brand_name?: string;
  campaign_type?: string;
  status?: 'ENABLED' | 'PAUSED' | 'ARCHIVED';
  budget?: number;
  start_date?: string;
  end_date?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CampaignListResponse {
  campaigns: Campaign[];
  total: number;
  page?: number;
  page_size?: number;
}

export interface CampaignSearchParams {
  instance_id: string;
  brand_name?: string;
  status?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

const campaignService = {
  // Get campaigns for an instance
  getCampaigns: async (params: CampaignSearchParams): Promise<CampaignListResponse> => {
    const response = await api.get('/campaigns/', { params });
    return response.data;
  },

  // Get single campaign details
  getCampaign: async (instanceId: string, campaignId: string): Promise<Campaign> => {
    const response = await api.get(`/campaigns/${instanceId}/${campaignId}`);
    return response.data;
  },

  // Get unique brands for campaigns in an instance
  getCampaignBrands: async (instanceId: string): Promise<string[]> => {
    const response = await api.get(`/campaigns/${instanceId}/brands`);
    return response.data.brands || [];
  }
};

export default campaignService;