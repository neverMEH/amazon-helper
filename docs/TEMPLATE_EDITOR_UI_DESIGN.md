# Query Flow Template Editor - UI Design Specification

## Design Philosophy
- **Progressive Disclosure**: Start simple, reveal complexity as needed
- **Visual Feedback**: Immediate validation and parameter detection
- **Guided Experience**: Help text, examples, and smart defaults
- **Professional Tools**: Power user features without overwhelming beginners

## Layout Structure

### Option Selected: **Tabbed Single-Page Editor**
Superior to wizard for power users while maintaining clarity through logical tab organization.

```
┌─────────────────────────────────────────────────────────────┐
│ Header Bar                                                  │
│ [← Back] Query Flow Template Editor     [Save Draft] [Test] │
├─────────────────────────────────────────────────────────────┤
│ Status Bar                                                  │
│ ● Unsaved changes  Last saved: 2 mins ago  [Auto-save: ON] │
├─────────────────────────────────────────────────────────────┤
│ Tab Navigation                                              │
│ [Metadata] [SQL Template] [Parameters] [Visualizations]    │
│ [Preview & Test]                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    Tab Content Area                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Tab Designs

### 1. Metadata Tab
```
┌─────────────────────────────────────────────────────────────┐
│ Template Information                                        │
├─────────────────────────────────────────────────────────────┤
│ Template ID*     [campaign_performance_____]               │
│                  Must be unique, lowercase, underscores    │
│                                                             │
│ Name*           [Campaign Performance Analysis_______]      │
│                                                             │
│ Category*       [Performance ▼]                            │
│                                                             │
│ Description     ┌─────────────────────────────────┐       │
│                 │ Analyze campaign metrics...     │       │
│                 └─────────────────────────────────┘       │
│                                                             │
│ Tags            [performance] [campaign] [+Add]            │
│                                                             │
│ Visibility      (●) Public  ( ) Private  ( ) Team         │
│                                                             │
│ Status          [✓] Active  [ ] Featured                  │
└─────────────────────────────────────────────────────────────┘
```

### 2. SQL Template Tab
```
┌─────────────────────────────────────────────────────────────┐
│ Toolbar: [Format SQL] [Validate] [Insert Parameter]        │
├─────────────────────────────────────────────────────────────┤
│ Split View (60% Editor / 40% Helper)                       │
│ ┌──────────────────────┬────────────────────────┐         │
│ │ SQL Editor           │ Parameter Detection     │         │
│ │                      │ ┌────────────────────┐ │         │
│ │ WITH metrics AS (    │ │ Detected:          │ │         │
│ │   SELECT             │ │ • :start_date      │ │         │
│ │     campaign,        │ │ • :end_date        │ │         │
│ │     SUM(clicks)      │ │ • :campaign_ids    │ │         │
│ │   FROM impressions   │ │                    │ │         │
│ │   WHERE event_dt     │ │ Jinja Blocks:      │ │         │
│ │     BETWEEN          │ │ • {% if campaign_  │ │         │
│ │     :start_date      │ │   ids %}           │ │         │
│ │     AND :end_date    │ └────────────────────┘ │         │
│ │   {% if campaign_ids %}                       │         │
│ │   AND campaign_id IN (:campaign_ids)          │         │
│ │   {% endif %}        │ Available Tables:      │         │
│ │   GROUP BY campaign  │ • impressions          │         │
│ │ )                    │ • clicks               │         │
│ │ SELECT * FROM metrics│ • conversions          │         │
│ └──────────────────────┴────────────────────────┘         │
│ Validation: ✓ SQL is valid | 3 parameters detected        │
└─────────────────────────────────────────────────────────────┘
```

### 3. Parameters Tab
```
┌─────────────────────────────────────────────────────────────┐
│ Configure Parameters                                        │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐           │
│ │ Parameter: start_date                [↑][↓][🗑]         │
│ ├─────────────────────────────────────────────┤           │
│ │ Display Name: [Start Date_________]         │           │
│ │ Type:         [Date ▼]                      │           │
│ │ Required:     [✓]                            │           │
│ │ Default:      [2024-01-01_________]         │           │
│ │ Validation:   Min: [2023-01-01___]          │           │
│ │               Max: [2025-12-31___]          │           │
│ │ Help Text:    [Beginning of period_____]    │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ Parameter: campaign_ids           [↑][↓][🗑]           │
│ ├─────────────────────────────────────────────┤           │
│ │ Display Name: [Campaigns__________]         │           │
│ │ Type:         [Campaign List ▼]             │           │
│ │ Required:     [ ]                            │           │
│ │ Multi-select: [✓]                            │           │
│ │ Show All:     [✓]                            │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ [+ Add Parameter Manually]                                 │
└─────────────────────────────────────────────────────────────┘
```

### 4. Visualizations Tab
```
┌─────────────────────────────────────────────────────────────┐
│ Configure Charts & Visualizations                          │
├─────────────────────────────────────────────────────────────┤
│ Default View: [Table ▼]                                    │
│                                                             │
│ Charts:                                                     │
│ ┌─────────────────────────────────────────────┐           │
│ │ 1. Performance Table              [✓][⚙][🗑]           │
│ │    Type: Table | Default: Yes                │           │
│ └─────────────────────────────────────────────┘           │
│ ┌─────────────────────────────────────────────┐           │
│ │ 2. Revenue by Campaign            [✓][⚙][🗑]           │
│ │    Type: Bar Chart | X: campaign | Y: revenue│           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ [+ Add Visualization]                                      │
│                                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ Chart Configuration (Revenue by Campaign)    │           │
│ ├─────────────────────────────────────────────┤           │
│ │ Chart Type: [Bar Chart ▼]                   │           │
│ │ X Axis:     [campaign ▼]                    │           │
│ │ Y Axis:     [revenue ▼]                     │           │
│ │ Aggregation:[Sum ▼]                         │           │
│ │ Sort By:    [revenue ▼] [Desc ▼]           │           │
│ │ Limit:      [20_____]                       │           │
│ │ Colors:     [Auto ▼]                        │           │
│ └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 5. Preview & Test Tab
```
┌─────────────────────────────────────────────────────────────┐
│ Test Your Template                                         │
├─────────────────────────────────────────────────────────────┤
│ Test Parameters:                                           │
│ Start Date: [2024-01-01___] End Date: [2024-12-31___]     │
│ Campaigns:  [All Campaigns ▼]                              │
│                                                             │
│ [Generate Preview] [Run Test Query]                        │
│                                                             │
│ Generated SQL:                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ WITH metrics AS (                            │           │
│ │   SELECT                                     │           │
│ │     campaign,                                │           │
│ │     SUM(clicks)                              │           │
│ │   FROM impressions                           │           │
│ │   WHERE event_dt                             │           │
│ │     BETWEEN '2024-01-01'                    │           │
│ │     AND '2024-12-31'                        │           │
│ │   GROUP BY campaign                          │           │
│ │ )                                            │           │
│ │ SELECT * FROM metrics                        │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ Estimated Cost: $0.0234 | Estimated Time: ~45s            │
└─────────────────────────────────────────────────────────────┘
```

## Component States

### Validation States
- **Valid**: Green checkmark, subtle green background
- **Invalid**: Red X, red border, error message below
- **Warning**: Yellow !, yellow border, warning message
- **Processing**: Spinner, disabled interaction

### Auto-save Indicator
```
Saving...      (spinner)
Saved ✓        (green)
Error saving   (red)
```

## Responsive Breakpoints

### Desktop (>1280px)
- Full layout as shown
- Split views side-by-side
- All tabs visible

### Tablet (768-1280px)
- Stacked layout for split views
- Condensed tab labels
- Collapsible sections

### Mobile (<768px)
- Single column layout
- Hamburger menu for tabs
- Bottom sheet for configurations

## Color Scheme

```css
/* Primary Actions */
--primary: #4F46E5;      /* Indigo-600 */
--primary-hover: #4338CA; /* Indigo-700 */

/* Status Colors */
--success: #10B981;      /* Green-500 */
--warning: #F59E0B;      /* Amber-500 */
--error: #EF4444;        /* Red-500 */

/* UI Elements */
--border: #E5E7EB;       /* Gray-200 */
--background: #F9FAFB;   /* Gray-50 */
--text: #111827;         /* Gray-900 */
--text-muted: #6B7280;   /* Gray-500 */
```

## Interaction Patterns

### Keyboard Shortcuts
- `Ctrl/Cmd + S`: Save draft
- `Ctrl/Cmd + Enter`: Run test
- `Ctrl/Cmd + Shift + F`: Format SQL
- `Tab`: Navigate between fields
- `Ctrl/Cmd + K`: Command palette

### Drag & Drop
- Reorder parameters
- Reorder visualizations
- Drag fields from schema to SQL editor

### Context Menus
- Right-click on parameters for quick actions
- Right-click in SQL editor for snippets

## Accessibility Features
- ARIA labels on all interactive elements
- Keyboard navigation support
- High contrast mode support
- Screen reader friendly
- Focus indicators
- Error announcements

## Performance Optimizations
- Lazy load visualization tab
- Debounced SQL validation (500ms)
- Virtual scrolling for large parameter lists
- Code splitting per tab
- Optimistic UI updates