/**
 * Build Guide Service
 * Handles API communication for Build Guides feature
 */

import api from './api';
import type {
  BuildGuide,
  BuildGuideListItem,
  UserGuideProgress,
  GuideProgressUpdate,
  GuideQueryExecution,
  GuideQueryExecutionResult
} from '../types/buildGuide';

class BuildGuideService {
  /**
   * List all available build guides
   */
  async listGuides(category?: string, showUnpublished = false): Promise<BuildGuideListItem[]> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (showUnpublished) params.append('show_unpublished', 'true');
    
    const response = await api.get(`/build-guides/?${params}`);
    return response.data;
  }

  /**
   * Get all available guide categories
   */
  async getCategories(): Promise<string[]> {
    const response = await api.get('/build-guides/categories');
    return response.data;
  }

  /**
   * Get a specific guide with all content
   */
  async getGuide(guideId: string): Promise<BuildGuide> {
    const response = await api.get(`/build-guides/${guideId}`);
    return response.data;
  }

  /**
   * Get queries for a specific guide
   */
  async getGuideQueries(guideId: string): Promise<any[]> {
    const response = await api.get(`/build-guides/${guideId}/queries`);
    return response.data;
  }

  /**
   * Start or resume a guide
   */
  async startGuide(guideId: string): Promise<UserGuideProgress> {
    const response = await api.post(`/build-guides/${guideId}/start`);
    return response.data;
  }

  /**
   * Update progress on a guide
   */
  async updateProgress(
    guideId: string,
    update: GuideProgressUpdate
  ): Promise<UserGuideProgress> {
    const response = await api.put(`/build-guides/${guideId}/progress`, update);
    return response.data;
  }

  /**
   * Execute a query from a guide
   */
  async executeQuery(
    guideId: string,
    queryId: string,
    execution: GuideQueryExecution
  ): Promise<GuideQueryExecutionResult> {
    const response = await api.post(
      `/build-guides/${guideId}/queries/${queryId}/execute`,
      execution
    );
    return response.data;
  }

  /**
   * Create a template from a guide query
   */
  async createTemplateFromQuery(guideId: string, queryId: string): Promise<any> {
    const response = await api.post(
      `/build-guides/${guideId}/queries/${queryId}/create-template`
    );
    return response.data;
  }

  /**
   * Toggle favorite status for a guide
   */
  async toggleFavorite(guideId: string): Promise<{ is_favorite: boolean }> {
    const response = await api.post(`/build-guides/${guideId}/favorite`);
    return response.data;
  }

  /**
   * Get user's progress on all guides
   */
  async getUserProgress(): Promise<UserGuideProgress[]> {
    const response = await api.get('/build-guides/user/progress');
    return response.data;
  }

  /**
   * Get a specific section of a guide
   */
  async getGuideSection(guideId: string, sectionId: string): Promise<any> {
    const response = await api.get(`/build-guides/${guideId}/sections/${sectionId}`);
    return response.data;
  }

  /**
   * Mark a section as completed
   */
  async markSectionComplete(guideId: string, sectionId: string): Promise<UserGuideProgress> {
    return this.updateProgress(guideId, { section_id: sectionId });
  }

  /**
   * Mark a query as executed
   */
  async markQueryExecuted(guideId: string, queryId: string): Promise<UserGuideProgress> {
    return this.updateProgress(guideId, { query_id: queryId });
  }

  /**
   * Mark entire guide as complete
   */
  async markGuideComplete(guideId: string): Promise<UserGuideProgress> {
    return this.updateProgress(guideId, { mark_complete: true });
  }

  /**
   * Get guides filtered by user progress status
   */
  async getGuidesByStatus(status: 'not_started' | 'in_progress' | 'completed'): Promise<BuildGuideListItem[]> {
    const guides = await this.listGuides();
    return guides.filter(guide => guide.user_progress?.status === status);
  }

  /**
   * Get favorite guides
   */
  async getFavoriteGuides(): Promise<BuildGuideListItem[]> {
    const guides = await this.listGuides();
    return guides.filter(guide => guide.is_favorite);
  }

  /**
   * Calculate estimated time to complete remaining guides
   */
  calculateRemainingTime(guides: BuildGuideListItem[]): number {
    return guides
      .filter(guide => guide.user_progress?.status !== 'completed')
      .reduce((total, guide) => {
        const completed = guide.user_progress?.progress_percentage || 0;
        const remaining = (100 - completed) / 100;
        return total + (guide.estimated_time_minutes * remaining);
      }, 0);
  }

  /**
   * Get guide statistics for dashboard
   */
  async getGuideStatistics(): Promise<{
    total: number;
    completed: number;
    in_progress: number;
    not_started: number;
    total_time_minutes: number;
    completed_time_minutes: number;
  }> {
    const guides = await this.listGuides();
    
    const stats = {
      total: guides.length,
      completed: 0,
      in_progress: 0,
      not_started: 0,
      total_time_minutes: 0,
      completed_time_minutes: 0
    };
    
    guides.forEach(guide => {
      stats.total_time_minutes += guide.estimated_time_minutes;
      
      const status = guide.user_progress?.status || 'not_started';
      if (status === 'completed') {
        stats.completed++;
        stats.completed_time_minutes += guide.estimated_time_minutes;
      } else if (status === 'in_progress') {
        stats.in_progress++;
        const progress = guide.user_progress?.progress_percentage || 0;
        stats.completed_time_minutes += (guide.estimated_time_minutes * progress / 100);
      } else {
        stats.not_started++;
      }
    });
    
    return stats;
  }
}

export const buildGuideService = new BuildGuideService();