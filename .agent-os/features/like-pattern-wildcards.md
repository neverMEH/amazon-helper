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

## Related Commits
- `f020068` - Initial LIKE pattern auto-formatting
- `142f56f` - Fix: Auto-format LIKE pattern parameters with % wildcards
- `b273e4e` - Fix: Enhanced LIKE pattern detection to handle indirect parameter references