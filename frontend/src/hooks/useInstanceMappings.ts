import { useQuery } from '@tanstack/react-query';
import instanceMappingService, { type InstanceMappings } from '../services/instanceMappingService';

/**
 * Custom hook to fetch and cache instance parameter mappings
 * Used for auto-populating query parameters based on instance configuration
 *
 * @param instanceId - The AMC instance ID to fetch mappings for
 * @param enabled - Whether to enable the query (default: true)
 * @returns Query result with mappings, loading state, error, and refetch function
 */
export function useInstanceMappings(instanceId: string | null | undefined, enabled: boolean = true) {
  return useQuery<InstanceMappings | null>({
    queryKey: ['instanceMappings', instanceId],
    queryFn: async () => {
      if (!instanceId) return null;
      return await instanceMappingService.getInstanceMappings(instanceId);
    },
    enabled: enabled && !!instanceId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000,   // 10 minutes (previously cacheTime)
    retry: 1,
  });
}

/**
 * Custom hook to fetch parameter values formatted for auto-population
 * Returns ready-to-use parameter arrays for brands, ASINs, and campaigns
 *
 * @param instanceId - The AMC instance ID to fetch parameter values for
 * @param enabled - Whether to enable the query (default: true)
 * @returns Query result with formatted parameter values
 */
export function useInstanceParameterValues(instanceId: string | null | undefined, enabled: boolean = true) {
  return useQuery({
    queryKey: ['instanceParameterValues', instanceId],
    queryFn: async () => {
      if (!instanceId) return null;
      return await instanceMappingService.getParameterValues(instanceId);
    },
    enabled: enabled && !!instanceId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000,   // 10 minutes
    retry: 1,
  });
}
