import api from './api';
import type { AMCExecution, AMCExecutionDetail } from '../types/amcExecution';

export const amcExecutionService = {
  /**
   * List all AMC workflow executions for an instance
   */
  async listExecutions(instanceId: string, limit: number = 50): Promise<{
    success: boolean;
    executions: AMCExecution[];
    total: number;
  }> {
    const response = await api.get(`/amc-executions/${instanceId}`, {
      params: { limit }
    });
    return response.data;
  },

  /**
   * Get details for a specific AMC execution
   */
  async getExecutionDetails(instanceId: string, executionId: string): Promise<{
    success: boolean;
    execution: AMCExecutionDetail;
  }> {
    const response = await api.get(`/amc-executions/${instanceId}/${executionId}`);
    return response.data;
  }
};