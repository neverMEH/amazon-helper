# Fix Summary: AMC Undeclared Parameter Error

## Issue
AMC API was rejecting workflow creation from templates with error:
```
Failed to create workflow: Status 400, Response: {'code': '400', 'details': 'Was unable to compile workflow wf_9fbfce61 because it was found to be invalid: Filter operation filter_operation referenced an undeclared parameter ad_product_type.'}
```

## Root Cause
When creating workflows from templates containing parameter placeholders like `{{ad_product_type}}`, the system was:

1. Processing and attempting to replace placeholders with default values
2. Setting `input_parameters = None` assuming all placeholders were replaced
3. BUT some placeholders remained unprocessed or AMC detected the pattern
4. AMC requires formal parameter declarations via `inputParameters` field when SQL contains any parameter placeholders

## Solution Implemented

### 1. Enhanced Parameter Detection (workflows.py)
Modified `/mnt/c/Users/Aeciu/Projects/amazon-helper-2/amc_manager/api/supabase/workflows.py` to:
- Check for remaining placeholders after parameter processing
- Generate proper `inputParameters` declarations for AMC when placeholders exist
- Include appropriate data types based on parameter names
- Provide default values where applicable

### 2. Improved Default Values (parameter_processor.py)
Modified `/mnt/c/Users/Aeciu/Projects/amazon-helper-2/amc_manager/utils/parameter_processor.py` to:
- Add specific handling for `ad_product_type` parameter
- Return valid AMC value `'sponsored_products'` instead of generic `'dummy_value'`
- Better type detection for common AMC parameters

## Key Changes

### workflows.py (lines 373-410)
```python
# Check if there are still any unprocessed placeholders in the SQL
remaining_placeholders = re.findall(param_pattern, sql_query)

if remaining_placeholders:
    # Create input parameter declarations for any remaining placeholders
    input_parameters = []
    for param_name in set(remaining_placeholders):
        # Determine parameter type based on name
        param_type = 'STRING'  # Default type
        # ... type detection logic ...

        input_parameters.append({
            'name': param_name,
            'dataType': param_type,
            'required': False,
            'defaultValue': params_to_use.get(param_name, '')
        })
else:
    input_parameters = None
```

### parameter_processor.py (lines 480-485)
```python
# Handle ad_product_type specifically - common AMC parameter
if param_name == 'ad_product_type' or 'product_type' in lower:
    return ['sponsored_products']  # Valid AMC ad product type
```

## Testing
Created comprehensive test suite (`test_template_workflow_fix.py`) that verifies:
- Proper default values for `ad_product_type`
- Placeholder detection in SQL templates
- Input parameter generation for AMC
- Partial parameter processing
- Complete workflow creation scenario

All tests pass successfully.

## Impact
- Workflows created from templates with parameters will no longer fail with "undeclared parameter" errors
- AMC will receive proper parameter declarations when needed
- Templates can use placeholders that get declared to AMC for runtime substitution
- Backward compatible - workflows without placeholders continue to work as before

## Files Modified
1. `/mnt/c/Users/Aeciu/Projects/amazon-helper-2/amc_manager/api/supabase/workflows.py`
2. `/mnt/c/Users/Aeciu/Projects/amazon-helper-2/amc_manager/utils/parameter_processor.py`

## Files Created
1. `/mnt/c/Users/Aeciu/Projects/amazon-helper-2/test_template_workflow_fix.py` (test suite)
2. `/mnt/c/Users/Aeciu/Projects/amazon-helper-2/FIX_SUMMARY_AMC_UNDECLARED_PARAMETER.md` (this document)

## Next Steps
1. Deploy the fix to the environment
2. Test with the actual template (`tpl_bff6eb8ded5c`) that was failing
3. Monitor for any other templates that might have similar issues
4. Consider adding validation in the template creation process to ensure parameter names follow AMC conventions