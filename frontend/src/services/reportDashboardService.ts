import api from './api';

export interface DashboardData {
  collection: {
    id: string;
    name: string;
    workflow_id: string;
    instance_id: string;
    status: string;
    created_at: string;
    weeks_completed: number;
    weeks_failed: number;
    weeks_pending: number;
  };
  weeks: WeekData[];
  summary: SummaryStats | null;
  chartData: ChartData | null;
}

export interface WeekData {
  id: string;
  week_number: number;
  week_start: string;
  week_end: string;
  status: string;
  execution_results?: {
    metrics: Record<string, number>;
  };
}

export interface SummaryStats {
  total_impressions: number;
  total_clicks: number;
  total_conversions: number;
  total_spend: number;
  avg_ctr: number;
  avg_cvr: number;
  avg_cpc: number;
  [key: string]: number;
}

export interface ChartData {
  line?: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      borderColor: string;
      backgroundColor: string;
      tension?: number;
    }>;
  };
  bar?: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      backgroundColor: string | string[];
      borderColor?: string | string[];
      borderWidth?: number;
    }>;
  };
  pie?: {
    labels: string[];
    datasets: Array<{
      data: number[];
      backgroundColor: string[];
      borderColor?: string[];
      borderWidth?: number;
    }>;
  };
  area?: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      fill: boolean;
      backgroundColor: string;
      borderColor: string;
    }>;
  };
}

export interface ComparisonData {
  period1: {
    weeks: WeekData[];
    summary: SummaryStats;
  };
  period2: {
    weeks: WeekData[];
    summary: SummaryStats;
  };
  changes: {
    [key: string]: number;
  };
}

export interface DashboardConfig {
  id?: string;
  name: string;
  chartTypes: string[];
  metrics: string[];
  groupBy?: string;
  filters?: Record<string, any>;
  layout?: {
    columns: number;
    widgets: Array<{
      type: string;
      position: { x: number; y: number; w: number; h: number };
      config: Record<string, any>;
    }>;
  };
}

export interface DashboardSnapshot {
  id: string;
  name: string;
  description?: string;
  data: DashboardData;
  config: DashboardConfig;
  created_at: string;
  shared_with?: string[];
}

export interface DashboardFilters {
  weeks?: string[];
  metrics?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  aggregation?: 'sum' | 'avg' | 'min' | 'max';
}

// Get dashboard data for a collection
export async function getDashboardData(
  collectionId: string,
  filters?: DashboardFilters
): Promise<DashboardData> {
  const params = new URLSearchParams();
  
  if (filters?.weeks) {
    params.append('weeks', filters.weeks.join(','));
  }
  if (filters?.metrics) {
    params.append('metrics', filters.metrics.join(','));
  }
  if (filters?.dateRange) {
    params.append('start_date', filters.dateRange.start);
    params.append('end_date', filters.dateRange.end);
  }
  if (filters?.aggregation) {
    params.append('aggregation', filters.aggregation);
  }

  const queryString = params.toString();
  const url = `/collections/${collectionId}/report-dashboard${queryString ? `?${queryString}` : ''}`;
  
  const response = await api.get(url);
  return response.data;
}

// Compare two periods
export async function comparePeriods(
  collectionId: string,
  period1Weeks: string[],
  period2Weeks: string[]
): Promise<ComparisonData> {
  const response = await api.post(`/collections/${collectionId}/report-dashboard/compare`, {
    period1_weeks: period1Weeks,
    period2_weeks: period2Weeks,
  });
  return response.data;
}

// Get chart data in specific format
export async function getChartData(
  collectionId: string,
  chartType: 'line' | 'bar' | 'pie' | 'area' | 'scatter',
  metrics: string[],
  options?: {
    groupBy?: string;
    weeks?: string[];
  }
): Promise<ChartData> {
  const response = await api.post(`/collections/${collectionId}/report-dashboard/chart`, {
    chart_type: chartType,
    metrics,
    group_by: options?.groupBy,
    weeks: options?.weeks,
  });
  return response.data;
}

// Save dashboard configuration
export async function saveDashboardConfig(
  collectionId: string,
  config: DashboardConfig
): Promise<DashboardConfig> {
  const response = await api.post(`/collections/${collectionId}/report-dashboard/config`, config);
  return response.data;
}

// Get dashboard configurations
export async function getDashboardConfigs(collectionId: string): Promise<DashboardConfig[]> {
  const response = await api.get(`/collections/${collectionId}/report-dashboard/configs`);
  return response.data;
}

// Update dashboard configuration
export async function updateDashboardConfig(
  collectionId: string,
  configId: string,
  config: Partial<DashboardConfig>
): Promise<DashboardConfig> {
  const response = await api.put(`/collections/${collectionId}/report-dashboard/config/${configId}`, config);
  return response.data;
}

// Delete dashboard configuration
export async function deleteDashboardConfig(
  collectionId: string,
  configId: string
): Promise<void> {
  await api.delete(`/collections/${collectionId}/report-dashboard/config/${configId}`);
}

// Create a snapshot of the dashboard
export async function createSnapshot(
  collectionId: string,
  snapshot: {
    name: string;
    description?: string;
    data: DashboardData;
    config: DashboardConfig;
  }
): Promise<DashboardSnapshot> {
  const response = await api.post(`/collections/${collectionId}/report-dashboard/snapshot`, snapshot);
  return response.data;
}

// Get dashboard snapshots
export async function getSnapshots(collectionId: string): Promise<DashboardSnapshot[]> {
  const response = await api.get(`/collections/${collectionId}/report-dashboard/snapshots`);
  return response.data;
}

// Get a specific snapshot
export async function getSnapshot(
  collectionId: string,
  snapshotId: string
): Promise<DashboardSnapshot> {
  const response = await api.get(`/collections/${collectionId}/report-dashboard/snapshot/${snapshotId}`);
  return response.data;
}

// Delete a snapshot
export async function deleteSnapshot(
  collectionId: string,
  snapshotId: string
): Promise<void> {
  await api.delete(`/collections/${collectionId}/report-dashboard/snapshot/${snapshotId}`);
}

// Export dashboard as PDF or image
export async function exportDashboard(
  collectionId: string,
  format: 'pdf' | 'png' | 'csv',
  options?: {
    includeCharts?: boolean;
    includeTables?: boolean;
    dateRange?: { start: string; end: string };
  }
): Promise<Blob> {
  const response = await api.post(
    `/collections/${collectionId}/report-dashboard/export`,
    {
      format,
      ...options,
    },
    {
      responseType: 'blob',
    }
  );
  return response.data;
}

// Get available metrics for a collection
export async function getAvailableMetrics(collectionId: string): Promise<string[]> {
  const response = await api.get(`/collections/${collectionId}/report-dashboard/metrics`);
  return response.data;
}

// Get aggregated data for specific metrics
export async function getAggregatedData(
  collectionId: string,
  metrics: string[],
  aggregation: 'sum' | 'avg' | 'min' | 'max',
  groupBy?: 'week' | 'month' | 'quarter'
): Promise<Record<string, any>> {
  const response = await api.post(`/collections/${collectionId}/report-dashboard/aggregate`, {
    metrics,
    aggregation,
    group_by: groupBy,
  });
  return response.data;
}

// Get trend analysis
export async function getTrendAnalysis(
  collectionId: string,
  metric: string,
  options?: {
    smoothing?: 'none' | 'moving_average' | 'exponential';
    window?: number;
  }
): Promise<{
  trend: 'increasing' | 'decreasing' | 'stable';
  slope: number;
  forecast?: number[];
  confidence?: number;
}> {
  const response = await api.post(`/collections/${collectionId}/report-dashboard/trend`, {
    metric,
    ...options,
  });
  return response.data;
}

// Share dashboard with other users
export async function shareDashboard(
  collectionId: string,
  userIds: string[],
  permissions: 'view' | 'edit'
): Promise<void> {
  await api.post(`/collections/${collectionId}/report-dashboard/share`, {
    user_ids: userIds,
    permissions,
  });
}

// Get shared users for a dashboard
export async function getSharedUsers(collectionId: string): Promise<Array<{
  user_id: string;
  email: string;
  permissions: string;
  shared_at: string;
}>> {
  const response = await api.get(`/collections/${collectionId}/report-dashboard/shares`);
  return response.data;
}

// Revoke dashboard sharing
export async function revokeShare(
  collectionId: string,
  userId: string
): Promise<void> {
  await api.delete(`/collections/${collectionId}/report-dashboard/share/${userId}`);
}