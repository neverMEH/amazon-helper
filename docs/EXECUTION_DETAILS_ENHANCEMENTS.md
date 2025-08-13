# Execution Details Enhancements Documentation

## Date: 2025-01-13

This document details the enhancements made to the execution details viewing system, including the addition of rerun/refresh functionality and fixes to various display issues.

## Overview

Enhanced the AMCExecutionDetail modal component to provide better user experience with rerun capabilities, refresh functionality, and proper data field mapping.

## Changes Implemented

### 1. Added Rerun and Refresh Buttons to AMCExecutionDetail Modal

**Problem**: Users couldn't easily rerun workflows with the same parameters or manually refresh execution data.

**Solution**: Added two action buttons in the modal header:
- **Refresh Button**: Manually triggers data refetch with toast notification
- **Rerun Button**: Executes the workflow again with the same parameters

**Implementation Details**:

```typescript
// Location: frontend/src/components/executions/AMCExecutionDetail.tsx

// Added imports
import { toast } from 'react-hot-toast';

// Rerun mutation
const rerunMutation = useMutation({
  mutationFn: async () => {
    const workflowId = execution?.workflowId || execution?.workflowInfo?.id;
    if (!workflowId) {
      throw new Error('Workflow ID not found');
    }
    
    const { default: api } = await import('../../services/api');
    
    const response = await api.post(`/workflows/${workflowId}/execute`, {
      parameters: execution.executionParameters || {},
      instance_id: instanceId
    });
    
    return response.data;
  },
  onSuccess: (data) => {
    toast.success('Workflow rerun initiated');
    setIsRerunning(false);
    queryClient.invalidateQueries({ queryKey: ['amc-execution-detail'] });
    queryClient.invalidateQueries({ queryKey: ['amc-executions'] });
    
    if (data.execution_id) {
      toast.success(`New execution started: ${data.execution_id}`);
    }
  },
  onError: (error: any) => {
    toast.error(error.response?.data?.detail || 'Failed to rerun workflow');
    setIsRerunning(false);
  }
});
```

### 2. Fixed TypeScript Compilation Errors

**Problems Fixed**:
1. Using `require()` instead of ES6 imports for react-hot-toast
2. Incorrect property access for workflow ID and parameters
3. Type mismatches with AMCExecutionDetail interface

**Solutions**:
- Changed `const { toast } = require('react-hot-toast')` to `import { toast } from 'react-hot-toast'`
- Updated to use `execution.executionParameters` instead of `execution.parameters`
- Fixed workflow ID access to check both `execution.workflowId` and `execution.workflowInfo.id`

### 3. Fixed Rerun Button Disabled State

**Problem**: The rerun button was always greyed out (disabled) even when viewing valid workflow executions.

**Root Cause**: 
- Frontend was checking for `execution.workflowId`
- API returns the workflow ID in `execution.workflowInfo.id` field
- This mismatch caused the button to always be disabled

**Data Structure from API**:
```javascript
// API returns:
{
  execution: {
    executionId: "22f7fe31-99ef-472f-8822-5bd864ebe17c",
    workflowInfo: {
      id: "wf_916558f8",  // The workflow ID (TEXT field)
      name: "Query Name",
      description: "...",
      sqlQuery: "...",
      parameters: {...}
    },
    executionParameters: {...},
    // ... other fields
  }
}
```

**Solution**:
```typescript
// Check both possible locations for workflow ID
const workflowId = execution?.workflowId || execution?.workflowInfo?.id;

// Button disabled state also checks both locations
disabled={isRerunning || (!execution?.workflowId && !execution?.workflowInfo?.id)}
```

## Component Discovery Issue

**Initial Confusion**: Initially added buttons to `ExecutionDetailModal` component, but they weren't visible.

**Discovery**: The application actually uses `AMCExecutionDetail` component for viewing execution details, not `ExecutionDetailModal`.

**Key Learning**: 
- `ExecutionDetailModal` is used in the workflows context
- `AMCExecutionDetail` is the primary component for viewing AMC execution details throughout the application
- Both components exist but serve different purposes

## UI/UX Improvements

### Button Placement
- Buttons placed in modal header for consistent visibility
- Refresh button uses grey border style (secondary action)
- Rerun button uses primary indigo style (primary action)
- Both buttons show appropriate icons (RefreshCw and Play)

### Loading States
- Rerun button shows spinner and "Rerunning..." text when active
- Button is disabled during rerun to prevent duplicate requests
- Toast notifications provide immediate feedback

### Error Handling
- Clear error messages displayed via toast notifications
- Graceful handling when workflow ID is missing
- Proper error propagation from API failures

## Files Modified

1. `/root/amazon-helper/frontend/src/components/executions/AMCExecutionDetail.tsx`
   - Added rerun and refresh functionality
   - Fixed TypeScript errors
   - Improved workflow ID detection

## Testing Notes

The implementation was tested with execution ID: `22f7fe31-99ef-472f-8822-5bd864ebe17c`

This revealed the workflow ID field mismatch issue that was subsequently fixed.

## Related Database Schema

Understanding the ID relationships is critical:

```sql
-- workflow_executions table
execution_id: TEXT (e.g., "exec_12345678")  -- Internal execution ID
workflow_id: UUID                            -- Foreign key to workflows.id
amc_execution_id: TEXT                       -- AMC's execution ID

-- workflows table  
id: UUID                                     -- Primary key (foreign key target)
workflow_id: TEXT (e.g., "wf_916558f8")     -- AMC-compliant workflow ID
```

## Future Considerations

1. **Workflow Deletion Handling**: Executions may have no associated workflow if the workflow was deleted
2. **External Executions**: Executions created directly via AMC API won't have workflow info
3. **Permission Checks**: Consider adding checks to ensure user can execute the workflow
4. **Parameter Validation**: Could add validation to ensure parameters are still valid for the workflow

## Success Metrics

- ✅ Users can rerun workflows without navigating away from execution details
- ✅ Manual refresh available for checking execution status
- ✅ Clear visual feedback for all actions
- ✅ TypeScript compilation passes without errors
- ✅ Buttons properly enable/disable based on data availability

## Commit History

1. `feat: Add rerun and refresh buttons to AMCExecutionDetail modal` (869b119)
2. `fix: Resolve TypeScript errors in AMCExecutionDetail component` (98eb5ee)
3. `fix: Enable rerun button by checking workflowInfo.id field` (7a64b59)

## Conclusion

The execution details viewing experience has been significantly enhanced with the ability to rerun workflows and refresh data on demand. The implementation properly handles the complex data structure returned by the AMC API and provides a smooth user experience with appropriate loading states and error handling.