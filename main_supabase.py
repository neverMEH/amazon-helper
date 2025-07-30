"""Minimal FastAPI application with Supabase integration"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path

from amc_manager.config import settings
from amc_manager.core.logger_simple import get_logger
from amc_manager.core.supabase_client import SupabaseManager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting AMC Manager application with Supabase...")
    
    # Test Supabase connection
    try:
        client = SupabaseManager.get_client()
        # Simple connection test
        response = client.table('users').select('count', count='exact').limit(1).execute()
        logger.info("✓ Supabase connection successful")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AMC Manager application...")


# Create FastAPI app
app = FastAPI(
    title="Amazon Marketing Cloud Manager",
    description="Manage AMC instances, build queries, and track executions",
    version="0.2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "AMC Manager API",
        "version": "0.2.0",
        "backend": "Supabase"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "status": "healthy",
        "checks": {
            "api": "operational",
            "supabase": "unknown"
        }
    }
    
    # Check Supabase connection
    try:
        client = SupabaseManager.get_client()
        response = client.table('users').select('count', count='exact').limit(1).execute()
        health_status["checks"]["supabase"] = "operational"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["supabase"] = f"error: {str(e)}"
    
    return health_status


# Import and include routers (we'll create simplified versions)
try:
    from amc_manager.api.supabase.auth import router as auth_router
    from amc_manager.api.supabase.instances_simple import router as instances_router
    from amc_manager.api.supabase.workflows import router as workflows_router
    from amc_manager.api.supabase.campaigns import router as campaigns_router
    from amc_manager.api.supabase.queries import router as queries_router
    from amc_manager.api.supabase.brands import router as brands_router
    
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(instances_router, prefix="/api/instances", tags=["AMC Instances"])
    app.include_router(workflows_router, prefix="/api/workflows", tags=["Workflows"])
    app.include_router(campaigns_router, prefix="/api/campaigns", tags=["Campaigns"])
    app.include_router(queries_router, prefix="/api/queries", tags=["Query Templates"])
    app.include_router(brands_router, prefix="/api/brands", tags=["Brands"])
    
    logger.info("All API routers loaded successfully")
except ImportError as e:
    logger.warning(f"Could not import all routers: {e}")
    logger.info("Running with limited endpoints")

# Serve static files if built frontend exists
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    # Catch-all route for SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't catch API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # Serve index.html for all other routes
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            raise HTTPException(status_code=404, detail="Frontend not found")
    
    logger.info("Frontend static files mounted")


if __name__ == "__main__":
    # Run the application
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(
        "main_supabase:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )