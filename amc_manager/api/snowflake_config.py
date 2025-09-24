"""
Snowflake Configuration API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid

from ..services.snowflake_service import SnowflakeService
from ..core.logger_simple import get_logger
from .supabase.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/snowflake", tags=["Snowflake Configuration"])

# Initialize service
# snowflake_service = SnowflakeService()  # Comment out to avoid initialization at import time


# Pydantic models
class SnowflakeConfigCreate(BaseModel):
    """Model for creating Snowflake configuration"""
    account_identifier: str = Field(..., description="Snowflake account identifier")
    warehouse: str = Field(..., description="Snowflake warehouse name")
    database: str = Field(..., description="Snowflake database name")
    schema: str = Field(..., description="Snowflake schema name")
    role: Optional[str] = Field(None, description="Snowflake role")
    username: Optional[str] = Field(None, description="Username for password auth")
    password: Optional[str] = Field(None, description="Password for password auth")
    private_key: Optional[str] = Field(None, description="Private key for key-pair auth")


class SnowflakeConfigUpdate(BaseModel):
    """Model for updating Snowflake configuration"""
    account_identifier: Optional[str] = None
    warehouse: Optional[str] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    role: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    is_active: Optional[bool] = None


class SnowflakeConfigResponse(BaseModel):
    """Model for Snowflake configuration response"""
    id: str
    user_id: str
    account_identifier: str
    warehouse: str
    database: str
    schema: str
    role: Optional[str]
    username: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str


class SnowflakeTestRequest(BaseModel):
    """Model for testing Snowflake connection"""
    account_identifier: str
    warehouse: str
    database: str
    schema: str
    role: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None


class SnowflakeTestResponse(BaseModel):
    """Model for Snowflake test response"""
    success: bool
    message: Optional[str] = None
    version: Optional[str] = None
    error: Optional[str] = None


class SnowflakeTableResponse(BaseModel):
    """Model for Snowflake table response"""
    name: str
    type: str
    row_count: int
    size_bytes: int
    created: str
    last_altered: str


# Configuration endpoints
@router.post("/config", status_code=status.HTTP_201_CREATED, response_model=SnowflakeConfigResponse)
async def create_snowflake_config(
    config_data: SnowflakeConfigCreate,
    current_user: dict = Depends(get_current_user)
) -> SnowflakeConfigResponse:
    """Create a new Snowflake configuration"""
    try:
        # Validate that either password or private key is provided
        if not config_data.password and not config_data.private_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either password or private key must be provided"
            )
        
        if config_data.password and config_data.private_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either password or private key, not both"
            )

        # Prepare configuration data
        config_dict = config_data.dict(exclude_unset=True)
        
        # Create the configuration
        snowflake_service = SnowflakeService()  # Lazy initialization
        result = snowflake_service.create_snowflake_config(
            config_data=config_dict,
            user_id=current_user["id"]
        )

        # Convert to response model (exclude sensitive fields)
        return SnowflakeConfigResponse(
            id=result["id"],
            user_id=result["user_id"],
            account_identifier=result["account_identifier"],
            warehouse=result["warehouse"],
            database=result["database"],
            schema=result["schema"],
            role=result.get("role"),
            username=result.get("username"),
            is_active=result["is_active"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )

    except ValueError as ve:
        logger.error(f"Validation error creating Snowflake configuration: {str(ve)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating Snowflake configuration: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/config", response_model=Optional[SnowflakeConfigResponse])
async def get_snowflake_config(
    current_user: dict = Depends(get_current_user)
) -> Optional[SnowflakeConfigResponse]:
    """Get active Snowflake configuration for current user"""
    try:
        snowflake_service = SnowflakeService()  # Lazy initialization
        config = snowflake_service.get_user_snowflake_config(current_user["id"])
        
        if not config:
            return None
            
        return SnowflakeConfigResponse(
            id=config["id"],
            user_id=config["user_id"],
            account_identifier=config["account_identifier"],
            warehouse=config["warehouse"],
            database=config["database"],
            schema=config["schema"],
            role=config.get("role"),
            username=config.get("username"),
            is_active=config["is_active"],
            created_at=config["created_at"],
            updated_at=config["updated_at"]
        )

    except Exception as e:
        logger.error(f"Error fetching Snowflake configuration: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/config", response_model=SnowflakeConfigResponse)
async def update_snowflake_config(
    config_data: SnowflakeConfigUpdate,
    current_user: dict = Depends(get_current_user)
) -> SnowflakeConfigResponse:
    """Update Snowflake configuration"""
    try:
        # Get existing configuration
        snowflake_service = SnowflakeService()  # Lazy initialization
        existing_config = snowflake_service.get_user_snowflake_config(current_user["id"])
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Snowflake configuration found"
            )

        # Prepare update data
        update_dict = config_data.dict(exclude_unset=True)
        
        # Update the configuration
        result = snowflake_service.update_snowflake_config(
            config_id=existing_config["id"],
            update_data=update_dict,
            user_id=current_user["id"]
        )

        return SnowflakeConfigResponse(
            id=result["id"],
            user_id=result["user_id"],
            account_identifier=result["account_identifier"],
            warehouse=result["warehouse"],
            database=result["database"],
            schema=result["schema"],
            role=result.get("role"),
            username=result.get("username"),
            is_active=result["is_active"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Snowflake configuration: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/config", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snowflake_config(
    current_user: dict = Depends(get_current_user)
):
    """Delete Snowflake configuration"""
    try:
        # Get existing configuration
        snowflake_service = SnowflakeService()  # Lazy initialization
        existing_config = snowflake_service.get_user_snowflake_config(current_user["id"])
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Snowflake configuration found"
            )

        # Delete the configuration
        snowflake_service.delete_snowflake_config(
            config_id=existing_config["id"],
            user_id=current_user["id"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Snowflake configuration: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Test connection endpoint
@router.post("/test", response_model=SnowflakeTestResponse)
async def test_snowflake_connection(
    test_data: SnowflakeTestRequest,
    current_user: dict = Depends(get_current_user)
) -> SnowflakeTestResponse:
    """Test Snowflake connection with provided credentials"""
    try:
        # Validate that either password or private key is provided
        if not test_data.password and not test_data.private_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either password or private key must be provided"
            )
        
        if test_data.password and test_data.private_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either password or private key, not both"
            )

        # Prepare test configuration
        config_dict = test_data.dict(exclude_unset=True)
        
        # Test connection
        snowflake_service = SnowflakeService()  # Lazy initialization
        result = snowflake_service.test_connection(config_dict)
        
        return SnowflakeTestResponse(
            success=result["success"],
            message=result.get("message"),
            version=result.get("version"),
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing Snowflake connection: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Tables endpoint
@router.get("/tables", response_model=List[SnowflakeTableResponse])
async def list_snowflake_tables(
    database: Optional[str] = None,
    schema: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> List[SnowflakeTableResponse]:
    """List tables in Snowflake database/schema"""
    try:
        snowflake_service = SnowflakeService()  # Lazy initialization
        tables = snowflake_service.list_user_tables(
            user_id=current_user["id"],
            database=database,
            schema=schema
        )
        
        return [
            SnowflakeTableResponse(
                name=table["name"],
                type=table["type"],
                row_count=table["row_count"],
                size_bytes=table["size_bytes"],
                created=table["created"],
                last_altered=table["last_altered"]
            )
            for table in tables
        ]

    except Exception as e:
        logger.error(f"Error listing Snowflake tables: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
