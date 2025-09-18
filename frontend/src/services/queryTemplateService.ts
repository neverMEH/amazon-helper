import api from './api';
import type { QueryTemplate, QueryTemplateCreate, QueryTemplateUpdate, CreateFromWorkflow } from '../types/queryTemplate';

interface TemplateFilters {
  category?: string;
  search?: string;
  tags?: string[];
  include_public?: boolean;
  sort_by?: 'usage_count' | 'created_at' | 'name';
}

export const queryTemplateService = {
  async listTemplates(includePublic = true, filters?: TemplateFilters): Promise<{ data: { templates: QueryTemplate[] } }> {
    const params = new URLSearchParams();
    params.append('include_public', includePublic.toString());

    if (filters) {
      if (filters.category) params.append('category', filters.category);
      if (filters.search) params.append('search', filters.search);
      if (filters.tags?.length) params.append('tags', filters.tags.join(','));
      if (filters.sort_by) params.append('sort_by', filters.sort_by);
    }

    const response = await api.get(`/query-templates?${params.toString()}`);
    // Return in the format expected by the component
    return { data: { templates: response.data } };
  },

  async getTemplate(templateId: string): Promise<QueryTemplate> {
    const response = await api.get(`/query-templates/${templateId}`);
    return response.data;
  },

  async createTemplate(template: QueryTemplateCreate): Promise<{ templateId: string; name: string; category: string; createdAt: string }> {
    const response = await api.post('/query-templates', template);
    return response.data;
  },

  async updateTemplate(templateId: string, updates: QueryTemplateUpdate): Promise<{ templateId: string; name: string; updatedAt: string }> {
    const response = await api.put(`/query-templates/${templateId}`, updates);
    return response.data;
  },

  async deleteTemplate(templateId: string): Promise<void> {
    await api.delete(`/query-templates/${templateId}`);
  },

  async createFromWorkflow(data: CreateFromWorkflow): Promise<{ templateId: string; name: string; category: string; createdAt: string }> {
    const response = await api.post('/query-templates/from-workflow', data);
    return response.data;
  },

  async getCategories(): Promise<string[]> {
    const response = await api.get('/query-templates/categories');
    return response.data;
  },

  async useTemplate(templateId: string): Promise<{ templateId: string; usageCount: number }> {
    const response = await api.post(`/query-templates/${templateId}/use`);
    return response.data;
  },

  async buildQueryFromTemplate(templateId: string, parameters: Record<string, any>): Promise<{
    template_id: string;
    template_name: string;
    sql_query: string;
    parameters_used: Record<string, any>;
  }> {
    const response = await api.post(`/query-templates/${templateId}/build`, parameters);
    return response.data;
  },

  async incrementUsage(templateId: string): Promise<{ success: boolean }> {
    try {
      await api.post(`/query-templates/${templateId}/increment-usage`);
      return { success: true };
    } catch (error) {
      console.error('Failed to increment template usage:', error);
      return { success: false };
    }
  },

  async forkTemplate(templateId: string, forkData: {
    name: string;
    description?: string;
    sql_query: string;
    is_public?: boolean;
    parent_template_id?: string;
    version?: number;
  }): Promise<QueryTemplate> {
    const response = await api.post(`/query-templates/${templateId}/fork`, forkData);
    return response.data;
  },

  async getTemplateMetrics(templateId: string, timeRange?: '7d' | '30d' | '90d'): Promise<any> {
    const params = timeRange ? `?time_range=${timeRange}` : '';
    const response = await api.get(`/query-templates/${templateId}/metrics${params}`);
    return response.data;
  },

  async updateTemplateTags(templateId: string, tags: string[], category: string): Promise<QueryTemplate> {
    const response = await api.put(`/query-templates/${templateId}/tags`, { tags, category });
    return response.data;
  },

  async favoriteTemplate(templateId: string): Promise<{ success: boolean }> {
    const response = await api.post(`/query-templates/${templateId}/favorite`);
    return response.data;
  },

  async unfavoriteTemplate(templateId: string): Promise<{ success: boolean }> {
    const response = await api.delete(`/query-templates/${templateId}/favorite`);
    return response.data;
  },

  async getTemplateVersionHistory(templateId: string): Promise<any[]> {
    const response = await api.get(`/query-templates/${templateId}/versions`);
    return response.data;
  }
};

// Export individual functions for backward compatibility
export const { listTemplates } = queryTemplateService;