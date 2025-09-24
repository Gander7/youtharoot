from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers.person import router as person_router
from app.routers.event import router as event_router
from app.database import init_database
from app.repositories import init_repositories
from app.config import settings

app = FastAPI(title="Youth Attendance API", description="API for managing youth group attendance")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",  # Local Astro dev server
        "http://localhost:3000",  # Alternative local dev
        "https://youtharoot.vercel.app",  # Your Vercel deployment
        "https://*.vercel.app",  # Allow all Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and repositories on startup
@app.on_event("startup")
async def startup_event():
    print(f"🚀 Starting Youth Attendance API")
    print(f"📊 Database type: {settings.DATABASE_TYPE}")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    
    init_database()
    init_repositories()
    
    print("✅ Application startup complete")

app.include_router(person_router)
app.include_router(event_router)

@app.get("/")
async def root():
    """Simple root endpoint to test API connectivity"""
    return {"message": "Youth Attendance API is running", "status": "ok"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database_type": settings.DATABASE_TYPE,
        "debug": settings.DEBUG
    }