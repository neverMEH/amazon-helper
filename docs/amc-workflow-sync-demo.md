# AMC Workflow Sync Demo

This document shows how the AMC workflow sync functionality works with the frontend flow.

## Frontend Integration

The AMC workflow sync is now integrated into the frontend with the following features:

### 1. AMC Sync Status Component

A new `AMCSyncStatus` component has been added that displays:
- Current sync status (Not synced, Syncing, Synced, Failed)
- AMC workflow ID when synced
- Last sync timestamp
- Sync/Re-sync/Remove buttons

### 2. Workflow Detail Page Integration

The AMC sync status is shown on the workflow detail page when:
- The workflow is not in edit mode
- The workflow has an associated AMC instance

### 3. User Flow

1. **Create Workflow**: User creates a workflow normally through the UI
2. **View Workflow**: On the workflow detail page, they see the AMC sync status
3. **Sync to AMC**: User clicks "Sync to AMC" button
   - Frontend calls `POST /workflows/{id}/sync-to-amc`
   - Backend creates the workflow in AMC
   - UI shows syncing status and then updates to "Synced"
4. **Execute Workflow**: When executing a synced workflow:
   - The execution uses saved workflow mode (better performance)
   - Parameters are passed to AMC separately
   - No SQL substitution happens locally

### 4. Benefits of Saved Workflows

- **Performance**: AMC can optimize saved workflows
- **Reusability**: Execute the same workflow with different parameters
- **Version Control**: Track workflow changes in AMC
- **Cost Efficiency**: Reduced query parsing overhead

## API Endpoints Used

```typescript
// Check sync status
GET /workflows/{workflowId}/amc-status

// Sync workflow to AMC  
POST /workflows/{workflowId}/sync-to-amc

// Remove workflow from AMC
DELETE /workflows/{workflowId}/amc-sync
```

## Status Indicators

- 🔴 **Not synced**: Workflow exists only locally
- 🔵 **Syncing**: Currently creating workflow in AMC
- 🟢 **Synced**: Workflow successfully created in AMC
- 🟠 **Sync failed**: Error during sync process

## Parameter Handling

When a workflow is synced to AMC:
1. Parameters are extracted from the SQL query (e.g., `{{start_date}}`)
2. Parameter types are inferred (STRING, INTEGER, TIMESTAMP)
3. AMC stores the parameter definitions
4. During execution, parameter values are passed separately

## Example Workflow

```sql
SELECT 
    campaign_id,
    COUNT(DISTINCT user_id) as unique_users
FROM campaign_data
WHERE 
    event_date >= '{{start_date}}'
    AND event_date <= '{{end_date}}'
    AND brand_id = '{{brand_id}}'
GROUP BY campaign_id
```

This workflow would create 3 parameters in AMC:
- `start_date` (TIMESTAMP)
- `end_date` (TIMESTAMP)  
- `brand_id` (STRING)