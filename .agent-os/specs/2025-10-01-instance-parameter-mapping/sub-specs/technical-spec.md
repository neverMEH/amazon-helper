# Technical Specification - Instance Parameter Mapping

## Technical Requirements

### 1. UI/UX Design

#### Instance Detail Page - Mapping Tab
**Location**: New tab on Instance Detail page, positioned next to "Executions" tab

**Layout Structure**:
```
Instance Detail Page
├── Overview (existing)
├── Executions (existing)
└── Mapping (NEW)
    ├── Header: "Parameter Mapping Configuration"
    ├── Save/Cancel buttons (top-right)
    └── Main Content: Three-column layout
        ├── Left Column: Brand Selection (30% width)
        │   ├── Search/filter input
        │   ├── "Select All" / "Deselect All" buttons
        │   └── Brand list with checkboxes
        ├── Middle Column: ASIN Management (35% width)
        │   ├── Tab header: "ASINs by Brand"
        │   ├── Brand filter dropdown (shows selected brands)
        │   ├── Search/filter input
        │   ├── "Select All" / "Deselect All" buttons (per brand)
        │   └── Collapsible brand sections
        │       └── ASIN checkboxes with ASIN + title display
        └── Right Column: Campaign Management (35% width)
            ├── Tab header: "Campaigns by Brand"
            ├── Brand filter dropdown (shows selected brands)
            ├── Search/filter input
            ├── "Select All" / "Deselect All" buttons (per brand)
            └── Collapsible brand sections
                └── Campaign checkboxes with name + type display
```

**Interaction Flows**:
1. **Initial Load**: Fetch existing mappings and display checked items
2. **Brand Selection**:
   - User checks/unchecks brand → triggers fetch of ASINs/campaigns for that brand
   - By default, all ASINs and campaigns under a selected brand are checked
3. **ASIN/Campaign Filtering**:
   - User can expand/collapse brand sections
   - Search filters within each column
   - Unchecking items marks them as excluded (stored in database)
4. **Save Action**:
   - Validates at least one brand is selected
   - Sends payload to backend API
   - Shows success/error notification
   - Reloads instance detail page

**Visual Design**:
- Use existing Tailwind CSS styles for consistency
- Checkboxes: Default browser styling with indeterminate state for partial selections
- Collapsible sections: Chevron icon (up/down) for expand/collapse
- Loading states: Skeleton loaders for async operations
- Empty states: "No brands available", "No ASINs for this brand", etc.

#### Auto-Population in Workflow Execution
**Location**: Workflow creation/edit modal, Query Library execution modal, Report Builder

**Behavior**:
1. User selects instance from dropdown
2. System detects parameters in SQL: `{{brand_list}}`, `{{asin_list}}`, `{{campaign_ids}}`
3. API call fetches instance mappings: `GET /api/instances/{instance_id}/parameter-mappings`
4. Parameter inputs are pre-filled:
   - **Brand parameter**: Comma-separated list of selected brand tags
   - **ASIN parameter**: Comma-separated list of checked ASINs
   - **Campaign parameter**: Comma-separated list of checked campaign IDs
5. User can edit/override the pre-filled values
6. Visual indicator: Show "(Auto-populated from instance)" label next to pre-filled fields

### 2. Frontend Components

#### New Components to Create

**`InstanceMappingTab.tsx`**
```typescript
interface InstanceMappingTabProps {
  instanceId: string;
}

// Main container component
// Manages state for brands, ASINs, campaigns, and selections
// Handles save/cancel actions
```

**`BrandSelector.tsx`**
```typescript
interface BrandSelectorProps {
  selectedBrands: string[];
  onBrandToggle: (brandTag: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
}

// Left column: Brand selection with checkboxes
// Search/filter functionality
```

**`ASINManager.tsx`**
```typescript
interface ASINManagerProps {
  selectedBrands: string[];
  selectedASINs: Record<string, string[]>; // brandTag → ASIN[]
  onASINToggle: (brandTag: string, asin: string) => void;
  onBrandSelectAll: (brandTag: string) => void;
  onBrandDeselectAll: (brandTag: string) => void;
}

// Middle column: ASIN management grouped by brand
// Collapsible brand sections with ASIN checkboxes
```

**`CampaignManager.tsx`**
```typescript
interface CampaignManagerProps {
  selectedBrands: string[];
  selectedCampaigns: Record<string, string[]>; // brandTag → campaignId[]
  onCampaignToggle: (brandTag: string, campaignId: string) => void;
  onBrandSelectAll: (brandTag: string) => void;
  onBrandDeselectAll: (brandTag: string) => void;
}

// Right column: Campaign management grouped by brand
// Collapsible brand sections with campaign checkboxes
```

#### Modified Components

**`InstanceDetail.tsx`**
- Add "Mapping" tab to existing tab navigation
- Conditional rendering: `<InstanceMappingTab instanceId={instance.id} />`

**`WorkflowEditor.tsx` / `QueryLibraryExecution.tsx` / `ReportBuilder.tsx`**
- Add `useEffect` hook that watches `selectedInstanceId`
- On change, call `fetchInstanceParameterMappings(instanceId)`
- Pre-fill parameter form fields with returned data

### 3. Backend Service Layer

#### New Service: `InstanceMappingService`
**File**: `amc_manager/services/instance_mapping_service.py`

```python
class InstanceMappingService(DatabaseService):
    """
    Manages instance-level parameter mappings for brands, ASINs, and campaigns.
    """

    async def get_available_brands(self, user_id: str) -> List[dict]:
        """Fetch all brands available to user from brand_configurations and campaign_mappings"""

    async def get_brand_asins(self, brand_tag: str, user_id: str) -> List[dict]:
        """Fetch all ASINs associated with a brand from product_asins table"""

    async def get_brand_campaigns(self, brand_tag: str, user_id: str) -> List[dict]:
        """Fetch all campaigns associated with a brand from campaign_mappings table"""

    async def get_instance_mappings(self, instance_id: str, user_id: str) -> dict:
        """
        Retrieve current mappings for an instance.
        Returns: {
            'brands': ['brand1', 'brand2'],
            'asins': {'brand1': ['ASIN1', 'ASIN2'], 'brand2': ['ASIN3']},
            'campaigns': {'brand1': ['12345', '67890'], 'brand2': ['11111']}
        }
        """

    async def save_instance_mappings(
        self,
        instance_id: str,
        user_id: str,
        mappings: dict
    ) -> dict:
        """
        Save instance mappings to database tables.
        Handles three tables:
        - instance_brands (brand associations)
        - instance_brand_asins (ASIN inclusions per brand)
        - instance_brand_campaigns (campaign inclusions per brand)

        Strategy: Delete existing + insert new (transactional)
        """

    async def get_parameter_values(self, instance_id: str, user_id: str) -> dict:
        """
        Get formatted parameter values for auto-population.
        Returns: {
            'brands': 'brand1,brand2,brand3',
            'asins': 'B001,B002,B003,B004',
            'campaign_ids': '12345,67890,11111'
        }
        """
```

### 4. Data Flow Architecture

#### Mapping Configuration Flow
```
User Action (UI)
    ↓
InstanceMappingTab Component
    ↓
instanceMappingService.saveInstanceMappings()
    ↓
POST /api/instances/{instance_id}/mappings
    ↓
InstanceMappingService.save_instance_mappings()
    ↓
Database (Transactional):
    1. DELETE FROM instance_brands WHERE instance_id = ?
    2. INSERT INTO instance_brands (brand associations)
    3. DELETE FROM instance_brand_asins WHERE instance_id = ?
    4. INSERT INTO instance_brand_asins (ASIN inclusions)
    5. DELETE FROM instance_brand_campaigns WHERE instance_id = ?
    6. INSERT INTO instance_brand_campaigns (campaign inclusions)
    ↓
Return success/error
    ↓
UI updates + notification
```

#### Auto-Population Flow
```
User selects instance (UI)
    ↓
useEffect hook triggers
    ↓
instanceMappingService.getParameterValues(instanceId)
    ↓
GET /api/instances/{instance_id}/parameter-mappings
    ↓
InstanceMappingService.get_parameter_values()
    ↓
Database Queries:
    1. Fetch brands from instance_brands
    2. Fetch ASINs from instance_brand_asins (join with product_asins)
    3. Fetch campaigns from instance_brand_campaigns (join with campaign_mappings)
    ↓
Format as comma-separated strings
    ↓
Return to frontend
    ↓
Pre-fill parameter form fields
```

### 5. Integration Points

#### Workflow Execution Integration
**Files to Modify**:
- `frontend/src/components/workflows/WorkflowEditor.tsx`
- `frontend/src/pages/QueryLibrary.tsx`
- `frontend/src/components/report-builder/RunReportModal.tsx`

**Changes**:
1. Add `useEffect` to watch `selectedInstanceId`
2. Call `fetchInstanceParameterMappings(instanceId)` on change
3. Update parameter state with returned values
4. Add visual indicator for auto-populated fields

#### Parameter Detection Integration
**Existing System**: `parameterDetection.ts` detects `{{parameter_name}}` in SQL

**Enhancement**: Map detected parameter types to instance mappings:
- `{{brand_list}}` → `mappings.brands`
- `{{asin_list}}` → `mappings.asins`
- `{{campaign_ids}}` → `mappings.campaign_ids`
- `{{campaign_names}}` → `mappings.campaign_names` (if needed)

### 6. Performance Considerations

#### Caching Strategy
- **Frontend**: Use React Query with 5-minute stale time for instance mappings
- **Cache Keys**: `['instance-mappings', instanceId]`
- **Invalidation**: On save, invalidate cache for that instance

#### Database Optimization
- **Indexes**: Add indexes on foreign keys and brand_tag columns (see database-schema.md)
- **Query Optimization**: Use JOINs instead of multiple round-trip queries
- **Batch Operations**: Use multi-row INSERTs for saving mappings

#### UI Performance
- **Lazy Loading**: Load ASINs/campaigns only when brand is selected
- **Virtualization**: If ASIN/campaign lists exceed 100 items, use `react-window` for virtualization
- **Debouncing**: Debounce search inputs (300ms delay)

### 7. Error Handling

#### Frontend Error Scenarios
1. **API Failure**: Show error notification, keep form editable, allow retry
2. **Network Timeout**: Show retry button with exponential backoff
3. **Validation Errors**: Inline error messages (e.g., "At least one brand must be selected")

#### Backend Error Scenarios
1. **Instance Not Found**: Return 404 with message
2. **Unauthorized Access**: Return 403 if user doesn't own instance
3. **Database Constraint Violation**: Return 400 with validation details
4. **Transaction Failure**: Rollback all changes, return 500

### 8. Testing Strategy

#### Unit Tests
- `InstanceMappingService` methods (mock database calls)
- Parameter formatting functions
- Brand/ASIN/campaign filtering logic

#### Integration Tests
- Full mapping save/retrieve flow
- Auto-population integration with workflow execution
- Permission checks (user must own instance)

#### E2E Tests (Playwright)
```typescript
test('Configure instance mappings and verify auto-population', async ({ page }) => {
  // Navigate to instance detail
  // Open Mapping tab
  // Select brands
  // Select ASINs and campaigns
  // Save mappings
  // Navigate to workflow editor
  // Select same instance
  // Verify parameters are auto-populated
});
```

### 9. Accessibility Requirements

- **Keyboard Navigation**: All checkboxes and buttons must be keyboard accessible
- **Screen Reader Support**: Proper ARIA labels for all interactive elements
- **Focus Management**: Logical tab order through form elements
- **Visual Indicators**: Clear focus states for all interactive elements

### 10. Browser Compatibility

- **Target Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Responsive Design**: Support desktop viewports (1280px+)
- **Mobile**: Not required for this feature (admin/power user feature)

## External Dependencies

No new external dependencies are required. This feature uses existing libraries and frameworks:
- **Frontend**: React, React Query, Tailwind CSS (all already in use)
- **Backend**: FastAPI, Supabase client (all already in use)
