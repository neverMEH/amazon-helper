# Spec Requirements Document

> Spec: Instance Parameter Mapping
> Created: 2025-10-01

## Overview

Enable users to configure brand, ASIN, and campaign associations at the instance level through a management UI, allowing automatic population of query parameters when executing workflows based on the selected AMC instance. This eliminates repetitive parameter selection and ensures consistency across query executions.

## User Stories

### Instance Configuration Management
As an **AMC analyst**, I want to **configure which brands, ASINs, and campaigns are associated with each AMC instance**, so that **I don't have to manually select the same parameters every time I run a query**.

**Detailed Workflow:**
1. User navigates to an AMC instance detail page
2. User clicks on the "Mapping" tab (next to "Executions" tab)
3. User sees a brand-centric hierarchy interface with three sections:
   - **Brands**: List of available brands with checkboxes
   - **ASINs by Brand**: Nested view showing ASINs grouped under each selected brand
   - **Campaigns by Brand**: Nested view showing campaigns grouped under each selected brand
4. User selects brands to associate with the instance
5. For each selected brand, user sees associated ASINs and campaigns (automatically filtered by brand)
6. User can uncheck specific ASINs or campaigns they don't want included
7. System saves all mappings to the database
8. Mappings are shared across all users who have access to that instance

### Auto-Population During Query Execution
As an **AMC analyst**, I want **query parameters to auto-populate based on my selected instance**, so that **I can quickly execute queries with the correct scope without manual selection**.

**Detailed Workflow:**
1. User creates or edits a workflow/query template
2. User selects an AMC instance from the dropdown
3. System automatically detects parameters in the SQL query (e.g., `{{brand_list}}`, `{{asin_list}}`, `{{campaign_ids}}`)
4. System fetches the instance's configured mappings from the database
5. Parameter inputs are pre-filled with:
   - All brands mapped to the instance
   - All ASINs from those brands (excluding unchecked ones)
   - All campaigns from those brands (excluding unchecked ones)
6. User can see and modify the auto-populated values if needed
7. User executes the query with populated or overridden parameters

### Brand-Driven Campaign and ASIN Filtering
As an **AMC analyst**, I want **campaigns and ASINs to be organized by brand**, so that **I can easily manage which products and campaigns are in scope for each instance**.

**Detailed Workflow:**
1. User opens the Mapping tab on an instance detail page
2. User sees a hierarchical view with brands at the top level
3. When user selects a brand checkbox, the system:
   - Shows all campaigns that have that brand tag in `campaign_mappings.brand_tag`
   - Shows all ASINs that have that brand in `product_asins.brand`
4. User can expand/collapse brand sections to view ASINs and campaigns
5. Within each brand section:
   - **ASINs tab**: Shows filterable list with checkboxes (all checked by default)
   - **Campaigns tab**: Shows filterable list with checkboxes (all checked by default)
6. User unchecks specific items they want to exclude
7. System saves the inclusion/exclusion state per brand per instance
8. Only checked items are used for auto-population during query execution

## Spec Scope

1. **Mapping Management UI**: Create a "Mapping" tab on the instance detail page with a hierarchical brand → ASINs/campaigns interface for configuring instance associations.

2. **Database Schema Updates**: Add tables to store instance-level mappings including brand associations, ASIN inclusions/exclusions, and campaign inclusions/exclusions.

3. **Backend API Endpoints**: Implement REST APIs for fetching available brands/ASINs/campaigns, saving instance mappings, and retrieving mappings for auto-population.

4. **Brand Hierarchy Logic**: Build filtering logic that retrieves ASINs and campaigns based on selected brands, respecting user-defined inclusion/exclusion preferences.

5. **Auto-Population Integration**: Integrate mapping retrieval into the workflow execution flow to automatically populate query parameters when an instance is selected.

## Out of Scope

- User-specific overrides (all mappings are instance-level and shared)
- Historical tracking of mapping changes or audit logs
- Bulk import/export of mappings across instances
- Advanced campaign filtering beyond brand association (e.g., by campaign type, date range)
- ASIN validation or product data enrichment
- Brand configuration or brand creation (uses existing brands from `brand_configurations` and `campaign_mappings`)
- Migration of existing workflow parameters to instance mappings

## Expected Deliverable

1. **Instance Mapping UI**: Users can navigate to any instance detail page, click the "Mapping" tab, select brands, and configure ASINs/campaigns with a save button that persists to the database.

2. **Auto-Population in Query Execution**: When creating or editing a workflow and selecting an instance, parameter fields for brands, ASINs, and campaigns are automatically populated with the instance's configured mappings.

3. **Brand-Filtered ASIN/Campaign Lists**: In the Mapping tab, selecting a brand dynamically shows only the ASINs and campaigns associated with that brand, with checkboxes to include/exclude specific items.
