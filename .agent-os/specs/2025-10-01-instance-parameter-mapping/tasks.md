# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-10-01-instance-parameter-mapping/spec.md

> Created: 2025-10-01
> Status: Ready for Implementation

## Tasks

### Task 1: Database Schema & Migration ✅

**Goal**: Create and apply database schema changes for instance-level parameter mappings

- [x] 1.1. Write migration script `scripts/apply_instance_parameter_mapping_migration.py` to create:
  - `instance_brand_asins` table (id, instance_id, brand_id, asin_id, created_at)
  - `instance_brand_campaigns` table (id, instance_id, brand_id, campaign_id, created_at)
  - Add `brand_tag` column to `campaign_mappings` table (nullable VARCHAR)
  - Create indexes on foreign keys and brand_tag
  - Add RLS policies for user access control
- [x] 1.2. Write unit tests in `tests/supabase/test_instance_parameter_mapping_schema.py` to verify:
  - Tables created with correct columns and types
  - Foreign key constraints work properly
  - Indexes exist and improve query performance
  - RLS policies restrict access appropriately
- [x] 1.3. Apply migration to development database
- [x] 1.4. Verify schema in Supabase dashboard
- [x] 1.5. Seed test data for development (at least 2 instances with brand/ASIN/campaign mappings)
- [x] 1.6. Verify all schema tests pass

---

### Task 2: Backend Service Layer & API Endpoints ✅

**Goal**: Implement service layer and REST API for managing instance parameter mappings

- [ ] 2.1. Write unit tests in `tests/test_instance_mapping_service.py` for:
  - Fetching instance mappings (ASINs and campaigns by brand)
  - Saving ASIN mappings (create/delete)
  - Saving campaign mappings (create/delete with brand_tag updates)
  - Handling edge cases (non-existent instances, duplicate mappings, invalid IDs)
  - Permission validation (user can only access their instances)
- [x] 2.2. Create `amc_manager/services/instance_mapping_service.py`:
  - Service class with db_service integration
  - Implement `get_available_brands(user_id)` - returns all available brands
  - Implement `get_brand_asins(brand_tag, user_id, search, limit, offset)` - returns ASINs for brand
  - Implement `get_brand_campaigns(brand_tag, user_id, ...)` - returns campaigns (placeholder for now)
  - Implement `get_instance_mappings(instance_id, user_id)` - returns complete mappings
  - Implement `save_instance_mappings(instance_id, user_id, mappings)` - transactional save
  - Implement `get_parameter_values(instance_id, user_id)` - formatted for auto-population
- [x] 2.3. Create Pydantic schemas in `amc_manager/schemas/instance_mapping.py`:
  - `InstanceMappingsInput` - request schema with validation
  - `InstanceMappingsOutput` - response schema
  - `SaveMappingsResponse` - save operation response
  - `Brand`, `ASIN`, `Campaign` - entity schemas
  - `BrandsListResponse`, `BrandASINsResponse`, `BrandCampaignsResponse` - list responses
  - `ParameterValuesOutput` - auto-populate response
- [x] 2.4. Create API endpoints in `amc_manager/api/supabase/instance_mappings.py`:
  - `GET /api/instances/{instance_id}/available-brands` - get all available brands
  - `GET /api/instances/{instance_id}/brands/{brand_tag}/asins` - get ASINs for brand
  - `GET /api/instances/{instance_id}/brands/{brand_tag}/campaigns` - get campaigns for brand
  - `GET /api/instances/{instance_id}/mappings` - get all mappings
  - `POST /api/instances/{instance_id}/mappings` - save mappings
  - `GET /api/instances/{instance_id}/parameter-values` - get auto-populate values
- [x] 2.5. Register routes in `main_supabase.py`
- [ ] 2.6. Write integration tests in `tests/test_api_instance_mappings.py`:
  - Test all 6 API endpoints with valid data
  - Test authentication/authorization (wrong user, missing token)
  - Test validation errors (invalid IDs, missing fields)
  - Test concurrent updates and race conditions
- [ ] 2.7. Verify API endpoints in Swagger docs at `http://localhost:8001/docs`
- [ ] 2.8. Verify all tests pass with `pytest tests/test_instance_mapping_service.py tests/test_api_instance_mappings.py -v`

---

### Task 3: Frontend Components - Instance Mapping Tab UI

**Goal**: Build the Instance Mapping tab UI with brand/ASIN/campaign management

- [ ] 3.1. Write unit tests in `frontend/src/components/instances/__tests__/InstanceMappingTab.test.tsx`:
  - Component renders with loading state
  - Displays brands with ASIN and campaign counts
  - Handles brand selection and shows detail view
  - Shows empty states appropriately
  - Error handling for failed API calls
- [ ] 3.2. Create `frontend/src/services/instanceMappingService.ts`:
  - `getMappings(instanceId)` - fetch all mappings
  - `saveASINMappings(instanceId, brandId, asinIds)` - save ASIN mappings
  - `deleteASINMapping(instanceId, brandId, asinId)` - delete ASIN
  - `saveCampaignMappings(instanceId, brandId, campaignIds, brandTag)` - save campaigns
  - `deleteCampaignMapping(instanceId, brandId, campaignId)` - delete campaign
  - `getAutoPopulateDefaults(instanceId)` - get default parameters
- [ ] 3.3. Create `frontend/src/components/instances/BrandSelector.tsx`:
  - Display list of brands with ASIN/campaign counts
  - Highlight selected brand
  - Show "All Brands" option at top
  - Use Tailwind for styling (consistent with app design)
- [ ] 3.4. Create `frontend/src/components/instances/ASINManager.tsx`:
  - Display list of ASINs for selected brand
  - Multi-select interface with checkboxes
  - Search/filter ASINs by name or ID
  - Save and delete buttons with loading states
  - Success/error toast notifications
- [ ] 3.5. Create `frontend/src/components/instances/CampaignManager.tsx`:
  - Display list of campaigns for selected brand
  - Multi-select interface with checkboxes
  - Search/filter campaigns by name
  - Brand tag input field (text input)
  - Save and delete buttons with loading states
  - Success/error toast notifications
- [ ] 3.6. Create `frontend/src/components/instances/InstanceMappingTab.tsx`:
  - Three-column layout (Brand | ASINs | Campaigns)
  - Integrate BrandSelector, ASINManager, CampaignManager
  - Use TanStack Query for data fetching and caching
  - Handle loading, error, and empty states
  - Implement optimistic updates on save/delete
- [ ] 3.7. Integrate Mapping tab into `frontend/src/pages/InstanceDetail.tsx`:
  - Add "Mappings" tab to existing tab navigation
  - Pass instance_id prop to InstanceMappingTab
  - Ensure tab switching preserves state
- [ ] 3.8. Verify UI functionality manually:
  - Test brand selection updates ASIN/campaign views
  - Test multi-select and save operations
  - Test delete operations with confirmation
  - Test search/filter functionality
  - Verify responsive layout on different screen sizes
  - Verify all unit tests pass with `npm test`

---

### Task 4: Auto-Population Integration

**Goal**: Integrate instance mappings into query execution contexts to auto-populate parameters

- [ ] 4.1. Write integration tests in `frontend/src/components/__tests__/AutoPopulateIntegration.test.tsx`:
  - Instance selection triggers parameter auto-population
  - Parameters correctly populate from instance mappings
  - Manual parameter changes override auto-populated values
  - Visual indicators show when parameters are auto-populated
  - Works in WorkflowEditor, QueryLibrary, and ReportBuilder
- [ ] 4.2. Create `frontend/src/hooks/useInstanceMappings.ts`:
  - Custom hook to fetch and cache instance mappings
  - Return `{ mappings, isLoading, error, refetch }`
  - Use TanStack Query for caching with 5-minute stale time
- [ ] 4.3. Update `frontend/src/components/workflows/WorkflowEditor.tsx`:
  - Add useEffect to watch `selectedInstanceId` changes
  - Call `getAutoPopulateDefaults(instanceId)` on instance selection
  - Pre-fill brand, ASIN, and campaign parameter fields
  - Add badge/icon next to auto-populated fields (e.g., "🔗 Auto")
  - Allow manual override (clicking field removes auto-populate indicator)
- [ ] 4.4. Update `frontend/src/pages/QueryLibrary.tsx`:
  - Add useEffect to watch instance selection
  - Auto-populate template parameters from instance mappings
  - Show visual indicator for auto-populated fields
  - Preserve manual overrides during instance switching
- [ ] 4.5. Update `frontend/src/pages/ReportBuilder.tsx`:
  - Add useEffect to watch instance selection
  - Auto-populate data collection parameters
  - Show visual indicator for auto-populated fields
  - Handle cases where multiple brands exist (default to first or show selector)
- [ ] 4.6. Create `frontend/src/utils/parameterAutoPopulator.ts`:
  - Utility function `autoPopulateParameters(mappings, currentParams)`
  - Returns merged parameters with auto-populate metadata
  - Handles conflicts (manual > auto-populated)
  - Validates parameter types match expected formats
- [ ] 4.7. Add user feedback:
  - Toast notification on first auto-populate: "Parameters populated from instance mappings"
  - Tooltip on auto-populate indicator explaining the feature
  - Help text in parameter sections mentioning auto-population
- [ ] 4.8. Verify auto-population works end-to-end:
  - Select instance in WorkflowEditor → parameters auto-fill
  - Change instance → parameters update
  - Manual override persists until instance change
  - Visual indicators appear/disappear correctly
  - Verify all integration tests pass with `npm test`

---

### Task 5: Testing, Documentation & Verification

**Goal**: Comprehensive testing and final verification of the complete feature

- [ ] 5.1. Write E2E tests in `frontend/e2e/instance-parameter-mapping.spec.ts`:
  - Full flow: navigate to instance → mappings tab → add ASINs → save
  - Full flow: add campaigns with brand tag → save → verify in database
  - Full flow: create workflow → select instance → verify auto-populated parameters
  - Test error scenarios (network failures, invalid data, permission errors)
  - Test concurrent user editing same mappings
- [ ] 5.2. Run all backend tests:
  - `pytest tests/supabase/test_instance_mappings_schema.py -v`
  - `pytest tests/test_instance_mapping_service.py -v`
  - `pytest tests/test_api_instance_mappings.py -v`
  - Ensure 100% pass rate and >80% code coverage
- [ ] 5.3. Run all frontend tests:
  - `npm test` (unit tests with Vitest)
  - `npm run test:coverage` (ensure >80% coverage for new components)
  - `npx playwright test frontend/e2e/instance-parameter-mapping.spec.ts`
- [ ] 5.4. Performance testing:
  - Test with 100+ ASINs mapped to single instance
  - Test with 50+ campaigns mapped across 10 brands
  - Verify UI remains responsive (< 2s load time)
  - Verify API response times (< 500ms for mappings endpoint)
  - Check database query performance with EXPLAIN ANALYZE
- [ ] 5.5. Manual testing checklist:
  - [ ] Create new instance mappings from scratch
  - [ ] Edit existing mappings (add/remove ASINs and campaigns)
  - [ ] Delete individual mappings
  - [ ] Verify mappings appear in workflow editor
  - [ ] Verify auto-population works on instance switch
  - [ ] Test with multiple brands per instance
  - [ ] Test with no mappings (empty state)
  - [ ] Test permission boundaries (user A cannot edit user B's mappings)
- [ ] 5.6. Update `CLAUDE.md` with:
  - New database tables (instance_brand_asins, instance_brand_campaigns)
  - New API endpoints (6 instance mapping endpoints)
  - New frontend components (InstanceMappingTab, BrandSelector, ASINManager, CampaignManager)
  - Critical gotcha: Campaign brand_tag field is nullable and optional
- [ ] 5.7. Create user-facing documentation (if requested):
  - Feature announcement
  - How to set up instance parameter mappings
  - How auto-population works in different contexts
  - Screenshots of the UI
- [ ] 5.8. Final verification:
  - [ ] All tests passing (backend + frontend + E2E)
  - [ ] No console errors or warnings
  - [ ] No TypeScript errors (`npx tsc --noEmit`)
  - [ ] No linting errors (`npm run lint`)
  - [ ] Feature works in production build (`npm run build && npm run preview`)
  - [ ] Database migration applied successfully
  - [ ] CLAUDE.md updated with new feature details

---

## Definition of Done

- [ ] All 5 tasks completed with all subtasks checked off
- [ ] All automated tests passing (backend, frontend, E2E)
- [ ] Code coverage >80% for new code
- [ ] No TypeScript or linting errors
- [ ] Manual testing checklist 100% complete
- [ ] CLAUDE.md updated with architectural changes
- [ ] Feature deployed and verified in development environment
- [ ] Ready for code review and QA testing

---

## Technical Dependencies

**Task Order**: Tasks should be completed sequentially (1 → 2 → 3 → 4 → 5) due to dependencies:
- Task 2 depends on Task 1 (schema must exist)
- Task 3 depends on Task 2 (API endpoints must exist)
- Task 4 depends on Task 3 (UI components must exist)
- Task 5 depends on all previous tasks (integration testing)

**Estimated Effort**: 3-4 days for full implementation and testing

**Risk Areas**:
- Complex three-column UI layout may require CSS refinement
- Auto-population logic must handle edge cases gracefully
- Performance with large numbers of mappings needs monitoring
- RLS policies must be thoroughly tested for security
