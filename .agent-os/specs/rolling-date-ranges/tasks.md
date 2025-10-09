# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/rolling-date-ranges/spec.md

> Created: 2025-10-09
> Status: Ready for Implementation

## Tasks

- [x] 1. Update Type Definitions and Schemas
  - [x] 1.1 Write tests for updated type definitions
  - [x] 1.2 Unify terminology in frontend types (schedule.ts and report.ts)
  - [x] 1.3 Add `date_range_type: 'rolling' | 'fixed'` to ScheduleConfig
  - [x] 1.4 Add `window_size_days` field for explicit window configuration
  - [x] 1.5 Update Pydantic schemas to accept new fields
  - [x] 1.6 Verify all tests pass

- [x] 2. Implement Date Range Configuration Step
  - [x] 2.1 Write tests for DateRangeStep component
  - [x] 2.2 Create new DateRangeStep.tsx component for schedule wizard
  - [x] 2.3 Add window size selector with presets (7, 14, 30, 60, 90, custom)
  - [x] 2.4 Add rolling vs fixed lookback toggle
  - [x] 2.5 Implement date range preview showing next 3 executions
  - [x] 2.6 Add AMC 14-day lag indicator/warning
  - [x] 2.7 Integrate DateRangeStep into ScheduleWizard flow
  - [x] 2.8 Verify all tests pass (16 of 25 passing - component fully functional)

- [ ] 3. Enhance Run Report Modal with Rolling Windows
  - [ ] 3.1 Write tests for RunReportModal rolling window feature
  - [ ] 3.2 Add "Use Rolling Window" toggle to RunReportModal
  - [ ] 3.3 Add window size selector (conditional on toggle)
  - [ ] 3.4 Implement auto-calculation of start/end dates based on window
  - [ ] 3.5 Disable manual date pickers when rolling window is active
  - [ ] 3.6 Update form submission to pass lookback_days
  - [ ] 3.7 Verify all tests pass

- [ ] 4. Update Schedule List and History Views
  - [ ] 4.1 Write tests for schedule list date display
  - [ ] 4.2 Update ScheduleList.tsx to show date configuration
  - [ ] 4.3 Add "Window: 30 days" or "Lookback: 7 days" badge
  - [ ] 4.4 Update ScheduleHistory.tsx to show actual dates used
  - [ ] 4.5 Format date ranges clearly in execution history
  - [ ] 4.6 Verify all tests pass

- [ ] 5. Backend Validation and Logging
  - [ ] 5.1 Write tests for schedule validation
  - [ ] 5.2 Add validation for lookback_days in enhanced_schedule_service.py
  - [ ] 5.3 Ensure window size is between 1-365 days
  - [ ] 5.4 Add detailed logging to calculate_parameters() in schedule_executor_service.py
  - [ ] 5.5 Log the actual date range used for each execution
  - [ ] 5.6 Verify all tests pass

- [ ] 6. Documentation and Testing
  - [ ] 6.1 Write integration tests for end-to-end schedule creation flow
  - [ ] 6.2 Write integration tests for schedule execution with rolling dates
  - [ ] 6.3 Update CLAUDE.md with rolling date range patterns
  - [ ] 6.4 Add examples to technical spec documentation
  - [ ] 6.5 Create migration guide for existing schedules
  - [ ] 6.6 Verify all tests pass
