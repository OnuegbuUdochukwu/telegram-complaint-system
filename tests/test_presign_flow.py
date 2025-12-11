import os
import uuid

import boto3
import pytest
from httpx import AsyncClient
from moto import mock_aws
from sqlmodel import Session

os.environ.setdefault("ALLOW_DEV_REGISTER", "1")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("BACKEND_SERVICE_TOKEN", "test-service-token")
os.environ.setdefault("STORAGE_PROVIDER", "s3")
os.environ.setdefault("S3_BUCKET", "test-complaint-bucket")
os.environ.setdefault("S3_REGION", "us-east-1")
os.environ.setdefault("S3_ACCESS_KEY_ID", "testing")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only-12345")
# Use the shared test database
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

from app.main import app, init_db  # noqa: E402
from app.database import engine  # noqa: E402
from app.models import Complaint  # noqa: E402
from app.routes import photos as photos_router  # noqa: E402


@pytest.mark.asyncio
async def test_presign_and_confirm_flow(monkeypatch):
    # Setup boto3 with moto inside context
    with mock_aws():
        s3 = boto3.client(
            "s3",
            region_name=os.environ["S3_REGION"],
            aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
        )
        s3.create_bucket(Bucket=os.environ["S3_BUCKET"])

        # Patch storage to be S3Storage so _ensure_s3 passes.
        # This creates S3Storage inside the mocked environment.
        from app.storage_s3 import S3Storage
        from app.routes import photos

        monkeypatch.setattr(photos, "storage", S3Storage())

        # Disable thumbnail job for test
        photos_router.enqueue_thumbnail_job = lambda *a, **k: None

        # Create complaint using sync engine connected to the shared test.db
        # app.database.engine is async. We create a sync engine for setup.
        db_url = os.environ["DATABASE_URL"]
        sync_url = db_url.replace("sqlite+aiosqlite", "sqlite")
        from sqlmodel import create_engine

        sync_engine = create_engine(sync_url)

        complaint = Complaint(
            telegram_user_id="tester",
            hostel="John",
            room_number="A101",
            category="plumbing",
            description="Leak",
            severity="low",
        )

        with Session(sync_engine) as session:
            session.add(complaint)
            session.commit()
            session.refresh(complaint)
            complaint_id = complaint.id

        headers = {"Authorization": "Bearer test-service-token"}

        async with AsyncClient(app=app, base_url="http://test") as client:
            presign_resp = await client.post(
                f"/api/v1/complaints/{complaint_id}/photos/presign",
                json={
                    "filename": "test.jpg",
                    "content_type": "image/jpeg",
                    "content_length": 1024,
                },
                headers=headers,
            )
            assert presign_resp.status_code == 201
            body = presign_resp.json()
            assert body["photo_id"]
            key = body["s3_key"]

            # Simulate upload by writing directly via boto3
            s3.put_object(
                Bucket=os.environ["S3_BUCKET"],
                Key=key,
                Body=b"\xff\xd8\xff",
                ContentType="image/jpeg",
            )

            confirm_resp = await client.post(
                f"/api/v1/complaints/{complaint_id}/photos/confirm",
                json={
                    "photo_id": body["photo_id"],
                    "s3_key": key,
                    "file_size": 3,
                    "content_type": "image/jpeg",
                },
                headers=headers,
            )
            assert confirm_resp.status_code == 200
            payload = confirm_resp.json()
            assert payload["complaint_id"] == complaint_id
            assert payload["file_name"] == "test.jpg"
