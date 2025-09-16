# Spec Requirements Document

> Spec: Report Builder Flow Update
> Created: 2025-09-16

## Overview

Update the RecomAMP report builder to provide a comprehensive 4-step flow for creating and scheduling AMC reports. This enhancement streamlines parameters selection, introduces flexible scheduling options including 365-day backfill capability, and provides a clear review process before execution.

## User Stories

### Agency Analyst Creating Weekly Performance Reports

As an agency analyst, I want to quickly configure performance reports with flexible lookback windows and automated scheduling, so that I can deliver consistent insights to my clients without manual weekly intervention.

The analyst navigates to the Report Builder, selects a 7-day lookback window, chooses weekly scheduling, reviews the configuration to ensure it captures the right metrics, and submits. The system then automatically generates reports every week, saving 2-3 hours of manual work per client.

### Campaign Manager Performing Historical Analysis

As a campaign manager, I want to backfill an entire year of campaign performance data with consistent segmentation, so that I can identify long-term trends and seasonal patterns across my accounts.

The manager accesses Report Builder, selects parameters with monthly segmentation, chooses "backfill with schedule" to analyze 365 days of historical data, reviews the query structure and schedule configuration, then submits. The system processes the historical data in segments while maintaining the schedule for ongoing analysis.

### Marketing Director Reviewing Ad Hoc Reports

As a marketing director, I want to generate one-time reports with custom date ranges for board presentations, so that I can provide specific insights without setting up recurring schedules.

The director uses Report Builder to select a custom date range for the last quarter, chooses "once" for execution type, reviews the query to ensure it includes all necessary KPIs, and submits for immediate execution.

## Spec Scope

1. **Parameter Selection with Lookback Window** - Enhanced parameter step with calendar date selection and predefined lookback options (7, 14, 30 days, week, month)
2. **Schedule Type Selection** - Renamed execution step offering once, scheduled (with frequency options), and backfill with schedule (365-day historical with segmentation)
3. **Comprehensive Review Step** - Dedicated review interface displaying query format, lookback configuration, schedule details, and parameter summary
4. **Simplified Submission** - Streamlined final step for execution confirmation with clear success/error feedback
5. **Backfill Segmentation Logic** - Intelligent processing of historical data in user-defined segments (daily, weekly, monthly) with progress tracking

## Out of Scope

- Custom SQL query editing within the flow
- Real-time data streaming or live dashboard updates
- Cross-instance report aggregation
- Email/notification configuration for report delivery
- Advanced data transformation or post-processing features

## Expected Deliverable

1. Four-step Report Builder interface with clear progression: Parameters → Schedule → Review → Submit
2. Functional lookback window selection supporting both calendar and relative date options
3. Working backfill capability processing 365 days of historical data with configurable segmentation and integrated scheduling

## Spec Documentation

- Tasks: @.agent-os/specs/2025-09-16-report-builder-flow-update/tasks.md
- Technical Specification: @.agent-os/specs/2025-09-16-report-builder-flow-update/sub-specs/technical-spec.md