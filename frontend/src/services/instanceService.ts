import api from './api';

export interface AMCInstance {
  id: string;
  instanceId: string;
  instanceName: string;
  region: string;
  accountId: string;
  accountName: string;
  isActive: boolean;
  type: string;
  createdAt: string;
  brands?: string[];
  stats?: {
    totalCampaigns: number;
    totalWorkflows: number;
    activeWorkflows: number;
  };
}

class InstanceService {
  /**
   * Get all instances
   */
  async list(): Promise<AMCInstance[]> {
    const response = await api.get('/instances', {
      params: {
        limit: 100,
        offset: 0
      }
    });
    return response.data;
  }

  /**
   * Get a specific instance
   */
  async get(instanceId: string): Promise<AMCInstance> {
    const response = await api.get(`/instances/${instanceId}`);
    return response.data;
  }

  /**
   * Create a new instance
   */
  async create(data: Partial<AMCInstance>): Promise<AMCInstance> {
    const response = await api.post('/instances/', data);
    return response.data;
  }

  /**
   * Update an instance
   */
  async update(instanceId: string, data: Partial<AMCInstance>): Promise<AMCInstance> {
    const response = await api.put(`/instances/${instanceId}`, data);
    return response.data;
  }

  /**
   * Delete an instance
   */
  async delete(instanceId: string): Promise<void> {
    await api.delete(`/instances/${instanceId}`);
  }
}

export const instanceService = new InstanceService();