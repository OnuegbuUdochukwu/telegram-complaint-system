"""
Legacy storage helpers retained for backwards compatibility and local dev.

New S3-first flows live in `storage_s3.py`, but several parts of the codebase
still import `upload_photo`/`get_photo_url`. Those functions now call into the
shared configuration + storage wrapper.
"""

from pathlib import Path
from typing import Optional, Tuple
import logging

from .config import get_settings
from .storage_s3 import S3Storage, guess_extension, StorageError

logger = logging.getLogger("app.storage")

SETTINGS = get_settings()

# Place local storage inside the project workspace (e.g. /app/storage in container)
# Using parents[1] resolves to the project root when the app is located at /app/app
LOCAL_STORAGE_PATH = Path(__file__).resolve().parents[1] / "storage"
try:
    LOCAL_STORAGE_PATH.mkdir(exist_ok=True)
except PermissionError:
    # If the runtime user can't create the directory (e.g., running as non-root),
    # fall back to a writable temp directory to avoid crashing the app.
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="cms_storage_"))
    LOCAL_STORAGE_PATH = tmp
    logger.warning(
        "Could not create %s; falling back to temp storage %s",
        Path(__file__).resolve().parents[1] / "storage",
        LOCAL_STORAGE_PATH,
    )

_s3: Optional[S3Storage] = None
if SETTINGS.storage_provider.lower() == "s3":
    try:
        _s3 = S3Storage()
        _s3.ensure_bucket()
    except Exception as exc:  # pragma: no cover - initialization failure
        logger.error(
            "Failed to initialize S3 storage, falling back to local filesystem: %s", exc
        )
        _s3 = None

logger.info("Storage initialized (provider=%s)", "s3" if _s3 else "local")


def get_s3_key(
    complaint_id: str,
    photo_id: str,
    is_thumbnail: bool = False,
    content_type: str = "image/jpeg",
) -> str:
    """Generate canonical S3 key using the new prefix structure."""
    variant = "thumbnail" if is_thumbnail else "original"
    extension = guess_extension(content_type)
    return S3Storage.build_s3_key(complaint_id, photo_id, variant, extension)


def upload_photo(
    file_data: bytes, complaint_id: str, photo_id: str, content_type: str = "image/jpeg"
) -> Tuple[str, Optional[str]]:
    """
    Upload a photo to storage.

    Returns:
        Tuple of (file_url, thumbnail_url)
    """
    # Generate storage paths
    s3_key = get_s3_key(complaint_id, photo_id, is_thumbnail=False)
    thumbnail_key = get_s3_key(complaint_id, photo_id, is_thumbnail=True)

    if _s3:
        try:
            _s3.put_object(s3_key, file_data, content_type)
            file_url = f"s3://{SETTINGS.s3_bucket}/{s3_key}"
            return file_url, None
        except StorageError as exc:
            logger.error(
                "Failed to upload photo to S3, falling back to local storage: %s", exc
            )

    # Local storage fallback
    local_dir = LOCAL_STORAGE_PATH / complaint_id
    local_dir.mkdir(parents=True, exist_ok=True)

    photo_path = local_dir / f"{photo_id}.jpg"
    photo_path.write_bytes(file_data)

    file_url = f"/storage/{complaint_id}/{photo_id}.jpg"
    thumbnail_url = None

    logger.info(f"Stored photo locally: {photo_path}")
    return file_url, thumbnail_url


def upload_thumbnail(
    thumbnail_data: bytes, complaint_id: str, photo_id: str
) -> Optional[str]:
    """Upload a thumbnail version of a photo."""
    s3_key = get_s3_key(complaint_id, photo_id, is_thumbnail=True)

    if _s3:
        try:
            _s3.put_object(s3_key, thumbnail_data, "image/jpeg")
            return f"s3://{SETTINGS.s3_bucket}/{s3_key}"
        except StorageError as exc:
            logger.error("Failed to upload thumbnail to S3: %s", exc)

    # Local storage fallback
    local_dir = LOCAL_STORAGE_PATH / complaint_id
    local_dir.mkdir(parents=True, exist_ok=True)

    thumbnail_path = local_dir / f"{photo_id}_thumb.jpg"
    thumbnail_path.write_bytes(thumbnail_data)

    logger.info(f"Stored thumbnail locally: {thumbnail_path}")
    return f"/storage/{complaint_id}/{photo_id}_thumb.jpg"


def get_photo_url(complaint_id: str, photo_id: str, is_thumbnail: bool = False) -> str:
    """
    Generate a URL for accessing a photo.

    For S3, this returns a signed URL valid for 7 days.
    For local storage, returns a path-relative URL.
    """
    s3_key = get_s3_key(complaint_id, photo_id, is_thumbnail)

    if _s3:
        try:
            return _s3.generate_presigned_get(s3_key)
        except StorageError as exc:
            logger.error("Failed to generate signed URL: %s", exc)

    # Local storage
    suffix = "_thumb.jpg" if is_thumbnail else ".jpg"
    return f"/storage/{complaint_id}/{photo_id}{suffix}"


def delete_photo(complaint_id: str, photo_id: str) -> bool:
    """Delete a photo from storage."""
    s3_key = get_s3_key(complaint_id, photo_id, is_thumbnail=False)
    thumbnail_key = get_s3_key(complaint_id, photo_id, is_thumbnail=True)

    deleted = False

    if _s3:
        try:
            _s3.delete_object_tree(complaint_id, photo_id)
            deleted = True
        except StorageError as exc:
            logger.error("Failed to delete photo from S3: %s", exc)

    # Also try to delete from local storage
    local_dir = LOCAL_STORAGE_PATH / complaint_id
    if local_dir.exists():
        photo_path = local_dir / f"{photo_id}.jpg"
        thumbnail_path = local_dir / f"{photo_id}_thumb.jpg"

        if photo_path.exists():
            photo_path.unlink()
            deleted = True
        if thumbnail_path.exists():
            thumbnail_path.unlink()
            deleted = True

    return deleted
