from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base workspace path resolution
BACKEND_SRC_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_SRC_DIR.parents[2]
_ENV_PATH = BACKEND_SRC_DIR.parent / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DEV_MODE: bool = True
    REQUIRE_AUTH: bool = False  # Toggleable authentication
    DATABASE_URL: str = ""
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    SECRET_KEY: str = "dev-secret-key-change-in-production-smart-shelf"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Model Weights & Config Paths (relative to REPO_ROOT)
    MODEL_CHECKPOINT_PATH: str = "model/checkpoints/best_model.pt"
    MODEL_CONFIG_PATH: str = "model/config.yaml"
    
    # Storage
    UPLOAD_DIR: str = str(BACKEND_SRC_DIR.parent / "tmp" / "uploads")

    def model_post_init(self, __context):
        # Auto-configure DATABASE_URL if empty
        if not self.DATABASE_URL:
            db_path = BACKEND_SRC_DIR.parent / "dev.db"
            self.DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
        
        # Ensure upload folder exists
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

settings = Settings()
