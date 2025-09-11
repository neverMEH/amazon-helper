# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-09-11-query-library-redesign/spec.md

> Created: 2025-09-11
> Version: 1.0.0

## Endpoints

### GET /api/query-library/templates
**Purpose:** List all available query templates with filtering and pagination
**Parameters:** 
- category (optional): Filter by template category
- search (optional): Search in name and description
- page (optional): Page number for pagination
- limit (optional): Items per page (default: 20)
**Response:** 
```json
{
  "templates": [
    {
      "id": "uuid",
      "template_id": "tpl_xxx",
      "name": "string",
      "description": "string",
      "category": "string",
      "usage_count": 0,
      "is_public": false,
      "parameters": []
    }
  ],
  "total": 100,
  "page": 1,
  "pages": 5
}
```
**Errors:** 401 Unauthorized, 500 Server Error

### POST /api/query-library/templates
**Purpose:** Create a new query template with parameters
**Parameters:** 
```json
{
  "name": "string",
  "description": "string",
  "category": "string",
  "sql_template": "string",
  "parameters": [
    {
      "name": "string",
      "type": "string",
      "display_name": "string",
      "required": true,
      "default_value": "any",
      "validation_rules": {},
      "ui_config": {}
    }
  ],
  "report_config": {}
}
```
**Response:** Created template object with generated ID
**Errors:** 400 Bad Request, 401 Unauthorized, 422 Validation Error

### GET /api/query-library/templates/{template_id}
**Purpose:** Get detailed template information including parameters and reports
**Parameters:** template_id (path parameter)
**Response:** Complete template object with parameters and report configurations
**Errors:** 401 Unauthorized, 404 Not Found

### POST /api/query-library/templates/{template_id}/fork
**Purpose:** Create a copy of an existing template for customization
**Parameters:** template_id (path parameter)
**Response:** New template object with parent_template_id reference
**Errors:** 401 Unauthorized, 404 Not Found, 403 Forbidden

### POST /api/query-library/templates/{template_id}/execute
**Purpose:** Execute a template with provided parameters
**Parameters:**
```json
{
  "parameters": {
    "param_name": "value"
  },
  "instance_id": "amc_instance_id"
}
```
**Response:** Execution ID and status
**Errors:** 400 Bad Request, 401 Unauthorized, 422 Validation Error

### GET /api/query-library/templates/{template_id}/parameters
**Purpose:** Get parameter definitions for dynamic form generation
**Parameters:** template_id (path parameter)
**Response:** Array of parameter definitions with UI configurations
**Errors:** 401 Unauthorized, 404 Not Found

### POST /api/query-library/templates/{template_id}/validate-parameters
**Purpose:** Validate parameter values before execution
**Parameters:**
```json
{
  "parameters": {
    "param_name": "value"
  }
}
```
**Response:** Validation results with errors if any
**Errors:** 400 Bad Request, 422 Validation Error

### POST /api/query-library/templates/{template_id}/instances
**Purpose:** Save a parameter set for future use
**Parameters:**
```json
{
  "instance_name": "string",
  "saved_parameters": {},
  "is_favorite": false
}
```
**Response:** Created instance object
**Errors:** 401 Unauthorized, 422 Validation Error

### GET /api/query-library/instances
**Purpose:** List saved template instances for the current user
**Parameters:** 
- template_id (optional): Filter by template
- is_favorite (optional): Filter favorites only
**Response:** Array of saved instances
**Errors:** 401 Unauthorized

### POST /api/query-library/templates/{template_id}/generate-dashboard
**Purpose:** Generate dashboard configuration from template execution results
**Parameters:**
```json
{
  "execution_id": "uuid",
  "dashboard_name": "string"
}
```
**Response:** Generated dashboard configuration
**Errors:** 401 Unauthorized, 404 Not Found, 422 Validation Error

## Controllers

### QueryLibraryController
- **list_templates**: Retrieve paginated template list with filtering
- **create_template**: Create new template with validation
- **get_template**: Retrieve single template details
- **fork_template**: Create template copy with parent reference
- **share_template**: Update template sharing settings

### TemplateExecutionController
- **execute_template**: Process template with parameters and create AMC execution
- **validate_parameters**: Validate parameter values against rules
- **get_execution_status**: Check execution progress

### TemplateInstanceController
- **save_instance**: Store parameter set for reuse
- **list_instances**: Get user's saved instances
- **execute_instance**: Execute saved instance

### TemplateReportController
- **generate_dashboard**: Create dashboard from execution results
- **get_report_config**: Retrieve report configuration
- **update_field_mappings**: Modify result-to-widget mappings

## Error Handling

All endpoints return standardized error responses:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

Common error codes:
- TEMPLATE_NOT_FOUND
- INVALID_PARAMETERS
- EXECUTION_FAILED
- PERMISSION_DENIED
- VALIDATION_ERROR