# Spec Requirements Document

> Spec: Report Builder Query Library Integration
> Created: 2025-09-18
> Status: Planning

## Overview

Enhance the Report Builder workflow by integrating the full Query Library template system into the first step of the wizard, enabling users to browse, select, and customize query templates with context-aware parameter detection and intelligent input components. This integration transforms the Report Builder from a basic query tool into a powerful template-driven reporting system that leverages the entire Query Library ecosystem.

## User Stories

### Template-First Report Creation

As a user creating a report, I want to browse and select from the Query Library templates in the first step of the Report Builder wizard, so that I can quickly create reports based on proven query patterns without writing SQL from scratch.

The workflow starts with template selection where users can search, filter by category/tags, view template metadata (usage count, difficulty level), and preview the SQL with detected parameters. After selecting a template, the system automatically detects parameters, provides context-aware input components based on parameter types, and shows a real-time SQL preview with parameter substitution.

### Custom Query with Template Features

As a power user, I want to write custom SQL queries in the Report Builder while still benefiting from the Query Library's advanced parameter detection and input components, so that I can create custom reports with the same level of sophistication as template-based reports.

When choosing to write a custom query, users get access to the Monaco SQL editor with syntax highlighting, automatic parameter detection as they type, context-aware parameter type inference, and the same intelligent input components used for templates. The system provides real-time parameter validation and SQL preview with injected values.

### Template Customization and Forking

As a user working with templates, I want to customize template parameters and even fork templates for my specific needs, so that I can adapt existing query patterns to my unique reporting requirements.

Users can override default parameter values, add custom parameters to templates, save customized parameter sets for reuse, and fork templates to create personalized versions. The system tracks template usage and maintains template versioning history.

## Spec Scope

1. **Template Selection Interface** - Full Query Library browser integrated into the Report Builder's first step with search, filtering, category navigation, and template preview capabilities.

2. **Context-Aware Parameter System** - Integration of the SQL parameter analyzer that detects parameter context (LIKE, IN, VALUES, BETWEEN) and automatically suggests appropriate input components and formatting.

3. **Intelligent Input Components** - Dynamic parameter input forms that adapt based on SQL context, including AsinMultiSelect for bulk ASIN input, CampaignSelector with wildcard patterns, and DateRangePicker with presets and dynamic expressions.

4. **SQL Preview with Parameter Injection** - Real-time SQL preview showing how parameters will be injected into the query, with syntax highlighting and parameter value substitution.

5. **Template Metadata Integration** - Display and utilize template metadata including usage statistics, difficulty levels, categories, tags, and parameter schemas for validation.

## Out of Scope

- Creating new templates from within the Report Builder (use Query Library page instead)
- Modifying the core Query Library template structure or database schema
- Adding new parameter types beyond what Query Library currently supports
- Changing the subsequent steps of the Report Builder wizard (execution, schedule, review)
- Template sharing or collaboration features

## Expected Deliverable

1. Report Builder wizard opens with template selection as the default first step, with an option to write custom SQL
2. Users can browse, search, and filter Query Library templates directly within the Report Builder
3. Selected templates automatically populate with detected parameters and appropriate input components based on SQL context analysis

## Spec Documentation

- Tasks: @.agent-os/specs/2025-09-18-report-builder-query-integration/tasks.md
- Technical Specification: @.agent-os/specs/2025-09-18-report-builder-query-integration/sub-specs/technical-spec.md