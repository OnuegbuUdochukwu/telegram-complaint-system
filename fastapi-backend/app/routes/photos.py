"""Photo/S3 routes implementing presigned uploads + metadata flows."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, Field, constr
from sqlmodel import Session, select

from ..dependencies import get_authenticated_user_or_service
from ..database import get_session
from ..models import Complaint, Photo, PhotoUpload
from ..photo_utils import ALLOWED_MIME_TYPES
from ..storage_s3 import S3Storage, guess_extension, StorageError
from ..upload_metrics import (
    UPLOAD_ATTEMPTS,
    UPLOAD_FAILURES,
    UPLOAD_SUCCESSES,
)
from ..config import get_settings
from ..photo_processing import enqueue_thumbnail_job
from ..storage import delete_photo


router = APIRouter(prefix="/api/v1")
settings = get_settings()
storage = S3Storage() if settings.storage_provider.lower() == "s3" else None


class PresignRequest(BaseModel):
    filename: constr(strip_whitespace=True, min_length=1)
    content_type: constr(strip_whitespace=True, min_length=3)
    content_length: Optional[int] = Field(None, gt=0)


class PresignResponse(BaseModel):
    upload_id: str
    photo_id: str
    s3_key: str
    method: str
    url: str
    fields: Optional[dict]
    expires_in: int


class ConfirmUploadRequest(BaseModel):
    photo_id: str
    s3_key: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    checksum: Optional[str] = None


class PhotoResponse(BaseModel):
    id: str
    complaint_id: str
    file_url: str
    thumbnail_url: Optional[str]
    file_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    created_at: Optional[datetime]
    processed_at: Optional[datetime]
    download_url: Optional[str] = None
    thumbnail_download_url: Optional[str] = None


def _ensure_s3():
    if not storage:
        raise HTTPException(status_code=412, detail="S3 storage is not enabled. Set STORAGE_PROVIDER=s3.")
    return storage


def _load_complaint(session: Session, complaint_id: str) -> Complaint:
    complaint = session.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.post("/complaints/{complaint_id}/photos/presign", response_model=PresignResponse, status_code=status.HTTP_201_CREATED)
def presign_upload(
    complaint_id: str,
    request: PresignRequest,
    _: object = Depends(get_authenticated_user_or_service),
    session: Session = Depends(get_session),
):
    """Issue a presigned PUT URL for the Telegram bot/dashboard to upload directly to S3."""
    _ensure_s3()
    _load_complaint(session, complaint_id)

    content_type = request.content_type.lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}")

    photo_id = str(uuid.uuid4())
    extension = guess_extension(content_type)
    key = f"complaints/{complaint_id}/originals/{photo_id}.{extension}"

    try:
        upload = storage.generate_presigned_put(key, content_type, request.content_length)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    record = PhotoUpload(
        id=str(uuid.uuid4()),
        complaint_id=complaint_id,
        photo_id=photo_id,
        filename=request.filename,
        content_type=content_type,
        content_length=request.content_length,
        s3_key=key,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.s3_presign_expiry_upload),
        created_at=datetime.now(timezone.utc),
    )
    session.add(record)
    session.commit()

    return PresignResponse(
        upload_id=record.id,
        photo_id=photo_id,
        s3_key=key,
        method=upload.method,
        url=upload.url,
        fields=upload.fields,
        expires_in=upload.expires_in,
    )


@router.post("/complaints/{complaint_id}/photos/confirm", response_model=PhotoResponse)
def confirm_upload(
    complaint_id: str,
    payload: ConfirmUploadRequest,
    _: object = Depends(get_authenticated_user_or_service),
    session: Session = Depends(get_session),
):
    """Confirm that a PUT upload completed and persist metadata."""
    s3 = _ensure_s3()
    _load_complaint(session, complaint_id)
    UPLOAD_ATTEMPTS.inc()

    try:
        upload_stmt = select(PhotoUpload).where(
            PhotoUpload.complaint_id == complaint_id,
            PhotoUpload.photo_id == payload.photo_id,
            PhotoUpload.s3_key == payload.s3_key,
        )
        upload = session.exec(upload_stmt).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload record not found")

        now = datetime.now(timezone.utc)
        if upload.expires_at < now:
            raise HTTPException(status_code=410, detail="Presigned upload expired")

        head = s3.head_object(payload.s3_key)
        file_size = payload.file_size or head.get("ContentLength")
        content_type = payload.content_type or head.get("ContentType")
        file_url = f"s3://{settings.s3_bucket}/{payload.s3_key}"

        photo = session.get(Photo, payload.photo_id)
        if photo is None:
            photo = Photo(
                id=payload.photo_id,
                complaint_id=complaint_id,
                file_url=file_url,
                thumbnail_url=None,
                file_name=upload.filename,
                file_size=file_size,
                mime_type=content_type,
                storage_provider=settings.storage_provider,
                s3_key=payload.s3_key,
                checksum_sha256=payload.checksum,
            )
        else:
            photo.file_url = file_url
            photo.file_name = upload.filename
            photo.file_size = file_size
            photo.mime_type = content_type
            photo.storage_provider = settings.storage_provider
            photo.s3_key = payload.s3_key
            photo.checksum_sha256 = payload.checksum

        session.add(photo)
        upload.status = "confirmed"
        upload.confirmed_at = now
        session.add(upload)
        session.commit()
        session.refresh(photo)
    except HTTPException:
        UPLOAD_FAILURES.inc()
        raise
    except Exception as exc:
        UPLOAD_FAILURES.inc()
        raise HTTPException(status_code=500, detail=str(exc))

    enqueue_thumbnail_job(photo.id, complaint_id=complaint_id)
    UPLOAD_SUCCESSES.inc()

    return _serialize_photo(photo)


@router.get("/complaints/{complaint_id}/photos", response_model=List[PhotoResponse])
def list_photos(
    complaint_id: str,
    _: object = Depends(get_authenticated_user_or_service),
    session: Session = Depends(get_session),
):
    _load_complaint(session, complaint_id)
    stmt = select(Photo).where(Photo.complaint_id == complaint_id).order_by(Photo.created_at.desc())
    photos = session.exec(stmt).all()
    return [_serialize_photo(p) for p in photos]


@router.get("/complaints/{complaint_id}/photos/{photo_id}", response_model=PhotoResponse)
def get_photo(
    complaint_id: str,
    photo_id: str,
    _: object = Depends(get_authenticated_user_or_service),
    session: Session = Depends(get_session),
):
    photo = session.get(Photo, photo_id)
    if not photo or photo.complaint_id != complaint_id:
        raise HTTPException(status_code=404, detail="Photo not found")
    return _serialize_photo(photo, include_signed_urls=True)


@router.delete("/complaints/{complaint_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo_endpoint(
    complaint_id: str,
    photo_id: str,
    _: object = Depends(get_authenticated_user_or_service),
    session: Session = Depends(get_session),
):
    photo = session.get(Photo, photo_id)
    if not photo or photo.complaint_id != complaint_id:
        raise HTTPException(status_code=404, detail="Photo not found")

    delete_photo(complaint_id, photo_id)
    session.delete(photo)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/admin/storage-health")
def storage_health(_: object = Depends(get_authenticated_user_or_service)):
    s3 = _ensure_s3()
    try:
        s3.ensure_bucket()
        return {"status": "ok", "bucket": settings.s3_bucket, "region": settings.s3_region}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


def _serialize_photo(photo: Photo, include_signed_urls: bool = False) -> PhotoResponse:
    download_url = None
    thumbnail_url = None
    if include_signed_urls and storage and photo.s3_key:
        try:
            download_url = storage.generate_presigned_get(photo.s3_key)
            if photo.s3_thumbnail_key:
                thumbnail_url = storage.generate_presigned_get(photo.s3_thumbnail_key)
        except StorageError:
            download_url = photo.file_url
            thumbnail_url = photo.thumbnail_url

    return PhotoResponse(
        id=photo.id,
        complaint_id=photo.complaint_id,
        file_url=photo.file_url,
        thumbnail_url=photo.thumbnail_url,
        file_name=photo.file_name,
        file_size=photo.file_size,
        mime_type=photo.mime_type,
        width=photo.width,
        height=photo.height,
        created_at=photo.created_at,
        processed_at=photo.processed_at,
        download_url=download_url,
        thumbnail_download_url=thumbnail_url,
    )

