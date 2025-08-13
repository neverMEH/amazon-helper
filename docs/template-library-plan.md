# AMC Instructional Query Template Library - Implementation Plan

## Overview
Create a comprehensive template library system for AMC instructional queries that includes the Sponsored Products and DSP Display overlap query, with support for complex parameters, documentation, and seamless integration with the existing query builder.

## Phase 1: Database Schema Enhancements

### 1.1 Extend query_templates table
- Add `template_type` field (enum: 'custom', 'instructional', 'amazon_official')
- Add `documentation` field (JSONB) for storing comprehensive docs
- Add `requirements` field (JSONB) for prerequisites and timing requirements
- Add `parameter_groups` field (JSONB) for organizing complex parameters
- Add `result_interpretation` field (JSONB) for analysis guides
- Add `version` field for template versioning
- Add `source_url` field for reference links

### 1.2 Create instructional_templates_metadata table
- Store extended metadata for instructional queries
- Include fields for time_requirements, data_requirements, expected_results
- Link to parent query_templates table

## Phase 2: Backend Service Enhancements

### 2.1 Enhance QueryTemplateService
- Add methods for handling instructional templates
- Support complex parameter types (arrays of values)
- Add validation for time requirements
- Add template versioning support

### 2.2 Create InstructionalTemplateParser
- Parse complex SQL with multiple CTEs
- Extract and categorize parameters (campaign IDs, names, dates)
- Validate query structure
- Generate parameter schemas automatically

### 2.3 Add Template Import/Export API
- Endpoint to import templates from JSON/YAML
- Bulk import for template library
- Export templates with full documentation

## Phase 3: Frontend Template Library UI

### 3.1 Create Template Library Page (`/template-library`)
- Categorized view (Instructional, Custom, Official)
- Search and filter capabilities
- Preview with documentation
- One-click import to query builder

### 3.2 Enhance Template Details View
- Show full documentation
- Display requirements and prerequisites
- Parameter configuration wizard
- Result interpretation guide
- Time requirement warnings

### 3.3 Create Parameter Configuration Wizard
- Step-by-step parameter input
- Support for array parameters (multiple campaign IDs)
- Validation based on requirements
- Default value suggestions

## Phase 4: Integrate SP/DSP Overlap Template

### 4.1 Process the provided template
- Parse the SQL and extract parameters:
  - Display campaign IDs (array)
  - SP campaign names (array)
- Create parameter schema with proper types
- Store documentation sections

### 4.2 Create parameter configuration UI
- Campaign ID selector with search
- Campaign name input with autocomplete
- Date range validation (14-day wait requirement)
- Preview of substituted values

### 4.3 Add result interpretation component
- Display exposure groups explanation
- Calculate metrics automatically
- Generate insights based on results
- Export formatted reports

## Phase 5: Query Execution Enhancements

### 5.1 Add pre-execution validation
- Check time requirements (14-day wait)
- Validate required data availability
- Warn about query performance considerations

### 5.2 Enhance execution results view
- Template-specific result formatting
- Automatic metric calculations
- Visualization for overlap analysis
- Export with interpretation guide

## Phase 6: Template Management Features

### 6.1 Template versioning
- Track template changes
- Allow rollback to previous versions
- Show change history

### 6.2 Template sharing
- Share templates within organization
- Public template gallery
- Template ratings and reviews

### 6.3 Template documentation
- Rich text editor for documentation
- Code syntax highlighting
- Embedded examples
- Video tutorials support

## Implementation Timeline

### Day 1: Database Migration
- Create migration script for schema changes
- Add seed data for the SP/DSP overlap template

### Days 2-3: Backend Implementation
- Extend QueryTemplateService
- Create template parser
- Add import/export endpoints
- Implement validation logic

### Days 4-5: Frontend Template Library
- Create library page component
- Build parameter wizard
- Add documentation viewer
- Integrate with query builder

### Day 6: Template Integration
- Import SP/DSP overlap template
- Test parameter substitution
- Validate execution flow
- Add result interpretation

### Day 7: Testing & Documentation
- End-to-end testing
- Create user documentation
- Add more template examples
- Performance optimization

## Key Features to Implement

### Smart Parameter Detection
- Automatically detect parameter patterns in SQL
- Suggest parameter types based on names
- Generate UI components based on types

### Template Validation
- SQL syntax validation
- AMC-specific query validation
- Parameter completeness check
- Performance estimation

### Documentation System
- Markdown support for rich documentation
- Section templates (Purpose, Requirements, Usage)
- Interactive examples
- Result interpretation guides

### Parameter Types Support
- Single values (string, number, date)
- Arrays (campaign IDs, names)
- Date ranges with validation
- Dynamic lookups from database

## File Structure

```
frontend/src/
├── pages/
│   └── TemplateLibrary.tsx
├── components/
│   └── template-library/
│       ├── TemplateLibraryGrid.tsx
│       ├── TemplateDetailView.tsx
│       ├── ParameterWizard.tsx
│       ├── DocumentationViewer.tsx
│       └── ResultInterpreter.tsx
└── services/
    └── instructionalTemplateService.ts

backend/
├── amc_manager/
│   ├── services/
│   │   ├── instructional_template_service.py
│   │   └── template_parser.py
│   └── api/
│       └── supabase/
│           └── instructional_templates.py
└── database/
    └── migrations/
        └── add_instructional_templates.sql
```

## SP/DSP Overlap Template Details

### Template Parameters
1. **Display Campaign IDs**: Array of campaign IDs (e.g., 11111111111, 2222222222)
2. **SP Campaign Names**: Array of campaign names (e.g., 'SP_campaign_name1', 'SP_campaign_name2')

### Requirements
- Both Sponsored Products and Display data in same AMC instance
- Both ad types advertising same products during same time period
- Minimum one week of overlapping campaign runtime
- Must wait 14 full days after query end date before execution

### Expected Results
- **exposure_group**: User exposure categories (both, SP only, Display only, none)
- **unique_reach**: Number of distinct users reached
- **users_that_purchased**: Number of unique users who purchased
- **purchases**: Total number of purchase events

### Result Interpretation
1. **Reach Distribution**: Calculate percentage of users exposed to each ad type
2. **Purchase Rate**: Calculate conversion rate for each exposure group
3. **Lift Analysis**: Compare performance of combined exposure vs. single channel

## Technical Considerations

### Performance
- Query time depends on number of advertisers and data volume
- Start with small time windows (1 day) for testing
- Scale up gradually to week/month periods
- Consider implementing query result caching

### AMC Limitations
- Lack of Customer Facing IDs (CFIDs) for Sponsored Products
- Must use campaign names instead of IDs for SP filtering
- User ID matching issues between conversion and impression data

### Data Privacy
- Ensure compliance with AMC data privacy requirements
- Aggregate results only, no individual user data
- Minimum threshold requirements for reporting

## Success Metrics

### Implementation Success
- Successful import and execution of SP/DSP overlap template
- Parameter substitution working correctly
- Results matching expected format
- Documentation accessible and clear

### User Adoption
- Number of templates created/imported
- Template usage frequency
- User feedback on parameter wizard
- Time saved vs. manual query creation

### Performance Metrics
- Query execution time
- Template load time
- Parameter validation speed
- Result interpretation accuracy

## Next Steps

1. Review and approve implementation plan
2. Set up development environment
3. Create database migration scripts
4. Begin backend service implementation
5. Develop frontend components
6. Import and test SP/DSP overlap template
7. Conduct user acceptance testing
8. Deploy to production
9. Monitor and iterate based on feedback