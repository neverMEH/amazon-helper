# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-10-15-instance-templates/spec.md

> Created: 2025-10-15
> Version: 1.0.0

## Technical Requirements

### Backend Architecture

- **Service Layer**: Create `InstanceTemplateService` class extending `DatabaseService` with connection retry decorator
- **Database Integration**: Use Supabase client for all database operations with proper error handling
- **Access Control**: Ensure templates are only accessible by their owner (user_id) and scoped to specific instances
- **Caching**: Implement simple in-memory caching with 5-minute TTL similar to `QueryTemplateService`
- **ID Generation**: Use `tpl_inst_{uuid.uuid4().hex[:12]}` format for template_id to distinguish from global templates

### Frontend Architecture

- **Component Structure**: Replace `InstanceWorkflows.tsx` with new `InstanceTemplates.tsx` component
- **State Management**: Use TanStack Query for data fetching and caching with appropriate query keys: `['instance-templates', instanceId]`
- **API Service**: Create `instanceTemplateService.ts` following existing service patterns with axios-based API calls
- **Modal Editor**: Create `InstanceTemplateEditor.tsx` modal component with simplified fields (no parameter schema)
- **TypeScript Types**: Define `InstanceTemplate` interface in `types/instanceTemplate.ts`

### UI/UX Specifications

- **Template List View**: Display templates in card layout similar to QueryLibrary grid view
- **Empty State**: Show helpful message with "Create Template" button when no templates exist
- **Template Actions**: Each template card has Edit, Delete, and "Use Template" buttons
- **Editor Modal**: Simple form with three fields: Name (required), Description (optional), SQL Query (required, Monaco editor)
- **Confirmation Dialogs**: Show confirmation before deleting templates
- **Toast Notifications**: Success/error feedback for all CRUD operations

### Integration Points

- **Instance Detail Page**: Update tab configuration in `InstanceDetail.tsx` to show "Templates" instead of "Workflows"
- **Query Builder**: When "Use Template" clicked, navigate to query builder with template SQL pre-populated
- **Workflow Creation**: Template SQL becomes the initial SQL for new workflow, instance is pre-selected

### Performance Considerations

- **List Pagination**: Initially load all templates (expect low volume per instance), add pagination if needed
- **SQL Editor**: Use Monaco Editor with lazy loading to minimize bundle size impact
- **Query Caching**: Cache template lists with 5-minute stale time to reduce API calls
- **Optimistic Updates**: Use TanStack Query optimistic updates for delete operations

### Error Handling

- **Network Errors**: Display toast notifications with retry option
- **Validation Errors**: Show inline field validation for required fields
- **Access Denied**: Show 404 if user attempts to access other users' templates
- **Database Errors**: Log errors server-side and show generic error message to users

## Approach

### Database Schema

```sql
-- New table: instance_templates
CREATE TABLE instance_templates (
    template_id VARCHAR(50) PRIMARY KEY,  -- Format: tpl_inst_{12-char-uuid}
    instance_id UUID NOT NULL REFERENCES amc_instances(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sql_query TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_instance_templates_instance ON instance_templates(instance_id);
CREATE INDEX idx_instance_templates_user ON instance_templates(user_id);
CREATE INDEX idx_instance_templates_instance_user ON instance_templates(instance_id, user_id);

-- RLS policies
ALTER TABLE instance_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own instance templates"
    ON instance_templates FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own instance templates"
    ON instance_templates FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own instance templates"
    ON instance_templates FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own instance templates"
    ON instance_templates FOR DELETE
    USING (auth.uid() = user_id);
```

### Backend Implementation

**File Structure**:
```
amc_manager/
├── services/
│   └── instance_template_service.py       # Business logic
├── api/
│   └── supabase/
│       └── instance_template_endpoints.py # API routes
└── schemas/
    └── instance_template.py               # Pydantic models
```

**Service Layer** (`instance_template_service.py`):
```python
from amc_manager.services.database_service import DatabaseService, with_connection_retry
from typing import List, Optional
import uuid

class InstanceTemplateService(DatabaseService):
    def __init__(self):
        super().__init__()
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes

    @with_connection_retry
    async def list_templates(self, instance_id: str, user_id: str) -> List[dict]:
        """List all templates for an instance and user"""
        cache_key = f"{instance_id}_{user_id}"
        # Check cache first
        # Query: SELECT * FROM instance_templates
        #        WHERE instance_id = ? AND user_id = ?
        #        ORDER BY created_at DESC

    @with_connection_retry
    async def get_template(self, template_id: str, user_id: str) -> dict:
        """Get a single template"""
        # Query with user_id check for access control

    @with_connection_retry
    async def create_template(self, instance_id: str, user_id: str,
                            name: str, sql_query: str,
                            description: Optional[str] = None) -> dict:
        """Create a new template"""
        # Generate template_id: tpl_inst_{uuid.uuid4().hex[:12]}
        # Insert and invalidate cache

    @with_connection_retry
    async def update_template(self, template_id: str, user_id: str,
                            name: Optional[str] = None,
                            sql_query: Optional[str] = None,
                            description: Optional[str] = None) -> dict:
        """Update an existing template"""
        # Update with user_id check and invalidate cache

    @with_connection_retry
    async def delete_template(self, template_id: str, user_id: str) -> bool:
        """Delete a template"""
        # Delete with user_id check and invalidate cache
```

**API Endpoints** (`instance_template_endpoints.py`):
```python
from fastapi import APIRouter, Depends, HTTPException
from amc_manager.schemas.instance_template import (
    InstanceTemplateCreate, InstanceTemplateUpdate, InstanceTemplateResponse
)

router = APIRouter(prefix="/api/instance-templates", tags=["Instance Templates"])

@router.get("/instance/{instance_id}")
async def list_templates(instance_id: str, user_id: str = Depends(get_current_user)):
    """List all templates for an instance"""

@router.get("/{template_id}")
async def get_template(template_id: str, user_id: str = Depends(get_current_user)):
    """Get a single template"""

@router.post("/")
async def create_template(data: InstanceTemplateCreate, user_id: str = Depends(get_current_user)):
    """Create a new template"""

@router.put("/{template_id}")
async def update_template(template_id: str, data: InstanceTemplateUpdate,
                         user_id: str = Depends(get_current_user)):
    """Update a template"""

@router.delete("/{template_id}")
async def delete_template(template_id: str, user_id: str = Depends(get_current_user)):
    """Delete a template"""
```

**Pydantic Schemas** (`instance_template.py`):
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class InstanceTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sql_query: str = Field(..., min_length=1)

class InstanceTemplateCreate(InstanceTemplateBase):
    instance_id: str

class InstanceTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sql_query: Optional[str] = Field(None, min_length=1)

class InstanceTemplateResponse(InstanceTemplateBase):
    template_id: str
    instance_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### Frontend Implementation

**File Structure**:
```
frontend/src/
├── services/
│   └── instanceTemplateService.ts         # API client
├── types/
│   └── instanceTemplate.ts                # TypeScript types
├── components/
│   ├── instances/
│   │   ├── InstanceTemplates.tsx          # Main template list
│   │   └── InstanceTemplateEditor.tsx     # Create/edit modal
│   └── InstanceDetail.tsx                 # Update tab config
```

**TypeScript Types** (`instanceTemplate.ts`):
```typescript
export interface InstanceTemplate {
  template_id: string;
  instance_id: string;
  user_id: string;
  name: string;
  description?: string;
  sql_query: string;
  created_at: string;
  updated_at: string;
}

export interface InstanceTemplateCreate {
  instance_id: string;
  name: string;
  description?: string;
  sql_query: string;
}

export interface InstanceTemplateUpdate {
  name?: string;
  description?: string;
  sql_query?: string;
}
```

**API Service** (`instanceTemplateService.ts`):
```typescript
import api from './api';
import type { InstanceTemplate, InstanceTemplateCreate, InstanceTemplateUpdate } from '../types/instanceTemplate';

export const instanceTemplateService = {
  list: (instanceId: string) =>
    api.get<InstanceTemplate[]>(`/instance-templates/instance/${instanceId}`),

  get: (templateId: string) =>
    api.get<InstanceTemplate>(`/instance-templates/${templateId}`),

  create: (data: InstanceTemplateCreate) =>
    api.post<InstanceTemplate>('/instance-templates/', data),

  update: (templateId: string, data: InstanceTemplateUpdate) =>
    api.put<InstanceTemplate>(`/instance-templates/${templateId}`, data),

  delete: (templateId: string) =>
    api.delete(`/instance-templates/${templateId}`),
};
```

**Main Component** (`InstanceTemplates.tsx`):
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { instanceTemplateService } from '../../services/instanceTemplateService';
import InstanceTemplateEditor from './InstanceTemplateEditor';

export default function InstanceTemplates({ instanceId }: { instanceId: string }) {
  const queryClient = useQueryClient();

  // Fetch templates
  const { data: templates, isLoading } = useQuery({
    queryKey: ['instance-templates', instanceId],
    queryFn: () => instanceTemplateService.list(instanceId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Delete mutation with optimistic update
  const deleteMutation = useMutation({
    mutationFn: instanceTemplateService.delete,
    onMutate: async (templateId) => {
      // Optimistic update
      await queryClient.cancelQueries(['instance-templates', instanceId]);
      const previous = queryClient.getQueryData(['instance-templates', instanceId]);
      queryClient.setQueryData(['instance-templates', instanceId], (old) =>
        old?.filter((t) => t.template_id !== templateId)
      );
      return { previous };
    },
    onError: (err, templateId, context) => {
      // Rollback on error
      queryClient.setQueryData(['instance-templates', instanceId], context.previous);
    },
    onSettled: () => {
      queryClient.invalidateQueries(['instance-templates', instanceId]);
    },
  });

  // Grid layout with template cards
  // Empty state when no templates
  // Create, edit, delete, "Use Template" actions
}
```

**Editor Modal** (`InstanceTemplateEditor.tsx`):
```typescript
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import MonacoEditor from '../common/MonacoEditor';
import Modal from '../common/Modal';

interface Props {
  instanceId: string;
  template?: InstanceTemplate;
  isOpen: boolean;
  onClose: () => void;
}

export default function InstanceTemplateEditor({ instanceId, template, isOpen, onClose }: Props) {
  const [name, setName] = useState(template?.name || '');
  const [description, setDescription] = useState(template?.description || '');
  const [sqlQuery, setSqlQuery] = useState(template?.sql_query || '');

  const queryClient = useQueryClient();
  const isEdit = !!template;

  // Create/update mutation
  const mutation = useMutation({
    mutationFn: (data) => {
      if (isEdit) {
        return instanceTemplateService.update(template.template_id, data);
      }
      return instanceTemplateService.create({ ...data, instance_id: instanceId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['instance-templates', instanceId]);
      onClose();
      toast.success(isEdit ? 'Template updated' : 'Template created');
    },
  });

  // Form with name, description, Monaco SQL editor
  // Validation: name and sql_query required
  // Submit/cancel buttons
}
```

**Instance Detail Integration** (`InstanceDetail.tsx`):
```typescript
// Replace "Workflows" tab with "Templates" tab
const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'templates', label: 'Templates' },  // Changed from 'workflows'
  { id: 'mappings', label: 'Mappings' },
  { id: 'asins', label: 'ASINs' },
];

// In tab content rendering:
{activeTab === 'templates' && <InstanceTemplates instanceId={instance.id} />}
```

### Query Builder Integration

When user clicks "Use Template" on a template card:

```typescript
const navigate = useNavigate();

const handleUseTemplate = (template: InstanceTemplate) => {
  // Navigate to query builder with template SQL and instance pre-selected
  navigate('/workflows/new', {
    state: {
      initialSql: template.sql_query,
      instanceId: template.instance_id,
      fromTemplate: true,
    }
  });
};
```

In `WorkflowBuilder.tsx`:
```typescript
// Check for template state on mount
const location = useLocation();
const { initialSql, instanceId, fromTemplate } = location.state || {};

useEffect(() => {
  if (fromTemplate && initialSql) {
    setSqlQuery(initialSql);
    setSelectedInstance(instanceId);
    toast.success('Template loaded! Modify and save as a workflow.');
  }
}, []);
```

## External Dependencies

No new external dependencies required. The feature uses existing libraries:

**Backend**:
- FastAPI (existing)
- Supabase Python client (existing)
- Pydantic (existing)

**Frontend**:
- React 19.1.0 (existing)
- TanStack Query v5 (existing)
- Monaco Editor (existing, already used in WorkflowBuilder)
- Lucide React icons (existing)
- React Hot Toast (existing)
- Axios (existing, via api service)

All required infrastructure and libraries are already present in the codebase.
