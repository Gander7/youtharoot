from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers.person import router as person_router
from app.routers.event import router as event_router
from app.database import init_database
from app.repositories import init_repositories
from app.config import settings

app = FastAPI(title="Youth Attendance API", description="API for managing youth group attendance")

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