"""
AMC Data Sources API Endpoints
Provides access to AMC schema documentation and field definitions
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Any, Optional
import logging

from .auth import get_current_user
from ...services.data_source_service import DataSourceService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Data Sources"])


@router.get("/", response_model=List[Dict[str, Any]])
async def list_data_sources(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search term"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    List AMC data sources with optional filtering
    
    - **category**: Filter by schema category (e.g., "DSP Tables", "Attribution Tables")
    - **search**: Full-text search across names and descriptions
    - **tags**: Filter by tags (e.g., ["attribution", "conversion"])
    - **limit**: Maximum number of results to return
    - **offset**: Pagination offset
    """
    try:
        service = DataSourceService()
        return service.list_data_sources(
            category=category,
            search=search,
            tags=tags,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error listing data sources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", response_model=List[str])
async def get_categories(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[str]:
    """Get all unique data source categories"""
    try:
        service = DataSourceService()
        return service.get_categories()
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags", response_model=List[Dict[str, Any]])
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100, description="Maximum tags to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get most commonly used tags with usage counts"""
    try:
        service = DataSourceService()
        return service.get_popular_tags(limit=limit)
    except Exception as e:
        logger.error(f"Error getting tags: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-fields", response_model=List[Dict[str, Any]])
async def search_fields(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Search for fields across all data sources
    
    Returns fields matching the search term along with their data source information.
    Useful for finding where specific fields are available.
    """
    try:
        service = DataSourceService()
        return service.search_fields(search_term=q, limit=limit)
    except Exception as e:
        logger.error(f"Error searching fields: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-ai", response_model=Dict[str, Any])
async def export_for_ai(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Export all schemas in AI/LLM-optimized format
    
    Returns a structured JSON document designed for AI consumption,
    with semantic tagging and relationship mappings.
    """
    try:
        service = DataSourceService()
        return service.export_for_ai()
    except Exception as e:
        logger.error(f"Error exporting for AI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{schema_id}", response_model=Dict[str, Any])
async def get_data_source(
    schema_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a single data source by schema ID
    
    Returns the complete schema metadata including description, tags, and availability.
    """
    try:
        service = DataSourceService()
        result = service.get_data_source(schema_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Data source '{schema_id}' not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data source {schema_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{schema_id}/fields", response_model=List[Dict[str, Any]])
async def get_schema_fields(
    schema_id: str,
    dimension_or_metric: Optional[str] = Query(None, description="Filter by Dimension or Metric"),
    aggregation_threshold: Optional[str] = Query(None, description="Filter by aggregation threshold"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get field definitions for a data source
    
    - **dimension_or_metric**: Filter by "Dimension" or "Metric"
    - **aggregation_threshold**: Filter by threshold (NONE, LOW, MEDIUM, HIGH, VERY_HIGH)
    """
    try:
        service = DataSourceService()
        return service.get_schema_fields(
            schema_id=schema_id,
            dimension_or_metric=dimension_or_metric,
            aggregation_threshold=aggregation_threshold
        )
    except Exception as e:
        logger.error(f"Error getting fields for {schema_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{schema_id}/examples", response_model=List[Dict[str, Any]])
async def get_query_examples(
    schema_id: str,
    category: Optional[str] = Query(None, description="Filter by example category"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get query examples for a data source
    
    Returns SQL query examples demonstrating how to use the data source.
    - **category**: Filter by category (Basic, Advanced, Performance, Attribution, etc.)
    """
    try:
        service = DataSourceService()
        return service.get_query_examples(
            schema_id=schema_id,
            category=category
        )
    except Exception as e:
        logger.error(f"Error getting examples for {schema_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{schema_id}/sections", response_model=List[Dict[str, Any]])
async def get_schema_sections(
    schema_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get documentation sections for a data source
    
    Returns markdown-formatted documentation sections including overview,
    concepts, best practices, and usage guidelines.
    """
    try:
        service = DataSourceService()
        return service.get_schema_sections(schema_id)
    except Exception as e:
        logger.error(f"Error getting sections for {schema_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{schema_id}/relationships", response_model=Dict[str, List[Dict[str, Any]]])
async def get_schema_relationships(
    schema_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get relationships for a data source
    
    Returns both outgoing relationships (where this schema references others)
    and incoming relationships (where other schemas reference this one).
    """
    try:
        service = DataSourceService()
        return service.get_schema_relationships(schema_id)
    except Exception as e:
        logger.error(f"Error getting relationships for {schema_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{schema_id}/complete", response_model=Dict[str, Any])
async def get_complete_schema(
    schema_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get complete schema details including all related data
    
    Returns a comprehensive view including:
    - Schema metadata
    - All field definitions
    - Query examples
    - Documentation sections
    - Relationships to other schemas
    
    This endpoint is optimized for displaying a complete schema detail page.
    """
    try:
        service = DataSourceService()
        result = service.get_complete_schema(schema_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Data source '{schema_id}' not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting complete schema for {schema_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))