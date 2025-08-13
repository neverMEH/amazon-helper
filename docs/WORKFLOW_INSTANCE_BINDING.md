# Workflow Instance Binding and Copy Feature

## Overview
Workflows are permanently tied to a specific AMC instance upon creation. This binding ensures consistent execution context and simplifies the execution process.

## Key Concepts

### Instance Binding
- Each workflow is associated with ONE AMC instance at creation time
- This instance relationship is stored in the database (`workflows.instance_id`)
- The instance cannot be changed after creation (by design)
- Execution always uses the workflow's tied instance

### Workflow Execution Flow
1. User clicks "Execute" on a workflow
2. Execution modal opens showing the tied instance (readonly)
3. User configures parameters and date ranges
4. Execution runs on the pre-configured instance
5. No instance selection required during execution

## Copy Workflow Feature

### Purpose
Allows users to create a new workflow based on an existing one, with the ability to:
- Select a different AMC instance
- Modify the query and parameters
- Create variations for different environments or accounts

### Implementation Details

#### Frontend Routes
```javascript
// Routes in App.tsx
<Route path="/query-builder/copy/:workflowId" element={<QueryBuilder />} />
<Route path="/query-builder/edit/:workflowId" element={<QueryBuilder />} />
<Route path="/query-builder/new" element={<QueryBuilder />} />
```

#### Copy Mode Detection
```javascript
// In QueryBuilder.tsx
const isCopyMode = window.location.pathname.includes('/copy/');
const [currentWorkflowId, setCurrentWorkflowId] = useState<string | undefined>(
  isCopyMode ? undefined : workflowId // Don't use original ID if copying
);
```

#### Data Handling in Copy Mode
```javascript
if (isCopyMode) {
  // Create new workflow with copied data but clear instance
  setQueryState(prev => ({
    ...prev,
    sqlQuery: workflow.sqlQuery || workflow.sql_query,
    name: `Copy of ${workflow.name}`,
    description: workflow.description || '',
    instanceId: '', // Clear instance so user must select a new one
    parameters: workflow.parameters || {}
  }));
}
```

### User Interface

#### Workflows List (MyQueries.tsx)
- Added purple "Copy" button with Copy icon from lucide-react
- Button placement: Between Edit and Schedule buttons
- Click handler: `navigate(/query-builder/copy/${workflowId})`

#### Execution Modal (ExecutionModal.tsx)
```javascript
// Display tied instance (readonly)
{(workflowData?.instance || instanceId) ? (
  <div>
    <h3 className="text-lg font-medium mb-2">Target Instance</h3>
    <p className="text-sm text-gray-600 mb-4">
      This workflow will be executed on its configured instance.
    </p>
    <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
      <p className="text-sm font-medium text-gray-900">
        {workflowData?.instance?.name || 'Loading...'}
      </p>
      <p className="text-xs text-gray-500 mt-1">
        ID: {workflowData?.instance?.id}
      </p>
    </div>
  </div>
) : (
  // Show warning if no instance configured
  <div>
    <p className="text-sm text-gray-600 mb-4">
      ⚠️ No instance configured for this workflow. Please copy the workflow and select an instance.
    </p>
  </div>
)}
```

## API Response Structure

### Workflow GET Response
```javascript
{
  "id": "wf_916558f8",           // String workflow ID
  "workflowId": "wf_916558f8",   // Duplicate for compatibility
  "name": "Campaign Analysis",
  "instance": {                   // Tied instance information
    "id": "amcusecase-123",       // AMC instance ID
    "instanceId": "amcusecase-123",
    "instanceName": "Production AMC"
  },
  "sqlQuery": "SELECT ...",
  "parameters": {...}
}
```

## Database Relationships

### Key Tables
- `workflows` - Contains workflow definitions
  - `id` (UUID) - Internal database ID
  - `workflow_id` (TEXT) - User-facing workflow ID
  - `instance_id` (UUID) - Foreign key to amc_instances.id
  
- `amc_instances` - AMC instance configurations
  - `id` (UUID) - Internal database ID  
  - `instance_id` (TEXT) - AMC instance identifier
  - `instance_name` (TEXT) - Display name

## Common Use Cases

### 1. Execute Workflow on Original Instance
- Click "Execute" button
- Execution modal shows tied instance
- Configure parameters
- Run execution

### 2. Copy Workflow to Different Instance
- Click "Copy" button
- Query Builder opens in copy mode
- Select new instance in configuration step
- Modify query/parameters as needed
- Save as new workflow

### 3. Create Workflow Variations
- Copy workflow multiple times
- Each copy can target different:
  - AMC instances (different accounts/regions)
  - Date ranges via parameters
  - Filter criteria
  - Output formats

## Benefits

### Simplified Execution
- No instance selection during execution
- Reduced chance of running on wrong instance
- Faster execution workflow

### Flexibility
- Copy feature enables multi-instance scenarios
- Original workflows remain unchanged
- Easy to create variations

### Clear Ownership
- Each workflow clearly belongs to one instance
- No ambiguity about execution context
- Better audit trail

## Technical Notes

### Copy vs Edit Detection
The system differentiates between copy and edit modes by:
1. URL pattern (`/copy/` vs `/edit/`)
2. `isCopyMode` flag in QueryBuilder
3. `currentWorkflowId` state (undefined for copies)

### Instance Selection in Copy Mode
When copying, the instance field is intentionally cleared to:
1. Force user to make conscious instance choice
2. Prevent accidental execution on wrong instance
3. Support cross-account workflow migration

### Workflow Naming
Copied workflows automatically get "Copy of" prefix to:
1. Distinguish from original
2. Prevent naming conflicts
3. Maintain clear lineage

## Migration Path
For existing workflows without instance binding:
1. System shows warning in execution modal
2. User must copy workflow to assign instance
3. Original can be deleted after successful copy

## Future Enhancements
- Bulk copy workflows to new instance
- Instance migration wizard
- Cross-region workflow replication
- Template library with instance parameters

---

**Last Updated**: 2025-01-12
**Related Documentation**: 
- `/docs/ID_FIELD_REFERENCE.md` - ID field relationships
- `/CLAUDE.md` - Project conventions