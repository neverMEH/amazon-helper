# LIKE Pattern Wildcard Auto-Formatting Feature

## Overview
Implemented automatic wildcard (`%`) wrapping for SQL parameters used in LIKE clauses to enable pattern matching without requiring users to manually add wildcards.

## Problem Solved
When using query templates with LIKE clauses (e.g., `WHERE campaign LIKE {{campaign_pattern}}`), users had to manually enter wildcards (`%supergoop%`) for pattern matching to work. This was error-prone and not intuitive.

## Solution Implemented

### Backend Changes (`amc_manager/services/amc_execution_service.py`)

#### Detection Logic
The system now automatically detects when a parameter should be formatted with wildcards through multiple methods:

1. **Parameter Name Analysis**: Checks if parameter name contains "pattern" or "like"
2. **Direct LIKE Context**: Detects `LIKE {{param}}` patterns
3. **Indirect LIKE Context**: Detects parameters within 50 characters of LIKE keyword (handles `s.campaign LIKE {{campaign_brand}}`)
4. **Multiple Format Support**: Works with `{{param}}`, `:param`, and `$param` formats

#### Code Implementation
```python
# Check multiple conditions for LIKE pattern detection
param_lower = param.lower()
is_pattern_param = 'pattern' in param_lower or 'like' in param_lower

# Various regex patterns to detect LIKE context
like_pattern = rf'\bLIKE\s+[\'"]?\s*\{{\{{{param}\}}\}}'
like_colon = rf'\bLIKE\s+[\'"]?\s*:{param}\b'
like_dollar = rf'\bLIKE\s+[\'"]?\s*\${param}\b'
like_anywhere = rf'\bLIKE\s+.{{0,50}}\{{\{{{param}\}}\}}'

# Apply wildcards if any condition matches
if (matches_any_pattern or is_pattern_param):
    value_str = f"'%{value_escaped}%'"
```

### Frontend Changes

#### Query Configuration (`QueryConfigurationStep.tsx`)
- Pattern parameters excluded from campaign selector modal
- Show as text inputs with helpful placeholder
- Display preview: "Will be formatted as: %value%"

#### SQL Preview (`QueryReviewStep.tsx`)
- Detects pattern parameters and LIKE context
- Shows wildcards in SQL preview
- Handles both direct and indirect LIKE usage

## User Experience

### Before
- User enters: `supergoop`
- SQL executed: `WHERE campaign LIKE 'supergoop'` ❌ (no matches)

### After
- User enters: `supergoop`
- Preview shows: "Will be formatted as: %supergoop%"
- SQL executed: `WHERE campaign LIKE '%supergoop%'` ✅ (pattern matching works)

## Technical Details

### Pattern Detection Regex Patterns
- **Direct**: `\bLIKE\s+[\'"]?\s*\{\{param\}\}`
- **Indirect**: `\bLIKE\s+.{0,50}\{\{param\}\}` (within 50 chars)
- **Colon format**: `\bLIKE\s+[\'"]?\s*:param\b`
- **Dollar format**: `\bLIKE\s+[\'"]?\s*\$param\b`

### Parameter Name Heuristics
Automatically applies wildcards to parameters containing:
- "pattern" (e.g., `campaign_pattern`, `brand_pattern`)
- "like" (e.g., `like_value`, `campaign_like`)

### Debug Logging
Enhanced logging shows:
- Parameter being checked
- SQL context snippet
- Which detection method matched
- Final formatted value

## Files Modified
- `/amc_manager/services/amc_execution_service.py` - Backend LIKE detection and wildcard formatting
- `/frontend/src/components/query-builder/QueryConfigurationStep.tsx` - UI parameter input handling
- `/frontend/src/components/query-builder/QueryReviewStep.tsx` - SQL preview generation

## Testing
Successfully tested with:
- Direct LIKE patterns: `WHERE campaign LIKE {{campaign_pattern}}`
- Indirect patterns: `WHERE s.campaign LIKE {{campaign_brand}}`
- Multiple parameter formats
- Various SQL formatting styles

## Recent Changes (2025-09-23)

### Enhanced LIKE Pattern Parameter Handling
Completed major improvements to LIKE pattern parameter handling for campaign filtering, addressing issues where users couldn't use pattern matching with campaign parameters.

**Problem Solved**: Campaign parameters with LIKE patterns were incorrectly treated as dropdown lists instead of text inputs, causing SQL errors due to improper quote and wildcard handling.

**Key Improvements**:

#### Frontend Parameter Detection Enhancement
- **UniversalParameterSelector**: Now properly shows pattern input with wildcard help for campaign parameters
- **Parameter Type Detection**: Enhanced to recognize LIKE context even with quotes and wildcards (e.g., `'%{{param}}%'`)
- **Context Prioritization**: Fixed sqlParameterAnalyzer to prioritize LIKE context over name-based classification
- **Campaign Parameter Handling**: Campaign parameters with LIKE now correctly show as 'pattern' type instead of 'campaign_list'

#### Frontend Parameter Formatting Improvements
- **Wildcard Detection**: Detects when wildcards are already present in SQL template
- **Double-Wrapping Prevention**: Prevents `'%'%value%'%'` errors by returning plain values when template has quotes/wildcards
- **Quote Management**: Proper handling of pre-quoted parameters in SQL templates

#### Backend Parameter Processing Enhancement
- **Template Pattern Detection**: Updated ParameterProcessor to detect `'%{{param}}%'` patterns in templates
- **Conditional Formatting**: When wildcards are already in template, returns escaped value without adding quotes
- **SQL Error Prevention**: Fixes "Column 'value' not found" errors due to missing quotes

**Example Use Case**: Users can now write queries like:
```sql
WHERE campaign LIKE '%{{campaign_pattern}}%'
```
When entering "Nike", it correctly generates: `WHERE campaign LIKE '%Nike%'`

**Files Modified Today**:
- `frontend/src/components/parameter-detection/UniversalParameterSelector.tsx`
- `frontend/src/utils/parameterDetection.ts`
- `frontend/src/utils/sqlParameterAnalyzer.ts`
- `amc_manager/utils/parameter_processor.py`

## Related Commits
- `f020068` - Initial LIKE pattern auto-formatting
- `142f56f` - Fix: Auto-format LIKE pattern parameters with % wildcards
- `b273e4e` - Fix: Enhanced LIKE pattern detection to handle indirect parameter references
- `8675cbf` - Fix: Improve LIKE pattern detection to handle quotes and wildcards (2025-09-23)
- `3241a47` - Fix: Handle LIKE patterns with wildcards already in SQL template (2025-09-23)
- `ac6eb91` - Fix: Backend handling of LIKE patterns with wildcards in template (2025-09-23)