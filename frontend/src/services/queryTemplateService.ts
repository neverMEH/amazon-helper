import api from './api';
import type { QueryTemplate, QueryTemplateCreate, QueryTemplateUpdate, CreateFromWorkflow } from '../types/queryTemplate';

export const queryTemplateService = {
  async listTemplates(includePublic = true, category?: string): Promise<QueryTemplate[]> {
    const params = new URLSearchParams();
    params.append('include_public', includePublic.toString());
    if (category) {
      params.append('category', category);
    }
    
    const response = await api.get(`/query-templates?${params.toString()}`);
    return response.data;
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
    const response = await api.post(`/queries/templates/${templateId}/build`, parameters);
    return response.data;
  }
};