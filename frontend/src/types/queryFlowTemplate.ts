/**
 * Types for Query Flow Templates
 */

// Parameter types
export type ParameterType = 
  | 'date' 
  | 'date_range' 
  | 'string' 
  | 'number' 
  | 'boolean' 
  | 'campaign_list' 
  | 'asin_list' 
  | 'string_list';

// Parameter validation rules
export interface ParameterValidationRules {
  // Date validation
  min?: string;
  max?: string;
  allow_future?: boolean;
  
  // Date range validation
  min_days?: number;
  max_days?: number;
  
  // String validation
  min_length?: number;
  max_length?: number;
  pattern?: string;
  
  // Number validation
  min_value?: number;
  max_value?: number;
  type?: 'integer' | 'float';
  
  // List validation
  min_selections?: number;
  max_selections?: number;
  min_items?: number;
  max_items?: number;
  allow_all?: boolean;
}

// Date range preset types
export interface DateRangePreset {
  label: string;
  value: string;
}

// Parameter UI configuration
export interface ParameterUIConfig {
  placeholder?: string;
  help_text?: string;
  show_presets?: boolean;
  presets?: DateRangePreset[];
  multi_select?: boolean;
  show_all_option?: boolean;
  allow_add?: boolean;
  allow_remove?: boolean;
  multiline?: boolean;
  display_style?: 'toggle' | 'buttons';
  input_mode?: 'bulk' | 'single';
}

// Template parameter definition
export interface TemplateParameter {
  id?: string;
  template_id?: string;
  parameter_name: string;
  display_name: string;
  parameter_type: ParameterType;
  required: boolean;
  default_value?: any;
  validation_rules: ParameterValidationRules;
  ui_component: string;
  ui_config: ParameterUIConfig;
  dependencies?: string[];
  order_index: number;
}

// Chart types
export type ChartType = 
  | 'line' 
  | 'bar' 
  | 'pie' 
  | 'scatter' 
  | 'table' 
  | 'heatmap' 
  | 'funnel' 
  | 'area' 
  | 'combo';

// Chart data mapping
export interface ChartDataMapping {
  x_field?: string;
  y_field?: string;
  y_fields?: string[];
  series_field?: string;
  value_format?: 'number' | 'percentage' | 'currency' | 'date' | 'string';
  date_format?: string;
  aggregation?: 'sum' | 'avg' | 'count' | 'min' | 'max' | null;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  limit?: number;
  color_scheme?: string;
}

// Chart configuration
export interface ChartConfig {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  indexAxis?: 'x' | 'y';
  plugins?: any;
  scales?: any;
  columns?: Array<{
    field: string;
    header: string;
    format: string;
  }>;
  pagination?: boolean;
  pageSize?: number;
  sortable?: boolean;
  filterable?: boolean;
  exportable?: boolean;
}

// Template chart configuration
export interface TemplateChartConfig {
  id?: string;
  template_id?: string;
  chart_name: string;
  chart_type: ChartType;
  chart_config: ChartConfig;
  data_mapping: ChartDataMapping;
  is_default: boolean;
  order_index: number;
}

// Query flow template
export interface QueryFlowTemplate {
  id: string;
  template_id: string;
  name: string;
  description?: string;
  category: string;
  sql_template: string;
  is_active: boolean;
  is_public: boolean;
  version: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
  execution_count: number;
  avg_execution_time_ms?: number;
  tags: string[];
  metadata?: Record<string, any>;
  
  // Related data
  parameters?: TemplateParameter[];
  chart_configs?: TemplateChartConfig[];
  
  // User-specific data
  is_favorite?: boolean;
  rating_info?: {
    avg_rating: number;
    rating_count: number;
  };
  user_rating?: {
    rating: number;
    review?: string;
  };
}

// Template execution
export interface TemplateExecution {
  id: string;
  template_id: string;
  user_id: string;
  instance_id: string;
  parameters_used: Record<string, any>;
  workflow_id?: string;
  execution_id?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  result_summary?: {
    row_count?: number;
    data_scanned_gb?: number;
  };
  execution_time_ms?: number;
  error_details?: any;
  created_at: string;
  completed_at?: string;
}

// API request/response types
export interface TemplateListResponse {
  templates: QueryFlowTemplate[];
  total_count: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface ExecuteTemplateRequest {
  instance_id: string;
  parameters: Record<string, any>;
  schedule_id?: string;
}

export interface ExecuteTemplateResponse {
  execution_id: string;
  template_id: string;
  workflow_id: string;
  status: string;
  created_at: string;
  message: string;
}

export interface ValidateParametersRequest {
  parameters: Record<string, any>;
}

export interface ValidateParametersResponse {
  valid: boolean;
  processed_parameters?: Record<string, any>;
  errors?: string[];
}

export interface PreviewSQLRequest {
  parameters: Record<string, any>;
}

export interface PreviewSQLResponse {
  sql: string;
  parameter_count: number;
  estimated_cost?: number;
}

// Form value types
export interface DateRangeValue {
  start: string;
  end: string;
  preset?: string;
}

export interface ParameterFormValues {
  [key: string]: any;
}

// Parameter input props (for components)
export interface BaseParameterInputProps {
  parameter: TemplateParameter;
  value: any;
  onChange: (value: any) => void;
  onError?: (error: string | null) => void;
  disabled?: boolean;
  className?: string;
}