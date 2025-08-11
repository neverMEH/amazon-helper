import api from './api';

export interface BatchExecuteRequest {
  instanceIds: string[];
  parameters: Record<string, any>;
  instanceParameters?: Record<string, Record<string, any>>;
  name?: string;
  description?: string;
}

export interface BatchExecution {
  batchId: string;
  batchExecutionId: string;
  workflowId: string;
  totalInstances: number;
  status: 'pending' | 'running' | 'completed' | 'partial' | 'failed';
  executions: {
    instanceId: string;
    executionId?: string;
    status: string;
    error?: string;
  }[];
}

export interface BatchStatus {
  batchId: string;
  workflowId: string;
  name: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'partial' | 'failed';
  totalInstances: number;
  completedInstances: number;
  failedInstances: number;
  runningInstances: number;
  pendingInstances: number;
  startedAt?: string;
  completedAt?: string;
  executions: any[];
  statusCounts: Record<string, number>;
}

export interface BatchResults {
  batchId: string;
  status: string;
  totalInstances: number;
  completedInstances: number;
  failedInstances: number;
  instanceResults: {
    instanceId: string;
    instanceName: string;
    instanceRegion?: string;
    executionId: string;
    rowCount: number;
    durationSeconds?: number;
    completedAt?: string;
  }[];
  aggregatedData?: {
    columns: { name: string; type: string }[];
    rows: any[];
    totalRows: number;
  };
}

class WorkflowService {
  /**
   * Execute a workflow on a single instance
   */
  async executeWorkflow(workflowId: string, instanceId: string, parameters: Record<string, any>) {
    const response = await api.post(`/workflows/${workflowId}/execute`, {
      instance_id: instanceId,
      execution_parameters: parameters
    });
    return response.data;
  }

  /**
   * Execute a workflow across multiple instances as a batch
   */
  async batchExecuteWorkflow(workflowId: string, request: BatchExecuteRequest): Promise<BatchExecution> {
    const response = await api.post(`/workflows/${workflowId}/batch-execute`, {
      instance_ids: request.instanceIds,
      parameters: request.parameters,
      instance_parameters: request.instanceParameters,
      name: request.name,
      description: request.description
    });
    return response.data.batch;
  }

  /**
   * Get the status of a batch execution
   */
  async getBatchStatus(batchId: string): Promise<BatchStatus> {
    const response = await api.get(`/workflows/batch/${batchId}/status`);
    return response.data.batch_status;
  }

  /**
   * Get the results of a batch execution
   */
  async getBatchResults(batchId: string): Promise<BatchResults> {
    const response = await api.get(`/workflows/batch/${batchId}/results`);
    return response.data.batch_results;
  }

  /**
   * Cancel a batch execution
   */
  async cancelBatchExecution(batchId: string): Promise<boolean> {
    const response = await api.post(`/workflows/batch/${batchId}/cancel`);
    return response.data.success;
  }

  /**
   * List batch executions with optional filters
   */
  async listBatchExecutions(params?: {
    workflowId?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) {
    const response = await api.get('/workflows/batch/list', { params });
    return response.data;
  }

  /**
   * Get execution status for a single execution
   */
  async getExecutionStatus(executionId: string) {
    const response = await api.get(`/workflows/executions/${executionId}/status`);
    return response.data;
  }

  /**
   * Get execution details for a single execution
   */
  async getExecutionDetail(executionId: string) {
    const response = await api.get(`/workflows/executions/${executionId}/detail`);
    return response.data;
  }

  /**
   * Get execution results for a single execution
   */
  async getExecutionResults(executionId: string) {
    const response = await api.get(`/workflows/executions/${executionId}/results`);
    return response.data;
  }

  /**
   * Get all workflows
   */
  async getWorkflows(params?: { instance_id?: string; status?: string }) {
    const response = await api.get('/workflows', { params });
    return response.data;
  }

  /**
   * Get a specific workflow
   */
  async getWorkflow(workflowId: string) {
    const response = await api.get(`/workflows/${workflowId}`);
    return response.data;
  }

  /**
   * Create a new workflow
   */
  async createWorkflow(data: {
    name: string;
    description?: string;
    instance_id: string;
    sql_query: string;
    parameters?: Record<string, any>;
    tags?: string[];
    template_id?: string;
  }) {
    const response = await api.post('/workflows/', data);
    return response.data;
  }

  /**
   * Update a workflow
   */
  async updateWorkflow(workflowId: string, data: {
    name?: string;
    description?: string;
    sql_query?: string;
    parameters?: Record<string, any>;
    tags?: string[];
    status?: string;
  }) {
    const response = await api.put(`/workflows/${workflowId}`, data);
    return response.data;
  }

  /**
   * Delete a workflow
   */
  async deleteWorkflow(workflowId: string) {
    const response = await api.delete(`/workflows/${workflowId}`);
    return response.data;
  }

  /**
   * Get workflow executions
   */
  async getWorkflowExecutions(workflowId: string, params?: { 
    limit?: number; 
    offset?: number; 
    status?: string 
  }) {
    const response = await api.get(`/workflows/${workflowId}/executions`, { params });
    return response.data;
  }
}

export const workflowService = new WorkflowService();