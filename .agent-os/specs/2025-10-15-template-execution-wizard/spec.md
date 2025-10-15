# Spec Requirements Document

> Spec: Template Execution Wizard
> Created: 2025-10-15
> Status: Planning

## Overview

Create a streamlined 4-step wizard that enables users to execute Instance Templates directly with ad-hoc or recurring schedule options, replacing the current "Use Template" navigation to Query Builder with an immediate execution path that includes Snowflake integration.

## User Stories

### Quick Template Execution

As an AMC analyst, I want to execute my saved instance templates immediately with a date range, so that I can run common queries without navigating through the Query Builder and manually configuring workflows.

**Workflow**: User navigates to Instance Detail → Templates tab, clicks "Use Template" on a saved template, sees a 4-step wizard with pre-filled SQL and instance, selects "Run Once", picks a date range (or uses default last 30 days), reviews the configuration with Snowflake option, and submits. The execution starts immediately and the user is redirected to the Executions page to monitor progress.

### Schedule Recurring Template Execution

As a campaign manager, I want to schedule my instance templates to run automatically on a recurring basis, so that I can receive regular reports without manual intervention.

**Workflow**: User clicks "Use Template" on an instance template, progresses through the wizard, selects "Recurring Schedule", configures the schedule frequency (daily/weekly/monthly) with rolling date range support, reviews the full configuration, and submits. A schedule is created and the user is redirected to the Schedules page to see the next execution time.

### Automated Workflow Naming

As a data analyst, I want template executions to have clear, descriptive names automatically generated, so that I can easily identify what each execution represents without manually naming them.

**Workflow**: When user submits a template execution (either run once or recurring), the system automatically generates a name in the format "{Instance Brand Name} - {Template Name} - {Start Date} - {End Date}" (e.g., "Nike Brand - Top Products Analysis - 2025-10-01 - 2025-10-31"). This name appears in the executions list and schedule list for easy identification.

## Spec Scope

1. **Template Execution Wizard Component** - 4-step modal wizard with step indicator, navigation, and validation
2. **Run Once Execution Path** - Step 2 → Step 3 date range selection with calendar picker and rolling window support → Step 4 review with Snowflake toggle
3. **Recurring Schedule Path** - Step 2 → Step 3 schedule configuration reusing existing DateRangeStep component → Step 4 review
4. **Backend API Endpoints** - Two new endpoints for executing templates immediately and creating schedules from templates
5. **Auto-Generated Naming** - Service for generating descriptive workflow names based on instance brand, template name, and date range

## Out of Scope

- Parameter editing (templates execute with their saved SQL as-is)
- Template modification during execution flow (use template editor instead)
- Multi-template batch execution
- Custom naming by user (auto-generated names only)
- Template versioning or execution history tracking
- Cost estimation before execution

## Expected Deliverable

1. User can click "Use Template" and immediately configure execution through a 4-step wizard without navigating to Query Builder
2. Run Once executions start immediately with specified date range and optional Snowflake integration
3. Recurring schedules are created with rolling date range support and appear in the Schedules page
4. All executions and schedules have auto-generated descriptive names following the pattern: "{Instance Brand} - {Template Name} - {Dates}"

## Spec Documentation

- Tasks: @.agent-os/specs/2025-10-15-template-execution-wizard/tasks.md
- Technical Specification: @.agent-os/specs/2025-10-15-template-execution-wizard/sub-specs/technical-spec.md
- API Specification: @.agent-os/specs/2025-10-15-template-execution-wizard/sub-specs/api-spec.md
