/**
 * Data Collection Service
 * Handles API calls for historical data collection operations
 */

import api from './api';
import type { CollectionResponse, CollectionProgress, CollectionCreate } from '../types/dataCollection';

class DataCollectionService {
  /**
   * Start a new data collection
   */
  async createCollection(data: CollectionCreate): Promise<CollectionResponse> {
    const response = await api.post('/api/data-collections/', data);
    return response.data;
  }

  /**
   * List all collections for the current user
   */
  async listCollections(params?: {
    status?: string;
    workflow_id?: string;
    limit?: number;
  }): Promise<CollectionResponse[]> {
    const response = await api.get('/api/data-collections/', { params });
    return response.data;
  }

  /**
   * Get detailed progress for a specific collection
   */
  async getCollectionProgress(collectionId: string): Promise<CollectionProgress> {
    const response = await api.get(`/api/data-collections/${collectionId}`);
    return response.data;
  }

  /**
   * Pause an active collection
   */
  async pauseCollection(collectionId: string): Promise<{ message: string; status: string }> {
    const response = await api.post(`/api/data-collections/${collectionId}/pause`);
    return response.data;
  }

  /**
   * Resume a paused collection
   */
  async resumeCollection(collectionId: string): Promise<{ message: string; status: string }> {
    const response = await api.post(`/api/data-collections/${collectionId}/resume`);
    return response.data;
  }

  /**
   * Cancel and delete a collection
   */
  async cancelCollection(collectionId: string): Promise<{ message: string; status: string }> {
    const response = await api.delete(`/api/data-collections/${collectionId}`);
    return response.data;
  }

  /**
   * Retry failed weeks in a collection
   */
  async retryFailedWeeks(collectionId: string): Promise<{
    message: string;
    failed_count: number;
    retrying: Array<{ week_start: string; week_end: string }>;
  }> {
    const response = await api.post(`/api/data-collections/${collectionId}/retry-failed`);
    return response.data;
  }
}

export const dataCollectionService = new DataCollectionService();