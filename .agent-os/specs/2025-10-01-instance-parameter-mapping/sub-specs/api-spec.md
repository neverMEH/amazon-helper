# API Specification - Instance Parameter Mapping

## Overview

This specification defines the REST API endpoints for managing instance-level parameter mappings and retrieving them for auto-population during query execution.

## Base URL

All endpoints are prefixed with `/api/instances/{instance_id}/`

## Authentication

All endpoints require authentication via JWT token in the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### 1. Get Available Brands

**Endpoint**: `GET /api/instances/{instance_id}/available-brands`

**Description**: Fetch all brands available to the user for selection

**Path Parameters**:
- `instance_id` (UUID, required): The instance ID

**Query Parameters**: None

**Response** (200 OK):
```json
{
  "brands": [
    {
      "brand_tag": "acme",
      "brand_name": "Acme Products",
      "source": "configuration",
      "asin_count": 45,
      "campaign_count": 12
    },
    {
      "brand_tag": "globex",
      "brand_name": "Globex Corporation",
      "source": "campaign",
      "asin_count": 78,
      "campaign_count": 23
    }
  ]
}
```

**Error Responses**:
- `404`: Instance not found
- `403`: User does not have access to this instance
- `401`: Unauthorized (missing or invalid token)

**Backend Implementation**:
```python
@router.get("/{instance_id}/available-brands")
async def get_available_brands(
    instance_id: str,
    current_user: User = Depends(get_current_user)
):
    """Fetch all brands available to user"""
    service = InstanceMappingService()
    brands = await service.get_available_brands(instance_id, current_user.id)
    return {"brands": brands}
```

---

### 2. Get Brand ASINs

**Endpoint**: `GET /api/instances/{instance_id}/brands/{brand_tag}/asins`

**Description**: Fetch all ASINs associated with a specific brand

**Path Parameters**:
- `instance_id` (UUID, required): The instance ID
- `brand_tag` (string, required): The brand tag identifier

**Query Parameters**:
- `search` (string, optional): Search filter for ASIN or title
- `limit` (integer, optional): Maximum number of results (default: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "brand_tag": "acme",
  "asins": [
    {
      "asin": "B08N5WRWNW",
      "title": "Acme Premium Widget",
      "brand": "Acme Products",
      "image_url": "https://example.com/image.jpg",
      "price": 29.99,
      "active": true
    },
    {
      "asin": "B07FZ8S74R",
      "title": "Acme Deluxe Gadget",
      "brand": "Acme Products",
      "image_url": "https://example.com/image2.jpg",
      "price": 49.99,
      "active": true
    }
  ],
  "total": 45,
  "limit": 100,
  "offset": 0
}
```

**Error Responses**:
- `404`: Instance or brand not found
- `403`: User does not have access to this instance
- `401`: Unauthorized

**Backend Implementation**:
```python
@router.get("/{instance_id}/brands/{brand_tag}/asins")
async def get_brand_asins(
    instance_id: str,
    brand_tag: str,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Fetch ASINs for a specific brand"""
    service = InstanceMappingService()
    result = await service.get_brand_asins(
        instance_id=instance_id,
        brand_tag=brand_tag,
        user_id=current_user.id,
        search=search,
        limit=limit,
        offset=offset
    )
    return result
```

---

### 3. Get Brand Campaigns

**Endpoint**: `GET /api/instances/{instance_id}/brands/{brand_tag}/campaigns`

**Description**: Fetch all campaigns associated with a specific brand

**Path Parameters**:
- `instance_id` (UUID, required): The instance ID
- `brand_tag` (string, required): The brand tag identifier

**Query Parameters**:
- `search` (string, optional): Search filter for campaign name
- `campaign_type` (string, optional): Filter by campaign type (SP, SB, SD, DSP)
- `limit` (integer, optional): Maximum number of results (default: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "brand_tag": "acme",
  "campaigns": [
    {
      "campaign_id": 12345678901,
      "campaign_name": "Acme - Sponsored Products - Brand Defense",
      "campaign_type": "SP",
      "marketplace_id": "ATVPDKIKX0DER",
      "profile_id": "1234567890",
      "status": "active",
      "created_at": "2025-01-15T10:30:00Z"
    },
    {
      "campaign_id": 98765432109,
      "campaign_name": "Acme - Sponsored Brand - Category Expansion",
      "campaign_type": "SB",
      "marketplace_id": "ATVPDKIKX0DER",
      "profile_id": "1234567890",
      "status": "active",
      "created_at": "2025-02-20T14:15:00Z"
    }
  ],
  "total": 12,
  "limit": 100,
  "offset": 0
}
```

**Error Responses**:
- `404`: Instance or brand not found
- `403`: User does not have access to this instance
- `401`: Unauthorized

**Backend Implementation**:
```python
@router.get("/{instance_id}/brands/{brand_tag}/campaigns")
async def get_brand_campaigns(
    instance_id: str,
    brand_tag: str,
    search: Optional[str] = None,
    campaign_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Fetch campaigns for a specific brand"""
    service = InstanceMappingService()
    result = await service.get_brand_campaigns(
        instance_id=instance_id,
        brand_tag=brand_tag,
        user_id=current_user.id,
        search=search,
        campaign_type=campaign_type,
        limit=limit,
        offset=offset
    )
    return result
```

---

### 4. Get Instance Mappings

**Endpoint**: `GET /api/instances/{instance_id}/mappings`

**Description**: Retrieve current parameter mappings for an instance

**Path Parameters**:
- `instance_id` (UUID, required): The instance ID

**Query Parameters**: None

**Response** (200 OK):
```json
{
  "instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "brands": ["acme", "globex"],
  "asins_by_brand": {
    "acme": ["B08N5WRWNW", "B07FZ8S74R", "B09KMVNY9J"],
    "globex": ["B08X1Q2B9T", "B07H8QWXYZ"]
  },
  "campaigns_by_brand": {
    "acme": [12345678901, 98765432109],
    "globex": [11111111111, 22222222222, 33333333333]
  },
  "updated_at": "2025-10-01T15:30:00Z"
}
```

**Empty State Response** (when no mappings configured):
```json
{
  "instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "brands": [],
  "asins_by_brand": {},
  "campaigns_by_brand": {},
  "updated_at": null
}
```

**Error Responses**:
- `404`: Instance not found
- `403`: User does not have access to this instance
- `401`: Unauthorized

**Backend Implementation**:
```python
@router.get("/{instance_id}/mappings")
async def get_instance_mappings(
    instance_id: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieve current mappings for instance"""
    service = InstanceMappingService()
    mappings = await service.get_instance_mappings(instance_id, current_user.id)
    return mappings
```

---

### 5. Save Instance Mappings

**Endpoint**: `POST /api/instances/{instance_id}/mappings`

**Description**: Save or update parameter mappings for an instance

**Path Parameters**:
- `instance_id` (UUID, required): The instance ID

**Request Body**:
```json
{
  "brands": ["acme", "globex"],
  "asins_by_brand": {
    "acme": ["B08N5WRWNW", "B07FZ8S74R", "B09KMVNY9J"],
    "globex": ["B08X1Q2B9T", "B07H8QWXYZ"]
  },
  "campaigns_by_brand": {
    "acme": [12345678901, 98765432109],
    "globex": [11111111111, 22222222222, 33333333333]
  }
}
```

**Validation Rules**:
- At least one brand must be provided
- ASINs and campaigns must correspond to provided brands
- ASINs must be valid format (B[0-9A-Z]{9})
- Campaign IDs must be valid integers

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Instance mappings saved successfully",
  "instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "stats": {
    "brands_saved": 2,
    "asins_saved": 5,
    "campaigns_saved": 5
  },
  "updated_at": "2025-10-01T15:35:00Z"
}
```

**Error Responses**:
- `400`: Validation error (e.g., no brands provided, invalid ASIN format)
  ```json
  {
    "error": "Validation failed",
    "details": {
      "brands": ["At least one brand must be provided"],
      "asins_by_brand.acme": ["Invalid ASIN format: XYZ123"]
    }
  }
  ```
- `404`: Instance not found
- `403`: User does not have access to this instance
- `401`: Unauthorized
- `500`: Server error (e.g., database transaction failed)

**Backend Implementation**:
```python
@router.post("/{instance_id}/mappings")
async def save_instance_mappings(
    instance_id: str,
    mappings: InstanceMappingsInput,
    current_user: User = Depends(get_current_user)
):
    """Save instance mappings"""
    # Validate input
    if not mappings.brands:
        raise HTTPException(status_code=400, detail="At least one brand must be provided")

    service = InstanceMappingService()

    try:
        result = await service.save_instance_mappings(
            instance_id=instance_id,
            user_id=current_user.id,
            mappings=mappings.dict()
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to save instance mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save mappings")
```

---

### 6. Get Parameter Values for Auto-Population

**Endpoint**: `GET /api/instances/{instance_id}/parameter-values`

**Description**: Get formatted parameter values for query auto-population

**Path Parameters**:
- `instance_id` (UUID, required): The instance ID

**Query Parameters**: None

**Response** (200 OK):
```json
{
  "instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "parameters": {
    "brand_list": "acme,globex",
    "asin_list": "B08N5WRWNW,B07FZ8S74R,B09KMVNY9J,B08X1Q2B9T,B07H8QWXYZ",
    "campaign_ids": "12345678901,98765432109,11111111111,22222222222,33333333333",
    "campaign_names": "Acme - SP - Brand Defense,Acme - SB - Category,Globex - DSP - Awareness,Globex - SP - Product Launch,Globex - SB - Competitor"
  },
  "has_mappings": true
}
```

**Empty State Response** (no mappings):
```json
{
  "instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "parameters": {
    "brand_list": "",
    "asin_list": "",
    "campaign_ids": "",
    "campaign_names": ""
  },
  "has_mappings": false
}
```

**Error Responses**:
- `404`: Instance not found
- `403`: User does not have access to this instance
- `401`: Unauthorized

**Backend Implementation**:
```python
@router.get("/{instance_id}/parameter-values")
async def get_parameter_values(
    instance_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get formatted parameter values for auto-population"""
    service = InstanceMappingService()
    values = await service.get_parameter_values(instance_id, current_user.id)
    return values
```

---

## Request/Response Schemas

### InstanceMappingsInput (Request Body Schema)

```python
from pydantic import BaseModel, Field, validator
from typing import Dict, List

class InstanceMappingsInput(BaseModel):
    brands: List[str] = Field(..., min_items=1, description="List of brand tags")
    asins_by_brand: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="ASINs grouped by brand tag"
    )
    campaigns_by_brand: Dict[str, List[int]] = Field(
        default_factory=dict,
        description="Campaign IDs grouped by brand tag"
    )

    @validator('asins_by_brand')
    def validate_asins(cls, v, values):
        """Ensure all ASIN keys match provided brands"""
        brands = values.get('brands', [])
        for brand_tag in v.keys():
            if brand_tag not in brands:
                raise ValueError(f"ASIN brand '{brand_tag}' not in brands list")
        return v

    @validator('campaigns_by_brand')
    def validate_campaigns(cls, v, values):
        """Ensure all campaign keys match provided brands"""
        brands = values.get('brands', [])
        for brand_tag in v.keys():
            if brand_tag not in brands:
                raise ValueError(f"Campaign brand '{brand_tag}' not in brands list")
        return v
```

### Brand (Response Schema)

```python
class Brand(BaseModel):
    brand_tag: str
    brand_name: str
    source: str  # "configuration" or "campaign"
    asin_count: int
    campaign_count: int
```

### ASIN (Response Schema)

```python
class ASIN(BaseModel):
    asin: str
    title: Optional[str]
    brand: str
    image_url: Optional[str]
    price: Optional[float]
    active: bool = True
```

### Campaign (Response Schema)

```python
class Campaign(BaseModel):
    campaign_id: int
    campaign_name: str
    campaign_type: str  # SP, SB, SD, DSP
    marketplace_id: str
    profile_id: str
    status: str
    created_at: datetime
```

## Error Handling

All endpoints follow consistent error response format:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "details": {
    "field": ["Validation error message"]
  }
}
```

### Common HTTP Status Codes
- `200`: Success
- `201`: Created (not used in this API, POST returns 200)
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (missing/invalid JWT token)
- `403`: Forbidden (user lacks access to resource)
- `404`: Not Found (instance, brand, etc.)
- `500`: Internal Server Error

## Rate Limiting

Standard rate limits apply:
- **Authenticated requests**: 1000 requests per hour per user
- **Get endpoints**: No additional limits
- **Post endpoints**: 100 requests per hour per user

## Caching

### Frontend Caching Strategy
```typescript
// React Query cache configuration
queryClient.setQueryData(['instance-mappings', instanceId], data, {
  staleTime: 5 * 60 * 1000,  // 5 minutes
  cacheTime: 10 * 60 * 1000  // 10 minutes
});

// Invalidate cache on save
queryClient.invalidateQueries(['instance-mappings', instanceId]);
```

### Backend Caching
No server-side caching is implemented initially. Database queries are fast enough (<50ms) for typical use cases.

## API Router Registration

**File**: `amc_manager/api/supabase/instances.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from amc_manager.services.instance_mapping_service import InstanceMappingService
from amc_manager.schemas.instance_mappings import (
    InstanceMappingsInput,
    InstanceMappingsOutput,
    ParameterValuesOutput
)

router = APIRouter(prefix="/api/instances", tags=["Instance Mappings"])

# Register all endpoints here
# (endpoints defined above)
```

**Registration in main application**:
```python
# main_supabase.py
from amc_manager.api.supabase.instances import router as instances_router

app.include_router(instances_router)
```

## Testing

### Unit Tests
Test service methods with mocked database:
```python
# tests/services/test_instance_mapping_service.py
def test_get_available_brands():
    service = InstanceMappingService()
    brands = await service.get_available_brands(instance_id, user_id)
    assert len(brands) > 0
    assert "brand_tag" in brands[0]
```

### Integration Tests
Test API endpoints with test database:
```python
# tests/api/test_instance_mappings.py
def test_save_instance_mappings(client, auth_headers):
    response = client.post(
        f"/api/instances/{instance_id}/mappings",
        json={"brands": ["acme"], "asins_by_brand": {"acme": ["B001"]}},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["success"] == True
```

### E2E Tests
Test full user flow with Playwright (see technical-spec.md)
