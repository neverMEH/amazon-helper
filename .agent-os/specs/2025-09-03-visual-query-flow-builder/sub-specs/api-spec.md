# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-09-03-visual-query-flow-builder/spec.md

## Endpoints

### Flow Composition Management (Extend Existing Template API)

#### GET /api/query-flow-templates/compositions/

**Purpose:** List all flow compositions accessible to the user (extends existing template list endpoint)
**Parameters:** 
- `search` (query, optional): Search term for name/description
- `tags` (query, optional): Filter by tags (comma-separated)
- `is_public` (query, optional): Filter public/private compositions
- `limit` (query, optional): Page size (default: 20)
- `offset` (query, optional): Pagination offset

**Response:** 
```json
{
  "compositions": [
    {
      "id": "uuid",
      "composition_id": "comp_campaign_analysis_v1",
      "name": "Campaign Performance Analysis Flow",
      "description": "Multi-step campaign analysis using connected templates",
      "tags": ["campaign", "performance", "attribution"],
      "node_count": 3,
      "template_ids": ["template_campaign_performance", "template_attribution"],
      "execution_count": 42,
      "last_executed_at": "2025-09-03T10:00:00Z",
      "created_by": "user_name",
      "created_at": "2025-09-01T10:00:00Z"
    }
  ],
  "total_count": 25,
  "limit": 20,
  "offset": 0
}
```
**Errors:** 401 Unauthorized, 500 Internal Server Error

#### POST /api/query-flow-templates/compositions/

**Purpose:** Create a new flow composition (extends existing template creation pattern)
**Parameters:** 
```json
{
  "composition_id": "comp_campaign_analysis_v1",
  "name": "Campaign Performance Analysis Flow",
  "description": "Multi-step campaign analysis using connected templates",
  "canvas_state": {
    "viewport": { "x": 0, "y": 0, "zoom": 1 },
    "nodes": [
      {
        "id": "node_1",
        "type": "templateNode",
        "position": { "x": 100, "y": 100 },
        "data": { "templateId": "template_campaign_performance" }
      }
    ],
    "edges": [
      {
        "id": "edge_1",
        "source": "node_1",
        "target": "node_2",
        "sourceHandle": "output",
        "targetHandle": "input"
      }
    ]
  },
  "global_parameters": {
    "start_date": "2025-09-01",
    "end_date": "2025-09-30"
  },
  "tags": ["campaign", "performance"],
  "is_public": false
}
```
**Response:** 201 Created with composition object
**Errors:** 400 Bad Request (validation), 409 Conflict (composition_id exists), 401 Unauthorized

#### GET /api/query-flow-templates/compositions/{composition_id}

**Purpose:** Get detailed flow composition with all nodes and connections
**Parameters:** 
- `composition_id` (path): Composition UUID or composition_id string

**Response:**
```json
{
  "id": "uuid",
  "composition_id": "comp_campaign_analysis_v1",
  "name": "Campaign Performance Analysis Flow",
  "canvas_state": {
    "viewport": { "x": 0, "y": 0, "zoom": 1 },
    "nodes": [ /* React Flow nodes */ ],
    "edges": [ /* React Flow edges */ ]
  },
  "nodes": [
    {
      "node_id": "node_1",
      "template_id": "template_campaign_performance",
      "template": { /* Full template object from existing API */ },
      "position": { "x": 100, "y": 100 },
      "parameter_overrides": { "lookback_days": 30 },
      "parameter_mappings": { /* mappings from other nodes */ }
    }
  ],
  "connections": [
    {
      "connection_id": "conn_1",
      "source_node_id": "node_1",
      "target_node_id": "node_2",
      "field_mappings": {
        "campaign_id": "campaign_list",
        "spend": "min_spend_threshold"
      }
    }
  ],
  "global_parameters": { /* Flow-level parameters */ }
}
```
**Errors:** 404 Not Found, 401 Unauthorized

#### PUT /api/query-flow-templates/compositions/{composition_id}

**Purpose:** Update an existing flow composition (follows existing template update patterns)
**Parameters:** Partial composition object (same structure as POST)
**Response:** 200 OK with updated composition
**Errors:** 404 Not Found, 403 Forbidden (not owner), 400 Bad Request

#### DELETE /api/query-flow-templates/compositions/{composition_id}

**Purpose:** Delete a flow composition
**Parameters:** 
- `composition_id` (path): Composition UUID

**Response:** 204 No Content
**Errors:** 404 Not Found, 403 Forbidden, 409 Conflict (has active schedules)

### Node Management

#### POST /api/query-flows/{flow_id}/nodes

**Purpose:** Add a node to a flow
**Parameters:**
```json
{
  "node_id": "node_3",
  "template_id": "template_attribution",
  "position": { "x": 300, "y": 200 },
  "parameter_values": {}
}
```
**Response:** 201 Created with node object
**Errors:** 404 Flow Not Found, 400 Bad Request, 409 Conflict (node_id exists)

#### PUT /api/query-flows/{flow_id}/nodes/{node_id}

**Purpose:** Update node configuration or position
**Parameters:** Partial node object
**Response:** 200 OK with updated node
**Errors:** 404 Not Found, 400 Bad Request

#### DELETE /api/query-flows/{flow_id}/nodes/{node_id}

**Purpose:** Remove a node from flow
**Response:** 204 No Content
**Errors:** 404 Not Found, 409 Conflict (has dependencies)

### Edge Management

#### POST /api/query-flows/{flow_id}/edges

**Purpose:** Create connection between nodes
**Parameters:**
```json
{
  "edge_id": "edge_2",
  "source": "node_1",
  "source_handle": "output",
  "target": "node_2",
  "target_handle": "input",
  "field_mappings": {
    "campaign_id": "@campaign_list",
    "spend": "@spend_threshold"
  }
}
```
**Response:** 201 Created with edge object
**Errors:** 400 Bad Request (invalid connection), 404 Nodes Not Found

#### DELETE /api/query-flows/{flow_id}/edges/{edge_id}

**Purpose:** Remove connection between nodes
**Response:** 204 No Content
**Errors:** 404 Not Found

### Flow Composition Execution (Integrate with Existing Template Execution)

#### POST /api/query-flow-templates/compositions/{composition_id}/execute

**Purpose:** Execute a flow composition (leverages existing template execution infrastructure)
**Parameters:**
```json
{
  "instance_id": "uuid",
  "global_parameters": {
    "start_date": "2025-09-01",
    "end_date": "2025-09-03"
  },
  "node_overrides": {
    "node_1": {
      "campaign_list": ["camp_123", "camp_456"]
    }
  }
}
```
**Response:**
```json
{
  "composition_execution_id": "comp_exec_12345",
  "composition_id": "comp_campaign_analysis_v1",
  "status": "running",
  "started_at": "2025-09-03T10:00:00Z",
  "node_executions": [
    {
      "node_id": "node_1",
      "workflow_execution_id": "exec_template_123",
      "status": "running",
      "template_id": "template_campaign_performance"
    },
    {
      "node_id": "node_2", 
      "status": "pending",
      "template_id": "template_attribution"
    }
  ]
}
```
**Errors:** 404 Not Found, 400 Bad Request (validation), 503 Service Unavailable

#### GET /api/query-flow-templates/compositions/executions/{composition_execution_id}

**Purpose:** Get composition execution status and results (aggregates individual workflow executions)
**Parameters:** 
- `composition_execution_id` (path): Composition execution ID
- `include_results` (query, optional): Include individual node results

**Response:**
```json
{
  "composition_execution_id": "comp_exec_12345",
  "composition_id": "comp_campaign_analysis_v1",
  "status": "completed",
  "started_at": "2025-09-03T10:00:00Z",
  "completed_at": "2025-09-03T10:05:00Z",
  "duration_ms": 300000,
  "node_executions": [
    {
      "node_id": "node_1",
      "template_id": "template_campaign_performance",
      "workflow_execution_id": "exec_template_123",
      "status": "completed",
      "result_row_count": 1000,
      "result_s3_path": "s3://bucket/results/exec_template_123.csv",
      "parameters_used": { /* Final parameters after mapping */ }
    }
  ],
  "result_summary": {
    "total_rows_processed": 5000,
    "nodes_completed": 2,
    "nodes_failed": 0,
    "total_duration_ms": 300000
  }
}
```
**Errors:** 404 Not Found, 401 Unauthorized

#### GET /api/query-flow-templates/compositions/executions/{composition_execution_id}/nodes/{node_id}/results

**Purpose:** Get individual node execution results (redirects to existing workflow execution endpoint)
**Response:** Redirects to `/api/workflow-executions/{workflow_execution_id}` (existing endpoint)
**Errors:** 404 Not Found, 401 Unauthorized

### Flow Templates and Sharing

#### POST /api/query-flows/{flow_id}/duplicate

**Purpose:** Create a copy of an existing flow
**Parameters:**
```json
{
  "name": "Copy of Campaign Analysis",
  "flow_id": "flow_campaign_analysis_v2"
}
```
**Response:** 201 Created with new flow object
**Errors:** 404 Not Found, 401 Unauthorized

#### GET /api/query-flows/{flow_id}/export

**Purpose:** Export flow configuration as JSON
**Response:** Flow configuration JSON file
**Errors:** 404 Not Found, 401 Unauthorized

#### POST /api/query-flows/import

**Purpose:** Import flow from JSON configuration
**Parameters:** Multipart form data with JSON file
**Response:** 201 Created with imported flow
**Errors:** 400 Bad Request (invalid format), 409 Conflict

### Data Mapping

#### POST /api/query-flows/validate-mapping

**Purpose:** Validate field mapping between nodes
**Parameters:**
```json
{
  "source_template_id": "template_campaign_performance",
  "target_template_id": "template_attribution",
  "field_mappings": {
    "campaign_id": "@campaign_list"
  }
}
```
**Response:**
```json
{
  "valid": true,
  "warnings": [],
  "errors": []
}
```
**Errors:** 400 Bad Request

#### GET /api/query-flows/templates/{template_id}/schema

**Purpose:** Get output schema for a template
**Response:**
```json
{
  "output_columns": [
    {
      "name": "campaign_id",
      "type": "string",
      "nullable": false
    },
    {
      "name": "impressions",
      "type": "integer",
      "nullable": false
    }
  ],
  "input_parameters": [
    {
      "name": "@start_date",
      "type": "date",
      "required": true
    }
  ]
}
```
**Errors:** 404 Template Not Found

## Controller Implementation

### FlowController (`flow_controller.py`)

**Actions:**
- `list_flows()`: Query flows with filters and pagination
- `create_flow()`: Validate and create new flow
- `get_flow()`: Retrieve full flow configuration
- `update_flow()`: Update flow with version management
- `delete_flow()`: Soft delete with cascade handling

### FlowExecutionController (`flow_execution_controller.py`)

**Actions:**
- `execute_flow()`: Initialize flow execution with dependency resolution
- `get_execution_status()`: Poll execution progress
- `cancel_execution()`: Graceful cancellation with cleanup
- `get_node_results()`: Retrieve individual node outputs

### FlowMappingController (`flow_mapping_controller.py`)

**Actions:**
- `validate_mapping()`: Type checking and schema validation
- `get_template_schema()`: Extract template I/O schema
- `suggest_mappings()`: AI-assisted field mapping suggestions

## Error Handling

All endpoints return standard error responses:
```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": { /* Additional context */ }
}
```

Common error codes:
- `FLOW_NOT_FOUND`: Flow does not exist
- `NODE_NOT_FOUND`: Node does not exist in flow
- `INVALID_CONNECTION`: Connection would create cycle
- `MAPPING_TYPE_MISMATCH`: Field types incompatible
- `EXECUTION_FAILED`: Flow execution encountered error
- `PERMISSION_DENIED`: User lacks required permissions