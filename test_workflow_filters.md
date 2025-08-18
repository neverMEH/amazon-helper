# Workflow Filters and Sorting Test Guide

## Features Implemented

### 1. Sorting Functionality ✅
- **Sort Dropdown** with multiple options:
  - Name (A → Z / Z → A)
  - Last Run (Newest/Oldest First)
  - Created Date (Newest/Oldest First)
  - Updated Date (Recently Modified/Least Recently)
  - Execution Count (Most/Least Executed)
  - Status (A → Z / Z → A)

### 2. Advanced Filtering ✅
- **Status Filter**: Multi-select checkboxes (Active, Draft, Archived)
- **Instance Filter**: Multi-select for AMC instances
- **Sync Status**: Radio buttons (All, Synced, Not Synced)
- **Tags Filter**: Multi-select checkboxes
- **Date Range**: Selectable field (Created/Updated/Last Executed) with date pickers and presets
- **Execution Count Range**: Min/Max number inputs

### 3. UI Enhancements ✅
- **Filter Sidebar**: Collapsible panel with all filter options
- **Active Filter Badges**: Visual chips showing applied filters with remove buttons
- **Results Counter**: Shows "X of Y workflows" when filters are active
- **Filter Indicator**: Filter button shows count badge when filters are active
- **Clear All**: Quick action to reset all filters
- **Responsive Design**: Mobile-friendly sidebar overlay

### 4. Performance & Persistence ✅
- **Debounced Search**: 300ms delay for search input
- **LocalStorage**: Saves filter and sort preferences
- **Memoized Functions**: Optimized filtering and sorting
- **Client-side Processing**: All filtering/sorting done in browser

## Testing Instructions

1. **Navigate to Workflows Page**
   - Go to http://localhost:5173
   - Login and navigate to "Workflows" (My Queries)

2. **Test Sorting**
   - Click the "Sort:" dropdown
   - Try different sort options
   - Verify the table updates accordingly
   - Check that the selected sort is highlighted in the dropdown

3. **Test Basic Filtering**
   - Use the search bar to filter by name/description
   - Click the "Filters" button to open the sidebar
   - Try selecting different status filters
   - Apply filters and verify results

4. **Test Advanced Filters**
   - Select multiple instances
   - Change sync status
   - Add date range filters with presets (Today, 7 Days, 30 Days, 90 Days)
   - Set execution count range
   - Apply combinations of filters

5. **Test Filter Badges**
   - Apply multiple filters
   - Check that active filter badges appear
   - Click the × on badges to remove individual filters
   - Use "Clear All" to reset everything

6. **Test Persistence**
   - Apply filters and sort
   - Refresh the page
   - Verify filters and sort are retained

7. **Test Responsive Design**
   - Resize browser window
   - Check filter sidebar on mobile view
   - Verify touch interactions work

## Key Features

### Filter Sidebar Layout
```
┌─────────────────────────┐
│ Filters           [X]   │
├─────────────────────────┤
│ □ Status               │
│   □ Active             │
│   □ Draft              │
│   □ Archived           │
│                         │
│ □ Instances            │
│   □ Instance 1         │
│   □ Instance 2         │
│                         │
│ ○ AMC Sync Status      │
│   ○ All                │
│   ○ Synced             │
│   ○ Not Synced         │
│                         │
│ □ Tags                 │
│   [Dynamic list]       │
│                         │
│ 📅 Date Range          │
│   [Field selector]     │
│   [Date pickers]       │
│   [Preset buttons]     │
│                         │
│ # Execution Count      │
│   [Min] [Max]          │
├─────────────────────────┤
│ [Reset] [Cancel] [Apply]│
└─────────────────────────┘
```

### Active Filters Display
```
Active Filters: [Status: Active ×] [Instance: Prod ×] [Last Run: 7 days ×] [Clear All]
Showing 12 of 45 workflows
```

## Implementation Details

### Components Created
1. `WorkflowSortDropdown.tsx` - Dropdown for sorting options
2. `WorkflowFilters.tsx` - Sidebar with all filter controls
3. `ActiveFilterBadges.tsx` - Display and manage active filters

### MyQueries.tsx Updates
- Added comprehensive state management for filters and sorting
- Implemented memoized filter and sort functions
- Added localStorage persistence
- Integrated all new components
- Enhanced UI with better layout and indicators

## Benefits
- **Improved UX**: Users can quickly find and organize workflows
- **Persistent Preferences**: Settings survive page refreshes
- **Visual Feedback**: Clear indication of active filters
- **Performance**: Optimized client-side processing
- **Flexibility**: Multiple filter combinations possible
- **Mobile-Friendly**: Responsive design for all devices