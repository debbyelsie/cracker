from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from .research import run_demo_research
from .schemas import ResearchRequest

app = FastAPI(title="Cracker Research API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"http://192\.168\.\d{1,3}\.\d{1,3}:3000",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "cracker-api"}


@app.post("/api/research")
def research(payload: ResearchRequest):
    return run_demo_research(payload)


@app.exception_handler(ValidationError)
async def validation_error_handler(_request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
