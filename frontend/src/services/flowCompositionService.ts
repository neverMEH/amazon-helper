import api from './api';
import type { 
  FlowComposition, 
  FlowExecutionRequest, 
  FlowExecutionResult 
} from '../types/flowComposition';

export interface GetCompositionsParams {
  limit?: number;
  offset?: number;
}

export interface CreateCompositionData {
  name: string;
  description?: string;
  nodes: Array<{
    node_id: string;
    template_id: string;
    position: { x: number; y: number };
    config: Record<string, any>;
  }>;
  connections: Array<{
    source_node_id: string;
    target_node_id: string;
    parameter_mappings: Array<{
      source_param: string;
      target_param: string;
      transformation?: string;
    }>;
  }>;
}

class FlowCompositionService {
  async getCompositions(params?: GetCompositionsParams) {
    const response = await api.get('/api/flow-compositions/', { params });
    return response.data;
  }

  async getComposition(id: string): Promise<FlowComposition> {
    const response = await api.get(`/api/flow-compositions/${id}`);
    return response.data;
  }

  async createComposition(data: CreateCompositionData): Promise<FlowComposition> {
    const response = await api.post('/api/flow-compositions/', data);
    return response.data;
  }

  async updateComposition(id: string, data: Partial<CreateCompositionData>): Promise<FlowComposition> {
    const response = await api.put(`/api/flow-compositions/${id}`, data);
    return response.data;
  }

  async deleteComposition(id: string): Promise<void> {
    await api.delete(`/api/flow-compositions/${id}`);
  }

  async executeComposition(data: FlowExecutionRequest): Promise<FlowExecutionResult> {
    const response = await api.post('/api/flow-compositions/execute', data);
    return response.data;
  }

  async getExecutionStatus(executionId: string): Promise<FlowExecutionResult> {
    const response = await api.get(`/api/flow-executions/${executionId}`);
    return response.data;
  }

  async validateComposition(data: CreateCompositionData): Promise<{ valid: boolean; errors?: string[] }> {
    const response = await api.post('/api/flow-compositions/validate', data);
    return response.data;
  }
}

export const flowCompositionService = new FlowCompositionService();