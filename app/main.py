from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers.person import router as person_router

app = FastAPI()
app.include_router(person_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
	return JSONResponse(
		status_code=500,
		content={"detail": str(exc)}
	)
