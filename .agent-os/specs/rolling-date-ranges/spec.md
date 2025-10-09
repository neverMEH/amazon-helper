# Rolling Date Ranges for Report Scheduler

> Spec: rolling-date-ranges
> Created: 2025-10-09
> Status: Planning

## Overview

Implement rolling date range functionality in the report builder scheduler so that when a report is scheduled to run repeatedly (daily, weekly, monthly), the date range automatically advances based on the execution frequency with clear UI controls for configuration.

## Problem Statement

Currently, scheduled reports can use dynamic lookback windows (e.g., "last 7 days"), but there's no UI to configure this. Users cannot easily set up rolling windows where the date range advances with each execution.

**Examples of desired behavior:**
- **Weekly schedule with 30-day window**: Sep 1-30 → Sep 8-Oct 7 → Sep 15-Oct 14
- **Daily schedule with 7-day window**: Sep 1-7 → Sep 2-8 → Sep 3-9
- **Monthly schedule with 90-day window**: Q3 → Q4 → Q1

## Current State

- ✅ Backend supports rolling dates via `lookback_days` parameter
- ✅ Backend applies 14-day AMC data lag automatically
- ✅ Database schema has `lookback_days` and `interval_days` fields
- ❌ No UI for configuring lookback days in schedule wizard
- ❌ No rolling date option in "Run Once" report modal
- ❌ Inconsistent terminology (lookback_days vs backfill_period)

## User Stories

### Story 1: Configure Rolling Date Range in Schedule
**As a** marketing analyst
**I want to** configure a schedule with a rolling 30-day window
**So that** each execution automatically queries the most recent 30 days of data

### Story 2: Preview Future Date Ranges
**As a** schedule creator
**I want to** see what date ranges will be used in future executions
**So that** I can verify the schedule is configured correctly

### Story 3: Run Ad-Hoc Report with Rolling Window
**As a** report user
**I want to** quickly run a report with a rolling 7-day window
**So that** I don't have to manually calculate dates accounting for AMC lag

### Story 4: View Historical Date Ranges
**As a** report reviewer
**I want to** see what exact date ranges were used in past executions
**So that** I can understand the data being analyzed

## Spec Scope

### In Scope

1. **Schedule Wizard Date Configuration**
   - Add "Date Range" step after timing configuration
   - Two options: "Rolling Window" or "Fixed Lookback"
   - Rolling Window: User selects window size (7, 14, 30, 60, 90 days or custom)
   - Fixed Lookback: Always query last N days from execution time
   - Preview showing example date ranges for next 3 executions
   - AMC 14-day lag clearly indicated in UI

2. **Run Once Modal Enhancement**
   - Keep existing manual date picker
   - Add "Use Rolling Window" toggle
   - When enabled, show window size selector
   - Disable start/end date pickers when rolling window is active
   - Show calculated dates with AMC lag applied

3. **Schedule Review & History**
   - Display configured date window in schedule list
   - Show actual dates used in each execution history entry
   - Indicate whether schedule uses rolling or fixed dates

4. **Backend Validation**
   - Ensure lookback_days is set when creating schedules
   - Validate window size is reasonable (1-365 days)
   - Apply AMC data lag consistently
   - Log date calculations for debugging

5. **Terminology Standardization**
   - Unify `lookback_days` and `backfill_period` usage
   - Use consistent language across UI and API
   - Add `date_range_type` field for clarity

## Out of Scope

- Changing backend date calculation logic (already works correctly)
- Modifying database schema (existing fields are sufficient)
- Data collection rolling windows (separate system in Phase 3)
- Custom date formulas beyond rolling windows
- Timezone-aware date calculations (schedules use UTC)
- Advanced date patterns (e.g., "last complete week", "month-to-date")

## Expected Deliverable

### Frontend Components
- `DateRangeStep.tsx` - New schedule wizard step for date configuration
- Updated `RunReportModal.tsx` - Add rolling window toggle
- Updated `ScheduleList.tsx` - Display date configuration
- Updated `ScheduleHistory.tsx` - Show actual dates used in executions

### Backend Updates
- Enhanced logging in `schedule_executor_service.py`
- Validation in `enhanced_schedule_service.py`
- Consistent terminology in schemas

### Type Definitions
- Add `date_range_type: 'rolling' | 'fixed'` to ScheduleConfig
- Add `window_size_days` field
- Unify lookback terminology

### User Experience Flow

**Schedule Creation:**
1. User selects workflow/report → frequency → execution time
2. **NEW: Date Range Configuration Step**
   - "How should the date range be calculated?"
   - Option A: "Rolling Window" - Always query the same window size
   - Option B: "Fixed Lookback" - Always query from execution date back N days
   - Window size selector with presets (7, 14, 30, 60, 90 days) + custom input
   - Preview: "Next 3 executions will query: [dates], [dates], [dates]"
   - Info banner: "AMC data has a 14-day lag. Dates are automatically adjusted."
3. Configure parameters → Review → Save

**Ad-Hoc Execution:**
1. User clicks "Run Report"
2. Default: Manual date picker (existing behavior)
3. **NEW: Toggle "Use Rolling Window"**
   - Shows window size selector
   - Calculates and displays start/end dates automatically
   - Updates preview when window size changes
   - Shows AMC lag adjustment

### Success Criteria

1. ✅ Users can create schedules with explicit rolling date windows
2. ✅ Schedule list clearly shows date configuration (e.g., "Rolling 30-day window")
3. ✅ Execution history shows actual dates queried (e.g., "2025-09-01 to 2025-09-30")
4. ✅ Rolling windows advance correctly with each execution
5. ✅ AMC 14-day lag is consistently applied and visible in UI
6. ✅ Preview accurately shows next 3 execution date ranges
7. ✅ All existing tests pass
8. ✅ New tests cover rolling date calculation and UI behavior

## Spec Documentation

- Tasks: @.agent-os/specs/rolling-date-ranges/tasks.md
- Technical Specification: @.agent-os/specs/rolling-date-ranges/sub-specs/technical-spec.md
- UI/UX Specification: @.agent-os/specs/rolling-date-ranges/sub-specs/ux-spec.md

## Technical Notes

- Backend `calculate_parameters()` already supports this (schedule_executor_service.py:531-582)
- `lookback_days` field exists in workflow_schedules table
- AMC 14-day lag: `end_date = now() - 14 days`
- Date format: ISO 8601 without 'Z' suffix (AMC requirement)
- No database migrations required - use existing fields

## Dependencies

- Existing schedule execution system
- WorkflowParameterEditor component
- Schedule wizard multi-step form
- AMC date calculation utilities

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| User confusion about rolling vs fixed dates | Medium | Clear UI labels, preview, and documentation |
| Incorrect date calculations | High | Extensive testing, logging, and validation |
| Breaking existing schedules | High | Backward compatibility with default values |
| AMC lag not visible to users | Medium | Explicit UI indicators and info banners |
