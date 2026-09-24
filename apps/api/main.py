"""FastAPI main application entrypoint for DineIQ Analytics."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.routers import analytics, health, jobs
from packages.common.logging import get_logger, setup_logging
from packages.core.config.settings import get_settings
from packages.core.schemas.common import ErrorDetail, ErrorEnvelope, ErrorPayload

settings = get_settings()
logger = get_logger("dineiq.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown hooks."""
    setup_logging(log_level="DEBUG" if settings.DEBUG else "INFO")
    logger.info("Starting %s in %s environment", settings.APP_NAME, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="DineIQ Analytics - Data Science Intelligence Arena REST API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Standardized validation error handler."""
    details = [
        ErrorDetail(
            loc=[str(part) for part in err.get("loc", [])],
            msg=err.get("msg", "Validation error"),
            type=err.get("type"),
        )
        for err in exc.errors()
    ]
    envelope = ErrorEnvelope(
        error=ErrorPayload(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=details,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=envelope.model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global catch-all error handler."""
    logger.exception("Unhandled server exception: %s", exc)
    envelope = ErrorEnvelope(
        error=ErrorPayload(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred",
            details=[ErrorDetail(msg=str(exc))],
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=envelope.model_dump(),
    )


# API v1 Router Registration
API_V1_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_V1_PREFIX)
app.include_router(analytics.router, prefix=API_V1_PREFIX)
app.include_router(jobs.router, prefix=API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root_endpoint():
    """Root entrypoint with service metadata and links."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "health": f"{API_V1_PREFIX}/health",
    }
