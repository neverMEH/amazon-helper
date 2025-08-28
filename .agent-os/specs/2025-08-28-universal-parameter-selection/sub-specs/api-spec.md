# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-28-universal-parameter-selection/spec.md

> Created: 2025-08-28
> Version: 1.0.0

## Endpoints

### GET /api/workflows/{workflow_id}/parameters

**Purpose:** Analyze workflow SQL query to detect and classify parameters
**Parameters:** 
- workflow_id (path): UUID of the workflow
**Response:** 
```json
{
  "parameters": [
    {
      "name": "start_date",
      "type": "date",
      "position": 1,
      "placeholder": "{{start_date}}"
    },
    {
      "name": "asins",
      "type": "asin",
      "position": 2,
      "placeholder": "{{asins}}"
    }
  ]
}
```
**Errors:** 
- 404: Workflow not found
- 401: Unauthorized

### GET /api/asins

**Purpose:** Retrieve ASINs filtered by instance and brand
**Parameters:**
- instance_id (query, required): UUID of the AMC instance
- brand_id (query, required): UUID of the brand
- search (query, optional): Search term for ASIN or product title
- limit (query, optional): Number of results (default: 100)
- offset (query, optional): Pagination offset
**Response:**
```json
{
  "asins": [
    {
      "asin": "B08XYZ123",
      "product_title": "Product Name",
      "brand_name": "Brand Name"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```
**Errors:**
- 400: Missing required parameters
- 401: Unauthorized
- 403: No access to instance/brand

### GET /api/campaigns

**Purpose:** Retrieve campaigns filtered by instance and brand
**Parameters:**
- instance_id (query, required): UUID of the AMC instance
- brand_id (query, required): UUID of the brand
- search (query, optional): Search term for campaign name
- campaign_type (query, optional): Filter by campaign type
- limit (query, optional): Number of results (default: 100)
- offset (query, optional): Pagination offset
**Response:**
```json
{
  "campaigns": [
    {
      "campaign_id": "12345",
      "campaign_name": "Holiday Campaign 2024",
      "campaign_type": "sponsored_products",
      "status": "enabled"
    }
  ],
  "total": 250,
  "limit": 100,
  "offset": 0
}
```
**Errors:**
- 400: Missing required parameters
- 401: Unauthorized
- 403: No access to instance/brand

### POST /api/workflows/{workflow_id}/validate-parameters

**Purpose:** Validate that all detected parameters have values before execution
**Parameters:**
- workflow_id (path): UUID of the workflow
**Request Body:**
```json
{
  "parameters": {
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T00:00:00",
    "asins": ["B08XYZ123", "B08XYZ456"],
    "campaign_ids": ["12345", "67890"]
  }
}
```
**Response:**
```json
{
  "valid": true,
  "errors": [],
  "formatted_parameters": {
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T00:00:00",
    "asins": "'B08XYZ123','B08XYZ456'",
    "campaign_ids": "'12345','67890'"
  }
}
```
**Errors:**
- 400: Invalid parameter values
- 404: Workflow not found
- 422: Validation errors

## Controllers

### WorkflowParameterController

**Location:** `amc_manager/api/workflow_parameters.py`
**Purpose:** Handle parameter detection and validation for workflows
**Methods:**
- `analyze_parameters()`: Parse SQL query to detect parameter placeholders
- `validate_parameters()`: Validate parameter values before execution
- `format_parameters()`: Convert parameter values to SQL-ready format

### AsinController

**Location:** `amc_manager/api/asins.py`
**Purpose:** Handle ASIN data retrieval and filtering
**Methods:**
- `list_asins()`: Retrieve filtered ASIN list with pagination
- `search_asins()`: Search ASINs by product title or ASIN
- `get_asin_details()`: Retrieve detailed information for specific ASINs

### CampaignController

**Location:** `amc_manager/api/campaigns.py`
**Purpose:** Handle campaign data retrieval and filtering
**Methods:**
- `list_campaigns()`: Retrieve filtered campaign list with pagination
- `search_campaigns()`: Search campaigns by name or ID
- `get_campaign_details()`: Retrieve detailed information for specific campaigns