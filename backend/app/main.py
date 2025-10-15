from contextlib import asynccontextmanager
import logging
import sys

# Configure logging FIRST, before importing any app modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers.person import router as person_router
from app.routers.event import router as event_router
from app.routers.attendance import router as attendance_router
from app.routers.user import router as user_router
from app.routers.groups import router as groups_router
from app.routers.sms import router as sms_router
from app.database import init_database
from app.repositories import init_repositories
from app.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Youtharoot API")
    logger.info(f"📊 Database type: {settings.DATABASE_TYPE}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    logger.info(f"💾 Database URL present: {'Yes' if settings.DATABASE_URL else 'No'}")
    
    # Mask sensitive info in database URL for security
    if settings.database_url:
        # Extract just the scheme and host for logging
        try:
            from urllib.parse import urlparse
            parsed = urlparse(settings.database_url)
            safe_url = f"{parsed.scheme}://{'***:***@' if parsed.username else ''}{parsed.hostname}{':' + str(parsed.port) if parsed.port else ''}{parsed.path}"
            logger.info(f"🔗 Database connection: {safe_url}")
        except Exception:
            logger.info("🔗 Database connection: [URL parsing error - connection configured]")
    else:
        logger.info("🔗 Database connection: In-memory storage")
    
    init_database()
    init_repositories()
    
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown (if needed)
    logger.info("🛑 Application shutdown")

app = FastAPI(
    title="Youtharoot API", 
    description="API for managing youth group attendance",
    lifespan=lifespan
)

# Configure CORS
cors_origins = [
    "http://localhost:4321",  # Local Astro dev server
    "http://localhost:3000",  # Alternative local dev
    "http://localhost:8000",  # Local API testing
    "https://youtharoot.vercel.app",  # Your Vercel deployment
]

# In production, be more permissive for now
if not settings.DEBUG or settings.DATABASE_URL:  # Railway usually sets DATABASE_URL
    cors_origins.append("*")

logger.info(f"🌐 CORS Origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(person_router)
app.include_router(event_router)
app.include_router(attendance_router)
app.include_router(user_router)
app.include_router(groups_router)
app.include_router(sms_router)

@app.get("/")
async def root():
    """Simple root endpoint to test API connectivity"""
    return {"message": "Youtharoot API is running", "status": "ok"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database_type": settings.DATABASE_TYPE,
        "debug": settings.DEBUG
    }

@app.get("/cors-test")
async def cors_test():
    """Test CORS configuration"""
    return {
        "message": "CORS is working!",
        "debug_mode": settings.DEBUG,
        "timestamp": "2025-09-24"
    }

@app.post("/cors-test")
async def cors_test_post():
    """Test CORS configuration for POST requests"""
    return {
        "message": "CORS POST is working!",
        "debug_mode": settings.DEBUG,
        "database_type": settings.DATABASE_TYPE
    }