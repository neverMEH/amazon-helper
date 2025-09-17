# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-16-report-builder-flow-update/spec.md

> Created: 2025-09-16
> Version: 1.0.0

## Technical Requirements

### Step 1: Parameter Selection Enhancement
- **Component**: Update `ReportBuilderParameters.tsx` to include lookback window selection
- **UI Elements**:
  - Date picker component for custom date range selection
  - Predefined lookback buttons: 7 days, 14 days, 30 days, Last Week, Last Month
  - Toggle between calendar and relative date modes
- **State Management**: Store selected date range in component state with format `{ startDate: string, endDate: string, lookbackType: 'custom' | 'relative', lookbackValue?: number }`
- **Validation**: Ensure date ranges don't exceed AMC's 14-month data retention limit

### Step 2: Schedule Type Selection
- **Component**: Rename and refactor execution step to `ReportScheduleSelection.tsx`
- **Schedule Options**:
  - **Once**: Immediate single execution
  - **Scheduled**: Recurring with frequency options (daily, weekly, monthly)
  - **Backfill with Schedule**: Historical 365-day processing plus ongoing schedule
- **Backfill Configuration**:
  - Segmentation picker: Daily, Weekly, Monthly chunks
  - Progress calculation: Total segments = 365 / segment_size
  - Parallel processing: Up to 10 concurrent segment executions
- **Database Schema**: Update `workflow_schedules` table to include `backfill_config` JSONB column

### Step 3: Review Interface
- **Component**: Create new `ReportReviewStep.tsx` component
- **Display Elements**:
  - SQL query preview with Monaco Editor (read-only mode)
  - Parameter summary table
  - Lookback window visualization
  - Schedule configuration summary
  - Estimated execution time and data volume
- **Preview Generation**: Generate sample SQL with parameter substitution for review

### Step 4: Submission Flow
- **Component**: Simplify existing submission to `ReportSubmission.tsx`
- **Actions**:
  - Single "Execute Report" button with loading state
  - Success: Redirect to execution monitoring view
  - Error: Display inline error with retry option
- **API Calls**:
  - For backfill: POST `/api/data-collections/` with backfill configuration
  - For scheduled: POST `/api/schedules/` with schedule configuration
  - For once: POST `/api/workflows/{id}/execute`

## Approach

### Frontend Architecture
- **Step-based Navigation**: Implement linear wizard flow with back/next navigation
- **State Management**: Use React Hook Form for form state and validation
- **Component Reusability**: Extract common date picker and schedule selector components
- **Type Safety**: Define TypeScript interfaces for all configuration objects

### Backend Implementation
- **Service Layer Pattern**: Extend existing `DataCollectionService` and `ScheduleService`
- **Async Processing**: Use background task queue for backfill operations
- **Progress Tracking**: Real-time updates via database polling and frontend refresh

### API Design
- **RESTful Endpoints**: Follow existing pattern with proper HTTP methods
- **Request Validation**: Use Pydantic schemas for input validation
- **Error Handling**: Standardized error responses with actionable messages

### Database Design
- **JSONB Storage**: Flexible configuration storage for varying schedule types
- **Indexing Strategy**: Optimize for date range and status queries
- **Migration Safety**: Backward-compatible schema changes

## External Dependencies

### Frontend Dependencies
- **React Hook Form**: Form state management and validation
- **React Datepicker**: Enhanced date selection component
- **Monaco Editor**: Read-only SQL preview
- **Chart.js**: Progress visualization for backfill operations

### Backend Dependencies
- **Croniter**: Enhanced cron expression parsing for schedules
- **asyncio**: Parallel execution management for backfill segments
- **Celery** (future): Background task queue for long-running operations

### Database Dependencies
- **PostgreSQL 14+**: JSONB column support and indexing
- **Supabase**: Real-time subscription capabilities for progress updates

### AMC API Constraints
- **Rate Limits**: 5 requests per second per account
- **Data Retention**: 14-month maximum lookback
- **Execution Timeout**: 30-minute maximum per query
- **Concurrent Limits**: 10 parallel executions per instance