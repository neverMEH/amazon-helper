export interface QueryTemplate {
  id: string;
  templateId?: string;
  name: string;
  description?: string;
  category: string;
  sqlTemplate?: string;
  sql_query?: string; // Added for compatibility
  parametersSchema?: Record<string, any>;
  parameter_definitions?: Record<string, any>; // Added for report builder
  defaultParameters?: Record<string, any>;
  parameters?: Record<string, any>; // Added for compatibility
  ui_schema?: Record<string, any>; // Added for report builder
  report_type?: string; // Added for report categorization
  report_config?: Record<string, any>; // Added for report configuration
  instance_types?: string[]; // Added for instance compatibility
  isPublic?: boolean;
  tags?: string[];
  usageCount?: number;
  isOwner?: boolean;
  created_at?: string; // Alternative naming
  createdAt?: string;
  updated_at?: string; // Alternative naming
  updatedAt?: string;
}

export interface QueryTemplateCreate {
  name: string;
  description?: string;
  category: string;
  sql_template: string;
  parameters_schema: Record<string, any>;
  default_parameters: Record<string, any>;
  is_public: boolean;
  tags: string[];
}

export interface QueryTemplateUpdate {
  name?: string;
  description?: string;
  category?: string;
  sql_template?: string;
  parameters_schema?: Record<string, any>;
  default_parameters?: Record<string, any>;
  is_public?: boolean;
  tags?: string[];
}

export interface CreateFromWorkflow {
  workflow_id: string;
  name: string;
  description?: string;
  category: string;
  parameters_schema: Record<string, any>;
  is_public: boolean;
  tags: string[];
}

export interface TemplateParameter {
  name: string;
  type: 'string' | 'number' | 'date' | 'array' | 'boolean';
  description?: string;
  required: boolean;
  default?: any;
  options?: any[]; // For select/dropdown parameters
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    minLength?: number;
    maxLength?: number;
  };
}