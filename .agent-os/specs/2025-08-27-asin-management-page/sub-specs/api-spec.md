# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-27-asin-management-page/spec.md

## Endpoints

### GET /api/asins/

**Purpose:** List all ASINs with pagination and filtering
**Parameters:**
- `page` (int, optional): Page number, default 1
- `page_size` (int, optional): Items per page, default 100, max 1000
- `brand` (string, optional): Filter by brand name
- `marketplace` (string, optional): Filter by marketplace ID
- `search` (string, optional): Search in ASIN and title fields
- `active` (boolean, optional): Filter by active status, default true

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "asin": "B0FN64FK6R",
      "title": "Product Title",
      "brand": "Brand Name",
      "marketplace": "ATVPDKIKX0DER",
      "last_known_price": 29.99,
      "monthly_estimated_units": 150,
      "active": true,
      "updated_at": "2025-08-27T10:00:00Z"
    }
  ],
  "total": 5000,
  "page": 1,
  "page_size": 100,
  "pages": 50
}
```

**Errors:** 
- 400: Invalid pagination parameters
- 401: Unauthorized

### GET /api/asins/{asin_id}

**Purpose:** Get detailed information for a specific ASIN
**Parameters:** None

**Response:**
```json
{
  "id": "uuid",
  "asin": "B0FN64FK6R",
  "title": "Product Title",
  "brand": "Brand Name",
  "marketplace": "ATVPDKIKX0DER",
  "description": "Product description",
  "department": "Home & Kitchen",
  "manufacturer": "Manufacturer Name",
  "product_group": "Kitchen",
  "product_type": "Storage",
  "color": "Clear",
  "size": "Large",
  "model": "Model123",
  "item_dimensions": {
    "length": 10.5,
    "height": 5.0,
    "width": 8.0,
    "weight": 1.5,
    "unit_dimension": "inches",
    "unit_weight": "pounds"
  },
  "parent_asin": null,
  "variant_type": null,
  "last_known_price": 29.99,
  "monthly_estimated_sales": 4500.00,
  "monthly_estimated_units": 150,
  "created_at": "2025-08-01T10:00:00Z",
  "updated_at": "2025-08-27T10:00:00Z",
  "last_imported_at": "2025-08-27T09:00:00Z"
}
```

**Errors:**
- 404: ASIN not found
- 401: Unauthorized

### POST /api/asins/import

**Purpose:** Bulk import ASINs from CSV file
**Parameters:** 
- `file` (multipart/form-data): CSV file with ASIN data
- `update_existing` (boolean, optional): Update existing ASINs, default true

**Request Headers:**
- `Content-Type: multipart/form-data`

**Response:**
```json
{
  "import_id": "uuid",
  "status": "processing",
  "total_rows": 1000,
  "message": "Import started successfully"
}
```

**Errors:**
- 400: Invalid file format or missing required columns
- 413: File too large (max 50MB)
- 401: Unauthorized

### GET /api/asins/import/{import_id}

**Purpose:** Check status of bulk import operation
**Parameters:** None

**Response:**
```json
{
  "id": "uuid",
  "status": "completed",
  "total_rows": 1000,
  "successful_imports": 950,
  "failed_imports": 10,
  "duplicate_skipped": 40,
  "started_at": "2025-08-27T10:00:00Z",
  "completed_at": "2025-08-27T10:01:30Z",
  "error_details": [
    {
      "row": 15,
      "error": "Invalid ASIN format"
    }
  ]
}
```

**Errors:**
- 404: Import not found
- 401: Unauthorized

### GET /api/asins/brands

**Purpose:** Get list of unique brands for filtering
**Parameters:** 
- `search` (string, optional): Filter brands by search term

**Response:**
```json
{
  "brands": [
    "Brand A",
    "Brand B",
    "Brand C"
  ],
  "total": 150
}
```

**Errors:**
- 401: Unauthorized

### POST /api/asins/search

**Purpose:** Search ASINs for parameter selection in query builder
**Parameters:**
```json
{
  "asin_ids": ["B0FN64FK6R", "B0FN51YPBH"],
  "brands": ["Brand A"],
  "search": "storage",
  "limit": 100
}
```

**Response:**
```json
{
  "asins": [
    {
      "asin": "B0FN64FK6R",
      "title": "Product Title",
      "brand": "Brand A"
    }
  ],
  "total": 25
}
```

**Errors:**
- 400: Invalid search parameters
- 401: Unauthorized

## Controllers

### ASINController

**Actions:**
- `list_asins()`: Paginated listing with filters
- `get_asin()`: Retrieve single ASIN details
- `import_asins()`: Handle CSV file upload and parsing
- `check_import_status()`: Monitor import progress
- `get_brands()`: Fetch unique brand list
- `search_asins()`: Advanced search for query builder

**Business Logic:**
- Validate CSV structure before import
- Handle duplicates with upsert logic
- Sanitize and normalize brand names
- Maintain import audit trail
- Cache frequently accessed brands

**Error Handling:**
- Return detailed validation errors for imports
- Log failed rows with specific error messages
- Implement retry logic for database operations
- Handle large file uploads gracefully

## Integration with Query Builder

### Parameter Population Flow

1. User clicks "Select ASINs" in QueryConfigurationStep
2. Modal opens with ASIN selector component
3. User filters/searches and selects ASINs
4. Selected ASINs returned via callback
5. ASINs formatted and inserted into parameter field

### Parameter Format

```json
{
  "asin_list": ["B0FN64FK6R", "B0FN51YPBH", "B0FN5F4T37"],
  "asin_list_formatted": "'B0FN64FK6R','B0FN51YPBH','B0FN5F4T37'"
}
```

## Rate Limiting

- Import endpoint: 10 requests per hour per user
- List endpoint: 100 requests per minute
- Search endpoint: 200 requests per minute