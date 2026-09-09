"""
Configuration management using environment variables with sensible defaults.
"""
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env from project root (two levels up from backend/)
_ROOT = Path(__file__).parent.parent.parent
_ENV_FILE = _ROOT / ".env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)

_BACKEND_ROOT = Path(__file__).parent.parent


class Settings:
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    bind_host: str = os.getenv("BIND_HOST", "127.0.0.1")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Storage paths — resolve relative to project root
    @property
    def project_root(self) -> Path:
        return _ROOT

    @property
    def temp_dir(self) -> Path:
        p = os.getenv("TEMP_DIR", "storage/temp")
        return Path(p) if Path(p).is_absolute() else _ROOT / p

    @property
    def output_dir(self) -> Path:
        p = os.getenv("OUTPUT_DIR", "storage/output")
        return Path(p) if Path(p).is_absolute() else _ROOT / p

    @property
    def jobs_dir(self) -> Path:
        return _ROOT / "storage" / "jobs"

    @property
    def db_path(self) -> Path:
        return self.jobs_dir / "youtube_cutter.db"

    @property
    def log_dir(self) -> Path:
        return _ROOT / "logs"

    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
    temp_file_ttl_hours: int = int(os.getenv("TEMP_FILE_TTL_HOURS", "24"))
    zip_file_ttl_hours: int = int(os.getenv("ZIP_FILE_TTL_HOURS", "72"))

    # AI / future integrations
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    whisper_model: str = os.getenv("WHISPER_MODEL", "base")


settings = Settings()

