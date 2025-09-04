# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-03-visual-query-flow-builder/spec.md

## Technical Requirements

### Frontend Architecture (Maximum Component Reuse)

- **Canvas Implementation**: Use React Flow v11+ integrated with existing RecomAMP components
  - **Template Node Component**: Direct reuse of existing `TemplateCard.tsx` as draggable nodes
  - **Parameter Configuration**: Exact reuse of `TemplateParameterForm.tsx` in node modals
  - **Template Gallery**: Reuse existing `QueryFlowTemplates.tsx` gallery as side panel
  - **Execution Monitoring**: Integrate existing `ExecutionModal.tsx` and `AMCExecutionDetail.tsx`
  - **Scheduling**: Direct integration with existing `ScheduleWizard.tsx`

- **Visual Flow Builder Page**:
  ```tsx
  // New page structure reusing existing components
  const VisualFlowBuilder = () => {
    return (
      <div className="flex h-screen">
        <TemplateGallerySidebar /> {/* Reuse existing gallery */}
        <ReactFlowCanvas />
        <FlowPropertiesPanel />
      </div>
    );
  };
  ```

- **Node Integration Strategy**:
  - **Wrapper Component**: `FlowTemplateNode` wraps existing `TemplateCard`
  - **Status Indicators**: Reuse existing status badge patterns from template cards
  - **Configuration Modal**: Exact same `TemplateDetailModal` with minor flow-specific modifications
  - **Parameter Handling**: Leverage existing parameter form components without changes

- **Data Mapping Interface**:
  - **Field Selector**: Reuse existing dropdown components from parameter forms
  - **Mapping Modal**: Extend existing modal patterns used throughout application  
  - **Schema Display**: Leverage existing schema explorer components from query builder
  - **Validation**: Extend existing parameter validation system

- **Flow Execution Integration**:
  - **Progress Tracking**: Reuse existing execution monitoring components
  - **Result Viewing**: Direct integration with existing result visualization
  - **Error Handling**: Use existing error display patterns and components
  - **Real-time Updates**: Leverage existing TanStack Query patterns for live updates

### Backend Architecture (Extend Existing Services)

- **Flow Composition Service** (`flow_composition_service.py`):
  ```python
  class FlowCompositionService(DatabaseService):
      """Extends existing DatabaseService patterns"""
      
      @with_connection_retry
      async def create_composition(self, composition_data):
          # Reuse existing database patterns
          pass
      
      @with_connection_retry  
      async def execute_composition(self, composition_id, parameters):
          # Orchestrate multiple template executions
          # Reuse existing template_execution_service
          pass
  ```

- **Template Execution Orchestration**:
  - **Extend Existing Service**: Modify `template_execution_service.py` to handle composition context
  - **Parameter Mapping**: Extend existing `parameter_engine.py` with node-to-node mapping
  - **Execution Coordination**: Use existing workflow execution patterns in sequence
  - **Result Aggregation**: Leverage existing result storage and retrieval patterns

- **Integration with Existing Services**:
  ```python
  # Flow execution leverages existing infrastructure
  async def execute_composition_node(node_config):
      # Use existing template execution service
      result = await template_execution_service.execute_template(
          template_id=node_config.template_id,
          parameters=mapped_parameters,  # Mapped from previous nodes
          instance_id=node_config.instance_id
      )
      # Result flows through existing workflow_executions table
      return result
  ```

- **Background Service Integration**:
  - **Execution Polling**: Existing `execution_status_poller.py` handles flow node polling
  - **Schedule Integration**: Existing `schedule_executor_service.py` extended for compositions
  - **Token Management**: Existing `TokenService` handles all AMC authentication
  - **No New Background Services**: All background processing reuses existing infrastructure

### Database Integration (Minimal New Schema)

- **Primary Integration Pattern**:
  ```python
  # Flow executions create multiple standard workflow executions
  composition_execution = {
      "composition_id": "comp_campaign_analysis",
      "nodes": [
          {"node_id": "node_1", "workflow_execution_id": "exec_123"},
          {"node_id": "node_2", "workflow_execution_id": "exec_124"}
      ]
  }
  
  # Each node execution is a standard workflow execution
  # Existing execution monitoring, results, and status patterns apply
  ```

- **Parameter Mapping Integration**:
  - **Extend Parameter Engine**: Add "mapped_from_node" parameter type
  - **Reuse Validation**: Existing parameter validation patterns apply
  - **SQL Injection Support**: Existing large parameter list handling works for mapped data
  - **No New Parameter System**: Build on proven parameter infrastructure

### API Architecture (Extend Existing Endpoints)

- **Extend Template Endpoints**:
  ```python
  # Add composition endpoints to existing template router
  @router.post("/api/query-flow-templates/compositions/")
  async def create_composition(composition_data: CompositionCreate):
      # Reuse existing patterns from template creation
      pass

  @router.post("/api/query-flow-templates/compositions/{comp_id}/execute")
  async def execute_composition(comp_id: str, execution_data: CompositionExecution):
      # Leverage existing template execution patterns
      pass
  ```

- **Reuse Existing API Patterns**:
  - **Authentication**: Existing JWT and OAuth patterns
  - **Validation**: Existing Pydantic model patterns  
  - **Error Handling**: Existing error response patterns
  - **Documentation**: Existing OpenAPI documentation patterns

### Component Reuse Strategy

#### Direct Reuse (No Modifications)
- `TemplateParameterForm.tsx` - Exact reuse for node configuration
- `ScheduleWizard.tsx` - Direct integration for flow scheduling  
- `ExecutionModal.tsx` - Results viewing for flow executions
- `TemplateCard.tsx` - Base component for flow nodes
- `SQLPreview.tsx` - SQL preview for individual nodes

#### Minor Extensions (Minimal Changes)
- `QueryFlowTemplates.tsx` - Add composition list view
- `TemplateDetailModal.tsx` - Add "Add to Flow" button
- `AMCExecutionDetail.tsx` - Show flow context when part of composition

#### New Components (Built on Existing Patterns)
- `FlowCanvas.tsx` - React Flow integration wrapper
- `FlowTemplateNode.tsx` - Wrapper around existing TemplateCard
- `NodeConnectionModal.tsx` - Data mapping interface using existing modal patterns

### Performance Optimizations (Leverage Existing Infrastructure)

- **Caching Strategy**:
  - **Template Metadata**: Use existing TanStack Query caching for templates
  - **Execution Results**: Leverage existing result caching in workflow_executions
  - **Parameter Schemas**: Reuse existing parameter schema caching
  - **Canvas State**: Client-side caching for flow compositions

- **Real-time Updates**:
  - **Execution Status**: Existing 5-second polling for node executions
  - **Flow Progress**: Aggregate existing execution statuses
  - **Background Processing**: Existing asyncio patterns for concurrent execution

### Security Integration

- **Authentication**: Reuse existing JWT + OAuth patterns
- **Authorization**: Extend existing RLS policies for flow compositions  
- **Parameter Security**: Existing Fernet encryption for sensitive parameters
- **API Security**: Existing rate limiting and validation patterns

### Testing Strategy (Extend Existing Test Patterns)

- **Frontend Tests**: Extend existing component test patterns
- **Backend Tests**: Add flow composition tests to existing service test suites
- **Integration Tests**: Add flow execution tests to existing execution test patterns
- **E2E Tests**: Extend existing Playwright tests with flow builder scenarios

### Development Workflow Integration

- **Hot Reload**: Existing Vite HMR patterns work with new components
- **TypeScript**: Existing strict TypeScript patterns apply to flow components  
- **API Documentation**: New endpoints auto-documented with existing OpenAPI patterns
- **Database Migrations**: Follow existing migration patterns for new tables

### Performance Optimizations

- **Canvas Rendering**:
  - Virtualization for large flows (100+ nodes)
  - Lazy loading of node details
  - Debounced auto-save during editing
  - Optimistic UI updates for better responsiveness

- **Execution Optimization**:
  - Result caching between executions
  - Parallel execution of independent branches
  - Incremental result streaming
  - Query result pagination for large datasets

- **Data Transfer**:
  - Compressed result storage in S3
  - Streaming result transfer between nodes
  - Temporary result tables in AMC for large datasets
  - Cleanup of intermediate results after flow completion

### Security Considerations

- **Access Control**:
  - Flow-level permissions (view, edit, execute)
  - Template access restrictions maintained
  - Parameter value encryption for sensitive data
  - Audit logging for flow modifications

- **Data Protection**:
  - Result isolation between users
  - Secure parameter passing between nodes
  - Connection string encryption
  - PII data masking in previews

### Integration Points

- **With Existing Systems**:
  - Workflow Service: Create master workflow for flow execution
  - Execution Service: Track individual node executions
  - Schedule Service: Register flows as schedulable entities
  - Template Service: Fetch template metadata and parameters
  - Result Storage: Leverage existing S3 result handling

- **UI Component Reuse**:
  - TemplateParameterForm for node configuration
  - ScheduleWizard for flow scheduling
  - ExecutionModal for result viewing
  - SQLPreview for generated query inspection

## External Dependencies

- **React Flow** (v11.11.0+) - Node-based UI library for building visual programming interfaces
  - **Justification:** Industry-standard library specifically designed for flow-based interfaces, provides drag-and-drop, connection handling, and zoom/pan controls out of the box
  
- **reactflow/background** (v11.11.0+) - Background patterns and grids for React Flow
  - **Justification:** Provides visual grid alignment aids essential for professional canvas interfaces
  
- **reactflow/controls** (v11.11.0+) - Zoom and fit controls for React Flow
  - **Justification:** Standard navigation controls users expect in canvas-based applications
  
- **reactflow/minimap** (v11.11.0+) - Minimap component for React Flow
  - **Justification:** Essential for navigating large flows with many nodes
  
- **@tanstack/react-table** (v8.11.0+) - For data mapping preview tables
  - **Justification:** Already used in project, provides powerful data grid capabilities for showing mapped results
  
- **immer** (v10.0.3+) - For immutable state updates in flow reducer
  - **Justification:** Simplifies complex state updates when modifying nested flow configurations
  
- **dagre** (v0.8.5) - For automatic flow layout algorithms
  - **Justification:** Provides automatic layout for imported flows or auto-arrangement features
  
- **file-saver** (v2.0.5) - For flow export functionality
  - **Justification:** Enables client-side flow export to JSON files for sharing and backup