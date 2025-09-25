# Spec Requirements Document

> Spec: Query Library Template Fixes
> Created: 2025-09-25
> Status: Planning

## Overview

Fix critical integration issues in the Query Library Template system, particularly the broken CampaignSelector integration and enhance the template management experience. This will restore full functionality to parameter handling and improve template usability across the application.

## User Stories

### Template Creator - Campaign Parameter Story

As a template creator, I want to use the CampaignSelector component when defining campaign_list parameters, so that I can properly configure and test templates with real campaign data.

Currently, the TemplateEditor uses a basic textarea for campaign parameters instead of the sophisticated CampaignSelector component that exists in the codebase. This makes it impossible to properly test templates with campaign data, as users must manually enter campaign IDs without seeing campaign names or metadata. The workflow should allow selecting campaigns from a searchable dropdown with brand filtering, seeing campaign types (SP, SB, SD, DSP), and choosing between campaign names or IDs for the query.

### Template User - Persistent Name Visibility Story

As a template user, I want to see the template name at all times while editing, so that I don't lose context when switching between tabs.

Users currently lose sight of the template name when switching from the Editor tab to Preview or Settings tabs. This causes confusion especially when working with multiple templates. The template name should remain visible in a persistent header area across all tabs, be editable from any tab, and save automatically when changed.

### Report Builder User - Template Integration Story

As a Report Builder user, I want to access and use Query Library templates directly from the Report Builder, so that I can leverage pre-built queries in my reports.

The Report Builder currently has its own separate template system (TemplateGrid) that doesn't connect to the Query Library. Users need to access the full Query Library from Report Builder, apply templates with parameter configuration, and save successful Report Builder queries as new templates for future use.

## Spec Scope

1. **CampaignSelector Integration** - Replace textarea with proper CampaignSelector component for campaign_list parameters in TemplateEditor
2. **Template Name Persistence** - Move template name field to persistent header visible across all tabs
3. **Parameter State Fix** - Ensure all parameter properties (description, required, preview values) persist correctly when saving
4. **Report Builder Integration** - Connect Query Library templates to Report Builder's template selection
5. **Enhanced Parameter UI** - Improve parameter input components for better user experience with proper validation

## Out of Scope

- Creating new parameter types beyond what sqlParameterAnalyzer already detects
- Changing the underlying database schema
- Modifying the core parameter detection algorithm
- Template versioning system (already exists but not exposed in UI)
- Cross-account template sharing
- Template approval workflows
- Performance analytics for templates

## Expected Deliverable

1. Working CampaignSelector integration where campaign_list parameters show the full multi-select dropdown with search, brand filtering, and campaign type indicators
2. Template name field that remains visible and editable in a persistent header across Editor, Preview, and Settings tabs
3. Report Builder template panel that displays Query Library templates and allows applying them with parameter configuration

## Spec Documentation

- Tasks: @.agent-os/specs/2025-09-25-query-template-fixes/tasks.md
- Technical Specification: @.agent-os/specs/2025-09-25-query-template-fixes/sub-specs/technical-spec.md