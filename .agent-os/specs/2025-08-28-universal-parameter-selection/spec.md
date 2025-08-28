# Spec Requirements Document

> Spec: Universal Parameter Selection
> Created: 2025-08-28
> Status: Planning

## Overview

Implement an intelligent parameter detection and selection system for workflow queries that automatically identifies parameter types (ASIN, date, campaign) and provides contextual dropdown interfaces for parameter value selection based on the selected instance brand. This feature will enhance user experience by simplifying parameter input and ensuring data consistency across workflows.

## User Stories

### Dynamic Parameter Detection and Selection

As a workflow creator, I want to have the system automatically detect parameters in my SQL query, so that I can easily select appropriate values from contextual dropdowns without manual entry.

When I create or edit a workflow with SQL parameters, the system analyzes the query to identify parameter types (ASIN, date, campaign). For each detected parameter, it presents the appropriate selection interface - ASINs filtered by the selected instance brand, date range pickers with quick presets (last 7/14/30 days), or campaigns filtered by the instance brand. This eliminates manual parameter entry errors and ensures users select valid values that exist in their AMC instance.

### Brand-Contextual ASIN Selection

As a marketing analyst, I want to select ASINs from a dropdown that only shows products for my selected brand, so that I can quickly build queries without remembering product identifiers.

When the system detects an ASIN parameter in the workflow query, it fetches and displays all ASINs associated with the selected instance brand from the asin_asins table. Users can search, filter, and select multiple ASINs through an intuitive dropdown interface. The selected ASINs are automatically formatted correctly for the SQL query parameter substitution.

### Flexible Date Range Selection

As a report scheduler, I want to easily specify date ranges using either preset options or custom dates, so that I can quickly configure recurring reports with appropriate time windows.

When a date parameter is detected, users see a date selector with quick options (Last 7 days, Last 14 days, Last 30 days, Custom range). For custom ranges, date pickers allow selection of specific start and end dates. The system handles date formatting according to AMC requirements (no timezone suffix) and validates that end dates are after start dates.

## Spec Scope

1. **Parameter Type Detection** - Analyze SQL queries to identify ASIN, date, and campaign parameters using pattern matching
2. **Contextual ASIN Dropdown** - Fetch and display ASINs filtered by selected instance brand with search capability
3. **Date Range Selector** - Provide preset and custom date range selection with proper AMC date formatting
4. **Campaign Parameter Interface** - Display campaigns filtered by instance brand with multi-select capability
5. **Parameter Validation** - Ensure selected values are valid and properly formatted before query execution

## Out of Scope

- Automatic parameter value suggestions based on historical usage
- Complex parameter dependencies or conditional parameter logic
- Parameter validation against AMC API before execution
- Bulk parameter import from CSV or external sources

## Expected Deliverable

1. Workflow creation/edit page displays detected parameters with appropriate selection interfaces based on parameter type
2. ASIN and campaign dropdowns populate with data filtered by the selected instance brand
3. Date selector provides both preset options and custom date range selection with proper formatting

## Spec Documentation

- Tasks: @.agent-os/specs/2025-08-28-universal-parameter-selection/tasks.md
- Technical Specification: @.agent-os/specs/2025-08-28-universal-parameter-selection/sub-specs/technical-spec.md