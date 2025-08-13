/**
 * AMC Data Source Types
 */

export interface DataSource {
  id: string;
  schema_id: string;
  name: string;
  category: string;
  description: string;
  data_sources: string[];
  version: string;
  tags: string[];
  is_paid_feature: boolean;
  availability?: {
    marketplaces?: Record<string, string>;
    requires_subscription?: boolean;
    historical_data_notes?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface SchemaField {
  id: string;
  data_source_id: string;
  field_name: string;
  data_type: string;
  dimension_or_metric: 'Dimension' | 'Metric';
  description: string;
  aggregation_threshold: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'VERY_HIGH' | 'INTERNAL';
  field_category?: string;
  examples?: string[];
  field_order: number;
  is_nullable?: boolean;
  is_array?: boolean;
}

export interface QueryExample {
  id: string;
  data_source_id: string;
  title: string;
  description?: string;
  sql_query: string;
  category?: string;
  use_case?: string;
  example_order: number;
  parameters?: Record<string, any>;
  expected_output?: string;
}

export interface SchemaSection {
  id: string;
  data_source_id: string;
  section_type: string;
  title?: string;
  content_markdown: string;
  section_order: number;
}

export interface SchemaRelationship {
  id: string;
  source_schema_id: string;
  target_schema_id: string;
  relationship_type: 'variant' | 'joins_with' | 'extends' | 'requires' | 'related';
  description?: string;
  join_condition?: string;
  target?: {
    schema_id: string;
    name: string;
  };
  source?: {
    schema_id: string;
    name: string;
  };
}

export interface CompleteSchema {
  schema: DataSource;
  fields: SchemaField[];
  examples: QueryExample[];
  sections: SchemaSection[];
  relationships: {
    from: SchemaRelationship[];
    to: SchemaRelationship[];
  };
}

export interface DataSourceFilters {
  category?: string;
  search?: string;
  tags?: string[];
  limit?: number;
  offset?: number;
}

export interface FieldSearchResult {
  id: string;
  field_name: string;
  data_type: string;
  dimension_or_metric: string;
  description: string;
  data_source: {
    schema_id: string;
    name: string;
    category: string;
  };
}

export interface TagWithCount {
  tag: string;
  count: number;
}

export interface AIExport {
  version: string;
  generated_at: string;
  total_schemas: number;
  schemas: Array<{
    id: string;
    name: string;
    category: string;
    description: string;
    tables: string[];
    tags: string[];
    key_fields: string[];
    metrics: Array<{
      name: string;
      type: string;
      description: string;
    }>;
    dimensions: Array<{
      name: string;
      type: string;
      description: string;
    }>;
    example_queries: Array<{
      title: string;
      sql: string;
      category: string;
    }>;
    use_cases: string[];
    relationships: Array<{
      type: string;
      target: string;
      direction: string;
    }>;
  }>;
}