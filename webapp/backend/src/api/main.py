# ruff: noqa: E402
"""FastAPI Application entry point.

Sets up database connections, registers routers, handles exceptions, 
and mounts static uploads serving directory.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import settings
from database import init_engine, create_tables
from api.route.auth_api import router as auth_router
from api.route.predict_api import router as predict_router
from api.route.history_api import router as history_router

# Configure logger formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-25s │ %(levelname)-8s │ %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup database engine setup and schema creation, plus shutdown cleanup."""
    # ── Startup ──
    logger.info("Initializing database connection ...")
    init_engine(settings.DATABASE_URL)
    
    if settings.DEV_MODE:
        logger.info("Auto-creating SQLite tables (DEV_MODE) ...")
        await create_tables()
        
    yield
    # ── Shutdown ──
    logger.info("Draining backend connections on shutdown ...")
    from database import engine
    if engine is not None:
        await engine.dispose()
        logger.info("Database engine connections closed.")

app = FastAPI(
    title="Smart Shelf Life Prediction API",
    description="Multimodal CNN-MLP food freshness and shelf life prediction backend.",
    version="1.0.0",
    lifespan=lifespan
)

from api.CORS import add_cors

# ── CORS Middleware Configuration ──
add_cors(app)

# ── Mount Image Upload Directory ──
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Register Routes ──
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(history_router)

# ── ArchonFlow Exception Handling Format ──
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Retrieve first error message
    msg = exc.errors()[0]["msg"] if exc.errors() else "Validation error"
    return JSONResponse(
        status_code=422,
        content={"error": {"code": 422, "message": f"{exc.errors()[0]['loc'][-1]}: {msg}"}},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled runtime error occurred: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": 500, "message": "An unexpected server error occurred. Internal traceback masked."}},
    )

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "Smart Shelf Life API", "version": "1.0.0"}
