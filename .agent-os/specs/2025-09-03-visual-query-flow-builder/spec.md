# Spec Requirements Document

> Spec: Visual Query Flow Builder
> Created: 2025-09-03

## Overview

Transform the existing Query Flow Templates gallery into a visual drag-and-drop pipeline builder where users can chain multiple templates together to create complex data workflows. This feature will enable visual composition of AMC queries through connected template nodes, allowing data to flow from one query's output to another's input, while leveraging the existing robust Workflow, Execution, and Schedule systems.

## User Stories

### Marketing Analyst - Visual Query Pipeline Creation

As a marketing analyst, I want to visually build query pipelines by dragging and connecting templates, so that I can create complex multi-step analyses without writing SQL.

The user opens the Visual Query Flow Builder and sees a canvas with a side panel containing the template gallery. They search for "Campaign Performance" template and drag it onto the canvas, creating a node. Double-clicking the node opens the familiar parameter configuration modal where they set date ranges and campaign filters. They then drag an "Attribution Analysis" template, creating a second node. By drawing a connection from the Campaign Performance output port to the Attribution Analysis input port, they map the campaign_ids from the first query to feed into the second. The visual pipeline shows green status indicators when configured correctly. Upon execution, both queries run in sequence with results from the first automatically feeding into the second.

### Data Engineer - Reusable Flow Templates

As a data engineer, I want to save and share visual query flows as reusable templates, so that my team can execute standardized analysis workflows consistently.

The engineer builds a complex 5-node query flow that performs customer journey analysis across multiple touchpoints. Each node represents a different Query Flow Template with specific parameter configurations and data mappings between them. Once tested and validated, they save the entire flow with a descriptive name and tags. Team members can then load this saved flow, adjust only the date parameters, and execute the entire analysis pipeline with confidence that the logic and connections remain consistent.

### Business User - Scheduled Pipeline Execution

As a business user, I want to schedule my visual query flows to run automatically, so that I receive regular reports combining data from multiple analysis steps.

After building a query flow that analyzes campaign performance, attribution, and ROI across three connected templates, the user clicks "Schedule Flow" which opens the familiar scheduling wizard. They set the flow to run weekly on Mondays at 9 AM. The scheduler handles dynamic date parameters across all templates in the flow. Each week, the entire pipeline executes automatically, with intermediate results cached and final combined results delivered via the existing notification system.

## Spec Scope

1. **Visual Canvas Interface** - Replace current template gallery page with a React Flow-based canvas supporting drag-and-drop template nodes and connection drawing
2. **Template Node System** - Transform templates into visual nodes with configuration modals, status indicators, and execution state visualization
3. **Data Flow Mapping** - Implement visual mapping interface to connect output columns to input parameters between templates with transformation support
4. **Flow Execution Engine** - Create orchestrator service to manage chained template execution with dependency resolution and result caching
5. **Flow Persistence** - Design database schema and storage system for saving, loading, and versioning visual query flows

## Out of Scope

- Modifying the existing single template execution system
- Creating new Query Flow Templates (only chaining existing ones)
- Real-time collaborative editing of flows
- External data source integration beyond AMC
- Custom code nodes or script execution
- Branching logic or conditional execution paths

## Expected Deliverable

1. A functional visual query builder interface where users can drag templates from a gallery, connect them on a canvas, configure parameters, and execute the entire flow with results displayed for each node
2. Ability to save and load visual query flows with all node positions, configurations, and connections preserved
3. Integration with the existing schedule system allowing entire flows to be scheduled and executed automatically with proper dependency handling