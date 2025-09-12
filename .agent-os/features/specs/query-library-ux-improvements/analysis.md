# Query Library UX Analysis & Requirements

## Current State Analysis

### Problem Statement
Users are confused when creating query templates in the Query Library. They see "No SQL query content" in template cards and don't realize they need to click "Create Template" or "Edit" to access the Monaco SQL editor.

### Current User Flow
1. User navigates to Query Library page
2. Sees template cards/list items displaying:
   - Template name
   - Description
   - "No SQL query content" (for templates without SQL)
   - Use/Edit/Delete buttons
3. User must click "Create Template" or "Edit" to open modal
4. Modal contains the actual Monaco SQL editor for writing queries

### Pain Points Identified

#### 1. Misleading Empty State Message
- **Location**: QueryLibrary.tsx (TemplateCard component, around line 573)
- **Issue**: Shows "No SQL query content" which implies no editor exists
- **Impact**: Users think the feature is incomplete or broken

#### 2. Hidden SQL Editor
- **Location**: TemplateEditor.tsx (lines 359-363)
- **Issue**: Monaco editor only visible in modal, not discoverable from main view
- **Impact**: Users don't know where to write SQL queries

#### 3. Lack of Visual Preview
- **Issue**: No SQL preview in template cards, even for existing templates
- **Impact**: Users can't quickly see what a template does without opening it

#### 4. Missing Action Guidance
- **Issue**: No clear visual cues pointing users to the Create/Edit buttons
- **Impact**: Users don't understand the workflow

## Requirements for Improvement

### Must Have (P0)
1. **Replace misleading text**: Remove "No SQL query content" message
2. **Add SQL preview**: Show truncated SQL preview in template cards (read-only)
3. **Clear action prompts**: Add visual cues for creating/editing templates
4. **Helpful empty states**: Guide users when templates have no SQL

### Should Have (P1)
1. **Syntax highlighting in preview**: Use lightweight highlighting for SQL preview
2. **Tooltips**: Add helpful tooltips on hover for key actions
3. **Empty template guidance**: Special UI for templates without SQL yet
4. **Visual hierarchy**: Make Create/Edit buttons more prominent

### Nice to Have (P2)
1. **Inline expand**: Quick expand to see full SQL without opening modal
2. **Copy SQL button**: Quick copy SQL from preview
3. **Template stats**: Show usage stats, last modified, etc.
4. **Keyboard shortcuts**: Quick keys for common actions

## Success Criteria

1. **User Understanding**: Users immediately understand how to create/edit SQL queries
2. **Reduced Confusion**: No more reports of "missing SQL editor"
3. **Improved Discoverability**: Users find and use the Monaco editor without help
4. **Better Preview**: Users can assess templates without opening each one
5. **Faster Workflow**: Reduced clicks to common actions

## Technical Approach

### Component Structure
```
QueryLibrary
├── TemplateCard (enhanced)
│   ├── SQLPreview (new component)
│   ├── ActionButtons (enhanced with tooltips)
│   └── EmptyState (new for templates without SQL)
└── TemplateEditor (modal - already working)
    └── SQLEditor (Monaco - already working)
```

### Implementation Priority
1. Create SQLPreview component
2. Update TemplateCard to show SQL preview
3. Add helpful empty states
4. Enhance action buttons with tooltips
5. Add visual cues and guidance

## Affected Files
- `/frontend/src/pages/QueryLibrary.tsx` - Main page
- `/frontend/src/components/query-library/SQLPreview.tsx` - New component
- `/frontend/src/components/query-library/TemplateCard.tsx` - Extract from QueryLibrary
- `/frontend/src/components/query-library/TemplateListItem.tsx` - Extract from QueryLibrary