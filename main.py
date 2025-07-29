"""Main FastAPI application"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

from amc_manager.config import settings
from amc_manager.models import init_db
from amc_manager.api import (
    auth_router,
    instances_router,
    workflows_router,
    executions_router,
    campaigns_router,
    queries_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting AMC Manager application...")
    init_db()
    yield
    # Shutdown
    print("Shutting down AMC Manager application...")


# Create FastAPI app
app = FastAPI(
    title="Amazon Marketing Cloud Manager",
    description="Manage AMC instances, build queries, and track executions",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(instances_router, prefix="/api/instances", tags=["Instances"])
app.include_router(workflows_router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(executions_router, prefix="/api/executions", tags=["Executions"])
app.include_router(campaigns_router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(queries_router, prefix="/api/queries", tags=["Queries"])

# Mount static files for web UI
app.mount("/static", StaticFiles(directory="amc_manager/web/static"), name="static")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Amazon Marketing Cloud Manager API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=settings.api_workers if not settings.debug else 1
    )