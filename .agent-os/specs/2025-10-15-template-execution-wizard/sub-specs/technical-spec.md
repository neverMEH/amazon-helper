# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-10-15-template-execution-wizard/spec.md

## Technical Requirements

### Frontend Requirements

#### 1. TemplateExecutionWizard Component

**Location**: `frontend/src/components/instances/TemplateExecutionWizard.tsx`

**Props Interface**:
```typescript
interface TemplateExecutionWizardProps {
  isOpen: boolean;
  onClose: () => void;
  template: InstanceTemplate;  // From types/instanceTemplate.ts
  instanceInfo: {
    id: string;              // UUID for API calls
    instanceId: string;      // AMC instance ID (e.g., "amcibersblt")
    instanceName: string;
    brands?: string[];
  };
  onComplete: () => void;  // Called after successful submission
}
```

**State Management**:
```typescript
const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);
const [executionType, setExecutionType] = useState<'once' | 'recurring'>('once');
const [dateRange, setDateRange] = useState<{ start: string; end: string }>(defaultDateRange);
const [useRollingWindow, setUseRollingWindow] = useState(false);
const [rollingWindowDays, setRollingWindowDays] = useState(30);
const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>(defaultScheduleConfig);
const [snowflakeEnabled, setSnowflakeEnabled] = useState(false);
const [snowflakeTableName, setSnowflakeTableName] = useState('');
const [snowflakeSchemaName, setSnowflakeSchemaName] = useState('');
```

**Step Flow Logic**:
- Step 1: Display (SQL preview, template info, instance badge)
- Step 2: Execution type selection (radio buttons)
- Step 3:
  - If `executionType === 'once'`: Date range picker with rolling window option
  - If `executionType === 'recurring'`: Reuse `DateRangeStep` component from schedules
- Step 4: Review screen with all configuration + Snowflake toggle

**Default Date Range Calculation** (Step 1 useEffect):
```typescript
const AMC_LAG_DAYS = 14;
const DEFAULT_WINDOW_DAYS = 30;

const today = new Date();
const endDate = new Date(today);
endDate.setDate(endDate.getDate() - AMC_LAG_DAYS);  // Account for AMC lag

const startDate = new Date(endDate);
startDate.setDate(startDate.getDate() - DEFAULT_WINDOW_DAYS);

setDateRange({
  start: startDate.toISOString().split('T')[0],
  end: endDate.toISOString().split('T')[0]
});
```

**Auto-Generated Name Format**:
```typescript
const generateExecutionName = (
  brandName: string,
  templateName: string,
  startDate: string,
  endDate: string
): string => {
  return `${brandName} - ${templateName} - ${startDate} - ${endDate}`;
};

// Example: "Nike Brand - Top Products Analysis - 2025-10-01 - 2025-10-31"
```

**Submission Logic**:
```typescript
const handleSubmit = async () => {
  const brandName = instanceInfo.brands?.[0] || instanceInfo.instanceName;
  const executionName = generateExecutionName(
    brandName,
    template.name,
    dateRange.start,
    dateRange.end
  );

  if (executionType === 'once') {
    // Call execute endpoint
    const payload = {
      name: executionName,
      timeWindowStart: dateRange.start,
      timeWindowEnd: dateRange.end,
      snowflake_enabled: snowflakeEnabled,
      snowflake_table_name: snowflakeTableName || undefined,
      snowflake_schema_name: snowflakeSchemaName || undefined,
    };

    await templateExecutionService.execute(instanceInfo.id, template.templateId, payload);
    toast.success('Template execution started!');
    navigate('/executions');
  } else {
    // Call schedule endpoint
    const payload = {
      name: executionName,
      schedule_config: {
        frequency: scheduleConfig.type,
        time: scheduleConfig.executeTime,
        lookback_days: scheduleConfig.lookbackDays,
        date_range_type: scheduleConfig.dateRangeType,
        timezone: scheduleConfig.timezone,
        // ... other schedule fields from DateRangeStep
      },
    };

    await templateExecutionService.createSchedule(instanceInfo.id, template.templateId, payload);
    toast.success('Schedule created successfully!');
    navigate('/schedules');
  }

  onComplete();
};
```

#### 2. TypeScript Types

**Location**: `frontend/src/types/templateExecution.ts`

```typescript
export interface TemplateExecutionRequest {
  name: string;
  timeWindowStart: string;  // ISO date format: 2025-10-15
  timeWindowEnd: string;
  snowflake_enabled?: boolean;
  snowflake_table_name?: string;
  snowflake_schema_name?: string;
}

export interface TemplateScheduleRequest {
  name: string;
  schedule_config: {
    frequency: 'daily' | 'weekly' | 'monthly';
    time: string;  // HH:mm format
    lookback_days?: number;
    date_range_type?: 'rolling' | 'fixed';
    window_size_days?: number;
    timezone: string;
    day_of_week?: number;  // For weekly (0-6)
    day_of_month?: number;  // For monthly (1-31)
  };
}

export interface TemplateExecutionResponse {
  workflow_execution_id: string;
  amc_execution_id: string;
  status: string;
  created_at: string;
}

export interface TemplateScheduleResponse {
  schedule_id: string;
  workflow_id: string;
  next_run_at: string;
  created_at: string;
}
```

#### 3. API Service

**Location**: `frontend/src/services/templateExecutionService.ts`

```typescript
import api from './api';
import type { TemplateExecutionRequest, TemplateExecutionResponse, TemplateScheduleRequest, TemplateScheduleResponse } from '../types/templateExecution';

export const templateExecutionService = {
  /**
   * Execute a template immediately (run once)
   */
  execute: async (
    instanceId: string,  // UUID
    templateId: string,
    data: TemplateExecutionRequest
  ): Promise<TemplateExecutionResponse> => {
    const response = await api.post(
      `/instances/${instanceId}/templates/${templateId}/execute`,
      data
    );
    return response.data;
  },

  /**
   * Create a recurring schedule for a template
   */
  createSchedule: async (
    instanceId: string,
    templateId: string,
    data: TemplateScheduleRequest
  ): Promise<TemplateScheduleResponse> => {
    const response = await api.post(
      `/instances/${instanceId}/templates/${templateId}/schedule`,
      data
    );
    return response.data;
  },
};
```

#### 4. Component Integration

**Update**: `frontend/src/components/instances/InstanceTemplates.tsx`

**Changes**:
```typescript
// Add state for wizard modal
const [executionWizardOpen, setExecutionWizardOpen] = useState(false);
const [selectedTemplateForExecution, setSelectedTemplateForExecution] = useState<InstanceTemplate | null>(null);

// Update "Use Template" button handler
const handleUseTemplate = async (template: InstanceTemplate) => {
  // Increment usage count
  await instanceTemplateService.useTemplate(instanceId, template.templateId);

  // Open execution wizard instead of navigating
  setSelectedTemplateForExecution(template);
  setExecutionWizardOpen(true);
};

// Add wizard component at end of render
return (
  <>
    {/* Existing template list UI */}

    {/* Template Execution Wizard */}
    {executionWizardOpen && selectedTemplateForExecution && (
      <TemplateExecutionWizard
        isOpen={executionWizardOpen}
        onClose={() => {
          setExecutionWizardOpen(false);
          setSelectedTemplateForExecution(null);
        }}
        template={selectedTemplateForExecution}
        instanceInfo={{
          id: instance.id,
          instanceId: instance.instance_id,
          instanceName: instance.instance_name,
          brands: instance.brands,
        }}
        onComplete={() => {
          setExecutionWizardOpen(false);
          setSelectedTemplateForExecution(null);
          // Refetch templates to update usage count
          queryClient.invalidateQueries(['instanceTemplates', instanceId]);
        }}
      />
    )}
  </>
);
```

### Backend Requirements

#### 1. Pydantic Schemas

**Location**: `amc_manager/schemas/template_execution.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TemplateExecutionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    timeWindowStart: str = Field(..., description="ISO date format: YYYY-MM-DD")
    timeWindowEnd: str = Field(..., description="ISO date format: YYYY-MM-DD")
    snowflake_enabled: Optional[bool] = False
    snowflake_table_name: Optional[str] = None
    snowflake_schema_name: Optional[str] = None

class ScheduleConfigSchema(BaseModel):
    frequency: str = Field(..., pattern="^(daily|weekly|monthly)$")
    time: str = Field(..., description="HH:mm format")
    lookback_days: Optional[int] = Field(None, ge=1, le=365)
    date_range_type: Optional[str] = Field(None, pattern="^(rolling|fixed)$")
    window_size_days: Optional[int] = Field(None, ge=1, le=365)
    timezone: str
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)

class TemplateScheduleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    schedule_config: ScheduleConfigSchema

class TemplateExecutionResponse(BaseModel):
    workflow_execution_id: str
    amc_execution_id: Optional[str]
    status: str
    created_at: datetime

class TemplateScheduleResponse(BaseModel):
    schedule_id: str
    workflow_id: str
    next_run_at: Optional[datetime]
    created_at: datetime
```

#### 2. FastAPI Router

**Location**: `amc_manager/api/supabase/template_execution.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from ...auth.jwt_handler import get_current_user
from ...services.instance_template_service import InstanceTemplateService
from ...services.workflow_service import WorkflowService
from ...services.schedule_service import ScheduleService
from ...services.amc_api_client_with_retry import amc_api_client_with_retry
from ...schemas.template_execution import (
    TemplateExecutionRequest,
    TemplateExecutionResponse,
    TemplateScheduleRequest,
    TemplateScheduleResponse,
)

router = APIRouter()

@router.post(
    "/instances/{instance_id}/templates/{template_id}/execute",
    response_model=TemplateExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def execute_template(
    instance_id: str,
    template_id: str,
    request: TemplateExecutionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Execute an instance template immediately (run once) with specified date range.

    This creates a workflow execution that starts immediately.
    """
    user_id = current_user.get("user_id")
    template_service = InstanceTemplateService()
    workflow_service = WorkflowService()

    # 1. Fetch template
    template = template_service.get_template(instance_id, template_id)
    if not template or template.get('user_id') != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or access denied"
        )

    # 2. Fetch instance with entity_id
    instance = workflow_service.get_instance_with_account(instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found"
        )

    entity_id = instance['amc_accounts']['account_id']
    amc_instance_id = instance['instance_id']  # The AMC string ID

    # 3. Create workflow execution with AMC API
    execution_result = await amc_api_client_with_retry.create_workflow_execution(
        instance_id=amc_instance_id,
        user_id=user_id,
        entity_id=entity_id,
        sql_query=template['sql_query'],
        time_window_start=request.timeWindowStart,
        time_window_end=request.timeWindowEnd,
        parameters={},  # Templates don't have parameters
    )

    # 4. Store execution in database
    execution_record = workflow_service.create_execution_record({
        'user_id': user_id,
        'instance_id': instance_id,
        'amc_execution_id': execution_result.get('executionId'),
        'amc_workflow_id': execution_result.get('workflowId'),
        'query_text': template['sql_query'],
        'parameters': {},
        'status': 'PENDING',
        'metadata': {
            'execution_name': request.name,
            'template_id': template_id,
            'template_name': template['name'],
            'snowflake_enabled': request.snowflake_enabled,
            'snowflake_table_name': request.snowflake_table_name,
            'snowflake_schema_name': request.snowflake_schema_name,
        }
    })

    return TemplateExecutionResponse(
        workflow_execution_id=execution_record['id'],
        amc_execution_id=execution_result.get('executionId'),
        status='PENDING',
        created_at=execution_record['created_at'],
    )


@router.post(
    "/instances/{instance_id}/templates/{template_id}/schedule",
    response_model=TemplateScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template_schedule(
    instance_id: str,
    template_id: str,
    request: TemplateScheduleRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Create a recurring schedule for an instance template.

    This creates a workflow and schedule that will execute the template
    on the specified frequency with rolling date range support.
    """
    user_id = current_user.get("user_id")
    template_service = InstanceTemplateService()
    workflow_service = WorkflowService()
    schedule_service = ScheduleService()

    # 1. Fetch template
    template = template_service.get_template(instance_id, template_id)
    if not template or template.get('user_id') != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or access denied"
        )

    # 2. Create workflow from template
    workflow = workflow_service.create_workflow({
        'user_id': user_id,
        'instance_id': instance_id,
        'name': request.name,
        'sql_query': template['sql_query'],
        'description': f"Auto-generated from template: {template['name']}",
        'metadata': {
            'source': 'instance_template',
            'template_id': template_id,
            'template_name': template['name'],
        }
    })

    # 3. Create schedule
    schedule_config = request.schedule_config
    schedule_data = {
        'workflow_id': workflow['workflow_id'],
        'user_id': user_id,
        'name': request.name,
        'schedule_type': schedule_config.frequency,
        'timezone': schedule_config.timezone,
        'execute_time': schedule_config.time,
        'lookback_days': schedule_config.lookback_days,
        'date_range_type': schedule_config.date_range_type,
        'window_size_days': schedule_config.window_size_days,
        'default_parameters': {},
        'is_active': True,
    }

    # Add day-specific fields
    if schedule_config.frequency == 'weekly' and schedule_config.day_of_week is not None:
        schedule_data['day_of_week'] = schedule_config.day_of_week
    if schedule_config.frequency == 'monthly' and schedule_config.day_of_month is not None:
        schedule_data['day_of_month'] = schedule_config.day_of_month

    schedule = schedule_service.create_schedule(schedule_data)

    return TemplateScheduleResponse(
        schedule_id=schedule['schedule_id'],
        workflow_id=workflow['workflow_id'],
        next_run_at=schedule.get('next_run_at'),
        created_at=schedule['created_at'],
    )
```

#### 3. Router Registration

**Update**: `main_supabase.py`

```python
from amc_manager.api.supabase import template_execution

# Add to router registrations
app.include_router(
    template_execution.router,
    prefix="/api",
    tags=["template-execution"]
)
```

### UI/UX Specifications

#### Step 1: Display Step
- **Layout**: Centered card with borders
- **Components**:
  - Template name as heading (text-lg font-medium)
  - Instance badge (small pill with brand name)
  - SQL preview in read-only Monaco editor (height: 300px)
  - "Next" button (full width, indigo)

#### Step 2: Execution Type Selection
- **Layout**: Vertical stack of radio button cards
- **Options**:
  1. "Run Once" - Execute immediately with date range
  2. "Recurring Schedule" - Automatic scheduled execution
- **Styling**:
  - Each option as a card with hover effect
  - Selected card has indigo border
  - Radio button + label + description layout

#### Step 3A: Date Range Selection (Run Once)
- **Components**:
  - AMC data lag warning banner (bg-yellow-50)
  - Rolling window toggle (checkbox)
  - Window size presets (7, 14, 30, 60, 90 days buttons)
  - Custom input for window size
  - Start date picker (HTML5 date input)
  - End date picker (HTML5 date input)
  - Calculated range preview text
- **Default**: Last 30 days accounting for 14-day AMC lag

#### Step 3B: Schedule Configuration (Recurring)
- **Component**: Reuse existing `DateRangeStep` component
- **Props**: Pass `scheduleConfig` and `onChange` handler
- **Features**:
  - Frequency selector (daily/weekly/monthly)
  - Time picker
  - Day of week/month selectors
  - Rolling date range configuration
  - Lookback days input

#### Step 4: Review Step
- **Layout**: Summary card with sections
- **Sections**:
  1. **Execution Details**:
     - Auto-generated name (large, bold)
     - Execution type badge
     - Instance name
     - Template name
  2. **Date/Schedule Details**:
     - Date range (for run once)
     - OR Schedule frequency + next run time (for recurring)
  3. **SQL Preview** (collapsible):
     - Read-only Monaco editor
     - Toggle button with chevron icon
  4. **Snowflake Integration** (run once only):
     - Checkbox toggle
     - Conditional fields: table name, schema name
     - Help text about auto-generation
- **Actions**:
  - "Submit" button (indigo, full width)
  - Loading spinner during submission

### Integration Points

1. **Existing Schedule System**:
   - Reuses `DateRangeStep` component for schedule configuration
   - Reuses `ScheduleService` backend methods
   - Integrates with schedule executor service for recurring runs

2. **Snowflake Integration**:
   - Reuses existing Snowflake upload logic from report builder
   - Stores Snowflake config in execution metadata
   - Triggers upload after execution completes

3. **Workflow Execution System**:
   - Creates standard workflow execution records
   - Appears in Executions page with other executions
   - Uses existing AMC API client with retry logic

4. **Instance Template Usage Tracking**:
   - Increments template usage count when "Use Template" clicked
   - Updates `usage_count` field in database
   - Maintains existing template analytics

### Performance Considerations

1. **Modal Loading**: Lazy load wizard component to reduce initial bundle size
2. **Date Calculations**: Perform client-side to avoid API calls
3. **SQL Preview**: Use Monaco editor's built-in syntax highlighting (no extra processing)
4. **Navigation**: Use React Router's `navigate()` for instant transitions

### Error Handling

1. **Template Not Found**: Show error toast, close wizard
2. **Instance Not Found**: Show error toast, close wizard
3. **Execution Creation Failed**: Show detailed error message, stay on review step
4. **Schedule Creation Failed**: Show detailed error message, stay on review step
5. **Invalid Date Range**: Validate on Step 3, prevent next button
6. **Missing Required Fields**: Disable submit button on Step 4

### Accessibility Requirements

1. **Keyboard Navigation**: Full support for Tab/Shift+Tab through all form fields
2. **Screen Reader Labels**: aria-labels on all interactive elements
3. **Focus Management**: Auto-focus first field on each step
4. **Error Announcements**: aria-live regions for error messages
5. **Step Indicator**: aria-current for active step

### Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
