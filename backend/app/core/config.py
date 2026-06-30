from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "ZPL Converter"
    api_prefix: str = "/api/v1"
    project_root: Path = PROJECT_ROOT
    renderer_dir: Path = PROJECT_ROOT / "renderer"
    frontend_dist_dir: Path = PROJECT_ROOT / "frontend" / "dist"
    max_upload_bytes: int = _positive_int("MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
    max_rendered_labels: int = _positive_int("MAX_RENDERED_LABELS", 1000)
    renderer_timeout_seconds: int = _positive_int("RENDERER_TIMEOUT_SECONDS", 180)

    @property
    def cors_origins(self) -> list[str]:
        raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
