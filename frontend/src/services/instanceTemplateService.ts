/**
 * Instance Template Service
 *
 * API service for managing SQL templates scoped to specific AMC instances
 */

import api from './api';
import type {
  InstanceTemplate,
  InstanceTemplateCreate,
  InstanceTemplateUpdate,
  InstanceTemplateResponse,
} from '../types/instanceTemplate';

export const instanceTemplateService = {
  /**
   * List all templates for a specific instance
   */
  async listTemplates(instanceId: string): Promise<InstanceTemplate[]> {
    const response = await api.get(`/instances/${instanceId}/templates`);
    return response.data;
  },

  /**
   * Get a specific template by ID
   */
  async getTemplate(instanceId: string, templateId: string): Promise<InstanceTemplate> {
    const response = await api.get(`/instances/${instanceId}/templates/${templateId}`);
    return response.data;
  },

  /**
   * Create a new template for an instance
   */
  async createTemplate(
    instanceId: string,
    template: InstanceTemplateCreate
  ): Promise<InstanceTemplateResponse> {
    const response = await api.post(`/instances/${instanceId}/templates`, template);
    return response.data;
  },

  /**
   * Update an existing template
   */
  async updateTemplate(
    instanceId: string,
    templateId: string,
    updates: InstanceTemplateUpdate
  ): Promise<{ templateId: string; name: string; updatedAt: string }> {
    const response = await api.put(`/instances/${instanceId}/templates/${templateId}`, updates);
    return response.data;
  },

  /**
   * Delete a template
   */
  async deleteTemplate(instanceId: string, templateId: string): Promise<{ message: string }> {
    const response = await api.delete(`/instances/${instanceId}/templates/${templateId}`);
    return response.data;
  },

  /**
   * Mark a template as used (increments usage count)
   */
  async useTemplate(
    instanceId: string,
    templateId: string
  ): Promise<{ templateId: string; usageCount: number }> {
    const response = await api.post(`/instances/${instanceId}/templates/${templateId}/use`);
    return response.data;
  },
};

// Export individual functions for convenience
export const {
  listTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  useTemplate,
} = instanceTemplateService;
