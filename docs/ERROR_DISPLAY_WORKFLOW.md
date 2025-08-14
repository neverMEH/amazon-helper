# AMC Error Display Workflow

## Where the Enhanced Error Display Appears

The enhanced error display appears in **multiple places** throughout the AMC query execution workflow:

### 🔄 Workflow Execution Flow

```
User Journey:
├── 1. Query Builder (/query-builder)
│   └── User creates/edits AMC SQL query
│
├── 2. Instance Workflows (/instances/:instanceId)
│   ├── User sees list of workflows for an instance
│   └── Clicks "Execute" button on a workflow
│       └── Opens: ExecutionModal ✅
│
├── 3. ExecutionModal Component
│   ├── User configures parameters
│   ├── Clicks "Execute Workflow" 
│   └── After execution:
│       ├── If SUCCESS → Shows results inline
│       └── If FAILED → Shows ExecutionErrorDetails ⚠️ (NEW)
│           └── User can click "View Full Error" → ErrorDetailsModal 🔍 (NEW)
│
├── 4. View Full Results Button
│   └── Opens: AMCExecutionDetail modal
│       └── If execution failed → Shows ExecutionErrorDetails ⚠️ (NEW)
│           └── User can click "View Full Error" → ErrorDetailsModal 🔍 (NEW)
│
└── 5. Executions List (/executions)
    ├── User sees all executions
    └── Clicks on failed execution
        └── Opens: AMCExecutionDetail modal
            └── Shows ExecutionErrorDetails with full error info ⚠️ (NEW)
```

### 📍 Specific Locations Where Errors Display

#### 1. **ExecutionModal** (`/components/workflows/ExecutionModal.tsx`)
- **When**: After executing a workflow that fails
- **Where**: In the execution status section
- **What Shows**: 
  - Basic error message with copy button
  - "View Full Error" button to open detailed modal
  
#### 2. **AMCExecutionDetail** (`/components/executions/AMCExecutionDetail.tsx`)
- **When**: Viewing details of any failed AMC execution
- **Where**: In the execution details panel
- **What Shows**:
  - Full ExecutionErrorDetails component
  - Includes errorDetails from AMC API
  - Shows SQL query that failed
  - Copy buttons for each error section
  - "View Full Error" button for comprehensive view

#### 3. **ErrorDetailsModal** (NEW - `/components/executions/ErrorDetailsModal.tsx`)
- **When**: User clicks "View Full Error" button
- **Where**: Full-screen modal overlay (z-index 70)
- **What Shows**:
  - **Structured View**: Parsed error components
    - Error code
    - Validation errors list
    - Query validation details
    - Failure reason
  - **Raw View**: Complete error text
  - **SQL View**: Failed query with syntax highlighting
  - Copy buttons for each section
  - Download error report as JSON
  - Common AMC issues help section

### 🎯 User Scenarios

#### Scenario 1: Executing from Instance Workflows
```
1. User navigates to: /instances/my-instance-id
2. Sees list of workflows
3. Clicks "Execute" on a workflow
4. ExecutionModal opens
5. Configures parameters and executes
6. Query fails with syntax error
7. Sees error in ExecutionModal with copy button ✅
8. Clicks "View Full Error" for details ✅
9. Can copy error, download report, view SQL ✅
```

#### Scenario 2: Viewing Past Failed Execution
```
1. User navigates to: /executions
2. Sees list with failed executions marked in red
3. Clicks on a failed execution
4. AMCExecutionDetail modal opens
5. Sees comprehensive error with all details ✅
6. Can expand to full error modal ✅
```

#### Scenario 3: Re-running Failed Query
```
1. In AMCExecutionDetail modal of failed execution
2. Sees error details
3. Copies error message for debugging
4. Clicks "Re-run" button
5. Makes corrections based on error info
6. Executes again
```

### 🔧 Technical Implementation

The error display enhancement touches these components:

1. **Backend** (`amc_manager/services/amc_api_client.py`)
   - Captures errorDetails from AMC API response
   - Includes: failureReason, validationErrors, errorCode, queryValidation

2. **API Layer** (`amc_manager/api/supabase/amc_executions.py`)
   - Passes errorDetails through to frontend
   - Preserves all error information from AMC

3. **Frontend Components**:
   - `ExecutionErrorDetails.tsx` - Basic error display with copy
   - `ErrorDetailsModal.tsx` - Full-screen detailed view
   - `AMCExecutionDetail.tsx` - Integration point for error display

### 💡 Key Features

- **One-click copy** for error messages
- **Structured parsing** of AMC error responses
- **SQL context** showing exactly what failed
- **Export capability** for sharing with team
- **Contextual help** for common AMC errors
- **Multiple view modes** (Structured, Raw, SQL)

### 🎨 Visual Indicators

- **Red background** for error sections
- **Copy icon** changes to checkmark when copied
- **Maximize icon** to open full error view
- **Color-coded** error sections (red, yellow, orange)
- **Monospace font** for code and SQL display