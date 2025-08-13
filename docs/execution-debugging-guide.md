# Execution Debugging Guide

This guide helps you find and debug running executions when they're not visible in the AMC console.

## The Problem

When you execute a query through your application, it may show as "running" in your app but not appear in the AMC console. This happens because:

1. **Dual Tracking Systems**: Your app uses an internal database while AMC has its own execution tracking
2. **Timing Delays**: AMC may take 45+ seconds to register executions in their console
3. **Missing AMC IDs**: Sometimes the AMC API call fails, leaving executions without AMC execution IDs

## Quick Solutions

### 1. Wait and Check Again
- **Time needed**: 1-2 minutes
- **Action**: Wait 45-60 seconds, then refresh the AMC console
- **Why**: AMC needs time to register new executions

### 2. Check Your App's Execution History
- **Location**: Go to your workflow → "Execution History" tab
- **Look for**: Executions with "running" or "pending" status
- **Contains**: Both internal execution IDs and AMC execution IDs (when available)

## Diagnostic Tools

### 1. Execution Finder Script

**Purpose**: Cross-reference executions between your database and AMC console

```bash
# Find all running executions in your database
python scripts/find_running_executions.py

# Check specific instance and user
python scripts/find_running_executions.py --instance-id amchnfozgta --user-email nick@nevermeh.com

# Output as JSON for further processing
python scripts/find_running_executions.py --instance-id amchnfozgta --user-email nick@nevermeh.com --json
```

**What it shows**:
- ✅ Executions properly matched between systems
- 🔄 Executions running in your database
- 🔄 Executions running in AMC console
- ⚠️ Executions missing AMC execution IDs
- 🔍 Executions in one system but not the other

### 2. Real-time Execution Monitor

**Location**: Frontend component in `/src/components/executions/ExecutionMonitor.tsx`

**Features**:
- Auto-refreshes every 5 seconds
- Shows running executions with progress
- Identifies missing AMC IDs
- Provides diagnostic recommendations
- Cross-references database and AMC data

**Usage in React**:
```tsx
import ExecutionMonitor from '@/components/executions/ExecutionMonitor';

// Monitor specific workflow
<ExecutionMonitor workflowId="your-workflow-id" />

// Monitor entire instance
<ExecutionMonitor instanceId="your-instance-id" />

// Both with custom refresh interval
<ExecutionMonitor 
  workflowId="your-workflow-id" 
  instanceId="your-instance-id"
  refreshInterval={10} // seconds
/>
```

### 3. Enhanced API Endpoints

**Workflow Execution Status**:
```
GET /api/workflows/{workflow_id}/execution-status
```
Returns detailed execution status with diagnostics and recommendations.

**Cross-Reference Executions**:
```
GET /api/workflows/executions/cross-reference?instance_id={instance_id}
```
Compares executions between your database and AMC console.

### 4. Execution Reconciliation Tool

**Purpose**: Fix common execution issues automatically

```bash
# Analyze issues (dry run)
python scripts/reconcile_executions.py --instance-id amchnfozgta --user-email nick@nevermeh.com --dry-run

# Apply automatic fixes
python scripts/reconcile_executions.py --instance-id amchnfozgta --user-email nick@nevermeh.com --fix

# Output as JSON for automation
python scripts/reconcile_executions.py --instance-id amchnfozgta --user-email nick@nevermeh.com --json
```

**What it fixes**:
- ✅ Syncs status mismatches between systems
- ✅ Marks legacy executions appropriately
- ✅ Identifies orphaned executions
- ✅ Provides repair recommendations

## Common Issues and Solutions

### Issue: "Execution shows as running but not in AMC console"

**Likely Cause**: Timing delay or missing AMC execution ID

**Solutions**:
1. Wait 1-2 minutes and check AMC console again
2. Run: `python scripts/find_running_executions.py --instance-id YOUR_INSTANCE --user-email YOUR_EMAIL`
3. Check if execution has an AMC ID in the results
4. If no AMC ID, check backend logs for API errors

### Issue: "Execution missing AMC execution ID"

**Likely Cause**: AMC API call failed during execution creation

**Solutions**:
1. Check authentication tokens are still valid
2. Verify AMC instance access permissions  
3. Look for AMC API errors in backend logs around execution start time
4. For completed executions, mark as legacy using reconciliation tool

### Issue: "Status mismatch between systems"

**Likely Cause**: Database not updated after AMC status change

**Solutions**:
1. Use reconciliation tool to sync statuses automatically
2. Check polling mechanism is working correctly
3. Verify network connectivity to AMC API

### Issue: "Orphaned executions"

**Likely Cause**: Execution exists in one system but not the other

**Solutions**:
1. Database-only: Check if AMC execution ID is valid
2. AMC-only: Investigation needed for missing database record
3. Use reconciliation tool for automated analysis

## Prevention

### 1. Monitor Execution Health
- Add ExecutionMonitor component to key pages
- Set up alerts for executions missing AMC IDs
- Regular reconciliation checks

### 2. Improve Error Handling
- Enhanced logging for AMC API calls
- Retry mechanisms for failed AMC operations
- Better user feedback for execution issues

### 3. Regular Maintenance
- Weekly reconciliation runs
- Token refresh monitoring
- Cleanup of old orphaned executions

## Backend Implementation Details

### Execution Flow
1. User executes query → Creates record in `workflow_executions` table
2. App calls AMC API → Receives AMC execution ID
3. Database updated with AMC execution ID
4. Polling checks AMC status every 2 seconds
5. Results fetched when AMC execution completes

### Key Components
- **AMCExecutionService** (`amc_execution_service.py:378`): Stores AMC execution ID
- **AMC API Client** (`amc_api_client.py:141`): Extracts execution ID from response
- **Status Polling** (`amc_execution_service.py:530`): Updates status from AMC
- **Database Schema**: `workflow_executions.amc_execution_id` links systems

### Critical Timing
- **45-second delay** (`amc_execution_service.py:584-585`): Wait before first AMC status check
- **2-second polling**: Frontend polls execution status  
- **3-attempt retry**: On execution not found errors

This comprehensive tooling should help you quickly identify and resolve execution tracking issues!