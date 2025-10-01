import api from './api';
import type {
  AnalyzeDataRequest,
  AnalyzeDataResponse,
  RecommendChartsRequest,
  RecommendChartsResponse,
  GenerateInsightsRequest,
  GenerateInsightsResponse,
} from '../types/ai';

/**
 * AI Service
 * Provides API client methods for all AI-powered analytics endpoints
 */

export const aiService = {
  /**
   * Analyze data and generate insights
   * POST /api/ai/analyze-data
   */
  analyzeData: async (request: AnalyzeDataRequest): Promise<AnalyzeDataResponse> => {
    const response = await api.post<AnalyzeDataResponse>('/ai/analyze-data', request);
    return response.data;
  },

  /**
   * Get chart recommendations for data
   * POST /api/ai/recommend-charts
   */
  recommendCharts: async (
    request: RecommendChartsRequest
  ): Promise<RecommendChartsResponse> => {
    const response = await api.post<RecommendChartsResponse>('/ai/recommend-charts', request);
    return response.data;
  },

  /**
   * Generate combined insights (data analysis + chart recommendations)
   * POST /api/ai/generate-insights
   */
  generateInsights: async (
    request: GenerateInsightsRequest
  ): Promise<GenerateInsightsResponse> => {
    const response = await api.post<GenerateInsightsResponse>('/ai/generate-insights', request);
    return response.data;
  },
};

export default aiService;
