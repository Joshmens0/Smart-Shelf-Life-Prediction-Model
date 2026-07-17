import sys
import os
from pathlib import Path
import uvicorn

# Resolve paths
scripts_dir = Path(__file__).resolve().parent
backend_dir = scripts_dir.parent
src_dir = backend_dir / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.config import settings

def main():
    print(f"Starting Smart Shelf Life Prediction API server...")
    print(f"Host: {settings.HOST}")
    print(f"Port: {settings.PORT}")
    print(f"Require Auth: {settings.REQUIRE_AUTH}")
    print(f"Database: {settings.DATABASE_URL}")
    print(f"Upload directory: {settings.UPLOAD_DIR}")
    
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEV_MODE,
        app_dir=str(src_dir)
    )

if __name__ == "__main__":
    main()
