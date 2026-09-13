# ruff: noqa: E402
"""FastAPI Application entry point.

Sets up database connections, registers routers, handles exceptions,
attaches structured JSON logging middleware, and mounts static uploads serving directory.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.CORS import add_cors
from api.middleware.request_logging import StructuredLoggingMiddleware, setup_json_logging
from api.route.auth_api import router as auth_router
from api.route.history_api import router as history_router
from api.route.predict_api import router as predict_router
from core.config import settings
from database import create_tables, init_engine

# Configure structured JSON logging per Universal App Template Section 8
setup_json_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup database engine setup and schema creation, plus shutdown cleanup."""
    # ── Startup ──
    logger.info("Initializing database connection engine ...")
    init_engine(settings.DATABASE_URL)

    # In DEV_MODE or SQLite, auto-create tables if they don't exist
    if settings.DEV_MODE or "sqlite" in settings.DATABASE_URL:
        logger.info("Ensuring database schema exists (DEV_MODE / SQLite) ...")
        await create_tables()

    yield
    # ── Shutdown ──
    logger.info("Draining backend connections on shutdown ...")
    from database import engine
    if engine is not None:
        await engine.dispose()
        logger.info("Database engine connections closed cleanly.")

app = FastAPI(
    title="Smart Shelf Life Prediction API",
    description="Production multimodal CNN-MLP food freshness and shelf life prediction backend.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# ── Structured JSON Logging Middleware ──
app.add_middleware(StructuredLoggingMiddleware)

# ── CORS Middleware Configuration ──
add_cors(app)

# ── Mount Image Upload Directory ──
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Register Routes ──
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(history_router)

# ── Standardized Exception Handling Format (Per Section 5.4) ──
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    msg = exc.errors()[0]["msg"] if exc.errors() else "Validation error"
    field = exc.errors()[0]["loc"][-1] if exc.errors() and exc.errors()[0]["loc"] else "body"
    return JSONResponse(
        status_code=422,
        content={"error": {"code": 422, "message": f"{field}: {msg}"}},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled runtime error occurred: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": 500, "message": "An unexpected server error occurred. Traceback masked for security."}},
    )

@app.get("/api/health", tags=["System"])
async def health():
    """Health check endpoint for container orchestrators and load balancers."""
    return {
        "status": "ok",
        "service": "Smart Shelf Life API",
        "version": "1.0.0",
        "auth_required": settings.REQUIRE_AUTH,
    }
