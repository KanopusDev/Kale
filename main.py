from fastapi import FastAPI, HTTPException, status, Request, Response, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.core.database import db_manager
from app.routes import auth, email, dashboard, user
from app.routes import templates as template_routes
import logging
import uvicorn
import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
import secrets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI"""
    # Startup
    try:
        logger.info("Starting Kale Email API...")
        
        # Initialize database
        db_manager.init_database()
        
        # Initialize services
        try:
            from app.services.template import TemplateService
            TemplateService.create_system_templates()
        except ImportError:
            logger.warning("Template service not available")
        except Exception as e:
            logger.error(f"Template service error: {e}")
        
        logger.info("Kale Email API started successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kale Email API...")


class SecurityMiddleware(BaseHTTPMiddleware):
    """Professional security middleware"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add basic security headers (no CSP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY" 
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Cache control for different file types
        if request.url.path.endswith('.html') or request.url.path == '/':
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        elif '/static/' in request.url.path:
            response.headers["Cache-Control"] = "public, max-age=31536000"  # 1 year
        
        return response


# Create FastAPI app
app = FastAPI(
    title="Kale Email API Platform",
    description="Enterprise Email API Platform",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
jinja_templates = Jinja2Templates(directory="templates")

# HTML Routes (Must be defined BEFORE public API routes to avoid conflicts)
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page"""
    with open("templates/index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Serve the dashboard page - authentication handled on frontend"""
    with open("templates/dashboard.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Serve the admin dashboard page - authentication handled on frontend"""
    with open("templates/admin.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/docs", response_class=HTMLResponse)
async def docs_page():
    """Serve the API documentation page"""
    with open("templates/docs.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """Serve the registration page"""
    with open("templates/register.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page"""
    with open("templates/login.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(template_routes.router, prefix="/api/v1")
app.include_router(email.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")

# Include documentation router
try:
    from app.routes.docs import router as docs_router
    app.include_router(docs_router, tags=["Documentation"])
    logger.info("Documentation router included successfully")
except ImportError as e:
    logger.warning(f"Documentation router not available: {e}")

# Include company pages router
try:
    from app.routes.company import router as company_router
    app.include_router(company_router, tags=["Company"])
    logger.info("Company router included successfully")
except ImportError as e:
    logger.warning(f"Company router not available: {e}")

# Include admin routes
try:
    from app.routes.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    logger.info("Admin router included successfully")
except ImportError as e:
    logger.warning(f"Admin router not available: {e}")

# Include public API router LAST (for personal URLs like /{username}/{template_id})
try:
    from app.routes.public import router as public_api_router
    app.include_router(public_api_router, tags=["Public API"])
    logger.info("Public API router included successfully")
except ImportError as e:
    logger.warning(f"Public API router not available: {e}")

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    from pathlib import Path
    from fastapi.responses import FileResponse
    
    favicon_path = Path("static/favicon.ico")
    if favicon_path.exists():
        return FileResponse(favicon_path)
    else:
        # Return empty response for favicon requests to avoid 404 errors
        return Response(content="", media_type="image/x-icon", status_code=204)



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = db_manager.get_db_connection()
        conn.close()
        
        # Test Redis connection
        redis_client = db_manager.get_redis_client()
        redis_client.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "timestamp": "2025-07-23T12:00:00Z",
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_UNAVAILABLE,
            detail="Service unhealthy"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
