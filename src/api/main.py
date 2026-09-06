"""FastAPI application for the TraceChain AI REST boundary."""

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.errors import ApiFailure
from src.api.routes import face, health, pipeline, search, verification
from src.api.schemas import ErrorResponse
from src.config import settings

logger = logging.getLogger("tracechain.api")

app = FastAPI(
    title="TraceChain AI API",
    description="Face Discovery and Blockchain Evidence Verification API",
    version="1.0.0",
)

if settings.ALLOWED_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.ALLOWED_ORIGINS), allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["*"])

app.include_router(health.router)
app.include_router(face.router)
app.include_router(pipeline.router)
app.include_router(search.router)
app.include_router(verification.router)


@app.get("/", include_in_schema=False, summary="API service information")
def root() -> dict[str, str]:
    return {
        "service": app.title,
        "message": "TraceChain AI API is running",
        "health": "/health",
        "docs": "/docs",
    }


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    logger.info("api_request_started request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("api_request_failed request_id=%s path=%s", request_id, request.url.path)
        raise
    duration = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info("api_request_completed request_id=%s path=%s status=%s duration_ms=%.2f", request_id, request.url.path, response.status_code, duration)
    return response


@app.exception_handler(ApiFailure)
async def api_failure_handler(_request: Request, exc: ApiFailure):
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "The request did not satisfy the API schema."}, "details": exc.errors()})


@app.exception_handler(Exception)
async def unexpected_handler(_request: Request, exc: Exception):
    logger.exception("unhandled_api_error error_type=%s", type(exc).__name__)
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "The server could not complete the request."}})
