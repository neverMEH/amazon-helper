# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-10-15-instance-templates/spec.md

> Created: 2025-10-15
> Version: 1.0.0

## Endpoints

### GET /api/instances/{instance_id}/templates

**Purpose:** List all templates for a specific instance owned by the current user

**Parameters:**
- `instance_id` (path, required): UUID of the AMC instance

**Authentication:** Required (JWT token)

**Response:** 200 OK
```json
[
  {
    "id": "tpl_inst_abc123def456",
    "templateId": "tpl_inst_abc123def456",
    "name": "Weekly Campaign Performance",
    "description": "Standard weekly report for campaign metrics",
    "sqlQuery": "SELECT campaign_id, impressions, clicks FROM ...",
    "instanceId": "550e8400-e29b-41d4-a716-446655440000",
    "tags": ["weekly", "campaigns"],
    "usageCount": 15,
    "createdAt": "2025-10-15T10:30:00Z",
    "updatedAt": "2025-10-15T10:30:00Z"
  }
]
```

**Errors:**
- 401 Unauthorized: User not authenticated
- 404 Not Found: Instance not found or user doesn't have access

---

### POST /api/instances/{instance_id}/templates

**Purpose:** Create a new template for a specific instance

**Parameters:**
- `instance_id` (path, required): UUID of the AMC instance

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "name": "Weekly Campaign Performance",
  "description": "Standard weekly report for campaign metrics",
  "sqlQuery": "SELECT campaign_id, impressions, clicks FROM campaigns WHERE date >= '{{start_date}}'",
  "tags": ["weekly", "campaigns"]
}
```

**Response:** 201 Created
```json
{
  "templateId": "tpl_inst_abc123def456",
  "name": "Weekly Campaign Performance",
  "instanceId": "550e8400-e29b-41d4-a716-446655440000",
  "createdAt": "2025-10-15T10:30:00Z"
}
```

**Errors:**
- 400 Bad Request: Missing required fields or invalid data
- 401 Unauthorized: User not authenticated
- 404 Not Found: Instance not found or user doesn't have access

---

### GET /api/instances/{instance_id}/templates/{template_id}

**Purpose:** Get a specific template by ID

**Parameters:**
- `instance_id` (path, required): UUID of the AMC instance
- `template_id` (path, required): Template identifier (e.g., "tpl_inst_abc123def456")

**Authentication:** Required (JWT token)

**Response:** 200 OK
```json
{
  "id": "tpl_inst_abc123def456",
  "templateId": "tpl_inst_abc123def456",
  "name": "Weekly Campaign Performance",
  "description": "Standard weekly report for campaign metrics",
  "sqlQuery": "SELECT campaign_id, impressions, clicks FROM campaigns WHERE date >= '{{start_date}}'",
  "instanceId": "550e8400-e29b-41d4-a716-446655440000",
  "tags": ["weekly", "campaigns"],
  "usageCount": 15,
  "createdAt": "2025-10-15T10:30:00Z",
  "updatedAt": "2025-10-15T10:30:00Z"
}
```

**Errors:**
- 401 Unauthorized: User not authenticated
- 404 Not Found: Template not found, access denied, or instance mismatch

---

### PUT /api/instances/{instance_id}/templates/{template_id}

**Purpose:** Update an existing template (owner only)

**Parameters:**
- `instance_id` (path, required): UUID of the AMC instance
- `template_id` (path, required): Template identifier

**Authentication:** Required (JWT token)

**Request Body:** (all fields optional)
```json
{
  "name": "Updated Template Name",
  "description": "Updated description",
  "sqlQuery": "SELECT * FROM updated_query",
  "tags": ["updated", "tags"]
}
```

**Response:** 200 OK
```json
{
  "templateId": "tpl_inst_abc123def456",
  "name": "Updated Template Name",
  "updatedAt": "2025-10-15T11:45:00Z"
}
```

**Errors:**
- 400 Bad Request: Invalid update data
- 401 Unauthorized: User not authenticated
- 404 Not Found: Template not found or access denied

---

### DELETE /api/instances/{instance_id}/templates/{template_id}

**Purpose:** Delete a template (owner only)

**Parameters:**
- `instance_id` (path, required): UUID of the AMC instance
- `template_id` (path, required): Template identifier

**Authentication:** Required (JWT token)

**Response:** 200 OK
```json
{
  "message": "Template deleted successfully"
}
```

**Errors:**
- 401 Unauthorized: User not authenticated
- 404 Not Found: Template not found or access denied

---

### POST /api/instances/{instance_id}/templates/{template_id}/use

**Purpose:** Increment usage count when template is used to create a workflow

**Parameters:**
- `instance_id` (path, required): UUID of the AMC instance
- `template_id` (path, required): Template identifier

**Authentication:** Required (JWT token)

**Response:** 200 OK
```json
{
  "templateId": "tpl_inst_abc123def456",
  "usageCount": 16
}
```

**Errors:**
- 401 Unauthorized: User not authenticated
- 404 Not Found: Template not found or access denied

## API Router Implementation

The endpoints will be implemented in a new FastAPI router module:

**File:** `amc_manager/api/supabase/instance_templates.py`

**Router prefix:** `/api/instances/{instance_id}/templates`

**Router tags:** `["instance-templates"]`

### Pydantic Schemas

**InstanceTemplateCreate:**
```python
class InstanceTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sql_query: str
    tags: List[str] = []
```

**InstanceTemplateUpdate:**
```python
class InstanceTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sql_query: Optional[str] = None
    tags: Optional[List[str]] = None
```

**InstanceTemplateResponse:**
```python
class InstanceTemplateResponse(BaseModel):
    id: str
    template_id: str
    name: str
    description: Optional[str]
    sql_query: str
    instance_id: str
    tags: List[str]
    usage_count: int
    created_at: str
    updated_at: str
```

### Integration with Main Application

The router must be registered in `main_supabase.py`:

```python
from amc_manager.api.supabase.instance_templates import router as instance_templates_router

app.include_router(
    instance_templates_router,
    prefix="/api/instances",
    tags=["instance-templates"]
)
```

## Business Logic

### Access Control
- All endpoints require authentication via `get_current_user` dependency
- Templates are scoped to user_id (RLS ensures users only see their own templates)
- Instance_id in URL path must match template's instance_id

### Validation
- Name: Required, non-empty string, max 255 characters
- SQL Query: Required, non-empty string, must be valid SQL (basic syntax check)
- Instance ID: Must be a valid UUID and exist in amc_instances table
- User must have access to the specified instance

### Error Responses
All error responses follow the FastAPI standard format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Controllers

### InstanceTemplatesController

The controller will be implemented as a service class that handles business logic:

**File:** `amc_manager/services/instance_template_service.py`

**Key Methods:**

1. `list_templates(instance_id: str, user_id: str) -> List[InstanceTemplateResponse]`
   - Fetch all templates for instance owned by user
   - Return sorted by usage_count DESC, then created_at DESC

2. `create_template(instance_id: str, user_id: str, data: InstanceTemplateCreate) -> InstanceTemplateResponse`
   - Validate instance exists and user has access
   - Generate unique template_id with "tpl_inst_" prefix
   - Insert into instance_query_templates table
   - Return created template

3. `get_template(instance_id: str, template_id: str, user_id: str) -> InstanceTemplateResponse`
   - Fetch template by ID
   - Verify ownership and instance match
   - Return template details

4. `update_template(instance_id: str, template_id: str, user_id: str, data: InstanceTemplateUpdate) -> InstanceTemplateResponse`
   - Fetch existing template
   - Verify ownership
   - Update only provided fields
   - Update updated_at timestamp
   - Return updated template

5. `delete_template(instance_id: str, template_id: str, user_id: str) -> bool`
   - Verify ownership
   - Delete template from database
   - Return success status

6. `increment_usage(instance_id: str, template_id: str, user_id: str) -> int`
   - Verify template exists and user has access
   - Increment usage_count by 1
   - Return new usage count

### Database Queries

**List Templates:**
```python
result = db.table('instance_query_templates')\
    .select('*')\
    .eq('instance_id', instance_id)\
    .eq('user_id', user_id)\
    .order('usage_count', desc=True)\
    .order('created_at', desc=True)\
    .execute()
```

**Create Template:**
```python
template_id = f"tpl_inst_{secrets.token_urlsafe(12)}"
result = db.table('instance_query_templates')\
    .insert({
        'template_id': template_id,
        'instance_id': instance_id,
        'user_id': user_id,
        'name': data.name,
        'description': data.description,
        'sql_query': data.sql_query,
        'tags': data.tags,
        'usage_count': 0
    })\
    .execute()
```

**Update Template:**
```python
result = db.table('instance_query_templates')\
    .update({
        'name': data.name,
        'description': data.description,
        'sql_query': data.sql_query,
        'tags': data.tags,
        'updated_at': 'now()'
    })\
    .eq('template_id', template_id)\
    .eq('user_id', user_id)\
    .execute()
```

**Increment Usage:**
```python
result = db.table('instance_query_templates')\
    .update({'usage_count': db.func.increment('usage_count')})\
    .eq('template_id', template_id)\
    .eq('user_id', user_id)\
    .execute()
```
