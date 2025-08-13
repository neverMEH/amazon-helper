"""Workflow schemas for input validation"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import re


class WorkflowCreateRequest(BaseModel):
    """Workflow creation request validation"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    sql_query: str = Field(..., min_length=1)
    instance_id: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    
    @validator('sql_query')
    def validate_sql_query(cls, v):
        if not v or not v.strip():
            raise ValueError('SQL query cannot be empty')
        
        # Check for dangerous operations without WHERE clause
        dangerous_patterns = [
            (r'DELETE\s+FROM\s+\w+(?!\s+WHERE)', 'DELETE without WHERE clause is not allowed'),
            (r'UPDATE\s+\w+\s+SET(?!.*WHERE)', 'UPDATE without WHERE clause is not allowed'),
            (r'TRUNCATE\s+TABLE', 'TRUNCATE TABLE is not allowed'),
            (r'DROP\s+(TABLE|DATABASE|SCHEMA)', 'DROP operations are not allowed'),
        ]
        
        sql_upper = v.upper()
        for pattern, error_msg in dangerous_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                raise ValueError(error_msg)
        
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Workflow name cannot be empty')
        # Remove leading/trailing whitespace
        return v.strip()
    
    @validator('instance_id')
    def validate_instance_id(cls, v):
        # Basic validation for instance ID format
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid instance ID format')
        return v


class WorkflowUpdateRequest(BaseModel):
    """Workflow update request validation"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    sql_query: Optional[str] = Field(None, min_length=1)
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, regex='^(active|inactive|archived)$')
    
    @validator('sql_query')
    def validate_sql_query(cls, v):
        if v is None:
            return v
            
        if not v.strip():
            raise ValueError('SQL query cannot be empty')
        
        # Same validation as create
        dangerous_patterns = [
            (r'DELETE\s+FROM\s+\w+(?!\s+WHERE)', 'DELETE without WHERE clause is not allowed'),
            (r'UPDATE\s+\w+\s+SET(?!.*WHERE)', 'UPDATE without WHERE clause is not allowed'),
            (r'TRUNCATE\s+TABLE', 'TRUNCATE TABLE is not allowed'),
            (r'DROP\s+(TABLE|DATABASE|SCHEMA)', 'DROP operations are not allowed'),
        ]
        
        sql_upper = v.upper()
        for pattern, error_msg in dangerous_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                raise ValueError(error_msg)
        
        return v


class WorkflowExecutionRequest(BaseModel):
    """Workflow execution request validation"""
    workflow_id: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('workflow_id')
    def validate_workflow_id(cls, v):
        # UUID format validation
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('Invalid workflow ID format')
        return v