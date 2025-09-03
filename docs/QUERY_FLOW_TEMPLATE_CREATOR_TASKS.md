# Query Flow Template Creator Frontend - Task List

## Overview
Build a comprehensive frontend interface for creating, editing, and managing Query Flow Templates. This feature will enable users to design SQL templates with dynamic parameters and visualization configurations without directly accessing the database.

## Task List

### Phase 1: Core Infrastructure

#### Task 1: Design the Query Flow Template creator/editor UI layout
- [ ] Create mockup/wireframe for the template builder interface
- [ ] Design multi-step wizard vs single-page editor approach
- [ ] Plan component hierarchy and state management
- [ ] Define responsive layout for mobile/tablet views
- [ ] Create design system for consistent UI elements

#### Task 2: Create route and page component for template creation
- [ ] Add `/query-flow-templates/new` route
- [ ] Add `/query-flow-templates/edit/:id` route
- [ ] Create main TemplateEditor page component
- [ ] Set up navigation from templates list
- [ ] Implement breadcrumb navigation

### Phase 2: Template Definition

#### Task 3: Build template metadata form (name, category, description, tags)
- [ ] Create TemplateMetadataForm component
- [ ] Add form fields: template_id, name, category dropdown, description textarea
- [ ] Implement tags input with autocomplete
- [ ] Add validation rules for required fields
- [ ] Include helper text and examples

#### Task 4: Implement SQL template editor with syntax highlighting and parameter detection
- [ ] Integrate Monaco Editor for SQL editing
- [ ] Add parameter syntax highlighting (`:parameter_name` format)
- [ ] Implement auto-detection of parameters from SQL
- [ ] Add Jinja2 template support (`{% if %}` blocks)
- [ ] Include SQL validation and error display
- [ ] Add SQL formatting and auto-completion

### Phase 3: Parameter Management

#### Task 5: Create parameter configuration UI with dynamic form generation
- [ ] Build ParameterConfigurator component
- [ ] Auto-generate parameter forms from detected SQL parameters
- [ ] Support parameter types: date, date_range, string, number, boolean, campaign_list, asin_list
- [ ] Add validation rules configuration per parameter
- [ ] Implement parameter ordering and dependencies
- [ ] Create parameter preview panel

### Phase 4: Visualization Setup

#### Task 6: Build chart configuration interface for visualization setup
- [ ] Create ChartConfigurator component
- [ ] Add chart type selector (table, bar, line, pie, scatter, etc.)
- [ ] Build data mapping interface (x_field, y_field, aggregations)
- [ ] Configure chart-specific options (colors, axes, labels)
- [ ] Support multiple charts per template
- [ ] Implement chart preview with sample data

### Phase 5: Testing & Validation

#### Task 7: Implement template validation and preview functionality
- [ ] Add SQL syntax validation
- [ ] Create test parameter input interface
- [ ] Build SQL preview with parameter substitution
- [ ] Implement dry-run execution for testing
- [ ] Show estimated query cost
- [ ] Display validation errors and warnings

### Phase 6: Persistence & API

#### Task 8: Add save/update template API integration
- [ ] Create API endpoints for template CRUD operations
- [ ] Implement save draft functionality
- [ ] Add publish/unpublish controls
- [ ] Handle validation errors from backend
- [ ] Show success/error notifications
- [ ] Implement optimistic updates

### Phase 7: Advanced Features

#### Task 9: Create template versioning and draft management
- [ ] Track template versions
- [ ] Allow reverting to previous versions
- [ ] Implement draft auto-save
- [ ] Add version comparison view
- [ ] Show version history timeline

#### Task 10: Add edit functionality to existing templates list
- [ ] Add Edit button to template cards/rows
- [ ] Load existing template data into editor
- [ ] Handle update vs create logic
- [ ] Preserve template history
- [ ] Implement change detection

#### Task 11: Implement template duplication/copy feature
- [ ] Add "Duplicate" action to templates
- [ ] Auto-generate new template_id
- [ ] Allow editing before saving copy
- [ ] Maintain parameter and chart configs
- [ ] Update references and dependencies

### Phase 8: Security & Permissions

#### Task 12: Add permission controls for template management
- [ ] Implement user role checks (admin, creator, viewer)
- [ ] Add template ownership tracking
- [ ] Control public/private visibility
- [ ] Restrict edit/delete based on permissions
- [ ] Add sharing and collaboration features

## Implementation Details

### Component Architecture

```
TemplateEditor/
├── TemplateEditor.tsx (main container)
├── components/
│   ├── TemplateMetadataForm.tsx
│   ├── SQLTemplateEditor.tsx
│   ├── ParameterConfigurator.tsx
│   ├── ChartConfigurator.tsx
│   ├── TemplatePreview.tsx
│   └── TemplateActions.tsx
├── hooks/
│   ├── useTemplateValidation.ts
│   ├── useParameterDetection.ts
│   └── useTemplateAutoSave.ts
└── services/
    └── templateEditorService.ts
```

### State Management Structure

```typescript
interface TemplateEditorState {
  metadata: {
    template_id: string;
    name: string;
    description: string;
    category: string;
    tags: string[];
  };
  sql_template: string;
  parameters: TemplateParameter[];
  charts: TemplateChartConfig[];
  validation: {
    errors: ValidationError[];
    warnings: ValidationWarning[];
  };
  isDirty: boolean;
  isSaving: boolean;
  lastSaved: Date | null;
}
```

### UI/UX Considerations

1. **Progressive Disclosure**: Start with essential fields, reveal advanced options as needed
2. **Real-time Validation**: Provide immediate feedback on SQL syntax and parameter configuration
3. **Auto-save**: Prevent data loss with periodic draft saves
4. **Guided Experience**: Include tooltips, examples, and documentation links
5. **Mobile Responsive**: Ensure usability on tablets for on-the-go template creation

### Technical Requirements

- React 19.1.0 with TypeScript
- Monaco Editor for SQL editing
- React Hook Form for form management
- TanStack Query for API state
- Tailwind CSS for styling
- Chart.js for visualization previews

### API Endpoints Needed

```
POST   /api/query-flow-templates/
GET    /api/query-flow-templates/:id
PUT    /api/query-flow-templates/:id
DELETE /api/query-flow-templates/:id
POST   /api/query-flow-templates/:id/validate
POST   /api/query-flow-templates/:id/preview
POST   /api/query-flow-templates/:id/duplicate
GET    /api/query-flow-templates/:id/versions
POST   /api/query-flow-templates/:id/publish
```

### Success Metrics

- Time to create first template < 5 minutes
- Template validation accuracy > 95%
- User satisfaction score > 4.5/5
- Template reuse rate > 60%
- Error rate in published templates < 1%

## Next Steps

1. Begin with Task 1: Design the UI layout
2. Get stakeholder feedback on design
3. Proceed with implementation following the task order
4. Conduct user testing after Phase 2
5. Iterate based on feedback