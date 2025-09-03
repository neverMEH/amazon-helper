import type { 
  QueryFlowTemplate, 
  TemplateListResponse,
  ExecuteTemplateRequest,
  ExecuteTemplateResponse,
  ValidateParametersRequest,
  ValidateParametersResponse,
  PreviewSQLRequest,
  PreviewSQLResponse,
  ParameterFormValues
} from '../types/queryFlowTemplate';
import api from './api';

export const queryFlowTemplateService = {
  // List templates with filtering
  async listTemplates(params?: {
    category?: string;
    search?: string;
    tags?: string[];
    limit?: number;
    offset?: number;
    include_stats?: boolean;
  }): Promise<TemplateListResponse> {
    const searchParams = new URLSearchParams();
    
    if (params?.category) searchParams.append('category', params.category);
    if (params?.search) searchParams.append('search', params.search);
    if (params?.tags) params.tags.forEach(tag => searchParams.append('tags', tag));
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    if (params?.include_stats !== undefined) searchParams.append('include_stats', params.include_stats.toString());

    const response = await api.get(`/query-flow-templates/?${searchParams}`);
    return response.data;
  },

  // Get single template
  async getTemplate(
    templateId: string, 
    includeParameters = true, 
    includeCharts = true
  ): Promise<QueryFlowTemplate> {
    const searchParams = new URLSearchParams();
    searchParams.append('include_parameters', includeParameters.toString());
    searchParams.append('include_charts', includeCharts.toString());

    const response = await api.get(`/query-flow-templates/${templateId}?${searchParams}`);
    return response.data;
  },

  // Execute template
  async executeTemplate(
    templateId: string,
    request: ExecuteTemplateRequest
  ): Promise<ExecuteTemplateResponse> {
    const response = await api.post(`/query-flow-templates/${templateId}/execute`, request);
    return response.data;
  },

  // Validate parameters
  async validateParameters(
    templateId: string,
    parameters: ParameterFormValues
  ): Promise<ValidateParametersResponse> {
    const request: ValidateParametersRequest = { parameters };
    const response = await api.post(`/query-flow-templates/${templateId}/validate-parameters`, request);
    return response.data;
  },

  // Preview SQL with parameter substitution
  async previewSQL(
    templateId: string,
    parameters: ParameterFormValues
  ): Promise<PreviewSQLResponse> {
    const request: PreviewSQLRequest = { parameters };
    const response = await api.post(`/query-flow-templates/${templateId}/preview-sql`, request);
    return response.data;
  },

  // Get execution history
  async getExecutionHistory(
    templateId: string,
    params?: {
      limit?: number;
      offset?: number;
      status?: string;
    }
  ): Promise<any> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    if (params?.status) searchParams.append('status', params.status);

    const response = await api.get(`/query-flow-templates/${templateId}/executions?${searchParams}`);
    return response.data;
  },

  // Create new template
  async createTemplate(template: {
    template_id: string;
    name: string;
    description?: string;
    category: string;
    sql_template: string;
    parameters?: any[];
    chart_configs?: any[];
    tags?: string[];
    is_public?: boolean;
    is_active?: boolean;
  }): Promise<QueryFlowTemplate> {
    const response = await api.post('/query-flow-templates/', template);
    return response.data;
  },

  // Update existing template
  async updateTemplate(
    templateId: string,
    updates: Partial<{
      name: string;
      description: string;
      category: string;
      sql_template: string;
      parameters: any[];
      chart_configs: any[];
      tags: string[];
      is_public: boolean;
      is_active: boolean;
    }>
  ): Promise<QueryFlowTemplate> {
    const response = await api.put(`/query-flow-templates/${templateId}`, updates);
    return response.data;
  },

  // Delete template
  async deleteTemplate(templateId: string): Promise<void> {
    await api.delete(`/query-flow-templates/${templateId}`);
  },

  // Duplicate template
  async duplicateTemplate(templateId: string, newName: string): Promise<QueryFlowTemplate> {
    const response = await api.post(`/query-flow-templates/${templateId}/duplicate`, { name: newName });
    return response.data;
  },

  // Toggle favorite
  async toggleFavorite(templateId: string): Promise<{ is_favorite: boolean; message: string }> {
    const response = await api.post(`/query-flow-templates/${templateId}/favorite`);
    return response.data;
  },

  // Rate template
  async rateTemplate(
    templateId: string,
    rating: number,
    review?: string
  ): Promise<any> {
    const response = await api.post(`/query-flow-templates/${templateId}/rate`, {
      rating,
      review
    });
    return response.data;
  },

  // Get categories
  async getCategories(): Promise<string[]> {
    const response = await api.get('/query-flow-templates/categories');
    return response.data.categories;
  },

  // Get popular tags
  async getPopularTags(limit = 20): Promise<Array<{ tag: string; count: number }>> {
    const response = await api.get(`/query-flow-templates/tags?limit=${limit}`);
    return response.data.tags;
  },

};