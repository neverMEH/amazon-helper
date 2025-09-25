"""
Simple Snowflake Configuration API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid

from ..core.logger_simple import get_logger
from .supabase.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/snowflake", tags=["Snowflake Configuration"])


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


class SnowflakeConfigResponse(BaseModel):
    """Model for Snowflake configuration response"""
    id: str
    user_id: str
    account_identifier: str
    warehouse: str
    database: str
    schema: str
    role: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str


# Simple endpoints without complex service initialization
@router.post("/config", status_code=status.HTTP_201_CREATED, response_model=SnowflakeConfigResponse)
async def create_snowflake_config(
    config_data: SnowflakeConfigCreate,
    current_user: dict = Depends(get_current_user)
) -> SnowflakeConfigResponse:
    """Create a new Snowflake configuration"""
    try:
        from ..core.supabase_client import SupabaseManager
        
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
        
        # Create configuration record
        client = SupabaseManager.get_client()
        config_record = {
            'id': str(uuid.uuid4()),
            'user_id': current_user["id"],
            'account_identifier': config_dict['account_identifier'],
            'warehouse': config_dict['warehouse'],
            'database': config_dict['database'],
            'schema': config_dict['schema'],
            'role': config_dict.get('role'),
            'username': config_dict.get('username'),
            'encrypted_password': config_dict.get('password'),  # TODO: Encrypt this
            'encrypted_private_key': config_dict.get('private_key'),  # TODO: Encrypt this
            'is_active': True
        }
        
        # Insert into database
        response = client.table('snowflake_configurations').insert(config_record).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create Snowflake configuration"
            )
        
        created_config = response.data[0]
        
        # Return response (exclude sensitive fields)
        return SnowflakeConfigResponse(
            id=created_config["id"],
            user_id=created_config["user_id"],
            account_identifier=created_config["account_identifier"],
            warehouse=created_config["warehouse"],
            database=created_config["database"],
            schema=created_config["schema"],
            role=created_config.get("role"),
            username=created_config.get("username"),
            is_active=created_config["is_active"],
            created_at=created_config["created_at"],
            updated_at=created_config["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Snowflake configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Snowflake configuration"
        )


@router.get("/config", response_model=Optional[SnowflakeConfigResponse])
async def get_snowflake_config(
    current_user: dict = Depends(get_current_user)
) -> Optional[SnowflakeConfigResponse]:
    """Get active Snowflake configuration for current user"""
    try:
        from ..core.supabase_client import SupabaseManager
        
        client = SupabaseManager.get_client()
        response = client.table('snowflake_configurations')\
            .select('*')\
            .eq('user_id', current_user["id"])\
            .eq('is_active', True)\
            .single()\
            .execute()
        
        if not response.data:
            return None
            
        config = response.data
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
        return None


@router.delete("/config", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snowflake_config(
    current_user: dict = Depends(get_current_user)
):
    """Delete Snowflake configuration"""
    try:
        from ..core.supabase_client import SupabaseManager
        
        client = SupabaseManager.get_client()
        
        # Get existing configuration
        response = client.table('snowflake_configurations')\
            .select('id')\
            .eq('user_id', current_user["id"])\
            .eq('is_active', True)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Snowflake configuration found"
            )

        # Delete the configuration
        client.table('snowflake_configurations')\
            .delete()\
            .eq('id', response.data["id"])\
            .execute()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Snowflake configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete Snowflake configuration"
        )
