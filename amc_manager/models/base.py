"""Base database models and configuration"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import Column, DateTime, String
from datetime import datetime
import uuid

from ..config import settings


# Create engine (optional - primarily using Supabase)
engine = None
SessionLocal = None

if settings.database_url:
    engine = create_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.debug
    )
    # Session factory
    SessionLocal = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

# Base class for models
Base = declarative_base()
metadata = MetaData()


class BaseModel(Base):
    """Abstract base model with common fields"""
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
        
    def update(self, **kwargs):
        """Update model attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
    @classmethod
    def create(cls, **kwargs):
        """Create new instance"""
        instance = cls(**kwargs)
        return instance


def get_db():
    """Dependency to get database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not configured. Set DATABASE_URL environment variable.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    if engine is None:
        raise RuntimeError("Database not configured. Set DATABASE_URL environment variable.")
    Base.metadata.create_all(bind=engine)