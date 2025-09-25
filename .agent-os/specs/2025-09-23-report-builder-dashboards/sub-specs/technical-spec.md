# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-23-report-builder-dashboards/spec.md

> Created: 2025-09-23
> Version: 1.0.0

## Technical Requirements

### Frontend Components

- **Query Library Enhancement**: Modify existing QueryLibrary.tsx to add report enable/disable toggle with state persistence
- **Reports Library Page**: New route /reports with grid view showing report-enabled queries, execution status, and dashboard access buttons
- **Dashboard Container**: Main dashboard component handling layout, data fetching, and chart orchestration
- **Chart Components**: Individual Shadcn-based chart components (FunnelChart, MetricsCards, BarChart, LineChart, PieChart, DataTable)
- **AI Insights Panel**: Collapsible panel showing opus 4.1 generated insights with markdown rendering support
- **Export Service**: Client-side PDF generation using jsPDF/html2canvas for dashboard exports

### Backend Services

- **Report Configuration Service**: Manages report enablement state per query, dashboard templates, and visualization configurations
- **Data Aggregation Pipeline**: Processes raw AMC execution results into dashboard-ready format with calculated metrics
- **Insights Generation Service**: Interfaces with OpenAI API to generate contextual insights from aggregated data
- **Export API**: Handles server-side rendering for PDF generation with proper chart serialization

### Data Processing

- **Metric Calculations**: Server-side computation of derived metrics (ROAS, conversion rates, funnel drop-offs)
- **Time Series Handling**: Aggregation logic for multiple execution windows with period-over-period calculations
- **Data Caching**: Redis-based caching layer for processed dashboard data to reduce computation overhead
- **Background Processing**: Async job queue for heavy data processing tasks using existing BullMQ infrastructure

### UI/UX Specifications

- **Dashboard Layout**: Responsive grid system with 12-column layout, collapsible sections, and drag-to-reorder widgets (future)
- **Chart Interactions**: Hover tooltips, click-to-filter, zoom/pan capabilities on time series charts
- **Loading States**: Skeleton loaders for individual chart sections, progressive data loading
- **Error Handling**: Graceful degradation when data unavailable, clear error messages for failed insights generation
- **Theme Integration**: Full Shadcn/ui component library with consistent styling, dark mode support

### Performance Criteria

- **Dashboard Load Time**: Initial render < 2 seconds, complete data load < 5 seconds for 52-week datasets
- **Export Generation**: PDF export completion < 10 seconds for full dashboard
- **Insight Generation**: AI insights return < 5 seconds per dashboard view
- **Data Processing**: Background aggregation < 30 seconds for 1 million row result sets

## Approach

The implementation follows a phased approach building on the existing dashboard infrastructure:

1. **Phase 1: Query Report Enhancement** - Add toggle functionality to existing query library for report enablement
2. **Phase 2: Reports Library Interface** - Create dedicated reports page with dashboard access
3. **Phase 3: Chart Component System** - Implement modular chart components using Shadcn/Recharts
4. **Phase 4: AI Insights Integration** - Add OpenAI-powered insights generation
5. **Phase 5: Export & Performance** - PDF export functionality and performance optimizations

The architecture leverages existing AMC execution infrastructure while adding report-specific processing layers.

## External Dependencies

- **@shadcn/ui**: Complete component library for consistent UI elements and theming
- **Justification:** Provides production-ready components with built-in accessibility and consistent design system

- **recharts**: React charting library for all visualizations
- **Justification:** Lightweight, composable, and integrates well with React ecosystem. Already partially implemented in sample

- **jspdf & html2canvas**: PDF generation libraries for dashboard exports
- **Justification:** Industry standard for client-side PDF generation with chart rendering support

- **react-markdown & remark-gfm**: Markdown rendering for AI insights display
- **Justification:** Needed to properly format and display opus 4.1 generated insights with tables and formatting

- **date-fns**: Date manipulation and formatting utilities
- **Justification:** More lightweight than moment.js, better tree-shaking, needed for period comparisons

- **papaparse**: CSV parsing for data import/export
- **Justification:** Handles large datasets efficiently, already used in sample dashboard code