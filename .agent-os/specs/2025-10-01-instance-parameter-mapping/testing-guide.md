# Instance Parameter Mapping - Testing Guide

## Quick Start

### Start the Services

```bash
# Option 1: Use the start script (recommended)
./start_services.sh

# Option 2: Start manually
# Terminal 1 - Backend
python main_supabase.py  # or python3 on Mac/Linux

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Testing Tools Available

### 1. Manual UI Testing (Recommended First)

1. **Navigate to Mappings Tab:**
   - Go to http://localhost:5173
   - Click on any instance
   - Click the "Mappings" tab

2. **Test the Flow:**
   - Select a brand from the left column
   - Check some ASINs in the middle column
   - Check some campaigns in the right column
   - Click "Save Changes"
   - Open browser console (F12) to see debug logs

3. **What to Look For:**
   - Console shows: `Saving instance mappings: { brands: [...], asins_by_brand: {...}, ... }`
   - Success message appears (green box): "Instance mappings saved successfully"
   - OR error message (red box) with specific details

### 2. Debug HTML Tool (For API-Level Testing)

**File:** `frontend/debug-mapping.html`

**How to Use:**
1. Open the file in a browser: `file:///path/to/frontend/debug-mapping.html`
2. Fill in configuration:
   - API Base URL: `http://localhost:8001/api` (default)
   - Instance ID: Get from URL when viewing an instance
   - Auth Token: Get from browser console: `localStorage.getItem('token')`
3. Click buttons in order:
   - "Get Available Brands" → See all brands
   - "Get Current Mappings" → See what's saved
   - "Get Brand ASINs" → See ASINs for a brand
   - "Get Brand Campaigns" → See campaigns for a brand
   - "Test Save Mappings" → Test saving

**Benefits:**
- Test API directly without UI complications
- See exact request/response payloads
- Isolate backend vs frontend issues

### 3. Python Test Script (For Backend API Testing)

**File:** `scripts/test_instance_mappings.py`

**Setup:**
```python
# Edit the script and set:
AUTH_TOKEN = "your-jwt-token-here"  # From localStorage
INSTANCE_ID = "your-instance-uuid-here"  # From instance URL
```

**Run:**
```bash
python scripts/test_instance_mappings.py
```

**Output:**
- Tests all 6 mapping endpoints in sequence
- Shows request/response for each
- Auto-stores data for dependent tests
- Reports any errors

### 4. Playwright E2E Tests (For Full Flow Testing)

**File:** `frontend/tests/e2e/instance-mapping-debug.spec.ts`

**Prerequisites:**
- Services must be running
- Database must have test data

**Run:**
```bash
cd frontend

# Headed mode (see what's happening)
npx playwright test tests/e2e/instance-mapping-debug.spec.ts --headed

# Debug mode (step through)
npx playwright test tests/e2e/instance-mapping-debug.spec.ts --debug

# Specific test
npx playwright test tests/e2e/instance-mapping-debug.spec.ts --grep "save button"
```

**Tests Include:**
- Brand loading and selection
- ASIN checkbox selection
- Campaign checkbox selection
- Save button network monitoring
- Blank page detection
- API endpoint inspection

## Common Issues & Solutions

### Issue 1: "Failed to save mappings"

**Debug Steps:**
1. Open browser console (F12)
2. Look for console.log showing the payload
3. Check the error message details
4. Common causes:
   - Invalid ASIN format (must be B + 9 alphanumeric)
   - Invalid campaign ID (must be numeric or promotion ID)
   - Network error (check backend is running)
   - Auth error (token expired - re-login)

### Issue 2: Blank Page After Save

**Debug Steps:**
1. Check browser console for errors
2. Check Network tab for failed requests
3. Look for React error boundaries
4. Try refreshing the page
5. Check if navigation occurred unexpectedly

**Playwright Test:**
```bash
# Run the blank page detection test
npx playwright test tests/e2e/instance-mapping-debug.spec.ts --grep "blank page"
```

### Issue 3: Selections Not Persisting

**Possible Causes:**
- useEffect not re-running when mappings change
- State not updating correctly
- API save succeeded but UI didn't refresh

**Debug:**
1. Check console for "Saving instance mappings:" log
2. Check response shows success: true
3. Check query invalidation is working
4. Try hard refresh (Ctrl+Shift+R)

## Validation Rules

### ASINs
- Format: `B` followed by 9 alphanumeric characters
- Examples: `B08N5WRWNW`, `B07FZ8S74R`
- Case insensitive (now fixed!)

### Campaign IDs
- Must be positive integer OR
- Numeric string (BIGINT) OR
- Promotion ID: `coupon-*`, `promo-*`, `percentageoff-*`, etc.
- Note: Promotion IDs are excluded from selections

### Brands
- Can be any non-empty string
- Derived from campaigns or product_asins tables
- No longer requires at least one brand (can save empty)

## Debugging Checklist

- [ ] Backend running on port 8001
- [ ] Frontend running on port 5173
- [ ] Logged in with valid session
- [ ] Instance ID is correct
- [ ] Browser console shows no errors
- [ ] Network tab shows successful API calls
- [ ] Auth token is valid (not expired)
- [ ] Database has brands/ASINs/campaigns data

## Files to Check

### Backend Logs
- `main_supabase.py` - Look for startup errors
- Check terminal where backend is running
- Look for validation errors in API logs

### Frontend Console
- Check for console.log("Saving instance mappings: ...")
- Check for red error messages
- Look for network errors

### Database
```sql
-- Check if data exists
SELECT * FROM instance_brands WHERE instance_id = 'your-instance-id';
SELECT * FROM instance_brand_asins WHERE instance_id = 'your-instance-id';
SELECT * FROM instance_brand_campaigns WHERE instance_id = 'your-instance-id';

-- Check brands available
SELECT DISTINCT brand FROM campaigns WHERE brand IS NOT NULL;
SELECT DISTINCT brand FROM product_asins WHERE brand IS NOT NULL AND active = true;
```

## Next Steps After Testing

1. **If Save Works:**
   - Verify data in database
   - Test auto-population in workflow editor
   - Test with multiple brands
   - Test clearing all mappings

2. **If Save Fails:**
   - Copy error message
   - Check validation rules above
   - Try debug HTML tool to isolate issue
   - Run Python test script for API verification

3. **If Blank Page Occurs:**
   - Run Playwright blank page test
   - Check browser console immediately
   - Check network tab for errors
   - Report findings with console output

## Getting Help

Include in bug report:
1. Browser console output
2. Network tab for failed request
3. Exact error message
4. Payload that was sent (from console.log)
5. Steps to reproduce
6. Backend terminal output

## Test Data Setup

If you need test data:

```sql
-- Insert test brand
INSERT INTO campaigns (campaign_id, campaign_name, brand, campaign_type, state)
VALUES (12345, 'Test Campaign', 'TestBrand', 'SP', 'enabled');

-- Insert test ASIN
INSERT INTO product_asins (asin, title, brand, active)
VALUES ('B08N5WRWNW', 'Test Product', 'TestBrand', true);
```
