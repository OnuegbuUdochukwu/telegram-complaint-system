"""Photo/S3 routes implementing presigned uploads + metadata flows."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
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


from fastapi.concurrency import run_in_threadpool

async def _load_complaint(session: Session, complaint_id: str) -> Complaint:
    complaint = await session.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.post("/complaints/{complaint_id}/photos/presign", response_model=PresignResponse, status_code=status.HTTP_201_CREATED)
async def presign_upload(
    complaint_id: str,
    request: PresignRequest,
    _: object = Depends(get_authenticated_user_or_service),
    session: Session = Depends(get_session),
):
    """Issue a presigned PUT URL for S3 or a direct upload URL for local storage."""
    await _load_complaint(session, complaint_id)

    content_type = request.content_type.lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}")

    photo_id = str(uuid.uuid4())
    extension = guess_extension(content_type)
    key = f"complaints/{complaint_id}/originals/{photo_id}.{extension}"

    # If S3 is enabled, use presigned PUT
    if storage:
        try:
            # generate_presigned_put is purely local crypto and string formatting in boto3
            # so it is safe to call synchronously without threadpool
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
            expires_at=datetime.utcnow() + timedelta(seconds=settings.s3_presign_expiry_upload),
            created_at=datetime.utcnow(),
        )
        session.add(record)
        await session.commit()

        return PresignResponse(
            upload_id=record.id,
            photo_id=photo_id,
            s3_key=key,
            method=upload.method,
            url=upload.url,
            fields=upload.fields,
            expires_in=upload.expires_in,
        )
    
    # For local storage, return a direct upload URL to the backend
    record = PhotoUpload(
        id=str(uuid.uuid4()),
        complaint_id=complaint_id,
        photo_id=photo_id,
        filename=request.filename,
        content_type=content_type,
        content_length=request.content_length,
        s3_key=key,
        expires_at=datetime.utcnow() + timedelta(seconds=3600),  # 1 hour
        created_at=datetime.utcnow(),
    )
    session.add(record)
    await session.commit()

    # Return backend upload URL for local storage
    from ..config import get_settings
    backend_url = get_settings().backend_url or "http://localhost:8001"
    upload_url = f"{backend_url}/api/v1/complaints/{complaint_id}/photos/{photo_id}/upload"

    return PresignResponse(
        upload_id=record.id,
        photo_id=photo_id,
        s3_key=key,
        method="PUT",
        url=upload_url,
        fields=None,
        expires_in=3600,
    )


@router.put("/complaints/{complaint_id}/photos/{photo_id}/upload", response_model=PhotoResponse)
async def direct_upload(
    complaint_id: str,
    photo_id: str,
    request: Request,
    session: Session = Depends(get_session),
):
    """Direct upload endpoint for local storage (alternative to S3 presigned PUT).
    
    This endpoint mimics S3 presigned URLs by relying on the secrecy of the photo_id/upload_id
    and the expiry time checked against the PhotoUpload record. Authentication is NOT required
    because the client (using S3-style flow) does not send credentials, only the URL.
    """
    await _load_complaint(session, complaint_id)
    UPLOAD_ATTEMPTS.inc()

    # Read the raw body
    body = await request.body()
    if not body:
        UPLOAD_FAILURES.inc()
        raise HTTPException(status_code=400, detail="Empty upload body")

    # Find the upload record
    upload_stmt = select(PhotoUpload).where(
        PhotoUpload.complaint_id == complaint_id,
        PhotoUpload.photo_id == photo_id,
    )
    result = await session.exec(upload_stmt)
    upload = result.first()
    if not upload:
        UPLOAD_FAILURES.inc()
        raise HTTPException(status_code=404, detail="Upload record not found")

    # Check expiry
    now = datetime.utcnow()
    expiry = upload.expires_at or now
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry < now:
        UPLOAD_FAILURES.inc()
        raise HTTPException(status_code=410, detail="Upload expired")

    # Store using local storage
    from ..storage import upload_photo as local_upload_photo
    try:
        # File I/O might block, use threadpool
        file_url, thumbnail_url = await run_in_threadpool(
            local_upload_photo, 
            body, 
            complaint_id, 
            photo_id, 
            upload.content_type or "image/jpeg"
        )
    except Exception as exc:
        UPLOAD_FAILURES.inc()
        raise HTTPException(status_code=500, detail=f"Failed to store photo: {exc}")

    # Create or update photo record
    photo = await session.get(Photo, photo_id)
    if photo is None:
        photo = Photo(
            id=photo_id,
            complaint_id=complaint_id,
            file_url=file_url,
            thumbnail_url=thumbnail_url,
            file_name=upload.filename,
            file_size=len(body),
            mime_type=upload.content_type,
            storage_provider="local",
        )
    else:
        photo.file_url = file_url
        photo.thumbnail_url = thumbnail_url
        photo.file_name = upload.filename
        photo.file_size = len(body)
        photo.mime_type = upload.content_type
        photo.storage_provider = "local"

    session.add(photo)
    upload.status = "confirmed"
    upload.confirmed_at = datetime.utcnow()
    session.add(upload)
    await session.commit()
    await session.refresh(photo)

    UPLOAD_SUCCESSES.inc()
    return _serialize_photo(photo)


@router.post("/complaints/{complaint_id}/photos/confirm", response_model=PhotoResponse)
async def confirm_upload(
    complaint_id: str,
    payload: ConfirmUploadRequest,
    _: object = Depends(get_authenticated_user_or_service),
    session: Session = Depends(get_session),
):
    """Confirm that a PUT upload completed and persist metadata."""
    s3 = _ensure_s3()
    await _load_complaint(session, complaint_id)
    UPLOAD_ATTEMPTS.inc()

    try:
        upload_stmt = select(PhotoUpload).where(
            PhotoUpload.complaint_id == complaint_id,
            PhotoUpload.photo_id == payload.photo_id,
            PhotoUpload.s3_key == payload.s3_key,
        )
        result = await session.exec(upload_stmt)
        upload = result.first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload record not found")

        now = datetime.utcnow()
        expiry = upload.expires_at or now
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry < now:
            raise HTTPException(status_code=410, detail="Presigned upload expired")

        # s3.head_object makes network call -> run in threadpool
        head = await run_in_threadpool(s3.head_object, payload.s3_key)
        
        file_size = payload.file_size or head.get("ContentLength")
        content_type = payload.content_type or head.get("ContentType")
        file_url = f"s3://{settings.s3_bucket}/{payload.s3_key}"

        photo = await session.get(Photo, payload.photo_id)
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
        upload.confirmed_at = datetime.utcnow()
        session.add(upload)
        await session.commit()
        await session.refresh(photo)
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
async def list_photos(
    complaint_id: str,
    _: object = Depends(get_authenticated_user_or_service),
    session: Session = Depends(get_session),
):
    await _load_complaint(session, complaint_id)
    stmt = select(Photo).where(Photo.complaint_id == complaint_id).order_by(Photo.created_at.desc())
    result = await session.exec(stmt)
    photos = result.all()
    return [_serialize_photo(p) for p in photos]


@router.get("/complaints/{complaint_id}/photos/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    complaint_id: str,
    photo_id: str,
    _: object = Depends(get_authenticated_user_or_service),
    session: Session = Depends(get_session),
):
    photo = await session.get(Photo, photo_id)
    if not photo or photo.complaint_id != complaint_id:
        raise HTTPException(status_code=404, detail="Photo not found")
    # serialization is purely local/cpu
    return _serialize_photo(photo, include_signed_urls=True)


@router.delete("/complaints/{complaint_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo_endpoint(
    complaint_id: str,
    photo_id: str,
    _: object = Depends(get_authenticated_user_or_service),
    session: Session = Depends(get_session),
):
    photo = await session.get(Photo, photo_id)
    if not photo or photo.complaint_id != complaint_id:
        raise HTTPException(status_code=404, detail="Photo not found")

    # delete_photo might do blocking FS or s3 op -> threadpool
    await run_in_threadpool(delete_photo, complaint_id, photo_id)
    
    await session.delete(photo)
    await session.commit()
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

