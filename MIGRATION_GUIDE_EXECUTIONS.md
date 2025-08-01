# Migration Guide: Add Execution History to Instance View

## Overview
This guide explains how to enable execution history tracking in the instance detail view. Currently, executions are not shown because:
1. The `instance_id` column is missing from the `workflow_executions` table
2. Template workflows are associated with one instance but can be executed on any instance

## Steps to Enable Execution History

### 1. Add instance_id Column to Database

Run this SQL in your Supabase SQL Editor:

```sql
-- Add instance_id column to workflow_executions
ALTER TABLE workflow_executions 
ADD COLUMN IF NOT EXISTS instance_id TEXT;

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_workflow_executions_instance_id 
ON workflow_executions(instance_id);

-- Add composite index for workflow + instance queries
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_instance 
ON workflow_executions(workflow_id, instance_id);
```

### 2. Update Existing Executions (Optional)

If you want to backfill instance_id for existing executions based on their workflow's instance:

```sql
-- Update existing executions with instance_id from their workflows
UPDATE workflow_executions we
SET instance_id = (
  SELECT ami.instance_id 
  FROM workflows w
  JOIN amc_instances ami ON ami.id = w.instance_id
  WHERE w.id = we.workflow_id
)
WHERE we.instance_id IS NULL;
```

### 3. Update the Execution Service

The execution service needs to store the instance_id when creating executions. Update `/root/amazon-helper/amc_manager/services/amc_execution_service.py`:

```python
# Around line 94, update the execution_data to include instance_id:
execution_data = {
    "workflow_id": workflow_id,
    "status": "pending",
    "execution_parameters": execution_parameters or {},
    "triggered_by": triggered_by,
    "started_at": datetime.now(timezone.utc).isoformat(),
    "instance_id": instance['instance_id']  # Add this line
}
```

### 4. Update the Database Service

Add support for filtering executions by instance_id in `/root/amazon-helper/amc_manager/services/db_service.py`:

```python
# In the get_workflow_executions_sync method, the instance_id filter will now work
if instance_id:
    query = query.eq('instance_id', instance_id)
```

## What's New

### Frontend Changes
1. **New Executions Tab**: Added to the instance detail view showing all executions for workflows in that instance
2. **Aggregated View**: Shows executions from all workflows associated with the instance
3. **Execution Details**: Click any execution to see detailed information
4. **Quick Execute**: Button to execute workflows directly from the executions tab

### Features
- Real-time updates (polls every 10 seconds)
- Shows workflow name for each execution
- Sortable by date (most recent first)
- Status indicators with colors and icons
- Duration and row count display
- Error message display for failed executions

## Notes
- After applying the database migration, new executions will automatically track the instance they ran on
- The executions tab will show "No workflows configured" if there are no workflows for the instance
- The executions tab will show "No executions yet" if there are workflows but no executions
- Existing executions won't show up unless you run the backfill query

## Deployment
1. Apply the database migration first
2. Deploy the updated code
3. New executions will automatically appear in the instance executions tab