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
    UPLOAD_DIR: str = ""

    def model_post_init(self, __context):
        # Auto-configure DATABASE_URL: fallback to SQLite if empty or if docker host 'db' is unresolvable locally
        import socket
        use_sqlite = not self.DATABASE_URL
        if "postgresql" in self.DATABASE_URL and "@db:" in self.DATABASE_URL:
            try:
                socket.gethostbyname("db")
            except Exception:
                use_sqlite = True

        if use_sqlite:
            db_path = BACKEND_SRC_DIR.parent / "dev.db"
            self.DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

        # Resolve UPLOAD_DIR safely across container and host environments
        default_upload_dir = BACKEND_SRC_DIR.parent / "tmp" / "uploads"
        if not self.UPLOAD_DIR:
            target_path = default_upload_dir
        else:
            p = Path(self.UPLOAD_DIR)
            if not p.is_absolute():
                target_path = REPO_ROOT / p
            else:
                target_path = p

        try:
            target_path.mkdir(parents=True, exist_ok=True)
            self.UPLOAD_DIR = str(target_path)
        except Exception:
            # Fallback to local backend/tmp/uploads if target is not writable
            default_upload_dir.mkdir(parents=True, exist_ok=True)
            self.UPLOAD_DIR = str(default_upload_dir)

settings = Settings()
