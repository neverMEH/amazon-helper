# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-28-universal-parameter-selection/spec.md

> Created: 2025-08-28
> Version: 1.0.0

## Technical Requirements

### Parameter Detection Engine
- Implement regex pattern matching to identify parameter placeholders in SQL queries
- Support detection patterns for:
  - ASIN parameters: patterns like {{asin}}, {{asins}}, {{product_asin}}, :asin, $asin
  - Date parameters: patterns like {{start_date}}, {{end_date}}, {{date_from}}, :date_start, $date_range
  - Campaign parameters: patterns like {{campaign}}, {{campaign_id}}, {{campaigns}}, :campaign, $campaign_name
- Parse query on change and maintain parameter metadata including type, name, and position
- Handle multiple parameters of same type in single query

### Frontend Components

**ParameterDetector Component**
- Analyze SQL query text using regex patterns
- Return array of detected parameters with type classification
- Trigger re-detection on query text changes
- Cache detection results to prevent unnecessary re-processing

**UniversalParameterSelector Component**
- Container component that renders appropriate selector based on parameter type
- Props: parameterType, parameterName, instanceId, brandId, onChange
- Manages state for selected values
- Handles formatting of selected values for SQL substitution

**ASINSelector Component**
- Fetch ASINs from /api/asins endpoint filtered by brand_id
- Implement searchable multi-select dropdown using existing Select component pattern
- Display ASIN with product title for better identification
- Support selecting all ASINs option
- Format selected ASINs as comma-separated list for SQL IN clause

**DateRangeSelector Component**
- Preset options: Last 7 days, Last 14 days, Last 30 days, Custom
- Custom date picker using existing DatePicker component
- Calculate date ranges relative to current date for presets
- Format dates as YYYY-MM-DDTHH:MM:SS without timezone suffix
- Validate end date is after start date

**CampaignSelector Component**
- Fetch campaigns from /api/campaigns endpoint filtered by brand_id
- Searchable multi-select similar to ASINSelector
- Display campaign name and ID
- Support campaign type filtering if available
- Format for SQL parameter substitution

### Backend API Endpoints

**GET /api/workflows/{workflow_id}/parameters**
- Analyze workflow SQL and return detected parameters
- Response: Array of {name: string, type: 'asin' | 'date' | 'campaign', position: number}

**GET /api/asins**
- Query parameters: instance_id, brand_id, search (optional)
- Join asin_asins with instance_brands to filter by brand
- Return: {asin: string, product_title: string, brand_name: string}[]
- Implement pagination for large result sets

**GET /api/campaigns**
- Query parameters: instance_id, brand_id, search (optional), campaign_type (optional)
- Join campaigns with instance_brands to filter
- Return: {campaign_id: string, campaign_name: string, campaign_type: string}[]
- Include pagination support

### Database Schema Requirements
- Leverage existing tables: asin_asins, campaigns, instance_brands
- Ensure proper indexes on brand_id columns for performance
- Add compound indexes for (instance_id, brand_id) if not present

### Integration Points

**Workflow Execution Service**
- Modify parameter substitution to handle array values for multi-select parameters
- Ensure proper escaping for SQL injection prevention
- Validate all parameters have values before execution

**Workflow Form Component**
- Detect parameters when SQL query changes
- Render UniversalParameterSelector for each detected parameter
- Store parameter values in workflow metadata
- Pass parameter values to execution endpoint

### Performance Considerations
- Cache ASIN and campaign lists per brand to reduce API calls
- Implement debounced parameter detection on query typing
- Use React Query for data fetching with appropriate stale times
- Lazy load dropdown options with virtualization for large lists

### Error Handling
- Handle cases where no ASINs/campaigns exist for selected brand
- Provide clear error messages for invalid parameter formats
- Gracefully handle API failures with retry logic
- Show loading states during data fetching

### Security Considerations
- Validate parameter values server-side before query execution
- Prevent SQL injection through proper parameter substitution
- Ensure users can only access ASINs/campaigns for their authorized instances
- Rate limit API endpoints to prevent abuse