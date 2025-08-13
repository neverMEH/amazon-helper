import { useQuery, useQueries } from '@tanstack/react-query';
import { useMemo } from 'react';
import api from '../services/api';

interface ExecutionDataOptions {
  executionId: string;
  includeResults?: boolean;
  includeStatus?: boolean;
  includeDetail?: boolean;
  pollInterval?: number;
}

export function useExecutionData({
  executionId,
  includeResults = false,
  includeStatus = true,
  includeDetail = true,
  pollInterval = 2000
}: ExecutionDataOptions) {
  // Fetch execution detail
  const detailQuery = useQuery({
    queryKey: ['execution-detail', executionId],
    queryFn: async () => {
      const response = await api.get(`/workflows/executions/${executionId}/detail`);
      return response.data;
    },
    enabled: includeDetail && !!executionId,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
  });

  // Fetch execution status with polling
  const statusQuery = useQuery({
    queryKey: ['execution-status', executionId],
    queryFn: async () => {
      const response = await api.get(`/workflows/executions/${executionId}/status`);
      return response.data;
    },
    enabled: includeStatus && !!executionId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'running' || status === 'pending' ? pollInterval : false;
    },
    staleTime: 0, // Always consider stale for polling
  });

  // Fetch results only when completed
  const resultsQuery = useQuery({
    queryKey: ['execution-results', executionId],
    queryFn: async () => {
      const response = await api.get(`/workflows/executions/${executionId}/results`);
      return response.data;
    },
    enabled: includeResults && statusQuery.data?.status === 'completed',
    staleTime: 10 * 60 * 1000, // Results don't change, cache for 10 minutes
    gcTime: 30 * 60 * 1000, // Keep in cache for 30 minutes
  });

  // Memoize processed data
  const processedData = useMemo(() => {
    if (!resultsQuery.data) return null;
    
    const { columns, rows } = resultsQuery.data as any;
    
    // Transform rows to objects for easier manipulation
    const transformedData = rows.map((row: any) => {
      const obj: any = {};
      columns.forEach((col: any, idx: number) => {
        obj[col.name] = row[idx];
      });
      return obj;
    });

    // Calculate statistics
    const stats = {
      totalRows: resultsQuery.data.total_rows || rows.length,
      sampleSize: resultsQuery.data.sample_size || rows.length,
      columns: columns.length,
      numericColumns: columns.filter((col: any) => col.type === 'number' || col.type === 'integer').length,
      execution_details: resultsQuery.data.execution_details
    };

    return {
      data: transformedData,
      columns: columns.map((c: any) => c.name),
      stats
    };
  }, [resultsQuery.data]);

  return {
    detail: detailQuery.data,
    status: statusQuery.data,
    results: resultsQuery.data,
    processedData,
    isLoading: detailQuery.isLoading || statusQuery.isLoading || resultsQuery.isLoading,
    isError: detailQuery.isError || statusQuery.isError || resultsQuery.isError,
    error: detailQuery.error || statusQuery.error || resultsQuery.error,
    refetch: () => {
      detailQuery.refetch();
      statusQuery.refetch();
      if (includeResults) resultsQuery.refetch();
    }
  };
}

// Hook for batch fetching multiple executions
export function useExecutionsBatch(executionIds: string[]) {
  const queries = useQueries({
    queries: executionIds.map(id => ({
      queryKey: ['execution-status', id],
      queryFn: async () => {
        const response = await api.get(`/workflows/executions/${id}/status`);
        return { ...response.data, execution_id: id };
      },
      staleTime: 5 * 60 * 1000,
    }))
  });

  const data = useMemo(() => {
    return queries.map(q => q.data).filter(Boolean);
  }, [queries]);

  const isLoading = queries.some(q => q.isLoading);
  const isError = queries.some(q => q.isError);

  return {
    data,
    isLoading,
    isError
  };
}