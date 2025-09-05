/**
 * Data Collection Types
 */

export interface CollectionCreate {
  workflow_id: string;
  instance_id: string;
  target_weeks: number;
  end_date?: string;
  collection_type: 'backfill' | 'weekly_update';
}

export interface CollectionResponse {
  collection_id: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  target_weeks: number;
  start_date: string;
  end_date: string;
  progress_percentage?: number;
  weeks_completed?: number;
  message?: string;
  created_at?: string;
  updated_at?: string;
  workflow_name?: string;
  instance_name?: string;
  error_message?: string;
}

export interface CollectionProgress {
  collection_id: string;
  status: string;
  progress_percentage: number;
  statistics: {
    total_weeks: number;
    completed: number;
    pending: number;
    running: number;
    failed: number;
  };
  next_week?: {
    week_start: string;
    week_end: string;
    scheduled_for?: string;
  };
  weeks: CollectionWeek[];
  started_at: string;
  updated_at: string;
}

export interface CollectionWeek {
  id: string;
  week_start_date: string;
  week_end_date: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  execution_id?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  record_count?: number;
  execution_time_seconds?: number;
}