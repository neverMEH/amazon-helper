# Spec Requirements Document

> Spec: Instance Templates
> Created: 2025-10-15
> Status: Planning

## Overview

Create an instance-scoped SQL template system that allows users to save and reuse SQL queries specific to each AMC instance. This feature will replace the "Workflows" tab on instance detail pages, providing a simpler, instance-local alternative to the global query library for storing frequently-used queries without parameter management overhead.

## User Stories

### Save Frequently-Used Queries

As an AMC analyst, I want to save SQL queries specific to each instance, so that I can quickly reuse common queries without recreating them from scratch or managing complex parameters.

**Workflow**: User navigates to an instance detail page, switches to the "Templates" tab, clicks "Create Template", enters a name, description, and SQL query, then saves. The template appears in the instance's template list and can be used to quickly create new workflows.

### Organize Instance-Specific Queries

As a data analyst managing multiple AMC instances, I want to keep my SQL templates organized by instance, so that I can easily find and use queries relevant to each client or brand without searching through a global library.

**Workflow**: User works with different AMC instances for different clients. Each instance has its own set of templates tailored to that client's specific data structure and reporting needs. The user switches between instances and immediately sees only the relevant templates for that context.

### Quick Workflow Creation from Templates

As a campaign manager, I want to create workflows from saved templates with one click, so that I can execute common analyses without manually copying SQL code or setting up parameters each time.

**Workflow**: User views the Templates tab on an instance page, sees a list of saved templates, clicks "Use Template" on a desired template, which pre-fills a new workflow with the template's SQL. The user can then optionally modify dates or other values before executing.

## Spec Scope

1. **Instance-Scoped Template Storage** - Database table and API endpoints for storing SQL templates associated with specific AMC instances
2. **Template CRUD Operations** - Create, read, update, and delete operations for instance templates with proper access control
3. **Instance Templates Tab UI** - Replace the "Workflows" tab on instance detail pages with a "Templates" tab showing instance-specific templates
4. **Template Editor Modal** - Simple modal interface for creating and editing templates with name, description, and SQL query fields
5. **Template to Workflow Conversion** - Action to create a new workflow pre-filled with a template's SQL query

## Out of Scope

- Parameter management and schema definitions (templates are just SQL storage)
- Public/private sharing or visibility controls (templates are private to the user)
- Cross-instance template sharing or global template library
- Template versioning or forking capabilities
- Template categories or advanced organization beyond simple lists
- Usage tracking and analytics for templates

## Expected Deliverable

1. User can create, edit, and delete SQL templates from the Templates tab on any instance detail page
2. Templates are scoped to specific instances and only appear on their respective instance pages
3. User can click "Use Template" to create a new workflow pre-populated with the template's SQL query

## Spec Documentation

- Tasks: @.agent-os/specs/2025-10-15-instance-templates/tasks.md
- Technical Specification: @.agent-os/specs/2025-10-15-instance-templates/sub-specs/technical-spec.md
- Database Schema: @.agent-os/specs/2025-10-15-instance-templates/sub-specs/database-schema.md
- API Specification: @.agent-os/specs/2025-10-15-instance-templates/sub-specs/api-spec.md
