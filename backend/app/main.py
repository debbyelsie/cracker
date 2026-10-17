from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from .research import prepare_research_intake, run_demo_research
from .openalex import (
    OpenAlexConfigurationError,
    OpenAlexProviderError,
    OpenAlexRateLimitError,
    OpenAlexTimeoutError,
    search_openalex_works,
)
from .schemas import ResearchBrief, ResearchIntake, ResearchRequest, SourceSearchRequest, SourceSearchResponse

app = FastAPI(title="Cracker Research API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3100",
        "http://127.0.0.1:3100",
    ],
    allow_origin_regex=r"http://192\.168\.\d{1,3}\.\d{1,3}:(?:3000|3100)",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "cracker-api"}


@app.post("/api/research/intake", response_model=ResearchIntake)
def research_intake(payload: ResearchRequest):
    return prepare_research_intake(payload.question, payload.scope)


@app.post("/api/research", response_model=ResearchBrief)
def research(payload: ResearchRequest):
    return run_demo_research(payload)


@app.post("/api/research/sources", response_model=SourceSearchResponse)
def research_sources(payload: SourceSearchRequest):
    try:
        return search_openalex_works(payload.query, payload.limit)
    except OpenAlexTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except OpenAlexRateLimitError as exc:
        headers = {"Retry-After": exc.retry_after} if exc.retry_after else None
        raise HTTPException(status_code=429, detail=str(exc), headers=headers) from exc
    except OpenAlexProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except OpenAlexConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.exception_handler(ValidationError)
async def validation_error_handler(_request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
