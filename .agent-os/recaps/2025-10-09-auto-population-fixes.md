# 2025-10-09: Instance Parameter Mapping Auto-Population Fixes

## Summary

Fixed multiple critical issues preventing the auto-population feature from working in the Report Builder. The feature now successfully auto-populates ASINs and campaigns from instance mappings when users select an instance in the Report Builder.

## Issues Fixed

### 1. Parameter Type Detection - Missing "tracked" Keyword
**Problem**: Parameters named "tracked_asins" or "tracked ASINs" weren't being detected as ASIN parameters.

**Root Cause**: The `parameterDetection.ts` ASIN_KEYWORDS array didn't include "tracked".

**Fix**: Added "tracked", "tracked_asin", and "tracked_asins" to the ASIN_KEYWORDS array.

**Files Changed**:
- `frontend/src/utils/parameterDetection.ts` - Added tracked keywords to ASIN detection

**Commit**: `ce76349`

---

### 2. Instance ID Format Mismatch - UUID vs String
**Problem**: Auto-population API was returning empty mappings even though mappings existed in the database.

**Root Cause**:
- `InstanceSelector` was passing `instance.instanceId` (string like "amcibersblt")
- But the mappings API expects `instance.id` (UUID like "132dfc74-...")
- Backend uses UUID as foreign key in `instance_brand_asins` and `instance_brand_campaigns` tables

**Fix**: Changed `InstanceSelector` to pass `instance.id` (UUID) instead of `instance.instanceId` (string).

**Files Changed**:
- `frontend/src/components/query-builder/InstanceSelector.tsx` - Changed to pass UUID

**Commit**: `74a050d`

**Impact**: This was the critical fix that made mappings API return actual data instead of empty results.

---

### 3. Empty Array Handling in Auto-Population Logic
**Problem**: Even with mappings data loaded, auto-population wasn't populating parameters.

**Root Cause**: JavaScript empty arrays `[]` are truthy, so the check `!currentValue` returned false for empty arrays, treating them as "already has a value" instead of "needs to be populated".

**Fixes**:
1. **parameterAutoPopulator.ts**: Updated manual value check to explicitly exclude empty arrays:
   ```typescript
   if (manualValue !== undefined && manualValue !== null && manualValue !== '' &&
       !(Array.isArray(manualValue) && manualValue.length === 0))
   ```

2. **RunReportModal.tsx**: Updated hasNewValues detection to properly check for empty arrays:
   ```typescript
   const currentIsEmpty = !currentValue ||
                         currentValue === '' ||
                         (Array.isArray(currentValue) && currentValue.length === 0);
   ```

**Files Changed**:
- `frontend/src/utils/parameterAutoPopulator.ts` - Empty array check in preservation logic
- `frontend/src/components/report-builder/RunReportModal.tsx` - Empty array detection

**Commits**: `534e0a2`, `0af4ffc`

---

### 4. Cache Invalidation - Stale Mappings Data
**Problem**: After saving mappings in the Mappings tab, the Report Builder would still show old empty mappings.

**Root Cause**: React Query was caching the previous (empty) response and not refetching when the instance was selected.

**Fix**: Added `refetch()` call in a useEffect that triggers when `selectedInstance` or `isOpen` changes.

**Files Changed**:
- `frontend/src/components/report-builder/RunReportModal.tsx` - Added refetch on instance change
- `frontend/src/hooks/useInstanceMappings.ts` - Added console logging for debugging

**Commits**: `b903477`, `02d73f5`

---

### 5. Workflow Creation 403 Forbidden Error
**Problem**: After fixing InstanceSelector to pass UUIDs (fix #2), users got 403 Forbidden when trying to create workflows and were logged out.

**Root Cause**: The workflow creation endpoint was checking `inst['instance_id'] == workflow.instance_id`, but now `workflow.instance_id` is a UUID instead of the instance string.

**Fix**: Updated instance access checks to support both UUID and instance string:
```python
instance = next(
    (inst for inst in user_instances
     if inst['id'] == workflow.instance_id or inst['instance_id'] == workflow.instance_id),
    None
)
```

**Files Changed**:
- `amc_manager/api/supabase/workflows.py` - Updated two instance access checks (lines 157-161, 1430)

**Commits**: `efb0f6c`, `05e071a`

---

## Technical Details

### Auto-Population Flow (Working)

1. User opens Report Builder → selects template
2. User selects instance from InstanceSelector
3. **InstanceSelector passes UUID** → `onChange(instance.id)`
4. **RunReportModal refetches mappings** → `useInstanceMappings(selectedInstance)`
5. **API returns mappings** → `GET /api/instances/{uuid}/mappings`
6. **Parameters detected** → `tracked_asins` matched via "tracked" keyword
7. **Auto-population triggered** → `autoPopulateParameters(instanceMappings, ...)`
8. **Empty arrays treated as empty** → `currentIsEmpty: true`
9. **74 ASINs populated** → `setParameters(newValues)`
10. **Success toast shown** → "Parameters populated from instance mappings 🔗"

### Key Learnings

1. **JavaScript Truthiness**: Empty arrays `[]` are truthy - always use `.length === 0` for array checks
2. **Instance ID Consistency**: Backend should standardize on either UUID or string, not both
3. **Cache Invalidation**: Use `invalidateQueries()` after mutations and `refetch()` when data dependencies change
4. **Parameter Detection**: Be generous with keyword matching - include variations like "tracked", "selected", etc.

## Files Modified Summary

### Frontend (9 files)
- `frontend/src/components/query-builder/InstanceSelector.tsx`
- `frontend/src/components/report-builder/RunReportModal.tsx`
- `frontend/src/hooks/useInstanceMappings.ts`
- `frontend/src/utils/parameterAutoPopulator.ts`
- `frontend/src/utils/parameterDetection.ts`

### Backend (1 file)
- `amc_manager/api/supabase/workflows.py`

### Documentation (1 file)
- `CLAUDE.md`

## Commits

1. `59ead8f` - Improve ASIN parameter detection in Report Builder auto-population
2. `ce76349` - Add 'tracked' keyword to ASIN parameter detection
3. `3844290` - Improve auto-population value detection logic in RunReportModal
4. `74a050d` - Use UUID instead of instance string for instance mappings API
5. `534e0a2` - Add detailed logging to autoPopulateParameters function
6. `0af4ffc` - Treat empty arrays as empty values for auto-population detection
7. `b903477` - Force refetch of instance mappings when instance is selected
8. `02d73f5` - Add detailed API response logging for instance mappings
9. `04e4501` - Update CLAUDE.md with auto-population troubleshooting tips
10. `efb0f6c` - Support UUID in workflow creation instance access check
11. `05e071a` - Support UUID in all workflow instance access checks

## Testing

### Manual Testing - Complete ✅
- Configured mappings in Instance → Mappings tab (1 brand, 74 ASINs, 351 campaigns)
- Saved mappings successfully
- Opened Report Builder for "WEEKLY 4-STAGE MARKETING FUNNEL ANALYSIS"
- Selected instance with mappings
- **Result**: 74 ASINs auto-populated into `tracked_asins` parameter
- Created workflow successfully without 403 error
- Green toast notification displayed

### Console Verification
```javascript
[RunReportModal] ASINs by brand: {Supergoop!: Array(74)}
  - Supergoop!: 74 ASINs
[RunReportModal] ✓ tracked_asins has new array values (74 items)
[RunReportModal] Has new values to populate? true
// Toast: "Parameters populated from instance mappings 🔗"
```

## Deployment

All changes committed to `instance-parameter-mapping` branch and pushed to GitHub.

**Branch**: `instance-parameter-mapping`
**Commits**: 11 commits (59ead8f → 05e071a)
**Status**: Ready for Railway deployment

## Related Documentation

- Feature spec: `.agent-os/specs/2025-10-01-instance-parameter-mapping/`
- Feature recap: `.agent-os/recaps/2025-10-01-instance-parameter-mapping.md`
- Troubleshooting: `CLAUDE.md` (lines 508-518)
