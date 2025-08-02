export interface QueryTemplate {
  id: string;
  templateId: string;
  name: string;
  description?: string;
  category: string;
  sqlTemplate: string;
  parametersSchema: Record<string, any>;
  defaultParameters: Record<string, any>;
  isPublic: boolean;
  tags: string[];
  usageCount: number;
  isOwner: boolean;
  createdAt: string;
  updatedAt: string;
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