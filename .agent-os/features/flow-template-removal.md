# Flow Template and Visual Builder Removal

## Overview
Significant codebase cleanup completed on 2025-09-11 to remove unused flow template and visual query builder features from the RecomAMP platform. These features were originally designed for visual workflow composition but were never adopted in production usage.

## Recent Changes (2025-09-11)

### Backend Code Removal
- **API Endpoint Removal**: Removed `/api/query-flow-templates/` endpoints and router
  - Deleted `amc_manager/api/query_flow_templates.py` (Flow template CRUD operations)
  - Removed router registration from `main_supabase.py`

- **Service Layer Cleanup**: Removed flow composition and template management services
  - Deleted `amc_manager/services/flow_composition_service.py` (Flow orchestration logic)
  - Deleted `amc_manager/services/query_flow_template_service.py` (Template management)

- **Test Suite Removal**: Cleaned up comprehensive test coverage for removed features
  - Deleted entire `tests/flow_composition/` directory
  - Removed migration and seeding scripts: `apply_flow_composition_migration.py`, `seed_query_flow_templates.py`

### Frontend Code Removal
- **Component Cleanup**: Removed visual builder and template management components
  - Deleted `frontend/src/components/flow-builder/` directory containing:
    - `FlowTemplateNode.tsx` (Visual flow node representation)
    - `NodeConfigurationModal.tsx` (Node configuration interface)
  - Deleted `frontend/src/components/query-flow-templates/` directory (template editor components)

- **Page Component Removal**: Removed multiple page-level components
  - `QueryFlowTemplates.tsx` (Template listing and management)
  - `VisualFlowBuilder.tsx` (Main visual builder interface)
  - `TestFlowBuilder.tsx`, `TestReactFlow.tsx`, `TestReactFlowSimple.tsx`, `TestReactFlowWithProvider.tsx` (Test components)

- **Service and Type Cleanup**: Removed API services and TypeScript definitions
  - Deleted `flowCompositionService.ts` (Flow execution API calls)
  - Deleted `queryFlowTemplateService.ts` (Template management API calls)
  - Deleted `flowComposition.ts` and `queryFlowTemplate.ts` (Type definitions)

- **Router Cleanup**: Updated application routing
  - Removed all flow template routes from `App.tsx`
  - Cleaned up imports and route definitions

- **Test Cleanup**: Removed frontend test files
  - Deleted `VisualFlowBuilder.test.tsx`

## Technical Impact

### Database Schema
While the database tables for flow templates remain in the schema documentation, the actual implementation and usage have been completely removed from the codebase. The following tables are referenced in documentation but no longer actively used:
- `query_flow_templates`
- `template_parameters` 
- `template_chart_configs`
- `template_executions`
- `user_template_favorites`
- `template_ratings`
- `template_flow_compositions`
- `template_flow_nodes`
- `template_flow_connections`

### API Endpoints Removed
The following REST endpoints were completely removed:
```
GET    /api/query-flow-templates/
POST   /api/query-flow-templates/
GET    /api/query-flow-templates/{id}
PUT    /api/query-flow-templates/{id}
DELETE /api/query-flow-templates/{id}
```

### Dependencies Affected
The React Flow dependencies added for the visual builder were retained but are no longer actively used:
- `@reactflow/background`
- `@reactflow/controls` 
- `@reactflow/minimap`

## Rationale for Removal

### Usage Analysis
- Flow templates and visual builders were never adopted by users in production
- Core workflow functionality (SQL-based workflows) provided sufficient capability
- Visual complexity added maintenance overhead without user value
- Development resources better focused on core features

### Codebase Benefits
- **Simplified Architecture**: Removed ~15 files and thousands of lines of unused code
- **Reduced Complexity**: Eliminated complex visual editor state management
- **Improved Maintainability**: Fewer components and services to maintain
- **Cleaner Codebase**: Focused functionality on proven user needs

## Core Functionality Maintained

### What Remains Intact
- **Query Templates**: Pre-built SQL templates remain fully functional
- **Workflows**: Standard SQL workflow creation and execution unchanged
- **Build Guides**: Step-by-step AMC guidance system continues to work
- **Data Collections**: Historical data collection features unaffected
- **Dashboards**: Visualization and dashboard system continues to function

### User Impact
- **Zero User Impact**: No production users were utilizing the removed features
- **Simplified UI**: Cleaner navigation without unused template builder options
- **Performance**: Reduced bundle size from removed React Flow dependencies
- **Focus**: Development resources concentrated on actively used features

## Documentation Updates Required

The following documentation files require updates to remove references to flow templates:

1. **CLAUDE.md**: Remove query flow template API endpoints and database table references
2. **Database Schema Documentation**: Mark flow template tables as deprecated/unused
3. **API Route Documentation**: Remove flow template endpoint documentation
4. **Service Layer Documentation**: Remove references to flow composition services

## Future Considerations

### Alternative Approaches
If visual workflow composition is needed in the future, consider:
- **Simpler Implementation**: Basic drag-and-drop query chaining
- **User-Driven Development**: Build only when user demand is proven
- **Integration Focus**: Connect with existing workflow patterns rather than separate system

### Database Cleanup
Consider dropping unused flow template tables in future database migrations once the removal is confirmed stable:
```sql
-- Future cleanup (when ready)
DROP TABLE IF EXISTS template_flow_connections CASCADE;
DROP TABLE IF EXISTS template_flow_nodes CASCADE;
DROP TABLE IF EXISTS template_flow_compositions CASCADE;
DROP TABLE IF EXISTS template_ratings CASCADE;
DROP TABLE IF EXISTS user_template_favorites CASCADE;
DROP TABLE IF EXISTS template_executions CASCADE;
DROP TABLE IF EXISTS template_chart_configs CASCADE;
DROP TABLE IF EXISTS template_parameters CASCADE;
DROP TABLE IF EXISTS query_flow_templates CASCADE;
```

## Verification

### Codebase Verification
- [x] No remaining references to `query_flow_templates` in active code
- [x] No remaining references to `flow_composition_service`
- [x] Frontend builds successfully without flow builder components
- [x] Backend starts without flow template API endpoints
- [x] All tests pass with removed test suites

### Functional Verification
- [x] Core workflow features function normally
- [x] Query templates continue to work
- [x] Dashboard and build guides unaffected
- [x] User authentication and authorization unchanged

This cleanup represents a significant simplification of the RecomAMP codebase while maintaining all production-critical functionality and user-facing features.