"""
Minimal Snowflake Configuration API endpoints for testing
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid

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


class SnowflakeConfigResponse(BaseModel):
    """Model for Snowflake configuration response"""
    id: str
    account_identifier: str
    warehouse: str
    database: str
    schema: str
    role: Optional[str] = None
    username: Optional[str] = None
    message: str


# Simple test endpoint
@router.get("/test")
async def test_snowflake_endpoint():
    """Test endpoint to verify Snowflake router is working"""
    return {"message": "Snowflake API is working!", "status": "success"}


@router.post("/config", status_code=status.HTTP_201_CREATED, response_model=SnowflakeConfigResponse)
async def create_snowflake_config(
    config_data: SnowflakeConfigCreate
) -> SnowflakeConfigResponse:
    """Create a new Snowflake configuration (simplified for testing)"""
    try:
        # For now, just return the configuration data without saving to database
        config_id = str(uuid.uuid4())
        
        return SnowflakeConfigResponse(
            id=config_id,
            account_identifier=config_data.account_identifier,
            warehouse=config_data.warehouse,
            database=config_data.database,
            schema=config_data.schema,
            role=config_data.role,
            username=config_data.username,
            message="Configuration created successfully (test mode)"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Snowflake configuration: {str(e)}"
        )
