export interface FlowComposition {
  id: string;
  composition_id: string;
  name: string;
  description?: string;
  nodes: FlowNode[];
  connections: FlowConnection[];
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

export interface FlowNode {
  node_id: string;
  template_id: string;
  position: {
    x: number;
    y: number;
  };
  config: Record<string, any>;
  template?: {
    name: string;
    description?: string;
    parameters?: Array<{
      name: string;
      type: string;
      required?: boolean;
      default_value?: any;
    }>;
  };
}

export interface FlowConnection {
  source_node_id: string;
  target_node_id: string;
  parameter_mappings: ParameterMapping[];
}

export interface ParameterMapping {
  source_param: string;
  target_param: string;
  transformation?: string;
}

export interface FlowExecutionRequest {
  composition_id: string;
  instance_id: string;
  parameters: Record<string, any>;
  execution_mode?: 'sequential' | 'parallel';
}

export interface FlowExecutionResult {
  execution_id: string;
  composition_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  node_executions: NodeExecution[];
  created_at: string;
  completed_at?: string;
  error?: string;
}

export interface NodeExecution {
  node_id: string;
  workflow_execution_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  result?: any;
  error?: string;
}