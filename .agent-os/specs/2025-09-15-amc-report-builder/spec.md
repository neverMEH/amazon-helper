# Spec Requirements Document

> Spec: AMC Report Builder
> Created: 2025-09-15

## Overview

Replace the existing workflow-based system with a streamlined Report Builder that executes AMC SQL queries directly through ad-hoc executions, eliminating workflow complexity while providing unified report management, scheduling, and dashboard visualization capabilities. This transformation enables agencies to create, run, and analyze AMC reports with reduced technical overhead and improved time-to-insight.

## User Stories

### Agency Analyst - One-Click Report Execution

As an agency analyst, I want to select a pre-built report template and run it immediately, so that I can get insights without managing SQL workflows.

The analyst navigates to the Report Builder, selects a template like "Campaign Performance Analysis," chooses their client's AMC instance, fills in date ranges and campaign filters through a dynamic form, and clicks "Run Now." The system executes the query directly via AMC's ad-hoc API, shows real-time progress, and automatically generates a dashboard with visualizations when complete. The entire process takes minutes instead of the hours required with manual workflow creation.

### Marketing Manager - Automated Recurring Reports

As a marketing manager, I want to schedule weekly performance reports that run automatically, so that I have fresh data for Monday morning client reviews.

The manager creates a report from the "Weekly ROAS Tracker" template, sets parameters for their key campaigns, and configures it to run every Monday at 3 AM EST. The system creates a schedule, executes the report automatically each week, updates the dashboard with new data, and maintains a history of all runs. The manager can pause, resume, or adjust the schedule without recreating the entire workflow.

### Data Analyst - Historical Backfill

As a data analyst, I want to backfill 6 months of historical data for a new client, so that I can perform year-over-year comparisons and trend analysis.

The analyst selects a comprehensive metrics template, configures it for their client's AMC instance, and chooses "Backfill" with a 180-day lookback period using weekly segments. The system automatically generates 26 weekly execution jobs, processes them in parallel respecting AMC rate limits, and populates a unified dashboard showing the complete historical picture. Progress tracking shows each week's status, and failed segments can be retried individually.

## Spec Scope

1. **Template-Based Report Creation** - Dynamic parameter forms generated from query template definitions with validation and preview capabilities
2. **Direct Ad-Hoc Execution** - Bypass workflow creation entirely, executing SQL directly through AMC's ad-hoc API with immediate results
3. **Flexible Scheduling System** - Support for one-time, daily, weekly, monthly, and quarterly automated report runs with timezone awareness
4. **Historical Backfill Engine** - Segmented execution for up to 365 days of historical data with parallel processing and retry mechanisms
5. **Report-Specific Dashboards** - Automatically generated visualizations from template configurations with AI insights and export capabilities

## Out of Scope

- Migration of existing workflow data to the new report system
- Custom SQL editor for creating new templates (use existing template management)
- Real-time streaming data connections
- External data source integrations beyond AMC
- Multi-instance report aggregation in a single dashboard

## Expected Deliverable

1. Report Builder interface accessible from main navigation and as a new top-level item, allowing template selection, parameter configuration, and execution with visible progress tracking
2. Automated execution of scheduled reports with email notifications on completion and dashboard updates reflecting the latest data
3. Successfully backfilled historical data respecting AMC's 14-day lag and 365-day maximum lookback with complete execution history and retry capabilities