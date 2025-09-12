# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-01-12-query-library-ux-fix/spec.md

> Created: 2025-01-12
> Status: Ready for Implementation

## Tasks

### Task 1: Analyze Current Query Library UX Issues
**Priority:** High
**Estimated Time:** 1 hour

#### Subtasks:
1.1. **Review QueryLibrary.tsx template card rendering**
   - Examine how template cards display SQL content
   - Identify where "No SQL query content" message is generated
   - Document current card layout and information hierarchy

1.2. **Analyze TemplateEditor.tsx modal functionality**
   - Verify Monaco editor is properly working (lines 359-363)
   - Document the complete template creation/editing flow
   - Identify any missing visual cues or navigation hints

1.3. **Test current user journey**
   - Document step-by-step user experience from Query Library page
   - Identify points of confusion in the workflow
   - Take screenshots of current state for comparison

### Task 2: Design Improved Template Card Display
**Priority:** High
**Estimated Time:** 2 hours

#### Subtasks:
2.1. **Create SQL preview component**
   - Design read-only SQL preview with syntax highlighting
   - Implement truncation logic (e.g., first 3-4 lines, max 150 chars)
   - Add "View More" indicator when content is truncated
   - Handle empty/null SQL gracefully

2.2. **Redesign template card layout**
   - Replace "No SQL query content" with SQL preview or placeholder
   - Add visual indicators for templates with/without SQL
   - Include clear call-to-action buttons ("Edit Template", "View SQL")
   - Ensure consistent spacing and visual hierarchy

2.3. **Add helpful empty state messaging**
   - Create informative placeholder for templates without SQL
   - Add guidance text like "Click 'Edit' to add SQL query"
   - Include visual icons or graphics to guide user action

### Task 3: Enhance Navigation and User Guidance
**Priority:** Medium
**Estimated Time:** 1.5 hours

#### Subtasks:
3.1. **Improve "Create Template" button visibility**
   - Ensure button is prominent and clearly labeled
   - Consider adding tooltip explaining the template creation process
   - Position button optimally for user discovery

3.2. **Add tooltips and help text**
   - Add tooltip to template cards explaining edit functionality
   - Include help text near empty states
   - Add contextual hints about Monaco editor availability

3.3. **Implement breadcrumb or flow indicators**
   - Show users where they are in the template creation process
   - Add visual cues that editing opens a modal with full SQL editor
   - Consider adding a brief onboarding flow for first-time users

### Task 4: Write Comprehensive Tests
**Priority:** Medium
**Estimated Time:** 2 hours

#### Subtasks:
4.1. **Unit tests for SQL preview component**
   - Test SQL content truncation logic
   - Test handling of empty/null SQL content
   - Test syntax highlighting rendering
   - Test "View More" indicator functionality

4.2. **Integration tests for template card rendering**
   - Test template cards with various SQL content lengths
   - Test empty template card display
   - Test template card interaction flows
   - Test modal opening from template cards

4.3. **E2E tests for complete user journey**
   - Test complete template creation flow
   - Test template editing workflow
   - Test template card display and interaction
   - Test user guidance elements (tooltips, help text)

### Task 5: Implement SQL Preview Component
**Priority:** High
**Estimated Time:** 3 hours

#### Subtasks:
5.1. **Create SQLPreview component**
   ```typescript
   interface SQLPreviewProps {
     sql: string | null;
     maxLines?: number;
     maxChars?: number;
     showLineNumbers?: boolean;
     className?: string;
   }
   ```

5.2. **Implement truncation and formatting logic**
   - Add intelligent SQL truncation (preserve complete statements when possible)
   - Implement basic syntax highlighting for preview
   - Handle special characters and formatting
   - Add loading states for dynamic content

5.3. **Add expand/collapse functionality**
   - Implement "Show More/Less" toggle for longer SQL
   - Add smooth transitions for expand/collapse
   - Ensure accessibility for screen readers
   - Maintain performance with large SQL content

### Task 6: Update QueryLibrary Component
**Priority:** High
**Estimated Time:** 2.5 hours

#### Subtasks:
6.1. **Replace "No SQL query content" messaging**
   - Remove misleading "No SQL query content" text
   - Integrate SQLPreview component into template cards
   - Add appropriate fallback messaging for empty templates

6.2. **Enhance template card layout**
   - Improve visual hierarchy of template information
   - Add clear edit/view action buttons
   - Implement hover states and interaction feedback
   - Ensure responsive design for various screen sizes

6.3. **Add user guidance elements**
   - Implement tooltips for template actions
   - Add empty state illustrations or graphics
   - Include contextual help text for new users
   - Add loading states during template operations

### Task 7: Improve TemplateEditor Modal UX
**Priority:** Medium
**Estimated Time:** 1.5 hours

#### Subtasks:
7.1. **Enhance modal header and navigation**
   - Add clear title indicating editing mode vs. creation mode
   - Include breadcrumb or context information
   - Add save/cancel button states and feedback

7.2. **Improve Monaco editor integration**
   - Ensure proper focus management when modal opens
   - Add editor shortcuts and help text
   - Implement auto-save or draft functionality
   - Add SQL validation feedback

7.3. **Add modal onboarding**
   - Include brief explanation of SQL editor capabilities
   - Add helpful hints for SQL query construction
   - Consider adding query examples or templates

### Task 8: Accessibility and Performance Optimization
**Priority:** Medium
**Estimated Time:** 2 hours

#### Subtasks:
8.1. **Implement accessibility improvements**
   - Add proper ARIA labels for template cards and actions
   - Ensure keyboard navigation works correctly
   - Add screen reader support for SQL preview content
   - Test with accessibility tools and make corrections

8.2. **Optimize performance**
   - Implement lazy loading for SQL preview rendering
   - Add memoization for expensive SQL formatting operations
   - Optimize re-renders in template list
   - Add performance monitoring for large template lists

8.3. **Cross-browser testing**
   - Test SQL preview rendering across browsers
   - Verify Monaco editor compatibility
   - Test modal functionality and responsive design
   - Ensure consistent user experience

### Task 9: Documentation and Code Review
**Priority:** Low
**Estimated Time:** 1 hour

#### Subtasks:
9.1. **Update component documentation**
   - Document new SQLPreview component props and usage
   - Update QueryLibrary component documentation
   - Add examples of proper template card implementation

9.2. **Code review and cleanup**
   - Remove unused code related to old "No SQL query content" logic
   - Ensure consistent coding standards and patterns
   - Optimize imports and dependencies
   - Add proper TypeScript types for new components

9.3. **Create usage examples**
   - Document best practices for template creation UX
   - Add examples of effective empty states
   - Create guidelines for SQL preview implementation