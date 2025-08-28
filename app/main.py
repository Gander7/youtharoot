from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers.person import router as person_router

app = FastAPI()
app.include_router(person_router)
