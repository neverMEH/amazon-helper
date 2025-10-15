# Template Execution Wizard - Testing Checklist

> Created: 2025-10-15
> Feature: Template Execution Wizard
> Spec: @.agent-os/specs/2025-10-15-template-execution-wizard/spec.md

## Pre-Testing Setup

- [ ] Backend server running: `python main_supabase.py`
- [ ] Frontend server running: `cd frontend && npm run dev`
- [ ] Check Swagger UI available at: `http://localhost:8001/docs`
- [ ] Have at least one AMC instance configured with templates
- [ ] User authenticated with valid Amazon OAuth tokens

---

## Backend API Testing

### Execute Template Endpoint

- [ ] **Endpoint visible in Swagger UI**
  - Navigate to http://localhost:8001/docs
  - Find "Template Execution" tag
  - Verify `POST /api/instances/{instance_id}/templates/{template_id}/execute` endpoint exists

- [ ] **Test immediate execution**
  - Use "Try it out" in Swagger UI
  - Provide valid instance UUID and template ID
  - Submit request with valid date range
  - Verify 201 response with execution details
  - Check execution appears in `workflow_executions` table

- [ ] **Test with Snowflake enabled**
  - Set `snowflake_enabled: true` in request
  - Optionally provide table name and schema
  - Verify metadata stored correctly in execution record

- [ ] **Test error cases**
  - Invalid template ID → 404 response
  - Invalid instance UUID → 404 response
  - Invalid date format → 400 validation error
  - Template from different instance → 404 response

### Schedule Creation Endpoint

- [ ] **Endpoint visible in Swagger UI**
  - Verify `POST /api/instances/{instance_id}/templates/{template_id}/schedule` endpoint exists

- [ ] **Test daily schedule**
  - frequency: "daily"
  - time: "09:00"
  - timezone: "America/New_York"
  - Verify 201 response with schedule details
  - Check schedule created in `workflow_schedules` table
  - Verify workflow created in `workflows` table

- [ ] **Test weekly schedule**
  - frequency: "weekly"
  - day_of_week: 1 (Monday)
  - lookback_days: 30
  - date_range_type: "rolling"
  - Verify cron expression: "00 09 * * 1"

- [ ] **Test monthly schedule**
  - frequency: "monthly"
  - day_of_month: 15
  - Verify cron expression: "00 09 15 * *"

- [ ] **Test error cases**
  - Invalid frequency → 400 validation error
  - Invalid time format → 400 validation error
  - lookback_days out of range (< 1 or > 365) → 400 validation error

---

## Frontend Testing

### Wizard Access

- [ ] **Navigation to Templates tab**
  - Go to Instance Detail page
  - Click "Templates" tab
  - Verify templates list displays
  - If no templates, create one for testing

- [ ] **"Use Template" button**
  - Click "Use Template" on any template card
  - Verify wizard modal opens (NOT navigation to Query Builder)
  - Verify template name visible in wizard header

### Step 1: Template Display

- [ ] **Template information displayed**
  - Template name shown as heading
  - Instance badge with name visible
  - Brand badge visible (if instance has brands)
  - SQL query displayed in read-only Monaco editor (300px height)
  - Monaco editor has syntax highlighting

- [ ] **Navigation**
  - "Next" button visible and clickable
  - Clicking "Next" advances to Step 2
  - "X" button closes wizard
  - Closing wizard returns to templates list

### Step 2: Execution Type Selection

- [ ] **Step indicator**
  - Step 2 highlighted as active
  - Step 1 marked as completed (green checkmark)
  - Steps 3 and 4 shown as pending (gray)

- [ ] **Run Once option**
  - Card displays with PlayCircle icon
  - Title: "Run Once"
  - Description explains immediate execution
  - Clicking card selects it (blue border)

- [ ] **Recurring Schedule option**
  - Card displays with Clock icon
  - Title: "Recurring Schedule"
  - Description explains automatic execution
  - Clicking card selects it (blue border)

- [ ] **Navigation**
  - "Back" button returns to Step 1
  - "Next" button advances to Step 3
  - Selected option is persisted when navigating back/forward

### Step 3A: Date Range (Run Once Path)

- [ ] **AMC Data Lag Warning**
  - Yellow banner visible at top
  - Explains 14-day processing lag
  - AlertCircle icon present

- [ ] **Rolling Window Toggle**
  - Checkbox labeled "Use rolling window"
  - Checked by default
  - Clicking toggles rolling window mode

- [ ] **Window Size Presets**
  - Buttons for 7, 14, 30, 60, 90 days visible
  - Default: 30 days selected (blue button)
  - Clicking preset updates window size
  - Custom input field below presets

- [ ] **Date Range Calculation** (Rolling Mode)
  - Default dates calculated correctly:
    - End date = today - 14 days (AMC lag)
    - Start date = end date - 30 days
  - Changing window size updates dates
  - Date format: YYYY-MM-DD

- [ ] **Manual Date Selection** (Rolling Disabled)
  - Uncheck rolling window toggle
  - Start and end date pickers enabled
  - Selecting dates updates range
  - Date pickers disabled when rolling enabled

- [ ] **Date Range Preview**
  - Gray card shows "Date Range Preview:"
  - Displays calculated start and end dates
  - Shows day count: "(X days)"
  - Updates in real-time with changes

- [ ] **Navigation**
  - "Back" returns to Step 2
  - "Next" advances to Step 4 (Review)
  - Date range state persisted when navigating

### Step 3B: Schedule Configuration (Recurring Path)

- [ ] **DateRangeStep Component**
  - Existing DateRangeStep component renders
  - All schedule frequency options available (daily/weekly/monthly)
  - Time picker functional
  - Timezone selector functional

- [ ] **Rolling Date Range**
  - Lookback days input field available
  - Date range type selector (rolling/fixed)
  - Window size presets available
  - Values persist when navigating back/forward

- [ ] **Day Selection**
  - Weekly: Day of week selector (Sunday-Saturday)
  - Monthly: Day of month input (1-31)
  - Defaults work correctly (Monday for weekly, 1st for monthly)

- [ ] **Navigation**
  - "Back" returns to Step 2
  - "Next" advances to Step 4 (Review)
  - Schedule config state persisted

### Step 4: Review & Submit

- [ ] **Step indicator**
  - Step 4 highlighted as active
  - Steps 1-3 marked completed (green checkmarks)

- [ ] **Execution Details Section**
  - Auto-generated name displayed correctly
    - Format: "{Brand} - {Template} - {StartDate} - {EndDate}"
    - Example: "Nike Brand - Top Products - 2025-10-01 - 2025-10-31"
  - Execution type badge visible (green for Run Once, blue for Recurring)
  - Instance name shown
  - Template name shown

- [ ] **Date/Schedule Details Section** (Run Once)
  - Date range displayed: "YYYY-MM-DD to YYYY-MM-DD"
  - Matches dates from Step 3

- [ ] **Schedule Details Section** (Recurring)
  - Formatted schedule description shown
    - Daily: "Every day at HH:mm TIMEZONE"
    - Weekly: "Every [Day] at HH:mm TIMEZONE"
    - Monthly: "Every month on the [Nth] at HH:mm TIMEZONE"
  - Rolling window info (if enabled): "X days lookback"

- [ ] **SQL Preview (Collapsible)**
  - "SQL Query" header with eye icon
  - Clicking toggles expansion
  - When expanded: read-only Monaco editor (250px height)
  - SQL matches original template query

- [ ] **Snowflake Integration** (Run Once Only)
  - Checkbox: "Upload results to Snowflake after execution"
  - Unchecked by default
  - When checked:
    - Table name input appears (indented)
    - Schema name input appears (indented)
    - Help text shown: "Results will be automatically uploaded..."
  - Not visible for Recurring schedule path

- [ ] **Navigation**
  - "Back" button returns to Step 3
  - Submit button shows correct text:
    - Run Once: "Execute Now"
    - Recurring: "Create Schedule"

### Submission Testing (Run Once)

- [ ] **Submit execution**
  - Click "Execute Now" button
  - Button shows loading spinner
  - Button text changes to "Executing..."
  - Button disabled during submission

- [ ] **Success flow**
  - Toast notification: "Template execution started successfully!"
  - Modal closes
  - Browser navigates to `/executions` page
  - New execution visible in list
  - Execution status shows "PENDING" or "RUNNING"
  - Template usage count incremented (back on templates tab)

- [ ] **Error handling**
  - Test with invalid data (modify request in dev tools)
  - Toast shows error message
  - Modal stays open
  - Can retry submission

### Submission Testing (Recurring)

- [ ] **Submit schedule**
  - Click "Create Schedule" button
  - Button shows loading spinner
  - Button text changes to "Creating Schedule..."
  - Button disabled during submission

- [ ] **Success flow**
  - Toast notification: "Schedule created successfully!"
  - Modal closes
  - Browser navigates to `/schedules` page
  - New schedule visible in list
  - Schedule shows next run time
  - Workflow created and linked
  - Template usage count incremented

- [ ] **Error handling**
  - Test with invalid schedule config
  - Toast shows error message
  - Modal stays open
  - Can retry submission

---

## Integration Testing

### Cache Invalidation

- [ ] **Template usage count updates**
  - Note usage count before using template
  - Complete wizard flow
  - Return to Templates tab
  - Verify usage count incremented by 1

- [ ] **Executions list updates**
  - Run once execution
  - Navigate to Executions page
  - Verify new execution in list without manual refresh

- [ ] **Schedules list updates**
  - Create recurring schedule
  - Navigate to Schedules page
  - Verify new schedule in list without manual refresh

### Database Verification

- [ ] **workflow_executions table** (Run Once)
  - Record created with correct instance_id
  - execution_id format: "exec_<12-char-hex>"
  - query_text matches template SQL
  - metadata contains:
    - execution_name
    - template_id
    - template_name
    - snowflake_enabled
    - snowflake_table_name (if provided)
    - snowflake_schema_name (if provided)
  - execution_parameters contains timeWindowStart and timeWindowEnd

- [ ] **workflows table** (Recurring)
  - Workflow created with correct instance_id
  - workflow_id format: "wf_<12-char-hex>"
  - sql_query matches template SQL
  - metadata contains:
    - source: "instance_template"
    - template_id
    - template_name

- [ ] **workflow_schedules table** (Recurring)
  - Schedule created linked to workflow
  - schedule_id format: "sched_<12-char-hex>"
  - cron_expression correct for frequency
  - lookback_days set if provided
  - date_range_type set if provided
  - is_active = true

### AMC API Integration

- [ ] **Execution created in AMC** (Run Once)
  - Check AMC API logs
  - Verify create_workflow_execution called
  - amc_execution_id returned and stored
  - AMC instance ID used (not UUID)
  - entity_id passed correctly

- [ ] **No immediate AMC call** (Recurring)
  - Verify no AMC API call on schedule creation
  - Schedule executor will handle execution later

---

## Browser Compatibility

- [ ] **Chrome/Edge** (Chromium-based)
  - All wizard steps render correctly
  - Date pickers work
  - Monaco editor loads and displays SQL
  - Modals display properly

- [ ] **Firefox**
  - All functionality works
  - Styling consistent

- [ ] **Safari** (if available)
  - Date picker native behavior
  - No layout issues

---

## Responsive Design

- [ ] **Desktop** (1920x1080)
  - Wizard modal sized appropriately
  - All content visible without scrolling (except SQL in Step 1)
  - Step indicator readable

- [ ] **Laptop** (1366x768)
  - Modal fits on screen
  - Vertical scrolling works if needed
  - No horizontal overflow

- [ ] **Tablet** (768px width)
  - Wizard responsive
  - Touch targets large enough
  - Modal not too wide

---

## Edge Cases & Error Scenarios

- [ ] **No templates available**
  - Create at least one template for testing
  - Empty state shows "Create Template" button

- [ ] **Instance with no brands**
  - Auto-generated name uses instance name
  - Format: "{InstanceName} - {Template} - {Dates}"

- [ ] **Very long template names**
  - Name truncates gracefully in wizard
  - Full name visible in auto-generated execution name

- [ ] **Very long SQL queries**
  - Monaco editor scrollable
  - No performance issues
  - Query not truncated in database

- [ ] **Invalid date ranges**
  - Start date after end date → UI validation
  - Dates in future → No validation (user's choice)

- [ ] **Network errors**
  - Slow network → loading spinner shown
  - Network failure → error toast shown
  - Can retry after error

- [ ] **Session expiration**
  - JWT expired → 401 error
  - Redirect to login or show re-auth message

---

## Performance Testing

- [ ] **Wizard opens quickly**
  - Modal appears in < 500ms
  - No lag when clicking "Use Template"

- [ ] **Step transitions smooth**
  - No flicker when navigating steps
  - State transitions immediate

- [ ] **Monaco editor loads**
  - Syntax highlighting appears quickly
  - No blocking during load

- [ ] **API response times**
  - Execute endpoint: < 2 seconds
  - Schedule endpoint: < 500ms

---

## Accessibility Testing

- [ ] **Keyboard navigation**
  - Tab through all form fields
  - Enter key submits when appropriate
  - Escape key closes modal

- [ ] **Screen reader**
  - Step indicator announces current step
  - Form labels read correctly
  - Error messages announced

- [ ] **Focus management**
  - Focus returns to trigger button when closing
  - Focus moves to first field on step change

---

## Security Testing

- [ ] **Template ownership verification**
  - Cannot execute another user's template
  - API returns 404 for unauthorized access

- [ ] **Instance access control**
  - Cannot execute template on instance without access
  - API verifies user has instance permission

- [ ] **SQL injection protection**
  - Template SQL stored as-is (no modification)
  - No SQL injection risk in API parameters

- [ ] **XSS protection**
  - Template names and descriptions sanitized
  - No script execution in wizard UI

---

## Regression Testing

- [ ] **Existing template CRUD still works**
  - Create new template
  - Edit existing template
  - Delete template
  - No impact from wizard changes

- [ ] **Query Builder still accessible**
  - Can navigate to Query Builder directly
  - No broken navigation

- [ ] **Other wizard features unaffected**
  - Schedule Wizard still works
  - Report Builder wizard still works

---

## Post-Testing Cleanup

- [ ] Document any bugs found
- [ ] Create GitHub issues for bugs
- [ ] Update this checklist if new test cases discovered
- [ ] Verify all created test executions/schedules can be deleted

---

## Sign-Off

- [ ] All critical tests passing
- [ ] All high-priority tests passing
- [ ] Known issues documented
- [ ] Feature ready for production deployment

**Tested By:** ___________________________
**Date:** ___________________________
**Notes:** ___________________________
