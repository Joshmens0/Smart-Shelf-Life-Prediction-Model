from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

def add_cors(app: FastAPI) -> None:
    """Configures CORS middleware based on the deployment mode settings."""
    origins = []

    if settings.DEV_MODE:
        # Allow standard local dev servers
        for dev_origin in ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"]:
            if dev_origin not in origins:
                origins.append(dev_origin)
    else:
        # Default fallback or production configuration
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
