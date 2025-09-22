# Fix for VALUES Clause Column Mismatch Error

## Problem
The AMC API was rejecting SQL queries with the error:
```
From line 6, column 12 to line 6, column 17: Number of columns must match number of query columns
```

This occurred when executing workflows with ASIN parameters that needed to be injected into VALUES clauses.

## Root Cause
The `ParameterProcessor` class was incorrectly formatting array parameters for VALUES clauses. When it encountered an array parameter (like ASINs), it always used the IN clause format:

- **Wrong format (IN clause)**: `VALUES ('B001','B002','B003')` - Single row with multiple columns
- **Correct format (VALUES clause)**: `VALUES ('B001'), ('B002'), ('B003')` - Multiple rows with single column

The CTE definition `brand_asin (asin)` expects a single column, but the wrong format was creating multiple columns in a single row, causing the column count mismatch.

## Solution
Added context detection to determine when an array parameter is used in a VALUES clause vs an IN clause:

1. **New method `_is_values_parameter()`**: Detects if a parameter appears in a VALUES context
2. **New method `_format_values_parameter()`**: Formats arrays as separate rows for VALUES clauses
3. **Modified `_format_parameter_value()`**: Routes array formatting based on context

## Files Modified
- `/mnt/c/Users/Aeciu/Projects/amazon-helper-2/amc_manager/utils/parameter_processor.py`
  - Added VALUES context detection
  - Added proper VALUES clause formatting
  - Fixed datetime deprecation warnings in query_logger.py

## Tests Added
- `/mnt/c/Users/Aeciu/Projects/amazon-helper-2/tests/test_values_context_fix.py` - 10 test cases
- `/mnt/c/Users/Aeciu/Projects/amazon-helper-2/tests/test_workflow_values_clause.py` - 6 integration tests

## Example Fix
```sql
-- Before (WRONG):
WITH brand_asin (asin) AS (
    VALUES ('B001','B002','B003')  -- Single row, 3 columns
)

-- After (CORRECT):
WITH brand_asin (asin) AS (
    VALUES ('B001'), ('B002'), ('B003')  -- 3 rows, 1 column each
)
```

## Verification
All tests pass:
- ✅ VALUES clauses now format correctly with multiple rows
- ✅ IN clauses remain unchanged (single row format)
- ✅ Mixed contexts (VALUES and IN in same query) work correctly
- ✅ Empty arrays handled gracefully
- ✅ Special characters properly escaped
- ✅ Existing functionality preserved

## Impact
This fix ensures that:
1. AMC workflows with ASIN parameters execute successfully
2. Query templates using VALUES clauses work correctly
3. Large ASIN lists can be processed efficiently
4. The same parameter processor handles both VALUES and IN contexts appropriately