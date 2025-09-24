from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers.person import router as person_router
from app.routers.event import router as event_router

app = FastAPI()
app.include_router(person_router)
app.include_router(event_router)