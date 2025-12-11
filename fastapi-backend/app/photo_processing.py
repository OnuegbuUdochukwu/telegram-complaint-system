"""Celery worker tasks for post-upload image processing."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from celery import Celery
from celery.utils.log import get_task_logger
from sqlmodel import Session

from .config import get_settings
from .storage_s3 import S3Storage, StorageError
from .photo_utils import process_image, validate_image
from .database import engine
from .models import Photo

settings = get_settings()
celery_app = Celery(
    "photo_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.task_default_queue = "photo-processing"
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.imports = ("app.photo_processing",)

logger = get_task_logger(__name__)


def enqueue_thumbnail_job(photo_id: str, complaint_id: Optional[str] = None) -> None:
    """Fire-and-forget helper used by the API layer."""
    try:
        celery_app.send_task(
            "app.photo_processing.process_photo_task", args=[photo_id, complaint_id]
        )
    except Exception:  # pragma: no cover - Celery not running locally
        logger.warning("Celery unavailable; processing photo %s inline", photo_id)
        process_photo_task.apply(args=[photo_id, complaint_id])


@celery_app.task(
    name="app.photo_processing.process_photo_task",
    bind=True,
    autoretry_for=(StorageError,),
    retry_backoff=True,
    max_retries=3,
)
def process_photo_task(self, photo_id: str, complaint_id: Optional[str] = None) -> None:
    """Download an uploaded photo, generate a thumbnail, and update metadata."""
    s3 = S3Storage()
    with Session(engine) as session:
        photo = session.get(Photo, photo_id)
        if not photo:
            logger.warning("Photo %s not found; skipping", photo_id)
            return

        try:
            data = s3.get_object_bytes(photo.s3_key)
        except StorageError as exc:
            logger.error("Failed to download S3 object for photo %s: %s", photo_id, exc)
            raise

        ok, error = validate_image(data, photo.file_name or "upload.jpg")
        if not ok:
            logger.error("Validation failed for photo %s: %s", photo_id, error)
            raise StorageError(error or "Invalid image")

        optimized_data, thumbnail_data, width, height, mime_type = process_image(
            data, photo.file_name or "upload.jpg"
        )
        thumb_key = S3Storage.build_s3_key(
            photo.complaint_id, photo.id, variant="thumbnail"
        )
        s3.put_object(thumb_key, thumbnail_data, "image/jpeg")

        photo.s3_thumbnail_key = thumb_key
        photo.thumbnail_url = f"s3://{settings.s3_bucket}/{thumb_key}"
        photo.width = width
        photo.height = height
        photo.processed_at = datetime.now(timezone.utc)
        photo.mime_type = mime_type or photo.mime_type

        session.add(photo)
        session.commit()


__all__ = ["celery_app", "enqueue_thumbnail_job"]
