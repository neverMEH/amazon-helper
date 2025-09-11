# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-11-query-library-redesign/spec.md

> Created: 2025-09-11
> Version: 1.0.0

## Technical Requirements

### Database Schema Enhancements
- Enhance `query_templates` table with `report_config` (JSONB), `version` (integer), `parent_template_id` (UUID), and `execution_count` (integer) fields
- Create `query_template_parameters` table for structured parameter definitions with validation rules and UI configurations
- Create `query_template_reports` table for dashboard configurations and field mappings
- Create `query_template_instances` table for saved parameter sets and user favorites
- Implement proper foreign key constraints and cascading deletes
- Add indexes on frequently queried fields (template_id, user_id, created_at)

### Backend Services Architecture
- Enhance `QueryTemplateService` with versioning, forking, and sharing capabilities
- Create `TemplateParameterService` for parameter detection, type inference, and validation
- Create `TemplateReportService` for dashboard generation and result-to-widget mapping
- Enhance `ParameterEngine` to support new parameter types: asin_list, campaign_filter, date_expression, threshold_numeric
- Implement parameter validation with SQL injection prevention at multiple layers
- Add caching layer for frequently used templates

### Frontend Components
- Create Query Library page (`/query-library`) with template gallery, search, and filtering
- Implement Template Editor with Monaco SQL editor and live parameter detection
- Build specialized parameter input components:
  - AsinMultiSelect with bulk paste support (60+ items)
  - CampaignSelector with wildcard patterns
  - DateRangePicker with presets and dynamic expressions
  - ThresholdInput with min/max validation
- Create Report Builder interface with drag-drop layout and field mapping
- Implement real-time parameter validation and error feedback

### Integration Requirements
- Modify workflow creation to support "Create from Template" option
- Update collection creation to reference templates with batch parameters
- Enhance schedule system to support dynamic parameter expressions
- Ensure backward compatibility with existing query_templates
- Implement migration layer for legacy templates

### Performance Criteria
- Template loading time < 500ms
- Parameter validation < 100ms per field
- Support 100+ parameters per template
- Handle bulk ASIN lists of 1000+ items
- Dashboard generation < 3 seconds
- Concurrent template executions: 10+ per user

## Approach

### Phase 1: Database Schema and Backend Services
1. Apply database migrations for new tables and schema enhancements
2. Implement enhanced QueryTemplateService with versioning and forking
3. Create TemplateParameterService for parameter management
4. Add comprehensive test coverage for all backend services

### Phase 2: Template Management Interface
1. Build Query Library page with template gallery and search
2. Implement Template Editor with Monaco integration
3. Create parameter detection and validation system
4. Add template sharing and permission management

### Phase 3: Advanced Parameter Components
1. Build AsinMultiSelect with bulk paste functionality
2. Implement CampaignSelector with advanced filtering
3. Create DateRangePicker with dynamic expressions
4. Add ThresholdInput with validation rules

### Phase 4: Report Generation and Integration
1. Implement TemplateReportService for dashboard generation
2. Create Report Builder interface with field mapping
3. Integrate with existing workflows, collections, and schedules
4. Add export capabilities and sharing features

## External Dependencies

- **react-dnd** (^16.0.0) - Drag-and-drop functionality for dashboard builder
- **Justification:** Required for intuitive dashboard layout creation with widget positioning
- **papaparse** (^5.4.0) - CSV parsing for bulk parameter import
- **Justification:** Enables users to import large ASIN/campaign lists from spreadsheets
- **react-select** (^5.8.0) - Advanced multi-select components
- **Justification:** Provides searchable, performant multi-select for large parameter lists