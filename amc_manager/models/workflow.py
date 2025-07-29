"""Workflow and execution models"""

from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class Workflow(BaseModel):
    """AMC workflow model"""
    __tablename__ = 'workflows'
    
    # Identification
    workflow_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # AMC instance
    instance_id = Column(String(100), nullable=False, index=True)
    
    # SQL query and configuration
    sql_query = Column(Text, nullable=False)
    parameters = Column(JSONB, default=dict)
    
    # Metadata
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    status = Column(String(50), default='active', nullable=False)  # active, inactive, archived
    is_template = Column(Boolean, default=False)
    tags = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    schedules = relationship("WorkflowSchedule", back_populates="workflow", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_workflow_user_instance', 'user_id', 'instance_id'),
        Index('idx_workflow_status', 'status'),
    )
    
    def __repr__(self):
        return f"<Workflow(workflow_id='{self.workflow_id}', name='{self.name}')>"


class WorkflowExecution(BaseModel):
    """Workflow execution history"""
    __tablename__ = 'workflow_executions'
    
    # Identification
    execution_id = Column(String(100), unique=True, nullable=False, index=True)
    workflow_id = Column(String(36), ForeignKey('workflows.id'), nullable=False)
    
    # Execution details
    status = Column(String(50), nullable=False)  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0)
    
    # Parameters used for this execution
    execution_parameters = Column(JSONB, default=dict)
    
    # Results
    output_location = Column(String(500), nullable=True)  # S3 location
    row_count = Column(Integer, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(String(50), nullable=True)
    completed_at = Column(String(50), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Trigger information
    triggered_by = Column(String(255), nullable=True)  # user_id or 'scheduled'
    schedule_id = Column(String(36), ForeignKey('workflow_schedules.id'), nullable=True)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    schedule = relationship("WorkflowSchedule", back_populates="executions")
    
    __table_args__ = (
        Index('idx_execution_workflow', 'workflow_id'),
        Index('idx_execution_status', 'status'),
        Index('idx_execution_started', 'started_at'),
    )
    
    def __repr__(self):
        return f"<WorkflowExecution(execution_id='{self.execution_id}', status='{self.status}')>"


class WorkflowSchedule(BaseModel):
    """Workflow scheduling configuration"""
    __tablename__ = 'workflow_schedules'
    
    # Identification
    schedule_id = Column(String(100), unique=True, nullable=False, index=True)
    workflow_id = Column(String(36), ForeignKey('workflows.id'), nullable=False)
    
    # Schedule configuration
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default='UTC', nullable=False)
    
    # Parameters for scheduled executions
    default_parameters = Column(JSONB, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run_at = Column(String(50), nullable=True)
    next_run_at = Column(String(50), nullable=True)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="schedules")
    executions = relationship("WorkflowExecution", back_populates="schedule")
    
    __table_args__ = (
        Index('idx_schedule_workflow', 'workflow_id'),
        Index('idx_schedule_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<WorkflowSchedule(schedule_id='{self.schedule_id}', cron='{self.cron_expression}')>"