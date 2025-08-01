"""Brands API endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from ...services.brand_service import brand_service
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("")
def list_brands(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, str]]:
    """Get all available brands for the current user"""
    try:
        brands = brand_service.get_all_brands_sync(current_user['id'])
        return brands
    except Exception as e:
        logger.error(f"Error listing brands: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch brands")


@router.get("/stats")
def get_brand_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Dict[str, int]]:
    """Get statistics for all brands"""
    try:
        stats = brand_service.get_brand_stats_sync(current_user['id'])
        return stats
    except Exception as e:
        logger.error(f"Error fetching brand stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch brand statistics")