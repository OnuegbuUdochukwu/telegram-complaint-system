"""
Centralized settings for the Complaint Management System backend.

Provides a lightweight wrapper around environment variables (with `.env`
support for local development) so the rest of the codebase can import a single
`get_settings()` helper when configuration is needed. This avoids ad‑hoc calls
to `os.environ` spread across modules and keeps defaults consistent.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional
import os

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    """Immutable view of application configuration."""

    # General
    environment: str
    storage_provider: str
    service_token: Optional[str]

    # Database (read-only; SQLModel/alembic still look at DATABASE_URL)
    database_url: str

    # S3 / object storage
    s3_bucket: str
    s3_region: str
    s3_endpoint: Optional[str]
    s3_use_ssl: bool
    s3_access_key_id: Optional[str]
    s3_secret_access_key: Optional[str]
    s3_presign_expiry_upload: int
    s3_presign_expiry_get: int
    kms_key_id: Optional[str]
    cloudfront_domain: Optional[str]

    # Worker / background processing
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
    thumbnail_sizes: tuple[int, int]
    enable_virus_scan: bool

    # Observability
    metrics_namespace: str

    # Local development helpers
    minio_root_user: Optional[str]
    minio_root_password: Optional[str]


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_lookup(key: str, env: dict[str, str], default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key) or env.get(key) or default


@lru_cache()
def get_settings() -> Settings:
    """Load settings once per process."""

    env_path = Path(__file__).resolve().parents[2] / ".env"
    env_file = dotenv_values(str(env_path)) if env_path.exists() else {}

    storage_provider = _env_lookup("STORAGE_PROVIDER", env_file, "s3").lower()
    redis_url = _env_lookup("REDIS_URL", env_file, "redis://redis:6379/0")

    return Settings(
        environment=_env_lookup("APP_ENV", env_file, "development"),
        storage_provider=storage_provider,
        service_token=_env_lookup("BACKEND_SERVICE_TOKEN", env_file),
        database_url=_env_lookup("DATABASE_URL", env_file, "sqlite:///./test.db"),
        s3_bucket=_env_lookup("S3_BUCKET", env_file, "complaint-photos"),
        s3_region=_env_lookup("S3_REGION", env_file, "us-east-1"),
        s3_endpoint=_env_lookup("S3_ENDPOINT", env_file) or _env_lookup("S3_ENDPOINT_URL", env_file),
        s3_use_ssl=_as_bool(_env_lookup("S3_USE_SSL", env_file, "true"), True),
        s3_access_key_id=_env_lookup("S3_ACCESS_KEY_ID", env_file) or _env_lookup("S3_ACCESS_KEY", env_file),
        s3_secret_access_key=_env_lookup("S3_SECRET_ACCESS_KEY", env_file) or _env_lookup("S3_SECRET_KEY", env_file),
        s3_presign_expiry_upload=int(_env_lookup("S3_PRESIGN_EXPIRY_SECONDS_UPLOAD", env_file, "300")),
        s3_presign_expiry_get=int(_env_lookup("S3_PRESIGN_EXPIRY_SECONDS_GET", env_file, "3600")),
        kms_key_id=_env_lookup("KMS_KEY_ID", env_file),
        cloudfront_domain=_env_lookup("CLOUDFRONT_DOMAIN", env_file),
        redis_url=redis_url,
        celery_broker_url=_env_lookup("CELERY_BROKER_URL", env_file, redis_url),
        celery_result_backend=_env_lookup("CELERY_RESULT_BACKEND", env_file, redis_url),
        thumbnail_sizes=(
            int(_env_lookup("THUMBNAIL_SIZE_SMALL", env_file, "256")),
            int(_env_lookup("THUMBNAIL_SIZE_LARGE", env_file, "1024")),
        ),
        enable_virus_scan=_as_bool(_env_lookup("ENABLE_VIRUS_SCAN", env_file, "false")),
        metrics_namespace=_env_lookup("METRICS_NAMESPACE", env_file, "telegram_complaints"),
        minio_root_user=_env_lookup("MINIO_ROOT_USER", env_file),
        minio_root_password=_env_lookup("MINIO_ROOT_PASSWORD", env_file),
    )


__all__ = ["Settings", "get_settings"]

