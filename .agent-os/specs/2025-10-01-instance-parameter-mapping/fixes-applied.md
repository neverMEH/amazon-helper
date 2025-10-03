# Instance Parameter Mapping - Fixes Applied

## Date: 2025-10-03

## Issues Identified and Fixed

### 1. **Frontend: Incorrect Hook Usage**
**File:** `frontend/src/components/instances/InstanceMappingTab.tsx`
**Issue:** Line 46 used `useState()` instead of `useEffect()` to initialize selections from mappings
**Fix:** Changed to `useEffect()` with proper dependency array `[mappings]`
**Impact:** Selections now properly initialize when mappings data is loaded

### 2. **Frontend: Missing useEffect Import**
**File:** `frontend/src/components/instances/InstanceMappingTab.tsx`
**Issue:** `useEffect` was not imported from React
**Fix:** Added `useEffect` to React imports
**Impact:** Component now compiles without errors

### 3. **Backend: Overly Strict Brand Validation**
**File:** `amc_manager/services/instance_mapping_service.py:357-361`
**Issue:** Required at least one brand to be provided, preventing users from clearing mappings
**Fix:** Removed the strict validation, allowing empty mappings
**Impact:** Users can now save empty mappings to clear all associations

### 4. **Backend: Case-Sensitive ASIN Validation**
**File:** `amc_manager/schemas/instance_mapping.py:42`
**Issue:** ASIN regex pattern was case-sensitive, requiring uppercase but not handling lowercase input
**Fix:** Added `re.IGNORECASE` flag to regex pattern
**Impact:** ASINs in any case (upper/lower/mixed) are now accepted

### 5. **Frontend: Poor Error Message Display**
**File:** `frontend/src/components/instances/InstanceMappingTab.tsx:102-125`
**Issue:** Error messages only showed generic text, not the actual API validation errors
**Fix:** Enhanced error handling to:
  - Show detailed error messages from API
  - Parse Pydantic validation errors
  - Display field-level error information
  - Extended error display time to 8 seconds
**Impact:** Users now see specific error messages explaining what went wrong

### 6. **Frontend: Missing Debug Logging**
**File:** `frontend/src/components/instances/InstanceMappingTab.tsx:97`
**Issue:** No visibility into what data was being sent to API
**Fix:** Added console.log for payload before API call
**Impact:** Developers can now debug save operations in browser console

## Testing Tools Created

### 1. **Debug HTML Tool**
**File:** `frontend/debug-mapping.html`
**Purpose:** Standalone HTML page to test mapping API endpoints directly
**Features:**
  - Test all 5 mapping endpoints independently
  - View request/response payloads
  - Debug authentication issues
  - Manual endpoint testing

### 2. **Playwright E2E Test Suite**
**File:** `frontend/tests/e2e/instance-mapping-debug.spec.ts`
**Purpose:** Automated testing of mapping functionality
**Coverage:**
  - Brand loading and selection
  - ASIN selection
  - Campaign selection
  - Save operation with network monitoring
  - Blank page detection
  - API endpoint inspection

## Remaining Potential Issues to Monitor

### 1. **Empty Brands Scenario**
**Current Behavior:** If user selects ASINs/campaigns but the frontend doesn't build the brands array correctly, it will send empty brands array
**Potential Issue:** Line 89 builds brands from selections - if this logic fails, save will work but might not associate items correctly
**Mitigation:** Frontend logging now shows exactly what's being sent

### 2. **Campaign ID Type Handling**
**Current Behavior:** Campaign IDs can be string or number (BIGINT from database)
**Potential Issue:** Type inconsistencies between frontend Sets and backend validation
**Mitigation:** Backend accepts both int and str, frontend uses `string | number` union type

### 3. **Blank Page Issue**
**Root Cause:** Not yet identified - may be related to:
  - Network errors causing unhandled promise rejections
  - React error boundaries not catching errors
  - Navigation triggered unexpectedly
**Next Steps:** Use Playwright test to reproduce and identify

## How to Test the Fixes

### Using the Debug Tool
1. Start backend: `python main_supabase.py` (or `python3` on non-Windows)
2. Open `frontend/debug-mapping.html` in browser
3. Enter your instance ID and auth token
4. Click through the test buttons in order:
   - Get Available Brands
   - Get Current Mappings
   - Get Brand ASINs
   - Get Brand Campaigns
   - Test Save Mappings
5. Review results for any errors

### Using the UI
1. Start both services: `./start_services.sh`
2. Navigate to instance detail page
3. Click "Mappings" tab
4. Select a brand
5. Check some ASINs and/or campaigns
6. Click "Save Changes"
7. Open browser console (F12) to see:
   - Payload being sent
   - Any errors
   - Success/error messages

### Using Playwright (if services running)
```bash
cd frontend
npx playwright test tests/e2e/instance-mapping-debug.spec.ts --headed
```

## Code Review Checklist

- [x] Fixed useState → useEffect
- [x] Added useEffect import
- [x] Removed strict brand validation
- [x] Made ASIN validation case-insensitive
- [x] Enhanced error message display
- [x] Added debug logging
- [x] Created debug tools
- [ ] Verify routes are accessible
- [ ] Test with real data
- [ ] Confirm blank page issue is resolved

## Next Steps

1. **Start Services:** Use correct Python command for your system
2. **Manual Testing:** Test save operation with various combinations:
   - Only ASINs selected
   - Only campaigns selected
   - Both selected
   - Clear all (empty save)
3. **Monitor Console:** Check for:
   - Payload structure
   - API responses
   - Any client-side errors
4. **Identify Blank Page:** If still occurs, use browser network tab to see what request/response caused it

## Files Modified

1. `frontend/src/components/instances/InstanceMappingTab.tsx` (4 changes)
2. `amc_manager/schemas/instance_mapping.py` (1 change)
3. `amc_manager/services/instance_mapping_service.py` (1 change)

## Files Created

1. `frontend/debug-mapping.html` (debug tool)
2. `frontend/tests/e2e/instance-mapping-debug.spec.ts` (test suite)
3. `.agent-os/specs/2025-10-01-instance-parameter-mapping/fixes-applied.md` (this document)
