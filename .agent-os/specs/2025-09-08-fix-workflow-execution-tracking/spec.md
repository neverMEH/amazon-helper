# Spec Requirements Document

> Spec: Fix Workflow Execution ID Tracking in Data Collections
> Created: 2025-09-08
> Status: Planning

## Overview

The report_data_weeks table contains an execution_id column designed to track which workflow execution generated the data for each week, but this field is currently not being populated during data collection operations. This missing tracking makes it impossible to trace back from collected data to the specific execution that generated it, hindering debugging and data lineage capabilities.

## User Stories

### Primary User Story
**As a data analyst**, I want to be able to trace any collected weekly data back to the specific workflow execution that generated it, so that I can debug data quality issues and understand the lineage of my analytics data.

### Supporting User Stories
- **As a developer**, I want the execution_id to be automatically populated when data collection workflows run, so that the system maintains proper data lineage without manual intervention.
- **As a system administrator**, I want to be able to query which executions failed or succeeded for specific weeks, so that I can monitor collection health and troubleshoot issues.
- **As an AMC user**, I want confidence that my historical data collections are properly tracked, so that I can trust the integrity of my analytics reports.

## Spec Scope

### In Scope
1. **Database Schema Analysis**: Verify current execution_id column structure in report_data_weeks table
2. **Service Layer Fix**: Update HistoricalCollectionService to capture and pass execution IDs
3. **Database Update Methods**: Modify update_week_status method to accept and store execution_id
4. **Data Flow Validation**: Ensure execution IDs flow properly from AMC API through to database storage
5. **Backward Compatibility**: Ensure existing data collection processes continue to work during transition
6. **Testing Coverage**: Comprehensive tests for the new tracking functionality

### Technical Components Affected
- `amc_manager/services/historical_collection_service.py`
- `amc_manager/services/data_collection_service.py`  
- Database update methods in collection services
- AMC API client execution result handling
- Data collection background task processing

## Out of Scope

1. **Historical Data Backfill**: Populating execution_id for existing data_weeks records (can be addressed in separate spec)
2. **UI Changes**: Frontend modifications to display execution tracking information
3. **Reporting Enhancements**: New reports or analytics based on execution tracking
4. **Performance Optimization**: Database indexing or query optimization for execution_id lookups
5. **Cross-Collection Analysis**: Features that analyze execution patterns across different collections

## Expected Deliverable

A fully functional workflow execution tracking system where:
- Every data collection operation that executes a workflow stores the resulting execution_id in the report_data_weeks table
- The execution_id field is properly populated for all new data collection activities
- Existing data collection functionality remains unchanged and stable
- The system provides clear data lineage from collected data back to source executions
- Comprehensive test coverage validates the tracking functionality works correctly

## Root Cause Analysis

### Current Data Flow
1. `HistoricalCollectionService._collect_week_data()` executes AMC workflow
2. AMC API returns execution result with execution_id
3. Service calls `update_week_status()` with status and data
4. Database update occurs but execution_id is not passed or stored
5. execution_id information is lost

### Technical Root Cause
The `update_week_status` method in the data collection service only accepts `status` and `data` parameters, but not `execution_id`. The historical collection service receives the execution_id from the AMC API response but has no way to pass it to the database update method.

### Code Location Analysis
- **Issue Location**: `amc_manager/services/historical_collection_service.py:_collect_week_data()`
- **Missing Parameter**: `update_week_status()` method signature
- **Data Source**: AMC workflow execution response contains execution_id
- **Storage Target**: `report_data_weeks.execution_id` column (already exists in schema)

## Spec Documentation

- Tasks: @.agent-os/specs/2025-09-08-fix-workflow-execution-tracking/tasks.md
- Technical Specification: @.agent-os/specs/2025-09-08-fix-workflow-execution-tracking/sub-specs/technical-spec.md
- Database Schema: @.agent-os/specs/2025-09-08-fix-workflow-execution-tracking/sub-specs/database-schema.md
- Tests Specification: @.agent-os/specs/2025-09-08-fix-workflow-execution-tracking/sub-specs/tests.md