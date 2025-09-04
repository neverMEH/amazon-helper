# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-09-03-visual-query-flow-builder/spec.md

> Created: 2025-09-03
> Status: Ready for Implementation (Revised for Maximum Integration)

## Tasks

### 1. Database Schema and Service Integration
- [x] 1.1 Write tests for new composition tables integration with existing schema
- [x] 1.2 Create minimal database tables (template_flow_compositions, template_flow_nodes, template_flow_connections)
- [x] 1.3 Extend existing workflow_executions and workflow_schedules tables with composition columns
- [x] 1.4 Create FlowCompositionService extending existing DatabaseService patterns with @with_connection_retry
- [x] 1.5 Extend existing /api/query-flow-templates/ endpoints with composition management
- [x] 1.6 Integrate composition execution with existing template_execution_service and AMC API client
- [x] 1.7 Extend existing parameter_engine.py to handle node-to-node parameter mapping
- [x] 1.8 Verify all backend tests pass and existing template functionality remains unchanged

### 2. Visual Canvas with Component Reuse
- [ ] 2.1 Write tests for React Flow canvas integration with existing TemplateCard components
- [ ] 2.2 Install React Flow dependencies (v11+, @reactflow/background, @reactflow/controls, @reactflow/minimap)
- [ ] 2.3 Create VisualFlowBuilder page reusing existing QueryFlowTemplates.tsx as template gallery sidebar
- [ ] 2.4 Create FlowTemplateNode component wrapping existing TemplateCard with React Flow handles
- [ ] 2.5 Implement canvas state persistence using existing TanStack Query caching patterns
- [ ] 2.6 Add template drag-and-drop from existing template gallery to React Flow canvas
- [ ] 2.7 Integrate canvas controls with existing Tailwind UI patterns and design system
- [ ] 2.8 Verify canvas works with all existing query flow templates without requiring modifications

### 3. Node Configuration Using Existing Forms
- [ ] 3.1 Write tests for node configuration using existing TemplateParameterForm integration
- [ ] 3.2 Modify existing TemplateDetailModal.tsx to support flow composition context
- [ ] 3.3 Reuse existing TemplateParameterForm.tsx for node parameter configuration without changes
- [ ] 3.4 Create parameter mapping UI using existing dropdown components and modal patterns
- [ ] 3.5 Implement node status indicators reusing existing template card badge patterns
- [ ] 3.6 Add React Flow Handle components for visual node connections
- [ ] 3.7 Create connection validation extending existing parameter validation patterns
- [ ] 3.8 Verify all existing parameter types (CampaignListParameter, ASINListParameter, etc.) work in flow context

### 4. Execution Integration with Existing Services
- [ ] 4.1 Write tests for flow execution using existing workflow_executions patterns
- [ ] 4.2 Implement dependency graph calculation and topological sorting for node execution order
- [ ] 4.3 Extend existing parameter_engine.py to handle "mapped_from_node" parameter type
- [ ] 4.4 Create composition execution that orchestrates multiple existing template executions
- [ ] 4.5 Integrate with existing execution_status_poller.py for real-time node status updates
- [ ] 4.6 Reuse existing result storage patterns (S3 paths, result caching, workflow_executions table)
- [ ] 4.7 Add flow progress aggregation by combining individual node execution statuses
- [ ] 4.8 Verify flow executions appear correctly in existing ExecutionModal and AMCExecutionDetail components

### 5. Scheduling and Production Integration
- [ ] 5.1 Write tests for composition scheduling using existing workflow_schedules patterns
- [ ] 5.2 Extend existing ScheduleWizard.tsx to support flow composition scheduling
- [ ] 5.3 Integrate composition scheduling with existing schedule_executor_service.py
- [ ] 5.4 Add composition list view to existing MyQueries.tsx page with existing filter/sort patterns
- [ ] 5.5 Create example flow compositions using existing high-value query flow templates
- [ ] 5.6 Add composition favorites using existing user_template_favorites table pattern
- [ ] 5.7 Verify all existing schedule, execution monitoring, and result viewing functionality works unchanged
- [ ] 5.8 Complete production deployment following existing Railway deployment patterns with Docker