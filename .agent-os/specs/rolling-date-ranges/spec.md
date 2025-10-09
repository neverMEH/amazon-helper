# Rolling Date Ranges for Report Scheduler

> Spec: rolling-date-ranges
> Created: 2025-10-09
> Status: Complete
> Completed: 2025-10-09

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

## Implementation Examples

### Example 1: Weekly Schedule with 30-Day Rolling Window

**Scenario**: Marketing analyst wants to run a conversion report every Monday morning with the last 30 days of data.

**Configuration**:
```typescript
{
  type: 'weekly',
  dayOfWeek: 1, // Monday
  executeTime: '02:00',
  lookbackDays: 30,
  dateRangeType: 'rolling',
  windowSizeDays: 30
}
```

**Execution Timeline**:
- **Oct 7, 2025** (Mon) → Queries **Aug 24 - Sep 23** (Oct 7 - 14 days lag - 30 days)
- **Oct 14, 2025** (Mon) → Queries **Aug 31 - Sep 30** (Oct 14 - 14 days lag - 30 days)
- **Oct 21, 2025** (Mon) → Queries **Sep 7 - Oct 7** (Oct 21 - 14 days lag - 30 days)

Each execution gets a consistent 30-day window, automatically advanced.

### Example 2: Daily Schedule with 7-Day Fixed Lookback

**Scenario**: Performance marketer needs daily reports showing "last 7 days" (always relative to execution date).

**Configuration**:
```typescript
{
  type: 'daily',
  executeTime: '01:00',
  lookbackDays: 7,
  dateRangeType: 'fixed',
  windowSizeDays: 7
}
```

**Execution Timeline**:
- **Oct 9, 2025** → Queries **Sep 18 - Sep 25** (last 7 days with AMC lag)
- **Oct 10, 2025** → Queries **Sep 19 - Sep 26** (last 7 days with AMC lag)
- **Oct 11, 2025** → Queries **Sep 20 - Sep 27** (last 7 days with AMC lag)

Each execution queries the most recent 7 days relative to that execution.

### Example 3: Ad-Hoc Report with 60-Day Rolling Window

**Scenario**: Executive wants to quickly run a trend analysis for the last 60 days.

**UI Interaction**:
1. Click "Run Report" button
2. Toggle "Use Rolling Window" ✓
3. Select "60 days" from preset buttons
4. See calculated dates: **Aug 6 - Oct 5, 2025** (auto-calculated with AMC lag)
5. Click "Run"

**Backend Receives**:
```typescript
{
  execution_type: 'once',
  time_window_start: '2025-08-06',
  time_window_end: '2025-10-05',
  lookback_days: 60
}
```

### Example 4: Monthly Schedule with Quarterly Window

**Scenario**: Quarterly performance review report, run on the 1st of each month.

**Configuration**:
```typescript
{
  type: 'monthly',
  dayOfMonth: 1,
  executeTime: '03:00',
  lookbackDays: 90,
  dateRangeType: 'rolling',
  windowSizeDays: 90
}
```

**Execution Timeline**:
- **Nov 1, 2025** → Queries **Jul 4 - Oct 3** (Q3 data)
- **Dec 1, 2025** → Queries **Aug 3 - Nov 2** (Q3-Q4 transition)
- **Jan 1, 2026** → Queries **Sep 3 - Dec 2** (Q4 data)

Each execution covers exactly 90 days, rolling forward monthly.

## Usage Guidelines

### When to Use Rolling Window
✅ **Best for:**
- Trend analysis requiring consistent time periods
- Month-over-month or week-over-week comparisons
- Performance dashboards with historical continuity
- Reports that need to show "same window size" over time

### When to Use Fixed Lookback
✅ **Best for:**
- Real-time performance monitoring ("last 7 days")
- Dashboards showing "current state" metrics
- Alert-based reporting (recent performance)
- Any report needing "freshest available data"

### Date Range Configuration Best Practices

1. **Account for AMC Lag**: Always remember data is 14 days behind. If you need "yesterday's" data, it's not available yet.

2. **Window Size Selection**:
   - **7 days**: Short-term trends, campaign optimization
   - **14 days**: Standard reporting period, captures full attribution window
   - **30 days**: Monthly reporting, seasonal analysis
   - **60-90 days**: Quarterly trends, strategic planning

3. **Schedule Frequency vs Window Size**:
   - **Daily + 7-day window**: Smooths out day-to-day volatility
   - **Weekly + 30-day window**: Monthly trend tracking
   - **Monthly + 90-day window**: Quarterly business reviews

4. **Validation Rules**:
   - Window size: 1-365 days (enforced by backend)
   - Date range type: 'rolling' or 'fixed' only
   - All dates calculated as ISO strings without timezone

## Testing the Feature

### Manual Testing Checklist

**Schedule Creation**:
- [ ] Create daily schedule with 7-day rolling window
- [ ] Create weekly schedule with 30-day rolling window
- [ ] Create monthly schedule with 90-day rolling window
- [ ] Verify preview shows correct dates for next 3 executions
- [ ] Confirm AMC lag warning is visible
- [ ] Test custom window size input (1-365 days)
- [ ] Verify validation rejects invalid values (<1 or >365)

**Ad-Hoc Execution**:
- [ ] Toggle rolling window on/off
- [ ] Select each preset (7, 14, 30, 60, 90 days)
- [ ] Enter custom window size
- [ ] Verify dates update automatically
- [ ] Confirm manual date pickers are disabled when rolling window is active

**Schedule List & History**:
- [ ] Verify schedule shows "X days" badge with "Rolling window" label
- [ ] Check execution history shows actual dates used
- [ ] Confirm format is clear (e.g., "Sep 1 - Sep 30, 2025")

### Automated Testing

**Type Tests** (47 tests):
- `schedule.test.ts` - ScheduleConfig interface validation
- `report.test.ts` - Report and CreateReportRequest validation

**Component Tests** (25 tests):
- `DateRangeStep.test.tsx` - Window selection, preview, validation

**Backend Tests**:
- `test_schedule_schemas.py` - Pydantic schema validation (1-365 range)

**Expected Coverage**:
- Unit tests: 95%+ coverage for date calculation logic
- Component tests: 80%+ coverage for DateRangeStep
- Integration tests: E2E schedule creation with rolling dates
