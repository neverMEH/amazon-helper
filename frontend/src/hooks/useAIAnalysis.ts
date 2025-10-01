import { useMutation, useQueryClient } from '@tanstack/react-query';
import { aiService } from '../services/aiService';
import type {
  AnalyzeDataRequest,
  AnalyzeDataResponse,
  RecommendChartsRequest,
  RecommendChartsResponse,
  GenerateInsightsRequest,
  GenerateInsightsResponse,
} from '../types/ai';

/**
 * Hook for analyzing data and generating insights
 * Uses mutation since this is a POST request that generates new data
 */
export function useAIAnalysis() {
  const queryClient = useQueryClient();

  return useMutation<AnalyzeDataResponse, Error, AnalyzeDataRequest>({
    mutationFn: aiService.analyzeData,
    onSuccess: (data) => {
      // Cache the results for potential reuse
      queryClient.setQueryData(['ai-analysis', data.metadata], data);
    },
    retry: 2, // Retry failed requests up to 2 times
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
  });
}

/**
 * Hook for getting chart recommendations
 * Uses mutation since this is a POST request
 */
export function useChartRecommendations() {
  const queryClient = useQueryClient();

  return useMutation<RecommendChartsResponse, Error, RecommendChartsRequest>({
    mutationFn: aiService.recommendCharts,
    onSuccess: (data) => {
      // Cache the results
      queryClient.setQueryData(['chart-recommendations', data.metadata], data);
    },
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}

/**
 * Hook for generating combined insights (analysis + chart recommendations)
 * This is more efficient than calling both endpoints separately
 */
export function useGenerateInsights() {
  const queryClient = useQueryClient();

  return useMutation<GenerateInsightsResponse, Error, GenerateInsightsRequest>({
    mutationFn: aiService.generateInsights,
    onSuccess: (data) => {
      // Cache both analysis and chart recommendations separately
      if (data.data_analysis) {
        queryClient.setQueryData(['ai-analysis', data.metadata], data.data_analysis);
      }
      if (data.chart_recommendations) {
        queryClient.setQueryData(['chart-recommendations', data.metadata], {
          recommendations: data.chart_recommendations,
          metadata: data.metadata,
        });
      }
      // Cache the combined result
      queryClient.setQueryData(['combined-insights', data.metadata], data);
    },
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}

/**
 * Helper hook to check if AI features are available
 * Can be used to show/hide AI features based on API availability
 */
export function useAIAvailability() {
  // Could add a health check endpoint in the future
  // For now, assume AI is available
  return {
    isAvailable: true,
    isLoading: false,
    error: null,
  };
}
