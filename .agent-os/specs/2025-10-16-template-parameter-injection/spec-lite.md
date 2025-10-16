# Instance Template Parameter Auto-Population - Lite Summary

Enhance Instance Template Editor with automatic parameter detection and auto-population from instance mappings. When users write SQL with parameters like `{{asin}}` or `{{campaign_id}}`, the system detects them, auto-fills ASIN/campaign values from mappings, allows manual entry for other types, shows live SQL preview with substituted values, and saves complete queries ready for immediate execution.

## Key Points
- **Auto-Detection**: Detects parameters from SQL (supports `{{param}}`, `:param`, `$param` formats)
- **Smart Auto-Fill**: ASIN/campaign parameters auto-populate from instance mappings; dates/custom remain manual
- **Live Preview**: Monaco Editor shows final SQL with substituted values (300ms debounced updates)
- **Save Complete SQL**: Templates store fully parameterized queries in `instance_templates.sql_query` (no API changes)
- **Reuse Existing**: Leverages ParameterDetector, parameterAutoPopulator, ParameterSelectorList, and useInstanceMappings from WorkflowParameterEditor
- **Zero Backend Changes**: Frontend-only feature using existing database schema and API endpoints
- **50% Time Savings**: Eliminates manual copy-paste for large parameter lists (50+ ASINs)
