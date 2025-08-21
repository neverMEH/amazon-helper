/**
 * TypeScript types for Build Guides feature
 */

export interface BuildGuide {
  id: string;
  guide_id: string;
  name: string;
  category: string;
  short_description?: string;
  tags: string[];
  icon?: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  estimated_time_minutes: number;
  prerequisites: string[];
  is_published: boolean;
  display_order: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
  
  // Relations
  sections?: BuildGuideSection[];
  queries?: BuildGuideQuery[];
  metrics?: BuildGuideMetric[];
  user_progress?: UserGuideProgress;
  is_favorite?: boolean;
}

export interface BuildGuideSection {
  id: string;
  guide_id: string;
  section_id: string;
  title: string;
  content_markdown: string;
  display_order: number;
  is_collapsible: boolean;
  default_expanded: boolean;
  created_at: string;
  updated_at: string;
}

export interface BuildGuideQuery {
  id: string;
  guide_id: string;
  query_template_id?: string;
  title: string;
  description?: string;
  sql_query: string;
  parameters_schema: Record<string, any>;
  default_parameters: Record<string, any>;
  display_order: number;
  query_type: 'exploratory' | 'main_analysis' | 'validation';
  expected_columns?: Record<string, any>;
  interpretation_notes?: string;
  created_at: string;
  updated_at: string;
  
  // Relations
  examples?: BuildGuideExample[];
}

export interface BuildGuideExample {
  id: string;
  guide_query_id: string;
  example_name: string;
  sample_data: any;
  interpretation_markdown?: string;
  insights: string[];
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface BuildGuideMetric {
  id: string;
  guide_id: string;
  metric_name: string;
  display_name: string;
  definition: string;
  metric_type: 'metric' | 'dimension';
  display_order: number;
  created_at: string;
}

export interface UserGuideProgress {
  id: string;
  user_id: string;
  guide_id: string;
  status: 'not_started' | 'in_progress' | 'completed';
  current_section?: string;
  completed_sections: string[];
  executed_queries: string[];
  started_at?: string;
  completed_at?: string;
  last_accessed_at: string;
  progress_percentage: number;
}

export interface UserGuideProgressSummary {
  status: 'not_started' | 'in_progress' | 'completed';
  progress_percentage: number;
}

export interface GuideProgressUpdate {
  section_id?: string;
  query_id?: string;
  mark_complete?: boolean;
}

export interface GuideQueryExecution {
  instance_id: string;
  parameters: Record<string, any>;
}

export interface GuideQueryExecutionResult {
  workflow_id: string;
  execution_id?: string;
  status: string;
}

export interface GuideCategory {
  name: string;
  count: number;
}

// For list views
export interface BuildGuideListItem {
  id: string;
  guide_id: string;
  name: string;
  category: string;
  short_description?: string;
  tags: string[];
  icon?: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  estimated_time_minutes: number;
  is_published: boolean;
  user_progress?: UserGuideProgressSummary;
  is_favorite?: boolean;
  created_at: string;
}

// Table of Contents item for navigation
export interface GuideTOCItem {
  id: string;
  title: string;
  level: number;
  type: 'section' | 'query';
  completed?: boolean;
}