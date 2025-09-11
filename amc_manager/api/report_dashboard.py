"""Report Dashboard API endpoints for collection data visualization"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field

from ..core.logger_simple import get_logger
from ..services.report_dashboard_service import ReportDashboardService
from ..api.supabase.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(tags=["report-dashboard"])

# Initialize service
report_dashboard_service = ReportDashboardService()


class PeriodComparisonRequest(BaseModel):
    """Request model for period comparison"""
    period_1: Dict[str, Any] = Field(..., description="First period data")
    period_2: Dict[str, Any] = Field(..., description="Second period data")
    metrics: List[str] = Field(..., description="Metrics to compare")


class ReportConfigCreate(BaseModel):
    """Request model for creating report configuration"""
    config_name: str = Field(..., description="Configuration name")
    chart_configs: Dict[str, Any] = Field(..., description="Chart configuration")
    default_view: Optional[str] = Field(None, description="Default view type")


class SnapshotCreate(BaseModel):
    """Request model for creating snapshot"""
    snapshot_name: str = Field(..., description="Snapshot name")
    week_range: Optional[Dict[str, str]] = Field(None, description="Week range")
    is_public: bool = Field(False, description="Public accessibility")


@router.get("/collections/{collection_id}/report-dashboard")
async def get_dashboard_data(
    collection_id: str,
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    aggregation: str = Query("none", description="Aggregation type: none, sum, avg, min, max"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get dashboard data for a collection
    
    Returns comprehensive data including metadata, weekly metrics, and summary statistics.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get dashboard data from service
        result = report_dashboard_service.get_dashboard_data(
            collection_id=collection_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            aggregation=aggregation
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        return result
        
    except ValueError as e:
        if "Collection not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_id}/report-dashboard/compare")
async def compare_periods(
    collection_id: str,
    comparison_request: PeriodComparisonRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Compare metrics between two periods
    
    Calculates deltas and percentage changes between selected periods.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Verify user has access to collection
        collection = report_dashboard_service._client.table('report_data_collections')\
            .select('user_id')\
            .eq('collection_id', collection_id)\
            .execute()
        
        if not collection.data:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        if collection.data[0]['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get data for both periods
        period1_data = comparison_request.period_1.get('weeks', [])
        period2_data = comparison_request.period_2.get('weeks', [])
        
        # Calculate comparison
        result = report_dashboard_service.calculate_comparison(
            period1_data=period1_data,
            period2_data=period2_data,
            metrics=comparison_request.metrics
        )
        
        return {"comparison": result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing periods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_id}/report-dashboard/chart-data")
async def get_chart_data(
    collection_id: str,
    chart_type: str = Query(..., description="Chart type: line, bar, pie, area, scatter"),
    metrics: str = Query(..., description="Comma-separated list of metrics"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get data formatted for Chart.js
    
    Transforms collection data into Chart.js compatible format.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get dashboard data
        dashboard_data = report_dashboard_service.get_dashboard_data(
            collection_id=collection_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not dashboard_data:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Parse metrics
        metrics_list = [m.strip() for m in metrics.split(',')]
        
        # Transform for chart
        chart_data = report_dashboard_service.transform_for_chart(
            data=dashboard_data.get('data', []),
            chart_type=chart_type,
            metrics=metrics_list
        )
        
        return chart_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_id}/report-configs")
async def save_report_config(
    collection_id: str,
    config_data: ReportConfigCreate,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Save a report configuration
    
    Stores user's preferred chart settings and view configurations.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Verify collection exists
        collection = report_dashboard_service._client.table('report_data_collections')\
            .select('id')\
            .eq('collection_id', collection_id)\
            .execute()
        
        if not collection.data:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Save configuration
        config = {
            'collection_id': collection.data[0]['id'],
            'user_id': user_id,
            'config_name': config_data.config_name,
            'chart_configs': config_data.chart_configs,
            'default_view': config_data.default_view
        }
        
        result = report_dashboard_service.save_report_config(config)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving report config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_id}/report-configs")
async def get_report_configs(
    collection_id: str,
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get all report configurations for a collection
    
    Returns user's saved configurations for the collection.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get collection ID
        collection = report_dashboard_service._client.table('report_data_collections')\
            .select('id')\
            .eq('collection_id', collection_id)\
            .execute()
        
        if not collection.data:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Get configurations
        configs = report_dashboard_service.get_report_configs(
            collection_id=collection.data[0]['id'],
            user_id=user_id
        )
        
        return configs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_id}/report-snapshots")
async def create_snapshot(
    collection_id: str,
    snapshot_data: SnapshotCreate,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a report snapshot
    
    Creates a shareable snapshot of the current dashboard state.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get collection data
        collection = report_dashboard_service._client.table('report_data_collections')\
            .select('id')\
            .eq('collection_id', collection_id)\
            .execute()
        
        if not collection.data:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Get dashboard data for snapshot
        dashboard_data = report_dashboard_service.get_dashboard_data(
            collection_id=collection_id,
            user_id=user_id
        )
        
        # Create snapshot
        snapshot = {
            'collection_id': collection.data[0]['id'],
            'user_id': user_id,
            'snapshot_name': snapshot_data.snapshot_name,
            'snapshot_data': dashboard_data,
            'week_range': snapshot_data.week_range,
            'is_public': snapshot_data.is_public
        }
        
        result = report_dashboard_service.create_snapshot(snapshot)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report-snapshots/{snapshot_id}")
async def get_snapshot(
    snapshot_id: str,
    current_user: Optional[dict] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a report snapshot
    
    Returns snapshot data if public or user has access.
    """
    try:
        # Get snapshot
        snapshot = report_dashboard_service.get_snapshot(snapshot_id)
        
        if not snapshot:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        
        # Check access
        if not snapshot.get('is_public'):
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            user_id = current_user.get('id')
            if snapshot.get('user_id') != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        return snapshot
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_id}/report-dashboard/export")
async def export_dashboard_data(
    collection_id: str,
    format: str = Query("csv", description="Export format: csv, json, excel"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Export dashboard data
    
    Exports collection data in various formats for external analysis.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get dashboard data
        dashboard_data = report_dashboard_service.get_dashboard_data(
            collection_id=collection_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not dashboard_data:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Export data based on format
        if format == "json":
            return dashboard_data
        elif format == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if dashboard_data.get('data'):
                # Get all unique keys from data
                all_keys = set()
                for week in dashboard_data['data']:
                    all_keys.update(week.keys())
                    if 'metrics' in week:
                        all_keys.update(week['metrics'].keys())
                
                writer = csv.DictWriter(output, fieldnames=sorted(all_keys))
                writer.writeheader()
                
                for week in dashboard_data['data']:
                    row = week.copy()
                    if 'metrics' in row:
                        row.update(row.pop('metrics'))
                    writer.writerow(row)
                
                return {
                    "format": "csv",
                    "data": output.getvalue(),
                    "filename": f"collection_{collection_id}_export.csv"
                }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_id}/report-dashboard/metrics")
async def get_available_metrics(
    collection_id: str,
    current_user: dict = Depends(get_current_user)
) -> List[str]:
    """
    Get available metrics for a collection
    
    Returns a list of metric names that can be used for dashboard visualization.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # TODO: Implement actual metric extraction from collection data
        # For now, return common metrics
        return [
            "impressions",
            "clicks", 
            "conversions",
            "spend",
            "ctr",
            "cvr",
            "cpc",
            "revenue",
            "roas"
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_id}/report-dashboard/configs")
async def get_dashboard_configs(
    collection_id: str,
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get saved dashboard configurations for a collection
    
    Returns a list of saved dashboard configurations.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # TODO: Implement actual config storage and retrieval
        # For now, return empty list
        return []
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))