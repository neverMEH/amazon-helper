/**
 * TypeScript types for AI-powered insights and analysis
 * Corresponds to backend schemas in amc_manager/schemas/ai_schemas.py
 */

export type InsightCategory =
  | 'trend'
  | 'anomaly'
  | 'correlation'
  | 'performance'
  | 'optimization'
  | 'pattern'
  | 'forecast';

export type ChartType =
  | 'line'
  | 'bar'
  | 'pie'
  | 'area'
  | 'scatter'
  | 'table'
  | 'metric_card'
  | 'heatmap'
  | 'funnel';

export type ImpactLevel = 'low' | 'medium' | 'high';

export interface DataInsight {
  category: InsightCategory;
  title: string;
  description: string;
  confidence: number; // 0.0 to 1.0
  impact: ImpactLevel;
  recommendation?: string;
  supporting_data?: Record<string, any>;
  timestamp: string;
}

export interface StatisticalSummary {
  metrics: Record<string, Record<string, number>>;
  correlations: Record<string, number>;
  outliers: Record<string, number[]>;
  trends: Record<string, Record<string, any>>;
}

export interface ChartConfig {
  x_axis?: string;
  y_axis?: string[];
  x_axis_label?: string;
  y_axis_label?: string;
  color_palette: string[];
  enable_tooltips: boolean;
  enable_zoom: boolean;
  enable_legend: boolean;
  stacked: boolean;
  show_grid: boolean;
  animation_enabled: boolean;
}

export interface ChartRecommendation {
  chart_type: ChartType;
  confidence_score: number;
  reasoning: string;
  suggested_title: string;
  config: ChartConfig;
  optimization_tips: string[];
  warnings: string[];
  data_requirements?: Record<string, any>;
}

export interface AnalyzeDataResponse {
  insights: DataInsight[];
  statistical_summary: StatisticalSummary;
  recommendations: string[];
  metadata: Record<string, any>;
}

export interface RecommendChartsResponse {
  recommendations: ChartRecommendation[];
  metadata: Record<string, any>;
}

export interface GenerateInsightsResponse {
  data_analysis?: AnalyzeDataResponse;
  chart_recommendations?: ChartRecommendation[];
  metadata: Record<string, any>;
}

// Request types
export interface AnalyzeDataRequest {
  data: {
    columns: string[];
    rows: any[][];
  };
  analysis_type?: 'comprehensive' | 'trends_only' | 'anomalies_only';
  confidence_threshold?: number;
  max_insights?: number;
  include_forecasting?: boolean;
}

export interface RecommendChartsRequest {
  data: {
    columns: string[];
    rows: any[][];
  };
  max_recommendations?: number;
  min_confidence?: number;
}

export interface GenerateInsightsRequest {
  data: {
    columns: string[];
    rows: any[][];
  };
  include_charts?: boolean;
  include_analysis?: boolean;
  max_insights?: number;
  max_chart_recommendations?: number;
}
