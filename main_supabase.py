"""Minimal FastAPI application with Supabase integration"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from amc_manager.config import settings
from amc_manager.core.logger_simple import get_logger
from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.services.token_refresh_service import token_refresh_service
from amc_manager.services.execution_status_poller import execution_status_poller
from amc_manager.services.schedule_executor_service import get_schedule_executor

logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Recom AMP application with Supabase...")
    
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
    
    # Start execution status poller
    await execution_status_poller.start()
    logger.info("✓ Execution status poller started")
    
    # Start schedule executor service
    schedule_executor = get_schedule_executor()
    asyncio.create_task(schedule_executor.start())
    logger.info("✓ Schedule executor service started")
    
    # Load only users with valid tokens for token refresh tracking
    try:
        users_response = client.table('users').select('id, auth_tokens').execute()
        if users_response.data:
            users_with_tokens = 0
            for user in users_response.data:
                # Only track users who have auth tokens
                if user.get('auth_tokens'):
                    token_refresh_service.add_user(user['id'])
                    users_with_tokens += 1
            logger.info(f"✓ Added {users_with_tokens} users with tokens to refresh tracking (out of {len(users_response.data)} total)")
    except Exception as e:
        logger.warning(f"Could not load users for token refresh: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Recom AMP application...")
    await token_refresh_service.stop()
    await execution_status_poller.stop()
    await schedule_executor.stop()


# Create FastAPI app
app = FastAPI(
    title="Recom AMP",
    description="Amazon Marketing Cloud query development and execution platform",
    version="0.2.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS with environment-specific settings
if settings.environment == "production":
    # In production, only allow specific origins
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '').split(',')
    if not allowed_origins or allowed_origins == ['']:
        allowed_origins = ["https://your-domain.com"]  # Replace with actual domain
else:
    # In development, allow localhost
    allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:8001').split(',')
    
if os.getenv('FRONTEND_URL'):
    allowed_origins.append(os.getenv('FRONTEND_URL'))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Only add HSTS in production
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


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
from amc_manager.api.supabase.amc_executions import router as amc_executions_router
from amc_manager.api.supabase.profile import router as profile_router
from amc_manager.api.supabase.data_sources import router as data_sources_router
from amc_manager.api.supabase.schedule_endpoints import router as schedules_router
from amc_manager.api.routes.build_guides import router as build_guides_router

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
app.include_router(profile_router, prefix="/api/profile", tags=["Profile"])
app.include_router(instances_router, prefix="/api/instances", tags=["AMC Instances"])
app.include_router(workflows_router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(campaigns_router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(query_templates_router, prefix="/api/query-templates", tags=["Query Templates"])
app.include_router(brands_router, prefix="/api/brands", tags=["Brands"])
app.include_router(amc_executions_router, prefix="/api/amc-executions", tags=["AMC Executions"])
app.include_router(data_sources_router, prefix="/api/data-sources", tags=["Data Sources"])
app.include_router(schedules_router, prefix="/api", tags=["Schedules"])
app.include_router(build_guides_router, prefix="/api", tags=["Build Guides"])

# Apply rate limiting to specific endpoints
for route in app.routes:
    if hasattr(route, "path"):
        if route.path == "/api/auth/login" and route.methods == {"POST"}:
            route.endpoint = limiter.limit("5 per minute")(route.endpoint)
        elif route.path == "/api/auth/refresh" and route.methods == {"POST"}:
            route.endpoint = limiter.limit("10 per minute")(route.endpoint)

logger.info("All API routers loaded successfully with rate limiting")

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
        
        # Check if it's a static file that exists (favicon, manifest, etc.)
        static_file = frontend_dist / full_path
        if static_file.exists() and static_file.is_file():
            # Serve the static file directly
            return FileResponse(str(static_file))
        
        # For all other routes (including /data-sources/*), serve index.html
        # This allows React Router to handle client-side routing
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            # Important: Set correct content type for HTML
            return FileResponse(str(index_path), media_type="text/html")
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