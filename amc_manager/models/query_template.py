"""Query template models for saving and sharing queries"""

from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class QueryTemplate(BaseModel):
    """Saved query templates"""
    __tablename__ = 'query_templates'
    
    # Template identification
    template_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Query definition
    sql_query = Column(Text, nullable=False)
    parameter_definitions = Column(JSONB, default=dict)  # Parameter schema
    
    # Categorization
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, default=list)
    
    # Sharing and visibility
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    is_public = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # System-provided templates
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(String(50), nullable=True)
    
    # Version control
    version = Column(Integer, default=1)
    parent_template_id = Column(String(36), nullable=True)  # For versioning
    
    # Example parameters for documentation
    example_parameters = Column(JSONB, default=dict)
    
    # Performance hints
    estimated_runtime = Column(String(50), nullable=True)  # e.g., "< 1 min", "5-10 min"
    recommended_date_range = Column(String(50), nullable=True)  # e.g., "30 days"
    
    # Relationships
    user = relationship("User", back_populates="query_templates")
    
    __table_args__ = (
        Index('idx_template_user', 'user_id'),
        Index('idx_template_category', 'category'),
        Index('idx_template_public', 'is_public'),
        Index('idx_template_name', 'template_name'),
    )
    
    def __repr__(self):
        return f"<QueryTemplate(name='{self.template_name}', category='{self.category}')>"
        
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow().isoformat()


class QueryExecution(BaseModel):
    """Track query template executions for analytics"""
    __tablename__ = 'query_executions'
    
    # Execution identification
    template_id = Column(String(36), ForeignKey('query_templates.id'), nullable=True)
    workflow_id = Column(String(36), ForeignKey('workflows.id'), nullable=True)
    
    # Query details
    executed_query = Column(Text, nullable=False)
    parameters_used = Column(JSONB, default=dict)
    
    # Execution context
    instance_id = Column(String(100), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Results
    execution_time_ms = Column(Integer, nullable=True)
    row_count = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationships
    template = relationship("QueryTemplate")
    workflow = relationship("Workflow")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_query_exec_template', 'template_id'),
        Index('idx_query_exec_user', 'user_id'),
    )
    
    def __repr__(self):
        return f"<QueryExecution(template_id='{self.template_id}', user_id='{self.user_id}')>"