"""API router for ASIN management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from ..services.asin_service import asin_service
from ..api.supabase.auth import get_current_user
from ..core.logger_simple import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/asins", tags=["asins"])


class ASINSearchRequest(BaseModel):
    """Request model for ASIN search"""
    asin_ids: Optional[List[str]] = Field(None, description="List of specific ASIN IDs")
    brands: Optional[List[str]] = Field(None, description="List of brands to filter by")
    search: Optional[str] = Field(None, description="Search term for ASIN/title")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results to return")


class ASINListResponse(BaseModel):
    """Response model for ASIN list"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    pages: int


class BrandsResponse(BaseModel):
    """Response model for brands list"""
    brands: List[str]
    total: int


class ImportResponse(BaseModel):
    """Response model for import operation"""
    import_id: Optional[str]
    status: str
    total_rows: Optional[int]
    message: str


class SearchResponse(BaseModel):
    """Response model for ASIN search"""
    asins: List[Dict[str, Any]]
    total: int


@router.get("/", response_model=ASINListResponse)
async def list_asins(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    marketplace: Optional[str] = Query(None, description="Filter by marketplace"),
    search: Optional[str] = Query(None, description="Search in ASIN and title"),
    active: bool = Query(True, description="Filter by active status"),
    current_user: dict = Depends(get_current_user)
) -> ASINListResponse:
    """
    List ASINs with pagination and filtering
    
    Returns paginated list of ASINs with optional filters for brand, marketplace, and search terms.
    """
    try:
        result = asin_service.list_asins(
            page=page,
            page_size=page_size,
            brand=brand,
            marketplace=marketplace,
            search=search,
            active=active
        )
        
        return ASINListResponse(**result)
        
    except Exception as e:
        logger.error(f"Error listing ASINs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ASINs")


@router.get("/brands", response_model=BrandsResponse)
async def get_brands(
    search: Optional[str] = Query(None, description="Filter brands by search term"),
    current_user: dict = Depends(get_current_user)
) -> BrandsResponse:
    """
    Get list of unique brands
    
    Returns all unique brand names from the ASIN database with optional search filtering.
    """
    try:
        result = asin_service.get_brands(search=search)
        return BrandsResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting brands: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve brands")


@router.post("/search", response_model=SearchResponse)
async def search_asins(
    request: ASINSearchRequest,
    current_user: dict = Depends(get_current_user)
) -> SearchResponse:
    """
    Search ASINs for query parameter selection
    
    Advanced search endpoint for finding ASINs to use in query parameters.
    Supports filtering by specific ASIN IDs, brands, and search terms.
    """
    try:
        result = asin_service.search_asins(
            asin_ids=request.asin_ids,
            brands=request.brands,
            search=request.search,
            limit=request.limit
        )
        
        return SearchResponse(**result)
        
    except Exception as e:
        logger.error(f"Error searching ASINs: {e}")
        raise HTTPException(status_code=500, detail="Failed to search ASINs")


@router.post("/import", response_model=ImportResponse)
async def import_asins(
    file: UploadFile = File(..., description="CSV file to import"),
    update_existing: bool = Form(True, description="Update existing ASINs"),
    current_user: dict = Depends(get_current_user)
) -> ImportResponse:
    """
    Import ASINs from CSV file
    
    Uploads and processes a CSV file containing ASIN data.
    The import runs asynchronously and progress can be tracked using the import ID.
    
    Expected CSV format (tab-delimited):
    - ASIN: Product ASIN
    - TITLE: Product title
    - BRAND: Brand name
    - MARKETPLACE: Marketplace ID (optional, defaults to ATVPDKIKX0DER)
    - ACTIVE: Active status (1 or 0)
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.txt', '.tsv')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload a CSV, TXT, or TSV file."
            )
        
        # Check file size (max 50MB)
        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 50MB."
            )
        
        result = asin_service.import_csv(
            file_content=file_content,
            filename=file.filename,
            user_id=current_user['id'],
            update_existing=update_existing
        )
        
        if result['status'] == 'failed':
            raise HTTPException(status_code=400, detail=result['message'])
        
        return ImportResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing ASINs: {e}")
        raise HTTPException(status_code=500, detail="Failed to import ASINs")


@router.get("/import/{import_id}")
async def get_import_status(
    import_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get status of an import operation
    
    Returns detailed information about an import including progress,
    success/failure counts, and any error details.
    """
    try:
        result = asin_service.get_import_status(import_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Import not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get import status")


@router.get("/{asin_id}")
async def get_asin(
    asin_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed information for a specific ASIN
    
    Returns complete ASIN details including all metadata, dimensions, and sales data.
    """
    try:
        result = asin_service.get_asin(asin_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="ASIN not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ASIN: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ASIN")