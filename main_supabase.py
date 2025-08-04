"""Minimal FastAPI application with Supabase integration"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path

from amc_manager.config import settings
from amc_manager.core.logger_simple import get_logger
from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.services.token_refresh_service import token_refresh_service

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
    
    # Start token refresh service
    await token_refresh_service.start()
    logger.info("✓ Token refresh service started")
    
    # Load all active users for token refresh tracking
    try:
        users_response = client.table('users').select('id').execute()
        if users_response.data:
            for user in users_response.data:
                token_refresh_service.add_user(user['id'])
            logger.info(f"✓ Added {len(users_response.data)} users to token refresh tracking")
    except Exception as e:
        logger.warning(f"Could not load users for token refresh: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AMC Manager application...")
    await token_refresh_service.stop()


# Create FastAPI app
app = FastAPI(
    title="Amazon Marketing Cloud Manager",
    description="Manage AMC instances, build queries, and track executions",
    version="0.2.0",
    lifespan=lifespan
)

# Configure CORS
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:8001').split(',')
if os.getenv('FRONTEND_URL'):
    allowed_origins.append(os.getenv('FRONTEND_URL'))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AMC Manager API",
        "version": "0.2.0",
        "backend": "Supabase"
    }


# Debug endpoint to list all routes
@app.get("/api/debug/routes")
async def list_routes():
    """List all registered routes for debugging"""
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, "methods") else []
            })
    return {"routes": sorted(routes, key=lambda x: x["path"])}


# Import and include routers
from amc_manager.api.supabase.auth import router as auth_router
from amc_manager.api.supabase.amazon_auth import router as amazon_auth_router
from amc_manager.api.supabase.instances_simple import router as instances_router
from amc_manager.api.supabase.workflows import router as workflows_router
from amc_manager.api.supabase.campaigns import router as campaigns_router
from amc_manager.api.supabase.query_templates import router as query_templates_router
from amc_manager.api.supabase.brands import router as brands_router

# Add redirect for misconfigured callback URL (must be before router includes)
@app.get("/api/auth/callback")
async def redirect_amazon_callback(code: str, state: str, scope: str = None):
    """Redirect misconfigured Amazon callback to correct endpoint"""
    from fastapi.responses import RedirectResponse
    params = f"code={code}&state={state}"
    if scope:
        params += f"&scope={scope}"
    return RedirectResponse(url=f"/api/auth/amazon/callback?{params}")

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(amazon_auth_router, prefix="/api/auth/amazon", tags=["Amazon OAuth"])
app.include_router(instances_router, prefix="/api/instances", tags=["AMC Instances"])
app.include_router(workflows_router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(campaigns_router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(query_templates_router, prefix="/api/query-templates", tags=["Query Templates"])
app.include_router(brands_router, prefix="/api/brands", tags=["Brands"])

logger.info("All API routers loaded successfully")

# Serve static files if built frontend exists
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    # Mount static assets
    assets_path = frontend_dist / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
    
    # Serve index.html for root and all non-API routes
    @app.get("/")
    async def serve_root():
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            return {"message": "Frontend not built. Please run 'npm run build' in the frontend directory."}
    
    # Catch-all route for SPA (must be last)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't catch API routes - let FastAPI handle 404s for them
        if full_path.startswith("api/"):
            # Return 404 but don't override FastAPI's error handling
            raise HTTPException(status_code=404)
        
        # Serve index.html for all other routes
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            raise HTTPException(status_code=404, detail="Frontend not found")
    
    logger.info("Frontend static files mounted")
else:
    logger.warning("Frontend dist directory not found. API-only mode.")
    
    @app.get("/")
    async def root():
        return {
            "message": "AMC Manager API is running",
            "docs": "/docs",
            "frontend": "Not built - run 'npm run build' in frontend directory"
        }


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