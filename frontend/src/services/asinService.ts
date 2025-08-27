import api from './api';

export interface ASIN {
  id: string;
  asin: string;
  title?: string;
  brand?: string;
  marketplace?: string;
  last_known_price?: number;
  monthly_estimated_units?: number;
  active: boolean;
  updated_at: string;
}

export interface ASINDetail extends ASIN {
  description?: string;
  department?: string;
  manufacturer?: string;
  product_group?: string;
  product_type?: string;
  color?: string;
  size?: string;
  model?: string;
  item_dimensions?: {
    length?: number;
    height?: number;
    width?: number;
    weight?: number;
    unit_dimension?: string;
    unit_weight?: string;
  };
  parent_asin?: string;
  variant_type?: string;
  monthly_estimated_sales?: number;
  created_at: string;
  last_imported_at?: string;
}

export interface ASINListResponse {
  items: ASIN[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ASINSearchRequest {
  asin_ids?: string[];
  brands?: string[];
  search?: string;
  limit?: number;
}

export interface ASINSearchResponse {
  asins: Array<{
    asin: string;
    title?: string;
    brand?: string;
  }>;
  total: number;
}

export interface BrandsResponse {
  brands: string[];
  total: number;
}

export interface ImportResponse {
  import_id?: string;
  status: string;
  total_rows?: number;
  message: string;
}

export interface ImportStatus {
  id: string;
  status: string;
  total_rows: number;
  successful_imports: number;
  failed_imports: number;
  duplicate_skipped?: number;
  error_details?: any;
  started_at: string;
  completed_at?: string;
}

const asinService = {
  // List ASINs with pagination and filters
  listASINs: async (params?: {
    page?: number;
    page_size?: number;
    brand?: string;
    marketplace?: string;
    search?: string;
    active?: boolean;
  }): Promise<ASINListResponse> => {
    const response = await api.get('/asins/', { params });
    return response.data;
  },

  // Get single ASIN details
  getASIN: async (asinId: string): Promise<ASINDetail> => {
    const response = await api.get(`/asins/${asinId}`);
    return response.data;
  },

  // Get unique brands list
  getBrands: async (search?: string): Promise<BrandsResponse> => {
    const response = await api.get('/asins/brands', { 
      params: search ? { search } : undefined 
    });
    return response.data;
  },

  // Search ASINs for parameter selection
  searchASINs: async (request: ASINSearchRequest): Promise<ASINSearchResponse> => {
    const response = await api.post('/asins/search', request);
    return response.data;
  },

  // Import ASINs from CSV file
  importASINs: async (file: File, updateExisting: boolean = true): Promise<ImportResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('update_existing', updateExisting.toString());

    const response = await api.post('/asins/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  // Get import status
  getImportStatus: async (importId: string): Promise<ImportStatus> => {
    const response = await api.get(`/asins/import/${importId}`);
    return response.data;
  }
};

export default asinService;